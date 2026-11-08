"""Snapshot format 3 (model 1.8, design 0004 section 5): the cells a state's places use, written from their runs and read back by the
package, on Michigan part 1's real runs (CACHE/era5/runs/model1.8, Nov 4, 2026: read, never rerun). An estimate from a format 3 snapshot
is the one computed straight from the cell's run file."""
import hashlib, json, os, shutil

import pytest

from waterledger.national import cells, data, era5 as E, provider
from waterledger.national.build import checks
from waterledger_data import era5

RUNS = os.path.join(os.path.expanduser("~"), ".cache", "waterledger", "era5", "runs", "model1.8")
CELLS = ["41.75_-83.50", "42.00_-85.00", "43.50_-83.50"]          # corrected (78% land); land (98%); Akron township's, which the land rule moved it to
PLACES = [{"geoid": "2600001", "name": "A shore place", "level": "place", "lat": 41.76, "lon": -83.52},
          {"geoid": "2600002", "name": "An inland place", "level": "place", "lat": 42.01, "lon": -85.02},
          {"geoid": "2615700720", "name": "Akron township", "level": "township", "lat": 43.63167, "lon": -83.52086}]
pytestmark = pytest.mark.skipif(not all(os.path.exists(os.path.join(RUNS, f"{c}.json")) for c in CELLS), reason="Michigan part 1's runs are not on this machine")


@pytest.fixture
def runs(tmp_path):
    d = tmp_path / "runs"
    d.mkdir()
    for c in CELLS:
        shutil.copy(os.path.join(RUNS, f"{c}.json"), d)
    return str(d)


def _snapshot(tmp_path, runs):
    """A format 3 snapshot folder with the cells and places, and as much of the rest as an estimate reads."""
    folder = tmp_path / "MI" / "2026-11-05"
    folder.mkdir(parents=True)
    fields, cell_files, weather, correction = cells.write(str(folder), PLACES, runs)
    (folder / "places.json").write_text(json.dumps({"places": [{**p, "county_fips": "26000", "division": "2601", **fields[p["geoid"]]} for p in PLACES]}))
    (folder / "climate.json").write_text(json.dumps({"divisions": {"2601": {"name": "MI climate division 1", "station": "S", "station_id": "1-2", "lat": 42.0, "lon": -84.0}},
                                                     "staff_runs": [[40.0, 0.3, 20.0, 0.1, 500.0, 5.0, 0.2]] * 20, "lake_source": {}}))
    files = {n: {"bytes": os.path.getsize(folder / n), "sha256": hashlib.sha256(open(folder / n, "rb").read()).hexdigest()} for n in ("places.json", "climate.json")}
    (folder / "manifest.json").write_text(json.dumps({"format": 3, "state": "MI", "date": "2026-11-05", "model_version": E.RUN_MODEL, "files": files,
                                                      "cells": cell_files, "weather": weather, "correction": correction}))
    return folder


def test_cells_index_places_and_manifest(tmp_path, runs):
    folder = _snapshot(tmp_path, runs)
    idx = json.load(open(folder / "cells" / "index.json"))["cells"]
    assert sorted(idx) == CELLS
    assert idx["43.50_-83.50"]["moved"] == ["2615700720"] and idx["41.75_-83.50"]["corrected"] and not idx["42.00_-85.00"]["corrected"]
    places = {p["geoid"]: p for p in json.load(open(folder / "places.json"))["places"]}
    akron = places["2615700720"]
    assert akron["cell"] == "43.50_-83.50" and akron["cell_moved"] and akron["nearest_cell"] == "43.75_-83.50" and akron["nearest_land"] < 0.5
    assert places["2600001"]["weather_corrected"] and not places["2600002"]["weather_corrected"]
    rec = json.load(open(folder / "cells" / "41.75_-83.50.json"))
    run = json.load(open(os.path.join(runs, "41.75_-83.50.json")))
    assert rec["per_100mw"] == run["per_100mw"] and rec["design_dry_bulb_c"] == run["design_dry_bulb_c"] and rec["period"] == "1995-2024"
    assert rec["correction"]["method"] == "qm-1" and [s["name"] for s in rec["correction"]["stations"]] == ["Detroit Metro Wayne County Airport", "Windsor A", "Detroit City Airport"]
    assert "Copernicus" in rec["attribution"] and rec["source"]["licence"] == "CC-BY-4.0"
    m = json.load(open(folder / "manifest.json"))
    assert m["weather"]["doi"] == "10.24381/cds.adbb2d47" and m["weather"]["cells"] == 3 and m["correction"]["cells_corrected"] == 1
    anchors = {a["id"]: a for a in m["correction"]["anchors"]}
    assert anchors["eccc-6139530"]["source"] == "eccc" and "Environment and Climate Change Canada" in m["correction"]["eccc"]["attribution"]
    assert set(m["cells"]) == {f"cells/{c}.json" for c in CELLS} | {"cells/index.json"}


def test_a_cell_with_no_run_stops_the_snapshot(tmp_path, runs):
    os.remove(os.path.join(runs, "42.00_-85.00.json"))
    with pytest.raises(FileNotFoundError, match=f"1 of 3 cells have no model {E.RUN_MODEL} run"):
        cells.write(str(tmp_path), PLACES, runs)


def test_an_estimate_from_a_format_3_snapshot_is_the_cells_run(tmp_path, runs, monkeypatch):
    import waterledger as wl
    from waterledger import scenario as sc
    from waterledger.estimate import water_use
    folder = _snapshot(tmp_path, runs)
    sd = data.SnapshotData("MI", str(folder))
    monkeypatch.setattr(provider, "state_data", lambda state: sd)
    monkeypatch.setattr(wl.Place, "context", lambda self: type("C", (), {"receiving": type("R", (), {"great_lake": None})(),
                                                                        "supply": type("S", (), {"systems": [], "nearest_system_km": None})(),
                                                                        "wastewater": type("W", (), {"plants": []})()})())
    place = wl.Place(geoid="2600001", name="A shore place", kind="city", level="place", state="MI", county="X", county_fips="26000", lat=41.76, lon=-83.52)
    run = json.load(open(os.path.join(runs, "41.75_-83.50.json")))
    D = {"regions": {"41.75_-83.50": {"per_100mw": run["per_100mw"]}}, "staff": {"runs": sd.staff_runs()}, "lake_source": {}}
    for cool in ("dry", "assist", "hybrid", "towers"):
        site = wl.Site(place=place, facility=wl.DataCenter(it_mw=250, cooling=cool), source="muni", wastewater="sewer")
        got = provider.estimate("MI", site)
        assert got.water == water_use(sc.cooling_estimate(D, "41.75_-83.50", cool, 250, "sewer"))
        assert got.model_version == E.RUN_MODEL
    assert provider._cooling("MI", place)[0] == "41.75_-83.50"


def test_check_snapshot_finds_a_cell_that_does_not_close_or_names_no_stations(tmp_path, runs):
    folder = _snapshot(tmp_path, runs)
    sd = data.SnapshotData("MI", str(folder))
    got = cells.check(sd, [p["geoid"] for p in PLACES])
    assert got == {"cells": 3, "places_with_cell": 1.0, "cells_missing": [], "unclosed": [], "corrected_without_stations": []}
    rec = json.load(open(folder / "cells" / "41.75_-83.50.json"))
    rec["per_100mw"]["towers"]["withdrawn_avg"]["central"] *= 1.01
    rec["correction"]["stations"] = []
    sd._j["cells/41.75_-83.50.json"] = rec
    got = cells.check(sd, [p["geoid"] for p in PLACES])
    assert got["unclosed"] == ["41.75_-83.50 towers avg"] and got["corrected_without_stations"] == ["41.75_-83.50"]


def test_a_cell_file_that_does_not_match_the_manifest_is_refused(tmp_path, runs, monkeypatch):
    folder = _snapshot(tmp_path, runs)
    path = folder / "cells" / "42.00_-85.00.json"
    path.write_text(path.read_text().replace('"draws":400', '"draws":401'))
    monkeypatch.setattr(data, "_get", lambda url, timeout=30: b'{"tampered": true}')
    with pytest.raises(data.DataUnavailable, match="does not match its manifest checksum"):
        data.SnapshotData("MI", str(folder)).cell("42.00_-85.00")


def test_a_format_2_snapshot_still_cools_by_division(monkeypatch):
    sd = data.SnapshotData.__new__(data.SnapshotData)
    sd.manifest, sd._j = {"format": 2}, {"climate": {"divisions": {"3901": {"lat": 40.0, "lon": -83.0, "name": "OH 1", "station": "S", "per_100mw": {}}}},
                                         "places": {"places": [{"geoid": "39001", "county_fips": "39049", "division": "3901"}]}}
    monkeypatch.setattr(provider, "state_data", lambda state: sd)
    place = type("P", (), {"geoid": "39001", "county_fips": "39049", "lat": 40.0, "lon": -83.0, "name": "X"})()
    assert provider._cooling("OH", place)[0] == "3901"


def test_latest_json_files_a_snapshot_under_its_own_model(tmp_path, capsys):
    from waterledger import cli
    from waterledger_models import MODEL_VERSION
    (tmp_path / "OH" / "2026-11-05").mkdir(parents=True)
    (tmp_path / "OH" / "2026-11-05" / "manifest.json").write_text(json.dumps({"model_version": "1.8"}))
    cli.main(["latest-json", "OH", "2026-11-05", "--dir", str(tmp_path)])
    got = json.loads(capsys.readouterr().out)
    assert got["by_model"] == {"1.8": "2026-11-05"}
    cli.main(["latest-json", "OH", "2026-11-05"])
    assert json.loads(capsys.readouterr().out)["by_model"] == {MODEL_VERSION: "2026-11-05"}


def test_the_statewide_checks_fail_a_format_3_snapshot_on_its_cells(tmp_path, runs):
    """check-snapshot's checks on a snapshot whose other layers all pass: it passes with every place on a cell that closes, and fails, naming the
    cell, when one doesn't close or isn't in the manifest's stations."""
    import pandas as pd
    folder = _snapshot(tmp_path, runs)
    sd = data.SnapshotData("MI", str(folder))
    pl = pd.DataFrame([{**p, "county_fips": "26000"} for p in PLACES])
    for name, fn in {"places": lambda: pl, "plants": lambda: [{"lat": 42.0, "lon": -84.0}], "water_use": lambda: {"national": {"counties": {"26000": {}}}},
                     "division_of": lambda f: "2601", "storms": lambda: {"26000": {}}, "rain": lambda: {"26000": 30.0}, "systems_for": lambda g: [1],
                     "sheds_for": lambda g: {"h12": [1]}, "utilities_for": lambda g: [1]}.items():
        setattr(sd, name, fn)
    sd.plants = lambda: [{"lat": p["lat"], "lon": p["lon"]} for p in PLACES]
    got = checks("MI", sd, sample=0)
    assert got["coverage"]["era5_cell"] == 1.0 and got["cells"] == 3 and got["errors"] == []
    sd._j["cells/42.00_-85.00.json"]["per_100mw"]["hybrid"]["returned_annual_mg"]["central"] += 1.0
    with pytest.raises(RuntimeError, match="cell 42.00_-85.00 hybrid annual_mg does not close"):
        checks("MI", sd, sample=0)
    sd._j["cells/42.00_-85.00.json"]["per_100mw"]["hybrid"]["returned_annual_mg"]["central"] -= 1.0
    sd.manifest["correction"]["anchors"] = [a for a in sd.manifest["correction"]["anchors"] if a["id"] != "eccc-6139530"]
    with pytest.raises(RuntimeError, match=r"cell 41.75_-83.50's stations \['eccc-6139530'\] are not in the manifest's anchors"):
        checks("MI", sd, sample=0)
    assert era5.LAND == 0.5
