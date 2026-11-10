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

DRAWS = 400       # as for data centers (datacenter.physics.DRAWS)
UTILIZATION = ("full", "sampled")


def draws(n=DRAWS, seed=7, utilization="full", settings=None):
    """The Monte Carlo draws, run by run, then the central run last: [{name: value}]. `settings` fixes parameters in every run, for a scenario: a plant's
    own operating settings (cycles of concentration, its hybrid's switch_on dry-bulb) or any value its documents give."""
    if utilization not in UTILIZATION:
        raise ValueError(f"utilization must be one of {UTILIZATION}, not {utilization!r}")
    settings = dict(settings or {})
    unknown = set(settings) - set(bp.PARAMETERS) - {"switch_on"}
    if unknown:
        raise ValueError(f"unknown settings: {sorted(unknown)}")
    v = bp.sample_parameters(n, seed)
    runs = [{k: float(a[i]) for k, a in v.items()} for i in range(n)] + [bp.central_parameters()]
    if utilization == "full":
        runs = [{**p, "utilization": 1.0} for p in runs]
    return [{**p, **settings} for p in runs]


def run_location(times, temps, rhs, n=DRAWS, seed=7, gwh=1.0, utilization="full", designs=None, settings=None, water_temps=None):
    """Monte Carlo for each design at one location, per `gwh` GWh/yr of cell capacity. `settings` fixes parameters in every run (draws). The lake
    design runs when `water_temps` is given: the lake's daily long-term average surface temperatures by day of year (366, as NOAA GLERL's;
    once_through.glerl_temperatures). designs defaults to every design the inputs allow.

    Returns {design: {stat: {"p10", "p50", "p90", "central"}}}: withdrawn, consumed and returned, and returned's two destinations to_sewer and
    to_source (MGD), as avg, peak_1in10, record, annual_mg and, for withdrawn and consumed, max_month, max_90day and worst_year_mg; power_mw_avg,
    power_mw_peak_1in10 (the 1-in-10-year highest hour, at the run's output) and power_mw_peak_day_1in10 (electricity, MW); fuel_mw_avg;
    site_kwh_per_kwh (electricity and fuel per kWh of cells made, the cooling plant included); withdrawn_l_per_kwh and consumed_l_per_kwh (per kWh
    of cells made); utilization.
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
    runs = draws(n, seed, utilization, settings)
    out = {}
    for design in designs:
        acc = {}
        for p in runs:
            p = bp.for_location(p, tdb, rh)
            h = bp.hourly(tdb, twb, rh, design, p, water_t)
            for name in ("withdrawn", "consumed", "returned", "to_sewer", "to_source"):
                s = daily_stats(day_index, len(uniq), years, h[name], gwh, months if name in ("withdrawn", "consumed") else None, by)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            day_mw = np.bincount(day_index, weights=h["electricity"], minlength=len(uniq)) / counts * gwh / 1000.0
            acc.setdefault("power_mw_avg", []).append(float(h["electricity"].mean()) * gwh / 1000.0)
            acc.setdefault("power_mw_peak_1in10", []).append(float(np.quantile([part.max() for part in np.split(h["electricity"], year_ends[:-1])], 0.9)) * gwh / 1000.0)
            acc.setdefault("power_mw_peak_day_1in10", []).append(float(np.quantile([day_mw[g].max() for g in by[0]], 0.9)))
            acc.setdefault("fuel_mw_avg", []).append(float(h["fuel"].mean()) * gwh / 1000.0)
            made = bp.CELLS_PER_HOUR * p["utilization"]
            acc.setdefault("site_kwh_per_kwh", []).append(float((h["electricity"] + h["fuel"]).mean()) / made)
            acc.setdefault("withdrawn_l_per_kwh", []).append(float(h["withdrawn"].mean()) * bp.L_GAL / made)
            acc.setdefault("consumed_l_per_kwh", []).append(float(h["consumed"].mean()) * bp.L_GAL / made)
            acc.setdefault("utilization", []).append(p["utilization"])
        out[design] = {k: {"p10": float(np.quantile(v[:-1], 0.1)), "p50": float(np.quantile(v[:-1], 0.5)), "p90": float(np.quantile(v[:-1], 0.9)),
                           "central": float(v[-1])} for k, v in acc.items()}
    return out


def lake_hours(times, water_temps):
    """Each hour's lake surface temperature, C, from daily values by day of year (day 1 first)."""
    t = np.asarray(water_temps, dtype=float)
    day = np.array([x[:10] for x in times], dtype="datetime64[D]")
    doy = (day - day.astype("datetime64[Y]").astype("datetime64[D]")).astype(int)
    return t[np.minimum(doy, t.size - 1)]
