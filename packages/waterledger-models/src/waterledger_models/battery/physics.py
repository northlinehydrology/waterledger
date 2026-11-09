"""Battery cell plants (design 0009, model 1.12): the plant's heat and power hour by hour, and the water it takes, per GWh/yr of cell capacity.

Water follows heat. Making a kWh of cells takes about 25-45 kWh of electricity and fuel (Kuki et al. 2025; UKBIC 2022; Degen et al. 2023),
nearly all of it in electrode drying, dry rooms and formation. Each hour:

  production = capacity x utilization / 8,760, kWh of cells an hour
  plant energy = production at full output x energy x (fixed share + (1 - fixed share) x utilization): dry rooms and building services run
      whatever the output (the fixed share), the lines in proportion to it. Split into electricity and fuel (gas for ovens, boilers, heaters).
  heat to the cooling water = a share of plant energy, part of it on chilled water (formation rooms, dry-room coils, NMP condensers), the
      rest on a warmer process loop (compressors, hydraulics); the rest leaves in exhaust air, flue gas and the building envelope.
  outdoor air: the dry rooms and conditioned areas take make-up air that must be cooled and dried. Its load on the chilled water follows the
      outdoor air's enthalpy above the supply air's, sized as a share of the cooling load at the location's design enthalpy.
  the loops, chillers, pumps and fans, the towers, hybrid or dry coolers, and the water they take: heat_rejection, shared with data centers.
  process water: purified water for anode slurry (evaporated in the dryers), water leaving in recovered NMP, other purified water (to
      sewer), the purification's reject (to sewer), boiler make-up (mostly lost as steam). Staff water follows the people on site.

Energy closes: electricity + fuel + the heat outdoor air brings in = heat rejected through the water or dry coolers + heat to exhaust, flue
and envelope + the heat rejection fans' heat, which goes straight to the exhaust air. Mass closes: withdrawn = consumed + returned.
Condensate from the make-up air coils is not counted [A]: it is under 1% of the plant's water (about 12,000 gal/day at Lansing's size).

Parameter ranges and their sources: RANGES and SOURCES below; the evidence is in docs/research/battery-cell-parameters.md and
battery-plant-water.md, the design in docs/design/0009-battery-cell-plants.md.
"""
import numpy as np

from waterledger_models import heat_rejection as hr

DESIGNS = ("dry", "hybrid", "towers")
HOURS_A_YEAR = 8760.0
CELLS_PER_HOUR = 1e6 / HOURS_A_YEAR          # kWh of cells an hour at full output, per GWh/yr of capacity
L_GAL = 3.78541

# (low, high), sampled in the Monte Carlo (Latin hypercube, uniform in each range); central values are the midpoints. [A] marks an estimate.
RANGES = {
    # Plant energy per kWh of cells at full output, electricity and fuel, less the cooling plant's own chillers, pumps and fans, which the model
    # works out each hour and adds back (about 2-3 kWh/kWh). Whole-plant figures: Kuki et al. 2025, Table 1 (CATL Debrecen 34.6, Samsung SDI Göd 28.3,
    # SK Iváncsa at least 29.4, permit documents); UKBIC 2022 (29, gigafactory scale); Degen et al. 2023 (22.4 for NMC811, which leaves out building
    # services, a floor); Dai et al. 2019 (47 at 75% of capacity, a 2016 line). So 25-45 for the whole plant, 23-42 less the cooling plant [A].
    "energy": (23.0, 42.0),
    # Share of plant energy that runs whatever the output (dry rooms, building services, material handling): Degen et al. 2023 source data
    # (dry rooms and handling, about 30%); UKBIC 2022, sec. 2.5 [A].
    "fixed_share": (0.3, 0.5),
    # Electricity's share of plant energy, the rest fuel: Degen et al. 2023 (0.48); Kuki et al. 2025 (0.39 and 0.67); Lansing EA (0.42-0.70, derived [A]).
    "elec_share": (0.35, 0.70),
    # Share of plant energy (less the cooling plant) that becomes load on the cooling water, by step: formation and other process electricity
    # 0.7-0.95, cathode dryers' NMP condensers about half, anode dryers and desiccant regeneration 0.05-0.2, space heating none; 0.53 in the
    # central case (docs/research/battery-cell-parameters.md, sec. 3) [A]. With chiller work added back it is 0.45-0.75 of the whole plant's
    # energy, which Lansing's EA consumption (0.57-0.71) and CATL Debrecen's water (at most 0.54) bracket.
    "to_water": (0.40, 0.66),
    # Share of that load on chilled water, the rest on the warmer process loop (air compressors, hydraulics, the first NMP coils) [A], sec. 3.
    "chilled_share": (0.60, 0.85),
    # Chilled water supply, C: 4-6 for dry-room pre-cooling and NMP condensers (Ahmed et al. 2016, cited secondhand), 7-14 for formation rooms
    # and process; one loop for both at 5-10 [A].
    "chilled_supply": (5.0, 10.0),
    # Process cooling water supply, C: tower water through a plate exchanger to compressors and hydraulics [A].
    "process_supply": (24.0, 32.0),
    # Outdoor air's share of the cooling load at the location's design enthalpy: psychrometric estimate 0.03-0.22 for make-up air of 5,000-40,000
    # m3/h per GWh/yr; Spring Hill's 1.32 peak-to-average water (DOE/EA-2189, p. 14) caps it near 0.3; Dai et al. 2019's climate swing in dry-room
    # electricity argues against the lowest values (sec. 4) [A].
    "oa_share": (0.05, 0.30),
    # Enthalpy of the conditioned supply air, kJ per kg of dry air: about 18 for dry rooms (18 C, -40 C dew point), 34 for other areas (12 C
    # saturated) [A]. Outdoor air below it takes no cooling: in the heating season fuel heats it, and none of that reaches the cooling water.
    "oa_supply_enthalpy": (18.0, 34.0),
    # Process water, liters per kWh of cells (sec. 6). Anode slurry water, purified, evaporated in the dryers: UKBIC's 42% solids [A].
    "anode_water": (1.0, 2.0),
    # Water leaving with recovered NMP or trucked process water: BlueOval City EA Table 6 (144 million lb/yr of NMP scrap); StarPlus EA Table 4 [A].
    "shipped_water": (0.0, 1.0),
    # Other purified water (cleaning, scrubbers, labs), to sewer [A].
    "other_purified": (0.2, 1.0),
    # Purification recovery, permeate over feed; the reject goes to sewer [A].
    "ro_recovery": (0.65, 0.80),
    # Boiler make-up, liters per kWh of cells, and the share of it that leaves as blowdown to sewer; the rest is lost as steam [A].
    "boiler_makeup": (0.2, 2.0),
    "boiler_blowdown": (0.1, 0.4),
    # People on site per GWh/yr of capacity at full production: DOE EAs for Ultium Lansing (35), Spring Hill (26-37), BlueOval City (56), BlueOval SK
    # Glendale (61) and StarPlus Kokomo (52).
    "staff_per_gwh": (25.0, 65.0),
    # Gallons per person per calendar day, and the share used up: as for data centers (EPA 2002 Table 3-4; Michigan septic design criteria, 35 per
    # factory worker per shift; Shaffer and Runkle 2007, Table 9).
    "staff_gpcd": (10.0, 30.0),
    "staff_used": (0.05, 0.15),
    # Output over nameplate for a running plant: Korean makers' company-wide utilization, 44-88% in 2022-2025 (Korea Times, Aug 15, 2025); ramp-ups
    # and pauses (Ultium, 2026). Full output, 1.0, is the headline, as every EA states its figure (design 0009, decision 2).
    "utilization": (0.4, 1.0),
}
SOURCES = {
    "energy": "Kuki et al. 2025, Table 1; UKBIC 2022; Degen et al. 2023; Dai et al. 2019; less the cooling plant's work, which the model adds [A]",
    "fixed_share": "Degen et al. 2023 source data; UKBIC 2022, sec. 2.5 [A]",
    "elec_share": "Degen et al. 2023; Kuki et al. 2025; Lansing EA, derived [A]",
    "to_water": "Step-by-step estimate [A]; checked against Lansing's EA consumption and CATL Debrecen's water",
    "chilled_share": "Step-by-step estimate [A]",
    "chilled_supply": "Ahmed et al. 2016 (cited secondhand); common plant practice [A]",
    "process_supply": "Common plant practice [A]",
    "oa_share": "Psychrometric estimate [A]; Spring Hill's peak-to-average water (DOE/EA-2189, p. 14) as an upper bound",
    "oa_supply_enthalpy": "Dry rooms at 18 C and -40 C dew point to other areas at 12 C saturated [A]",
    "anode_water": "UKBIC 2022 slurry solids [A]",
    "shipped_water": "DOE/EA-2201, Table 6; DOE/EA-2263, Table 4 [A]",
    "other_purified": "Estimate [A]",
    "ro_recovery": "Estimate [A]",
    "boiler_makeup": "Estimate [A]",
    "boiler_blowdown": "Estimate [A]",
    "staff_per_gwh": "DOE/EA-2189-S1, -2189, -2201, -2263 employment at full production",
    "staff_gpcd": "EPA 2002 Table 3-4; Michigan septic design criteria",
    "staff_used": "Shaffer and Runkle 2007, Table 9 [A]",
    "utilization": "Korea Times, Aug 15, 2025 (company reports); Ultium pauses, 2026",
}
PARAMETERS = tuple(RANGES) + tuple(hr.EQUIPMENT)


def enthalpy(tdb, rh):
    """Moist air enthalpy, kJ per kg of dry air, at sea level (ASHRAE Fundamentals; Magnus vapor pressure, as in heat_rejection)."""
    w = hr._humidity_ratio(hr._saturation_kpa(tdb) * np.clip(rh, 0.0, 100.0) / 100.0)
    return 1.006 * tdb + w * (2501.0 + 1.86 * tdb)


def for_location(p, tdb, rh):
    """Parameters with the location's design dry-bulb and design enthalpy (the 0.4% values of its whole hourly record). Every run at a location goes through this."""
    return {**hr.for_location(p, tdb), "design_h": float(np.quantile(enthalpy(np.asarray(tdb, float), np.asarray(rh, float)), 0.996))}


def ranges():
    """Every parameter's range: the plant's own and the shared equipment's."""
    return {**RANGES, **hr.EQUIPMENT}


def sample_parameters(n, seed=7):
    """Latin hypercube draws of every parameter: {name: array (n,)}."""
    return hr.latin_hypercube(ranges(), n, seed)


def central_parameters():
    return {k: (a + b) / 2 for k, (a, b) in ranges().items()}


def switch_point(p):
    """Dry-bulb at which a hybrid goes wet, C: where its dry coil can no longer hold the process loop's supply, plus the run's margin [A]."""
    return hr.switch_point(p, p["process_supply"] - p["dc_approach"] - p["hx_approach"])


def hourly(tdb, twb, rh, design, p):
    """Each hour, per GWh/yr of capacity at p["utilization"]: a dict of kW (energy and heat) and gallons (water) for the hour.

    kW: "energy" (plant energy less the cooling plant), "electricity", "fuel", "outdoor_air" (its load on the chilled water), "heat" (rejected through
    the water or dry coolers), "exhaust" (to exhaust air, flue and envelope), "fans" (heat rejection fans). Gallons: "withdrawn", "consumed", "returned",
    and the parts "evap", "drift", "blow", "process_withdrawn", "process_consumed", "staff".
    """
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    u = p["utilization"]
    made = CELLS_PER_HOUR * u
    energy = p["energy"] * CELLS_PER_HOUR * (p["fixed_share"] + (1.0 - p["fixed_share"]) * u) * np.ones_like(tdb)
    load = p["to_water"] * energy
    design_load = p["to_water"] * p["energy"] * CELLS_PER_HOUR
    oa_design = p["oa_share"] / (1.0 - p["oa_share"]) * design_load
    outdoor_air = oa_design * np.maximum(enthalpy(tdb, rh) - p["oa_supply_enthalpy"], 0.0) / (p["design_h"] - p["oa_supply_enthalpy"])
    wet = hr.wet_share(tdb, design, p, switch_point(p))
    heat, cooling_power, fans = 0.0, 0.0, 0.0
    for loop_load, supply in ((p["chilled_share"] * load + outdoor_air, p["chilled_supply"]), ((1.0 - p["chilled_share"]) * load, p["process_supply"])):
        chiller, pumps, fan = hr.loop(loop_load, supply, tdb, twb, tdb, wet, design, p)
        heat, cooling_power, fans = heat + loop_load + chiller + pumps, cooling_power + chiller + pumps + fan, fans + fan
    electricity = p["elec_share"] * energy + cooling_power
    fuel = (1.0 - p["elec_share"]) * energy
    evap, drift, blow = hr.tower_water(heat * hr.KWH_BTU, tdb, wet, p)
    purified = (p["anode_water"] + p["other_purified"] + p["shipped_water"]) * made
    ro_feed = purified / p["ro_recovery"]
    boiler = p["boiler_makeup"] * made
    process_withdrawn = (ro_feed + boiler) / L_GAL
    process_consumed = (p["anode_water"] * made + p["shipped_water"] * made + boiler * (1.0 - p["boiler_blowdown"])) / L_GAL
    staff = p["staff_per_gwh"] * p["staff_gpcd"] / 24.0
    ones = np.ones_like(tdb)
    return {
        "energy": energy, "electricity": electricity, "fuel": fuel * ones, "outdoor_air": outdoor_air, "heat": heat,
        "exhaust": (1.0 - p["to_water"]) * energy, "fans": fans,
        "evap": evap, "drift": drift, "blow": blow, "process_withdrawn": process_withdrawn * ones, "process_consumed": process_consumed * ones,
        "staff": staff * ones,
        "withdrawn": evap + drift + blow + process_withdrawn + staff,
        "consumed": evap + drift + process_consumed + staff * p["staff_used"],
        "returned": blow + (process_withdrawn - process_consumed) + staff * (1.0 - p["staff_used"]),
    }
