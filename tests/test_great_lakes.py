"""The Great Lakes check and lake-source rules in any state, with geometry and water worked by hand."""


import geopandas as gpd
import pytest
from shapely.geometry import box

from waterledger import scenario as sc
from waterledger_data import greatlakes
from waterledger_models.datacenter import lake as lc

# In meters in the equal-area projection: a lake 100 km across with a second one 12 km to its east, and places around them
LAKES = gpd.GeoDataFrame({"name": ["Lake Erie", "Lake Ontario"], "geometry": [box(0, 0, 100000, 100000), box(112000, 0, 200000, 100000)]}, crs=greatlakes.ALBERS)


def _places(**boxes):
    return gpd.GeoDataFrame({"geoid": list(boxes), "geometry": list(boxes.values())}, crs=greatlakes.ALBERS)


def test_distance_is_polygon_to_polygon():
    n = greatlakes.near(_places(touching=box(100000, 40000, 103000, 43000), off_shore=box(-5000, 20000, -3000, 22000),    # 3 km from the lake's edge
                                edge=box(-7000, 20000, -5000, 22000), past=box(-7100, 40000, -5100, 42000)), LAKES)      # 5 km exactly; 5.1 km
    assert n["touching"] == {"lake": "Lake Erie", "km": 0.0} and n["off_shore"] == {"lake": "Lake Erie", "km": 3.0} and n["edge"]["km"] == 5.0 and "past" not in n


def test_between_two_lakes_the_nearer_one():
    n = greatlakes.near(_places(between=box(103000, 50000, 108000, 52000)), LAKES)     # 3 km from Erie, 4 km from Ontario
    assert n["between"] == {"lake": "Lake Erie", "km": 3.0}


def test_a_place_far_from_either_is_not_on_a_lake():
    assert greatlakes.near(_places(inland=box(-90000, 0, -80000, 10000)), LAKES) == {}


@pytest.mark.parametrize("name,src,cool", [("Phoenix", "lake", "towers"), ("Phoenix", None, "lake"), ("Phoenix", "lake", "lake")])
def test_lake_water_needs_a_great_lake_in_any_state(name, src, cool):
    with pytest.raises(ValueError, match="not within about 5 km of a Great Lake"):
        sc.check_lake(name, None, cool, src)


def test_lake_source_cooling_needs_the_lake_as_its_source():
    with pytest.raises(ValueError, match="needs lake surface water"):
        sc.check_lake("Cleveland", "Lake Erie", "lake", "muni")
    sc.check_lake("Cleveland", "Lake Erie", "lake", "lake")
    sc.check_lake("Cleveland", "Lake Erie", "towers", "lake")
    sc.check_lake("Columbus", None, "towers", "wells")


def test_no_michigan_in_the_error():
    with pytest.raises(ValueError) as e:
        sc.check_lake("Phoenix", None, "lake", None)
    assert "Michigan" not in str(e.value)


def _temperatures():
    import pandas as pd
    rows = [{"lake": code, "dayOfYear": d, "temperature": t} for code, t in (("o", 8.0), ("e", 12.0)) for d in range(1, 367)]
    return pd.DataFrame(rows)


def test_lake_ontario_has_results_and_st_clair_uses_erie():
    from waterledger.national.climate import lake_results
    R = lake_results(["Lake Ontario", "Lake Erie", "Lake St. Clair"], _temperatures(), n=20)
    assert R["Lake St. Clair"] == R["Lake Erie"] and R["Lake Ontario"]["evap_avg"]["p50"] != R["Lake Erie"]["evap_avg"]["p50"] and "Lake St. Clair" in R["note"]
    assert R["power"]["pue_avg"] == R["Lake Ontario"]["pue_avg"]             # the same draws at every lake


def test_a_lake_estimate_closes_and_scales():
    """Withdrawn = returned for once-through, 100 MW of water through the exchangers by hand at middle values: 100e6 W x 0.65 x 1.11 / (1000 x 4186 x 8) m3/s = 2.154 m3/s = 49.2 MGD."""
    assert lc.withdrawal_m3s(100, 0.65, 1.11, 8) * 86400 * lc.GAL_M3 / 1e6 == pytest.approx(49.2, abs=0.1)
    L = {"withdrawn": {"p10": 40.0, "p50": 50.0, "p90": 60.0}, "evap_avg": {"p10": .4, "p50": .5, "p90": .6}, "evap_peak_month": {"p10": .5, "p50": .6, "p90": .7}}
    stat = {k: {"p10": 0.0, "p50": 0.0, "p90": 0.0} for k in ("withdrawn_avg", "withdrawn_peak_1in10", "withdrawn_annual_mg", "consumed_avg", "consumed_peak_1in10", "returned_avg", "returned_peak_1in10")}
    D = {"lake_source": {"Lake Erie": L}, "regions": {"r": {"per_100mw": {"dry": stat}}}, "staff": {"runs": _staff()}}
    E = sc.lake_estimate(D, "Lake Erie", "r", 200, "sewer")
    assert E["lake"] and E["wAvg"]["mid"] == 100.0 and E["rAvg"] == E["wAvg"] and E["cAvg"]["mid"] == 1.0 and E["wAnn"]["mid"] == pytest.approx(100.0 * 365.25)


def _staff():
    from waterledger_models.datacenter import cooling as cw
    return cw.staff_runs(10)


