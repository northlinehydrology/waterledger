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

A study's own forcing (design 0018): AORC, like most hydrologic forcings, gives only global horizontal radiation and the 10 m wind. For it,
hourly_from_ghi() splits the global into beam and diffuse with decompose(): Erbs et al. (1982) on AORC (AORC_SPLIT, check A2), or DIRINT
(Perez et al. 1992) or DISC (Maxwell 1987), as pvlib implements them, the split closing on the global every hour; places the sun by the forcing's own time stamp (shift_s;
AORC_SHIFT_S); and takes the 10 m wind as it is. Then the same chain. ERA5's functions are unchanged to the bit (tests/test_supply_identity.py).

pvlib (Holmgren et al. 2018) is the test reference: tests/test_supply.py holds this chain to pvlib's functions hour by hour on the same inputs,
tests/test_supply_split.py the splits.
Parameters: RANGES (ERA5's path) and RANGES_AORC (AORC's: the resource factor from check A3), each [A] unless sourced in
docs/research/power-supply-water.md.
"""
import warnings

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
RANGES_AORC = RANGES | {
    "resource": (0.73, 1.02),      # the same on AORC (hourly_from_ghi, Erbs, shift 0): EIA's 2024 tracking fleet (944 plants, 24.1%) against
                                   # this chain on AORC at the plants' 1 km points (27.6%), 0.87 overall and 0.73-1.02 across the 15 states with
                                   # ten or more plants, wider than ERA5's: AORC's radiation scatters more (design 0018, checks A2 and A3;
                                   # docs/methods/power_supply/aorc_check.py)
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


def geometry(times_utc, lat, lon, mount="tracking", tilt=None, shift_s=-1800):
    """The sun and the array for each hour ending at the UTC times, worked once per place: {zenith, cos_zenith, cos_aoi, surface_tilt,
    extraterrestrial, iam}. mount: "tracking" or "fixed" (tilt defaults to the latitude). shift_s: where in the hour the radiation stands,
    seconds from the time stamp: -1800 (the default) for a mean over the preceding hour, as ERA5's is, so the sun is placed at mid-hour; 0 for
    radiation centred on its stamp (AORC_SHIFT_S)."""
    t = np.asarray(times_utc, dtype="datetime64[s]") + np.timedelta64(int(shift_s), "s")
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
    m/s, taken to 10 m for the cells' temperature by a 1/7 power law [A]. p: RANGES' parameters (scalars or (n, 1) arrays). ERA5's path."""
    return _chain(g, ghi, beam_horizontal, temp_air, np.asarray(wind_100m, float) * (10.0 / 100.0) ** (1 / 7), p)


def _chain(g, ghi, beam_horizontal, temp_air, wind_10m, p):
    """The PVWatts chain from horizontal radiation and the 10 m wind, shared by output() (ERA5) and output_from_ghi() (a study's forcing)."""
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
    t_cell = cell_temperature(poa, np.asarray(temp_air, float), wind_10m)
    pdc = p["ilr"] * effective / 1000.0 * (1 + p["gamma"] * (t_cell - 25.0)) * (1 - p["losses"])     # per MW AC
    pdc0 = 1.0 / ETA_INV                                                   # the inverter's DC rating per MW AC
    zeta = np.maximum(pdc, 1e-12) / pdc0
    eta = ETA_INV / ETA_INV_REF * (-0.0162 * zeta - 0.0059 / zeta + 0.9858)
    return np.clip(np.where(pdc > 0, eta * pdc, 0.0), 0.0, 1.0)


def hourly(times_utc, lat, lon, ghi, beam_horizontal, temp_air, wind_100m, p, mount="tracking", tilt=None):
    """AC output per MW AC each hour, as a share of the AC rating (0-1), for the hour ending at each UTC time: geometry() then output()."""
    return output(geometry(times_utc, lat, lon, mount, tilt), ghi, beam_horizontal, temp_air, wind_100m, p)


# ---------------------------------------------------------------- a forcing with global horizontal radiation only (design 0018)
# AORC's shortwave is NLDAS-2's, NARR's 3-hourly field spread to hours (AORC v1.1 methods, sec. 4.2). It stands at the middle of its hour, not
# the end: check A1 (docs/methods/power_supply/aorc_timing.py, 2024) puts clear days' centroids -2 to +1 minutes from solar noon at four points
# (the Clam River and three SURFRAD stations), the same estimator giving 0 to 4 minutes on SURFRAD's measured radiation averaged that way and
# 30 to 35 averaged over the hour ending at the stamp.
AORC_SHIFT_S = 0
SPLITS = ("dirint", "disc", "erbs")
# The split on AORC (design 0018, decision 1, Andrew Nov 16: "the industry norm"): Erbs, PVsyst's default. Check A2
# (docs/methods/power_supply/split_check.py, three SURFRAD stations, 2024) gave it the smallest hourly and daily PV scatter on AORC's global at
# all three and the smallest annual bias, DIRINT next, DISC last; on measured radiation DIRINT was best. AORC's hours are NARR's 3-hourly
# radiation spread out, so a split that commits more to beam loses when the cloud is in the wrong hour.
AORC_SPLIT = "erbs"
DISC_SOLAR_CONSTANT = 1370.0      # DISC's I0 (Maxwell 1987), as pvlib.irradiance.disc
MIN_COS_ZENITH = 0.065            # pvlib's floor on cos(zenith) in the clearness index
MAX_ZENITH = 87.0                 # no beam with the sun lower (pvlib's max_zenith)


def _clearness(ghi, cos_zen, i0):
    return np.clip(np.asarray(ghi, float) / (i0 * np.maximum(cos_zen, MIN_COS_ZENITH)), 0.0, 1.0)


def _airmass(zenith, pressure):
    """Kasten (1966) relative air mass, as pvlib's 'kasten1966', NaN with the sun down, at the pressure (Pa)."""
    z = np.where(zenith > 90.0, np.nan, zenith)
    with np.errstate(invalid="ignore"):
        am = 1.0 / (np.cos(_rad(z)) + 0.15 * (93.885 - z) ** -1.253)
    return am * np.asarray(pressure, float) / 101325.0


def _disc(ghi, g, pressure):
    """DISC (Maxwell 1987): beam normal from the clearness index and air mass, as pvlib.irradiance.disc. Returns (dni, kt, airmass)."""
    i0 = g["extraterrestrial"] * (DISC_SOLAR_CONSTANT / SOLAR_CONSTANT)
    kt = _clearness(ghi, g["cos_zenith"], i0)
    am = np.minimum(_airmass(g["zenith"], pressure), 12.0)
    cloudy = kt <= 0.6
    a = np.where(cloudy, 0.512 + kt * (-1.56 + kt * (2.286 - 2.222 * kt)), -5.743 + kt * (21.77 + kt * (-27.49 + 11.56 * kt)))
    b = np.where(cloudy, 0.37 + 0.962 * kt, 41.4 + kt * (-118.5 + kt * (66.05 + 31.9 * kt)))
    c = np.where(cloudy, -0.28 + kt * (0.932 - 2.048 * kt), -47.01 + kt * (184.2 + kt * (-222.0 + 73.81 * kt)))
    knc = 0.866 + am * (-0.122 + am * (0.0121 + am * (-0.000653 + 1.4e-05 * am)))
    dni = (knc - (a + b * np.exp(c * am))) * i0
    dni = np.where((g["zenith"] > MAX_ZENITH) | (np.asarray(ghi, float) < 0) | (dni < 0), 0.0, dni)
    return dni, kt, am


def _bins(x, edges, closed_top):
    """1-based bins as DIRINT's (pvlib._dirint_bins): x in [edges[i], edges[i+1]), the last bin closed on top if closed_top; 0 outside."""
    out = np.zeros(np.shape(x), dtype=int)
    for i in range(len(edges) - 1):
        top = (x <= edges[i + 1]) if (closed_top and i == len(edges) - 2) else (x < edges[i + 1])
        out = np.where((x >= edges[i]) & top, i + 1, out)
    return out


def _dirint(ghi, g, pressure, dew_point):
    """DIRINT (Perez et al. 1992): DISC's beam normal times a coefficient by the hour's zenith-independent clearness, zenith, the change in
    clearness to the hours either side (the series must be consecutive hours), and the dew point if given; as pvlib.irradiance.dirint."""
    from waterledger_models.supply._dirint import COEFFS
    dni, kt, am = _disc(ghi, g, pressure)
    with np.errstate(invalid="ignore"):
        ktp = np.clip(kt / (1.031 * np.exp(-1.4 / (0.9 + 9.4 / am)) + 0.1), 0.0, 1.0)
        ktp = np.where(np.isnan(am), np.nan, ktp)
    nxt, prv = np.r_[ktp[1:], np.nan], np.r_[np.nan, ktp[:-1]]
    d = np.vstack([np.abs(ktp - nxt), np.abs(ktp - prv)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)              # an hour with neither neighbour in daylight: NaN, no coefficient
        dktp = np.nanmean(d, axis=0)                                  # Perez eqns 2-3: the mean of the neighbours there are
    zen = g["zenith"]
    kb = _bins(ktp, (0, 0.24, 0.4, 0.56, 0.7, 0.8, 1.0), True)
    zb = _bins(zen, (0, 25, 40, 55, 70, 80, np.inf), False)
    db = _bins(dktp, (0, 0.015, 0.035, 0.07, 0.15, 0.3, 1.0), True)
    if dew_point is None:
        wb = np.full(np.shape(zen), 5)
    else:
        w = np.exp(0.07 * np.asarray(dew_point, float) - 0.075)    # Perez eqn 4: precipitable water, cm
        wb = _bins(w, (0, 1, 2, 3, np.inf), False)
    ok = (kb > 0) & (zb > 0) & (db > 0) & (wb > 0)
    coef = np.where(ok, COEFFS[np.maximum(kb, 1) - 1, np.maximum(zb, 1) - 1, np.maximum(db, 1) - 1, np.maximum(wb, 1) - 1], np.nan)
    return dni * coef


def _erbs(ghi, g):
    """Erbs et al. (1982): the diffuse fraction from the clearness index alone; beam normal as pvlib.irradiance.erbs."""
    ghi = np.asarray(ghi, float)
    kt = _clearness(ghi, g["cos_zenith"], g["extraterrestrial"])
    df = np.where(kt <= 0.22, 1 - 0.09 * kt, np.where(kt <= 0.8, 0.9511 - 0.1604 * kt + 4.388 * kt ** 2 - 16.638 * kt ** 3 + 12.336 * kt ** 4,
                                                       0.165))
    with np.errstate(divide="ignore", invalid="ignore"):
        dni = (ghi - df * ghi) / g["cos_zenith"]
    return np.where((g["zenith"] > MAX_ZENITH) | (ghi < 0) | (dni < 0), 0.0, dni)


def decompose(g, ghi, method="dirint", dew_point=None, pressure=101325.0):
    """Beam (direct) horizontal radiation, W/m2, from global horizontal on a geometry() whose shift matches the radiation's time stamp:
    "dirint" (Perez et al. 1992), "disc" (Maxwell 1987) or "erbs" (Erbs et al. 1982), each as pvlib implements it. dew_point (C) for DIRINT,
    optional; pressure in Pa. Diffuse is ghi less the beam, so the two close on ghi every hour: the beam is held to [0, ghi], 0 with the sun
    under MAX_ZENITH or where DIRINT has no coefficient (an hour with no daylight neighbour)."""
    ghi = np.asarray(ghi, float)
    if method == "dirint":
        dni = _dirint(ghi, g, pressure, dew_point)
    elif method == "disc":
        dni = _disc(ghi, g, pressure)[0]
    elif method == "erbs":
        dni = _erbs(ghi, g)
    else:
        raise ValueError(f"method must be one of {SPLITS}")
    dni = np.minimum(np.nan_to_num(dni, nan=0.0), g["extraterrestrial"])      # no beam above the top of the atmosphere's
    return np.clip(dni * np.maximum(g["cos_zenith"], 0.0), 0.0, np.maximum(ghi, 0.0))


def output_from_ghi(g, ghi, temp_air, wind_10m, p, method=AORC_SPLIT, dew_point=None, pressure=101325.0):
    """AC output per MW AC each hour (0-1) on a geometry() from a forcing that gives global horizontal radiation and the 10 m wind (AORC):
    the beam by decompose() on the forcing's own radiation, then output()'s chain. p: RANGES_AORC's parameters (scalars or (n, 1) arrays)."""
    return _chain(g, ghi, decompose(g, ghi, method, dew_point, pressure), temp_air, np.asarray(wind_10m, float), p)


def hourly_from_ghi(times_utc, lat, lon, ghi, temp_air, wind_10m, p, shift_s=AORC_SHIFT_S, mount="tracking", tilt=None, method=AORC_SPLIT,
                    dew_point=None, pressure=101325.0):
    """hourly() for a forcing that gives global horizontal radiation and the 10 m wind: geometry() at the forcing's shift_s, then
    output_from_ghi(). The defaults are AORC's (shift_s AORC_SHIFT_S, method AORC_SPLIT). For DIRINT the times must be consecutive hours."""
    return output_from_ghi(geometry(times_utc, lat, lon, mount, tilt, shift_s), ghi, temp_air, wind_10m, p, method, dew_point, pressure)
