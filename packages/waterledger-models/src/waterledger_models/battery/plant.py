"""The battery cell plant Monte Carlo at one location (design 0009, model 1.12): every draw's hours through physics.hourly, then daily totals and
their statistics, per `gwh` GWh/yr of cell capacity.

utilization="full" (the headline, as every EA states its figure) runs every draw at full output; "sampled" draws it (physics.RANGES) for a
running plant. The peak day is the 1-in-10-year peak day (the 90th percentile of annual maxima) at the same output: a cell plant's output does
not follow the weather, so its peak is the weather's, through the towers and the outdoor air.
"""
import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models.battery import physics as bp
from waterledger_models import runs

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


def run_location(times, temps, rhs, n=DRAWS, seed=7, gwh=1.0, utilization="full", designs=None, settings=None, water_temps=None, chemistry="nmc", grid=None,
                 discharge="sewer"):
    """Monte Carlo for each design at one location, per `gwh` GWh/yr of cell capacity, for the plant's chemistry (physics.CHEMISTRIES: "nmc" for
    NMC and NCA, "lfp"). `settings` fixes parameters in every run (draws). The lake
    design runs when `water_temps` is given: the lake's daily long-term average surface temperatures by day of year (366, as NOAA GLERL's;
    once_through.glerl_temperatures). designs defaults to every design the inputs allow.

    Returns {design: {stat: {"p10", "p50", "p90", "central"}}}: withdrawn, consumed and returned, and returned's two destinations to_sewer and
    to_source (MGD), as avg, peak_1in10, record, annual_mg and, for withdrawn and consumed, max_month, max_90day and worst_year_mg; power_mw_avg,
    power_mw_peak_1in10 (the 1-in-10-year highest hour, at full output) and power_mw_peak_day_1in10 (electricity, MW); fuel_mw_avg;
    site_kwh_per_kwh (electricity and fuel per kWh of cells made, the cooling plant included); withdrawn_l_per_kwh and consumed_l_per_kwh (per kWh
    of cells made); utilization; blowdown_avg (towers and hybrid: the cooling towers' blowdown, MGD on an average day, part of to_sewer or to_stream). As for data centers (design 0010's standard treatment): withdrawn_peak_full_capacity, the 1-in-10-year peak day at
    full output, and power_mw_peak_1in10 at full output, so with utilization="sampled" each run is also worked at full output; at full output they
    are the run's own.

    grid: {balancing authority: {kind: gal/MWh for each hour of `times`}} (waterledger_models.grid.lookup), as data centers take it: each adds the
    plant's water at those power plants, grid_<BA>_<kind>_avg and grid_<BA>_<kind>_peak_1in10 (MGD at `gwh`), from its hourly electricity through
    grid.RunWater. A cell plant has no load factor, so its peak day is at the run's own output.
    """
    model = _CellPlantRuns(n, seed, gwh, utilization, settings, chemistry, water_temps, discharge)
    return runs.run_location(model, times, temps, rhs, designs=designs, grid=grid)


class _CellPlantRuns:
    """The cell plant's part of the shared runner (waterledger_models.runs): its draws, and each draw's hours from physics.hourly. Its loads: the run's
    output, which is also its peak day's (a cell plant has no load factor); full output for the full-capacity withdrawal and the highest hour, worked
    apart only when utilization is sampled."""

    def __init__(self, n, seed, gwh, utilization, settings, chemistry, water_temps, discharge="sewer"):
        self.n, self.seed, self.gwh, self.utilization, self.settings, self.chemistry = n, seed, gwh, utilization, settings, chemistry
        self.water_temps, self.discharge = water_temps, discharge
        self.designs = tuple(d for d in bp.DESIGNS if d != "lake" or water_temps is not None)    # every design the inputs allow

    def draws(self):
        return draws(self.n, self.seed, self.utilization, self.settings, self.chemistry)

    def setup(self, times, tdb, twb, rh):
        self.tdb, self.twb, self.rh = tdb, twb, rh
        self.water_t = None if self.water_temps is None else lake_hours(times, self.water_temps)

    def run(self, design, p):
        tdb, twb, rh, gwh = self.tdb, self.twb, self.rh, self.gwh
        p = bp.for_location(p, tdb, rh)
        h = bp.hourly(tdb, twb, rh, design, p, self.water_t, self.discharge)
        full = None if p["utilization"] == 1.0 else bp.hourly(tdb, twb, rh, design, {**p, "utilization": 1.0}, self.water_t, self.discharge)
        made = bp.CELLS_PER_HOUR * p["utilization"]
        to_mw = gwh / 1000.0                            # kW per GWh/yr to MW at the plant's size
        return runs.Hours(water={name: (h[name], gwh) for name in ("withdrawn", "consumed", "returned", "to_sewer", "to_source", "to_stream")},
                          mw=h["electricity"] * to_mw, utilization=p["utilization"],
                          full=None if full is None else (full["withdrawn"], gwh), mw_full=None if full is None else full["electricity"] * to_mw,
                          extras={"fuel_mw_avg": float(h["fuel"].mean()) * gwh / 1000.0,
                                  "site_kwh_per_kwh": float((h["electricity"] + h["fuel"]).mean()) / made,
                                  "withdrawn_l_per_kwh": float(h["withdrawn"].mean()) * bp.L_GAL / made,
                                  "consumed_l_per_kwh": float(h["consumed"].mean()) * bp.L_GAL / made,
                                  **({"blowdown_avg": float(h["blow"].mean()) * 24 * gwh / 1e6} if design in ("towers", "hybrid") else {})})


def lake_hours(times, water_temps):
    """Each hour's lake surface temperature, C, from daily values by day of year (day 1 first)."""
    t = np.asarray(water_temps, dtype=float)
    day = np.array([x[:10] for x in times], dtype="datetime64[D]")
    doy = (day - day.astype("datetime64[Y]").astype("datetime64[D]")).astype(int)
    return t[np.minimum(doy, t.size - 1)]
