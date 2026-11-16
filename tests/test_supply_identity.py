"""Design 0018's identity test: the ERA5 supply path (pv.hourly, pv.output, wind.hourly, and supply scenarios on the shared runner) gives what it
gave before the path for a study's own forcing was added (tests/data/supply_before_aorc.json, written by tests/supply_reference.py from main at
f370fcc), to the last bit."""
import json
import os

import supply_reference

HERE = os.path.dirname(os.path.abspath(__file__))


def test_the_era5_path_is_unchanged():
    want = json.load(open(os.path.join(HERE, "data", "supply_before_aorc.json"), encoding="utf-8"))
    got = json.loads(json.dumps(supply_reference.results()))
    assert set(got) == set(want)
    for k in want:
        assert got[k] == want[k], k
