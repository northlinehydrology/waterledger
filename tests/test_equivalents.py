"""est.equivalents and est.power_plants: an estimate in homes and golf courses, and its water at power plants. Full values; the page mirrors them (WQ.*)."""
from types import SimpleNamespace

import pytest

import waterledger as wl
from waterledger import comparisons as cm
from waterledger.estimate import Electricity

R = lambda a, b, c: wl.Range(p10=a, p50=b, p90=c)
F = lambda a, b, c: wl.Flow(avg=R(a, b, c), peak_day=R(a * 10, b * 10, c * 10))
POWER = Electricity(avg_mw=R(300, 400, 500), peak_mw=R(500, 600, 700), pue=R(1.1, 1.2, 1.3), peak_pue=R(1.2, 1.3, 1.4))
REF = {"golf_gpd": 40000, "home_kwh_month": 730, "home_customers": 1000000}
OPTIONS = {"mix": {"label": "Mix", "gal_mwh": 200, "lo": 100, "hi": 300, "wd_gal_mwh": 5000, "wd_lo": 4000, "wd_hi": 6000, "sources": ["x"]}}


def water(lake=False):
    return SimpleNamespace(lake_source=lake, withdrawn=F(0.1, 0.2, 0.3), consumed=F(0.05, 0.15, 0.25))


def test_the_arithmetic():
    assert cm.water_homes(0.3) == pytest.approx(1000)
    assert cm.golf_courses(0.08, 40000) == pytest.approx(2)
    assert cm.electricity_homes(1, 730) == pytest.approx(1000)      # 730 kWh a month is 1 kW around the clock
    assert cm.share_of_customers(1000, 1000000) == pytest.approx(0.1)
    assert cm.plant_water(100, 500) == pytest.approx(1.2)
    assert cm.evaporated_share(0.15, 0.2) == pytest.approx(75)


def test_equivalents_count_water_taken():
    q = cm.equivalents(SimpleNamespace(water=water(), electricity=POWER), REF)
    assert q.homes.p50 == pytest.approx(0.2e6 / 300) and q.homes_peak_day.p50 == pytest.approx(2e6 / 300)
    assert q.golf_courses.p50 == pytest.approx(5) and q.golf_course_gpd == 40000
    assert q.evaporated_share == pytest.approx(75)
    assert q.electricity_homes.p50 == pytest.approx(400000) and q.electricity_homes_peak.p50 == pytest.approx(600000)
    assert q.share_of_home_customers.p50 == pytest.approx(40)


def test_lake_source_counts_what_the_lake_loses():
    q = cm.equivalents(SimpleNamespace(water=water(lake=True), electricity=POWER), REF)
    assert q.homes.p50 == pytest.approx(0.15e6 / 300) and q.golf_courses.p50 == pytest.approx(3.75)


def test_a_value_the_state_lacks_is_none_not_zero():
    q = cm.equivalents(SimpleNamespace(water=water(), electricity=POWER), {"golf_gpd": None, "home_kwh_month": None, "home_customers": None})
    assert q.golf_courses is None and q.electricity_homes is None and q.electricity_homes_peak is None and q.share_of_home_customers is None
    assert cm.equivalents(SimpleNamespace(water=water(), electricity=POWER), {**REF, "home_customers": None}).share_of_home_customers is None
    assert cm.equivalents(SimpleNamespace(water=water(), electricity=None), REF).electricity_homes is None


def test_plant_water_pairs_each_end_of_the_range():
    p = cm.plant_waters(POWER, OPTIONS)["mix"]
    assert p.consumed.p10 == pytest.approx(300 * 24 * 100 / 1e6) and p.consumed.p50 == pytest.approx(400 * 24 * 200 / 1e6) and p.consumed.p90 == pytest.approx(500 * 24 * 300 / 1e6)
    assert p.withdrawn.p50 == pytest.approx(48.0) and p.returned == pytest.approx(48.0 - 1.92)
    assert p.sources == ["x"]


def test_returned_is_never_below_zero():
    o = {"w": {**OPTIONS["mix"], "gal_mwh": 500, "wd_gal_mwh": 100}}
    assert cm.plant_waters(POWER, o)["w"].returned == 0


@pytest.mark.live
def test_a_michigan_site_reports_them():
    est = wl.Site(place=wl.place("Gaines charter township, MI"), facility=wl.DataCenter(it_mw=300, cooling="hybrid")).estimate()
    assert est.site.power == "mi_mix" and est.equivalents.homes.p50 == pytest.approx(est.water.withdrawn.avg.p50 * 1e6 / 300)
    assert est.power_plants["mi_mix"].consumed.p50 == pytest.approx(est.electricity.avg_mw.p50 * 24 * 268 / 1e6)
    with pytest.raises(ValueError, match="power must be one of"):
        wl.Site(place=wl.place("Gaines charter township, MI"), facility=wl.DataCenter(it_mw=300, cooling="hybrid"), power="nope").estimate()


def test_utility_shares_leave_out_a_utility_with_no_sales():
    from waterledger.context import Utility
    U = lambda n, a, s=None: Utility(name=n, type="", share_of_place=0.5, avg_mw=a, summer_peak_mw=s)
    c = cm.utility_shares(POWER, [U("wires", None), U("nothing sold", 0), U("A", 1000, 2000), U("B", 800)], 10000)
    assert [x.name for x in c] == ["A", "B", "State"]
    assert c[0].percent.avg.p50 == pytest.approx(40) and c[0].percent.peak_day.p50 == pytest.approx(30)
    assert c[1].percent.peak_day is None and c[2].percent.avg.p50 == pytest.approx(4)


def test_county_share_falls_back_on_all_withdrawals():
    w = wl.Flow(avg=R(1, 2, 3), peak_day=R(1, 2, 3))
    assert cm.county_share(w, {"Public water systems": 100, "All reported withdrawals": 400}).measure == "public_water"
    assert cm.county_share(w, {"public_supply": 100}).percent.avg.p50 == pytest.approx(2)
    c = cm.county_share(w, {"All reported withdrawals": 400})
    assert c.measure == "all_withdrawals" and c.percent.avg.p50 == pytest.approx(0.5)
    assert cm.county_share(w, {"Livestock": 3}) is None


def _plant(design, flow):
    from waterledger.context import SewerPlant
    return SewerPlant(npdes="x", name="P", design_mgd=design, flow_mgd=flow, km=1)


def test_sewer_shares():
    w = SimpleNamespace(to_sewer=R(0.5, 1, 2), returned=wl.Flow(avg=R(0.5, 1, 2), peak_day=R(1, 2, 4)), lake_source=False)
    a, b = cm.sewer_shares(w, _plant(14, 10))
    assert a.against == "sewer_plant" and a.percent.avg.p50 == pytest.approx(10)
    assert b.against == "sewer_spare_room" and b.existing == 4 and b.percent.avg.p50 == pytest.approx(25) and b.percent.peak_day.p50 == pytest.approx(50)
    assert [c.against for c in cm.sewer_shares(w, _plant(10, 10))] == ["sewer_plant"]      # no spare room to compare with
    assert cm.sewer_shares(w, _plant(10, None)) == [] and cm.sewer_room(_plant(10, None)) is None


def test_before_after_rows_follow_the_water():
    W = R(0.4, 0.5, 0.6)
    args = (W, R(1, 1.5, 2), R(0.2, 0.3, 0.4), R(0.1, 0.2, 0.3), 200, 34, "farm", 0.5, 300)
    keys = lambda rows: [r.key for r in rows]
    a = cm.before_after("muni", "sewer", *args, R(200, 210, 220), 100, _plant(14, 10))
    assert keys(a) == ["water", "used", "sewer", "runoff", "mud", "build", "p", "salt", "fuel", "power"]
    assert a[0].today == 100 and a[0].percent == pytest.approx(0.5) and a[2].percent == pytest.approx(2)
    assert keys(cm.before_after("wells", "septic", *args))[:3] == ["water", "used", "wastewater"]
    assert "sewer" not in keys(cm.before_after("muni", "sewer", *args, reuse=True))
    assert cm.before_after("wells", "water", *args, county_public=100)[0].today is None      # the county's public water is not what wells draw on


OPTS = {"mix": {"label": "Mix", "gal_mwh": 200, "lo": 200, "hi": 200}, "grid": {"label": "PJM grid average", "gal_mwh": 900, "lo": 900, "hi": 900}, "coal": {"label": "Coal", "gal_mwh": 500, "lo": 500, "hi": 500},
        "gas": {"label": "Gas", "gal_mwh": 500, "lo": 500, "hi": 500}, "renew": {"label": "Wind and solar", "gal_mwh": 1, "lo": 1, "hi": 1}}


def test_offered_and_thirstiest_power():
    assert cm.offered_power(OPTS, "mix") == ["mix", "coal", "gas", "renew"]               # a state with its own mix keeps grid averages for comparison
    assert cm.offered_power(OPTS, "grid") == list(OPTS)
    assert cm.thirstiest_power(OPTS, "mix") == "coal"                                     # the first of a tie
    assert cm.thirstiest_power({"mix": OPTS["mix"], "renew": OPTS["renew"]}, "mix") is None


def _design(c, mw, peak):
    return (SimpleNamespace(consumed=SimpleNamespace(avg=R(c, c, c))), Electricity(avg_mw=R(mw, mw, mw), peak_mw=R(peak, peak, peak), pue=R(1, 1, 1), peak_pue=R(1, 1, 1)))


def test_compare_designs():
    d = cm.compare_designs({"dry": _design(0.01, 110, 150), "towers": _design(1.0, 100, 120)}, OPTS, "mix", "mix")
    assert d.best == "dry" and d.designs["dry"].total == pytest.approx(0.01 + 110 * 24 * 200 / 1e6)
    assert d.closed_loop_more_power_pct == pytest.approx(10) and d.closed_loop_more_peak_mw == 30 and d.closed_loop_saves_on_site == pytest.approx(0.99)
    d = cm.compare_designs({"dry": _design(0.01, 300, 400), "towers": _design(0.02, 100, 120)}, OPTS, "gas", "mix")
    assert d.best == "towers"     # on a thirsty supply, closed loop's extra power can cost more water than the towers evaporate
    assert cm.compare_designs({"towers": _design(1, 100, 120)}, OPTS, "mix", "mix").closed_loop_more_peak_mw is None


def test_contract_to_computing():
    assert cm.it_mw_from_contract(1400, 1.289) == pytest.approx(1086.1, abs=0.1)


def test_default_power_follows_the_largest_utility_only_without_a_state_mix():
    U = lambda s, ba: SimpleNamespace(share_of_place=s, balancing_authority=ba)
    O = {"mix": {"label": "Mix"}, "pjm": {"label": "PJM grid average"}, "miso": {"label": "MISO grid average"}}
    assert cm.default_power(O, "mix", [U(1, "PJM")]) == "mix"
    assert cm.default_power(O, "pjm", [U(0.2, "PJM"), U(0.8, "MISO")]) == "miso"
    assert cm.default_power(O, "pjm", [U(0.9, None), U(0.1, "TVA")]) == "pjm" and cm.default_power(O, "pjm", []) == "pjm"     # TVA is not an option here


def test_wells_summary():
    assert cm.wells_summary(None) is None and cm.wells_summary({"drift_n": 5, "rock_n": 4}) is None
    s = cm.wells_summary({"drift_n": 30, "drift_depth_ft": 88, "drift_level_ft": 21, "rock_n": 10, "rock_depth_ft": 200, "rock_level_ft": 40})
    assert (s.wells, s.main, s.depth_ft, s.water_level_ft, s.other_share) == (40, "drift", 88, 21, 25)
    assert cm.wells_summary({"drift_n": 3, "rock_n": 20, "rock_depth_ft": 200, "rock_level_ft": 0}).water_level_ft is None


def test_listed_leaves_out_what_runoff_does_not_add_to():
    from waterledger_models import runoff as rq
    assert [x[0] for x in rq.listed([["sed", 1, []], ["ecoli", 0, []], ["fish", 0, []], ["nut", 0, []]])] == ["sed", "nut"]
    assert rq.listed(None) == []
