"""Rainfall for every county and independent city: a city NOAA has no record for takes its surrounding county's, and says so; anything else missing is an error."""
import urllib.error

import geopandas as gpd
import pytest
from shapely.geometry import Point

from waterledger.national import climate as nc
from waterledger_data import divisions


def places():
    # a county around a city, and a neighbor it barely touches
    county = Point(-79.5, 37.8).buffer(0.2)
    return gpd.GeoDataFrame({"geoid": ["51163", "51530", "5145512"], "base": ["Rockbridge", "Far", "Lexington"], "level": ["county", "county", "place"],
                             "county_fips": ["51163", "51530", "51678"]},
                            geometry=[county.difference(Point(-79.45, 37.8).buffer(0.02)), Point(-79.0, 37.8).buffer(0.25), Point(-79.45, 37.8).buffer(0.02)], crs=4326)


AREAS = [{"geoid": g} for g in ("51163", "51530", "51678")]


def test_a_city_without_a_record_takes_its_surrounding_county():
    rain, used = nc.fill_rain({"51163": 44.79, "51530": 40.0}, places(), AREAS)
    assert rain["51678"] == 44.79 and used == {"51678": "Rockbridge"}


def test_nothing_borrowed_when_noaa_has_the_city():
    rain, used = nc.fill_rain({"51163": 44.79, "51530": 40.0, "51678": 45.0}, places(), AREAS)
    assert rain["51678"] == 45.0 and used == {}


def test_a_county_without_a_record_is_an_error():
    with pytest.raises(RuntimeError, match="county 51530"):
        nc.fill_rain({"51163": 44.79}, places(), AREAS)


def test_a_city_whose_county_has_no_record_is_an_error():
    with pytest.raises(RuntimeError, match="51678"):
        nc.fill_rain({"51530": 40.0}, places(), [{"geoid": "51530"}, {"geoid": "51678"}])


@pytest.mark.parametrize("code,raises", [(404, False), (500, True), (429, True)])
def test_only_no_such_record_leaves_a_county_out(monkeypatch, code, raises):
    def fail(url):
        raise urllib.error.HTTPError(url, code, "x", {}, None)
    monkeypatch.setattr(divisions, "cag_json", fail)
    monkeypatch.setattr(divisions, "_cached", lambda name, fn: fn())
    C = [{"geoid": "51678", "lat": 37.8, "lon": -79.4}]
    if raises:
        with pytest.raises(urllib.error.HTTPError):
            divisions.rain_in("VA", C)
    else:
        assert divisions.rain_in("VA", C) == {}
