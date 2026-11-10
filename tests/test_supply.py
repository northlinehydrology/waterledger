"""Hourly PV and wind generation (design 0014, step 3). The PV chain is held to pvlib's (Holmgren et al. 2018) hour by hour on the same inputs:
sun position, tracking with backtracking or fixed tilt, Hay and Davies' sky diffuse, the physical cover reflection, Sandia's cell temperature,
PVWatts' DC and inverter. Wind follows the IEA 3.4 MW reference turbine's curve."""
import numpy as np
import pandas as pd
import pytest

from waterledger_models.supply import pv, wind

pvlib = pytest.importorskip("pvlib")
LAT, LON = 42.9, -85.5
T_END = np.arange(np.datetime64("2023-01-01T01:00"), np.datetime64("2024-01-01T01:00"), np.timedelta64(1, "h"))
MID = pd.DatetimeIndex(T_END - np.timedelta64(30, "m"), tz="UTC")
P = {"losses": 0.14, "gamma": -0.0037, "ilr": 1.3, "albedo": 0.2, "resource": 1.0}


@pytest.fixture(scope="module")
def sky():
    """A year of hours under clear sky (Ineichen) dimmed by random cloud, with a seasonal temperature and random wind."""
    sp = pvlib.solarposition.get_solarposition(MID, LAT, LON, method="nrel_numpy")
    cs = pvlib.location.Location(LAT, LON).get_clearsky(MID, model="ineichen", solar_position=sp)
    rng = np.random.default_rng(1)
    cloud = rng.uniform(0.2, 1.0, len(MID))
    ghi = cs["ghi"].values * cloud
    beam_h = np.minimum(cs["dni"].values * cloud ** 2 * np.cos(np.radians(sp["zenith"].values)).clip(0), ghi)
    temp = 10 + 12 * np.sin(2 * np.pi * (np.arange(len(MID)) / 8760 - 0.3))
    return sp, ghi, beam_h, temp, rng.uniform(2, 12, len(MID))


def _pvlib_ac(sp, ghi, beam_h, temp, w100, mount):
    zen, az = sp["zenith"].values, sp["azimuth"].values
    if mount == "tracking":
        tr = pvlib.tracking.singleaxis(sp["zenith"], sp["azimuth"], axis_tilt=0, axis_azimuth=180, max_angle=pv.MAX_ANGLE, backtrack=True,
                                       gcr=pv.GCR)
        st, saz, aoi = tr["surface_tilt"].fillna(0).values, tr["surface_azimuth"].fillna(180).values, tr["aoi"].fillna(90).values
    else:
        st, saz = np.full(len(zen), LAT), np.full(len(zen), 180.0)
        aoi = pvlib.irradiance.aoi(st, saz, zen, az)
    dni = np.where(zen < 85, beam_h / np.maximum(np.cos(np.radians(zen)), 1e-6), 0.0)
    poa = pvlib.irradiance.get_total_irradiance(st, saz, zen, az, dni, ghi, np.maximum(ghi - beam_h, 0),
                                                dni_extra=pvlib.irradiance.get_extra_radiation(MID).values, model="haydavies", albedo=P["albedo"])
    up = zen < 90
    eff = np.where(up, np.nan_to_num(np.asarray(poa["poa_direct"])) * pvlib.iam.physical(aoi) + np.nan_to_num(np.asarray(poa["poa_diffuse"])), 0)
    tc = pvlib.temperature.sapm_cell(np.where(up, np.nan_to_num(np.asarray(poa["poa_global"])), 0), temp, w100 * 0.1 ** (1 / 7),
                                     a=-3.56, b=-0.075, deltaT=3)
    pdc = pvlib.pvsystem.pvwatts_dc(eff, tc, pdc0=P["ilr"], gamma_pdc=P["gamma"]) * (1 - P["losses"])
    return np.nan_to_num(np.asarray(pvlib.inverter.pvwatts(pdc, pdc0=1 / pv.ETA_INV, eta_inv_nom=pv.ETA_INV, eta_inv_ref=pv.ETA_INV_REF)))


def test_sun_position_matches_nrel_spa(sky):
    sp = sky[0]
    zen, az = pv.solar_position(T_END - np.timedelta64(1800, "s"), LAT, LON)
    up = sp["zenith"].values < 90
    assert np.abs(zen - sp["zenith"].values)[up].max() < 0.03
    assert np.abs((az - sp["azimuth"].values + 180) % 360 - 180)[up].max() < 0.05


@pytest.mark.parametrize("mount", ["tracking", "fixed"])
def test_pv_matches_pvlib_hour_by_hour(sky, mount):
    sp, ghi, beam_h, temp, w100 = sky
    mine = pv.hourly(T_END, LAT, LON, ghi, beam_h, temp, w100, P, mount=mount)
    ref = _pvlib_ac(sp, ghi, beam_h, temp, w100, mount)
    assert np.abs(mine - ref).max() < 0.002                       # 0.2% of the AC rating, the worst hour (sun position differs by 0.02 degrees)
    assert mine.sum() == pytest.approx(ref.sum(), rel=1e-3)
    assert (mine >= 0).all() and (mine <= 1).all() and not mine[sp["zenith"].values >= 90].any()


def test_tracking_beats_fixed_tilt_and_clips(sky):
    sp, ghi, beam_h, temp, w100 = sky
    track, fix = (pv.hourly(T_END, LAT, LON, ghi, beam_h, temp, w100, P, mount=m) for m in ("tracking", "fixed"))
    assert track.sum() > fix.sum()
    hi = pv.hourly(T_END, LAT, LON, ghi, beam_h, temp, w100, {**P, "ilr": 1.6})
    assert hi.max() == pytest.approx(1.0) and hi.sum() > track.sum()


def test_wind_follows_the_reference_curve():
    """Under cut-in and over cut-out nothing; at rated speed the rating less losses; the curve's own points through the shear and losses."""
    p = {"alpha": 0.0, "losses": 0.0, "resource": 1.0}
    assert wind.hourly(np.array([2.9, 26.0]), np.zeros(2), p).tolist() == [0.0, 0.0]
    assert wind.hourly(np.array([12.0]), np.zeros(1), p)[0] == pytest.approx(1.0)
    assert wind.hourly(np.array([0.0]), np.array([8.0899]), p)[0] == pytest.approx(1901.5 / 3370.0)
    q = {"alpha": 1 / 7, "losses": 0.15, "resource": 1.0}
    assert wind.hourly(np.array([6.0]), np.zeros(1), q)[0] == pytest.approx(
        np.interp(6.0 * 1.1 ** (1 / 7), wind.SPEED, wind.POWER_KW) / 3370.0 * 0.85)
    speeds = np.random.default_rng(2).weibull(2.0, 100000) * 8.0      # a Weibull k = 2 site at about 7.1 m/s mean at 100 m
    cf = wind.hourly(speeds, np.zeros_like(speeds), {"alpha": 0.14, "losses": 0.15, "resource": 1.0}).mean()
    assert 0.25 < cf < 0.45                                            # U.S. fleet 34% in 2024 (EIA EPM Table 6.07.B)
