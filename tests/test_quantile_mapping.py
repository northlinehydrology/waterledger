"""Quantile mapping of ERA5 cells to shore stations (design 0005, decided Nov 4, 2026), on synthetic weather worked by hand, and the
leave-one-station-out results the decision rests on."""
import json
import os

import numpy as np
import pytest

from waterledger_models import quantile_mapping as Q

HERE = os.path.dirname(os.path.abspath(__file__))
QM = os.path.join(HERE, "..", "docs", "methods", "qm-check")


def _weather(years=3, seed=0, warm=0.0, wet=0.0):
    """Hourly local times, T with a daily and yearly cycle plus noise, and Td a depression below it: warm and wet shift them."""
    times = np.arange(np.datetime64("2001-01-01T00"), np.datetime64(f"{2001 + years}-01-01T00"), np.timedelta64(1, "h"))
    h = (times - times.astype("datetime64[D]")).astype(int)
    doy = (times.astype("datetime64[D]") - times.astype("datetime64[Y]")).astype(int)
    r = np.random.default_rng(seed)
    t = 10 - 12 * np.cos(2 * np.pi * doy / 365) + 5 * np.sin(2 * np.pi * (h - 9) / 24) + r.normal(0, 3, len(times)) + warm
    d = np.abs(r.normal(4, 3, len(times))) - wet
    return times.astype(str), t, t - d


def _station(times, t, td, lat=42.0, lon=-83.0, land=0.6, elev=180.0, sid="s"):
    return {"id": sid, "name": sid, "lat": lat, "lon": lon, "cell_land": land, "elev_m": elev, "qt": Q.fit(times, t, td)}


CELL = {"lat": 42.0, "lon": -83.0, "land": 0.6, "elev_m": 180.0}


def test_a_station_with_the_cells_own_weather_changes_nothing():
    times, t, td = _weather()
    tc, tdc, note = Q.correct(times, t, td, CELL, [_station(times, t, td)])
    assert note["applied"] and note["method"] == "qm-3"
    assert np.allclose(tc, t, atol=1e-9) and np.allclose(tdc, td, atol=1e-9)


def test_a_station_2c_warmer_moves_every_hour_2c_and_keeps_the_depression():
    times, t, td = _weather()
    tc, tdc, _ = Q.correct(times, t, td, CELL, [_station(times, t + 2, td + 2)])
    assert np.allclose(tc, t + 2, atol=1e-9) and np.allclose(tc - tdc, t - td, atol=1e-9)


def test_dew_point_never_passes_temperature():
    """A station far more humid than the cell (its depression 6 C smaller) would push D below 0: it stops at 0, so Td <= T and RH <= 100%."""
    times, t, td = _weather()
    st_t, st_td = _weather(seed=1, wet=6.0)[1:]
    tc, tdc, _ = Q.correct(times, t, td, CELL, [_station(times, st_t, np.minimum(st_td, st_t))])
    assert (tdc <= tc).all()
    assert (tc - tdc == 0).sum() > 0                          # the clamp is reached, so the test reaches it
    assert Q.rh_from(tc, tdc).max() <= 100


def test_the_mapping_keeps_each_hours_rank_in_its_bin():
    """So the corrected cell keeps ERA5's own sequence, and its trend: within a bin, a warmer hour stays warmer."""
    times, t, td = _weather()
    st_t, st_td = _weather(seed=2, warm=1.5)[1:]
    tc, _, _ = Q.correct(times, t, td, CELL, [_station(times, st_t, st_td)])
    m, b = Q.bins(times)
    for mo, bl in ((0, 0), (6, 5)):
        sel = (m == mo) & (b == bl)
        order = np.argsort(t[sel], kind="stable")
        assert (np.diff(tc[sel][order]) >= -1e-9).all()


def test_lapse_moves_a_station_100_m_above_the_cell_0_65_c_warmer_and_leaves_its_dew_point():
    """The lapse rate moves temperature only; the dew point is mapped as it is (qm-3), where through model 1.9 the depression kept it moving with T."""
    times, t, td = _weather()
    tc, tdc, _ = Q.correct(times, t, td, CELL, [_station(times, t, td, elev=280.0)])
    assert np.allclose(tc, t + 0.65, atol=1e-9) and np.allclose(tdc, td, atol=1e-9)


def test_a_hot_day_correction_leaves_the_dew_point_alone():
    """The reason for qm-3: a station whose hot hours are 2 C hotter than the cell's, with the same dew points, warms those hours and
    leaves their dew point; mapping the depression would have carried the dew point up 2 C with them."""
    times, t, td = _weather()
    hot = t + 2.0 * (t > np.quantile(t, 0.9))
    tc, tdc, _ = Q.correct(times, t, td, CELL, [_station(times, hot, np.minimum(td, hot))])
    top = t > np.quantile(t, 0.95)
    assert tc[top].mean() > t[top].mean() + 1.0 and abs(tdc[top].mean() - td[top].mean()) < 0.2


def test_land_cells_are_corrected_from_land_stations_near():
    """From model 1.9 a land cell is corrected too, from the land stations within 100 km (whose own nearest cell is at least 90% land), as a shore
    cell is from shore stations; a shore station near it is not used, and with no land station that near it is left as it is."""
    times, t, td = _weather()
    inland = _station(times, t + 2, td + 2, lat=42.5, land=0.95, sid="inland")         # 56 km away, its cell 95% land
    shore = _station(times, t - 1, td - 1, lat=42.1, land=0.7, sid="shore")            # 11 km away, on the shore
    tc, tdc, note = Q.correct(times, t, td, CELL | {"land": 0.9}, [inland, shore])
    assert note["applied"] and note["reason"] == "cell at least 90% land" and [s[0] for s in note["stations"]] == ["inland"]
    assert np.allclose(tc, t + 2, atol=1e-9) and np.allclose(tc - tdc, t - td, atol=1e-9)
    far = _station(times, t + 2, td + 2, lat=43.0, land=0.95, sid="far")                # 111 km
    tc, tdc, note = Q.correct(times, t, td, CELL | {"land": 0.95}, [far, shore])
    assert not note["applied"] and note["reason"] == "no land station within 100 km" and (tc == t).all() and (tdc == td).all()


def test_only_shore_stations_anchor_a_shore_cell():
    times, t, td = _weather()
    inland = _station(times, t + 2, td + 2, lat=42.5, land=0.95, sid="inland")         # 56 km away, its cell 95% land
    tc, _, note = Q.correct(times, t, td, CELL, [inland])
    assert not note["applied"] and note["reason"] == "no shore station within 100 km" and (tc == t).all()
    shore = _station(times, t + 1, td + 1, lat=42.8, land=0.7, sid="shore")             # 89 km away, its cell 70% land
    tc, _, note = Q.correct(times, t, td, CELL, [inland, shore])
    assert note["applied"] and [s[0] for s in note["stations"]] == ["shore"] and np.allclose(tc, t + 1, atol=1e-9)
    far = _station(times, t + 1, td + 1, lat=43.0, land=0.7, sid="far")                 # 111 km
    assert Q.correct(times, t, td, CELL, [far])[2]["reason"] == "no shore station within 100 km"


def test_stations_weigh_1_over_d_squared_nearest_four():
    st = [{"id": i, "lat": 42.0 + d / 111.195, "lon": -83.0, "cell_land": 0.5} for i, d in enumerate((10, 20, 30, 40, 50))]
    ws = Q.weights(42.0, -83.0, st)
    assert [s["id"] for s, _ in ws] == [0, 1, 2, 3]
    w = np.array([1 / 10 ** 2, 1 / 20 ** 2, 1 / 30 ** 2, 1 / 40 ** 2])
    assert np.allclose([x for _, x in ws], w / w.sum(), rtol=1e-3)
    assert Q.weights(42.0, -83.0, [{"lat": 42.0, "lon": -83.0, "cell_land": 0.5}])[0][1] == 1.0     # a station at the center: d taken as 5 km


def test_leave_one_station_out_on_a_synthetic_shore():
    """A shore 1.5 C cooler in ERA5 than at its stations: each held-out shore station's cell, corrected from the others, comes closer
    than uncorrected on the 0.4% dry-bulb, and an inland station is not used."""
    times, t0, td0 = _weather()
    stations, cells = [], []
    for i in range(5):
        lat = 42.0 + 0.2 * i
        era5_t, era5_td = t0 + 0.1 * i, td0 + 0.1 * i
        true_t, true_td = era5_t + 1.5, era5_td + 1.0
        stations.append(_station(times, true_t, true_td, lat=lat, land=0.6, sid=f"shore{i}") | {"truth": true_t})
        cells.append((era5_t, era5_td))
    stations.append(_station(times, t0 - 3, td0 - 3, lat=42.3, land=1.0, sid="inland"))
    for i, s in enumerate(stations[:5]):
        rest = [x for x in stations if x is not s]
        tc, _, note = Q.correct(times, *cells[i], CELL | {"lat": s["lat"]}, rest)
        assert "inland" not in [x[0] for x in note["stations"]]
        ddb = lambda x: np.quantile(x, 0.996)
        assert abs(ddb(tc) - ddb(s["truth"])) < 0.25 < abs(ddb(cells[i][0]) - ddb(s["truth"]))


def test_the_recorded_leave_one_out_check_supports_the_rule():
    """The prototype's results (docs/methods/qm-check), held to what design 0005 says of them: on shore cells the decided rule beats
    raw ERA5 on the design dry-bulb at the held-out stations it corrects; no held-out corrected series has Td above T."""
    rows = json.load(open(os.path.join(QM, "cv_weather.json")))["rows"]
    shore = [r for r in rows if r["cell_land"] < Q.SHORE_LAND and r["errors"]["lapse_shore"]["corrected"]]
    assert len(shore) >= 10
    med = lambda way: np.median([abs(r["errors"][way]["ddb"]) for r in shore])
    assert med("lapse_shore") < med("none")
    places = json.load(open(os.path.join(QM, "cv_places.json")))["runs"]
    assert all(r["td_over_t"] == 0 for r in places if r["corrected"])
    assert all(r["rh_max"] <= 100 for r in places)
    # the shoreline places under the decided rule, against their stations (percent): no overshoot where a shore station is near
    rows = {r["name"]: r["err"]["decided"] for r in json.load(open(os.path.join(QM, "cv_places_summary.json")))}
    for name in ("Lorain city", "Cleveland city", "Virginia Beach city", "Toledo city"):
        assert abs(rows[name]["hybrid.withdrawn_avg"]) < 10 and abs(rows[name]["assist.withdrawn_avg"]) < 10
        assert abs(rows[name]["hybrid.withdrawn_peak_1in10"]) < 6 and abs(rows[name]["towers.withdrawn_avg"]) < 2


@pytest.mark.parametrize("land", [0.5, 0.89])
def test_a_cell_under_90_percent_land_is_a_shore_cell(land):
    assert Q.is_shore_station({"cell_land": land}) and not Q.is_shore_station({"cell_land": 0.9})
