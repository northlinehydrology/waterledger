"""A place's context and estimate are the same from a state's snapshot as from a local build (nightly; pytest -m live)."""
import random

import pytest

import waterledger as wl
from waterledger.national.data import SnapshotData, state_data

pytestmark = pytest.mark.live


def _same_digits(x):
    """Floats to 12 significant figures: a build on another machine can differ in the last digit or two (about 1e-16)."""
    if isinstance(x, float):
        return float(f"{x:.12g}")
    if isinstance(x, dict):
        return {k: _same_digits(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_same_digits(v) for v in x]
    return x


def test_snapshot_equals_live(monkeypatch):
    snap = state_data("OH")
    if not isinstance(snap, SnapshotData):
        pytest.skip("no OH snapshot reachable")
    random.seed(11)
    for g in random.sample(list(snap.places().geoid), 5):
        p = wl.place(geoid=g)
        a = (p.context().model_dump(), wl.Site(place=p, facility=wl.DataCenter(it_mw=200, cooling="hybrid")).estimate().water.model_dump())
        state_data.cache_clear()
        monkeypatch.setenv("WATERLEDGER_DATA", "live")
        b = (p.context().model_dump(), wl.Site(place=p, facility=wl.DataCenter(it_mw=200, cooling="hybrid")).estimate().water.model_dump())
        monkeypatch.delenv("WATERLEDGER_DATA")
        state_data.cache_clear()
        assert _same_digits(a) == _same_digits(b), g
