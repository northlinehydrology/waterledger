"""A place's context and estimate are the same from a state's snapshot as from a local build (nightly; pytest -m live)."""
import random

import pytest

import waterledger as wl
from waterledger.national.data import SnapshotData, state_data

pytestmark = pytest.mark.live


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
        assert a == b, g
