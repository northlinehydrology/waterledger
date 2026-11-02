"""The statewide checks read the data they are given, so a snapshot's check tests what the snapshot holds."""
from types import SimpleNamespace

import pandas as pd
import pytest

from waterledger.national import build


def _data(**over):
    pl = pd.DataFrame({"geoid": ["1", "2"], "name": ["A", "B"], "county_fips": ["01", "02"], "lat": [42.0, 42.0], "lon": [-85.0, -85.0]})
    d = dict(places=lambda: pl, plants=lambda: [{"lat": 42.0, "lon": -85.0}], water_use=lambda: {"national": {"counties": {"01": {}, "02": {}}}},
             division_of=lambda f: "d", storms=lambda: {"01": {}, "02": {}}, rain=lambda: {"01": 30, "02": 30},
             systems_for=lambda g: [{"pwsid": "x"}] if g == "1" else [], sheds_for=lambda g: {"h12": [{"code": "c"}], "h8": None},
             utilities_for=lambda g: [{"name": "u"}])
    return SimpleNamespace(**{**d, **over})


def test_coverage_comes_from_the_data_given(monkeypatch):
    from waterledger_data import energy, receiving, supply, wastewater, wateruse

    def live(*a, **k):
        raise AssertionError("the checks went to a live source")
    for mod, name in ((supply, "systems_by_place"), (receiving, "watersheds_by_place"), (energy, "utilities_by_place"), (wastewater, "plants"), (wateruse, "usgs_2015")):
        monkeypatch.setattr(mod, name, live)
    r = build.checks("OH", _data(), sample=0)
    assert r["coverage"]["water_system"] == 0.5
    assert all(v == 1.0 for k, v in r["coverage"].items() if k != "water_system")


def test_a_layer_below_its_minimum_fails():
    with pytest.raises(RuntimeError, match="utilities"):
        build.checks("OH", _data(utilities_for=lambda g: []), sample=0)
