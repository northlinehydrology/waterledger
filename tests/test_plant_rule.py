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


def test_which_plants_count(monkeypatch):
    """The same rule in every state: ECHO has a permit it hasn't terminated, whether on its list of public plants or looked up by number, or the survey gives a state permit."""
    tables = {"FACILITIES": [], "FLOW": [], "PHYSICAL_LOCATION": [], "FACILITY_PERMIT": []}
    plants = (("ok", ["XX1"]), ("expired", ["XX2"]), ("terminated", ["XX3"]), ("no_permit", []), ("state", ["GW99  "]), ("one_terminated", ["XX3", "XX1"]),
              ("off_the_list", ["XX4"]), ("off_the_list_terminated", ["XX5"]), ("gone_from_echo", ["XX6"]))
    for cid, permits in plants:
        tables["FACILITIES"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "INFRASTRUCTURE_TYPE": "Wastewater", "FACILITY_NAME": cid})
        tables["FLOW"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "FLOW_TYPE": "Total Flow", "CURRENT_DESIGN_FLOW": "2.0"})
        tables["PHYSICAL_LOCATION"].append({"CWNS_ID": cid, "STATE_CODE": "XX", "LATITUDE": "40.0", "LONGITUDE": "-90.0", "CITY": "C"})
        tables["FACILITY_PERMIT"] += [{"CWNS_ID": cid, "STATE_CODE": "XX", "PERMIT_NUMBER": pm, "PERMIT_TYPE": "State" if pm.startswith("GW") else "Individual Permit"} for pm in permits]
    row = lambda k, v: {"SourceID": k, "CWPPermitStatusDesc": v, "PastCalYrAverageFlow": "1.0", "CWPMajorMinorStatusFlag": "M", "CWPCsoFlag": "N", "CWPStateWaterBodyName": "R", "RadWBDHuc12": "1"}
    asked = {}
    monkeypatch.setattr(ww, "_cwns", lambda t: tables[t])
    monkeypatch.setattr(ww, "_echo", lambda st: [row("XX1", "Effective"), row("XX2", "Expired"), row("XX3", "Terminated")])
    monkeypatch.setattr(ww, "_echo_by_permit", lambda st, ids: asked.setdefault("ids", set(ids)) and [row("XX4", "Admin Continued"), row("XX5", "Terminated")])
    got = {q["name"].lower(): q for q in ww.plants("XX")}
    assert set(got) == {"ok", "expired", "state", "one_terminated", "off_the_list"}
    assert asked["ids"] == {"XX4", "XX5", "XX6"}                    # only what the list of public plants doesn't have, and no state permit
    assert got["expired"]["flow_mgd"] == 1.0 and got["off_the_list"]["flow_mgd"] == 1.0 and got["state"]["flow_mgd"] is None and got["state"]["id"] == "GW99" and got["one_terminated"]["id"] == "XX1"
