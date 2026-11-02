"""The data center cooling model's physics and parameter ranges, in one place, vectorized.

Hour by hour, electricity and water from one heat balance (model 1.5), after Lei and Masanet (2022; preprint rs-769999/v1, Eqs. 2-4):
facility power = IT + UPS and distribution losses + lighting + air handler fans + chillers + pumps + heat rejection fans, with the
economizer carrying as much of the load as the weather allows. Energy closes: that power becomes heat, outside air brings or takes away a
little more, and heat rejected through the water or coil = the two together less the heat rejection fans, whose heat goes straight to the exhaust air. Evaporation = heat x the
wet share x the Rutberg et al. (2011) evaporative ratio / latent heat; drift = a share of the flow through the wet part. Mass closes:
makeup = evaporation + drift + blowdown, condensate from the outside air joins what goes back, and the dissolved solids balance (makeup x solids = (blowdown + drift) x cycles x solids) gives
blowdown + drift = evaporation / (cycles of concentration - 1). Closed loops add small top-ups; staff water follows the people on site. Designs differ in when they evaporate (dry, assist, hybrid, towers); assist evaporates into the air ahead of a dry cooler. The method and sources are
described in cooling.py and on the Water Ledger methods page.

Every function takes parameters as scalars or as arrays shaped (runs, 1) against hourly weather shaped (hours,), giving
(runs, hours). cooling.py (the per-run loop Water Ledger's builders use) and ensemble.py (xarray ensembles) both use
these functions and ranges, so the two cannot drift apart.
"""
import zlib

import numpy as np

KWH_BTU = 3412.14
LATENT_KJ = 2450.0     # latent heat of water, kJ/kg, near the coil and hall
CFM_M3S = 0.000471947  # m3/s per cfm
KG_GAL = 3.78541       # kg of water per gallon
HFG = 1050.0          # latent heat near tower temperatures, BTU/lb
LB_GAL = 8.34
GAL_M3 = 264.172       # gallons per cubic meter
DESIGNS = ("dry", "assist", "hybrid", "towers")

# (low, high) ranges sampled in the Monte Carlo (sample_parameters: Latin hypercube, uniform in each range); central values are the midpoints.
RANGES = {
    # average IT draw ÷ IT capacity at full build-out (model 1.3; was 0.60-0.90). EPRI 2026 measured 75% of nameplate at a large hyperscale
    # site and 57% at co-location sites; IEA 2025 puts hyperscale at 53-56%; LBNL's server parameters give about 40% (AI inference) to 60%
    # (AI training). Load over a site's own peak (EPRI: 88-94%) is a different ratio and does not bound this one.
    "utilization": (0.50, 0.80),
    # Load factor, a site's average load over its own peak load (model 1.7): EPRI 2026 measured 94% at a large hyperscale site and 88% at co-location sites. The peak day
    # runs at utilization / load factor (peak_utilization): EPRI's own pairs give 0.75 / 0.94 = 0.80 and 0.57 / 0.88 = 0.65. Every computer at capacity all day is the upper case.
    "load_factor": (0.88, 0.94),
    # Evaporative ratio adjustment (model 1.3, was +/-0.05): asymmetric because Rutberg et al.'s fit (Poppe runs at 40 °C inlet water,
    # RH 60%) is applied hourly to cooler data center tower water and cold hours, where it likely runs high. USGS SIR 2013-5188 (Diehl et al.): +/-5-15% for the
    # Leung and Moore method (p. 24); 15% added to the modeled tower suite (p. 28); +/-18% for towers is consumption with the error in heat included (p. 29), and
    # USGS's 18% for the evaporative ratio itself is for water surfaces. LBNL and Lei and Masanet evaporate all the heat; this ratio is the model's stated departure.
    "er_adj": (-0.10, 0.05),
    # Cycles of concentration, about 3-6 (model 1.7, was 3-7). Lei and Masanet's Table 3, case 2, allows 3-15; the consumptive ratios Han et al. (2026, Table 2) report
    # for operators, 0.72-0.91, are about 3.6-11 cycles, median about 4.5; ICPRB's 75% is 4. DOE FEMP BMP #10's typical range is lower, two to four, with six or more
    # possible. Nothing is published for large campuses, and source water sets the real limit, so 3-6 is the part of the operators' values that is common practice [A].
    "coc": (3.0, 6.0),
    "range_f": (7.2, 10.8),            # tower range, °F (model 1.7, was 7-15, whose top had no source): Lei and Masanet preprint, Table 3, 4-6 °C; the 10 °F rating sits inside it
    # Drift as a share of circulating flow (model 1.7, was 0.0005-0.02%, whose low end was ten times under the source): modern eliminators at 0.005% (EPA WaterSense at
    # Work 2012, section 6.3, p. 6-9: less than 0.005%; the end of Lei and Masanet's Table 3) to EPA AP-42 13.4's induced-draft 0.020% (Table 13.4-1).
    "drift": (0.00005, 0.0002),
    # Closed loop volume, gal per MW of IT capacity (model 1.3, was 2,000-6,000): Crusoe (2026) about 1.7 million gal for a typical system, which is 8,500 if that is
    # its 200 MW building, as its figure suggests; chilled-water loops of 3-10 gal per ton (850-2,840 per MW of heat), not read directly, at the low end. The top is
    # that 8,500 and a margin, for lack of a filing that states a volume and a capacity together [A]. Vantage's 11.8 million gal, used until model 1.7, is out: it was a
    # TV tour of its Sterling, Virginia site, not Port Washington, with no capacity given.
    "fill_gal_per_mw": (2000.0, 12000.0),
    # When a dry cooler goes wet is an operator's setting, not a property of the equipment (EVAPCO 2019, p. 2: a selection and control output; Trane DC-WPR004A: the
    # customer chooses; US 12,426,214 B1: a controller threshold with a range of embodiments). It is tied to the loop (model 1.7): the setting sits at the dry-bulb where the dry coil can no longer hold loop
    # supply, loop_limit below, give or take this margin in K for operators who go wet early or trim with chillers a while longer [A]. Same for assist and hybrid.
    "switch_margin": (-2.0, 2.0),
    # Dry coolers with adiabatic pre-cooling (model 1.3). Microsoft's 85 °F is for its direct-air evaporative design, a
    # different system, and is not used here. Pad saturation effectiveness: EVAPCO (presented at CTI, Feb 2019, p. 2) measured 72-78% at 400-700 fpm across 10
    # pads, a maker's own test; ASHRAE (2016, ch. 41) gives 70 to over 95% for rigid media.
    "assist_eff": (0.70, 0.80),
    # Hybrid dry coolers: wet mode from the switch point up (above). Fully evaporative at each location's own 0.4% design dry-bulb (design_dry_bulb; model 1.7, was 30-33 °C everywhere,
    # which is West Michigan's), give or take this many K [A]: the source gives no such point, so this says the dry section is sized to carry part of the load
    # up to the hottest weather the plant is designed for.
    "hybrid_full_offset": (-1.5, 1.5),
}
# Share of the loop volume lost to small leaks and topped up each year (NIH 2023 Technical Bulletin: "typically less than 5% of the
# system's total volume in a year"; the 1% floor is an assumption), all of it counted as lost. Poorly kept loops can lose far more (NIH:
# 25% a month "is not uncommon"), which the range does not cover.
TOPUP = (0.01, 0.05)
# Adiabatic pre-cooling. Air temperature rise across the dry cooler coil at
# design, K: 9-13 from makers' selection sheets (Thermokey 11.2, Kelvion 12.8) [estimate]. Bleed as a share of evaporation: none for once-through
# pads (Guentner; Spinazzola 2021), up to 0.5 for recirculating pads (SCE ET13SCE1020, 2015, p. 29: 10-50%; ASHRAE 2016 ch. 41 allows 5-100%).
ADIABATIC = {"assist_dt_air": (9.0, 13.0), "assist_bleed": (0.0, 0.5)}
# Electricity and heat (model 1.4). Large-scale values are Lei and Masanet's Table 3, case 2 (preprint rs-769999/v1;
# waterside economizer, 2.8-6.7 C tower approach, and so on), which LBNL 2024 also draws on, unless noted.
POWER = {
    "ups": (0.90, 0.99), "dist_loss": (0.0, 0.02), "light": (0.0, 0.002),
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
# Lei and Masanet's sensible heat ratio (0.95-0.99) was removed in model 1.5 for OUTSIDE below: at their ratio the coils would condense moisture no air was
# bringing in, and these coils are too warm to condense.
# Outside air (model 1.5). The building takes a little outside air to stay pressurized and ventilated; it brings heat and
# moisture in, and leaves at indoor conditions. Flow per MW of IT capacity, a bracket [A]: ASHRAE 62.1's 0.06 cfm/ft2 for computer rooms (2007 table, as
# quoted secondhand; the area rate, since these rooms are mostly unoccupied) at about 5,000 ft2 per MW [A] is 300; the ends are 100 and 1,500 [A]. No
# published flow for large campuses was found. Share of the dry-air shortfall made up by humidifiers, not published for any fleet, so all of 0-1 is
# sampled [A]: some facilities no longer humidify (HVAC.best on ASHRAE TC 9.9). Humidifiers are taken as adiabatic [A].
OUTSIDE = {"oa_cfm_per_mw": (100.0, 1500.0), "humidify_share": (0.0, 1.0)}
# Indoor dew point limits, C: ASHRAE TC 9.9's recommended -9 to 15, as secondary sources give them, not read directly. Water to the outside air unit's
# dehumidifying coil, C [A]: it must be colder than the 15 C dew point, while the air loop's water, at 18.7 C or more, is not, so those coils stay dry.
DEW_LOW, DEW_HIGH, DEHUMIDIFY_WATER = -9.0, 15.0, 9.0
TOWER_DESIGN_WB = 25.6     # C, the 78 F wet-bulb of the standard cooling tower rating (95/85/78 F) [A]; a site's own design wet-bulb differs by a few degrees
# Switch settings stay within the 70-95 °F (21.1-35.1 °C) that US 12,426,214 B1 (2025) gives for its controller's wet mode threshold (example: 82 °F, 27.8 °C); applied to assist by analogy [A].
SWITCH_SETTINGS = (21.1, 35.1)
HYBRID_MIN_RAMP = 1.0      # K [A]: where a location's design dry-bulb is at or below the switch point, wet mode still comes on over this span, in its hottest hours only
PARAMETERS = tuple(RANGES) + ("topup",) + tuple(ADIABATIC) + tuple(POWER) + tuple(OUTSIDE)

# Staff water. People = the campus's permanent headcount (employees and on-site contractors), a fixed core plus a share per MW of IT
# capacity: JLARC 2024 puts a typical building at about 50 full-time workers; announced campuses run 0.1 to 0.5 jobs per MW (Meta Richland
# Parish 0.1, Meta El Paso and Saline Township about 0.3, Gilroy 0.5). Gallons are per person per calendar day (model 1.3; was 15-30 with
# no source): EPA 2002 Table 3-4 gives 7-16 (13 typical) per office or industrial employee per workday, about 9 per calendar day; Michigan's
# septic design criteria give 35 per factory worker per shift, and Gilroy's applicant 1,800 gpd for about 50 employees (about 30). About
# 10% is lost (Shaffer and Runkle 2007, Table 9: commercial, Great Lakes Basin, median 10%, quartiles 8-15%); the rest goes to the sewer.
# Maintenance and other non-cooling water (model 1.3): equipment and floor washdown, janitorial and fire-system testing, loop flushing,
# a campus base plus a little per MW, bracketed by applicant projections rather than measured (none published): Hermantown, MN (Google;
# loop maintenance about 2,000 gal per building a month) at the low end, Crusoe's 200 MW building (about 2 million gal a year for
# restrooms, kitchens, maintenance and washdown, less its staff water) at the high end; checked against Microsoft at Tyrone, GA (2,000
# gpd per building), Saline Township (about 20,000 gpd for 1.4 GW) and Mount Pleasant, WI. Mostly to the sewer: 3-15% lost (USGS
# commercial coefficients). Landscape irrigation is site- and climate-specific and is not included. Gallons a day.
STAFF = {"core": (20.0, 60.0), "per_mw": (0.1, 0.5), "gpcd": (10.0, 30.0), "used": (0.05, 0.15),
         "maint_base": (0.0, 2000.0), "maint_per_mw": (2.0, 20.0), "maint_used": (0.03, 0.15)}
STAFF_PARAMETERS = tuple(f"staff_{k}" for k in STAFF)

# Where each parameter's range comes from, in a line; the reasoning is in the comments above. [A] marks an assumption or estimate.
_LM = "Lei and Masanet (preprint rs-769999/v1), Table 3, case 2"
_STAFF_WATER = "Applicant projections, none measured: Hermantown, MN and Crusoe's 200 MW building, checked against Tyrone, GA, Saline Township and Mount Pleasant, WI [A]"
SOURCES = {
    "utilization": "EPRI 2026; IEA 2025; LBNL 2024 server parameters",
    "load_factor": "EPRI 2026 (94% hyperscale, 88% co-location)",
    "er_adj": "USGS SIR 2013-5188 (Diehl et al.), pp. 24, 28 (5-15% for tower evaporative ratios); asymmetric for Rutberg et al.'s fit at cooler water [A]",
    "coc": "Lei and Masanet (preprint rs-769999/v1), Table 3, case 2; Han et al. 2026, Table 2; DOE FEMP BMP #10's typical range is lower (2-4; 6 or more possible)",
    "range_f": "Lei and Masanet (preprint rs-769999/v1), Table 3; 10 F rating",
    "drift": "EPA WaterSense at Work 2012, section 6.3, p. 6-9; EPA AP-42 13.4, Table 13.4-1",
    "fill_gal_per_mw": "Crusoe 2026; chilled-water loops of 3-10 gal per ton; top 12,000 [A]",
    "switch_margin": "Operator's setting around the loop's limit [A]: Trane DC-WPR004A (the customer chooses); US 12,426,214 B1 (a controller threshold, 70-95 F in its embodiments); EVAPCO 2019, p. 2",
    "assist_eff": "EVAPCO 2019 (presented at CTI, Feb 2019), p. 2; ASHRAE 2016, ch. 41",
    "hybrid_full_offset": "Around the location's own 0.4% design dry-bulb [A], no published value",
    "topup": "NIH 2023 Technical Bulletin (under 5% a year); 1% floor [A]",
    "assist_dt_air": "Makers' selection sheets: Thermokey, Kelvion [A]",
    "assist_bleed": "Guentner; Spinazzola 2021; SCE ET13SCE1020, 2015, p. 29; ASHRAE 2016, ch. 41",
    "oa_cfm_per_mw": "ASHRAE 62.1-2007 computer rooms, quoted secondhand, at about 5,000 ft2 per MW [A]; ends 100 and 1,500 [A], no published campus flow",
    "humidify_share": "Not published for any fleet; all of 0-1 sampled [A]; HVAC.best on ASHRAE TC 9.9 (many facilities no longer humidify)",
    **dict.fromkeys(("ups", "dist_loss", "light", "supply_air", "air_rise", "coil_eff", "water_rise", "crah_pa", "fan_eff", "tower_fan_pa", "lg",
                     "tower_approach", "hx_approach", "pump_chw_kpa", "pump_tower_kpa", "pump_econ_kpa", "pump_eff"), _LM),
    "carnot_water": "WAC 51-11C-403323 (replica of ASHRAE 90.1 Table 6.8.1-3); +/-11% from Lei and Masanet; fitted with the temperature offsets [A]",
    "carnot_air": "EER 10.1; 0.55 [A]; fitted with the temperature offsets [A]",
    "dc_approach": "ThermoKey catalogue point (10 K); makers' quotes for larger coils (5 K) [A]",
    "dc_fan_pa": "By analogy with Lei and Masanet's tower fans [A]",
    "liquid_water": "ASHRAE TC 9.9 classes W32-W45; LBNL 2024 Table 4.3",
    "liquid_air_share": "HPE GB200 NVL72; Schneider WP210; ASME InterPACK2022, not read directly [A]",
    "liquid_share": "Not published for any fleet; all of 0-1 sampled [A]",
    "core": "JLARC 2024 (about 50 full-time workers a building) [A]",
    "per_mw": "Announced campuses: Meta Richland Parish, Meta El Paso, Saline Township, Gilroy",
    "gpcd": "EPA 2002 Table 3-4; Michigan septic design criteria; Gilroy applicant",
    "used": "Shaffer and Runkle 2007, Table 9 (Great Lakes Basin and climatically similar areas), used in every state [A]",
    "maint_base": _STAFF_WATER,
    "maint_per_mw": _STAFF_WATER,
    "maint_used": "USGS commercial coefficients (Shaffer and Runkle 2007, Great Lakes Basin and climatically similar areas), used in every state [A]",
}


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


def peak_utilization(p):
    """IT load on the peak day as a share of capacity: average load over the load factor, at most every computer at capacity."""
    return np.minimum(p["utilization"] / p["load_factor"], 1.0)


def design_dry_bulb(tdb):
    """The 0.4% design dry-bulb of an hourly record, C: the temperature exceeded in 0.4% of its hours, the way ASHRAE defines it. Any hourly record works, station or grid cell."""
    return float(np.quantile(np.asarray(tdb, dtype=float), 0.996))


def for_location(p, tdb):
    """Parameters with the location's design dry-bulb from its whole hourly record. Every run at a location goes through this; hybrid needs it."""
    return {**p, "design_db": design_dry_bulb(tdb)}


def loop_limit(p):
    """Dry-bulb where a dry coil can no longer hold the loops' supply temperature, C: supply less the coil's approach, with the air and liquid loops weighted by their
    shares of the heat (Lei and Masanet's air loop water; a liquid loop of its own). Above it, a dry plant needs chillers or evaporation."""
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    air_water = p["supply_air"] + p["air_rise"] - p["air_rise"] / p["coil_eff"]
    return air * air_water + (1.0 - air) * p["liquid_water"] - p["dc_approach"]


def switch_point(p):
    """Dry-bulb at which assist or hybrid goes wet, C: the operator's setting. Set "switch_on" to fix it, for example as a scenario; otherwise the loop's limit plus the
    run's margin, within SWITCH_SETTINGS."""
    return p["switch_on"] if "switch_on" in p else np.clip(loop_limit(p) + p["switch_margin"], *SWITCH_SETTINGS)


def hybrid_full(p):
    """Dry-bulb at which a hybrid is fully evaporative, C: the location's design dry-bulb plus the run's offset, and at least HYBRID_MIN_RAMP above the switch point."""
    if "design_db" not in p:
        raise ValueError("the hybrid design needs the location's design dry-bulb: pass parameters through for_location(p, tdb), or set design_db (in a BMI configuration, under parameters, unless a forcing file supplies it)")
    return np.maximum(p["design_db"] + p["hybrid_full_offset"], switch_point(p) + HYBRID_MIN_RAMP)


def _ramp(x, lo, hi):
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


CHILLER_COP_CAP = {"water": 8.0, "air": 5.0}          # FEMP's 5-8 for water-cooled; air-cooled part-load code minimums reach about 4.1-4.7 [A]
CP_AIR, CP_WATER, RHO_AIR, RHO_WATER = 1.01, 4.1868, 1.15, 1000.0     # kJ/kg/K, kg/m3; 4.1868 kJ/kg/K is the 1 BTU/lb/F the water terms use


def _fan_kw(kg_s, pa, eff):
    return kg_s / RHO_AIR * pa / eff / 1000.0


def _pump_kw(kg_s, kpa, eff):
    return kpa * kg_s / (RHO_WATER * eff)


def _saturated_enthalpy(t_c):
    """Moist air enthalpy at saturation, kJ per kg of dry air, at sea level (ASHRAE Fundamentals; Magnus vapor pressure)."""
    es = 0.6112 * np.exp(17.62 * t_c / (243.12 + t_c))
    w = 0.622 * es / (101.325 - es)
    return 1.006 * t_c + w * (2501.0 + 1.86 * t_c)


def _saturation_kpa(t_c):
    return 0.6112 * np.exp(17.62 * t_c / (243.12 + t_c))


def _humidity_ratio(e_kpa):
    return 0.622 * e_kpa / (101.325 - e_kpa)


def _outside_air(tdb, twb, p, rh=None):
    """Air and moisture through the building, per kW of IT: (kg of air per s, humidity ratio outside, humidity ratio indoors). Indoors holds the outside
    humidity between the dew point limits; above the high one the air is dehumidified to it, and below the low one humidifiers make up their share.
    rh is the hour's relative humidity, %. Without it, vapor pressure comes from the psychrometric equation on the wet-bulb (ASHRAE Fundamentals), which on
    Stull's wet-bulb is good above about 0 C and off by several times in cold, dry air, so everything that runs the model on weather passes rh."""
    kg_s = p["oa_cfm_per_mw"] / 1000.0 * CFM_M3S * RHO_AIR / p["utilization"]
    vapor = _saturation_kpa(tdb) * rh / 100.0 if rh is not None else np.maximum(_saturation_kpa(twb) - 0.0674 * (tdb - twb), 1e-4)
    outside = _humidity_ratio(vapor)
    low, high = _humidity_ratio(_saturation_kpa(DEW_LOW)), _humidity_ratio(_saturation_kpa(DEW_HIGH))
    indoors = np.minimum(outside, high) + p["humidify_share"] * np.maximum(low - outside, 0.0)
    return kg_s, outside, indoors


def hourly_outside_air_heat(tdb, twb, p, rh=None):
    """Heat outside air brings in, kW per IT kW: (through the warm air loop, can be negative when the air is cool or dry; latent heat at the dehumidifying
    coil). Their sum is the air's flow x (its enthalpy outside - its enthalpy leaving at indoor conditions, at the supply air temperature)."""
    kg_s, outside, indoors = _outside_air(tdb, twb, p, rh)
    sensible = kg_s * CP_AIR * (tdb - p["supply_air"])
    return sensible - kg_s * LATENT_KJ * np.maximum(indoors - outside, 0.0), kg_s * LATENT_KJ * np.maximum(outside - indoors, 0.0)


def hourly_water_with_air(tdb, twb, p, rh=None):
    """Gallons per IT kWh: (humidifier water, condensate drawn out of the outside air)."""
    kg_s, outside, indoors = _outside_air(tdb, twb, p, rh)
    return kg_s * np.maximum(indoors - outside, 0.0) * 3600.0 / KG_GAL, kg_s * np.maximum(outside - indoors, 0.0) * 3600.0 / KG_GAL


def _wet_share(tdb, design, p):
    """Share of the heat going through evaporation: all of it for towers, none for dry and assist coils, a ramp for hybrid."""
    if design == "towers":
        return np.ones_like(tdb)
    if design == "hybrid":
        return _ramp(tdb, switch_point(p), hybrid_full(p)) * np.ones_like(tdb)
    return np.zeros_like(tdb)


def _loop(load, supply, tdb, twb, coil_air, wet, design, p):
    """One facility water loop carrying `load` (kW per IT kW) at `supply` C, kW per IT kW: chiller power, pump power (both end up as heat to
    reject) and heat rejection fan power (whose heat goes straight to the exhaust air)."""
    ret = supply + p["water_rise"]
    outside = wet * (twb + p["tower_approach"] + p["hx_approach"]) + (1 - wet) * (coil_air + p["dc_approach"])
    free = _ramp(ret - outside, 0.0, ret - supply)                # Lei and Masanet: the economizer's share falls from 1 to 0 as outside approaches the return
    chilled = load * (1 - free)
    evaporator = supply - 2.0
    cop = lambda condenser, eta, cap: np.minimum(eta * (evaporator + 273.15) / np.maximum(condenser - evaporator, 1.0), cap)
    water_cooled = cop(twb + p["tower_approach"] + p["range_f"] / 1.8 + 2.0, p["carnot_water"], CHILLER_COP_CAP["water"])
    air_cooled = cop(coil_air + 12.0, p["carnot_air"], CHILLER_COP_CAP["air"])     # its rated COP includes its condenser fans
    # the chiller rejects through the same split as the rest of the heat: to evaporating water in the wet share, to air in the rest
    chiller = chilled * (wet / water_cooled + (1 - wet) / air_cooled)
    pumps = (_pump_kw(load * free / (CP_WATER * p["water_rise"]), p["pump_econ_kpa"], p["pump_eff"])
             + _pump_kw(chilled / (CP_WATER * p["water_rise"]), p["pump_chw_kpa"], p["pump_eff"]))
    # tower flow carries its share of all the water's heat, the tower pump's own included: m x cp x range = wet x (load + chiller + pumps + m x dP / eff)
    pump_per_flow = p["pump_tower_kpa"] / (RHO_WATER * p["pump_eff"])
    tower_range = p["range_f"] / 1.8
    tower_water = (load + chiller + pumps) * wet / (CP_WATER * tower_range - wet * pump_per_flow)
    tower_pump = tower_water * pump_per_flow
    # tower fans: a tower is sized for a design point and its fans slow when less air will do. Design: full heat through evaporation at the rating wet-bulb, with air
    # at the sampled water-to-air ratio, capped where air would leave hotter than saturated at the hot water. Each hour the air needed goes with the tower's heat over
    # the enthalpy the air can pick up, saturated at the hot water less the air coming in (Merkel's driving potential, with the design point's effectiveness); the
    # fan affinity law then gives the power, cubic with a 10% floor as for the dry coolers. In cool weather the water stays near the loop's return, not the wet-bulb's.
    design_water = load / (CP_WATER * tower_range)
    design_hot = TOWER_DESIGN_WB + p["tower_approach"] + tower_range
    design_potential = _saturated_enthalpy(design_hot) - _saturated_enthalpy(TOWER_DESIGN_WB)
    design_air = design_water / np.minimum(p["lg"], design_potential / (CP_WATER * tower_range))
    hot_water = np.maximum(twb + p["tower_approach"] + tower_range, ret - p["hx_approach"])
    air_share = tower_water / np.maximum(design_water, 1e-12) * design_potential / (_saturated_enthalpy(hot_water) - _saturated_enthalpy(twb))
    tower_fan = _fan_kw(design_air, p["tower_fan_pa"], p["fan_eff"]) * np.clip(air_share, 0.1, 1.0) ** 3 * (wet > 0)
    # dry cooler fans: the air flow that carries the economizer's heat, up to design flow, by the fan affinity law (cubic; 10% floor, immaterial)
    design_flow = load / (CP_AIR * p["assist_dt_air"])
    rise = np.maximum(ret - p["dc_approach"] - coil_air, p["assist_dt_air"])
    flow = load * free * (1 - wet) / (CP_AIR * rise)
    dry = _fan_kw(design_flow, p["dc_fan_pa"], p["fan_eff"]) * np.clip(flow / np.maximum(design_flow, 1e-12), 0.1, 1.0) ** 3
    return chiller, pumps + tower_pump, tower_fan + (0.0 if design == "towers" else dry)


def hourly_heat_power(tdb, twb, design, p, rh=None):
    """Each hour, per kW of IT: (facility power, kW; heat rejected through the water or coil, kW). Facility power over IT power is the hour's PUE.
    Energy closes: facility power + the heat outside air brings in = heat rejected + the heat rejection fans, whose heat goes straight to the exhaust air.

    After Lei and Masanet's Eqs. 2-4, with these departures, each so that it closes: air handler fan and pump heat are counted in the heat; their sensible
    heat ratio is replaced by outside air's own heat and moisture, since the warm air loop's coils run above the indoor dew point and condense nothing; the
    tower's fans slow to the air the hour's heat needs, capped by what air can carry. Dry cooler and liquid cooling designs are added, which their cases do not have. p as in hourly_rates."""
    q = 1.0 + (1.0 / p["ups"] - 1.0) + (1.0 / (1.0 - p["dist_loss"]) - 1.0) + p["light"]
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    kg_s = _outside_air(tdb, twb, p, rh)[0]
    room = q - (1.0 - air)                                    # the heat that reaches the room's air: the air-cooled computers and all the power losses and lighting
    crah = _fan_kw(room / (CP_AIR * p["air_rise"]) + kg_s, p["crah_pa"], p["fan_eff"])
    outside, latent = hourly_outside_air_heat(tdb, twb, p, rh)
    # supply air and the coil set the air loop's water temperature (Lei and Masanet); liquid-cooled heat goes to a warmer loop of its own
    air_water = p["supply_air"] + p["air_rise"] - p["air_rise"] / p["coil_eff"]
    coil_air = tdb - (p["assist_eff"] * np.maximum(tdb - twb, 0.0) * (tdb >= switch_point(p)) if design == "assist" else 0.0)
    wet = _wet_share(tdb, design, p)
    air_load = room + crah + outside                          # in rare, bitter hours outside air could cool more than the air loop carries; the rest comes off the liquid loop
    power, heat = q + crah + 0.0 * tdb, q + crah + outside + latent
    for load, supply in ((np.maximum(air_load, 0.0), air_water), (1.0 - air + np.minimum(air_load, 0.0), p["liquid_water"]), (latent, DEHUMIDIFY_WATER)):
        chiller, pumps, fans = _loop(load, supply, tdb, twb, coil_air, wet, design, p)
        power, heat = power + chiller + pumps + fans, heat + chiller + pumps
    return power, heat


def hourly_rates(tdb, twb, design, p, rh=None, heat=None):
    """Gallons per IT kWh for each hour: (withdrawn, consumed, returned).

    tdb, twb, rh: dry- and wet-bulb temperature (C) and relative humidity (%), shape (hours,). p: parameter dict whose values are scalars or arrays
    shaped (runs, 1). heat: hourly_heat_power's heat for these inputs, if already worked out. Mass closes: withdrawn + condensate = consumed + returned.
    Condensate comes out of the outside air, not the water system, and goes back with the blowdown (hourly_water_with_air).
    """
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    btu = KWH_BTU * (hourly_heat_power(tdb, twb, design, p, rh)[1] if heat is None else heat)
    evap_full = btu * evaporative_ratio(tdb, p["er_adj"]) / HFG / LB_GAL
    w = _wet_share(tdb, design, p) * np.ones_like(evap_full)
    circ = btu * w / (LB_GAL * p["range_f"])                # gal circulated through the wet part per kWh
    evap = evap_full * w
    drift = circ * p["drift"]
    blow = evap / (p["coc"] - 1.0) - drift                  # dissolved solids balance: what leaves as liquid, blowdown and drift, carries them out
    if design == "assist":
        # Water evaporated into the air ahead of the coil. The air cools by depr = effectiveness x wet-bulb depression; the fans slow until
        # it leaves the coil where it would at the switch point (on + rise), so air flow = heat / (cp x (on + rise - tdb + depr)), and
        # evaporation as a share of all the heat is depr over that same difference, at most 1. Pads have no tower drift.
        depr = p["assist_eff"] * np.maximum(tdb - twb, 0.0)
        on = switch_point(p)
        share = np.clip(depr / np.maximum(on + p["assist_dt_air"] - tdb + depr, 1e-6), 0.0, 1.0)
        evap = btu * share / HFG / LB_GAL * (tdb >= on)
        drift = np.zeros_like(evap)
        blow = evap * p["assist_bleed"]
    # loop top-up, gal/day per MW of capacity, as gal per IT kWh
    topup = p["fill_gal_per_mw"] * p["topup"] / 365.0 / (24 * 1000 * p["utilization"]) * np.ones_like(evap_full)
    humidify, condensate = hourly_water_with_air(tdb, twb, p, rh)
    withdrawn = evap + drift + blow + topup + humidify
    consumed = evap + drift + topup + humidify
    returned = blow + condensate
    return withdrawn, consumed, returned


# Parameters that describe one plant move together in the draws; drawn independently, a site could pair a 99% UPS with the worst fans, or a 45 C liquid loop
# with no liquid cooling. Each group has one shared score, and +1 or -1 says which way each member goes with it. No published correlation exists, so the
# strength is an assumption [A]: shared score + member's own score, equal weights, which gives two members a rank correlation of about 0.5, midway between
# independent and moving as one. Cycles of concentration stays out: it follows source water, which is a matter of place. Methods log, Nov 1, 2026.
LINKED = {
    # a well-built plant: efficient power equipment, low pressure drops, tight approaches and good chillers together
    "plant": {"ups": 1, "dist_loss": -1, "fan_eff": 1, "pump_eff": 1, "crah_pa": -1, "tower_fan_pa": -1, "dc_fan_pa": -1, "pump_chw_kpa": -1, "pump_tower_kpa": -1,
              "pump_econ_kpa": -1, "coil_eff": 1, "tower_approach": -1, "hx_approach": -1, "dc_approach": -1, "carnot_water": 1, "carnot_air": 1},
    # one temperature design: warm supply air goes with wide temperature rises across the coil, the loop and, through the plate exchanger, the tower
    "loop": {"supply_air": 1, "air_rise": 1, "water_rise": 1, "range_f": 1},
    # AI campuses: higher utilization and steadier load (EPRI's hyperscale pair against its co-location pair), more liquid cooling, warmer liquid loops
    "load": {"utilization": 1, "load_factor": 1, "liquid_share": 1, "liquid_water": 1},
}


def _strata(n, seed, name):
    """n values in 0-1, one from each of n equal strata, in random order, on a stream of its own: adding or removing a parameter leaves the others' draws alone."""
    rng = np.random.default_rng([seed, zlib.crc32(name.encode())])
    return (rng.permutation(n) + rng.random(n)) / n


def latin_hypercube(ranges, n, seed, linked=None):
    """Latin hypercube draws over {name: (low, high)}: {name: array (n,)}. Every parameter keeps one value in each of its n strata, however the groups in
    `linked` reorder them (rank reordering, after Iman and Conover 1982). The same n and seed always give the same draws."""
    u = {k: _strata(n, seed, k) for k in ranges}
    for group, members in (linked or {}).items():
        shared = _strata(n, seed, f"group {group}")
        for k, sign in members.items():
            if k in u:
                score = (shared if sign > 0 else 1.0 - shared) + _strata(n, seed, f"own {k}")
                u[k] = np.sort(u[k])[np.argsort(np.argsort(score))]
    return {k: a + (b - a) * u[k] for k, (a, b) in ranges.items()}


DRAWS = 400       # Latin hypercube draws at each location: 12 seeds at 200 left the hybrid and assist average medians within 6-16% (methods log, Nov 1, 2026), and error falls with the square root of the draws


def sample_parameters(n=DRAWS, seed=7):
    """Monte Carlo draws of the cooling parameters: {name: array (n,)}. cooling.py's per-run loop and ensemble.py both use these draws."""
    return latin_hypercube({**RANGES, "topup": TOPUP, **ADIABATIC, **POWER, **OUTSIDE}, n, seed, LINKED)


def central_parameters():
    """Every parameter at the middle of its range."""
    return {**{k: (a + b) / 2 for k, (a, b) in {**RANGES, **ADIABATIC, **POWER, **OUTSIDE}.items()}, "topup": sum(TOPUP) / 2}


def sample_staff(n=DRAWS, seed=13):
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
