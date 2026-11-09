"""Cooling water model v2 for Water Ledger: weather-driven, literature-aligned, with uncertainty.

Hour by hour over the weather record it is given (30 years for the published results):
  facility power and heat rejected, from one heat balance (physics.hourly_heat_power; model 1.5): facility power less the heat rejection
      fans, with the economizer carrying what the weather allows. Facility power over IT power is the hour's PUE.
  evaporation = heat × evaporative ratio ÷ latent heat, with the evaporative ratio from Rutberg et al. 2011
      (the dry-bulb relation USGS SIR 2013-5188 uses for cooling towers).
  drift = a small fraction of circulating flow (physics.RANGES: 0.005-0.02%); circulating flow from heat ÷ (500 × range °F).
  blowdown + drift = evaporation ÷ (cycles of concentration − 1)  (the dissolved solids balance; Lei and Masanet Eq. 7; DOE FEMP BMP #10).
Designs differ in when they evaporate:
  dry       air-cooled / dry closed loop, designed to use no water for cooling: loop top-ups only, plus the staff water every design has
  assist    dry coolers with adiabatic pre-cooling above a dry-bulb switch point tied to the loop's temperature, an operator's setting: water evaporates into the air ahead of the
            coil, in proportion to the wet-bulb depression; no tower drift
  hybrid    dry coolers most of the year, evaporative in warm weather (ramp from the same switch point; the top at the location's own 0.4% design dry-bulb)
  towers    open cooling towers, evaporative all year (upper bound for typical practice)
Outputs per run: withdrawn (makeup), consumed (evaporation + drift + loop top-up + humidifiers), returned to sewer (blowdown + condensate),
condensate (from the outside air, not withdrawn, so withdrawn + condensate = consumed + returned).
Monte Carlo over parameter ranges (Latin hypercube, linked parameters grouped: physics.sample_parameters) gives percentiles, per 100 MW of IT capacity.

Staff water (restrooms, kitchens, cleaning) is not per kWh: it follows the people on site, which grow slowly with size, so it
is a separate term, staff_runs() and staff_q(), added to the per-100 MW results at the campus's size (model 1.2). The designs modeled
recirculate indoor air, so outside air comes in only to pressurize and ventilate (model 1.5, physics.OUTSIDE): humidifiers may use a little
water in dry winters and a coil condenses some in humid summers. A direct outside-air design would use far more air and is not modeled.

Parameter ranges and their sources are in RANGES and documented on the Water Ledger methods page
(docs/research/water-ledger-methods-alignment.md).
"""
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from waterledger_models.datacenter import kernel
from waterledger_models.datacenter.physics import sample_staff
from waterledger_models.datacenter.physics import (ADIABATIC, DEFAULT_PLANT, DRAWS, DESIGNS as _DESIGNS, PLANTS, HFG, KWH_BTU, LB_GAL, OUTSIDE, POWER, RANGES, STAFF, TOPUP, _ramp,  # noqa: F401
                                                   central_parameters, evaporative_ratio, hourly_heat_power, hourly_rates, for_location, hourly_water_with_air, peak_utilization, sample_parameters, wet_bulb)

DESIGNS = list(_DESIGNS)
LABELS = {
    "dry": "Closed loop (designed to use no water for cooling)",
    "assist": "Dry coolers with adiabatic pre-cooling in warm weather",
    "hybrid": "Hybrid: dry most of the year, evaporative in warm weather",
    "towers": "Cooling towers (evaporative all year)",
}


def hourly(tdb, twb, design, p, rh=None, heat=None):
    """Gallons per IT kWh, by hour: (withdrawn, consumed, returned). See physics.hourly_rates."""
    return hourly_rates(tdb, twb, design, p, rh, heat)


def sample(n=DRAWS, seed=7, plant=DEFAULT_PLANT):
    """The Monte Carlo draws, run by run: physics.sample_parameters as a list of {name: value}."""
    v = sample_parameters(n, seed, plant)
    return [{k: float(a[i]) for k, a in v.items()} for i in range(n)]


def central(plant=DEFAULT_PLANT):
    return central_parameters(plant)


STAFF_KEYS = ("core", "per_mw", "gpcd", "used", "maint_base", "maint_per_mw", "maint_used")


def staff_runs(n=DRAWS, seed=13):
    """Non-cooling water parameters per run, on their own stream: [core people, people per MW, gal per person a day, share used up,
    maintenance gal a day for the campus, maintenance gal a day per MW, maintenance share lost]."""
    d = sample_staff(n, seed)
    return [[float(d[f"staff_{k}"][i]) for k in STAFF_KEYS] for i in range(n)]


def _nc(r, mw):
    """One run's non-cooling water at `mw` MW, MGD: (withdrawn, consumed). Runs of four (before model 1.3) have no maintenance."""
    g = (r[0] + r[1] * mw) * r[2] / 1e6
    m = (r[4] + r[5] * mw) / 1e6 if len(r) > 4 else 0.0
    return g + m, g * r[3] + (m * r[6] if len(r) > 4 else 0.0)


def staff_q(runs, mw, part=None):
    """Non-cooling water (staff plus maintenance) at `mw` MW of IT capacity, MGD: {"withdrawn"|"consumed"|"returned": {"p10","p50","p90"}}.
    part="staff" or "maint" gives one part only. Same as WQ.staff on the page."""
    if part:
        runs = [r[:4] + [0.0, 0.0, 0.0] if part == "staff" else [0.0, 0.0, 0.0, 0.0] + list(r[4:]) for r in runs]
    wc = np.array([_nc(r, mw) for r in runs])
    q = lambda v: {"p10": float(np.quantile(v, 0.1)), "p50": float(np.quantile(v, 0.5)), "p90": float(np.quantile(v, 0.9))}
    return {"withdrawn": q(wc[:, 0]), "consumed": q(wc[:, 1]), "returned": q(wc[:, 0] - wc[:, 1])}


def groups(labels):
    """Each label's run of positions, in label order, for labels already sorted (a run's days, years or months): [slice]. A slice
    picks the same values in the same order as `labels == label`, so a statistic over it is the same to the bit, without a pass over
    every day per label."""
    labels = np.asarray(labels)
    cut = np.r_[0, np.flatnonzero(labels[1:] != labels[:-1]) + 1, len(labels)]
    return [slice(a, b) for a, b in zip(cut[:-1], cut[1:])]


def daily_stats(day_index, ndays, years, gal_per_kwh_hour, kw, months=None, by=None):
    """From hourly gal/kWh and IT kW, compute daily MGD and summary statistics: average day, 1-in-10-year peak day (90th percentile
    of annual maxima), record day, average year, and with `months` (each day's YYYY-MM) the highest month's average day, the highest
    90 straight days' average and the highest calendar year. `by`: (groups(years), groups(months)) when the days are in order, which
    gives the same numbers faster."""
    daily = np.bincount(day_index, weights=gal_per_kwh_hour * kw, minlength=ndays) / 1e6
    in_years = [daily[s] for s in by[0]] if by else [daily[years == y] for y in np.unique(years)]
    ann_max = np.array([d.max() for d in in_years])
    out = {"avg": float(daily.mean()), "peak_1in10": float(np.quantile(ann_max, 0.9)), "record": float(daily.max()),
           "annual_mg": float(daily.mean() * 365.25)}
    if months is not None:
        in_months = [daily[s] for s in by[1]] if by else [daily[months == m] for m in np.unique(months)]
        out["max_month"] = float(max(d.mean() for d in in_months))
        out["max_90day"] = float(np.convolve(daily, np.ones(90) / 90, "valid").max()) if len(daily) >= 90 else float(daily.mean())
        out["worst_year_mg"] = float(max(d.sum() for d in in_years))
    return out


def summarize(days, mgd):
    """Statistics of one daily series (MGD by ISO date), for figures and single-run reports: average day, highest month, 1-in-10-year
    peak day, record day and its date, average and highest year."""
    days, v = np.array(days), np.array(mgd)
    years, months = np.array([d[:4] for d in days]), np.array([d[:7] for d in days])
    ann = [v[years == y] for y in np.unique(years)]
    return {"avg": float(v.mean()), "max_month": float(max(v[months == m].mean() for m in np.unique(months))),
            "peak_1in10": float(np.quantile([a.max() for a in ann], 0.9)), "record": float(v.max()), "record_day": str(days[v.argmax()]),
            "annual_mg": float(v.mean() * 365.25), "worst_year_mg": float(max(a.sum() for a in ann))}


def daily(times, temps, rhs, design, mw, p=None, plant=DEFAULT_PLANT):
    """One run's daily series at `mw` MW of IT capacity (central parameters by default), staff water at its central values included:
    (days, withdrawn MGD, returned MGD), at the average load. For seasonal figures and record days; the pages and reviews use the Monte Carlo percentiles."""
    tdb, rh = np.array(temps, dtype=float), np.array(rhs, dtype=float)
    p = {**for_location(central(plant), tdb), **(p or {})}
    w, c, r = hourly(tdb, wet_bulb(tdb, rh), design, p, rh)
    days = np.array([t[:10] for t in times])
    uniq, idx = np.unique(days, return_inverse=True)
    kw = mw * 1000 * p["utilization"]
    g, gu = _nc([sum(STAFF[k]) / 2 for k in STAFF_KEYS], mw)
    wd = np.bincount(idx, weights=w * kw, minlength=len(uniq)) / 1e6 + g
    rd = np.bincount(idx, weights=r * kw, minlength=len(uniq)) / 1e6 + g - gu
    return [str(d) for d in uniq], wd.tolist(), rd.tolist()


def run_locations(weather, n=DRAWS, seed=7, mw=100.0, workers=None, plant=DEFAULT_PLANT):
    """run_location for several places at once, one process each: {name: (times, temps, rhs)} to {name: results}. Each place's results are the same as
    running it alone. workers defaults to WATERLEDGER_WORKERS, else one, because a process pool needs the caller's script to have the usual `if __name__ == "__main__"`
    guard (on macOS it breaks without it) and a library can't know that. `waterledger build-state` and `build` turn on every core."""
    names = list(weather)
    workers = workers or int(os.environ.get("WATERLEDGER_WORKERS") or 1)
    if workers == 1 or len(names) == 1:
        return {k: run_location(*weather[k], n=n, seed=seed, mw=mw, plant=plant) for k in names}
    with ProcessPoolExecutor(min(workers, len(names))) as pool:
        jobs = {k: pool.submit(run_location, *weather[k], n=n, seed=seed, mw=mw, plant=plant) for k in names}
        return {k: job.result() for k, job in jobs.items()}


def run_plants(times, temps, rhs, n=DRAWS, seed=7, mw=100.0, block=None, plants=None, compiled=True):
    """run_location for each cooling plant (physics.PLANTS, the default first): {plant: results}. Each plant's draws share the same strata."""
    return {k: run_location(times, temps, rhs, n=n, seed=seed, mw=mw, block=block or HOUR_BLOCK, plant=k, compiled=compiled)
            for k in (plants or [DEFAULT_PLANT] + [k for k in PLANTS if k != DEFAULT_PLANT])}


# Hours worked at a time (model 1.8, Nov 4, 2026). Each step of the heat balance is a NumPy operation over every hour of a run, and over
# 30 years each step's result is 2.1 MB, so with six runs at once the steps wait on memory rather than the processor. Worked 4,096 hours
# at a time, the in-between results stay in the processor's cache. Every step is the same calculation on each hour, so the results are
# the same to the bit (tests/test_cooling_blocks.py). None works the whole record at once, as before.
HOUR_BLOCK = 4096


def _hourly_run(tdb, twb, rh, design, p, at_peak, block=HOUR_BLOCK):
    """One run's hourly series, block by block: PUE; withdrawn, consumed, returned and condensate at the run's load and at its peak
    load; withdrawn with every computer at capacity; and PUE at the peak load."""
    out = [np.empty_like(tdb) for _ in range(11)]
    at_capacity = {**p, "utilization": 1.0}
    for a in range(0, len(tdb), block or len(tdb)):
        s = slice(a, a + (block or len(tdb)))
        t, wb, h = tdb[s], twb[s], rh[s]
        pue, heat = hourly_heat_power(t, wb, design, p, h)      # the slow part: once for the run's water and PUE, once at the peak load
        pue_peak, heat_peak = hourly_heat_power(t, wb, design, at_peak, h)
        got = (pue, *hourly(t, wb, design, p, h, heat), hourly_water_with_air(t, wb, p, h)[1],
               *hourly(t, wb, design, at_peak, h, heat_peak), hourly_water_with_air(t, wb, at_peak, h)[1], hourly(t, wb, design, at_capacity, h)[0],
               pue_peak)
        for o, v in zip(out, got):
            o[s] = v
    return out


def run_location(times, temps, rhs, n=DRAWS, seed=7, mw=100.0, block=HOUR_BLOCK, plant=DEFAULT_PLANT, compiled=True):
    """Monte Carlo for every design at one location, per `mw` MW of IT capacity, for one cooling plant (physics.PLANTS). `block`: hours worked at a time (HOUR_BLOCK)
    on the NumPy path. compiled: the hours through kernel.py's compiled heat balance (model 1.10), which agrees with physics.py's NumPy path to about
    1e-15 of each value; False runs physics.py itself.

    Returns {design: {stat: {"p10","p50","p90"}}} for withdrawn/consumed/returned average, peak and annual, and electricity,
    plus the central-parameter run. Peak = 1-in-10-year peak day (90th percentile of annual maxima) at the peak load, average load over the load factor; the record
    day is at the same load, and averages, months and years at the average load. withdrawn_peak_full_capacity is the upper case, every computer at capacity all day. Electricity: pue_avg (energy over IT
    energy), power_mw_avg (at the run's utilization), pue_peak_1in10 and power_mw_peak_1in10 (the 1-in-10-year hottest hour, every computer
    running at capacity), and power_mw_peak_day_1in10 (the 1-in-10-year peak day's average power at the peak load, as the peak-day water; model 1.9).
    Each statistic takes its own days, so the peak power day and the peak water day are usually, not always, the same day.
    """
    tdb = np.array(temps, dtype=float)
    rh = np.array(rhs, dtype=float)
    twb = wet_bulb(tdb, rh)
    days = np.array([t[:10] for t in times])
    uniq, day_index = np.unique(days, return_inverse=True)
    years = np.array([d[:4] for d in uniq])
    months = np.array([d[:7] for d in uniq])
    hour_years = np.array([t[:4] for t in times])
    year_ends = np.r_[np.flatnonzero(hour_years[1:] != hour_years[:-1]) + 1, len(hour_years)]
    by = (groups(years), groups(months))
    runs = sample(n, seed, plant)
    weather = kernel.weather_terms(tdb, twb) if compiled else None
    out = {}
    for design in DESIGNS:
        acc = {}
        for p in runs + [central(plant)]:
            p = for_location(p, tdb)
            kw = mw * 1000 * p["utilization"]
            # the peak day and the record day: the same weather at the peak load, average load over the load factor (model 1.7)
            at_peak = {**p, "utilization": float(peak_utilization(p))}
            kw_peak = mw * 1000 * at_peak["utilization"]
            pue, w, c, r, cond, wp, cp, rp, condp, at_capacity, pue_peak = (kernel.hourly_run(tdb, twb, rh, weather, design, p, at_peak) if compiled else
                                                                             _hourly_run(tdb, twb, rh, design, p, at_peak, block))
            for name, arr in (("withdrawn", w), ("consumed", c), ("returned", r), ("condensate", cond)):
                s = daily_stats(day_index, len(uniq), years, arr, kw, months if name in ("withdrawn", "consumed") else None, by)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            for name, arr in (("withdrawn", wp), ("consumed", cp), ("returned", rp), ("condensate", condp)):
                s = daily_stats(day_index, len(uniq), years, arr, kw_peak, by=by)
                acc[f"{name}_peak_1in10"][-1], acc[f"{name}_record"][-1] = s["peak_1in10"], s["record"]
            # the upper case: every computer at capacity all day
            acc.setdefault("withdrawn_peak_full_capacity", []).append(daily_stats(day_index, len(uniq), years, at_capacity, mw * 1000.0, by=by)["peak_1in10"])
            # water use effectiveness: liters consumed per IT kWh (annual average), for comparison with LBNL/operators
            acc.setdefault("wue_l_per_kwh", []).append(float(np.average(c)) * 3.78541)          # consumed basis
            acc.setdefault("wue_makeup_l_per_kwh", []).append(float(np.average(w)) * 3.78541)   # LBNL/Lei basis (evaporation + drift + blowdown)
            acc.setdefault("utilization", []).append(p["utilization"])
            peak = float(np.quantile([part.max() for part in np.split(pue, year_ends[:-1])], 0.9))
            acc.setdefault("pue_avg", []).append(float(pue.mean()))
            acc.setdefault("power_mw_avg", []).append(float(pue.mean()) * mw * p["utilization"])
            acc.setdefault("pue_peak_1in10", []).append(peak)
            acc.setdefault("power_mw_peak_1in10", []).append(peak * mw)
            day_mw = np.bincount(day_index, weights=pue_peak * kw_peak / 1000.0, minlength=len(uniq)) / np.bincount(day_index, minlength=len(uniq))
            acc.setdefault("power_mw_peak_day_1in10", []).append(float(np.quantile([day_mw[g].max() for g in by[0]], 0.9)))
        res = {}
        for k, vals in acc.items():
            v = np.array(vals[:-1])
            res[k] = {"p10": float(np.quantile(v, 0.1)), "p50": float(np.quantile(v, 0.5)), "p90": float(np.quantile(v, 0.9)),
                      "central": float(vals[-1])}
        out[design] = res
    return out
