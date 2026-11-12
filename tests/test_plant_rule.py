"""One rule for a place's own sewer plant, in every state: its name, and close."""
import pytest

from waterledger import scenario as sc

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


def named(name, city, km, design=5.0):
    return {"id": name, "name": name, "city": city, "lat": km / 111.2, "lon": 0.0, "design_mgd": design}


def test_named_for_a_town():
    assert ww.named_for("ST. CLAIR STP", "St. Clair") and ww.named_for("CITY OF ALTO WWTP", "Alto") and ww.named_for("MONROE METRO WWTP", "monroe")
    assert ww.named_for("ROCK ISLAND MAIN STP", "Rock Island") and ww.named_for("SAGINAW TWP STP", "saginaw")
    assert not ww.named_for("CLINTON RIVER WATER RESOURCE RECOVERY FACILITY", "Clinton")       # a longer place name
    assert not ww.named_for("DEFIANCE CO BELDEN'S SUBDIVISION WWTP", "Defiance", plant_word=False)   # a county's
    assert not ww.named_for("JEFFERSONVILLE DOWNTOWN WWTP", "Jeffersonville") and ww.named_for("JEFFERSONVILLE DOWNTOWN WWTP", "Jeffersonville", plant_word=False)
    assert not ww.named_for("SAND LAKE LAGOONS", "grand rapids", plant_word=False) and not ww.named_for("GRAND RAPIDS WWTP", "")


def test_system_town_and_main_system():
    assert ww.system_town("BAY CITY, CITY OF") == "bay city" and ww.system_town("CITY OF BETHLEHEM") == "bethlehem"
    assert ww.system_town("ADA TOWNSHIP") == "ada" and ww.system_town("GRAND RAPIDS") == "grand rapids"
    systems = [{"name": "GRAND RAPIDS", "share": 0.59}, {"name": "ADA TOWNSHIP", "share": 0.06}]
    assert ww.main_system(systems) == "GRAND RAPIDS"
    assert ww.main_system([{"name": "BAY CITY, CITY OF", "share": 0.38}]) is None and ww.main_system(None) is None


def test_own_plant_named_for_the_place_first():
    """Grand Rapids: Sand Lake's lagoons mail from Grand Rapids and are nearer; the plant named for the city comes first. Of two named for Saginaw, a township's
    plant for the township, the city's for the city."""
    rows = [named("SAND LAKE LAGOONS", "grand rapids", 3.6, 0.05), named("GRAND RAPIDS WWTP", "grand rapids", 4.3, 61.1), named("WYOMING WWTP", "wyoming", 8.2, 24)]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "grand rapids")] == ["GRAND RAPIDS WWTP", "SAND LAKE LAGOONS", "WYOMING WWTP"]
    rows = [named("SAGINAW STP", "saginaw", 2, 32), named("SAGINAW TWP STP", "saginaw", 5, 4.8)]
    assert ww.nearest(rows, 0, 0, "saginaw", township=True)[0]["id"] == "SAGINAW TWP STP"
    assert ww.nearest(rows, 0, 0, "saginaw", township=False)[0]["id"] == "SAGINAW STP"
    # with no plant named for the place, its own plants stay nearest first, and the township word decides nothing
    rows = [named("EAST ROCKHILL TOWNSHIP WWTP", "perkasie", 1.2, 0.6), named("PENNLAND FARMS STP", "perkasie", 7.6, 0.6)]
    assert ww.nearest(rows, 0, 0, "perkasie")[0]["id"] == "EAST ROCKHILL TOWNSHIP WWTP"


def test_main_water_systems_plant_after_own_before_nearest():
    """Cascade Township is on Grand Rapids' water: the Grand Rapids plant before Lowell's, which is nearer, and after a plant of its own."""
    rows = [named("LOWELL STP", "lowell", 12.9, 1.0), named("GRAND RAPIDS WWTP", "grand rapids", 18.3, 61.1), named("WYOMING WWTP", "wyoming", 20.5, 24)]
    got = ww.nearest(rows, 0, 0, "cascade", township=True, system="GRAND RAPIDS")
    assert [q["id"] for q in got] == ["GRAND RAPIDS WWTP", "LOWELL STP", "WYOMING WWTP"] and got[0]["system"] and not got[1]["system"]
    assert ww.nearest(rows, 0, 0, "cascade", township=True)[0]["id"] == "LOWELL STP"                       # no main system: nearest
    assert ww.nearest(rows + [named("CASCADE TWP WWTP", "cascade", 5, 1)], 0, 0, "cascade", township=True, system="GRAND RAPIDS")[0]["id"] == "CASCADE TWP WWTP"
    # a small plant is never the system's: the 0.5 MGD floor holds
    assert not any(q["system"] for q in ww.nearest([named("GRAND RAPIDS STP", "grand rapids", 9, 0.1)], 0, 0, "cascade", system="GRAND RAPIDS"))


def test_michigan_places_by_the_rule():
    """The same rule on Michigan's site data (scenario._plants_near), and in place.context()."""
    import waterledger as wl
    first = lambda name: sc._plants_near(sc.place(wl.place(name).geoid))[0]
    assert first("Cascade charter township, MI")["n"] == "GRAND RAPIDS WWTP" and first("Cascade charter township, MI")["system"]
    assert first("Grand Rapids city, MI")["n"] == "GRAND RAPIDS WWTP" and first("Lansing city, MI")["n"] == "LANSING WWTP"
    assert first("Gaines charter township, MI")["n"] == "WYOMING WWTP"
    c = wl.place("Cascade charter township, MI").context()
    assert c.wastewater.plants[0].name == "GRAND RAPIDS WWTP" and c.wastewater.plants[0].system and not c.wastewater.plants[0].own
