"""est.comparisons: the campus against what is already there, the same calculation waterledger.org makes (WQ.systemPercent)."""
import json

import waterledger as wl
from waterledger import comparisons as cm
from waterledger.context import WaterSystem

R = wl.Flow(avg=wl.Range(p10=0.03, p50=0.06, p90=0.12), peak_day=wl.Range(p10=0.5, p50=1.0, p90=2.0))


def test_share_is_homes_against_connections():
    c = cm.water_system_share(R, [WaterSystem(pwsid="A", name="A", population=1000, connections=2000)])
    assert c.percent.avg.p50 == 100 * (0.06e6 / 300) / 2000 and c.percent.avg.p10 < c.percent.avg.p50 < c.percent.avg.p90
    assert c.percent.peak_day.p50 == 100 * (1.0e6 / 300) / 2000
    assert (c.against, c.measure, c.existing, c.unit) == ("water_system", "homes_vs_connections", 2000, "connections")


def test_largest_system_by_population_first_on_a_tie():
    a, b, d = (WaterSystem(pwsid=x, name=x, population=p, connections=10) for x, p in (("a", 5), ("b", 9), ("d", 9)))
    assert cm.water_system_share(R, [a, b, d]).name == "b"


def test_left_out_with_no_system_or_no_connections():
    assert cm.water_system_share(R, []) is None
    assert cm.water_system_share(R, [WaterSystem(pwsid="A", name="A", population=10, connections=None)]) is None
    assert cm.water_system_share(R, [WaterSystem(pwsid="A", name="A", population=10, connections=0)]) is None


def test_on_an_estimate_and_through_json():
    p = wl.place("Gaines charter township, MI")
    est = wl.Site(place=p, facility=wl.DataCenter(it_mw=300, cooling="hybrid")).estimate()
    c = est.comparisons[0]
    s = p.context().supply.systems[0]
    assert c.name == s.name and c.existing == s.connections
    assert c.percent.avg.p50 == 100 * (est.water.withdrawn.avg.p50 * 1e6 / cm.HOUSEHOLD_GPD) / s.connections
    assert c.percent.peak_day.p90 == 100 * (est.water.withdrawn.peak_day.p90 * 1e6 / cm.HOUSEHOLD_GPD) / s.connections
    assert json.loads(est.model_dump_json())["comparisons"][0]["measure"] == "homes_vs_connections"


def test_none_when_the_campus_takes_nothing_from_the_system():
    p = wl.place("Gaines charter township, MI")
    assert wl.Site(place=p, facility=wl.DataCenter(it_mw=300, cooling="hybrid"), source="wells").estimate().comparisons[0].against != "water_system"
