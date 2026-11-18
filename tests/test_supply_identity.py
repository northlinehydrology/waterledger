"""Design 0018's identity test: the ERA5 supply path (pv.hourly, pv.output, wind.hourly, and supply scenarios on the shared runner) gives what it
gave before the path for a study's own forcing was added (tests/data/supply_before_aorc.json, written by tests/supply_reference.py from main at
561740f on macOS arm64, never from this branch).

To the last bit on macOS arm64, where the fixture was written. Elsewhere the platform's own sin, cos and exp differ from macOS's in the last
bits, so the fixture can't be met exactly: within 1e-12, relative or absolute. Measured on Linux (Python 3.12, Nov 16, 2026): this branch
equalled f370fcc run on Linux to the bit, and both differ from the macOS fixture by at most 3.1e-15 relative (7.2e-16 absolute), so 1e-12
leaves a margin of about a thousand and still catches any change to the method."""
import json
import math
import os
import platform
import sys

import supply_reference

HERE = os.path.dirname(os.path.abspath(__file__))
EXACT = sys.platform == "darwin" and platform.machine() == "arm64"
TOL = 1e-12


def _same(a, b, path):
    if isinstance(b, dict):
        assert set(a) == set(b), path
        for k in b:
            _same(a[k], b[k], f"{path}/{k}")
    elif isinstance(b, list):
        assert len(a) == len(b), path
        for x, y in zip(a, b):
            _same(x, y, path)
    elif isinstance(b, float) and not EXACT:
        assert math.isclose(a, b, rel_tol=TOL, abs_tol=TOL), (path, a, b)
    else:
        assert a == b, (path, a, b)


def test_the_era5_path_is_unchanged():
    want = json.load(open(os.path.join(HERE, "data", "supply_before_aorc.json"), encoding="utf-8"))
    got = json.loads(json.dumps(supply_reference.results()))
    _same(got, want, "")
