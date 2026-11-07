"""`waterledger era5 check` (design 0005's leave-one-station-out check for any state) on a small fixture: synthetic ERA5 cells in Ohio,
stations whose records are their cells' plus a known bias, a stand-in for the cooling model. A state where ERA5 matches the stations
on land and runs cool at the shore passes; one where ERA5 runs 2 C cool on land (a mountain state, say) fails, and the command exits 1."""
import json, os

import numpy as np
import pytest

from waterledger import cli
from waterledger.national import era5 as E
from waterledger.national import era5_check as C
from waterledger_data import era5

LAND = ["40.00_-83.00", "40.25_-82.50", "39.75_-84.25", "40.50_-81.50", "41.00_-83.75", "39.25_-84.50"]
SHORE = ["41.50_-81.75", "41.50_-82.00", "41.75_-81.25", "41.50_-81.50"]          # 0.65, 0.59, 0.54 and 0.82 land


def _write(cid):
    n = int((era5.END - era5.START).astype(int))
    h = np.arange(n)
    r = np.random.default_rng(sum(map(ord, cid)))
    t = (10 - 12 * np.cos(2 * np.pi * h / 8766) + 5 * np.sin(2 * np.pi * (h - 14) / 24) + r.normal(0, 2, n)).astype(np.float32)
    era5.write_raw(cid, {"temperature_2m": t, "dew_point_2m": (t - np.abs(r.normal(4, 3, n))).astype(np.float32)}, "2026-11-04", {"source": "test"})


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(era5, "RAW", str(tmp_path / "raw"))
    monkeypatch.setattr(C, "CHECK", str(tmp_path / "check"))
    for c in LAND + SHORE:
        _write(c)
    return tmp_path


def _stations(land_bias=0.0, shore_bias=1.5):
    """A station 3 km from each cell's center, its record the cell's (in local time) plus `bias`, and a little noise of its own."""
    out = []
    for i, c in enumerate(LAND + SHORE):
        times, t, td = era5.local(c)
        b = shore_bias if c in SHORE else land_bias
        r = np.random.default_rng(i)
        lat, lon = (float(x) for x in c.split("_"))
        out.append({"id": f"s{i}", "name": f"Station {i}", "state": "OH", "source": "isd", "lat": lat + 0.027, "lon": lon, "elev_m": era5.elevation(c),
                    "cell": c, "cell_land": era5.land(c), "times": times, "t": t + b + r.normal(0, 0.1, len(t)), "td": td + b})
    return out


def _places(stations):
    return [{"geoid": f"p{s['id']}", "name": f"Place {s['id']}", "level": "place", "lat": s["lat"] + 0.02, "lon": s["lon"]} for s in stations]


def _run(times, temps, rhs, n, seed, mw):
    """The cooling model's stand-in: every result moves with the mean temperature, as water does with heat."""
    m = float(np.mean(temps)) + 30
    return {d: {s: {"p50": m * (2 if s.endswith("peak_1in10") else 1)} for s in ("withdrawn_avg", "withdrawn_peak_1in10")} for d in ("towers", "hybrid", "assist")}


def test_a_state_like_the_four_passes(cache):
    st = _stations()
    rep = C.run_check("OH", out=str(cache / "out"), n=8, workers=1, draws=5, places=_places(st), stations=st, run=_run, fetch=lambda ids: None)
    assert rep["verdict"] == "pass", [c for c in rep["criteria"] if c["pass"] is False]
    by = {c["id"]: c for c in rep["criteria"]}
    assert by["W1"]["value"] == 6 and by["W2"]["pass"]                            # land: corrected from the neighbors' stations, near enough
    land = [r for r in rep["weather"] if r["cell_land"] >= 0.9]
    assert any(r["corrected"] for r in land) and all(abs(r["uncorrected"]["ddb"]) < 0.3 for r in land)
    shore = [r for r in rep["weather"] if r["cell_land"] < 0.9]
    assert all(r["corrected"] for r in shore) and by["W5"]["value"] < 0.5 and by["W6"]["pass"]
    assert all(abs(r["uncorrected"]["ddb"] + 1.5) < 0.3 for r in shore)           # uncorrected, the shore runs 1.5 C cool
    held = next(r for r in shore if r["id"] == "s6")
    assert "Station 6" not in [a[1] for a in held["anchors"]]                     # held out of its own correction
    assert by["P1"]["value"] == 8 and by["P2"]["pass"] and by["P5"]["pass"]
    assert json.load(open(cache / "out" / "check.json"))["verdict"] == "pass"
    md = open(cache / "out" / "check.md").read()
    assert md.startswith("# ERA5 check: OH") and "**PASS**" in md and "| W2 |" in md and "Places through the cooling model" in md


def test_era5_2c_cool_on_land_is_corrected_from_the_stations_left(cache):
    """Model 1.9: ERA5 2 C cool on every land cell, which failed W2 and W3 when land cells were left as they were, is brought within
    the limits by the land cells' own correction, each held-out station's cell corrected from the others."""
    st = _stations(land_bias=2.0)
    rep = C.run_check("OH", out=str(cache / "out"), n=8, workers=1, draws=5, places=_places(st), stations=st, run=_run, fetch=lambda ids: None)
    by = {c["id"]: c for c in rep["criteria"]}
    land = [r for r in rep["weather"] if r["cell_land"] >= 0.9]
    assert all(r["uncorrected"]["ddb"] == pytest.approx(-2.0, abs=0.15) for r in land)
    assert by["W2"]["pass"] and by["W3"]["pass"] and by["W2"]["value"] < 0.75


def test_a_land_error_left_after_correction_fails_and_says_why(tmp_path):
    land = [{"cell_land": 1.0, "corrected": True, "uncorrected": {"ddb": -2.0, "wb": 0.05}, "decided": {"ddb": -1.9, "wb": 0.05}}] * 6
    places = [{"difference_pct": {f"{d}.{s}": 1.0 for d, s in C.STATS}}] * 5
    crit, ok = C.judge(land, places)
    by = {c["id"]: c for c in crit}
    assert not ok and by["W2"]["pass"] is False and by["W3"]["pass"] is False and by["W2"]["value"] == pytest.approx(1.9)


def test_too_few_stations_or_weather_only_cannot_pass(cache):
    st = _stations()[:3]
    rep = C.run_check("OH", out=str(cache / "few"), n=8, workers=1, draws=5, places=_places(st), stations=st, run=_run, fetch=lambda ids: None)
    assert rep["verdict"] == "fail" and {c["id"]: c for c in rep["criteria"]}["W1"]["pass"] is False
    st = _stations()
    rep = C.run_check("OH", out=str(cache / "w"), n=8, workers=1, weather_only=True, places=_places(st), stations=st, fetch=lambda ids: None)
    assert rep["verdict"] == "fail" and rep["places"] is None
    assert all(c["pass"] is None for c in rep["criteria"] if c["id"].startswith("P"))


def test_shore_criteria_wait_for_three_corrected_cells():
    land = [{"cell_land": 1.0, "corrected": False, "uncorrected": {"ddb": 0.1, "wb": 0.05}, "decided": {"ddb": 0.1, "wb": 0.05}}] * 6
    shore = [{"cell_land": 0.6, "corrected": True, "uncorrected": {"ddb": -1.0, "wb": 0.0}, "decided": {"ddb": 0.9, "wb": 0.0}}] * 2
    places = [{"difference_pct": {f"{d}.{s}": 1.0 for d, s in C.STATS}}] * 5
    crit, ok = C.judge(land + shore, places)
    assert ok and {c["id"]: c["pass"] for c in crit}["W5"] is None
    crit, ok = C.judge(land + shore * 2, places)                       # four corrected, each 0.9 C off: over 0.5 C
    assert not ok and {c["id"]: c["pass"] for c in crit}["W5"] is False


def test_the_command_exits_1_on_a_fail_and_0_on_a_pass(monkeypatch):
    monkeypatch.setattr(E, "state_places", lambda state, date=None: [])
    for verdict, code in (("fail", 1), ("pass", 0)):
        monkeypatch.setattr(C, "run_check", lambda *a, verdict=verdict, **k: {"verdict": verdict})
        with pytest.raises(SystemExit) as e:
            cli.main(["era5", "check", "OH", "--no-r2"])
        assert e.value.code == code


def test_a_state_not_yet_published_takes_its_local_builds_places(monkeypatch):
    import pandas as pd

    from waterledger.national import data

    def unpublished(state, date=None):
        raise data.DataUnavailable("404 latest.json")
    monkeypatch.setattr(data, "fetch_snapshot", unpublished)
    monkeypatch.setattr(data, "_newest_cached", lambda state: None)
    built = pd.DataFrame([{"geoid": "5501000", "name": "Madison city", "level": "place", "lat": 43.08, "lon": -89.39}])
    monkeypatch.setattr(data.LiveData, "places", lambda self: built)
    assert E.state_places("WI") == [{"geoid": "5501000", "name": "Madison city", "level": "place", "lat": 43.08, "lon": -89.39}]
    with pytest.raises(RuntimeError):
        E.state_places("WI", date="2026-11-02")                      # a pinned snapshot that isn't there is an error, not a fallback


def test_cells_as_json_say_when_a_state_is_done(cache, monkeypatch, capsys):
    monkeypatch.setattr(E, "RUNS", str(cache / "runs"))
    places = [{"geoid": str(i), "name": c, "level": "place", "lat": float(c.split("_")[0]) + 0.01, "lon": float(c.split("_")[1])} for i, c in enumerate(LAND)]
    monkeypatch.setattr(E, "state_places", lambda state, date=None: places)
    cli.main(["era5", "cells", "OH", "--part", "1/2", "--json"])
    got = json.loads(capsys.readouterr().out)
    assert (got["cells"], got["done"], got["complete"]) == (6, 0, False) and [p["cells"] for p in got["parts"]] == [3, 3]
    os.makedirs(E.RUNS)
    for c in LAND:
        open(E.result_path(c), "w").write("{}")
    cli.main(["era5", "cells", "OH", "--json"])
    assert json.loads(capsys.readouterr().out)["complete"] is True
