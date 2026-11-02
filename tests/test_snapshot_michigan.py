"""Michigan's snapshot (design 0003, decision 8): its shared files agree with what Michigan's provider says, and the site
files it carries are the site's own. Runs where Michigan's site data is at hand (Northline) or downloadable (-m live)."""
import os, random

import pytest

import waterledger as wl
from waterledger import scenario as sc
from waterledger.national.data import SnapshotData

pytestmark = [pytest.mark.live, pytest.mark.state_mi]
WELL_PLACES_MIN, WELL_RECORDS_MIN = 1300, 470000


@pytest.fixture(scope="module")
def snap(tmp_path_factory):
    from waterledger.states.mi.snapshot import write
    return SnapshotData("MI", write(str(tmp_path_factory.mktemp("snap")), date="2000-01-01"))


def test_carries_the_site_files(snap):
    import json
    for n in ("places", "estimates", "waters", "power"):
        assert json.load(open(os.path.join(snap.folder, "michigan", n + ".json"))) == sc.data(n)


def test_shared_files_agree_with_michigan(snap):
    random.seed(7)
    for r in random.sample(sc.data("places")["places"], 40):
        p = wl.place(geoid=r["g"])
        c = p.context()
        assert [s.pwsid for s in c.supply.systems] == [w["pwsid"] for w in snap.systems_for(r["g"])]
        if not c.supply.systems and c.supply.nearest_system:
            assert snap.nearest_system(r["g"])[0]["pwsid"] == c.supply.nearest_system.pwsid
        sheds = snap.sheds_for(r["g"])
        assert [w.huc12 for w in c.receiving.watersheds] == [w["code"] for w in sheds["h12"]]
        if sheds["h12"]:
            assert [x.huc12 for x in c.receiving.downstream] == [x["code"] for x in snap.downstream(sheds["h12"][0]["code"])]
        assert snap.division_of(r["cf"]) == c.climate.region or snap.division_runs()[c.climate.region]
        assert snap.storms().get(r["cf"], {}) == c.climate.design_storms_in
        assert {u.name for u in c.energy.utilities} == {u["name"] for u in snap.utilities_for(r["g"])}
    assert snap.division_runs()["west"]["per_100mw"] == sc.data("estimates")["regions"]["west"]["per_100mw"]


def test_water_use_is_egle_then_usgs(snap):
    W = snap.water_use()
    kent = sc.data("estimates")["county_uses_mgd"]["Kent"]
    assert W["state"]["basis"]["source"] == "egle2025" and W["state"]["counties"]["26081"]["source_values"] == kent
    assert W["state"]["counties"]["26081"]["mgd"]["public_supply"] == kent["Public water systems"]
    assert W["national"]["counties"]["26081"]["mgd"]["total"] == 27.76 and len(W["national"]["counties"]) == 83


def wells_look_whole(wells):
    """Household wells by place are all there: a source that answers with too little for some counties raises no error. Floors a little under the Nov 1, 2026 counts [A]."""
    return len(wells) >= WELL_PLACES_MIN and sum((v[0] or 0) + (v[3] or 0) for v in wells.values()) >= WELL_RECORDS_MIN


def test_household_wells_are_all_there():
    assert wells_look_whole(sc.data("waters")["wells"])
    assert not wells_look_whole({"a": [10, 1, 1, 0, 0, 0]})
