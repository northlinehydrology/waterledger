"""A state's snapshot (design 0003): files, manifest, checksums, and downstream paths equal to the tracer's (-m live). Format 3
needs the state's cell runs, so it is skipped where they aren't (GitHub's nightly) and runs on the machine that made them."""
import hashlib, json, os, random

import pytest

pytestmark = pytest.mark.live


def test_ohio_snapshot(tmp_path):
    from waterledger.national.snapshot import write
    from waterledger.national.cells import RunsMissing
    from waterledger_data import receiving as rc
    try:
        folder = write("OH", str(tmp_path), date="2000-01-01")
    except RunsMissing as ex:
        pytest.skip(f"no cell runs here: {ex}")
    m = json.load(open(os.path.join(folder, "manifest.json")))
    assert m["format"] == 3 and m["state"] == "OH" and m["model_version"]
    assert set(m["files"]) == {"places.json", "places.parquet", "supply.json", "wastewater.json", "receiving.json", "climate.json", "energy.json",
                               "wateruse.json"}
    assert m["water_use_years"]["national"] == 2015 and m["water_use_years"]["state"] >= 2024
    assert set(m["inputs"]) == {"inputs/wateruse/usgs2015_county_OH.csv", "inputs/wateruse/odnr_registration.json"}
    for name, f in {**m["files"], **m["inputs"], **m["cells"]}.items():
        assert hashlib.sha256(open(os.path.join(folder, name), "rb").read()).hexdigest() == f["sha256"]
    places = json.load(open(os.path.join(folder, "places.json")))["places"]
    assert len(places) > 2300 and all(p["division"] and f"cells/{p['cell']}.json" in m["cells"] for p in places)
    rec = json.load(open(os.path.join(folder, "receiving.json")))
    random.seed(5)
    for s in random.sample(sorted(rec["downstream"]), 3):
        assert rec["downstream"][s] == [r["code"] for r in rc.downstream(s, hops=24)]
    assert len(json.load(open(os.path.join(folder, "climate.json")))["divisions"]) == 10
    W = json.load(open(os.path.join(folder, "wateruse.json")))
    assert len(W["national"]["counties"]) == len(W["state"]["counties"]) == 88 and W["state"]["basis"]["source"] == "odnr_wwfr"
