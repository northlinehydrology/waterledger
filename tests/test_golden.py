"""The cooling model reproduces its stored results on two years of West Michigan weather. A failure means the numbers changed:
if that was deliberate, bump MODEL_VERSION and rerun tests/golden.py; if not, it is a bug."""
import json, math, os

import golden

HERE = os.path.dirname(__file__)


def close(a, b, path=""):
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for k in a:
            close(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, float) or isinstance(b, float):
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12), f"{path}: {a} != {b}"
    else:
        assert a == b, path


def test_cooling_matches_golden():
    want = json.load(open(os.path.join(HERE, "data", "golden_cooling.json")))
    got = json.loads(json.dumps(golden.results()))
    close(got, want)
