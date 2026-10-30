"""The data center cooling model's physics and parameter ranges, in one place, vectorized.

Hour by hour: heat rejected = IT energy x a heat factor that ramps with wet-bulb temperature from economizer to chiller
operation; evaporation = heat x the Rutberg et al. (2011) evaporative ratio / latent heat; drift = a share of circulating
flow; blowdown = evaporation / (cycles of concentration - 1); closed loops add small top-ups; staff water follows the
people on site. Designs differ in when they evaporate (dry, assist, hybrid, towers); assist evaporates into the air ahead of a dry cooler. The method and sources are
described in cooling.py and on the Water Ledger methods page.

Every function takes parameters as scalars or as arrays shaped (runs, 1) against hourly weather shaped (hours,), giving
(runs, hours). cooling.py (the per-run loop Water Ledger's builders use) and ensemble.py (xarray ensembles) both use
these functions and ranges, so the two cannot drift apart.
"""
import numpy as np

KWH_BTU = 3412.14
HFG = 1050.0          # latent heat near tower temperatures, BTU/lb
LB_GAL = 8.34
GAL_M3 = 264.172       # gallons per cubic meter
DESIGNS = ("dry", "assist", "hybrid", "towers")

# (low, high) uniform ranges sampled in the Monte Carlo; central values are the midpoints.
RANGES = {
    # average IT draw ÷ IT capacity at full build-out (model 1.3; was 0.60-0.90). EPRI 2026 measured 75% of nameplate at a large hyperscale
    # site and 57% at co-location sites; IEA 2025 puts hyperscale at 53-56%; LBNL's server parameters give about 40% (AI inference) to 60%
    # (AI training). Load over a site's own peak (EPRI: 88-94%) is a different ratio and does not bound this one.
    "utilization": (0.50, 0.80),
    # Heat rejected per unit of IT energy (model 1.3, derived; no published value). Economizer: IT plus fans, UPS and distribution
    # losses. Lei and Masanet's Table 3 (Research Square preprint rs-769999/v1, 2021; large-scale cases: UPS 90-99%, also LBNL 2024
    # Table 4.3; distribution 0-2%; CRAH fans 1.4-9.2% of IT at its pressure, efficiency and air temperature ranges) gives 1.02-1.22 with
    # every term at one end. All of them at the bad end is not a large new campus: heat through the water loop cannot exceed the
    # facility's overhead, and large campuses measure 1.09 (Google 2025) to 1.14 (IEA 2025) with cooling included (LBNL 2024: about 1.12 with
    # towers), so the top is 1.10. Chillers: plus compressor heat, "up to 20% of the total heat" (DOE FEMP, cooling water efficiency for
    # data centers); COP 5-8 gives 1.13-1.20 over IT.
    "hf_econ": (1.03, 1.10),
    "hf_chiller": (1.15, 1.25),
    # Wet-bulb (°C) limits of economizer and chiller operation (model 1.3, derived; no published value): chilled-water supply 12.8-18 °C
    # (FEMP Data Center Design guide 2024, p. 17: 55 °F or higher) less the tower (2.8-6.7 °C) and heat exchanger (1.7-2.8 °C) approaches
    # (Lei and Masanet preprint, Table 3) gives 3.3-13.5 °C for full economizer; the return (supply plus a 5-10 °C rise) less the approaches
    # gives 8.3-23.5 °C for full chiller operation. FEMP (p. 19): economizers suit climates below 55 °F (12.8 °C) wet-bulb 3,000+ h a year.
    # The two ranges are split at their midpoints so every draw ramps upward.
    "wb_econ": (5.0, 12.0),
    "wb_chiller": (14.0, 22.0),
    # Evaporative ratio adjustment (model 1.3, was +/-0.05): asymmetric because Rutberg et al.'s fit (Poppe runs at 40 °C inlet water,
    # RH 60%) is applied hourly to cooler data center tower water and cold hours, where it likely runs high; USGS SIR 2013-5188 (Diehl
    # et al.) puts tower evaporation error at +/-5-15% (p. 24) and +/-18% overall (pp. 28-29).
    "er_adj": (-0.10, 0.05),
    "coc": (3.0, 7.0),                 # cycles of concentration: DOE FEMP BMP #10, two to four typical, six or more possible
    "range_f": (7.0, 15.0),            # tower range, °F (model 1.3, was 8-15): Lei and Masanet preprint, Table 3, 4-6 °C (7.2-10.8 °F); 10 °F rating
    # Drift as a share of circulating flow (model 1.3, was 0.005-0.05%): modern eliminators under 0.005% (EPA WaterSense at Work 2012,
    # section 6.3, p. 6-9) to EPA AP-42 13.4's induced-draft 0.020% (Table 13.4-1).
    "drift": (0.000005, 0.0002),
    # Closed loop volume, gal per MW of IT capacity (model 1.3, was 2,000-6,000): Crusoe (2026) 1.7 million gal for a 200 MW building
    # (8,500); Vantage Port Washington about 11.8 million gal for about 1 GW (about 12,000); chilled-water loops of 3-10 gal per ton
    # (850-2,840 per MW of heat) at the low end.
    "fill_gal_per_mw": (2000.0, 12000.0),
    # Dry coolers with adiabatic pre-cooling (model 1.3; not shown on the pages). Turns on at a switch point no maker publishes, since it is a
    # selection and control output (EVAPCO 2018, p. 2): Uptime Institute (2025) reports 20 °C or higher; 30 °C is the top [A]. Microsoft's
    # 85 °F is for its direct-air evaporative design, a different system, and is no longer used here. Pad saturation effectiveness: EVAPCO
    # (2018, p. 2) measured 72-78% at 400-700 fpm across 10 pads; ASHRAE (2016, ch. 41) gives 70 to over 95% for rigid media.
    "assist_on": (20.0, 30.0),
    "assist_eff": (0.70, 0.80),
    # Hybrid dry coolers: wet mode from a customer-set switch point, 70-95 °F (21-35 °C) in US 12,426,214 B1 (2025), 82 °F (27.8 °C)
    # in its example (model 1.3, was 21-27); fully evaporative near the site's design dry-bulb [estimate, no published value].
    "hybrid_on": (21.0, 28.0),
    "hybrid_full": (30.0, 33.0),
}
# Share of the loop volume lost to small leaks and topped up each year (NIH 2023 Technical Bulletin: "typically less than 5% of the
# system's total volume in a year"; the 1% floor is an assumption), all of it counted as lost. Poorly kept loops can lose far more (NIH:
# 25% a month "is not uncommon"), which the range does not cover. Sampled on its own random stream (where model 1.1 drew its base-use share), so the other draws are unchanged.
TOPUP = (0.01, 0.05)
# Adiabatic pre-cooling, on their own random stream so the other draws are unchanged. Air temperature rise across the dry cooler coil at
# design, K: 9-13 from makers' selection sheets (Thermokey 11.2, Kelvion 12.8) [estimate]. Bleed as a share of evaporation: none for once-through
# pads (Guentner; Spinazzola 2021), up to 0.5 for recirculating pads (SCE ET13SCE1020, 2015, p. 29: 10-50%; ASHRAE 2016 ch. 41 allows 5-100%).
ADIABATIC = {"assist_dt_air": (9.0, 13.0), "assist_bleed": (0.0, 0.5)}
PARAMETERS = tuple(RANGES) + ("topup",) + tuple(ADIABATIC)

# Staff water. People = the campus's permanent headcount (employees and on-site contractors), a fixed core plus a share per MW of IT
# capacity: JLARC 2024 puts a typical building at about 50 full-time workers; announced campuses run 0.1 to 0.5 jobs per MW (Meta Richland
# Parish 0.1, Meta El Paso and Saline Township about 0.3, Gilroy 0.5). Gallons are per person per calendar day (model 1.3; was 15-30 with
# no source): EPA 2002 Table 3-4 gives 7-16 (13 typical) per office or industrial employee per workday, about 9 per calendar day; Michigan's
# septic design criteria give 35 per factory worker per shift, and Gilroy's applicant 1,800 gpd for about 50 employees (about 30). About
# 10% is used up (Shaffer and Runkle 2007, Table 9: commercial, Great Lakes Basin, median 10%, quartiles 8-15%); the rest goes to the sewer.
# Maintenance and other non-cooling water (model 1.3): equipment and floor washdown, janitorial and fire-system testing, loop flushing,
# a campus base plus a little per MW, bracketed by applicant projections rather than measured (none published): Hermantown, MN (Google;
# loop maintenance about 2,000 gal per building a month) at the low end, Crusoe's 200 MW building (about 2 million gal a year for
# restrooms, kitchens, maintenance and washdown, less its staff water) at the high end; checked against Microsoft at Tyrone, GA (2,000
# gpd per building), Saline Township (about 20,000 gpd for 1.4 GW) and Mount Pleasant, WI. Mostly to the sewer: 3-15% used up (USGS
# commercial coefficients). Landscape irrigation is site- and climate-specific and is not included. Gallons a day.
STAFF = {"core": (20.0, 60.0), "per_mw": (0.1, 0.5), "gpcd": (10.0, 30.0), "used": (0.05, 0.15),
         "maint_base": (0.0, 2000.0), "maint_per_mw": (2.0, 20.0), "maint_used": (0.03, 0.15)}
STAFF_PARAMETERS = tuple(f"staff_{k}" for k in STAFF)


def wet_bulb(t_c, rh):
    """Stull (2011) wet-bulb approximation, C. Stated for RH 5-99% and -20 to 50 C; least accurate in cold, very dry
    air (it can exceed the dry-bulb by up to ~0.9 C at -20 C and 10% RH), where it only nudges the heat factor."""
    rh = np.clip(rh, 5, 99)
    return (t_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659)) + np.arctan(t_c + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * np.arctan(0.023101 * rh) - 4.686035)


def evaporative_ratio(t_c, adj=0.0):
    """Share of heat rejected by evaporation (Rutberg et al. 2011 dry-bulb relation, as in USGS SIR 2013-5188)."""
    er = 1 - (-0.000279 * t_c ** 3 + 0.00109 * t_c ** 2 - 0.345 * t_c + 26.7) / 100
    return np.clip(er + adj, 0.55, 1.0)


def _ramp(x, lo, hi):
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def hourly_rates(tdb, twb, design, p):
    """Gallons per IT kWh for each hour: (withdrawn, consumed, returned).

    tdb, twb: dry- and wet-bulb temperature (C), shape (hours,). p: parameter dict whose values are scalars or arrays
    shaped (runs, 1). Withdrawn always equals consumed plus returned.
    """
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    hf = p["hf_econ"] + (p["hf_chiller"] - p["hf_econ"]) * _ramp(twb, p["wb_econ"], p["wb_chiller"])
    btu = KWH_BTU * hf
    evap_full = btu * evaporative_ratio(tdb, p["er_adj"]) / HFG / LB_GAL
    circ = btu / (LB_GAL * p["range_f"])                    # gal circulated per kWh
    if design == "towers":
        w = np.ones_like(evap_full)
    elif design == "hybrid":
        w = _ramp(tdb, p["hybrid_on"], p["hybrid_full"]) * np.ones_like(evap_full)
    else:
        w = np.zeros_like(evap_full)
    evap = evap_full * w
    drift = circ * p["drift"] * (w > 0)
    blow = evap / (p["coc"] - 1.0)
    if design == "assist":
        # Water evaporated into the air ahead of the coil. The air cools by depr = effectiveness x wet-bulb depression; the fans slow until
        # it leaves the coil where it would at the switch point (on + rise), so air flow = heat / (cp x (on + rise - tdb + depr)), and
        # evaporation as a share of all the heat is depr over that same difference, at most 1. Pads have no tower drift.
        depr = p["assist_eff"] * np.maximum(tdb - twb, 0.0)
        share = np.clip(depr / np.maximum(p["assist_on"] + p["assist_dt_air"] - tdb + depr, 1e-6), 0.0, 1.0)
        evap = btu * share / HFG / LB_GAL * (tdb >= p["assist_on"])
        drift = np.zeros_like(evap)
        blow = evap * p["assist_bleed"]
    # loop top-up, gal/day per MW of capacity, as gal per IT kWh
    topup = p["fill_gal_per_mw"] * p["topup"] / 365.0 / (24 * 1000 * p["utilization"]) * np.ones_like(evap_full)
    withdrawn = evap + drift + blow + topup
    consumed = evap + drift + topup
    returned = blow
    return withdrawn, consumed, returned


def sample_parameters(n=200, seed=7):
    """Monte Carlo draws: independent uniforms over RANGES (run-major, so the draws match a per-run loop of
    rng.uniform calls) and topup from its own stream. Returns {name: array (n,)}."""
    lo = np.array([v[0] for v in RANGES.values()])
    hi = np.array([v[1] for v in RANGES.values()])
    u = np.random.default_rng(seed).random((n, len(RANGES)))
    draws = lo + (hi - lo) * u
    out = {k: draws[:, i] for i, k in enumerate(RANGES)}
    out["topup"] = TOPUP[0] + (TOPUP[1] - TOPUP[0]) * np.random.default_rng(11).random(n)
    u = np.random.default_rng(17).random((n, len(ADIABATIC)))
    for i, (k, (a, b)) in enumerate(ADIABATIC.items()):
        out[k] = a + (b - a) * u[:, i]
    return out


def central_parameters():
    """Every parameter at the middle of its range."""
    return {**{k: (a + b) / 2 for k, (a, b) in {**RANGES, **ADIABATIC}.items()}, "topup": sum(TOPUP) / 2}


def sample_staff(n=200, seed=13):
    """Monte Carlo draws of the staff water parameters on their own stream (run-major, as Water Ledger's
    staff_runs): {"staff_core", "staff_per_mw", "staff_gpcd", "staff_used": array (n,)}."""
    lo = np.array([v[0] for v in STAFF.values()])
    hi = np.array([v[1] for v in STAFF.values()])
    draws = lo + (hi - lo) * np.random.default_rng(seed).random((n, len(STAFF)))
    return {k: draws[:, i] for i, k in enumerate(STAFF_PARAMETERS)}


def central_staff():
    """Staff water parameters at the middle of their ranges."""
    return {f"staff_{k}": (a + b) / 2 for k, (a, b) in STAFF.items()}


def staff_water(s, mw):
    """Non-cooling water at `mw` MW of IT capacity, million gallons per day: (withdrawn, consumed, returned): staff water plus
    maintenance (absent maintenance keys count as none). s holds the parameters (scalars or arrays, as from sample_staff or
    central_staff)."""
    g = (s["staff_core"] + s["staff_per_mw"] * mw) * s["staff_gpcd"] / 1e6
    m = (s.get("staff_maint_base", 0.0) + s.get("staff_maint_per_mw", 0.0) * mw) / 1e6
    used = g * s["staff_used"] + m * s.get("staff_maint_used", 0.0)
    return g + m, used, g + m - used
