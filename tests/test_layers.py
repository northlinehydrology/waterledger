"""A state's own layers on the base (design 0011): the registry, the manifest's description, and Michigan's layers against what Water
Ledger Michigan carries today (live, with Michigan's raw sources cached)."""
import pytest

from waterledger_data import layers


def test_michigans_layers_are_registered():
    got = {(L.category, L.mode) for L in layers.for_state("mi")}
    assert got == {("household_wells", "adds"), ("coldwater_streams", "adds"), ("impairments", "replaces"), ("utilities", "replaces"), ("salt_regions", "replaces")}
    assert layers.for_state("OH") == []


def test_describe_lists_water_use_and_golf_too():
    d = {x["category"]: x for x in layers.describe("MI")}
    assert d["county_water_use"]["sources"] == ["egle2025"] and d["golf"]["sources"] == ["egle2025"]
    assert {x["category"] for x in layers.describe("OH")} == {"county_water_use", "golf"}
    assert {x["category"] for x in layers.describe("VA")} == {"county_water_use"}        # Virginia's golf row is the regional survey
    assert layers.describe("WY") == []


def test_salt_days_cover_every_region():
    assert set(layers.MI_SALT_DAYS) == set(layers.MI_REGIONS) | {layers.MI_EASTERN_UP["id"]}


def test_eastern_up_counties_are_noaa_division_two():
    """Chippewa, Luce, Mackinac (division 2) go to the eastern Upper Peninsula; Marquette (division 1) stays in the Upper Peninsula region."""
    from unittest import mock
    cd = {"26033": "2002", "26095": "2002", "26097": "2002", "26103": "2001"}
    with mock.patch("waterledger_data.divisions.county_divisions", return_value=cd):
        got = layers.mi_county_regions([{"geoid": g, "lat": 46.4, "lon": -85.0 if g != "26103" else -87.6} for g in cd])
    assert got == {"26033": "eup", "26095": "eup", "26097": "eup", "26103": "up"}


@pytest.mark.live
def test_michigan_layers_match_its_site_data():
    """Built on the base's places, Michigan's layers give what its own builder gives: trout streams and impairments identical, the same top
    utility everywhere, the salt regions changed only at the eastern Upper Peninsula's 68 places (decision 3)."""
    import json
    import os
    from waterledger_data import census
    from waterledger_data.config import SITE
    W = os.path.join(SITE, "mi", "data")
    if not os.path.exists(os.path.join(W, "waters.json")):
        pytest.skip("no local Michigan site data")
    L = layers.build("MI", census.places("26"))
    Wd = json.load(open(os.path.join(W, "waters.json"), encoding="utf-8"))
    P = {p["g"]: p for p in json.load(open(os.path.join(W, "places.json"), encoding="utf-8"))["places"]}
    PW = json.load(open(os.path.join(W, "power.json"), encoding="utf-8"))
    assert all(L["coldwater_streams"][h] == v["tr"][1] for h, v in Wd["h12"].items() if v.get("tr"))
    assert all(L["impairments"][h]["listings"] == v.get("i", []) for h, v in Wd["h12"].items() if h in L["impairments"])
    assert all(PW["utilities"][lst[0][0]]["n"] == L["utilities"][g][0]["name"] for g, lst in PW["places"].items() if lst)
    moved = {g for g in P if P[g]["r"] != L["salt_regions"]["places"][g]}
    assert len(moved) == 68 and all(L["salt_regions"]["places"][g] == "eup" for g in moved)
