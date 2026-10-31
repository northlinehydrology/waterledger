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
