"""Validation rows any state can carry (design 0011, decision 9): Michigan's, worked out from its published cells and staff draws, are the rows its
page shows; a state with none has none."""
import glob
import json
import os

import pytest

from waterledger import validation


def test_a_state_without_rows_has_none():
    assert validation.rows("OH", {}, [], None) == []


@pytest.mark.live
def test_michigans_rows_are_its_pages():
    from waterledger_data.config import SITE
    d = os.path.join(SITE, "mi", "data")
    if not os.path.exists(os.path.join(d, "cells")):
        pytest.skip("no local Michigan site data")
    E = json.load(open(os.path.join(d, "estimates.json"), encoding="utf-8"))
    P = json.load(open(os.path.join(d, "places.json"), encoding="utf-8"))["places"]
    used = {p["e"] for p in P if p.get("e")}
    cells = {os.path.basename(f)[:-5]: json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(d, "cells", "*.json"))}
    cells = {k: v for k, v in cells.items() if k in used}
    named = lambda name, county: next(p for p in P if p["n"].lower() == name and p["c"] == county)["e"]
    assert validation.rows("MI", cells, E["staff"]["runs"], named) == E["validation"]
