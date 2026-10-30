"""Cooling water model v2 for Water Ledger: weather-driven, literature-aligned, with uncertainty.

Hour by hour over 30 years of weather:
  heat rejected (BTU) = IT energy × heat factor, where the heat factor is seasonal: lower when a
      waterside economizer carries the load (cool wet-bulb), higher when chillers run (compressor heat
      can add up to ~20% to tower load; DOE FEMP).
  evaporation = heat × evaporative ratio ÷ latent heat, with the evaporative ratio from Rutberg et al. 2011
      (the dry-bulb relation USGS SIR 2013-5188 uses for cooling towers).
  drift = a small fraction of circulating flow (EPA WaterSense at Work §6.3: 0.05–0.2%, <0.005% with
      modern eliminators); circulating flow from heat ÷ (500 × range °F).
  blowdown = evaporation ÷ (cycles of concentration − 1)  (DOE FEMP BMP #10 water balance).
Designs differ in when they evaporate:
  dry       air-cooled / dry closed loop, designed to use no water for cooling: loop top-ups only, plus the staff water every design has
  assist    closed loop with evaporative assist only on the hottest hours (dry-bulb setpoint; Microsoft
            publishes 85 °F / 29.4 °C for its direct-air designs)
  hybrid    dry coolers most of the year, evaporative in warm weather (ramp between two dry-bulb setpoints)
  towers    open cooling towers, evaporative all year (upper bound for typical practice)
Outputs per run: withdrawn (makeup), consumed (evaporation + drift + loop top-up), returned to sewer (blowdown).
Monte Carlo over parameter ranges gives percentiles, per 100 MW of IT capacity.

Staff water (restrooms, kitchens, cleaning) is not per kWh: it follows the people on site, which grow slowly with size, so it
is a separate term, staff_runs() and staff_q(), added to the per-100 MW results at the campus's size (model 1.2). No humidification
is counted: the designs modeled cool with liquid loops, chillers or towers and recirculate indoor air, so outside air comes in only
for ventilation [estimate]; a direct outside-air design would need some in Michigan's dry winters and is not modeled.

Parameter ranges and their sources are in RANGES and documented on the Water Ledger methods page
(docs/research/water-ledger-methods-alignment.md).
"""
import numpy as np

from waterledger_models.datacenter.physics import (DESIGNS as _DESIGNS, HFG, KWH_BTU, LB_GAL, RANGES, STAFF, TOPUP, _ramp,  # noqa: F401
                                                   evaporative_ratio, hourly_rates, wet_bulb)

DESIGNS = list(_DESIGNS)
LABELS = {
    "dry": "Closed loop (designed to use no water for cooling)",
    "assist": "Closed loop with evaporative assist on the hottest days",
    "hybrid": "Hybrid: dry most of the year, evaporative in warm weather",
    "towers": "Cooling towers (evaporative all year)",
}


def hourly(tdb, twb, design, p):
    """Gallons per IT kWh, by hour: (withdrawn, consumed, returned). See physics.hourly_rates."""
    return hourly_rates(tdb, twb, design, p)


def sample(rng, n):
    runs = [{k: rng.uniform(*v) for k, v in RANGES.items()} for _ in range(n)]
    extra = np.random.default_rng(11)
    for r in runs:
        r["topup"] = extra.uniform(*TOPUP)
    return runs


def central():
    return {**{k: (a + b) / 2 for k, (a, b) in RANGES.items()}, "topup": sum(TOPUP) / 2}


STAFF_KEYS = ("core", "per_mw", "gpcd", "used", "maint_base", "maint_per_mw", "maint_used")


def staff_runs(n=200, seed=13):
    """Non-cooling water parameters per run, on their own stream: [core people, people per MW, gal per person a day, share used up,
    maintenance gal a day for the campus, maintenance gal a day per MW, maintenance share used up]."""
    rng = np.random.default_rng(seed)
    return [[float(rng.uniform(*STAFF[k])) for k in STAFF_KEYS] for _ in range(n)]


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


def daily_stats(day_index, ndays, years, gal_per_kwh_hour, kw, months=None):
    """From hourly gal/kWh and IT kW, compute daily MGD and summary statistics: average day, 1-in-10-year peak day (90th percentile
    of annual maxima), record day, average year, and with `months` (each day's YYYY-MM) the highest month's average day and the
    highest calendar year."""
    daily = np.bincount(day_index, weights=gal_per_kwh_hour * kw, minlength=ndays) / 1e6
    ann_max = np.array([daily[years == y].max() for y in np.unique(years)])
    out = {"avg": float(daily.mean()), "peak_1in10": float(np.quantile(ann_max, 0.9)), "record": float(daily.max()),
           "annual_mg": float(daily.mean() * 365.25)}
    if months is not None:
        out["max_month"] = float(max(daily[months == m].mean() for m in np.unique(months)))
        out["worst_year_mg"] = float(max(daily[years == y].sum() for y in np.unique(years)))
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


def daily(times, temps, rhs, design, mw, p=None):
    """One run's daily series at `mw` MW of IT capacity (central parameters by default), staff water at its central values included:
    (days, withdrawn MGD, returned MGD). For seasonal figures and record days; the pages and reviews use the Monte Carlo percentiles."""
    p = p or central()
    tdb, rh = np.array(temps, dtype=float), np.array(rhs, dtype=float)
    w, c, r = hourly(tdb, wet_bulb(tdb, rh), design, p)
    days = np.array([t[:10] for t in times])
    uniq, idx = np.unique(days, return_inverse=True)
    kw = mw * 1000 * p["utilization"]
    g, gu = _nc([sum(STAFF[k]) / 2 for k in STAFF_KEYS], mw)
    wd = np.bincount(idx, weights=w * kw, minlength=len(uniq)) / 1e6 + g
    rd = np.bincount(idx, weights=r * kw, minlength=len(uniq)) / 1e6 + g - gu
    return [str(d) for d in uniq], wd.tolist(), rd.tolist()


def run_location(times, temps, rhs, n=200, seed=7, mw=100.0):
    """Monte Carlo for every design at one location, per `mw` MW of IT capacity.

    Returns {design: {stat: {"p10","p50","p90"}}} for withdrawn/consumed/returned average, peak and annual,
    plus the central-parameter run. Peak = 1-in-10-year peak day (90th percentile of annual maxima).
    """
    tdb = np.array(temps, dtype=float)
    rh = np.array(rhs, dtype=float)
    twb = wet_bulb(tdb, rh)
    days = np.array([t[:10] for t in times])
    uniq, day_index = np.unique(days, return_inverse=True)
    years = np.array([d[:4] for d in uniq])
    months = np.array([d[:7] for d in uniq])
    rng = np.random.default_rng(seed)
    runs = sample(rng, n)
    out = {}
    for design in DESIGNS:
        acc = {}
        for p in runs + [central()]:
            kw = mw * 1000 * p["utilization"]
            w, c, r = hourly(tdb, twb, design, p)
            for name, arr in (("withdrawn", w), ("consumed", c), ("returned", r)):
                s = daily_stats(day_index, len(uniq), years, arr, kw, months if name == "withdrawn" else None)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            # water use effectiveness: liters consumed per IT kWh (annual average), for comparison with LBNL/operators
            acc.setdefault("wue_l_per_kwh", []).append(float(np.average(c)) * 3.78541)          # consumed basis
            acc.setdefault("wue_makeup_l_per_kwh", []).append(float(np.average(w)) * 3.78541)   # LBNL/Lei basis (evaporation + drift + blowdown)
            acc.setdefault("utilization", []).append(p["utilization"])
        res = {}
        for k, vals in acc.items():
            v = np.array(vals[:-1])
            res[k] = {"p10": float(np.quantile(v, 0.1)), "p50": float(np.quantile(v, 0.5)), "p90": float(np.quantile(v, 0.9)),
                      "central": float(vals[-1])}
        out[design] = res
    return out
