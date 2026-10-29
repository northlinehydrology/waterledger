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

KWH_BTU = 3412.14
HFG = 1050.0          # latent heat near tower temperatures, BTU/lb
LB_GAL = 8.34
DESIGNS = ["dry", "assist", "hybrid", "towers"]
LABELS = {
    "dry": "Closed loop (designed to use no water for cooling)",
    "assist": "Closed loop with evaporative assist on the hottest days",
    "hybrid": "Hybrid: dry most of the year, evaporative in warm weather",
    "towers": "Cooling towers (evaporative all year)",
}

# (low, high) uniform ranges sampled in the Monte Carlo; central values are the midpoints.
RANGES = {
    "utilization": (0.60, 0.90),       # average IT load ÷ IT capacity [estimate]
    "hf_econ": (1.03, 1.08),           # heat factor with economizer cooling (pumps, fans, losses) [estimate]
    "hf_chiller": (1.15, 1.25),        # heat factor with chillers running; compressor heat up to ~20% (DOE FEMP)
    "wb_econ": (8.0, 12.0),            # wet-bulb (°C) below which the economizer carries the load [estimate]
    "wb_chiller": (16.0, 20.0),        # wet-bulb (°C) above which chillers carry the load [estimate]
    "er_adj": (-0.05, 0.05),           # uncertainty on the Rutberg evaporative ratio (USGS ±5–15% at baseload)
    "coc": (3.0, 7.0),                 # cycles of concentration (DOE FEMP: 2–4 typical, 6+ possible)
    "range_f": (8.0, 15.0),            # tower range, °F (USGS SIR 2013-5188 tower suite: 10–25)
    "drift": (0.00005, 0.0005),        # drift fraction of circulating flow (EPA: <0.005% modern to 0.05%)
    "fill_gal_per_mw": (2000.0, 6000.0),  # closed loop volume, gal per MW of IT capacity [estimate; Lowell reported a 1.2 million gallon fill]
    "assist_on": (27.5, 31.0),         # dry-bulb °C where assist starts (Microsoft 85 °F = 29.4 °C)
    "assist_share": (0.10, 0.30),      # assist water as a share of the full evaporative rate [estimate]
    "hybrid_on": (21.0, 27.0),         # dry-bulb °C where hybrid starts evaporating [estimate; cold-climate variant]
    "hybrid_full": (30.0, 33.0),       # dry-bulb °C where hybrid is fully evaporative [estimate]
}
# Share of the loop volume lost to small leaks and topped up each year (NIH 2023: closed loops typically lose under 5% a year), all of
# it counted as lost. Sampled on its own random stream (where model 1.1 drew its base-use share), so the other draws are unchanged.
TOPUP = (0.01, 0.05)

# Staff water [estimates]. People on site on a typical day (employees, security, contractors) = a fixed core plus a little per MW of
# IT capacity: Michigan's sales tax exemption needs at least 30 new jobs, and hyperscale campuses employ tens to a few hundred people.
# Gallons per person per day covers restrooms, kitchens and cleaning (office buildings use about 10 to 20; more with a cafeteria).
# About 10% of it is used up and the rest goes down the drain (USGS Great Lakes consumptive-use coefficients for commercial use).
STAFF = {"core": (20.0, 60.0), "per_mw": (0.1, 0.5), "gpcd": (15.0, 30.0), "used": (0.05, 0.15)}


def wet_bulb(t_c, rh):
    """Stull (2011) wet-bulb approximation, °C, valid for RH 5–99% and typical temperatures."""
    rh = np.clip(rh, 5, 99)
    return (t_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659)) + np.arctan(t_c + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * np.arctan(0.023101 * rh) - 4.686035)


def evaporative_ratio(t_c, adj=0.0):
    """Rutberg et al. 2011 dry-bulb relation (as used in USGS SIR 2013-5188): share of heat rejected by evaporation."""
    er = 1 - (-0.000279 * t_c ** 3 + 0.00109 * t_c ** 2 - 0.345 * t_c + 26.7) / 100
    return np.clip(er + adj, 0.55, 1.0)


def _ramp(x, lo, hi):
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def hourly(tdb, twb, design, p):
    """Gallons per IT kWh, by hour: (withdrawn, consumed, returned)."""
    hf = p["hf_econ"] + (p["hf_chiller"] - p["hf_econ"]) * _ramp(twb, p["wb_econ"], p["wb_chiller"])
    btu = KWH_BTU * hf
    evap_full = btu * evaporative_ratio(tdb, p["er_adj"]) / HFG / LB_GAL
    circ = btu / (LB_GAL * p["range_f"])                    # gal circulated per kWh (BTU / (8.34 × range))
    if design == "towers":
        w = np.ones_like(tdb)
    elif design == "hybrid":
        w = _ramp(tdb, p["hybrid_on"], p["hybrid_full"])
    elif design == "assist":
        w = _ramp(tdb, p["assist_on"], p["assist_on"] + 4.0) * p["assist_share"]
    else:
        w = np.zeros_like(tdb)
    evap = evap_full * w
    drift = circ * p["drift"] * (w > 0)
    blow = evap / (p["coc"] - 1.0)
    topup = np.full_like(tdb, p["fill_gal_per_mw"] * p["topup"] / 365.0 / (24 * 1000 * p["utilization"]))   # gal/day per MW, as gal per IT kWh
    withdrawn = evap + drift + blow + topup
    consumed = evap + drift + topup
    returned = blow
    return withdrawn, consumed, returned


def sample(rng, n):
    runs = [{k: rng.uniform(*v) for k, v in RANGES.items()} for _ in range(n)]
    extra = np.random.default_rng(11)
    for r in runs:
        r["topup"] = extra.uniform(*TOPUP)
    return runs


def central():
    return {**{k: (a + b) / 2 for k, (a, b) in RANGES.items()}, "topup": sum(TOPUP) / 2}


def staff_runs(n=200, seed=13):
    """Staff water parameters per run, [core people, people per MW, gal per person a day, share used up], on their own stream."""
    rng = np.random.default_rng(seed)
    return [[float(rng.uniform(*STAFF[k])) for k in ("core", "per_mw", "gpcd", "used")] for _ in range(n)]


def staff_q(runs, mw):
    """Staff water at `mw` MW of IT capacity, MGD: {"withdrawn"|"consumed"|"returned": {"p10","p50","p90"}}. Same as WQ.staff on the page."""
    g = np.array([(c + k * mw) * gpcd / 1e6 for c, k, gpcd, u in runs])
    u = np.array([r[3] for r in runs])
    q = lambda v: {"p10": float(np.quantile(v, 0.1)), "p50": float(np.quantile(v, 0.5)), "p90": float(np.quantile(v, 0.9))}
    return {"withdrawn": q(g), "consumed": q(g * u), "returned": q(g * (1 - u))}


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
    core, per_mw, gpcd, used = (sum(STAFF[k]) / 2 for k in ("core", "per_mw", "gpcd", "used"))
    g = (core + per_mw * mw) * gpcd / 1e6
    wd = np.bincount(idx, weights=w * kw, minlength=len(uniq)) / 1e6 + g
    rd = np.bincount(idx, weights=r * kw, minlength=len(uniq)) / 1e6 + g * (1 - used)
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
