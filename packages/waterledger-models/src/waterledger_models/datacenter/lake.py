"""Lake-source (once-through) cooling at a data center: the campus's heat, all of it, into Great Lake water run through heat exchangers once.

The lake physics (withdrawal from heat and rise, forced evaporation after Diehl et al. 2013, GLERL temperatures) is shared by every water user
and lives in once_through.py; it moved there unchanged (design 0009). This module keeps what is the data center's: the heat, from IT load,
utilization and the campus's heat factor.
"""

import numpy as np

from waterledger_models import once_through as ot
from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter.physics import DRAWS, latin_hypercube
from waterledger_models.once_through import (BOWEN, CP, EMIS, GAL_M3, GLERL, GLERL_CODES, LV, MPH_PER_MS, P_MB, RHO, SIGMA,  # noqa: F401
                                             _es, evaporation_ratio, glerl_temperatures)

# Ranges: utilization reuses the cooling-water model; rise, wind and the evaporation error are the lake's own (once_through.RANGES). All the campus's electricity leaves in the
# lake water, so the heat factor is also its PUE: IT, power losses, lighting, air handler fans and pumps from the cooling model's heat balance over
# its POWER ranges (5th to 95th percentile about 1.06-1.16), with no chillers or heat rejection fans because the lake water is colder than the loops.
RANGES = {
    "utilization": cw.RANGES["utilization"],
    "heat_factor": (1.05, 1.17),      # model 1.5, was 1.03-1.25
    **ot.RANGES,
}


def run_lake(water_temps, n=DRAWS, seed=11, mw=100.0):
    """Monte Carlo over the parameter ranges for one lake. water_temps: 366 daily long-term average surface temperatures (deg C).
    Returns MGD per `mw` of IT capacity: withdrawn and returned (steady), forced evaporation average and its highest month, and the
    electricity from the same heat."""
    draws = sample_parameters(n, seed)
    t = np.asarray(water_temps, dtype=float)
    out = {"withdrawn": [], "evap_avg": [], "evap_peak_month": [], "er_avg": [], "power_mw_avg": [], "power_mw_peak_1in10": [], "pue_avg": [], "pue_peak_1in10": []}
    for i in range(n):
        p = {k: float(v[i]) for k, v in draws.items()}
        heat_w = mw * 1e6 * p["utilization"] * p["heat_factor"]
        m3s = heat_w / (RHO * CP * p["rise_c"])
        out["withdrawn"].append(m3s * 86400 * GAL_M3 / 1e6)
        er = evaporation_ratio(t, p["wind_mph"]) * p["evap_error"]
        evap = er * heat_w / LV / RHO * 86400 * GAL_M3 / 1e6  # MGD by day of year
        month = np.convolve(evap, np.ones(30) / 30, mode="valid")
        out["evap_avg"].append(float(evap.mean()))
        out["evap_peak_month"].append(float(month.max()))
        out["er_avg"].append(float(er.mean()))
        out["power_mw_avg"].append(heat_w / 1e6)                  # all of it becomes the heat in the lake water
        out["power_mw_peak_1in10"].append(mw * p["heat_factor"])  # every computer at capacity
        out["pue_avg"].append(p["heat_factor"])
        out["pue_peak_1in10"].append(p["heat_factor"])
    stat = lambda a: {"p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))}
    return {k: stat(v) for k, v in out.items()}


def withdrawal_m3s(it_mw, utilization, heat_factor, rise_c):
    """Water drawn through the exchangers, m3/s."""
    return it_mw * 1e6 * utilization * heat_factor / (RHO * CP * rise_c)


def forced_evaporation_m3s(it_mw, utilization, heat_factor, water_temp_c, wind_mph, evap_error=1.0):
    """Extra evaporation from the lake caused by the returned heat, m3/s."""
    heat_w = it_mw * 1e6 * utilization * heat_factor
    return evaporation_ratio(water_temp_c, wind_mph) * evap_error * heat_w / LV / RHO


def sample_parameters(n=DRAWS, seed=11):
    """The Monte Carlo draws for run_lake and run_lake_ensemble, a Latin hypercube like the cooling model's: {name: array (n,)}."""
    return latin_hypercube(RANGES, n, seed)


def run_lake_ensemble(water_temps, n=DRAWS, seed=11, mw=100.0):
    """run_lake vectorized over runs, as an xarray Dataset (needs waterledger-models[ensemble]): withdrawn (steady), forced
    evaporation by day of year, its average and highest 30-day mean, and the evaporative share of the added heat, in million
    gallons a day per `mw` of IT capacity, plus each run's parameters."""
    import xarray as xr
    t = np.asarray(water_temps, dtype=float)
    p = {k: v[:, None] for k, v in sample_parameters(n, seed).items()}
    heat_w = mw * 1e6 * p["utilization"] * p["heat_factor"]
    mgd = 86400 * GAL_M3 / 1e6
    withdrawn = (heat_w / (RHO * CP * p["rise_c"]))[:, 0] * mgd
    er = evaporation_ratio(t[None, :], p["wind_mph"]) * p["evap_error"]
    evap = er * heat_w / LV / RHO * mgd
    month = np.stack([np.convolve(e, np.ones(30) / 30, mode="valid") for e in evap])
    ds = xr.Dataset(
        {"withdrawn": (("run",), withdrawn), "evap_daily": (("run", "dayofyear"), evap),
         "evap_avg": (("run",), evap.mean(axis=1)), "evap_peak_month": (("run",), month.max(axis=1)),
         "er_avg": (("run",), er.mean(axis=1))},
        coords={"run": np.arange(n), "dayofyear": np.arange(1, t.size + 1)},
        attrs={"units": "million gallons per day", "it_capacity_mw": mw, "n_runs": n, "seed": seed})
    for k, v in p.items():
        ds[f"param_{k}"] = (("run",), v[:, 0])
    return ds
