"""The battery cell plant Monte Carlo at one location (design 0009, model 1.12): every draw's hours through physics.hourly, then daily totals and
their statistics, per `gwh` GWh/yr of cell capacity.

utilization="full" (the headline, as every EA states its figure) runs every draw at full output; "sampled" draws it (physics.RANGES) for a
running plant. The peak day is the 1-in-10-year peak day (the 90th percentile of annual maxima) at the same output: a cell plant's output does
not follow the weather, so its peak is the weather's, through the towers and the outdoor air.
"""
import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models.battery import physics as bp
from waterledger_models.daily import daily_stats, groups
from waterledger_models.grid import RunWater

DRAWS = 400       # as for data centers (datacenter.physics.DRAWS)
UTILIZATION = ("full", "sampled")


def draws(n=DRAWS, seed=7, utilization="full", settings=None, chemistry="nmc"):
    """The Monte Carlo draws, run by run, then the central run last: [{name: value}]. `settings` fixes parameters in every run, for a scenario: a plant's
    own operating settings (cycles of concentration, its hybrid's switch_on dry-bulb) or any value its documents give. An LFP plant's runs also
    draw lfp_factor (physics.LFP); an NMC plant's runs are the same draws without it."""
    if utilization not in UTILIZATION:
        raise ValueError(f"utilization must be one of {UTILIZATION}, not {utilization!r}")
    if chemistry not in bp.CHEMISTRIES:
        raise ValueError(f"chemistry must be one of {bp.CHEMISTRIES}, not {chemistry!r}")
    settings = dict(settings or {})
    unknown = set(settings) - set(bp.PARAMETERS) - {"switch_on"}
    if unknown:
        raise ValueError(f"unknown settings: {sorted(unknown)}")
    if chemistry != "lfp" and set(settings) & set(bp.LFP):
        raise ValueError("lfp_factor is an LFP plant's: use chemistry='lfp'")
    v = bp.sample_parameters(n, seed)
    runs = [{k: float(a[i]) for k, a in v.items()} for i in range(n)] + [bp.central_parameters()]
    if chemistry == "lfp":
        f = hr.latin_hypercube(bp.LFP, n, seed)
        runs = [{**p, **({k: float(a[i]) for k, a in f.items()} if i < n else {k: (lo + hi) / 2 for k, (lo, hi) in bp.LFP.items()})}
                for i, p in enumerate(runs)]
    if utilization == "full":
        runs = [{**p, "utilization": 1.0} for p in runs]
    return [{**p, **settings} for p in runs]


def run_location(times, temps, rhs, n=DRAWS, seed=7, gwh=1.0, utilization="full", designs=None, settings=None, water_temps=None, chemistry="nmc", grid=None):
    """Monte Carlo for each design at one location, per `gwh` GWh/yr of cell capacity, for the plant's chemistry (physics.CHEMISTRIES: "nmc" for
    NMC and NCA, "lfp"). `settings` fixes parameters in every run (draws). The lake
    design runs when `water_temps` is given: the lake's daily long-term average surface temperatures by day of year (366, as NOAA GLERL's;
    once_through.glerl_temperatures). designs defaults to every design the inputs allow.

    Returns {design: {stat: {"p10", "p50", "p90", "central"}}}: withdrawn, consumed and returned, and returned's two destinations to_sewer and
    to_source (MGD), as avg, peak_1in10, record, annual_mg and, for withdrawn and consumed, max_month, max_90day and worst_year_mg; power_mw_avg,
    power_mw_peak_1in10 (the 1-in-10-year highest hour, at full output) and power_mw_peak_day_1in10 (electricity, MW); fuel_mw_avg;
    site_kwh_per_kwh (electricity and fuel per kWh of cells made, the cooling plant included); withdrawn_l_per_kwh and consumed_l_per_kwh (per kWh
    of cells made); utilization. As for data centers (design 0010's standard treatment): withdrawn_peak_full_capacity, the 1-in-10-year peak day at
    full output, and power_mw_peak_1in10 at full output, so with utilization="sampled" each run is also worked at full output; at full output they
    are the run's own.

    grid: {balancing authority: {kind: gal/MWh for each hour of `times`}} (waterledger_models.grid.lookup), as data centers take it: each adds the
    plant's water at those power plants, grid_<BA>_<kind>_avg and grid_<BA>_<kind>_peak_1in10 (MGD at `gwh`), from its hourly electricity through
    grid.RunWater. A cell plant has no load factor, so its peak day is at the run's own output.
    """
    if designs is None:
        designs = tuple(d for d in bp.DESIGNS if d != "lake" or water_temps is not None)
    tdb, rh = np.array(temps, dtype=float), np.array(rhs, dtype=float)
    twb = hr.wet_bulb(tdb, rh)
    water_t = None if water_temps is None else lake_hours(times, water_temps)
    days = np.array([t[:10] for t in times])
    uniq, day_index = np.unique(days, return_inverse=True)
    years, months = np.array([d[:4] for d in uniq]), np.array([d[:7] for d in uniq])
    by = (groups(years), groups(months))
    counts = np.bincount(day_index, minlength=len(uniq))
    hour_years = np.array([t[:4] for t in times])
    year_ends = np.r_[np.flatnonzero(hour_years[1:] != hour_years[:-1]) + 1, len(hour_years)]
    runs = draws(n, seed, utilization, settings, chemistry)
    plant_water = RunWater(grid, day_index, len(uniq), [g.start for g in by[0]]) if grid else None
    out = {}
    for design in designs:
        acc = {}
        for p in runs:
            p = bp.for_location(p, tdb, rh)
            h = bp.hourly(tdb, twb, rh, design, p, water_t)
            full = h if p["utilization"] == 1.0 else bp.hourly(tdb, twb, rh, design, {**p, "utilization": 1.0}, water_t)
            for name in ("withdrawn", "consumed", "returned", "to_sewer", "to_source"):
                s = daily_stats(day_index, len(uniq), years, h[name], gwh, months if name in ("withdrawn", "consumed") else None, by)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            acc.setdefault("withdrawn_peak_full_capacity", []).append(
                acc["withdrawn_peak_1in10"][-1] if full is h else daily_stats(day_index, len(uniq), years, full["withdrawn"], gwh, by=by)["peak_1in10"])
            day_mw = np.bincount(day_index, weights=h["electricity"], minlength=len(uniq)) / counts * gwh / 1000.0
            acc.setdefault("power_mw_avg", []).append(float(h["electricity"].mean()) * gwh / 1000.0)
            acc.setdefault("power_mw_peak_1in10", []).append(float(np.quantile([part.max() for part in np.split(full["electricity"], year_ends[:-1])], 0.9)) * gwh / 1000.0)
            acc.setdefault("power_mw_peak_day_1in10", []).append(float(np.quantile([day_mw[g].max() for g in by[0]], 0.9)))
            acc.setdefault("fuel_mw_avg", []).append(float(h["fuel"].mean()) * gwh / 1000.0)
            made = bp.CELLS_PER_HOUR * p["utilization"]
            acc.setdefault("site_kwh_per_kwh", []).append(float((h["electricity"] + h["fuel"]).mean()) / made)
            acc.setdefault("withdrawn_l_per_kwh", []).append(float(h["withdrawn"].mean()) * bp.L_GAL / made)
            acc.setdefault("consumed_l_per_kwh", []).append(float(h["consumed"].mean()) * bp.L_GAL / made)
            acc.setdefault("utilization", []).append(p["utilization"])
            if plant_water:                                  # water at the power plants for this hourly electricity (design 0008), as for data centers
                mw = h["electricity"] * (gwh / 1000.0)
                for key, v in plant_water.stats(mw, mw).items():
                    acc.setdefault(key, []).append(v)
        out[design] = {k: {"p10": float(np.quantile(v[:-1], 0.1)), "p50": float(np.quantile(v[:-1], 0.5)), "p90": float(np.quantile(v[:-1], 0.9)),
                           "central": float(v[-1])} for k, v in acc.items()}
    return out


def lake_hours(times, water_temps):
    """Each hour's lake surface temperature, C, from daily values by day of year (day 1 first)."""
    t = np.asarray(water_temps, dtype=float)
    day = np.array([x[:10] for x in times], dtype="datetime64[D]")
    doy = (day - day.astype("datetime64[Y]").astype("datetime64[D]")).astype(int)
    return t[np.minimum(doy, t.size - 1)]
