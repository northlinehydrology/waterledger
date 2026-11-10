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
import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models.heat_rejection import (CFM_M3S, CHILLER_COP_CAP, CP_AIR, CP_WATER, EQUIPMENT, GAL_M3, GLYCOL, HFG, HYBRID_MIN_RAMP, KG_GAL,  # noqa: F401
                                               KWH_BTU, LATENT_KJ, LB_GAL, RHO_AIR, RHO_WATER, SWITCH_SETTINGS, TOWER_DESIGN_WB, _fan_kw, _humidity_ratio,
                                               _pump_kw, _ramp, _saturated_enthalpy, _saturation_kpa, _strata, design_dry_bulb, evaporative_ratio, for_location,
                                               glycol_properties, latin_hypercube, wet_bulb)
from waterledger_models.heat_rejection import loop as _loop  # noqa: F401

DESIGNS = ("dry", "assist", "hybrid", "towers")

# (low, high) ranges sampled in the Monte Carlo (sample_parameters: Latin hypercube, uniform in each range); central values are the midpoints.
RANGES = {
    # Equipment parameters (towers, hybrid and dry coolers, loops, pumps, fans, chillers) are shared with every water user: their ranges and sources are
    # in heat_rejection.EQUIPMENT. The operating settings (heat_rejection.OPERATING: cycles of concentration, the switch margin) are the data center's own, below.
    # average IT draw ÷ IT capacity at full build-out (model 1.3; was 0.60-0.90). EPRI 2026 measured 75% of nameplate at a large hyperscale
    # site and 57% at co-location sites; IEA 2025 puts hyperscale at 53-56%; LBNL's server parameters give about 40% (AI inference) to 60%
    # (AI training). Load over a site's own peak (EPRI: 88-94%) is a different ratio and does not bound this one.
    "utilization": (0.50, 0.80),
    # Load factor, a site's average load over its own peak load (model 1.7): EPRI 2026 measured 94% at a large hyperscale site and 88% at co-location sites. The peak day
    # runs at utilization / load factor (peak_utilization): EPRI's own pairs give 0.75 / 0.94 = 0.80 and 0.57 / 0.88 = 0.65. Every computer at capacity all day is the upper case.
    "load_factor": (0.88, 0.94),
    "er_adj": EQUIPMENT["er_adj"],
    # Cycles of concentration, about 3-6 (model 1.7, was 3-7), a data center operating setting (heat_rejection.OPERATING). Lei and Masanet's Table 3, case 2,
    # allows 3-15; the consumptive ratios Han et al. (2026, Table 2) report for operators, 0.72-0.91, are about 3.6-11 cycles, median about 4.5; ICPRB's 75% is 4. DOE FEMP BMP #10's typical range is lower, two to four, with six or more
    # possible. Nothing is published for large campuses, and source water sets the real limit, so 3-6 is the part of the operators' values that is common practice [A].
    "coc": (3.0, 6.0),
    "range_f": EQUIPMENT["range_f"],
    "drift": EQUIPMENT["drift"],
    # Closed loop volume, gal per MW of IT capacity (model 1.3, was 2,000-6,000): Crusoe (2026) about 1.7 million gal for a typical system, which is 8,500 if that is
    # its 200 MW building, as its figure suggests; chilled-water loops of 3-10 gal per ton (850-2,840 per MW of heat), not read directly, at the low end. The top is
    # that 8,500 and a margin, for lack of a filing that states a volume and a capacity together [A]. Vantage's 11.8 million gal, used until model 1.7, is out: it was a
    # TV tour of its Sterling, Virginia site, not Port Washington, with no capacity given.
    "fill_gal_per_mw": (2000.0, 12000.0),
    # When a dry cooler goes wet is an operator's setting (heat_rejection.OPERATING), not a property of the equipment (EVAPCO 2019, p. 2: a selection and
    # control output; US 12,426,214 B1: a controller threshold with a range of embodiments). It is tied to the loop (model 1.7): the setting sits at the dry-bulb where the dry coil can no longer hold loop
    # supply, each user model's loop limit (switch_point), give or take this margin in K for operators who go wet early or trim with chillers a while longer [A]. Same for assist and hybrid.
    "switch_margin": (-2.0, 2.0),
    # Dry coolers with adiabatic pre-cooling (model 1.3): the pads' effectiveness is shared equipment (heat_rejection.EQUIPMENT, from model 1.12).
    "assist_eff": EQUIPMENT["assist_eff"],
    "hybrid_full_offset": EQUIPMENT["hybrid_full_offset"],
}
# Share of the loop volume lost to small leaks and topped up each year (NIH 2023 Technical Bulletin: "typically less than 5% of the
# system's total volume in a year"; the 1% floor is an assumption), all of it counted as lost. Poorly kept loops can lose far more (NIH:
# 25% a month "is not uncommon"), which the range does not cover.
TOPUP = (0.01, 0.05)
# Adiabatic pre-cooling: the air temperature rise across the dry cooler coil at design and the pads' bleed are shared equipment (heat_rejection.EQUIPMENT).
ADIABATIC = {"assist_dt_air": EQUIPMENT["assist_dt_air"], "assist_bleed": EQUIPMENT["assist_bleed"]}
# Electricity and heat (model 1.4). Large-scale values are Lei and Masanet's Table 3, case 2 (preprint rs-769999/v1;
# waterside economizer, 2.8-6.7 C tower approach, and so on), which LBNL 2024 also draws on, unless noted.
POWER = {
    "ups": (0.90, 0.99), "dist_loss": (0.0, 0.02), "light": (0.0, 0.002),
    "supply_air": (24.0, 30.0), "air_rise": (13.9, 19.4), "coil_eff": (0.70, 0.90), "water_rise": EQUIPMENT["water_rise"],
    "crah_pa": (300.0, 700.0), "fan_eff": EQUIPMENT["fan_eff"],
    "tower_fan_pa": EQUIPMENT["tower_fan_pa"], "lg": EQUIPMENT["lg"], "tower_approach": EQUIPMENT["tower_approach"], "hx_approach": EQUIPMENT["hx_approach"],
    "pump_chw_kpa": EQUIPMENT["pump_chw_kpa"], "pump_tower_kpa": EQUIPMENT["pump_tower_kpa"], "pump_econ_kpa": EQUIPMENT["pump_econ_kpa"], "pump_eff": EQUIPMENT["pump_eff"],
    "carnot_water": EQUIPMENT["carnot_water"], "carnot_air": EQUIPMENT["carnot_air"],
    "dc_approach": EQUIPMENT["dc_approach"], "dc_fan_pa": EQUIPMENT["dc_fan_pa"],
    "glycol_share": EQUIPMENT["glycol_share"],
    # Liquid-cooled computers: the rest of their heat goes by air: 12.9% (HPE GB200 NVL72), 20% (Schneider WP210), 25-39% (ASME InterPACK2022, not read
    # directly); 10-30% [A]. The share of computers that are liquid-cooled at a campus is not published for any fleet, so all of 0-1 is sampled [A]. Their
    # facility water depends on the plant (PLANTS below): on a shared loop it is the air loop's own water and liquid_water is not used; this range is
    # the separate warm loop's.
    "liquid_water": (30.0, 42.0), "liquid_air_share": (0.10, 0.30), "liquid_share": (0.0, 1.0),
}
# The cooling plant inside the building (model 1.10, design 0007; Andrew's decision, Nov 8, 2026). Through model 1.9 every campus ran supply air at
# 27-35 C, Lei and Masanet's upper float bound, and liquid-cooled computers on a loop of their own at 32-45 C, two of ASHRAE's W-class ceilings
# (ASHRAE TC 9.9 2021, p. 8: each class runs from 2 C up to its number), so every plant was a warm-water best case no source reports operating
# at. Three documented plants replace it:
#   shared  one facility water loop serves the air handlers and the liquid racks' coolant units, so the liquid racks get the air loop's water (about
#           16-28.5 C): OCP, "30 C Coolant" (Rev 1.0, Oct 2024), Fig. 10, p. 22 (one loop at 24/34 C, 30 C supply air); Vertiv GB200 reference
#           designs 006 and 007; Uptime Intelligence Update 373 (Jun 2025): operators commonly run 18-24 C at the coolant units because one loop
#           also carries the air loads. The common documented plant, and the default.
#   warm    a separate warm liquid loop on its own dry coolers, the air hall on a cooler loop: Schneider Reference Design 109 (37.2/47.2 C fluid
#           coolers with adiabatic assist above 32 C; 22.8/32.8 C chilled water for 27.8 C supply air; about 75% of the heat to liquid). Facility
#           water 30-42 C [A]: 42 is NVIDIA's 45 C rack inlet less about 3 K through the coolant unit (OCP 2024, p. 21: 4-8 K). Liquid-cooled
#           share 0.7-1.0 [A]: Vertiv's GB200 designs 72-80%, Schneider about 75%, Microsoft over 90%.
#   chilled a conventional chilled-water plant, as in older and many colocation buildings: supply air 18-22 C (ASHRAE TC 9.9 2021's H1 class for
#           high-density equipment, recommended 18-22 C, p. 14; ASHRAE 90.4-2022 Addendum g's basis, an 11 K rise to 29 C return air, so about 18 C; its zone 5A worked example, 18-19 C
#           supply air on 44/56 F chilled water), on chilled water set at 7-13 C (6.7 C in the worked example; 13 C [A]
#           for plants run warmer), the room air rising 11-14 K (90.4's 11 K to Lei and Masanet's 13.9 [A]). The coil relation can't reach water this
#           cold from these supply temperatures, so the chilled water is set, not derived. Liquid-cooled share 0-0.2 [A] (Uptime's 2024 survey: 22% of
#           operators use direct liquid cooling, nearly half of them on under 10% of racks), on the same chilled water. At this water the room coils can condense
#           some indoor moisture that humidifiers then replace; the model takes them as dry [A].
# Supply air in the shared and warm plants: 24-30 C [A] (above): Schneider 27.8, OCP 30, Meta's reference 18.3-29.4, ASHRAE's recommended upper limit 27. An air-cooled
# hall (liquid share near 0) is the shared plant at one end of its range. The hybrid and assist switch point is one setting for the plant, so in the warm
# plant it is the two loops' limits weighted by their heat (loop_limit), where a real plant could switch each loop on its own [A].
PLANTS = {"shared": {}, "warm": {"liquid_water": (30.0, 42.0), "liquid_share": (0.7, 1.0)},
          "chilled": {"supply_air": (18.0, 22.0), "air_rise": (11.0, 14.0), "chilled_water": (7.0, 13.0), "liquid_share": (0.0, 0.2)}}
SHARED = {"shared": True, "warm": False, "chilled": True}
DEFAULT_PLANT = "shared"
PLANT_LABELS = {"shared": "One facility water loop for air and liquid cooling", "warm": "A separate warm-water loop for liquid cooling",
                "chilled": "A conventional chilled-water plant"}
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
PARAMETERS = tuple(RANGES) + ("topup",) + tuple(ADIABATIC) + tuple(POWER) + tuple(OUTSIDE) + ("chilled_water",)

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
    "switch_margin": "Operator's setting around the loop's limit [A]: US 12,426,214 B1 (a controller threshold, 70-95 F in its embodiments); EVAPCO 2019, p. 2",
    "assist_eff": "EVAPCO 2019 (presented at CTI, Feb 2019), p. 2; ASHRAE 2016, ch. 41",
    "hybrid_full_offset": "Around the location's own 0.4% design dry-bulb [A], no published value",
    "topup": "NIH 2023 Technical Bulletin (under 5% a year); 1% floor [A]",
    "assist_dt_air": "Makers' selection sheets: Thermokey, Kelvion [A]",
    "assist_bleed": "Guentner; Spinazzola 2021; SCE ET13SCE1020, 2015, p. 29; ASHRAE 2016, ch. 41",
    "oa_cfm_per_mw": "ASHRAE 62.1-2007 computer rooms, quoted secondhand, at about 5,000 ft2 per MW [A]; ends 100 and 1,500 [A], no published campus flow",
    "humidify_share": "Not published for any fleet; all of 0-1 sampled [A]; HVAC.best on ASHRAE TC 9.9 (many facilities no longer humidify)",
    **dict.fromkeys(("ups", "dist_loss", "light", "air_rise", "coil_eff", "water_rise", "crah_pa", "fan_eff", "tower_fan_pa", "lg",
                     "tower_approach", "pump_chw_kpa", "pump_econ_kpa", "pump_eff"), _LM),
    "air_rise": f"{_LM}; the chilled plant 11-14 K, from ASHRAE 90.4-2022 Addendum g's 11 K basis [A]",
    "hx_approach": f"{_LM}; the dry coolers' glycol exchanger by analogy (model 1.9) [A]",
    "pump_tower_kpa": f"{_LM}; the dry coolers' glycol loop by analogy (model 1.9) [A]",
    "carnot_water": "WAC 51-11C-403323 (replica of ASHRAE 90.1 Table 6.8.1-3); +/-11% from Lei and Masanet; fitted with the temperature offsets [A]",
    "carnot_air": "EER 10.1; 0.55 [A]; fitted with the temperature offsets [A]",
    "dc_approach": "ThermoKey catalogue point (10 K); makers' quotes for larger coils (5 K) [A]",
    "dc_fan_pa": "By analogy with Lei and Masanet's tower fans [A]",
    "glycol_share": "Burst to freeze protection [A]; freezing points, heat capacity and density from Dow's DOWFROST Technical Data Sheet, Form No. 180-01314-1019",
    "supply_air": "Shared and warm plants 24-30 C: Schneider RD109 (27.8 C); OCP 2024, Fig. 10 (30 C); Meta/OCP reference band 18.3-29.4 C; ASHRAE TC 9.9 2021 recommended upper 27 C; 24 C floor [A]. Chilled plant 18-22 C: ASHRAE TC 9.9 2021 H1 class, recommended 18-22 C (p. 14); ASHRAE 90.4-2022 Addendum g and its zone 5A worked example",
    "liquid_water": "The warm plant only: Schneider RD109 (37.2 C); NVIDIA's 45 C rack inlet less about 3 K (OCP 2024, p. 21) [A]; on a shared loop, the air loop's water",
    "chilled_water": "The chilled plant only: ASHRAE 90.4 zone 5A worked example (Amistadi 2020), 44/56 F; 13 C [A]",
    "liquid_air_share": "HPE GB200 NVL72; Schneider WP210; ASME InterPACK2022, not read directly [A]",
    "liquid_share": "Not published for any fleet; all of 0-1 sampled on a shared loop [A]; 0.7-1.0 in the warm plant (Vertiv GB200 designs 72-80%, Schneider about 75%, Microsoft over 90%) [A]",
    "core": "JLARC 2024 (about 50 full-time workers a building) [A]",
    "per_mw": "Announced campuses: Meta Richland Parish, Meta El Paso, Saline Township, Gilroy",
    "gpcd": "EPA 2002 Table 3-4; Michigan septic design criteria; Gilroy applicant",
    "used": "Shaffer and Runkle 2007, Table 9 (Great Lakes Basin and climatically similar areas), used in every state [A]",
    "maint_base": _STAFF_WATER,
    "maint_per_mw": _STAFF_WATER,
    "maint_used": "USGS commercial coefficients (Shaffer and Runkle 2007, Great Lakes Basin and climatically similar areas), used in every state [A]",
}






def peak_utilization(p):
    """IT load on the peak day as a share of capacity: average load over the load factor, at most every computer at capacity."""
    return np.minimum(p["utilization"] / p["load_factor"], 1.0)






def air_loop_water(p):
    """The air loop's facility water, C: Lei and Masanet's coil relation from supply air (supply air less the coil's approach), or the chilled water a
    conventional plant sets (PLANTS: chilled)."""
    coil = p["supply_air"] + p["air_rise"] - p["air_rise"] / p["coil_eff"]
    return p["chilled_water"] if "chilled_water" in p else coil


def loop_limit(p):
    """Dry-bulb where a dry coil can no longer hold the loops' supply temperature, C: supply less the coil's approach, with the air and liquid loops weighted by their
    shares of the heat (Lei and Masanet's air loop water; a liquid loop of its own). Above it, a dry plant needs chillers or evaporation."""
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    air_water = air_loop_water(p)
    return air * air_water + (1.0 - air) * p["liquid_water"] - p["dc_approach"] - p["hx_approach"]


def switch_point(p):
    """Dry-bulb at which assist or hybrid goes wet, C: the operator's setting. Set "switch_on" to fix it, for example as a scenario; otherwise the loop's limit plus the
    run's margin, within SWITCH_SETTINGS (heat_rejection.switch_point)."""
    return hr.switch_point(p, loop_limit(p))


def hybrid_full(p):
    """Dry-bulb at which a hybrid is fully evaporative, C (heat_rejection.hybrid_full, from this plant's switch point)."""
    return hr.hybrid_full(p, switch_point(p))




















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
    """Share of the heat going through evaporation (heat_rejection.wet_share, from this plant's switch point); none for assist, whose pads evaporate ahead of a dry coil."""
    return hr.wet_share(tdb, design, p, switch_point(p))






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
    air_water = air_loop_water(p)
    coil_air = hr.coil_air(tdb, twb, design, p, switch_point(p))
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
    s = _rate_parts(tdb, twb, design, p, rh, heat)
    withdrawn = s["evap"] + s["drift"] + s["blow"] + s["topup"] + s["humidify"]
    consumed = s["evap"] + s["drift"] + s["topup"] + s["humidify"]
    returned = s["blow"] + s["condensate"]
    return withdrawn, consumed, returned


def _rate_parts(tdb, twb, design, p, rh=None, heat=None):
    """hourly_rates' flows one by one, gallons per IT kWh: {"evap", "drift", "blow", "topup", "humidify", "condensate"}."""
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    btu = KWH_BTU * (hourly_heat_power(tdb, twb, design, p, rh)[1] if heat is None else heat)
    evap, drift, blow = hr.tower_water(btu, tdb, _wet_share(tdb, design, p), p)
    if design == "assist":
        evap, drift, blow = hr.pad_water(btu, tdb, twb, p, switch_point(p))     # the pads' water (heat_rejection, shared from model 1.12)
    # loop top-up, gal/day per MW of capacity, as gal per IT kWh
    topup = p["fill_gal_per_mw"] * p["topup"] / 365.0 / (24 * 1000 * p["utilization"]) * np.ones(np.broadcast_shapes(np.shape(btu), np.shape(tdb), np.shape(p["er_adj"])))
    humidify, condensate = hourly_water_with_air(tdb, twb, p, rh)
    return {"evap": evap, "drift": drift, "blow": blow, "topup": topup, "humidify": humidify, "condensate": condensate}


# Water limits (design 0006, Nov 2026). The heat a campus makes has to go whatever a rule allows it to take: a limit cuts the evaporative duty (a hybrid's wet
# mode, assist's pads) and the dry coolers and chillers carry the rest, at the electricity they take that hour. Their capacity is finite [A]: sized for every
# computer at capacity, all dry, at the location's design dry-bulb, with a margin, and falling as the air warms past that point (air-cooled equipment derates;
# chillers' tables give 1.2-1.4% per K, dry coolers alone lose more; design 0006). A towers plant has no dry side, so the heat a limit leaves it is heat not removed: IT load that would
# have to be shed. Heat not removed is reported, never dropped. These are not sampled in the Monte Carlo; a limit is a scenario, set through the BMI.
LIMITS = {"dry_capacity_margin": (0.0, 0.20), "dry_derate_per_k": (0.01, 0.02)}
LIMIT_PARAMETERS = tuple(LIMITS)
LIMIT_SOURCES = {"dry_capacity_margin": "Over the design load [A]; no published sizing margin for large campuses",
                 "dry_derate_per_k": "Share of capacity lost per K above the design dry-bulb [A]: air-cooled chillers lose 1.2-1.4% (Parker GSFE, Titan tables); dry coolers alone lose more, with their ITD (design 0006)"}
CAPACITY_RH = 40.0         # %, the humidity at which dry capacity is worked out at the design dry-bulb [A]; it enters only through outside air's small latent heat


def central_limits():
    """The water limit parameters at the middle of their ranges."""
    return {k: (a + b) / 2 for k, (a, b) in LIMITS.items()}


def _dry_capacity(tdb, design, p):
    """Heat the dry coolers and chillers can reject this hour, kW per kW of the hour's IT load: the all-dry heat at the design dry-bulb for every computer at
    capacity, with the margin, less the derating for each K the air is above the design dry-bulb. No dry side for towers."""
    if design == "towers":
        return np.zeros_like(tdb)
    if "design_db" not in p:
        raise ValueError("a water limit on a dry-capable design needs the location's design dry-bulb (design_db) to size its dry coolers and chillers")
    d = np.full_like(tdb, p["design_db"], dtype=float)
    full = hourly_heat_power(d, wet_bulb(d, np.full_like(d, CAPACITY_RH)), design, {**p, "wet_frac": 0.0}, np.full_like(d, CAPACITY_RH))[1]
    derate = np.clip(1.0 - p["dry_derate_per_k"] * np.maximum(tdb - p["design_db"], 0.0), 0.0, 1.0)
    return full / p["utilization"] * (1.0 + p["dry_capacity_margin"]) * derate


def hourly_limited(tdb, twb, design, p, limit, rh=None, iterations=12):
    """Each hour under a cap on the cooling water, per IT kWh as in hourly_rates: limit is the most it may take for cooling, gallons per IT kWh (staff water
    comes off a campus's limit before this), infinity for none. Returns a dict of arrays:
      power, heat          facility power and the heat to be rejected, kW per IT kW, as hourly_heat_power gives them at the hour's wet share
      removed, unremoved   heat rejected and heat not removed (the IT load that would be shed, as heat); removed + unremoved = heat
      shed                 the share of the hour's load that couldn't be cooled, 0 to 1; power and the cooling water count only the load cooled
      wet_frac             the share of the hour's evaporative duty kept, 0 to 1
      evap, drift, blow, topup, humidify, condensate, withdrawn, consumed, returned
                           as _rate_parts and hourly_rates give them, for the load cooled
    Where the limit doesn't bind, every value is hourly_heat_power's and hourly_rates' to the bit. Top-ups and humidifier water don't depend on the
    evaporative duty and come off the limit first; a limit below them can't be met and isn't.

    Towers: the plant has nothing but evaporation, so the load the limit can't cool is shed. Hybrid and assist: the wet share or the pads' cooling is cut
    until the water meets the limit (a fixed point on withdrawal, which is close to proportional to the wet duty), the dry side carries the rest at its
    electricity, and heat beyond its capacity (_dry_capacity) is shed. Dry: it evaporates nothing, so a limit takes nothing from it."""
    tdb = np.asarray(tdb, dtype=float)
    power, heat = hourly_heat_power(tdb, twb, design, p, rh)
    s = _rate_parts(tdb, twb, design, p, rh, heat)
    base = {"power": power, "heat": heat, **s}
    fixed = s["topup"] + s["humidify"]
    cool = s["evap"] + s["drift"] + s["blow"]
    room = np.maximum(limit - fixed, 0.0)
    binding = cool > room * (1 + 1e-12)
    ones = np.ones(np.broadcast(power, cool).shape)
    out = {k: v * ones for k, v in base.items()}
    out.update(removed=heat * ones, unremoved=0.0 * ones, shed=0.0 * ones, wet_frac=ones.copy())
    if not binding.any():
        return _totals(out)
    if design == "towers":
        frac = np.where(binding, room / np.maximum(cool, 1e-300), 1.0)
        shed = 1.0 - frac
        lim = base
    else:
        frac = ones.copy()
        for _ in range(iterations):
            q = {**p, "wet_frac": frac}
            pw, ht = hourly_heat_power(tdb, twb, design, q, rh)
            sp = _rate_parts(tdb, twb, design, q, rh, ht)
            c = sp["evap"] + sp["drift"] + sp["blow"]
            frac = np.where(binding, np.clip(frac * room / np.maximum(c, 1e-300), 0.0, 1.0), 1.0)
        q = {**p, "wet_frac": frac}
        pw, ht = hourly_heat_power(tdb, twb, design, q, rh)
        sp = _rate_parts(tdb, twb, design, q, rh, ht)
        wet = _wet_share(tdb, design, q) * ones
        dry_heat = ht if design == "assist" else ht * (1.0 - wet)
        shed = np.where(binding, np.clip((dry_heat - _dry_capacity(tdb, design, p)) / np.maximum(ht, 1e-300), 0.0, 1.0), 0.0)
        lim = {"power": pw, "heat": ht, **sp}
    keep = 1.0 - shed
    for k in ("evap", "drift", "blow", "power"):
        out[k] = np.where(binding, lim[k] * keep, out[k])
    out["heat"] = np.where(binding, lim["heat"] * ones, out["heat"])
    out["removed"] = np.where(binding, lim["heat"] * keep, out["removed"])
    out["unremoved"] = np.where(binding, lim["heat"] * shed, 0.0)
    out["shed"] = np.where(binding, shed, 0.0)
    out["wet_frac"] = np.where(binding, frac, 1.0)
    return _totals(out)


def _totals(out):
    out["withdrawn"] = out["evap"] + out["drift"] + out["blow"] + out["topup"] + out["humidify"]
    out["consumed"] = out["evap"] + out["drift"] + out["topup"] + out["humidify"]
    out["returned"] = out["blow"] + out["condensate"]
    return out


# Return water (design 0006). Evaporation takes only water, so the dissolved mass in what a campus takes for cooling leaves as liquid: in blowdown, to the
# sewer, and in drift, to the air. Loop top-ups leave through small leaks and humidifier water through the air, so what they carry stays behind (leak and scale);
# so does what once-through pads carry, since they have no bleed. Temperatures: blowdown at the cold-water basin's temperature, the wet-bulb plus the tower's
# approach; assist's pad bleed at the sump's, about the wet-bulb; condensate at the dehumidifying coil's leaving dew point, the indoor high limit [A].
CONDENSATE_C = DEW_HIGH
STAFF_RETURN_C = 20.0      # C, staff and maintenance wastewater [A]


def dissolved_mass_split(parts):
    """Where the dissolved mass in the water taken for cooling goes, each as gallons of intake water per IT kWh whose mass goes there (multiply by the intake
    concentration): (to the sewer in blowdown, to the air in drift, left behind in leaks and scale). They add up to the water taken for cooling."""
    makeup = parts["evap"] + parts["drift"] + parts["blow"]
    liquid = parts["blow"] + parts["drift"]
    sewer = np.where(liquid > 0, makeup * parts["blow"] / np.where(liquid > 0, liquid, 1.0), 0.0)
    drift = np.where(liquid > 0, makeup * parts["drift"] / np.where(liquid > 0, liquid, 1.0), 0.0)
    return sewer, drift, makeup - sewer - drift + parts["topup"] + parts["humidify"]


def blowdown_temperature(twb, design, p):
    """C: the tower basin's cold water (wet-bulb plus approach) for towers and hybrid, the pads' sump (the wet-bulb) for assist."""
    return twb + (p["tower_approach"] if design in ("towers", "hybrid") else 0.0)


# Parameters that describe one plant move together in the draws; drawn independently, a site could pair a 99% UPS with the worst fans, or a 45 C liquid loop
# with no liquid cooling. Each group has one shared score, and +1 or -1 says which way each member goes with it. No published correlation exists, so the
# strength is an assumption [A]: shared score + member's own score, equal weights, which gives two members a rank correlation of about 0.5, midway between
# independent and moving as one. Cycles of concentration stays out: it follows source water, which is a matter of place. Methods log, Nov 1, 2026.
LINKED = {
    # a well-built plant: efficient power equipment, low pressure drops, tight approaches and good chillers together
    "plant": {"ups": 1, "dist_loss": -1, "fan_eff": 1, "pump_eff": 1, "crah_pa": -1, "tower_fan_pa": -1, "dc_fan_pa": -1, "pump_chw_kpa": -1, "pump_tower_kpa": -1,
              "pump_econ_kpa": -1, "coil_eff": 1, "tower_approach": -1, "hx_approach": -1, "dc_approach": -1, "carnot_water": 1, "carnot_air": 1},
    # one temperature design: warm supply air goes with wide temperature rises across the coil, the loop and, through the plate exchanger, the tower
    "loop": {"supply_air": 1, "air_rise": 1, "water_rise": 1, "range_f": 1, "chilled_water": 1},
    # AI campuses: higher utilization and steadier load (EPRI's hyperscale pair against its co-location pair), more liquid cooling, warmer liquid loops
    "load": {"utilization": 1, "load_factor": 1, "liquid_share": 1, "liquid_water": 1},
}






DRAWS = 400       # Latin hypercube draws at each location: 12 seeds at 200 left the hybrid and assist average medians within 6-16% (methods log, Nov 1, 2026), and error falls with the square root of the draws


def plant_ranges(plant=DEFAULT_PLANT):
    """Every cooling parameter's range for a plant (PLANTS): {name: (low, high)}."""
    if plant not in PLANTS:
        raise ValueError(f"plant must be one of {tuple(PLANTS)}, not {plant!r}")
    return {**RANGES, "topup": TOPUP, **ADIABATIC, **POWER, **OUTSIDE, **PLANTS[plant]}


def with_plant(p, plant=DEFAULT_PLANT):
    """The parameters with the plant's link applied: where the liquid racks share the air loop (shared, chilled) their facility water is the air
    loop's own (air_loop_water), so liquid_water is set from it; the warm plant keeps its own. Works on scalars or arrays; returns a new dict."""
    if plant not in PLANTS:
        raise ValueError(f"plant must be one of {tuple(PLANTS)}, not {plant!r}")
    if not SHARED[plant]:
        return dict(p)
    return {**p, "liquid_water": air_loop_water(p)}


def sample_parameters(n=DRAWS, seed=7, plant=DEFAULT_PLANT):
    """Monte Carlo draws of the cooling parameters for a plant: {name: array (n,)}. cooling.py's per-run loop and ensemble.py both use these draws.
    The same n and seed give the same strata for every plant; only the plant's own ranges and link differ."""
    return with_plant(latin_hypercube(plant_ranges(plant), n, seed, LINKED), plant)


def central_parameters(plant=DEFAULT_PLANT):
    """Every parameter at the middle of its range, for a plant."""
    return with_plant({k: (a + b) / 2 for k, (a, b) in plant_ranges(plant).items()}, plant)


def sample_staff(n=DRAWS, seed=13):
    """Latin hypercube draws of the staff water parameters on their own stream, as the cooling parameters are drawn:
    {"staff_core", "staff_per_mw", "staff_gpcd", "staff_used", ...: array (n,)}."""
    return {f"staff_{k}": v for k, v in latin_hypercube(STAFF, n, seed).items()}


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
