"""The cooling Monte Carlo's hourly heat balance and water, compiled (model 1.10's runs; methods log, Nov 8, 2026).

cooling.run_location works each draw's hours through physics.hourly_heat_power, hourly_rates and hourly_water_with_air: about sixty NumPy
steps a block, each over every hour, for three loads (the run's, the peak day's, every computer at capacity). Here the same calculation
runs one hour at a time in one compiled pass (Numba), so there are no in-between arrays and no Python between steps. The weather's own
terms (saturation pressure at the dry-bulb, saturated enthalpy at the wet-bulb, the evaporative ratio's curve) don't depend on a draw, so
they are worked out once per location with physics' own NumPy functions and passed in.

The arithmetic follows physics.py step by step, in the same order, so the two agree to the last bit or two: exp and pow come from the
compiler's math library rather than NumPy's, so a value can differ by about 1e-15 of itself. tests/test_kernel.py holds every design in
every plant to 1e-12 of physics.py, which is the reference: a change to the physics there has to be made here too, or that test fails.
Water limits, the BMI and the ensembles use physics.py only.
"""
import math

import numpy as np
from numba import njit

from waterledger_models.datacenter import physics as ph

DESIGN_CODE = {"dry": 0, "assist": 1, "hybrid": 2, "towers": 3}

# per-load values, worked out in Python from the draw's parameters (the same scalar arithmetic physics.py does), in this order
FIELDS = ("q", "air", "kg_s", "room", "crah", "air_water", "liquid_water", "switch", "hybrid_full", "low", "high", "humidify_share",
          "supply_air", "water_rise", "tower_approach", "hx_approach", "dc_approach", "range_f", "carnot_water", "carnot_air",
          "pump_econ_kpa", "pump_chw_kpa", "pump_tower_kpa", "pump_eff", "cp_glycol", "rho_glycol", "design_potential", "design_min",
          "tower_fan_pa", "fan_eff", "dc_fan_pa", "assist_dt_air", "assist_eff", "er_adj", "drift", "coc", "assist_bleed", "topup", "lg")
F = {k: i for i, k in enumerate(FIELDS)}
# physics.py's constants, which Numba takes in as fixed values when it compiles
RHO_AIR, RHO_WATER, CP_AIR, CP_WATER, LATENT_KJ = ph.RHO_AIR, ph.RHO_WATER, ph.CP_AIR, ph.CP_WATER, ph.LATENT_KJ
KWH_BTU, HFG, LB_GAL, KG_GAL, DEHUMIDIFY_WATER = ph.KWH_BTU, ph.HFG, ph.LB_GAL, ph.KG_GAL, ph.DEHUMIDIFY_WATER
COP_WATER, COP_AIR = ph.CHILLER_COP_CAP["water"], ph.CHILLER_COP_CAP["air"]


def load_values(p, design):
    """One load's values for the kernel, from a draw's parameters (scalars, after physics.for_location), as physics.py works them out."""
    if "wet_frac" in p:
        raise ValueError("the compiled heat balance has no water limits; use physics.hourly_limited")
    q = 1.0 + (1.0 / p["ups"] - 1.0) + (1.0 / (1.0 - p["dist_loss"]) - 1.0) + p["light"]
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    kg_s = p["oa_cfm_per_mw"] / 1000.0 * ph.CFM_M3S * ph.RHO_AIR / p["utilization"]
    room = q - (1.0 - air)
    crah = ph._fan_kw(room / (ph.CP_AIR * p["air_rise"]) + kg_s, p["crah_pa"], p["fan_eff"])
    tower_range = p["range_f"] / 1.8
    design_hot = ph.TOWER_DESIGN_WB + p["tower_approach"] + tower_range
    design_potential = ph._saturated_enthalpy(design_hot) - ph._saturated_enthalpy(ph.TOWER_DESIGN_WB)
    cp_glycol, rho_glycol = ph.glycol_properties(p)
    v = {"q": q, "air": air, "kg_s": kg_s, "room": room, "crah": crah, "air_water": ph.air_loop_water(p), "liquid_water": p["liquid_water"],
         "switch": ph.switch_point(p), "hybrid_full": ph.hybrid_full(p) if design == "hybrid" else 0.0,
         "low": ph._humidity_ratio(ph._saturation_kpa(ph.DEW_LOW)), "high": ph._humidity_ratio(ph._saturation_kpa(ph.DEW_HIGH)),
         "cp_glycol": cp_glycol, "rho_glycol": rho_glycol, "design_potential": design_potential,
         "design_min": np.minimum(p["lg"], design_potential / (ph.CP_WATER * tower_range)),
         "topup": p["fill_gal_per_mw"] * p["topup"] / 365.0 / (24 * 1000 * p["utilization"])}
    return np.array([float(v[k]) if k in v else float(p[k]) for k in FIELDS])


def weather_terms(tdb, twb):
    """The weather's own terms, once per location: saturation pressure at the dry-bulb, kPa; saturated enthalpy at the wet-bulb, kJ/kg;
    the evaporative ratio's curve before its adjustment and limits (physics.evaporative_ratio)."""
    er = 1 - (-0.000279 * tdb ** 3 + 0.00109 * tdb ** 2 - 0.345 * tdb + 26.7) / 100
    return ph._saturation_kpa(tdb), ph._saturated_enthalpy(twb), er


@njit(cache=True, error_model="numpy", inline="always")
def _clip(x, lo, hi):
    return min(max(x, lo), hi)


@njit(cache=True, error_model="numpy", inline="always")
def _cube(x):
    return x * x * x


@njit(cache=True, error_model="numpy", inline="always")
def _hsat(t):
    es = 0.6112 * math.exp(17.62 * t / (243.12 + t))
    w = 0.622 * es / (101.325 - es)
    return 1.006 * t + w * (2501.0 + 1.86 * t)


@njit(cache=True, error_model="numpy", inline="always")
def _fan(kg_s, pa, eff):
    return kg_s / RHO_AIR * pa / eff / 1000.0


@njit(cache=True, error_model="numpy", inline="always")
def _pump(kg_s, kpa, eff):
    return kpa * kg_s / (RHO_WATER * eff)


@njit(cache=True, error_model="numpy")
def _loop_terms(supply, t, wb, hsat_wb, coil_air, wet, v):
    """The parts of physics._loop that don't depend on the load, for one hour: (supply, return, economizer share, water- and air-cooled
    chiller COP, the tower's enthalpy difference, the dry coil's air rise). The three loads differ only in utilization, so each hour works
    these out once for all three."""
    ret = supply + v[13]
    outside = wet * (wb + v[14] + v[15]) + (1 - wet) * (coil_air + v[16] + v[15])
    free = _clip(((ret - outside) - 0.0) / ((ret - supply) - 0.0), 0.0, 1.0)
    evaporator = supply - 2.0
    water_cooled = min(v[18] * (evaporator + 273.15) / max(wb + v[14] + v[17] / 1.8 + 2.0 - evaporator, 1.0), COP_WATER)
    air_cooled = min(v[19] * (evaporator + 273.15) / max(coil_air + 12.0 - evaporator, 1.0), COP_AIR)
    hot_water = max(wb + v[14] + v[17] / 1.8, ret - v[15])
    rise = max(ret - v[15] - v[16] - coil_air, v[31])
    return free, water_cooled, air_cooled, _hsat(hot_water) - hsat_wb, rise


@njit(cache=True, error_model="numpy")
def _loop(load, k, wet, towers, v):
    """physics._loop for one hour at one load, from its _loop_terms k: (chiller, pumps, fans), kW per IT kW."""
    free, water_cooled, air_cooled, enthalpy, rise = k
    chilled = load * (1 - free)
    chiller = chilled * (wet / water_cooled + (1 - wet) / air_cooled)
    econ_pump = _pump(load * free / (CP_WATER * v[13]), v[20], v[23])
    pumps = econ_pump + _pump(chilled / (CP_WATER * v[13]), v[21], v[23])
    pump_per_flow = v[22] / (RHO_WATER * v[23])
    tower_range = v[17] / 1.8
    tower_water = (load + chiller + pumps) * wet / (CP_WATER * tower_range - wet * pump_per_flow)
    tower_pump = tower_water * pump_per_flow
    glycol_per_flow = v[22] / (v[25] * v[23])
    glycol = (load * free + econ_pump) * (1 - wet) / (v[24] * tower_range - (1 - wet) * glycol_per_flow)
    dry_pump = glycol * glycol_per_flow
    design_water = load / (CP_WATER * tower_range)
    design_air = design_water / v[27]
    air_share = tower_water / max(design_water, 1e-12) * v[26] / enthalpy
    tower_fan = _fan(design_air, v[28], v[29]) * _cube(_clip(air_share, 0.1, 1.0)) * (1.0 if wet > 0 else 0.0)
    design_flow = load / (CP_AIR * v[31])
    flow = load * free * (1 - wet) / (CP_AIR * rise)
    dry = _fan(design_flow, v[30], v[29]) * _cube(_clip(flow / max(design_flow, 1e-12), 0.1, 1.0))
    return chiller, pumps + tower_pump + dry_pump, tower_fan + (0.0 if towers else dry)


@njit(cache=True, error_model="numpy")
def _hour(t, wb, h, er_base, design, outside_w, indoors, coil_air, wet, k1, k2, k3, v):
    """One hour at one load: (PUE, withdrawn, consumed, returned, condensate), the PUE as facility power per IT kW and the water in gallons
    per IT kWh, as physics.hourly_heat_power, hourly_rates and hourly_water_with_air give them. k1, k2, k3: the air, liquid and
    dehumidifying loops' _loop_terms."""
    # outside air (physics._outside_air and hourly_outside_air_heat)
    kg_s = v[2]
    sensible = kg_s * CP_AIR * (t - v[12])
    outside = sensible - kg_s * LATENT_KJ * max(indoors - outside_w, 0.0)
    latent = kg_s * LATENT_KJ * max(outside_w - indoors, 0.0)
    # the heat balance (physics.hourly_heat_power)
    sw = v[7]
    q, air, room, crah = v[0], v[1], v[3], v[4]
    air_load = room + crah + outside
    power = q + crah + 0.0
    heat = q + crah + outside + latent
    towers = design == 3
    c, pu, fa = _loop(max(air_load, 0.0), k1, wet, towers, v)
    power = power + c + pu + fa
    heat = heat + c + pu
    c, pu, fa = _loop(1.0 - air + min(air_load, 0.0), k2, wet, towers, v)
    power = power + c + pu + fa
    heat = heat + c + pu
    if latent != 0.0:                 # a loop with no heat gives exact zeros, so the dehumidifying coil's is skipped in the hours it has none
        c, pu, fa = _loop(latent, k3, wet, towers, v)
        power = power + c + pu + fa
        heat = heat + c + pu
    # the water (physics._rate_parts)
    btu = KWH_BTU * heat
    evap_full = btu * _clip(er_base + v[33], 0.55, 1.0) / HFG / LB_GAL
    circ = btu * wet / (LB_GAL * v[17])
    evap = evap_full * wet
    drift = circ * v[34]
    blow = evap / (v[35] - 1.0) - drift
    if design == 1:
        depr = v[32] * max(t - wb, 0.0)
        share = _clip(depr / max(sw + v[31] - t + depr, 1e-6), 0.0, 1.0)
        evap = btu * share / HFG / LB_GAL * (1.0 if t >= sw else 0.0)
        drift = 0.0
        blow = evap * v[36]
    topup = v[37] * 1.0
    humidify = kg_s * max(indoors - outside_w, 0.0) * 3600.0 / KG_GAL
    condensate = kg_s * max(outside_w - indoors, 0.0) * 3600.0 / KG_GAL
    withdrawn = evap + drift + blow + topup + humidify
    consumed = evap + drift + topup + humidify
    returned = blow + condensate
    return power, withdrawn, consumed, returned, condensate


@njit(cache=True, error_model="numpy")
def _run(tdb, twb, rh, es_t, hsat_wb, er_base, design, v, v_peak, v_capacity, out):
    k3 = (0.0, 0.0, 0.0, 0.0, 0.0)
    for i in range(tdb.shape[0]):
        t, wb, h, hs, er = tdb[i], twb[i], rh[i], hsat_wb[i], er_base[i]
        # what the three loads share: the outside air's moisture, the coil's air, the wet share and the loops' load-free terms
        vapor = es_t[i] * h / 100.0
        outside_w = 0.622 * vapor / (101.325 - vapor)
        indoors = min(outside_w, v[10]) + v[11] * max(v[9] - outside_w, 0.0)
        sw = v[7]
        if design == 1:
            coil_air = t - (v[32] * max(t - wb, 0.0) * (1.0 if t >= sw else 0.0))
        else:
            coil_air = t - 0.0
        if design == 3:
            wet = 1.0
        elif design == 2:
            wet = _clip((t - sw) / (v[8] - sw), 0.0, 1.0) * 1.0
        else:
            wet = 0.0
        k1 = _loop_terms(v[5], t, wb, hs, coil_air, wet, v)
        k2 = _loop_terms(v[6], t, wb, hs, coil_air, wet, v)
        if outside_w - indoors > 0.0:
            k3 = _loop_terms(DEHUMIDIFY_WATER, t, wb, hs, coil_air, wet, v)
        pue, w, c, r, cond = _hour(t, wb, h, er, design, outside_w, indoors, coil_air, wet, k1, k2, k3, v)
        pue_p, wp, cp, rp, condp = _hour(t, wb, h, er, design, outside_w, indoors, coil_air, wet, k1, k2, k3, v_peak)
        out[0, i], out[1, i], out[2, i], out[3, i], out[4, i] = pue, w, c, r, cond
        out[5, i], out[6, i], out[7, i], out[8, i] = wp, cp, rp, condp
        out[9, i] = _hour(t, wb, h, er, design, outside_w, indoors, coil_air, wet, k1, k2, k3, v_capacity)[1]
        out[10, i] = pue_p


# the values a load's utilization changes; everything else is the same for the three loads, which _run relies on
BY_LOAD = ("kg_s", "crah", "topup")


def hourly_run(tdb, twb, rh, weather, design, p, at_peak):
    """cooling._hourly_run, compiled: the same eleven hourly series (PUE; withdrawn, consumed, returned and condensate at the run's load and
    at its peak load; withdrawn with every computer at capacity; PUE at the peak load). weather is weather_terms(tdb, twb)."""
    out = np.empty((11, len(tdb)))
    loads = [load_values(q, design) for q in (p, at_peak, {**p, "utilization": 1.0})]
    fixed = [F[k] for k in FIELDS if k not in BY_LOAD]
    if not all(np.array_equal(x[fixed], loads[0][fixed]) for x in loads[1:]):
        raise ValueError("the three loads may differ only in utilization")
    _run(tdb, twb, rh, *weather, DESIGN_CODE[design], *loads, out)
    return list(out)
