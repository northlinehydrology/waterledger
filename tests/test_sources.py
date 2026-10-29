"""Every public source the data package reads still answers (nightly; `pytest -m live`). Small requests only, using the same
addresses the modules use, so a moved or broken service shows up here before a state build needs it."""
import gzip, io, json, urllib.parse, urllib.request

import pytest

from waterledger_data import climate, places, power, waters

pytestmark = pytest.mark.live
UA = {"User-Agent": "waterledger-nightly (+https://github.com/northlinehydrology/waterledger)"}


def get(url, params=None, nbytes=None):
    q = url + ("?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=90) as r:
        assert r.status == 200, q
        return r.read(nbytes) if nbytes else r.read()


def arcgis_count(url, where="1=1"):
    d = json.loads(get(url, {"where": where, "returnCountOnly": "true", "f": "json"}))
    assert "error" not in d, d
    return d["count"]


def test_census_tigerweb_counties():
    assert arcgis_count(f"{places.TIGER}/State_County/MapServer/1/query", "STATE='26'") == 83


def test_epa_water_system_boundaries():
    assert arcgis_count(places.EPA_SA, "1=1") > 40000


def test_usgs_watershed_boundaries():
    assert arcgis_count(waters.WBD6, "huc12 LIKE '040500%'") > 100


def test_epa_attains():
    assert arcgis_count(f"{waters.ATTAINS}/1/query", "state='MI'") > 1000


def test_epa_echo():
    d = json.loads(get(f"{waters.ECHO}.get_facilities", {"output": "JSON", "p_st": "MI", "p_pcomp": "POT", "responseset": "1"}))
    assert int(d["Results"]["QueryRows"]) > 100


def test_epa_cwns_compilation():
    assert get(waters.CWNS, nbytes=100)


def test_noaa_atlas14():
    txt = get("https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py",
              {"lat": "42.88", "lon": "-85.52", "type": "pf", "data": "depth", "units": "english", "series": "pds"}).decode()
    assert "quantiles" in txt


def test_noaa_isd_station_list_and_file():
    assert get(climate.ISD_HISTORY, nbytes=200).startswith(b'"USAF"')
    raw = gzip.GzipFile(fileobj=io.BytesIO(get(climate.ISD_LITE.format(y=2024, usaf="726350", wban="94860")))).read()
    assert raw.count(b"\n") > 8000


def test_open_meteo_archive():
    d = json.loads(get("https://archive-api.open-meteo.com/v1/archive",
                       {"latitude": 42.88, "longitude": -85.52, "start_date": "2024-07-01", "end_date": "2024-07-02",
                        "hourly": "temperature_2m,relative_humidity_2m"}))
    assert len(d["hourly"]["temperature_2m"]) == 48


def test_nasa_power_hourly():
    d = json.loads(get(climate.POWER_HOURLY, {"parameters": "T2M", "community": "RE", "longitude": -85.52, "latitude": 42.88,
                                              "start": "20240701", "end": "20240701", "format": "JSON"}))
    assert len(d["properties"]["parameter"]["T2M"]) == 24


def test_eia_861():
    req = urllib.request.Request(power.EIA861.format(year=2024), headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=90) as r:
        assert r.status == 200


@pytest.mark.parametrize("url", [power.MPSC, waters.TROUT, waters.WELLOGIC], ids=["mpsc_territories", "mdnr_trout", "egle_wellogic"])
def test_michigan_layers(url):
    assert arcgis_count(url) > 0
