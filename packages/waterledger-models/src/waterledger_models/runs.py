"""The Monte Carlo at one location, shared by every water user type (design 0010's standard treatment, step 2a).

A type hands the runner a small model object and supplies only what is its own: its designs, its draws, and each draw's hours. The runner owns
the rest, the same for every type: the draws loop over every design, the standard loads, the daily statistics, water at the power plants, the
result names, and the p10 / p50 / p90 / central summary.

    model.designs                 the designs to run when none are given
    model.draws()                 the Monte Carlo's parameter sets, the central run last
    model.setup(times, tdb, twb, rh)
                                  once per location, before any draw (precomputed weather terms, a lake's hourly temperatures)
    model.run(design, p)          one draw's Hours

The standard loads (design 0010):
    run     the run's own load: averages, months and years, and the run's peak day unless the type gives a peak load
    peak    the peak day's load (a data center's average load over its load factor): the 1-in-10-year peak day and the record day
    full    full capacity: withdrawn_peak_full_capacity and the 1-in-10-year highest hour of electricity
A type whose peak or full load is the run's own leaves it out (None), and the run's hours stand for it.

Results, {design: {stat: {"p10", "p50", "p90", "central"}}}:
    <role>_avg, _peak_1in10, _record, _annual_mg, and for withdrawn and consumed _max_month, _max_90day, _worst_year_mg   MGD and MG at the scale given
    withdrawn_peak_full_capacity                                                                                         MGD
    the type's extras, in the order it gives them; utilization
    power_mw_avg, power_mw_peak_1in10 (the highest hour, at full capacity), power_mw_peak_day_1in10 (the peak day's average, at the peak load)
    grid_<BA>_<kind>_avg and _peak_1in10                                                                                 with grid= (grid.RunWater)
    whatever `extra` returns                                                                                             with extra=

`extra(design, p, hours)` is called for every draw with that draw's Hours, so a caller can work out more from each draw's hourly electricity
(the power supply scenarios: what serves it, and the water that takes) without the runner keeping every draw's hours. It returns {stat: value}.
"""
from dataclasses import dataclass, field

import numpy as np

from waterledger_models.daily import daily_stats, groups
from waterledger_models.grid import RunWater
from waterledger_models.heat_rejection import wet_bulb

MONTHLY = ("withdrawn", "consumed")      # the roles that also get months, 90 days and the worst year


@dataclass
class Hours:
    """One draw's hours, as a type gives them to the runner. Water is (gallons per unit of scale each hour, scale), passed to daily.daily_stats as
    they are; electricity is MW each hour."""
    water: dict                          # {role: (hourly, scale)} at the run's load, in the order the results should list them
    mw: np.ndarray                       # electricity at the run's load
    utilization: float
    peak: dict | None = None             # {role: (hourly, scale)} at the peak day's load; None: the run's own
    mw_peak: np.ndarray | None = None    # electricity at the peak day's load; None: the run's
    full: tuple | None = None            # (hourly withdrawal, scale) at full capacity; None: the run's own peak day
    mw_full: np.ndarray | None = None    # electricity at full capacity; None: the run's
    extras: dict = field(default_factory=dict)   # the type's own measures for this draw, {stat: value}


def run_location(model, times, temps, rhs, designs=None, grid=None, extra=None):
    """Monte Carlo for each design at one location (module docstring). grid: {BA: {kind: gal/MWh for each hour of `times`}}, as grid.RunWater
    takes it. extra: called as extra(design, p, hours) for every draw; its {stat: value} join the results."""
    tdb = np.array(temps, dtype=float)
    rh = np.array(rhs, dtype=float)
    twb = wet_bulb(tdb, rh)
    days = np.array([t[:10] for t in times])
    uniq, day_index = np.unique(days, return_inverse=True)
    years, months = np.array([d[:4] for d in uniq]), np.array([d[:7] for d in uniq])
    by = (groups(years), groups(months))
    counts = np.bincount(day_index, minlength=len(uniq))
    hour_years = np.array([t[:4] for t in times])
    year_ends = np.r_[np.flatnonzero(hour_years[1:] != hour_years[:-1]) + 1, len(hour_years)]
    plant_water = RunWater(grid, day_index, len(uniq), [g.start for g in by[0]]) if grid else None
    model.setup(times, tdb, twb, rh)
    runs = model.draws()
    out = {}
    for design in designs or model.designs:
        acc = {}
        for p in runs:
            h = model.run(design, p)
            for name, (arr, scale) in h.water.items():
                s = daily_stats(day_index, len(uniq), years, arr, scale, months if name in MONTHLY else None, by)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            for name, (arr, scale) in (h.peak or {}).items():
                s = daily_stats(day_index, len(uniq), years, arr, scale, by=by)
                acc[f"{name}_peak_1in10"][-1], acc[f"{name}_record"][-1] = s["peak_1in10"], s["record"]
            acc.setdefault("withdrawn_peak_full_capacity", []).append(
                acc["withdrawn_peak_1in10"][-1] if h.full is None else daily_stats(day_index, len(uniq), years, *h.full, by=by)["peak_1in10"])
            for k, v in h.extras.items():
                acc.setdefault(k, []).append(v)
            acc.setdefault("utilization", []).append(h.utilization)
            mw_peak = h.mw if h.mw_peak is None else h.mw_peak
            mw_full = h.mw if h.mw_full is None else h.mw_full
            day_mw = np.bincount(day_index, weights=mw_peak, minlength=len(uniq)) / counts
            acc.setdefault("power_mw_avg", []).append(float(h.mw.mean()))
            acc.setdefault("power_mw_peak_1in10", []).append(float(np.quantile([part.max() for part in np.split(mw_full, year_ends[:-1])], 0.9)))
            acc.setdefault("power_mw_peak_day_1in10", []).append(float(np.quantile([day_mw[g].max() for g in by[0]], 0.9)))
            if plant_water:                              # water at the power plants for this hourly electricity (design 0008)
                for k, v in plant_water.stats(h.mw, mw_peak).items():
                    acc.setdefault(k, []).append(v)
            if extra:
                for k, v in extra(design, p, h).items():
                    acc.setdefault(k, []).append(v)
        out[design] = {k: {"p10": float(np.quantile(v[:-1], 0.1)), "p50": float(np.quantile(v[:-1], 0.5)), "p90": float(np.quantile(v[:-1], 0.9)),
                           "central": float(v[-1])} for k, v in acc.items()}
    return out
