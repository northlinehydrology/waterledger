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
