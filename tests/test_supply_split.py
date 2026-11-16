"""Splitting global horizontal radiation into beam and diffuse (design 0018, section 1): Erbs, DISC and DIRINT held to pvlib's hour by hour on
the same inputs, the split closing on the global every hour, DIRINT's coefficients as pvlib carries them, and the PV chain from global radiation
alone reading as the ERA5 chain does when it is handed the same beam."""
import numpy as np
import pandas as pd
import pytest

from waterledger_models.supply import pv

pvlib = pytest.importorskip("pvlib")
LAT, LON = 42.9, -85.5
T = np.arange(np.datetime64("2023-01-01T00:00"), np.datetime64("2024-01-01T00:00"), np.timedelta64(1, "h"))
IDX = pd.DatetimeIndex(T, tz="UTC")
P = {"losses": 0.14, "gamma": -0.0037, "ilr": 1.3, "albedo": 0.2, "resource": 1.0}


@pytest.fixture(scope="module")
def sky():
    """A year of hours centred on their stamps (shift 0): clear sky (Ineichen) dimmed by cloud that persists for a few hours, a dew point."""
    g = pv.geometry(T, LAT, LON, shift_s=0)
    sp = pd.DataFrame({"apparent_zenith": g["zenith"], "zenith": g["zenith"], "apparent_elevation": 90 - g["zenith"]}, index=IDX)
    cs = pvlib.location.Location(LAT, LON).get_clearsky(IDX, model="ineichen", solar_position=sp)
    rng = np.random.default_rng(3)
    cloud = np.clip(np.repeat(rng.uniform(0.1, 1.05, len(T) // 3 + 1), 3)[:len(T)] + rng.normal(0, 0.05, len(T)), 0.05, 1.1)
    ghi = cs["ghi"].values * cloud
    dew = 5 + 10 * np.sin(2 * np.pi * (np.arange(len(T)) / 8760 - 0.3)) + rng.normal(0, 2, len(T))
    return g, ghi, dew


def _pvlib_dni(method, g, ghi, dew=None):
    z = pd.Series(g["zenith"], index=IDX)
    x = pd.Series(ghi, index=IDX)
    if method == "erbs":
        return np.asarray(pvlib.irradiance.erbs(x, z, IDX)["dni"])
    if method == "disc":
        return np.asarray(pvlib.irradiance.disc(x, z, IDX)["dni"])
    return np.nan_to_num(np.asarray(pvlib.irradiance.dirint(x, z, IDX, temp_dew=None if dew is None else pd.Series(dew, index=IDX))))


def test_dirint_coefficients_are_pvlibs():
    from pvlib.irradiance import _get_dirint_coeffs
    from waterledger_models.supply._dirint import COEFFS
    assert np.array_equal(COEFFS, _get_dirint_coeffs())


@pytest.mark.parametrize("method,dew", [("erbs", False), ("disc", False), ("dirint", False), ("dirint", True)])
def test_split_matches_pvlib_hour_by_hour(sky, method, dew):
    g, ghi, dp = sky
    beam = pv.decompose(g, ghi, method, dew_point=dp if dew else None)
    ref = np.clip(np.minimum(_pvlib_dni(method, g, ghi, dp if dew else None), g["extraterrestrial"]) * np.maximum(g["cos_zenith"], 0), 0, ghi)
    assert np.abs(beam - ref).max() < 1e-6                             # W/m2: the same equations, so the same numbers
    assert ref.sum() > 0.3 * ghi.sum()                                 # a test with beam in it


@pytest.mark.parametrize("method", pv.SPLITS)
def test_split_closes_on_the_global(sky, method):
    """Beam and diffuse horizontal close on the global every hour: the beam is never negative and never above the global."""
    g, ghi, _ = sky
    beam = pv.decompose(g, ghi, method)
    diffuse = ghi - beam
    assert (beam >= 0).all() and (diffuse >= 0).all() and np.abs(beam + diffuse - ghi).max() < 1e-9      # W/m2, to rounding
    assert not beam[g["zenith"] > pv.MAX_ZENITH].any()
    assert (beam / np.maximum(g["cos_zenith"], 1e-9) <= g["extraterrestrial"] + 1e-9)[g["zenith"] < 90].all()


def test_pv_from_global_reads_as_the_chain_with_the_same_beam(sky):
    """output_from_ghi is the ERA5 chain on the decomposed beam, with the 10 m wind as given."""
    g, ghi, _ = sky
    temp, w10 = np.full(len(T), 15.0), np.full(len(T), 4.0)
    beam = pv.decompose(g, ghi, "disc")
    a = pv.output_from_ghi(g, ghi, temp, w10, P, method="disc")
    b = pv.output(g, ghi, beam, temp, w10 / 0.1 ** (1 / 7), P)
    assert np.abs(a - b).max() < 1e-12
    assert np.array_equal(pv.hourly_from_ghi(T, LAT, LON, ghi, temp, w10, P, shift_s=0, method="disc"), a)


def test_the_splits_differ_where_they_should(sky):
    """Overcast hours are almost all diffuse under every split; on the year they differ by a few percent of the tracker's output, not more."""
    g, ghi, _ = sky
    temp, w10 = np.full(len(T), 15.0), np.full(len(T), 4.0)
    kt = ghi / (g["extraterrestrial"] * np.maximum(g["cos_zenith"], 0.065))
    dark = (kt < 0.15) & (g["zenith"] < 80)
    cf = {}
    for m in pv.SPLITS:
        beam = pv.decompose(g, ghi, m)
        assert beam[dark].sum() < 0.1 * ghi[dark].sum()
        cf[m] = pv.output_from_ghi(g, ghi, temp, w10, P, method=m).mean()
    assert max(cf.values()) / min(cf.values()) < 1.10
