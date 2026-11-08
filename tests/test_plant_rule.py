"""One rule for a place's own sewer plant, in every state: its name, and close."""
import pytest

from waterledger_data import wastewater as ww


def plant(city, km, design=5.0):
    return {"id": city, "name": city, "city": city, "lat": km / 111.2, "lon": 0.0, "design_mgd": design}


def test_own_needs_the_name_and_the_distance():
    assert ww.is_own(True, 9) and ww.is_own(True, ww.OWN_KM)
    assert not ww.is_own(True, 35) and not ww.is_own(False, 1)


def test_own_comes_first_and_small_plants_only_if_own():
    rows = [plant("Far", 30), plant("Close", 8), plant("Near", 3), plant("Tiny", 2, 0.1)]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Close")] == ["Close", "Near", "Far"]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Far")] == ["Near", "Close", "Far"]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Tiny")] == ["Tiny", "Near", "Close", "Far"]


def test_distance_by_hand():
    """One degree of latitude is 6371 x pi / 180 = 111.19 km. One degree of longitude at 60 degrees north is half that."""
    assert ww.distance_km(45, -85, 46, -85) == pytest.approx(111.19, abs=0.01)
    assert ww.distance_km(60, 0, 60, 1) == pytest.approx(55.6, abs=0.05)


def test_michigan_distance_is_true_not_map_units():
    """At 42 N, a degree of longitude is 111.19 x cos 42 = 82.6 km. Map coordinates, fixed at cos 45, made it 78.6 km."""
    from waterledger import scenario as sc
    from waterledger.states.mi import KX, LAT1, LON0, SC
    x = lambda lon: (lon - LON0) * KX * SC
    y = lambda lat: (LAT1 - lat) * SC
    p = {"n": "somewhere township", "x": x(-84.0), "y": y(42.0)}
    sc._cache["waters"] = {"plants": [{"n": "A", "city": "elsewhere", "x": x(-83.0), "y": y(42.0), "design": 5.0}]}
    try:
        assert sc._plants_near(p, km=100)[0]["km"] == pytest.approx(82.6, abs=0.1)
    finally:
        del sc._cache["waters"]


def test_a_plant_stays_without_positive_evidence_it_closed(monkeypatch):
    """The same rule in every state. City "C" has a live plant of 2 MGD; city "T" has none."""
    tables = {"FACILITIES": [], "FLOW": [], "PHYSICAL_LOCATION": [], "FACILITY_PERMIT": []}
    plants = (("ok", ["XX1"], "C", "2.0"), ("expired", ["XX2"], "E", "2.0"), ("state", ["GW99  "], "T", "2.0"), ("no_permit", [], "T", "2.0"), ("Austin 5 Year CIP", [], "C", "152"), ("East China REG CS", ["XX3"], "T", "2.0"),
              ("off_the_list", ["XX4"], "L", "2.0"), ("alone_terminated", ["XX3"], "T", "1.0"), ("alone_gone", ["XX6"], "T", "1.0"), ("small_lagoon", ["XX3"], "C", "0.05"), ("Hamburg Twp WWTP", ["XX3"], "C", "1.6"),
              ("renumbered", ["XX3"], "R", "9.0"), ("replaced_terminated", ["XX3"], "C", "1.5"), ("replaced_gone", ["XX6"], "C", "2.0"), ("larger_than_the_live_one", ["XX3"], "C", "3.0"))
    for cid, permits, city, mgd in plants:
        tables["FACILITIES"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "INFRASTRUCTURE_TYPE": "Wastewater", "FACILITY_NAME": cid})
        tables["FLOW"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "FLOW_TYPE": "Total Flow", "CURRENT_DESIGN_FLOW": mgd})
        tables["PHYSICAL_LOCATION"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "LATITUDE": "40.0", "LONGITUDE": "-90.0", "CITY": city})
        tables["FACILITY_PERMIT"] += [{"CWNS_ID": cid, "STATE_CODE": "XX", "PERMIT_NUMBER": pm, "PERMIT_TYPE": "State" if pm.startswith("GW") else "Individual Permit"} for pm in permits]
    row = lambda k, v, name="": {"SourceID": k, "CWPName": name, "CWPPermitStatusDesc": v, "PastCalYrAverageFlow": "1.0", "CWPMajorMinorStatusFlag": "M", "CWPCsoFlag": "N", "CWPStateWaterBodyName": "R", "RadWBDHuc12": "1"}
    monkeypatch.setattr(ww, "_cwns", lambda t: tables[t])
    monkeypatch.setattr(ww, "_echo", lambda st: [row("XX1", "Effective"), row("XX2", "Expired"), row("XX3", "Terminated")])
    monkeypatch.setattr(ww, "_echo_by_permit", lambda st, ids: [row("XX4", "Admin Continued")])
    monkeypatch.setattr(ww, "_echo_near", lambda st, where: {"renumbered": [row("XX7", "Effective", "RENUMBERED WWTP"), row("XX8", "Effective", "RENUMBERED MS4")]})
    got = {q["name"].lower(): q for q in ww.plants("XX")}
    assert set(got) == {"ok", "expired", "state", "no_permit", "off_the_list", "alone_terminated", "alone_gone", "renumbered", "larger_than_the_live_one", "small_lagoon", "hamburg twp wwtp"}
    assert got["renumbered"]["id"] == "XX7" and got["renumbered"]["flow_mgd"] == 1.0                # the live permit takes over
    assert got["alone_terminated"]["id"] == "XX3" and got["alone_terminated"]["flow_mgd"] is None and got["state"]["id"] == "GW99"


def test_live_permit_needs_the_sewer_and_the_town():
    rows = [{"CWPName": "AU GRES MS4 WWTP", "CWPPermitStatusDesc": "Effective"}, {"CWPName": "BOPP-BUSCH MFG CO-AU GRES", "CWPPermitStatusDesc": "Effective"},
            {"CWPName": "AU GRES WWTP", "CWPPermitStatusDesc": "Terminated"}, {"CWPName": "PINE ACRES WWTP", "CWPPermitStatusDesc": "Effective"},
            {"CWPName": "AU GRES WASTEWATER STORM SITE", "SourceID": "MIR051234", "CWPPermitStatusDesc": "Effective"}, {"CWPName": "AU GRES WWTP-YARD", "SourceID": "MIS310287", "CWPPermitStatusDesc": "Effective"}]
    assert ww.live_permit_at(rows, "AU GRES WWSL", "Au Gres") is None
    rows.append({"CWPName": "AU GRES WWTP", "CWPPermitStatusDesc": "Effective", "SourceID": "MI0058794"})
    assert ww.live_permit_at(rows, "AU GRES WWSL", "Au Gres")["SourceID"] == "MI0058794"
    # a record without the status field (ECHO, Nov 7, 2026) is read as a null status, not terminated, and doesn't stop the build
    assert ww.live_permit_at([{"CWPName": "AU GRES WWTP", "SourceID": "MI0058794"}], "AU GRES WWSL", "Au Gres")["SourceID"] == "MI0058794"


def test_project_records():
    assert ww.is_project("Austin 5 Year CIP - Citywide Waste") and ww.is_project("EAST CHINA REG CS")
    assert not ww.is_project("LUNA PIER STP-CS") and not ww.is_project("LEBANON WWTP & Coll. System") and not ww.is_project("KALKASKA STP")
