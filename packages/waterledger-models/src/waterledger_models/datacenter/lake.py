"""Lake-source (once-through) cooling: water taken from a Great Lake, run through heat exchangers once, and returned warmer.

Withdrawal follows from the heat load and the temperature rise: flow = heat / (density x specific heat x rise).
Nearly all of it is returned. The returned heat drives extra ("forced") evaporation from the lake surface, estimated with
the heat-balance method used by USGS for once-through power plants (Diehl et al. 2013, after Harbeck 1964 and Ward 1980):
the share of added heat that leaves as evaporation is dE / (dE + dC + dR), where evaporation and conduction share the same
wind function and radiation does not. Natural surface temperatures are NOAA GLERL daily long-term averages for each lake.
"""

import numpy as np

from waterledger_models.datacenter import cooling as cw

RHO, CP, LV = 1000.0, 4186.0, 2.45e6  # kg/m3, J/(kg K), J/kg
GAL_M3 = 264.172
P_MB = 1013.0
BOWEN = P_MB * 0.24 / (0.622 * 585.0)  # psychrometric constant in mb per deg C (cp of air 0.24 cal/g/K, L 585 cal/g)
SIGMA = 1.17e-7 / 86400.0  # cal/(cm2 s K4)
EMIS = 0.97

MPH_PER_MS = 2.23694
GLERL = "https://apps.glerl.noaa.gov/erddap/tabledap/glerlLTAvgTemp.csv?lake,dayOfYear,temperature"
GLERL_CODES = {"Lake Superior": "s", "Lake Michigan": "m", "Lake Huron": "h", "Lake Erie": "e", "Lake Ontario": "o"}

# Ranges: utilization reuses the cooling-water model; rise and wind are estimates (see methods page). All the campus's electricity leaves in the
# lake water, so the heat factor is also its PUE: IT, power losses, lighting, air handler fans and pumps from the cooling model's heat balance over
# its POWER ranges (5th to 95th percentile about 1.06-1.16), with no chillers or heat rejection fans because the lake water is colder than the loops.
RANGES = {
    "utilization": cw.RANGES["utilization"],
    "heat_factor": (1.05, 1.17),      # model 1.5, was 1.03-1.25
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
    Returns MGD per `mw` of IT capacity: withdrawn and returned (steady), forced evaporation average and its highest month, and the
    electricity from the same heat."""
    rng = np.random.default_rng(seed)
    t = np.asarray(water_temps, dtype=float)
    out = {"withdrawn": [], "evap_avg": [], "evap_peak_month": [], "er_avg": [], "power_mw_avg": [], "power_mw_peak_1in10": [], "pue_avg": [], "pue_peak_1in10": []}
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
        out["power_mw_avg"].append(heat_w / 1e6)                  # all of it becomes the heat in the lake water
        out["power_mw_peak_1in10"].append(mw * p["heat_factor"])  # every computer at capacity
        out["pue_avg"].append(p["heat_factor"])
        out["pue_peak_1in10"].append(p["heat_factor"])
    stat = lambda a: {"p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))}
    return {k: stat(v) for k, v in out.items()}


def withdrawal_m3s(it_mw, utilization, heat_factor, rise_c):
    """Water drawn through the exchangers, m3/s."""
    return it_mw * 1e6 * utilization * heat_factor / (RHO * CP * rise_c)


def forced_evaporation_m3s(it_mw, utilization, heat_factor, water_temp_c, wind_mph):
    """Extra evaporation from the lake caused by the returned heat, m3/s."""
    heat_w = it_mw * 1e6 * utilization * heat_factor
    return evaporation_ratio(water_temp_c, wind_mph) * heat_w / LV / RHO


def sample_parameters(n=200, seed=11):
    """The run_lake draws, vectorized: {name: array (n,)}."""
    lo = np.array([v[0] for v in RANGES.values()])
    hi = np.array([v[1] for v in RANGES.values()])
    draws = lo + (hi - lo) * np.random.default_rng(seed).random((n, len(RANGES)))
    return {k: draws[:, i] for i, k in enumerate(RANGES)}


def run_lake_ensemble(water_temps, n=200, seed=11, mw=100.0):
    """run_lake vectorized over runs, as an xarray Dataset (needs waterledger-models[ensemble]): withdrawn (steady), forced
    evaporation by day of year, its average and highest 30-day mean, and the evaporative share of the added heat, in million
    gallons a day per `mw` of IT capacity, plus each run's parameters."""
    import xarray as xr
    t = np.asarray(water_temps, dtype=float)
    p = {k: v[:, None] for k, v in sample_parameters(n, seed).items()}
    heat_w = mw * 1e6 * p["utilization"] * p["heat_factor"]
    mgd = 86400 * GAL_M3 / 1e6
    withdrawn = (heat_w / (RHO * CP * p["rise_c"]))[:, 0] * mgd
    er = evaporation_ratio(t[None, :], p["wind_mph"])
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


def glerl_temperatures(lake, source=GLERL):
    """NOAA GLERL long-term average daily surface temperature for one Great Lake, as an xarray DataArray on day of year."""
    import urllib.request

    import xarray as xr
    code = GLERL_CODES[lake]
    with urllib.request.urlopen(source, timeout=120) as r:
        text = r.read().decode()
    rows = [line.split(",") for line in text.splitlines()[2:] if line]
    days = sorted((int(d), float(v)) for c, d, v in rows if c == code)
    return xr.DataArray([v for _, v in days], coords={"dayofyear": [d for d, _ in days]}, dims="dayofyear",
                        name="water_temperature", attrs={"units": "degC", "lake": lake, "source": "NOAA GLERL"})
