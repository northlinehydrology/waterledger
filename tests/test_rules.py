"""Each state's reviewed rules (waterledger.rules): every file well formed and cited, and the lines read the way the statutes do. Nothing here changes an estimate
(test_runoff_by_hand.py pushes every line to both extremes and checks no estimated value moves)."""
import datetime

import pytest

from waterledger import levels as lv
from waterledger import rules

LEVELS, PERIODS, WHERE, SOURCES = {"mid", "large"}, {"capacity", "30 days", "90 days"}, {"great_lakes_basin", "outside_great_lakes_basin"}, {"ground", "surface", "lake"}


@pytest.mark.parametrize("st", rules.states())
def test_a_rules_file_is_well_formed_and_cited(st):
    R = rules.load(st)
    datetime.date.fromisoformat(str(R["checked"]))
    ids = {s["id"] for s in R["sources"]}
    assert len(ids) == len(R["sources"]), "a source id is used twice"
    for s in R["sources"]:
        assert s["url"].startswith("https://") and s["title"] and s.get("short"), s
    W = R["withdrawals"]
    assert W["summary"] and W.get("period", "30 days") in PERIODS
    keys = [x["key"] for x in W["lines"]]
    assert len(keys) == len(set(keys)) and "below" not in keys
    for x in W["lines"]:
        assert x["mgd"] > 0 and x["level"] in LEVELS and x["tag"], x
        assert x.get("period", W.get("period", "30 days")) in PERIODS and x.get("measure", "withdrawn") in ("withdrawn", "consumed")
        assert x.get("where") in WHERE | {None} and set(x.get("source", [])) <= SOURCES
        assert x.get("sources") and set(x["sources"]) <= ids, x
    for k in ("discharge", "lake_erie", "large_load", "septic"):
        if k in R:
            assert set(R[k].get("sources", [])) <= ids and R[k].get("sources"), k
    if "septic" in R:
        assert "below_gpd" not in R["septic"]["lines"][-1] and "max_gpd" not in R["septic"]["lines"][-1], "the last septic line covers everything above"
    if "large_load" in R:
        assert R["large_load"]["mw"] > 0 and R["large_load"]["text"] and R["large_load"]["caption"]
    # the context carries the Compact's line beside the state's
    assert rules.withdrawals(st)["compact_use_mgd"] == rules.COMPACT_USE_MGD and rules.withdrawals(st)["lines"]


def test_a_state_without_a_file_has_no_lines():
    assert rules.load("ZZ") is None and rules.withdrawals("ZZ") == {"compact_use_mgd": 5.0} and rules.jurisdiction("ZZ") == []


def test_michigan_part_327():
    # MCL 324.32701: over 100,000 gallons a day over any 30 days registers; MCL 324.32723: a permit over 2,000,000, or over 1,000,000 in Zone C; the Great Lakes are waters of the state
    W = rules.withdrawals("MI")
    assert [lv.withdrawal(v, W)[1] for v in (0.1, 0.11, 1.0, 1.01, 2.0, 2.01)] == ["below", "register", "register", "zone_c", "zone_c", "permit"]
    assert lv.withdrawal(2.01, W, basin=True, source="lake")[1] == "permit"
    assert lv.permit_flag("zone_c", W) == "zone_c" and lv.permit_flag("register", W) is None and "Zone C" in lv.flag_note("zone_c", W)


def test_ohio_by_basin_source_measure_and_period():
    W = rules.withdrawals("OH")
    q = lambda month=0.0, peak=0.0, c90=0.0, cpeak=0.0: {"withdrawn_month": month, "withdrawn_peak": peak, "consumed_90": c90, "consumed_peak": cpeak}
    # ORC 1521.16: registration on capacity (the peak day), more than 100,000 gallons a day
    assert lv.withdrawal(q(peak=0.1), W, basin=False)[1] == "below" and lv.withdrawal(q(peak=0.11), W, basin=False)[1] == "register"
    # ORC 1522.12: in the Lake Erie basin, at least 1 MGD from wells or streams over 90 days (the highest month stands in), at least 2.5 MGD from the lake
    assert lv.withdrawal(q(month=1.0, peak=1.5), W, basin=True, source="ground") == ("large", "permit")
    assert lv.withdrawal(q(month=0.99, peak=1.5), W, basin=True, source="ground")[1] == "register"
    assert lv.withdrawal(q(month=0.99, peak=1.5), W, basin=True, source="ground", peak=True)[1] == "permit"
    assert lv.withdrawal(q(month=2.4, peak=2.4), W, basin=True, source="lake")[1] == "register"
    assert lv.withdrawal(q(month=2.5, peak=2.5), W, basin=True, source="lake")[1] == "lake_permit"
    # ORC 1521.23: outside it, more than 2 MGD of water used up over 30 days; the Lake Erie lines don't apply there
    assert lv.withdrawal(q(month=5, peak=5, c90=1.9, cpeak=2.5), W, basin=False)[1] == "register"
    assert lv.withdrawal(q(month=5, peak=5, c90=2.01, cpeak=2.5), W, basin=False) == ("large", "consumptive_permit")
    assert lv.withdrawal(q(month=5, peak=5, c90=1.9, cpeak=2.5), W, basin=False, peak=True)[1] == "consumptive_permit"


def test_reviewed_states_are_covered_in_the_package():
    from waterledger.national import provider
    assert provider.not_covered("OH") == {} and "state_rules" in provider.not_covered("VA")
    assert {"topic": "withdrawal", "key": "register", "mgd": 0.1, "tag": "Must register with the state", "sources": ["orc_1521_16"]} in rules.jurisdiction("OH")


def test_georgia_one_line_on_the_monthly_average():
    # O.C.G.A. 12-5-31(b) and 12-5-96(a)(1): a permit from EPD above 100,000 gallons a day, surface water or groundwater; the monthly average (391-3-6-.07(4))
    W = rules.withdrawals("GA")
    q = lambda month, peak: {"withdrawn_month": month, "withdrawn_peak": peak, "consumed_90": 0.0, "consumed_peak": 0.0}
    assert lv.withdrawal(q(0.1, 0.5), W, source="ground")[1] == "below" and lv.withdrawal(q(0.11, 0.11), W, source="surface") == ("large", "permit")
    assert lv.withdrawal(q(0.1, 0.5), W, peak=True)[1] == "permit" and lv.permit_flag("permit", W) == "permit" and "EPD" in lv.flag_note("permit", W)
    # no sentence that the utility's permit covers the campus: Georgia's statutes and rules don't say so
    assert "utility" not in rules.load("GA")["withdrawals"] and "lake_erie" not in rules.load("GA")
