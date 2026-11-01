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


def _sys(n, pop, share):
    return WaterSystem(pwsid=n, name=n, population=pop, connections=100, share_of_place=share)


def test_main_system_covers_most_of_the_place_even_if_a_neighbor_is_bigger():
    assert cm.water_system_share(R, [_sys("Columbus", 900000, 0.008), _sys("Westerville", 40000, 0.997)]).name == "Westerville"


def test_main_system_largest_share_when_two_cover_half():       # service areas can overlap
    assert cm.main_system([_sys("a", 10, 0.6), _sys("b", 1000, 0.5), _sys("c", 5000, 0.2)]).name == "a"


def test_main_system_by_population_among_those_covering_5_percent():
    assert cm.main_system([_sys("Four Way", 5000, 0.3), _sys("Lufkin", 35000, 0.06), _sys("Far", 900000, 0.04)]).name == "Lufkin"


def test_main_system_by_population_when_none_covers_5_percent():
    assert cm.main_system([_sys("a", 500, 0.04), _sys("b", 90, 0.049), _sys("c", 900, None)]).name == "c"


def test_main_system_first_on_a_tie_and_none_with_none():
    assert cm.main_system([_sys("a", 500, 0.2), _sys("b", 500, 0.3)]).name == "a"
    assert cm.main_system([_sys("a", 500, 0.7), _sys("b", 900, 0.7)]).name == "a"
    assert cm.main_system([]) is None


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


def test_a_peak_below_the_average_load_counts_as_missing():
    from waterledger_data.power import usable_peak
    assert usable_peak(914.0, 2252 * 8760) is None
    assert usable_peak(2252.0, 2252 * 8760) == 2252.0
    assert usable_peak(None, 2252 * 8760) is None
