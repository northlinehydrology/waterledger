"""Hourly AC output of a hypothetical utility PV project, per MW AC, by the PVWatts method (Dobos 2014, NREL/TP-6A20-62641; design 0014).

The weather is ERA5's: global and direct (beam) horizontal radiation as means over the preceding hour, so the sun is placed at mid-hour; diffuse
is their difference, so no decomposition model is needed. Each hour:

  sun position         NOAA's solar calculator equations (after Meeus 1991), at mid-hour, UTC
  beam normal          direct horizontal / cos(zenith), 0 with the sun under 5 degrees [A]
  plane of array       single-axis tracking on a north-south axis with backtracking (Marion and Dobos 2013; Anderson and Mikofski 2020),
                       or fixed tilt facing south; sky diffuse by Hay and Davies (1980); ground reflection at the albedo
  cover reflection     the physical incidence angle modifier on the beam (De Soto et al. 2006), PVWatts' choice
  cell temperature     Sandia's model for open-rack glass-polymer modules (King et al. 2004), with the wind at 10 m from ERA5's 100 m by a
                       1/7 power law [A]
  DC                   PVWatts: nameplate x effective irradiance / 1,000 W/m2 x (1 + gamma (T_cell - 25)), less system losses
  AC                   PVWatts' inverter curve, clipped at the AC rating; DC over AC is the inverter loading ratio

pvlib (Holmgren et al. 2018) is the test reference: tests/test_supply.py holds this chain to pvlib's functions hour by hour on the same inputs.
Parameters: RANGES, each [A] unless sourced in docs/research/power-supply-water.md.
"""
import numpy as np

RANGES = {
    "losses": (0.10, 0.18),        # system losses, PVWatts' default 14.08% (Dobos 2014, Table 3) [A: the range]
    "gamma": (-0.0040, -0.0034),   # power temperature coefficient, 1/K; PVWatts' standard module -0.0037 [A: the range]
    "ilr": (1.2, 1.4),             # inverter loading ratio, DC over AC [A]
    "albedo": (0.15, 0.25),        # ground reflectance [A]
    "resource": (0.76, 0.92),      # delivered over modeled: EIA's 2024 tracking fleet (944 plants, 24.1%) against this chain on ERA5 at
                                   # their cells (28.5%), 0.84 overall and 0.76-0.92 across the states with ten or more plants. It holds ERA5's
                                   # radiation bias with snow, curtailment, outages and age, which the check can't separate (0014, check 5;
                                   # docs/methods/power_supply/pv_check.py)
}
GCR = 0.35                         # ground coverage ratio of a tracking array [A]
MAX_ANGLE = 60.0                   # tracker rotation limit, degrees [A]
ETA_INV = 0.96                     # PVWatts' nominal inverter efficiency (Dobos 2014)
ETA_INV_REF = 0.9637
SOLAR_CONSTANT = 1366.1            # W/m2, as pvlib's get_extra_radiation


def _rad(x):
    return np.radians(x)


def solar_position(times_utc, lat, lon):
    """(zenith, azimuth), degrees, for UTC datetime64 times: NOAA's solar calculator (after Meeus 1991). Azimuth east of north."""
    t = np.asarray(times_utc, dtype="datetime64[s]")
    jd = t.astype("int64") / 86400.0 + 2440587.5
    jc = (jd - 2451545.0) / 36525.0
    l0 = np.mod(280.46646 + jc * (36000.76983 + jc * 0.0003032), 360.0)
    m = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    c = (np.sin(_rad(m)) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + np.sin(_rad(2 * m)) * (0.019993 - 0.000101 * jc)
         + np.sin(_rad(3 * m)) * 0.000289)
    true_long = l0 + c
    omega = 125.04 - 1934.136 * jc
    app_long = true_long - 0.00569 - 0.00478 * np.sin(_rad(omega))
    obliq0 = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    obliq = obliq0 + 0.00256 * np.cos(_rad(omega))
    decl = np.degrees(np.arcsin(np.sin(_rad(obliq)) * np.sin(_rad(app_long))))
    y = np.tan(_rad(obliq / 2)) ** 2
    eot = 4 * np.degrees(y * np.sin(2 * _rad(l0)) - 2 * e * np.sin(_rad(m)) + 4 * e * y * np.sin(_rad(m)) * np.cos(2 * _rad(l0))
                         - 0.5 * y * y * np.sin(4 * _rad(l0)) - 1.25 * e * e * np.sin(2 * _rad(m)))   # minutes
    minutes = (t - t.astype("datetime64[D]")).astype("int64") / 60.0
    true_solar = np.mod(minutes + eot + 4 * lon, 1440.0)
    hour_angle = np.where(true_solar / 4 < 0, true_solar / 4 + 180, true_solar / 4 - 180)
    cos_zen = np.sin(_rad(lat)) * np.sin(_rad(decl)) + np.cos(_rad(lat)) * np.cos(_rad(decl)) * np.cos(_rad(hour_angle))
    zen = np.degrees(np.arccos(np.clip(cos_zen, -1, 1)))
    az_num = np.sin(_rad(lat)) * np.cos(_rad(zen)) - np.sin(_rad(decl))
    az_den = np.cos(_rad(lat)) * np.sin(_rad(zen))
    az = np.degrees(np.arccos(np.clip(az_num / np.where(az_den == 0, 1e-12, az_den), -1, 1)))
    az = np.where(hour_angle > 0, np.mod(az + 180, 360), np.mod(540 - az, 360))
    return zen, az


def extraterrestrial(times_utc):
    """Beam normal radiation at the top of the atmosphere, W/m2 (Spencer 1971, as pvlib's default)."""
    t = np.asarray(times_utc, dtype="datetime64[D]")
    doy = (t - t.astype("datetime64[Y]").astype("datetime64[D]")).astype(int) + 1
    b = 2 * np.pi * (doy - 1) / 365.0
    return SOLAR_CONSTANT * (1.00011 + 0.034221 * np.cos(b) + 0.00128 * np.sin(b) + 0.000719 * np.cos(2 * b) + 0.000077 * np.sin(2 * b))


def tracker(zenith, azimuth, gcr=GCR, max_angle=MAX_ANGLE):
    """A horizontal north-south single-axis tracker with backtracking: (surface tilt, surface azimuth, cos of the angle of incidence)."""
    sx = np.sin(_rad(zenith)) * np.sin(_rad(azimuth))
    sz = np.cos(_rad(zenith))
    theta = np.degrees(np.arctan2(sx, sz))                       # the true-tracking rotation, + toward the west
    temp = np.minimum(np.abs(np.cos(_rad(theta))) / gcr, 1.0)    # backtracking: rotate back until rows no longer shade each other
    theta = theta - np.sign(theta) * np.degrees(np.arccos(temp))
    theta = np.clip(theta, -max_angle, max_angle)
    cos_aoi = np.cos(_rad(theta)) * sz + np.sin(_rad(theta)) * sx
    return np.abs(theta), np.where(theta >= 0, 270.0, 90.0), np.clip(cos_aoi, -1, 1)


def fixed(zenith, azimuth, tilt, surface_azimuth=180.0):
    cos_aoi = np.cos(_rad(zenith)) * np.cos(_rad(tilt)) + np.sin(_rad(zenith)) * np.sin(_rad(tilt)) * np.cos(_rad(azimuth - surface_azimuth))
    return tilt * np.ones_like(zenith), surface_azimuth * np.ones_like(zenith), np.clip(cos_aoi, -1, 1)


def iam_physical(cos_aoi, n=1.526, k=4.0, el=0.002):
    """The physical incidence angle modifier (De Soto et al. 2006; pvlib.iam.physical's defaults): Fresnel reflection and absorption in the cover."""
    aoi = np.arccos(np.clip(cos_aoi, -1, 1))
    def tau(a):
        ar = np.arcsin(np.clip(np.sin(a) / n, -1, 1))
        rs = np.sin(ar - a) ** 2 / np.maximum(np.sin(ar + a) ** 2, 1e-30)
        rp = np.tan(ar - a) ** 2 / np.maximum(np.tan(ar + a) ** 2, 1e-30)
        rho = np.where(a < 1e-6, ((n - 1) / (n + 1)) ** 2, 0.5 * (rs + rp))
        return np.exp(-k * el / np.cos(ar)) * (1 - rho)
    out = tau(aoi) / tau(np.zeros(1))
    return np.where(aoi >= np.pi / 2, 0.0, out)


def cell_temperature(poa, temp_air, wind_10m, a=-3.56, b=-0.075, delta=3.0):
    """Sandia's cell temperature model, open-rack glass-polymer modules (King et al. 2004; pvlib's sapm_cell)."""
    module = poa * np.exp(a + b * wind_10m) + temp_air
    return module + poa / 1000.0 * delta


def geometry(times_utc, lat, lon, mount="tracking", tilt=None):
    """The sun and the array for each hour ending at the UTC times, worked once per place: {zenith, cos_zenith, cos_aoi, surface_tilt,
    extraterrestrial, iam}. mount: "tracking" or "fixed" (tilt defaults to the latitude)."""
    t = np.asarray(times_utc, dtype="datetime64[s]") - np.timedelta64(1800, "s")      # mid-hour: ERA5 radiation is the preceding hour's mean
    zen, az = solar_position(t, lat, lon)
    if mount == "tracking":
        st, _, cos_aoi = tracker(zen, az)
    elif mount == "fixed":
        st, _, cos_aoi = fixed(zen, az, abs(lat) if tilt is None else tilt)
    else:
        raise ValueError("mount must be 'tracking' or 'fixed'")
    cos_aoi = np.where(zen < 90.0, cos_aoi, 0.0)
    return {"zenith": zen, "cos_zenith": np.cos(_rad(zen)), "cos_aoi": cos_aoi, "surface_tilt": st, "extraterrestrial": extraterrestrial(t),
            "iam": iam_physical(cos_aoi)}


def output(g, ghi, beam_horizontal, temp_air, wind_100m, p):
    """AC output per MW AC each hour (0-1) on a geometry(): ghi and beam_horizontal in W/m2, preceding-hour means; temp_air in C; wind_100m in
    m/s. p: RANGES' parameters (scalars or (n, 1) arrays)."""
    zen, cos_zen, cos_aoi, st = g["zenith"], g["cos_zenith"], g["cos_aoi"], g["surface_tilt"]
    ghi = np.asarray(ghi, float) * p["resource"]
    beam_h = np.minimum(np.asarray(beam_horizontal, float) * p["resource"], ghi)
    dhi = np.maximum(ghi - beam_h, 0.0)
    dni = np.where(zen < 85.0, beam_h / np.maximum(cos_zen, 1e-6), 0.0)
    up = zen < 90.0
    beam = dni * np.maximum(cos_aoi, 0.0)
    ai = dni / g["extraterrestrial"]                                       # Hay and Davies' anisotropy index
    rb = np.maximum(cos_aoi, 0.0) / np.maximum(cos_zen, 0.01745)
    sky = dhi * (ai * rb + (1 - ai) * (1 + np.cos(_rad(st))) / 2)
    ground = ghi * p["albedo"] * (1 - np.cos(_rad(st))) / 2
    poa = np.where(up, beam + sky + ground, 0.0)
    effective = np.where(up, beam * g["iam"] + sky + ground, 0.0)
    t_cell = cell_temperature(poa, np.asarray(temp_air, float), np.asarray(wind_100m, float) * (10.0 / 100.0) ** (1 / 7))
    pdc = p["ilr"] * effective / 1000.0 * (1 + p["gamma"] * (t_cell - 25.0)) * (1 - p["losses"])     # per MW AC
    pdc0 = 1.0 / ETA_INV                                                   # the inverter's DC rating per MW AC
    zeta = np.maximum(pdc, 1e-12) / pdc0
    eta = ETA_INV / ETA_INV_REF * (-0.0162 * zeta - 0.0059 / zeta + 0.9858)
    return np.clip(np.where(pdc > 0, eta * pdc, 0.0), 0.0, 1.0)


def hourly(times_utc, lat, lon, ghi, beam_horizontal, temp_air, wind_100m, p, mount="tracking", tilt=None):
    """AC output per MW AC each hour, as a share of the AC rating (0-1), for the hour ending at each UTC time: geometry() then output()."""
    return output(geometry(times_utc, lat, lon, mount, tilt), ghi, beam_horizontal, temp_air, wind_100m, p)
