"""Who treats a place's sewage and where its water comes from (design 0023): the survey's sewers first, then the old rules, each labeled."""
import pytest

from waterledger_data import wastewater as ww


def test_chain_end_follows_discharges_with_shares():
    to = {"cs": [("pump", 1.0)], "pump": [("a", 0.6), ("b", 0.4)]}
    assert ww.chain_end("cs", to, {"a", "b"}) == [("a", 0.6), ("b", 0.4)]
    assert ww.chain_end("loop", {"loop": [("loop", 1.0)]}, set()) == []           # a cycle ends nowhere


def test_rank_takes_the_sellers_town_too():
    """Ada Township's system is named for Ada and buys from Grand Rapids: the Grand Rapids plant is the system's town's, before the nearer Lowell."""
    rows = [{"name": "LOWELL STP", "km": 13.4, "own": False}, {"name": "GRAND RAPIDS WWTP", "km": 18.3, "own": False}]
    assert ww.rank([dict(r) for r in rows], "ada", True, "ADA TOWNSHIP")[0]["name"] == "LOWELL STP"
    assert ww.rank([dict(r) for r in rows], "ada", True, ["ADA TOWNSHIP", "GRAND RAPIDS"])[0]["name"] == "GRAND RAPIDS WWTP"


def test_ranked_for_puts_the_survey_first_and_labels_every_row():
    plants = [{"cwns": "near", "id": "N", "name": "NEAR STP", "city": "x", "lat": 0.0, "lon": 0.01, "design_mgd": 1.0},
              {"cwns": "far", "id": "F", "name": "FAR WWTP", "city": "y", "lat": 0.0, "lon": 0.2, "design_mgd": 50.0}]
    served = [{"cwns": "far", "share": 1.0, "basis": "name", "systems": ["PLACE CS"]}]
    got = ww.ranked_for(plants, served, 0.0, 0.0, "place")
    assert [(q["id"], q["basis"]) for q in got] == [("F", "name"), ("N", "nearest")] and got[0]["served_share"] == 1.0


@pytest.mark.live
def test_michigan_places_by_the_survey():
    """Ada and Ypsilanti by their own sewers; Gaines by both of its (Cutlerville's to Wyoming, the township's to Grand Rapids), as its site record has it;
    Williamstown Township not by Meridian Township's system, which lies inside it but is named for Meridian."""
    from waterledger_data import census
    pl = census.places("26")
    S = ww.served_by("MI", pl)
    P = {q.get("cwns"): q["name"] for q in ww.plants("MI")}
    first = lambda n: P[S[pl[pl.name == n].iloc[0].geoid][0]["cwns"]]
    assert first("Ada township") == "GRAND RAPIDS WWTP" and first("Ypsilanti charter township") == "YCUA WWTP"
    assert first("Gaines charter township") == "WYOMING WWTP"
    assert pl[pl.name == "Williamstown township"].iloc[0].geoid not in S
