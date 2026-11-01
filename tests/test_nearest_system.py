"""The nearest sizable water system, one rule in every state, with distances worked by hand."""
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from waterledger import scenario as sc
from waterledger_data import supply


def _systems(monkeypatch, *rows):
    g = gpd.GeoDataFrame([dict(zip(("pwsid", "name", "population", "connections", "geometry"), r)) for r in rows], geometry="geometry", crs=supply.ALBERS).to_crs(4326)
    monkeypatch.setattr(supply, "water_systems", lambda state: g)


def test_point_to_edge_and_size(monkeypatch):
    """Service areas in meters, from a place at their origin: a large system whose edge is 8 km east and whose middle is 58 km east; a small one 1 km away, which doesn't count."""
    _systems(monkeypatch, ("BIG", "Big", 50000, 15000, box(8000, -50000, 108000, 50000)), ("TINY", "Tiny", 3300, 900, box(1000, -500, 2000, 500)), ("FAR", "Far", 9000, 3000, box(20000, -500, 21000, 500)))
    origin = gpd.GeoSeries(gpd.points_from_xy([0], [0]), crs=supply.ALBERS).to_crs(4326)
    points = pd.DataFrame({"geoid": ["p"], "lat": origin.y, "lon": origin.x})
    w, km = supply.nearest_sizable("XX", points)["p"]
    assert w["pwsid"] == "BIG" and km == pytest.approx(8.0, abs=0.05)      # to the edge, not the middle; 3,300 is not over the 3,300 line


def test_inside_a_service_area_is_zero(monkeypatch):
    _systems(monkeypatch, ("BIG", "Big", 50000, 15000, box(-1000, -1000, 1000, 1000)))
    origin = gpd.GeoSeries(gpd.points_from_xy([0], [0]), crs=supply.ALBERS).to_crs(4326)
    assert supply.nearest_sizable("XX", pd.DataFrame({"geoid": ["p"], "lat": origin.y, "lon": origin.x}))["p"][1] == 0.0


def test_no_sizable_system_at_all(monkeypatch):
    _systems(monkeypatch, ("TINY", "Tiny", 100, 30, box(0, 0, 10, 10)))
    assert supply.nearest_sizable("XX", pd.DataFrame({"geoid": ["p"], "lat": [40.0], "lon": [-90.0]})) == {}


def test_michigan_reads_the_stored_nearest_system():
    w = {"pwsid": "MI1", "name": "A", "pop": 9000, "connections": 3000, "km": 6.2}
    assert sc.near_system({"g": "1", "near": w})["km"] == 6.2 and sc.near_system({"g": "1", "near": w})["w"]["pwsid"] == "MI1"
    assert sc.near_system({"g": "1", "near": None}) is None


def test_reach_is_the_same_line_as_everywhere(monkeypatch):
    p = {"g": "1", "w": [], "near": {"pwsid": "MI1", "name": "A", "pop": 9000, "connections": 3000, "km": 10.0}}
    assert sc.src_for(p, "dry") == {"src": "muni", "near": sc.near_system(p), "reach": True} and sc.src_for(p, "towers")["src"] == "wells"
    far = {**p, "near": {**p["near"], "km": 10.1}}
    assert sc.src_for(far, "dry")["src"] == "wells"


def test_a_sliver_of_a_system_is_not_a_system_there():
    from waterledger.national.provider import serves
    assert serves([{"share": 0.05}]) and serves([{"share": 0.01}, {"share": 0.7}])
    assert not serves([{"share": 0.049}]) and not serves([]) and not serves([{"share": None}])
