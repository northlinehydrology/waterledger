"""place.context() gives every category for a Michigan place, from the same data as waterledger.org/mi."""
import waterledger as wl
from waterledger import scenario as sc


def test_gaines():
    c = wl.place("Gaines charter township, MI").context()
    assert c.jurisdiction.county == "Kent" and c.supply.provider == "MI"
    assert any("Byron" in s.name or "Gaines" in s.name for s in c.supply.systems)
    assert c.wastewater.plants and c.wastewater.plants[0].km <= 40
    assert c.receiving.downstream and c.receiving.downstream[0].huc12 == c.receiving.watersheds[0].huc12
    assert set(c.climate.design_storms_in) >= {"2", "10", "100"} and c.climate.region == "west"
    assert c.energy.utilities and 0 < c.energy.utilities[0].share_of_place <= 1
    assert wl.Context.model_validate_json(c.model_dump_json()) == c
    w = c.supply.county_water_use                       # EGLE's figures, the same numbers the page shows, in the shared categories
    assert (w.source, w.kind, w.year, w.county_fips) == ("egle2025", "reported", 2025, "26081")
    assert w.mgd["public_supply"] == c.supply.county_use_mgd["Public water systems"]
    assert w.mgd["total"] == round(sum(c.supply.county_use_mgd.values()), 3)


def test_plants_and_systems_match_the_page():
    p = wl.place("Saline township, MI")
    c, r = p.context(), sc.place(p.geoid)
    assert [q.npdes for q in c.wastewater.plants] == [q["id"] for q in sc._plants_near(r)]
    assert [s.pwsid for s in c.supply.systems] == [w["pwsid"] for w in r["w"]]
