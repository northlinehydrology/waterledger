"""A state's snapshot (design 0003): files, manifest, checksums, and downstream paths equal to the tracer's (nightly; -m live)."""
import hashlib, json, os, random

import pytest

pytestmark = pytest.mark.live


def test_ohio_snapshot(tmp_path):
    from waterledger.national.snapshot import write
    from waterledger_data import receiving as rc
    folder = write("OH", str(tmp_path), date="2000-01-01")
    m = json.load(open(os.path.join(folder, "manifest.json")))
    assert m["format"] == 1 and m["state"] == "OH" and m["model_version"]
    assert set(m["files"]) == {"places.json", "places.parquet", "supply.json", "wastewater.json", "receiving.json", "climate.json", "energy.json"}
    for name, f in m["files"].items():
        assert hashlib.sha256(open(os.path.join(folder, name), "rb").read()).hexdigest() == f["sha256"]
    places = json.load(open(os.path.join(folder, "places.json")))["places"]
    assert len(places) > 2300 and all(p["division"] for p in places)
    rec = json.load(open(os.path.join(folder, "receiving.json")))
    random.seed(5)
    for s in random.sample(sorted(rec["downstream"]), 3):
        assert rec["downstream"][s] == [r["code"] for r in rc.downstream(s, hops=24)]
    assert len(json.load(open(os.path.join(folder, "climate.json")))["divisions"]) == 10
