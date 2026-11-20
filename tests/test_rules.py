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
    assert W["summary"] and W.get("period", "30 days") in PERIODS and W.get("sources")
    if not W.get("lines"):          # a reviewed state with no numeric line (districts set their own): the summary is what a reader sees
        assert rules.withdrawals(st)["no_line"] == W["summary"]
    keys = [x["key"] for x in W.get("lines", [])]
    assert len(keys) == len(set(keys)) and "below" not in keys
    for x in W.get("lines", []):
        assert all(len(h) % 2 == 0 and h.isdigit() for h in x.get("huc", [])) and all(len(c) == 5 and c.isdigit() for c in x.get("counties", [])), x
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
    assert rules.withdrawals(st)["compact_use_mgd"] == rules.COMPACT_USE_MGD and (rules.withdrawals(st).get("lines") or rules.withdrawals(st).get("no_line"))


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
    assert provider.not_covered("OH") == {} and "state_rules" in provider.not_covered("KS")
    assert {"topic": "withdrawal", "key": "register", "mgd": 0.1, "tag": "Must register with the state", "sources": ["orc_1521_16"]} in rules.jurisdiction("OH")


def test_georgia_one_line_on_the_monthly_average():
    # O.C.G.A. 12-5-31(b) and 12-5-96(a)(1): a permit from EPD above 100,000 gallons a day, surface water or groundwater; the monthly average (391-3-6-.07(4))
    W = rules.withdrawals("GA")
    q = lambda month, peak: {"withdrawn_month": month, "withdrawn_peak": peak, "consumed_90": 0.0, "consumed_peak": 0.0}
    assert lv.withdrawal(q(0.1, 0.5), W, source="ground")[1] == "below" and lv.withdrawal(q(0.11, 0.11), W, source="surface") == ("large", "permit")
    assert lv.withdrawal(q(0.1, 0.5), W, peak=True)[1] == "permit" and lv.permit_flag("permit", W) == "permit" and "EPD" in lv.flag_note("permit", W)
    # no sentence that the utility's permit covers the campus: Georgia's statutes and rules don't say so
    assert "utility" not in rules.load("GA")["withdrawals"] and "lake_erie" not in rules.load("GA")


def test_a_line_limited_to_a_basin_or_counties_applies_only_there():
    W = {"lines": [{"key": "basin", "mgd": 0.1, "level": "large", "huc": ["0205"]}, {"key": "area", "mgd": 0.05, "level": "mid", "counties": ["51001"]}]}
    assert lv.withdrawal(1.0, W, huc="020501010101")[1] == "basin" and lv.withdrawal(1.0, W, huc="020402030405")[1] == "below"
    assert lv.withdrawal(1.0, W, county="51001")[1] == "area" and lv.withdrawal(1.0, W, county="51003")[1] == "below"
    assert lv.withdrawal(1.0, W)[1] == "below", "a place not known to be in the area gets no regional line"


def test_virginia_reporting_statewide_and_the_management_areas_by_county():
    # 9VAC25-200-30: report above 10,000 gallons a day averaged over a month, statewide; 9VAC25-610: a permit at 300,000 gallons a month, only in a management area
    W = rules.withdrawals("VA")
    assert lv.withdrawal(0.01, W, county="51107")[1] == "below" and lv.withdrawal(0.011, W, county="51107")[1] == "report"      # Loudoun: no management area
    assert lv.withdrawal(0.011, W, source="ground", county="51810") == ("large", "gwma_permit")                                  # Virginia Beach: Eastern Virginia
    assert lv.withdrawal(0.011, W, source="ground", county="51059")[1] == "report"                                               # Fairfax: split by I-95, no line


def test_minnesota_day_and_year_lines_and_the_basin():
    # Minn. Stat. 103G.271 subd. 4(a): exempt only under 10,000 gallons a day and no more than 1,000,000 a year; 103G.265 subd. 3, 4: water used up over 30 days
    W = rules.withdrawals("MN")
    assert lv.withdrawal(0.002, W)[1] == "below" and lv.withdrawal(0.003, W)[1] == "permit_year"
    assert lv.withdrawal({"withdrawn_month": 0.003, "withdrawn_peak": 0.01, "consumed_90": 0, "consumed_peak": 0}, W)[1] == "permit"
    used = lambda c: {"withdrawn_month": 9, "withdrawn_peak": 9, "consumed_90": c, "consumed_peak": c}
    assert lv.withdrawal(used(2.1), W, basin=False)[1] == "consumptive_review" and lv.withdrawal(used(5.1), W, basin=False)[1] == "consumptive_review"
    assert lv.withdrawal(used(5.1), W, basin=True)[1] == "great_lakes_approval"


def test_new_york_capacity_long_island_and_the_basin_commissions():
    W = rules.withdrawals("NY")
    q = lambda month, peak, c=0.0: {"withdrawn_month": month, "withdrawn_peak": peak, "consumed_90": c, "consumed_peak": c}
    assert lv.withdrawal(q(0.05, 0.09), W, huc="041300", county="36029")[1] == "below"                                  # Buffalo area, under 100,000 on the peak day
    assert lv.withdrawal(q(0.05, 0.1), W, huc="041300", county="36029")[1] == "permit"                                  # ECL 15-1501: capacity, at least
    assert lv.withdrawal(q(0.05, 0.07), W, huc="020301", county="36103")[1] == "long_island"                            # ECL 15-1527: over 45 gpm
    assert lv.withdrawal(q(0.1, 0.12, 0.01), W, huc="020501", county="36007")[1] == "srbc_withdrawal"                   # 18 CFR 806.4: SRBC wins over DEC's permit
    assert lv.withdrawal(q(0.05, 0.05, 0.02), W, huc="020501", county="36007")[1] == "srbc_consumptive"
    assert lv.withdrawal(q(0.11, 0.12), W, huc="020401", county="36025")[1] == "drbc_review"


def test_states_with_no_numeric_line_or_no_flag():
    # Texas: districts set their own rules, so the reader sees the summary and no level
    assert "lines" not in rules.withdrawals("TX") and "districts" in rules.withdrawals("TX")["no_line"]
    # Arizona: 35 gallons a minute is the exempt-well size; the AMA rule is in the summary, with no flag
    W = rules.withdrawals("AZ")
    assert lv.withdrawal(0.05, W)[1] == "below" and lv.withdrawal(0.051, W) == ("mid", "nonexempt") and lv.permit_flag("nonexempt", W) is None
    # Illinois: notice to the district at 100,000 gallons in any 24 hours, no permit
    W = rules.withdrawals("IL")
    assert lv.withdrawal(0.1, W, source="ground") == ("mid", "notice") and lv.permit_flag("notice", W) is None


def test_pennsylvania_registration_commissions_and_lake_erie():
    W = rules.withdrawals("PA")
    q = lambda month, c=0.0: {"withdrawn_month": month, "withdrawn_peak": month, "consumed_90": c, "consumed_peak": c}
    assert lv.withdrawal(q(0.011), W, huc="050100")[1] == "register"                                  # Ohio River basin: registration only
    assert lv.withdrawal(q(0.011, 0.02), W, huc="020501")[1] == "srbc_consumptive"                     # 18 CFR 806.4(a)(1)
    assert lv.withdrawal(q(0.1, 0.01), W, huc="020503")[1] == "srbc_withdrawal"
    assert lv.withdrawal(q(0.1), W, huc="020402")[1] == "register" and lv.withdrawal(q(0.11), W, huc="020402")[1] == "drbc_review"
    assert lv.withdrawal(q(0.1), W, basin=True, huc="041201")[1] == "great_lakes_review"
