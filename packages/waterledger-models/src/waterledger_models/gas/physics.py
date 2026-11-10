"""New gas plants (design 0014): a plant's output, fuel, heat and water hour by hour, for the hourly demand it is asked to serve.

A gas plant is a water user like the others (design 0010's standard treatment): its condenser heat goes through the shared heat rejection
(`heat_rejection`: towers, hybrid, assist, dry) or once-through lake water (`once_through`), exactly as a data center's or a cell plant's heat
does. Every plant is hypothetical: a technology, a number of identical units, a cooling design. None stands for a real plant. Each hour:

  inlet air: the dry-bulb, or with inlet evaporative cooling above its switch-on temperature, cooled toward the wet-bulb by the media's effectiveness
  unit capacity = ISO net rating x (1 - derate x max(0, T - T_ref)), at the inlet temperature (combustion turbine and combined cycle) or the
      dry-bulb (engines); a combined cycle's derate is its wet-cooled one in the hours its condenser is wet and its dry-cooled one otherwise
  units available: every unit, or with outages each hour's draw of units up at the sampled availability
  served = min(demand, available capacity); unserved = the rest, reported, never filled
  units online = enough to carry the hour, each at the same share of its capacity
  heat rate = ISO heat rate x (1 + slope x max(0, T - T_ref)) x (1 + part-load penalty x (1 - load) / 0.5), the penalty given at half load
  fuel = served x heat rate (HHV); auxiliary load = gross - net, from its share of gross
  condenser heat (combined cycle) = a share of fuel - net (NETL B31A: 391 of 628 MW); an engine on towers sends its jacket water's share there;
      the rest leaves in the exhaust, the stack and the generator
  water: the condenser heat through heat_rejection or once_through; NOx injection water (water-to-fuel mass ratio x fuel mass) from
      demineralized water, whose reject goes to the sewer; inlet cooling water (air flow x the rise in humidity ratio), evaporated

Energy closes: fuel = net + auxiliary + condenser + other (exhaust, stack, generator), and no term is negative. Mass closes: withdrawn =
consumed + returned, returned = to_sewer + to_source. Gas used to make the fuel, and water upstream of the plant, are outside the boundary
(design 0014, decision 11). Ranges and sources: RANGES and SOURCES below; the evidence is in docs/research/power-supply-water.md.

Departure from design 0014: the cooling's own fans and pumps are not worked from heat_rejection.loop, which models a facility water loop with
chillers, not a steam condenser; they are in the auxiliary share, with dry cooling's larger fans as its own range [A].
"""
import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models import once_through as ot

TECHNOLOGIES = ("cc", "ct", "engine", "fuel_cell")
# Every design the shared equipment allows (design 0010, item 1), with the exceptions stated: a simple-cycle turbine has no condenser (its heat
# leaves in the exhaust), engines run on radiators unless towers are chosen for the jacket water (EPA CHP Catalog p. 2-8), and fuel cells are dry.
DESIGNS = {"cc": ("towers", "hybrid", "assist", "dry", "lake"), "ct": ("none",), "engine": ("dry", "towers"), "fuel_cell": ("dry",)}
KWH_BTU = hr.KWH_BTU
GAS_BTU_LB = 22480.0          # natural gas HHV, Btu/lb: NETL Rev. 4a, B31A fuel input over fuel flow (Exhibit ES-4, p. 9)
KG_LB = 0.45359237
AIR_KG_H_PER_MW = 8040.0      # combustion air per MW of gas turbine output: NETL B31A stream 1, 3,834,126 kg/h for 477 MW (Exhibit 5-9, p. 564)
CC_TURBINE_SHARE = 477.0 / 740.0    # a combined cycle's gas turbine output over its gross output (NETL B31A)
T_REF = {"cc": 15.0, "ct": 15.0, "engine": 25.0, "fuel_cell": 15.0}   # C: ISO conditions; engines' derate starts about 77 F (EPA CHP Catalog p. 2-12)

# (low, high) by technology. Heat rates are HHV, net.
TECH = {
    "cc": {"heat_rate": (6200.0, 6450.0), "derate_wet": (0.003, 0.005), "derate_dry": (0.006, 0.008), "hr_slope": (0.0005, 0.002),
           "part_load_half": (0.15, 0.25), "cond_share": (0.55, 0.65), "aux_share": (0.017, 0.025)},
    "ct": {"heat_rate": (9100.0, 10500.0), "derate_wet": (0.009, 0.010), "derate_dry": (0.009, 0.010), "hr_slope": (0.003, 0.004),
           "part_load_half": (0.15, 0.25), "aux_share": (0.005, 0.015)},
    "engine": {"heat_rate": (8200.0, 9900.0), "derate_wet": (0.0015, 0.0021), "derate_dry": (0.0015, 0.0021), "hr_slope": (0.0, 0.001),
               "part_load_half": (0.08, 0.10), "jacket_share": (0.25, 0.40), "aux_share": (0.01, 0.03)},
    "fuel_cell": {"heat_rate": (6300.0, 9950.0), "derate_wet": (0.0, 0.0), "derate_dry": (0.0, 0.0), "hr_slope": (0.0, 0.0),
                  "part_load_half": (0.0, 0.05), "aux_share": (0.01, 0.03)},
}
# Shared by every technology
COMMON = {
    "availability": (0.90, 0.97),          # a unit's share of hours available [A]
    "demin_recovery": (0.70, 0.80),        # demineralized water out over water in [A]
    "inlet_eff": (0.85, 0.95),             # inlet evaporative media's effectiveness toward the wet-bulb [A]
    "inlet_on": (15.0, 25.0),              # C, dry-bulb above which inlet cooling runs [A]
    "dry_aux_extra": (0.005, 0.015),       # added auxiliary share for a dry or assist condenser's fans [A]
    "switch_on": (20.0, 30.0),             # C, dry-bulb at which a hybrid or assist condenser goes wet [A]
}
# Operating settings (heat_rejection.OPERATING): cycles of concentration 3-6, central 4 (NETL Rev. 4a p. 35; Diehl and Harris 2014 p. 12).
OPERATING = {"coc": (3.0, 6.0)}
# NOx control is a setting, not a draw: dry low-NOx (0) or water injection at a water-to-fuel mass ratio of 0.5-1.0 (AP-42 sec. 3.1.4.1, p. 3.1-6).
NOX = {"dln": 0.0, "water": (0.5, 1.0)}
SOURCES = {
    "heat_rate": "EIA AEO2023 Table 1; NETL Rev. 4a Exhibit ES-4; EPA CHP Catalog Tables 2-2, 3-2, 6-3",
    "derate_wet": "EPA CHP Catalog p. 3-10 (turbines), p. 2-12 (engines); Sathaye et al. 2011 p. 11 (combined cycle, wet)",
    "derate_dry": "Sathaye et al. 2011 p. 11 (combined cycle, dry, about 0.7%) [A]",
    "hr_slope": "EPA CHP Catalog p. 3-10 (turbines); Meng and Sanders 2019 sec. 4 (combined cycle) [A]",
    "part_load_half": "EPA CHP Catalog p. 2-11 (engines); turbines and combined cycle [A]",
    "cond_share": "NETL Rev. 4a Exhibit 5-9 p. 564 (B31A: 391 of 628 MW), sampled around it [A]",
    "jacket_share": "[A]: an engine's jacket and lube oil heat as a share of its losses, for the towers design",
    "aux_share": "NETL Rev. 4a ES-4 (B31A: 13 of 740 MW gross, 1.8%) for combined cycle; [A] for the others",
    "availability": "[A] (NERC GADS not yet read)", "demin_recovery": "[A]", "inlet_eff": "[A]", "inlet_on": "[A]",
    "dry_aux_extra": "[A]", "switch_on": "[A]",
    "coc": "NETL Rev. 4a p. 35; Diehl and Harris 2014 p. 12",
    "nox_ratio": "AP-42 sec. 3.1.4.1, p. 3.1-6 (water-to-fuel weight ratio under one)",
}


def ranges(technology, design, nox="dln"):
    """Every sampled parameter for this technology and design: its own, the shared ones, and the heat rejection's or the lake's where it has one."""
    if technology not in TECHNOLOGIES:
        raise ValueError(f"technology must be one of {TECHNOLOGIES}")
    if design not in DESIGNS[technology]:
        raise ValueError(f"{technology} designs are {DESIGNS[technology]}, not {design!r}")
    r = {**TECH[technology], **COMMON}
    if design in ("towers", "hybrid", "assist"):
        r.update({**hr.EQUIPMENT, **OPERATING})
    if design == "lake":
        r.update(ot.RANGES)
    if nox == "water":
        if technology not in ("ct", "cc"):
            raise ValueError("water injection is for combustion turbines (simple cycle or combined cycle)")
        r["nox_ratio"] = NOX["water"]
    elif nox != "dln":
        raise ValueError("nox must be 'dln' or 'water'")
    return r


def central_parameters(technology, design, nox="dln"):
    return {k: (a + b) / 2 for k, (a, b) in ranges(technology, design, nox).items()}


def _humidity_ratio(tdb, rh):
    return hr._humidity_ratio(hr._saturation_kpa(tdb) * np.clip(rh, 0.0, 100.0) / 100.0)


def hourly(demand_mw, tdb, twb, rh, technology, design, p, units, unit_mw, inlet_cooling=False, water_t=None, available=None):
    """Each hour, for `units` identical units of `unit_mw` net MW at ISO serving `demand_mw`: a dict of MW and gallons for the hour (module
    docstring). `available`: units up each hour (outages(), or None for every unit). The lake design needs `water_t`, the lake's surface
    temperature each hour, C; hybrid and assist need p["design_db"] (heat_rejection.for_location).

    MW: "served", "unserved", "fuel", "gross", "aux", "condenser", "other", "capacity" (available), "units_online", "inlet_t" (C).
    Gallons: "withdrawn", "consumed", "returned" (= "to_sewer" + "to_source"), and the parts "evap", "drift", "blow", "once_through", "lake_evap",
    "nox", "nox_reject", "inlet"."""
    if technology not in TECHNOLOGIES or design not in DESIGNS[technology]:
        raise ValueError(f"no {technology!r} plant with design {design!r}: {DESIGNS}")
    if design == "lake" and water_t is None:
        raise ValueError("the lake design needs the lake's surface temperature each hour (water_t)")
    tdb, twb, rh = (np.asarray(x, dtype=float) for x in (tdb, twb, rh))
    demand = np.maximum(np.asarray(demand_mw, dtype=float) * np.ones_like(tdb), 0.0)
    ones = np.ones_like(tdb)
    turbine = technology in ("ct", "cc")
    # inlet air: evaporative media cool it toward the wet-bulb above their switch-on temperature
    cooled = inlet_cooling and turbine
    inlet_t = np.where(tdb >= p["inlet_on"], tdb - p["inlet_eff"] * (tdb - twb), tdb) if cooled else tdb
    # the condenser's wet share: towers and the lake all wet, dry none, hybrid a ramp from its switch-on to the design dry-bulb; assist's pads ahead
    # of an air-cooled condenser count as dry for the derate, at the air the pads leave
    if design in ("towers", "lake"):
        wet = ones
    elif design == "hybrid":
        wet = hr.wet_share(tdb, "hybrid", p, p["switch_on"])
    else:
        wet = 0.0 * ones
    t_ref = T_REF[technology]
    t = inlet_t if turbine else tdb
    t_dry = hr.coil_air(tdb, twb, "assist", p, p["switch_on"]) if design == "assist" else t
    derate = wet * p["derate_wet"] * np.maximum(t - t_ref, 0.0) + (1.0 - wet) * p["derate_dry"] * np.maximum(t_dry - t_ref, 0.0)
    unit_cap = unit_mw * np.clip(1.0 - derate, 0.0, None)
    up = units * ones if available is None else np.asarray(available, dtype=float)
    capacity = up * unit_cap
    served = np.minimum(demand, capacity)
    unserved = demand - served
    online = np.where(served > 0, np.ceil(served / np.maximum(unit_cap, 1e-12) - 1e-9), 0.0)
    load = np.where(online > 0, served / np.maximum(online * unit_cap, 1e-12), 1.0)
    heat_rate = p["heat_rate"] * (1.0 + p["hr_slope"] * np.maximum(t - t_ref, 0.0)) * (1.0 + p["part_load_half"] * (1.0 - load) / 0.5)
    fuel = served * heat_rate / KWH_BTU                   # MW of fuel (HHV): MW x Btu/kWh / (Btu/kWh per kW)
    # a combined cycle's dry or assist condenser, and the dry part of a hybrid's, adds its fans; engines' radiators and fuel cells are in aux_share
    aux_share = p["aux_share"] + (p["dry_aux_extra"] * (1.0 - wet) if technology == "cc" and design != "lake" else 0.0)
    gross = served / (1.0 - aux_share)
    aux = gross - served
    losses = fuel - served
    if technology == "cc":
        condenser = p["cond_share"] * losses
    elif technology == "engine" and design == "towers":
        condenser = p["jacket_share"] * losses
    else:
        condenser = 0.0 * ones
    other = fuel - served - aux - condenser
    # water: the condenser's heat through the shared heat rejection or the lake, per hour
    btu = condenser * 1000.0 * KWH_BTU
    gal_hour = 3600.0 * ot.GAL_M3
    zero = 0.0 * ones
    evap = drift = blow = once = lake_evap = zero
    if design in ("towers", "hybrid"):
        evap, drift, blow = hr.tower_water(btu, tdb, wet, p)
    elif design == "assist":
        evap, drift, blow = hr.pad_water(btu, tdb, twb, p, p["switch_on"])
    elif design == "lake":
        once = ot.withdrawal_m3s(condenser * 1e6, p["rise_c"]) * gal_hour * ones
        lake_evap = ot.forced_evaporation_m3s(condenser * 1e6, water_t, p["wind_mph"], p["evap_error"]) * gal_hour
    # NOx injection: demineralized water at the water-to-fuel mass ratio, all of it out the stack; the demineralizer's reject to the sewer
    fuel_kg = fuel * 1000.0 * KWH_BTU / GAS_BTU_LB * KG_LB            # kg of gas an hour
    nox = p.get("nox_ratio", 0.0) * fuel_kg / hr.KG_GAL
    nox_reject = nox * (1.0 / p["demin_recovery"] - 1.0)
    # inlet cooling: the water the air takes up, at constant wet-bulb (sensible heat to latent), all of it evaporated
    if cooled:
        turbine_mw = gross * (CC_TURBINE_SHARE if technology == "cc" else 1.0)
        inlet = AIR_KG_H_PER_MW * turbine_mw * hr.CP_AIR * (tdb - inlet_t) / hr.LATENT_KJ / hr.KG_GAL
    else:
        inlet = zero
    to_sewer = blow + nox_reject
    to_source = once - lake_evap
    return {
        "served": served, "unserved": unserved, "fuel": fuel, "gross": gross, "aux": aux, "condenser": condenser, "other": other,
        "capacity": capacity, "units_online": online, "inlet_t": inlet_t,
        "evap": evap, "drift": drift, "blow": blow, "once_through": once, "lake_evap": lake_evap, "nox": nox, "nox_reject": nox_reject, "inlet": inlet,
        "withdrawn": evap + drift + blow + once + nox + nox_reject + inlet,
        "consumed": evap + drift + lake_evap + nox + inlet,
        "returned": to_sewer + to_source, "to_sewer": to_sewer, "to_source": to_source,
    }


def outages(units, availability, n_hours, seed):
    """Units up each hour: each unit is up in an hour with probability `availability`, drawn independently [A: forced outages run for days, not
    hours, so this understates runs of unserved hours while giving the right share of them]."""
    rng = np.random.default_rng(seed)
    return rng.binomial(int(units), float(availability), size=int(n_hours)).astype(float)
