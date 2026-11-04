"""Model 1.8's ERA5 path (design 0004): the land rule's cells, the raw cache, local standard time, parts, the per-cell results cache and
the optional R2 step (a folder stands in for the bucket; wrangler is faked). Offline but for the `live` tests, which read a few cells
from Open-Meteo's open copy of ERA5."""
import csv, json, os, subprocess

import numpy as np
import pytest

from waterledger.national import era5 as E
from waterledger_data import era5, r2

HERE = os.path.dirname(os.path.abspath(__file__))
ASSIGNMENT = os.path.join(HERE, "..", "docs", "methods", "era5-check", "cell_assignment.csv")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(era5, "RAW", str(tmp_path / "raw"))
    monkeypatch.setattr(E, "RUNS", str(tmp_path / "runs"))
    monkeypatch.setattr(E, "ANCHORS", str(tmp_path / "anchors"))
    return tmp_path


def test_every_places_cell_is_the_land_rules():
    """era5.cell on the shipped mask gives every place in the four states the cell, distance, land fraction and move of design 0004's
    cell_assignment.csv (the 2026-11-02.2 snapshots' 5,662 places, 189 of them moved)."""
    moved = 0
    for r in csv.DictReader(open(ASSIGNMENT)):
        c = era5.cell(float(r["lat"]), float(r["lon"]))
        assert (c["id"], c["nearest"]["id"], int(c["moved"])) == (r["cell"], r["nearest_cell"], int(r["moved"])), r["name"]
        assert c["land"] == pytest.approx(float(r["cell_land"]), abs=6e-4) and c["km"] == pytest.approx(float(r["cell_km"]), abs=0.051)
        moved += c["moved"]
    assert moved == 189


def test_lorain_moves_to_the_nearest_cell_at_least_half_land():
    c = era5.cell(41.4528, -82.1824)
    assert c["nearest"]["id"] == "41.50_-82.25" and c["nearest"]["land"] < 0.5
    assert c["moved"] and c["id"] == "41.50_-82.00" and c["land"] >= 0.5
    assert era5.cell(41.4528, -82.1824, land=None)["id"] == "41.50_-82.25"
    with pytest.raises(ValueError, match="outside the shipped grid"):
        era5.cell(61.2, -149.9)                                     # Anchorage


def test_parts_cover_every_cell_once_in_near_equal_runs():
    ids = {f"c{i:04d}": None for i in range(616)}
    got = [E.part(ids, k, 3) for k in (1, 2, 3)]
    assert [len(g) for g in got] == [205, 205, 206] and sorted(sum(got, [])) == sorted(ids)
    assert [len(E.part({f"c{i}": 0 for i in range(272)}, k, 2)) for k in (1, 2)] == [136, 136]
    assert E.parse_part("2/3") == (2, 3)
    for bad in ("3", "0/2", "3/2"):
        with pytest.raises(ValueError):
            E.part(ids, *E.parse_part(bad)) if "/" in bad else E.parse_part(bad)


def _synthetic(cid, seed=0):
    """A raw cell series as fetch writes it: hourly from 1995-01-01 UTC to 2025-01-02, a daily and yearly cycle."""
    n = int((era5.END - era5.START).astype(int))
    h = np.arange(n)
    r = np.random.default_rng(seed)
    t = (10 - 12 * np.cos(2 * np.pi * h / 8766) + 5 * np.sin(2 * np.pi * (h - 14) / 24) + r.normal(0, 2, n)).astype(np.float32)
    return era5.write_raw(cid, {"temperature_2m": t, "dew_point_2m": (t - np.abs(r.normal(4, 3, n))).astype(np.float32)}, "2026-11-04", {"source": "test"})


def test_a_cell_in_local_standard_time_is_whole_days_1995_2024(cache):
    _synthetic("41.50_-82.00")
    meta = json.load(open(era5.raw_path("41.50_-82.00")[:-4] + ".json"))
    assert meta["sha256"] == era5.sha256(era5.raw_path("41.50_-82.00")) and meta["licence"] == "CC-BY-4.0" and "Copernicus" in meta["attribution"]
    times, t, rh = era5.hourly("41.50_-82.00")
    assert times[0] == "1995-01-01T00:00" and times[-1] == "2024-12-31T23:00" and len(times) == 262992
    utc, ut, _ = era5.series("41.50_-82.00")
    assert t[0] == pytest.approx(ut[5])                            # 82 W: local standard time is UTC - 5 h
    assert 1 <= min(rh) and max(rh) <= 100


def test_a_cell_with_a_missing_hour_is_an_error(cache):
    path = _synthetic("41.50_-82.00")
    z = dict(np.load(path))
    z["temperature_2m"][1000] = np.nan
    era5.write_raw("41.50_-82.00", {k: z[k] for k in era5.VARIABLES}, "2026-11-05", {"source": "test"})
    with pytest.raises(ValueError, match="missing"):
        era5.local("41.50_-82.00")


# --- R2 ---

class Counting(r2.FolderStore):
    def __init__(self, root):
        super().__init__(root)
        self.puts = []

    def _put_file(self, key, path):
        self.puts.append(key)
        super()._put_file(key, path)


class Broken(r2.Store):
    name = "broken"

    def _put_file(self, key, path):
        raise ConnectionError("network down")

    def _get_file(self, key, path):
        raise ConnectionError("network down")


def test_r2_skips_a_file_it_already_has_and_checks_what_it_gives_back(tmp_path):
    s = Counting(str(tmp_path / "bucket"))
    f = tmp_path / "a.json"
    f.write_text('{"a": 1}')
    assert s.put("runs/a.json", str(f)) and s.puts == ["runs/a.json", "runs/a.json.sha256"]
    assert s.put("runs/a.json", str(f)) and len(s.puts) == 2                         # same checksum: not sent again
    f.write_text('{"a": 2}')
    assert s.put("runs/a.json", str(f)) and len(s.puts) == 4
    out = tmp_path / "got" / "a.json"
    assert s.get("runs/a.json", str(out)) and out.read_text() == '{"a": 2}'
    assert not s.get("runs/none.json", str(tmp_path / "none.json"))
    (tmp_path / "bucket" / "runs" / "a.json").write_text("corrupted")
    out.unlink()
    assert not s.get("runs/a.json", str(out)) and not out.exists()


def test_a_failed_upload_warns_and_never_raises(tmp_path, capsys):
    f = tmp_path / "a.json"
    f.write_text("{}")
    assert Broken().put("runs/a.json", str(f)) is False and f.exists()
    assert "could not upload runs/a.json" in capsys.readouterr().err
    assert Broken().get("runs/a.json", str(tmp_path / "b.json")) is False


def test_wrangler_is_called_with_the_bucket_and_remote_and_a_missing_key_is_none(tmp_path):
    calls = []

    def fake(cmd, **kw):
        calls.append(cmd)
        if cmd[5] == "get":
            open(cmd[cmd.index("--file") + 1], "w").close()               # wrangler leaves an empty file when the key is missing
            return subprocess.CompletedProcess(cmd, 1, "", "✘ [ERROR] The specified key does not exist.")
        return subprocess.CompletedProcess(cmd, 0, "Upload complete.", "")
    s = r2.WranglerStore("waterledger-raw", run=fake)
    f = tmp_path / "a.json"
    f.write_text("{}")
    assert s.put("runs/era5/model1.8/a.json", str(f))
    assert calls[0][:6] == ["npx", "--yes", "wrangler", "r2", "object", "get"] and calls[0][-1] == "--remote"
    assert calls[1][5:8] == ["put", "waterledger-raw/runs/era5/model1.8/a.json", "--file"]
    assert calls[2][6] == "waterledger-raw/runs/era5/model1.8/a.json.sha256"
    assert not s.get("runs/x.json", str(tmp_path / "x.json")) and not (tmp_path / "x.json").exists()


def test_r2_is_off_unless_it_is_set_up():
    assert r2.from_env({}) is None
    assert r2.from_env({"WATERLEDGER_R2": "off", "R2_ACCOUNT_ID": "a", "R2_ACCESS_KEY_ID": "b", "R2_SECRET_ACCESS_KEY": "c"}) is None
    assert isinstance(r2.from_env({"WATERLEDGER_R2": "wrangler"}), r2.WranglerStore)
    assert r2.from_env({"WATERLEDGER_R2": "wrangler", "WATERLEDGER_R2_BUCKET": "other"}).bucket == "other"
    assert isinstance(r2.from_env({"WATERLEDGER_R2": "dir:/tmp/x"}), r2.FolderStore)
    with pytest.raises(ValueError):
        r2.from_env({"WATERLEDGER_R2": "yes"})


# --- runs ---

CELLS = {c: {"cell": {"id": c, "lat": era5.indexes(c)[0] / 4, "lon": era5.indexes(c)[1] / 4, "land": era5.land(c)}, "places": []}
         for c in ("41.50_-82.00", "43.00_-85.50")}                 # Lorain's cell (0.59 land) and Grand Rapids' (0.98)


def _run_stub(calls):
    def run(times, temps, rhs, n, seed, mw):
        calls.append(len(times))
        return {"towers": {"withdrawn_avg": {"p50": float(np.mean(temps))}}}
    return run


def _station(cell_temps_plus=1.0):
    """A shore station 20 km from Lorain's cell, its record the cell's own plus 1 C."""
    from waterledger_models import quantile_mapping as Q
    times, t, td = era5.local("41.50_-82.00")
    return {"id": "s1", "name": "Shore Station", "source": "isd", "lat": 41.32, "lon": -82.0, "cell_land": 0.7,
            "elev_m": era5.elevation("41.50_-82.00"), "qt": Q.fit(times, t + cell_temps_plus, td + cell_temps_plus)}


def test_a_part_runs_each_cell_once_corrects_the_shore_and_resumes_on_another_machine(cache, monkeypatch):
    fetched = []
    fetch = lambda ids: [fetched.append(c) or _synthetic(c, seed=i) for i, c in enumerate(ids)]
    monkeypatch.setattr(E, "anchors", lambda cells, store=None: [_station()])
    bucket = Counting(str(cache / "bucket"))
    calls = []
    out = E.run_part("OH", 1, 1, workers=1, draws=5, store=bucket, cells=CELLS, run=_run_stub(calls), fetch=fetch)
    assert sorted(out) == sorted(CELLS) and sorted(fetched) == sorted(CELLS) and len(calls) == 2
    lorain = json.load(open(out["41.50_-82.00"]))
    assert lorain["model_version"] == "1.8" and lorain["draws"] == 5 and lorain["hours"] == 262992
    assert lorain["correction"]["applied"] and lorain["correction"]["stations"][0]["name"] == "Shore Station"
    before, after = lorain["correction"]["change"]["design_dry_bulb_c"]
    assert after - before == pytest.approx(1.0, abs=1e-6)          # the station is the cell plus 1 C, at the cell's own elevation
    assert json.load(open(out["43.00_-85.50"]))["correction"]["reason"] == "cell at least 90% land"
    keys = set(bucket.puts)
    for c in CELLS:
        assert f"runs/era5/model1.8/{c}.json" in keys and f"era5/{c}/2026-11-04.npz" in keys and f"era5/{c}/latest.json" in keys

    assert E.run_part("OH", 1, 1, workers=1, draws=5, store=bucket, cells=CELLS, run=_run_stub(calls), fetch=fetch) == out
    assert len(calls) == 2                                          # done cells are not run again

    elsewhere = cache / "mac2"                                      # another machine: nothing local, the same bucket
    monkeypatch.setattr(era5, "RAW", str(elsewhere / "raw"))
    monkeypatch.setattr(E, "RUNS", str(elsewhere / "runs"))
    got = E.run_part("OH", 1, 1, workers=1, draws=5, store=bucket, cells=CELLS, run=_run_stub(calls), fetch=fetch)
    assert len(calls) == 2 and len(fetched) == 2 and json.load(open(got["41.50_-82.00"])) == lorain
    assert era5.raw_path("43.00_-85.50")                            # the raw series came down too


def test_a_part_finishes_when_r2_fails(cache, monkeypatch, capsys):
    monkeypatch.setattr(E, "anchors", lambda cells, store=None: [])
    calls = []
    out = E.run_part("OH", 1, 1, workers=1, draws=5, store=Broken(), cells=CELLS, run=_run_stub(calls),
                     fetch=lambda ids: [_synthetic(c) for c in ids])
    assert len(calls) == 2 and all(os.path.exists(p) for p in out.values())
    assert "could not upload runs/era5/model1.8/" in capsys.readouterr().err
    assert json.load(open(out["41.50_-82.00"]))["correction"]["reason"] == "no shore station within 100 km"


@pytest.mark.live
def test_open_copy_cells_and_one_run(cache):
    """Two cells from the open copy (Lorain's and Port Huron's), their local series physical, and one short run with the real model."""
    from waterledger_models.datacenter import cooling
    paths = era5.fetch(["41.50_-82.00", "43.00_-82.50"])
    for c, p in paths.items():
        meta = json.load(open(p[:-4] + ".json"))
        assert meta["missing"] == {"temperature_2m": 0, "dew_point_2m": 0} and meta["sha256"] == era5.sha256(p)
        times, t, rh = era5.hourly(c)
        assert len(times) == 262992 and -40 < min(t) and max(t) < 45 and max(rh) <= 100
    times, t, rh = era5.hourly("41.50_-82.00")
    res = cooling.run_location(times, t, rh, n=5, seed=7, mw=100.0)
    assert res["towers"]["withdrawn_avg"]["p50"] > 0
