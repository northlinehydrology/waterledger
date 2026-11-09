"""Heat rejection, shared by every water user (design 0009, Nov 9, 2026): cooling towers, hybrid and dry coolers, the water loops, pumps,
fans and chillers between a plant's heat and the outside air, and the psychrometrics and Monte Carlo sampling they run on.

A tower is a tower: what it evaporates depends on the heat it is given, the weather and its own settings, not on what made the heat. So each
water user model (datacenter/, battery/) works out its own heat and power and hands the heat here, per kW of its own load. The code moved here
from datacenter/physics.py unchanged, and every data center result is the same to the last bit (tests/test_heat_rejection.py).

  evaporation = heat x wet share x evaporative ratio (Rutberg et al. 2011, as in USGS SIR 2013-5188) / latent heat
  drift = a share of the flow through the wet part; circulating flow = heat / (500 x range F)
  blowdown + drift = evaporation / (cycles of concentration - 1)   (the dissolved solids balance; Lei and Masanet Eq. 7; DOE FEMP BMP #10)

Designs differ in when they evaporate: towers always, hybrid in warm weather (from the switch point to full at the location's design dry-bulb),
dry never. Data centers add their own assist design (datacenter/physics.py).

The equipment's ranges are shared (EQUIPMENT); the operating settings (OPERATING: cycles of concentration, the hybrid's switch) are each user's own,
since operators choose them and the evidence differs by industry.
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

# Operating settings: chosen by whoever runs the plant, not fixed by the equipment, so each water user model sets their ranges from its own evidence
# (datacenter/physics.py, battery/physics.py) and a plant's own documents can fix them for a scenario. The physics here reads them as it reads the equipment's.
#   coc            cycles of concentration: how far the tower water concentrates before it is bled off. Source water and treatment set the real limit.
#   switch_margin  K from the user's loop limit to the dry-bulb where a hybrid (or a data center's assist) goes wet (switch_point).
OPERATING = ("coc", "switch_margin")

# (low, high) ranges of the equipment parameters, sampled in each water user's Monte Carlo. Each user model draws them with its own.
EQUIPMENT = {
    # Evaporative ratio adjustment (model 1.3, was +/-0.05): asymmetric because Rutberg et al.'s fit (Poppe runs at 40 °C inlet water,
    # RH 60%) is applied hourly to cooler data center tower water and cold hours, where it likely runs high. USGS SIR 2013-5188 (Diehl et al.): +/-5-15% for the
    # Leung and Moore method (p. 24); 15% added to the modeled tower suite (p. 28); +/-18% for towers is consumption with the error in heat included (p. 29), and
    # USGS's 18% for the evaporative ratio itself is for water surfaces. LBNL and Lei and Masanet evaporate all the heat; this ratio is the model's stated departure.
    "er_adj": (-0.10, 0.05),
    "range_f": (7.2, 10.8),            # tower range, °F (model 1.7, was 7-15, whose top had no source): Lei and Masanet preprint, Table 3, 4-6 °C; the 10 °F rating sits inside it
    # Drift as a share of circulating flow (model 1.7, was 0.0005-0.02%, whose low end was ten times under the source): modern eliminators at 0.005% (EPA WaterSense at
    # Work 2012, section 6.3, p. 6-9: less than 0.005%; the end of Lei and Masanet's Table 3) to EPA AP-42 13.4's induced-draft 0.020% (Table 13.4-1).
    "drift": (0.00005, 0.0002),
    # Hybrid dry coolers: wet mode from the switch point up (above). Fully evaporative at each location's own 0.4% design dry-bulb (design_dry_bulb; model 1.7, was 30-33 °C everywhere,
    # which is West Michigan's), give or take this many K [A]: the source gives no such point, so this says the dry section is sized to carry part of the load
    # up to the hottest weather the plant is designed for.
    "hybrid_full_offset": (-1.5, 1.5),
    # Water loops, pumps, fans and chillers (model 1.4): Lei and Masanet's Table 3, case 2 (preprint rs-769999/v1; waterside economizer,
    # 2.8-6.7 C tower approach, and so on), which LBNL 2024 also draws on, unless noted.
    "water_rise": (5.0, 10.0),
    "fan_eff": (0.65, 0.90),
    "tower_fan_pa": (100.0, 400.0),
    "lg": (0.2, 4.0),
    "tower_approach": (2.8, 6.7),
    "hx_approach": (1.7, 2.8),
    "pump_chw_kpa": (114.9, 172.4),
    "pump_tower_kpa": (166.9, 250.4),
    "pump_econ_kpa": (114.9, 172.4),
    "pump_eff": (0.60, 0.80),
    # Chillers as a fraction of Carnot COP. Water-cooled: 0.70 from code minimums for large plant (0.560 kW/ton gives 0.72, 0.585 gives 0.69; WAC
    # 51-11C-403323, a stated replica of ASHRAE 90.1 Table 6.8.1-3; its part-load adjustment gives 0.67-0.73), +/-11% (Lei and Masanet's COP error).
    # Air-cooled: 0.45 from EER 10.1, 0.55 [A]. Both are fitted together with the temperature offsets below (2 K, 2 K, 12 K) [A].
    "carnot_water": (0.62, 0.78),
    "carnot_air": (0.45, 0.55),
    # Dry coolers. No standard or peer-reviewed design values exist, since selection data are proprietary, so these are assumptions tested in the
    # sensitivity analysis [A]: approach, a catalogue point of 10 K (ThermoKey) to the 5 K makers quote for larger coils; air-side pressure and
    # efficiency by analogy with Lei and Masanet's tower fans. The air rise is assist_dt_air's selection-sheet range.
    "dc_approach": (5.0, 10.0),
    "dc_fan_pa": (100.0, 250.0),
    # The dry coolers' glycol (model 1.10; water's properties through 1.9 [A]): propylene glycol at 30-40% by volume [A], from burst protection to
    # freeze protection for a Great Lakes winter (Dow, DOWFROST Technical Data Sheet, Form No. 180-01314-1019: freezing points -12.7 C at 30% and
    # -21.1 C at 40%). Its heat capacity and density are taken at 20 C from the same sheet (GLYCOL); thicker than water (4.5 mPa s at -10 C at
    # 30%; water is about 1.8 near freezing), it would also take more pump pressure, which isn't modeled [A].
    "glycol_share": (0.30, 0.40),
    # Air temperature rise across a dry cooler's coil at design, K: 9-13 from makers' selection sheets (Thermokey 11.2, Kelvion 12.8) [estimate].
    "assist_dt_air": (9.0, 13.0),
}

TOWER_DESIGN_WB = 25.6     # C, the 78 F wet-bulb of the standard cooling tower rating (95/85/78 F) [A]; a site's own design wet-bulb differs by a few degrees
# Switch settings stay within the 70-95 °F (21.1-35.1 °C) that US 12,426,214 B1 (2025) gives for its controller's wet mode threshold (example: 82 °F, 27.8 °C); applied to assist by analogy [A].
SWITCH_SETTINGS = (21.1, 35.1)
HYBRID_MIN_RAMP = 1.0      # K [A]: where a location's design dry-bulb is at or below the switch point, wet mode still comes on over this span, in its hottest hours only
# Propylene glycol solutions at 20 C, by volume: (heat capacity, kJ/kg/K; density, kg/m3), between Dow's 30% and 40% saturation tables (DOWFROST
# Technical Data Sheet, Form No. 180-01314-1019; 30%: 3.821 and 3.903 at -10 and 40 C, 1033.71 and 1019.56; 40%: 3.668 and 3.768 at 10 and 40 C,
# 1042.14 and 1026.49), linear in temperature and share.
GLYCOL = {0.30: (3.870, 1025.2), 0.40: (3.701, 1036.9)}
CHILLER_COP_CAP = {"water": 8.0, "air": 5.0}          # FEMP's 5-8 for water-cooled; air-cooled part-load code minimums reach about 4.1-4.7 [A]
CP_AIR, CP_WATER, RHO_AIR, RHO_WATER = 1.01, 4.1868, 1.15, 1000.0     # kJ/kg/K, kg/m3; 4.1868 kJ/kg/K is the 1 BTU/lb/F the water terms use


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


def design_dry_bulb(tdb):
    """The 0.4% design dry-bulb of an hourly record, C: the temperature exceeded in 0.4% of its hours, the way ASHRAE defines it. Any hourly record works, station or grid cell."""
    return float(np.quantile(np.asarray(tdb, dtype=float), 0.996))


def for_location(p, tdb):
    """Parameters with the location's design dry-bulb from its whole hourly record. Every run at a location goes through this; hybrid needs it."""
    return {**p, "design_db": design_dry_bulb(tdb)}


def _ramp(x, lo, hi):
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def glycol_properties(p):
    """The glycol loop's (heat capacity, kJ/kg/K; density, kg/m3) at p["glycol_share"], between Dow's 30% and 40% values."""
    (a, (ca, ra)), (b, (cb, rb)) = sorted(GLYCOL.items())
    x = (p["glycol_share"] - a) / (b - a)
    return ca + x * (cb - ca), ra + x * (rb - ra)


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


def switch_point(p, limit):
    """Dry-bulb at which a hybrid (or a data center's assist) goes wet, C: the operator's setting. Set "switch_on" to fix it, for example as a scenario; otherwise
    the plant's own loop limit (the dry-bulb where a dry coil can no longer hold the loop's supply) plus the run's margin, within SWITCH_SETTINGS."""
    return p["switch_on"] if "switch_on" in p else np.clip(limit + p["switch_margin"], *SWITCH_SETTINGS)


def hybrid_full(p, switch):
    """Dry-bulb at which a hybrid is fully evaporative, C: the location's design dry-bulb plus the run's offset, and at least HYBRID_MIN_RAMP above the switch point."""
    if "design_db" not in p:
        raise ValueError("the hybrid design needs the location's design dry-bulb: pass parameters through for_location(p, tdb), or set design_db (in a BMI configuration, under parameters, "
                         "unless a forcing file supplies it; waterledger_models.weather.design_dry_bulb computes it from an hourly record)")
    return np.maximum(p["design_db"] + p["hybrid_full_offset"], switch + HYBRID_MIN_RAMP)


def wet_share(tdb, design, p, switch):
    """Share of the heat going through evaporation: all of it for towers, none for dry coils, a ramp for hybrid from the switch point to hybrid_full. Under a
    water limit "wet_frac" scales a hybrid's ramp down; a towers plant has no dry side to take the rest, so its share stays whole."""
    if design == "towers":
        return np.ones_like(tdb)
    if design == "hybrid":
        ramp = _ramp(tdb, switch, hybrid_full(p, switch)) * np.ones_like(tdb)
        return ramp * p["wet_frac"] if "wet_frac" in p else ramp
    return np.zeros_like(tdb)


def tower_water(btu, tdb, wet, p):
    """Water through the wet part, gallons per unit of the user's load-hour: (evaporation, drift, blowdown), from the heat rejected in BTU, the hour's dry-bulb
    and the wet share. Mass closes: makeup = evaporation + drift + blowdown, and blowdown + drift = evaporation / (cycles - 1)."""
    evap_full = btu * evaporative_ratio(tdb, p["er_adj"]) / HFG / LB_GAL
    w = wet * np.ones_like(evap_full)
    circ = btu * w / (LB_GAL * p["range_f"])                # gal circulated through the wet part
    evap = evap_full * w
    drift = circ * p["drift"]
    blow = evap / (p["coc"] - 1.0) - drift                  # dissolved solids balance: what leaves as liquid, blowdown and drift, carries them out
    return evap, drift, blow


def loop(load, supply, tdb, twb, coil_air, wet, design, p):
    """One facility water loop carrying `load` at `supply` C, in kW per kW of the water user's own load (IT for a data center, plant energy for a
    battery cell plant): chiller power, pump power (both end up as heat to reject) and heat rejection fan power (whose heat goes straight to the exhaust air).
    wet is the share of the heat through evaporation (wet_share); coil_air the air reaching the dry coils, C. Reads the equipment parameters in EQUIPMENT."""
    ret = supply + p["water_rise"]
    # every design's heat rejection sits behind a plate heat exchanger: towers' open water, and the glycol a closed dry cooler runs to keep from freezing [A]
    outside = wet * (twb + p["tower_approach"] + p["hx_approach"]) + (1 - wet) * (coil_air + p["dc_approach"] + p["hx_approach"])
    free = _ramp(ret - outside, 0.0, ret - supply)                # Lei and Masanet: the economizer's share falls from 1 to 0 as outside approaches the return
    chilled = load * (1 - free)
    evaporator = supply - 2.0
    cop = lambda condenser, eta, cap: np.minimum(eta * (evaporator + 273.15) / np.maximum(condenser - evaporator, 1.0), cap)
    water_cooled = cop(twb + p["tower_approach"] + p["range_f"] / 1.8 + 2.0, p["carnot_water"], CHILLER_COP_CAP["water"])
    air_cooled = cop(coil_air + 12.0, p["carnot_air"], CHILLER_COP_CAP["air"])     # its rated COP includes its condenser fans
    # the chiller rejects through the same split as the rest of the heat: to evaporating water in the wet share, to air in the rest
    chiller = chilled * (wet / water_cooled + (1 - wet) / air_cooled)
    econ_pump = _pump_kw(load * free / (CP_WATER * p["water_rise"]), p["pump_econ_kpa"], p["pump_eff"])
    pumps = econ_pump + _pump_kw(chilled / (CP_WATER * p["water_rise"]), p["pump_chw_kpa"], p["pump_eff"])
    # tower flow carries its share of all the water's heat, the tower pump's own included: m x cp x range = wet x (load + chiller + pumps + m x dP / eff)
    pump_per_flow = p["pump_tower_kpa"] / (RHO_WATER * p["pump_eff"])
    tower_range = p["range_f"] / 1.8
    tower_water = (load + chiller + pumps) * wet / (CP_WATER * tower_range - wet * pump_per_flow)
    tower_pump = tower_water * pump_per_flow
    # the dry coolers' glycol loop carries the economizer's heat and the economizer pump's (an air-cooled chiller rejects through its own condenser), its own pump's
    # heat included; its range and pressure are the tower loop's, by analogy [A], with the glycol's heat capacity and density (model 1.10)
    cp_glycol, rho_glycol = glycol_properties(p)
    glycol_per_flow = p["pump_tower_kpa"] / (rho_glycol * p["pump_eff"])
    glycol = (load * free + econ_pump) * (1 - wet) / (cp_glycol * tower_range - (1 - wet) * glycol_per_flow)
    dry_pump = glycol * glycol_per_flow
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
    rise = np.maximum(ret - p["hx_approach"] - p["dc_approach"] - coil_air, p["assist_dt_air"])
    flow = load * free * (1 - wet) / (CP_AIR * rise)
    dry = _fan_kw(design_flow, p["dc_fan_pa"], p["fan_eff"]) * np.clip(flow / np.maximum(design_flow, 1e-12), 0.1, 1.0) ** 3
    return chiller, pumps + tower_pump + dry_pump, tower_fan + (0.0 if design == "towers" else dry)


def lake_loop(load, supply, water_t, p):
    """One facility water loop carrying `load` at `supply` C on once-through lake water at `water_t` C (once_through.py), in kW per kW of the water user's
    own load: (chiller power, pump power), both ending up as heat in the lake water. The lake water cools the loop through a plate exchanger while it is
    colder than the loop's return, as an economizer does (loop); a water-cooled chiller carries the rest with its condenser on the lake water leaving at
    water_t + rise_c. No fans: no air is moved. The lake water's pumps run at the tower loop's pressure, by analogy [A]."""
    ret = supply + p["water_rise"]
    free = _ramp(ret - (water_t + p["hx_approach"]), 0.0, ret - supply)
    chilled = load * (1 - free)
    evaporator = supply - 2.0
    cop = np.minimum(p["carnot_water"] * (evaporator + 273.15) / np.maximum(water_t + p["rise_c"] + 2.0 - evaporator, 1.0), CHILLER_COP_CAP["water"])
    chiller = chilled / cop
    pumps = (_pump_kw(load * free / (CP_WATER * p["water_rise"]), p["pump_econ_kpa"], p["pump_eff"])
             + _pump_kw(chilled / (CP_WATER * p["water_rise"]), p["pump_chw_kpa"], p["pump_eff"]))
    # the lake water carries all the loop's heat, its own pump's included: m x cp x rise = load + chiller + pumps + m x dP / eff
    pump_per_flow = p["pump_tower_kpa"] / (RHO_WATER * p["pump_eff"])
    lake_water = (load + chiller + pumps) / (CP_WATER * p["rise_c"] - pump_per_flow)
    return chiller, pumps + lake_water * pump_per_flow
