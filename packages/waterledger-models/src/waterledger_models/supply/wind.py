"""Hourly output of a hypothetical onshore wind project, per MW of nameplate (design 0014).

ERA5's 100 m wind (the u and v components, instantaneous at the hour) is taken to hub height by a power law, through a reference turbine's power
curve, less plant losses:

  speed at hub     |(u, v)| x (hub / 100 m)^alpha, alpha 0.10-0.20 around the 1/7 of neutral air over open land [A]
  turbine          the IEA 3.4 MW reference turbine (130 m rotor, 110 m hub, IEC class IIIa; Bortolotti et al. 2019, NREL/TP-5000-73492),
                   its power curve as NREL's turbine-models library gives it (github.com/NREL/turbine-models, commit e9e4ccc,
                   data/Onshore/IEA_Reference_3.4MW_130.csv, BSD-3-Clause): 0 under 3 m/s and above the 25 m/s cut-out, linear between points
  losses           wakes, availability and electrical losses, 10-20% [A] (design 0014)
  resource         a factor on the speed: delivered over modeled at EIA's 2024 fleet (design 0014, check 5;
                   docs/methods/power_supply/wind_check.py)

Checked against EIA's 2024 fleet (1,069 onshore plants, 144.7 GW, 34.1%), the chain at its cells matches at a speed factor of 0.99 overall at
110 m, 0.91-1.05 across the interior states with ten or more plants. It runs far low where the cell is calm on average: under LOW_WIND_MS at
100 m (passes and ridgetops in California, the Northwest, the Northeast and West Virginia), the fleet delivers 1.5 times the model or more,
since a 0.25-degree cell smooths the terrain that makes those sites windy. No factor fixes that, so such a place is flagged, not scaled.

A study's own forcing (design 0018): AORC, like most hydrologic forcings, gives the wind at 10 m, not 100 m. hourly_from_10m() takes it to the hub
by an exponent for each calendar month and local solar hour (shear_table(), from ERA5's own 10 m and 100 m wind at the place; Andrew, Nov 16):
the shear from 10 m changes with stability every day (ERA5 at the Clam River, 2019-2021: 0.15-0.18 at midday, 0.27-0.31 at night), and one
exponent would put the energy in the wrong hours. The hours are the forcing's; ERA5 only sets the table, a parameter. Not for AORC: its 10 m wind
steps down against ERA5's in 2018 at most places (design 0018, check A5), so a study on AORC runs wind on ERA5's 100 m wind with hourly() and
says so (decision 6); hourly_from_10m is for a forcing whose 10 m wind is one series, with a resource factor from its own check. The curve is at sea-level
density with no correction for the hour's [A], as on ERA5's path; it stays under the Betz limit at any density above 0.92 kg/m3
(tests/test_supply_wind_10m.py).
"""
import numpy as np

HUB_M = 110.0
ROTOR_M = 130.0                  # rotor diameter, m (Bortolotti et al. 2019)
RATED_KW = 3370.0
SPEED = (3, 3.5392, 4.0485, 4.5267, 4.973, 5.3862, 5.7654, 6.1098, 6.4186, 6.6912, 6.9269, 7.1252, 7.2857, 7.408, 7.4919, 7.5371, 7.5435,
         7.5758, 7.6468, 7.7563, 7.9041, 8.0899, 8.3132, 8.5735, 8.8703, 9.203, 9.5707, 9.8127, 10.408, 10.8757, 11.3748, 11.9041, 12.4625,
         13.0487, 13.6615, 14.2995, 14.9612, 15.6452, 16.35, 17.074, 17.8155, 18.5731, 19.3448, 20.1292, 20.9244, 21.7286, 22.5401, 23.357,
         24.1776, 25)
POWER_KW = (51.6, 123.4, 213.2, 318.8, 436.0, 560.9, 688.9, 819.1, 949.7, 1075.9, 1193.7, 1299.2, 1389.0, 1460.1, 1510.2, 1537.7, 1541.7,
            1561.6, 1605.9, 1675.9, 1773.5, 1901.5, 2063.3, 2263.3, 2506.6, 2799.3, 3148.5, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0,
            3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0,
            3370.1)
CUT_OUT = 25.0
RANGES = {
    "alpha": (0.10, 0.20),       # shear exponent, 100 m to hub [A]
    "losses": (0.10, 0.20),      # wakes, availability, electrical [A]
    "resource": (0.93, 1.05),    # delivered over modeled at EIA's 2024 fleet: 0.99 overall; Texas, Oklahoma and Wyoming 0.93 (spring
                                 # curtailment), Illinois and the newest interior plants 1.05 (0014, check 5)
}
LOW_WIND_MS = 5.5                # a cell's mean 100 m speed below which the chain runs far low against the fleet (check 5): a flag, not a factor


def power_curve(speed):
    """Turbine output as a share of its rating at hub-height wind speed, m/s."""
    s = np.asarray(speed, dtype=float)
    out = np.interp(s, SPEED, POWER_KW, left=0.0, right=0.0) / RATED_KW
    return np.where((s < SPEED[0]) | (s > CUT_OUT), 0.0, np.minimum(out, 1.0))


def hourly(u100, v100, p):
    """Output per MW of nameplate each hour (0-1) from ERA5's 100 m wind components, m/s. p: RANGES' parameters (scalars or (n, 1) arrays)."""
    speed = np.hypot(np.asarray(u100, float), np.asarray(v100, float)) * p["resource"] * (HUB_M / 100.0) ** p["alpha"]
    return power_curve(speed) * (1.0 - p["losses"])


def low_wind(u100, v100):
    """(mean 100 m speed, m/s, True where it is under LOW_WIND_MS) for a cell's hours."""
    m = float(np.mean(np.hypot(np.asarray(u100, float), np.asarray(v100, float))))
    return m, m < LOW_WIND_MS


# ---------------------------------------------------------------- a forcing with the wind at 10 m (design 0018)
ALPHA_LIMITS = (0.0, 0.6)        # a table's exponents are held here [A: a month-hour mean outside it is a data fault, not shear]


def solar_hour(times_utc, lon):
    """Local solar hour (0-23, the mean sun's) of each UTC hour stamp at the longitude."""
    t = np.asarray(times_utc, dtype="datetime64[h]").astype("int64")
    return np.mod(t + int(round(lon / 15.0)), 24)


def month(times_utc):
    return np.asarray(times_utc, dtype="datetime64[M]").astype("int64") % 12


def shear_table(times_utc, lon, u10, v10, u100, v100):
    """The 10 m to 100 m power-law exponent for each calendar month and local solar hour, shape (12, 24), from one place's hourly 10 m and
    100 m wind (ERA5's at the place's cell; design 0018 sets it from 1995-2024): ln(mean |U100| / mean |U10|) / ln 10 over that month's
    hours at that hour [A: the ratio of means, so a calm hour does not blow it up], held to ALPHA_LIMITS."""
    m, h = month(times_utc), solar_hour(times_utc, lon)
    s10, s100 = np.hypot(np.asarray(u10, float), np.asarray(v10, float)), np.hypot(np.asarray(u100, float), np.asarray(v100, float))
    k = m * 24 + h
    a = np.bincount(k, weights=s10, minlength=288)
    b = np.bincount(k, weights=s100, minlength=288)
    if (np.bincount(k, minlength=288) == 0).any():
        raise ValueError("the wind must cover every month and hour of the day")
    return np.clip(np.log(b / a) / np.log(10.0), *ALPHA_LIMITS).reshape(12, 24)


def hourly_from_10m(times_utc, lon, u10, v10, table, p):
    """Output per MW of nameplate each hour (0-1) from a forcing's 10 m wind components, m/s, at UTC hour stamps: the speed x resource, to the
    hub by (HUB_M / 10)^(table[month, solar hour] x shear_scale), through the power curve, less losses. table: shear_table() at the place.
    p: shear_scale, losses and resource (scalars or (n, 1) arrays); no resource factor is set for AORC's wind (design 0018, decision 6)."""
    alpha = np.asarray(table, float)[month(times_utc), solar_hour(times_utc, lon)]
    speed = np.hypot(np.asarray(u10, float), np.asarray(v10, float)) * p["resource"] * (HUB_M / 10.0) ** (alpha * p["shear_scale"])
    return power_curve(speed) * (1.0 - p["losses"])
