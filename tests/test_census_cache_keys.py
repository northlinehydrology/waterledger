"""Caches worked out from a state's places are named for what made them, so a changed query or place list is not read from an old file."""
import pandas as pd

from waterledger_data import census


def test_places_key_follows_the_place_list_not_its_order():
    a = pd.DataFrame({"geoid": ["1836003", "1842624"]})
    assert census.places_key(a) == census.places_key(a.iloc[::-1])
    assert census.places_key(a) != census.places_key(a.iloc[:1])          # a place added (Indianapolis's balance) is a new key


def test_census_cache_is_named_for_its_query(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(census, "RAW", str(tmp_path))
    monkeypatch.setattr(census, "_get", lambda url, params, post=False: calls.append(params["where"]) or {"features": []})
    census._features("place", "18")
    census._features("place", "18")                                          # read from the cache the first call wrote
    assert len(calls) == 1
    (tmp_path / "18_place.json").write_text("[]")                           # a file from before 3.19.1 is not read
    names = sorted(p.name for p in tmp_path.iterdir())
    assert any(n.startswith("18_place_") and n.endswith(".json") for n in names)
