"""The national tier's water layers for the test states (nightly; pytest -m live)."""
import pytest

pytestmark = pytest.mark.live


@pytest.mark.parametrize("st, fips, name, system", [("OH", "39", "Columbus city", "COLUMBUS PUBLIC WATER SYSTEM"),
                                                    ("VA", "51", "Richmond city", "RICHMOND, CITY OF"),
                                                    ("TX", "48", "Austin city", "CITY OF AUSTIN WATER & WASTEWATER")])
def test_main_system_by_place(st, fips, name, system):
    from waterledger_data import census, supply
    pl = census.places(fips)
    by = supply.systems_by_place(st, pl)
    top = by[pl[pl.name == name].geoid.iloc[0]][0]
    assert top["name"] == system and top["share"] > 0.5 and top["population"] > 100000


@pytest.mark.parametrize("st, lat, lon, city, plant", [("TX", 30.2672, -97.7431, "Austin", "WALNUT CREEK WWTP"),
                                                         ("VA", 39.0438, -77.4874, None, "BROAD RUN REG. RECL. FAC."),
                                                         ("OH", 39.997, -82.998, "Columbus", "COLUMBUS JACKSON PIKE WWTP & SEWERS")])
def test_nearest_plant(st, lat, lon, city, plant):
    from waterledger_data import wastewater as ww
    P = ww.plants(st)
    assert ww.nearest(P, lat, lon, city)[0]["name"] == plant
    assert all(p["design_mgd"] is None or p["design_mgd"] > 0 for p in P)


@pytest.mark.parametrize("st, fips, name, basin, reaches", [("OH", "39", "Columbus city", "Upper Scioto", "Ohio River"),
                                                            ("VA", "51", "Loudoun County", "Middle Potomac-Catoctin", "Potomac River"),
                                                            ("TX", "48", "Austin city", "Austin-Travis Lakes", "Colorado River")])
def test_watersheds_and_downstream(st, fips, name, basin, reaches):
    from waterledger_data import census, receiving as rc
    pl = census.places(fips)
    w = rc.watersheds_by_place(st, pl)[pl[pl.name == name].geoid.iloc[0]]
    assert w["h8"]["name"] == basin and w["h12"][0]["share"] > 0.05
    path = rc.downstream(w["h12"][0]["code"])
    assert path[0]["code"] == w["h12"][0]["code"] and any(reaches in p["name"] for p in path)
    assert any(p["listings"] for p in path)


def test_statewide_impairment_table():
    from waterledger_data import receiving as rc
    H = rc.by_huc12("OH")
    assert rc.organization("OH")[0] == "21OHIO" and len(H) > 1400 and sum(1 for v in H.values() if "i" in v) > 1000
