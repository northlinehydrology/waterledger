"""Lake-source (once-through) cooling: water taken from a Great Lake, run through heat exchangers once, and returned warmer.

Withdrawal follows from the heat load and the temperature rise: flow = heat / (density x specific heat x rise).
Nearly all of it is returned. The returned heat drives extra ("forced") evaporation from the lake surface, estimated with
the heat-balance method used by USGS for once-through power plants (Diehl et al. 2013, after Harbeck 1964 and Ward 1980):
the share of added heat that leaves as evaporation is dE / (dE + dC + dR), where evaporation and conduction share the same
wind function and radiation does not. Natural surface temperatures are NOAA GLERL daily long-term averages for each lake.
"""
import math

import numpy as np

from waterledger_models.datacenter import cooling as cw

RHO, CP, LV = 1000.0, 4186.0, 2.45e6  # kg/m3, J/(kg K), J/kg
GAL_M3 = 264.172
P_MB = 1013.0
BOWEN = P_MB * 0.24 / (0.622 * 585.0)  # psychrometric constant in mb per deg C (cp of air 0.24 cal/g/K, L 585 cal/g)
SIGMA = 1.17e-7 / 86400.0  # cal/(cm2 s K4)
EMIS = 0.97

# Ranges: utilization and heat factor reuse the cooling-water model; rise and wind are estimates (see methods page).
RANGES = {
    "utilization": cw.RANGES["utilization"],
    "heat_factor": (cw.RANGES["hf_econ"][0], cw.RANGES["hf_chiller"][1]),
    "rise_c": (6.0, 10.0),
    "wind_mph": (5.0, 15.0),
}


def _es(t):
    """Saturation vapor pressure over water, mb (Magnus)."""
    return 6.112 * np.exp(17.62 * t / (243.12 + t))


def evaporation_ratio(t, wind_mph):
    """Share of added heat lost by evaporation at natural water temperature t (deg C), linearized heat balance (Ward 1980; USGS 2013 eq. 12-20)."""
    f = 7.0e-8 * wind_mph  # Ward wind function, cal/(cm2 s mb)
    de = (_es(t + 0.5) - _es(t - 0.5))  # mb per deg C
    d_e = 585.0 * f * de
    d_c = 585.0 * f * BOWEN
    d_r = 4 * EMIS * SIGMA * (t + 273.15) ** 3
    return d_e / (d_e + d_c + d_r)


def run_lake(water_temps, n=200, seed=11, mw=100.0):
    """Monte Carlo over the parameter ranges for one lake. water_temps: 366 daily long-term average surface temperatures (deg C).
    Returns MGD per `mw` of IT capacity: withdrawn and returned (steady), forced evaporation average and its highest month."""
    rng = np.random.default_rng(seed)
    t = np.asarray(water_temps, dtype=float)
    out = {"withdrawn": [], "evap_avg": [], "evap_peak_month": [], "er_avg": []}
    for _ in range(n):
        p = {k: rng.uniform(*v) for k, v in RANGES.items()}
        heat_w = mw * 1e6 * p["utilization"] * p["heat_factor"]
        m3s = heat_w / (RHO * CP * p["rise_c"])
        out["withdrawn"].append(m3s * 86400 * GAL_M3 / 1e6)
        er = evaporation_ratio(t, p["wind_mph"])
        evap = er * heat_w / LV / RHO * 86400 * GAL_M3 / 1e6  # MGD by day of year
        month = np.convolve(evap, np.ones(30) / 30, mode="valid")
        out["evap_avg"].append(float(evap.mean()))
        out["evap_peak_month"].append(float(month.max()))
        out["er_avg"].append(float(er.mean()))
    stat = lambda a: {"p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))}
    return {k: stat(v) for k, v in out.items()}
