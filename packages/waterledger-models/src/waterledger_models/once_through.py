"""Once-through cooling from a Great Lake, shared by every water user (design 0009, Nov 9, 2026): water taken from the lake, run through heat
exchangers once and returned warmer.

Withdrawal follows from the heat and the temperature rise: flow = heat / (density x specific heat x rise). Nearly all of it is returned. The
returned heat drives extra ("forced") evaporation from the lake surface, estimated with the heat-balance form USGS gives for once-through power
plants (Diehl et al. 2013, Eqs. 10-20, after Harbeck 1964 and Ward 1980): the share of added heat that leaves as evaporation is
dE / (dE + dC + dR), where evaporation and conduction share the same wind function and radiation does not. Natural surface temperatures are NOAA
GLERL daily long-term averages for each lake.

The wind function departs from USGS's practice. This module uses Ward's (1980), which USGS prints as an example (Eq. 14), while its own estimates for lakes used Webster
and Sherman (1995), and it did not use functions that reach zero at no wind (p. 27). Ward's is kept here because winds are sampled at 5-15 mph, away from zero, where USGS
puts the spread between wind functions at about 12% or less (p. 28), inside the error carried below. Webster and Sherman's coefficients are not in the USGS report and were not read.

What makes the heat is each water user's own (datacenter/lake.py, battery/physics.py). The code moved here from datacenter/lake.py unchanged, and
the data center's lake results are the same to the last bit (tests/test_lake.py).

A new plant drawing over 2 MGD with at least 25% of it for cooling falls under 40 CFR 125.81, whose new-facility rule holds the intake to about
what closed-cycle cooling would take. The numbers here are true to the physics; the rule is a flagged note where results are shown.
"""

import numpy as np

RHO, CP, LV = 1000.0, 4186.0, 2.45e6  # kg/m3, J/(kg K), J/kg
GAL_M3 = 264.172
P_MB = 1013.0
BOWEN = P_MB * 0.24 / (0.622 * 585.0)  # psychrometric constant in mb per deg C (cp of air 0.24 cal/g/K, L 585 cal/g)
SIGMA = 1.17e-7 / 86400.0  # cal/(cm2 s K4)
EMIS = 0.97

MPH_PER_MS = 2.23694
GLERL = "https://apps.glerl.noaa.gov/erddap/tabledap/glerlLTAvgTemp.csv?lake,dayOfYear,temperature"
GLERL_CODES = {"Lake Superior": "s", "Lake Michigan": "m", "Lake Huron": "h", "Lake Erie": "e", "Lake Ontario": "o"}

# (low, high) ranges of the lake's own parameters, sampled with each water user's: rise and wind are estimates (see the methods page).
RANGES = {
    "rise_c": (6.0, 10.0),
    "wind_mph": (5.0, 15.0),
    # USGS's error for the evaporation ratio from water surfaces: 18%, or 21% for once-through plants on the Great Lakes, where natural temperature adds uncertainty (p. 29). Model 1.7.
    "evap_error": (0.79, 1.21),
}


def _es(t):
    """Saturation vapor pressure over water, mb (Magnus)."""
    return 6.112 * np.exp(17.62 * t / (243.12 + t))


def evaporation_ratio(t, wind_mph):
    """Share of added heat lost by evaporation at natural water temperature t (deg C), linearized heat balance (Ward 1980; USGS 2013 eqs. 12-20), before evap_error."""
    f = 7.0e-8 * wind_mph  # Ward's wind function (USGS 2013 eq. 14), g/(cm2 s mb)
    de = (_es(t + 0.5) - _es(t - 0.5))  # mb per deg C
    d_e = 585.0 * f * de
    d_c = 585.0 * f * BOWEN
    d_r = 4 * EMIS * SIGMA * (t + 273.15) ** 3
    return d_e / (d_e + d_c + d_r)


def withdrawal_m3s(heat_w, rise_c):
    """Water drawn through the exchangers for `heat_w` watts at a rise of `rise_c`, m3/s."""
    return heat_w / (RHO * CP * rise_c)


def forced_evaporation_m3s(heat_w, water_temp_c, wind_mph, evap_error=1.0):
    """Extra evaporation from the lake caused by `heat_w` watts returned in the water, m3/s."""
    return evaporation_ratio(water_temp_c, wind_mph) * evap_error * heat_w / LV / RHO


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
