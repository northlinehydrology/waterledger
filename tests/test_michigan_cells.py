"""Michigan on ERA5 cells (model 1.8): a place in the site's data names its cell (`e`), and its cooling comes from the cell's results
(data/cells/<cell>.json), as the page loads them; a place without one (model 1.7 site data) keeps its region's. Rainfall, salt and golf
stay by region. On one of Michigan part 1's real runs (read, not rerun)."""
import json, os

import pytest

from waterledger import scenario as sc
from waterledger.national import cells

RUN = os.path.join(os.path.expanduser("~"), ".cache", "waterledger", "era5", "runs", "model1.8", "42.00_-85.00.json")
pytestmark = pytest.mark.skipif(not os.path.exists(RUN), reason="Michigan part 1's runs are not on this machine")


@pytest.fixture
def site(tmp_path, monkeypatch):
    """A site data folder: estimates with a region's results and staff draws, and one cell file, as `waterledger build mi` writes them."""
    run = json.load(open(RUN))
    d = tmp_path / "data"
    (d / "cells").mkdir(parents=True)
    old = {k: {"p10": v["p10"] * 2, "p50": v["p50"] * 2, "p90": v["p90"] * 2, "central": v["central"] * 2} for k, v in run["per_100mw"]["hybrid"].items()}
    est = {"regions": {"southwest": {"name": "Southwest Michigan", "station": "Kalamazoo area", "per_100mw": {**run["per_100mw"], "hybrid": old}}},
           "staff": {"runs": [[40.0, 0.3, 20.0, 0.1, 500.0, 5.0, 0.2]] * 20}, "lake_source": {}}
    (d / "estimates.json").write_text(json.dumps(est))
    (d / "cells" / "42.00_-85.00.json").write_text(json.dumps(cells.record(run)))
    monkeypatch.setattr(sc, "DATA", str(d))
    monkeypatch.setattr(sc, "_cache", {})
    return run


def test_a_place_with_a_cell_cools_on_its_cells_results(site):
    p = {"g": "1", "r": "southwest", "e": "42.00_-85.00"}
    D, key = sc.cooling(p)
    assert key == "42.00_-85.00" and D["regions"][key]["per_100mw"] == site["per_100mw"] and "southwest" in D["regions"]
    want = sc.cooling_estimate({"regions": {key: {"per_100mw": site["per_100mw"]}}, "staff": D["staff"], "lake_source": {}}, key, "hybrid", 300, "sewer")
    assert sc.estimate(p, 300, "hybrid", "sewer") == want
    assert sc.electricity(*sc.cooling(p), "hybrid", 300)["pue"]["mid"] == site["per_100mw"]["hybrid"]["pue_avg"]["p50"]


def test_a_place_without_a_cell_keeps_its_regions_results(site):
    p = {"g": "1", "r": "southwest"}
    assert sc.cooling(p)[1] == "southwest"
    a, b = sc.estimate(p, 300, "hybrid", "sewer"), sc.estimate({**p, "e": "42.00_-85.00"}, 300, "hybrid", "sewer")
    assert a["wAvg"]["mid"] > b["wAvg"]["mid"]                         # the fixture's region carries twice the cell's hybrid water


def test_a_cell_record_is_the_runs_numbers_with_its_story(site):
    rec = sc.cell("42.00_-85.00")
    assert rec["per_100mw"] == site["per_100mw"] and rec["correction"]["reason"] == "cell at least 90% land" and rec["model_version"] == "1.8"
    assert "Copernicus" in rec["attribution"]


def test_michigans_cell_points_are_the_snapshots():
    """`waterledger build mi` gives each place the cell of the point Michigan's snapshot carries for it (its page position in degrees,
    rounded to five places), which is the point `era5 run MI` assigned: a place on a cell boundary can't land in a cell with no run."""
    from waterledger.states.mi import build as B
    from waterledger_data import era5
    for lon, lat in ((-85.5207, 42.8802), (-83.4847, 42.2271), (-84.0132, 46.4900)):
        x, y = B.proj(lon, lat)
        lo, la = sc.lonlat({"x": x, "y": y})
        assert B.cell_for(lon, lat) == era5.cell(round(la, 5), round(lo, 5))["id"]
