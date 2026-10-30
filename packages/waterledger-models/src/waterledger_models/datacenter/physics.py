"""The data center cooling model's physics and parameter ranges, in one place, vectorized.

Hour by hour, electricity and water from one heat balance (model 1.4), after Lei and Masanet (2022; preprint rs-769999/v1, Eqs. 2-4):
facility power = IT + UPS and distribution losses + lighting + air handler fans + chillers + pumps + heat rejection fans, with the
economizer carrying as much of the load as the weather allows; heat rejected = the load + chiller power; evaporation = heat x the
Rutberg et al. (2011) evaporative ratio / latent heat; drift = a share of circulating flow; blowdown = evaporation / (cycles of
concentration - 1); closed loops add small top-ups; staff water follows the people on site. Designs differ in when they evaporate (dry, assist, hybrid, towers); assist evaporates into the air ahead of a dry cooler. The method and sources are
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
    # Dry coolers with adiabatic pre-cooling (model 1.3; on Michigan's detailed calculator only). Turns on at a switch point no maker publishes, since it is a
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
# Electricity and heat (model 1.4), on their own random stream. Large-scale values are Lei and Masanet's Table 3, case 2 (preprint rs-769999/v1;
# waterside economizer, 2.8-6.7 C tower approach, and so on), which LBNL 2024 also draws on, unless noted.
POWER = {
    "ups": (0.90, 0.99), "dist_loss": (0.0, 0.02), "light": (0.0, 0.002), "shr": (0.95, 0.99),
    "supply_air": (27.0, 35.0), "air_rise": (13.9, 19.4), "coil_eff": (0.70, 0.90), "water_rise": (5.0, 10.0),
    "crah_pa": (300.0, 700.0), "fan_eff": (0.65, 0.90),
    "tower_fan_pa": (100.0, 400.0), "lg": (0.2, 4.0), "tower_approach": (2.8, 6.7), "hx_approach": (1.7, 2.8),
    "pump_chw_kpa": (114.9, 172.4), "pump_tower_kpa": (166.9, 250.4), "pump_econ_kpa": (114.9, 172.4), "pump_eff": (0.60, 0.80),
    # Chillers as a fraction of Carnot COP. Water-cooled: 0.70 from code minimums for large plant (0.560 kW/ton gives 0.72, 0.585 gives 0.69; WAC
    # 51-11C-403323, a stated replica of ASHRAE 90.1 Table 6.8.1-3; its part-load adjustment gives 0.67-0.73), +/-11% (Lei and Masanet's COP error).
    # Air-cooled: 0.45 from EER 10.1, 0.55 [A]. Both are fitted together with the temperature offsets below (2 K, 2 K, 12 K) [A].
    "carnot_water": (0.62, 0.78), "carnot_air": (0.45, 0.55),
    # Dry coolers. No standard or peer-reviewed design values exist, since selection data are proprietary, so these are assumptions tested in the
    # sensitivity analysis [A]: approach, a catalogue point of 10 K (ThermoKey) to the 5 K makers quote for larger coils; air-side pressure and
    # efficiency by analogy with Lei and Masanet's tower fans. The air rise is ADIABATIC's selection-sheet range.
    "dc_approach": (5.0, 10.0), "dc_fan_pa": (100.0, 250.0),
    # Liquid-cooled computers: facility water at ASHRAE TC 9.9 classes W32-W45 (LBNL 2024 Table 4.3: W45), the rest of the heat by air on a cooler
    # loop: 12.9% (HPE GB200 NVL72), 20% (Schneider WP210), 25-39% (ASME InterPACK2022, not read directly); 10-30% [A]. The share of computers
    # that are liquid-cooled at a campus is not published for any fleet, so all of 0-1 is sampled [A].
    "liquid_water": (32.0, 45.0), "liquid_air_share": (0.10, 0.30), "liquid_share": (0.0, 1.0),
}
PARAMETERS = tuple(RANGES) + ("topup",) + tuple(ADIABATIC) + tuple(POWER)

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


CHILLER_COP_CAP = {"water": 8.0, "air": 5.0}          # FEMP's 5-8 for water-cooled; air-cooled part-load code minimums reach about 4.1-4.7 [A]
CP_AIR, CP_WATER, RHO_AIR, RHO_WATER = 1.01, 4.2, 1.15, 1000.0     # kJ/kg/K, kg/m3


def _fan_kw(kg_s, pa, eff):
    return kg_s / RHO_AIR * pa / eff / 1000.0


def _pump_kw(kg_s, kpa, eff):
    return kpa * kg_s / (RHO_WATER * eff)


def _wet_share(tdb, design, p):
    """Share of the heat going through evaporation: all of it for towers, none for dry and assist coils, a ramp for hybrid."""
    if design == "towers":
        return np.ones_like(tdb)
    if design == "hybrid":
        return _ramp(tdb, p["hybrid_on"], p["hybrid_full"]) * np.ones_like(tdb)
    return np.zeros_like(tdb)


def _loop(load, supply, tdb, twb, coil_air, wet, design, p):
    """One facility water loop carrying `load` (kW per IT kW) at `supply` C: chiller, pump and heat rejection power, kW per IT kW."""
    ret = supply + p["water_rise"]
    outside = wet * (twb + p["tower_approach"] + p["hx_approach"]) + (1 - wet) * (coil_air + p["dc_approach"])
    free = _ramp(ret - outside, 0.0, ret - supply)                # Lei and Masanet: the economizer's share falls from 1 to 0 as outside approaches the return
    chilled = load * (1 - free)
    evaporator = supply - 2.0
    if design in ("towers", "hybrid"):
        condenser = twb + p["tower_approach"] + p["range_f"] / 1.8 + 2.0
        eta, cap = p["carnot_water"], CHILLER_COP_CAP["water"]
    else:                                                          # an air-cooled trim chiller, whose rated COP includes its condenser fans
        condenser = coil_air + 12.0
        eta, cap = p["carnot_air"], CHILLER_COP_CAP["air"]
    cop = np.minimum(eta * (evaporator + 273.15) / np.maximum(condenser - evaporator, 1.0), cap)
    chiller = chilled / cop
    pumps = (_pump_kw(load * free / (CP_WATER * p["water_rise"]), p["pump_econ_kpa"], p["pump_eff"])
             + _pump_kw(chilled / (CP_WATER * p["water_rise"]), p["pump_chw_kpa"], p["pump_eff"]))
    heat = load + chiller
    tower_water = heat * wet / (CP_WATER * p["range_f"] / 1.8)
    tower = _pump_kw(tower_water, p["pump_tower_kpa"], p["pump_eff"]) + _fan_kw(tower_water / p["lg"], p["tower_fan_pa"], p["fan_eff"])
    # dry cooler fans: the air flow that carries the economizer's heat, up to design flow, by the fan affinity law (cubic; 10% floor, immaterial)
    design_flow = load / (CP_AIR * p["assist_dt_air"])
    rise = np.maximum(ret - p["dc_approach"] - coil_air, p["assist_dt_air"])
    flow = load * free * (1 - wet) / (CP_AIR * rise)
    dry = _fan_kw(design_flow, p["dc_fan_pa"], p["fan_eff"]) * np.clip(flow / np.maximum(design_flow, 1e-12), 0.1, 1.0) ** 3
    return chiller, pumps + tower + (0.0 if design == "towers" else dry)


def hourly_heat_power(tdb, twb, design, p):
    """Each hour, per kW of IT: (facility power, kW; heat rejected, kW). Facility power over IT power is the hour's PUE.

    After Lei and Masanet's Eqs. 2-4, with two departures: air handler fan heat is counted in the load, so the energy balance closes, and
    dry cooler and liquid cooling designs are added, which their cases do not have. p as in hourly_rates."""
    q = 1.0 + (1.0 / p["ups"] - 1.0) + (1.0 / (1.0 - p["dist_loss"]) - 1.0) + p["light"]
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    crah = _fan_kw(q * air / (CP_AIR * p["air_rise"]), p["crah_pa"], p["fan_eff"])
    load = (q + crah) / p["shr"]
    # supply air and the coil set the air loop's water temperature (Lei and Masanet); liquid-cooled heat goes to a warmer loop of its own
    air_water = p["supply_air"] + p["air_rise"] - p["air_rise"] / p["coil_eff"]
    coil_air = tdb - (p["assist_eff"] * np.maximum(tdb - twb, 0.0) * (tdb >= p["assist_on"]) if design == "assist" else 0.0)
    wet = _wet_share(tdb, design, p)
    power, heat = q + crah + 0.0 * tdb, load + 0.0 * tdb
    for share, supply in ((air, air_water), (1.0 - air, p["liquid_water"])):
        chiller, other = _loop(load * share, supply, tdb, twb, coil_air, wet, design, p)
        power, heat = power + chiller + other, heat + chiller
    return power, heat


def hourly_rates(tdb, twb, design, p):
    """Gallons per IT kWh for each hour: (withdrawn, consumed, returned).

    tdb, twb: dry- and wet-bulb temperature (C), shape (hours,). p: parameter dict whose values are scalars or arrays
    shaped (runs, 1). Withdrawn always equals consumed plus returned.
    """
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    btu = KWH_BTU * hourly_heat_power(tdb, twb, design, p)[1]
    evap_full = btu * evaporative_ratio(tdb, p["er_adj"]) / HFG / LB_GAL
    circ = btu / (LB_GAL * p["range_f"])                    # gal circulated per kWh
    w = _wet_share(tdb, design, p) * np.ones_like(evap_full)
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
    u = np.random.default_rng(23).random((n, len(POWER)))
    for i, (k, (a, b)) in enumerate(POWER.items()):
        out[k] = a + (b - a) * u[:, i]
    return out


def central_parameters():
    """Every parameter at the middle of its range."""
    return {**{k: (a + b) / 2 for k, (a, b) in {**RANGES, **ADIABATIC, **POWER}.items()}, "topup": sum(TOPUP) / 2}


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
