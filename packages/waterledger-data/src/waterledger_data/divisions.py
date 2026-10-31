"""Climate for any state (national tier, design 0002 decision 4): NOAA climate divisions, one long-record NOAA ISD station to
represent each, county rainfall normals and NOAA Atlas 14 design storms. Cached under <cache>/climate/.

  divisions      NOAA's county-to-climate-division table (each county in the division holding its centroid)
  station        for each division, the ISD station with at least 85% of hours observed over 1995-2024 that is
                 nearest the center of the division's counties (searching up to MAX_KM)
  rain_in        county mean annual precipitation, 1991-2020 (NOAA Climate at a Glance, nClimGrid)
  design_storms  NOAA Atlas 14 24-hour depths (2-, 10-, 100-year) at each county's internal point
"""
import json, math, os, time, urllib.error, urllib.request

from tqdm.auto import tqdm

from waterledger_data import climate
from waterledger_data.config import CACHE

RAW = os.path.join(CACHE, "climate")
COUNTY_DIVS = "https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/county-to-climdivs.txt"
CAG = "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/time-series/{st}-{county}/pcp/12/12/1991-2020/data.json"
MAX_KM = 150
FIRST, LAST = 1995, 2024


def _cached(name, fn):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        json.dump(fn(), open(path, "w"))
    return json.load(open(path))


def county_divisions():
    """{county FIPS: climate division id}, e.g. {"39049": "3305"} (NOAA's state code + division number)."""
    def fetch():
        req = urllib.request.Request(COUNTY_DIVS, headers={"User-Agent": "waterledger"})
        text = urllib.request.urlopen(req, timeout=120).read().decode()
        out = {}
        for ln in text.splitlines():
            p = ln.split()
            if len(p) == 3 and p[0].isdigit() and len(p[0]) == 5:
                out[p[0]] = p[2]
        return out
    return _cached("county_to_climdiv.json", fetch)


def _km(a_lat, a_lon, b_lat, b_lon):
    dlat, dlon = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def division_stations(state_fips, counties):
    """{division id: {id, name, lat, lon, km, share_observed, counties}} for a state's divisions. `counties` is
    [{geoid, lat, lon}] (the county rows of census.places)."""
    def fetch():
        divs = {}
        cd = county_divisions()
        for c in counties:
            d = cd.get(c["geoid"])
            if d:
                divs.setdefault(d, []).append(c)
        stations = climate.isd_stations(FIRST, LAST)
        out = {}
        for d, cs in tqdm(sorted(divs.items()), desc=f"{state_fips} stations", unit="division", disable=None):
            lat = sum(c["lat"] for c in cs) / len(cs)
            lon = sum(c["lon"] for c in cs) / len(cs)
            near = sorted((_km(lat, lon, s["lat"], s["lon"]), s) for s in stations)
            for km, s in near:
                if km > MAX_KM:
                    break
                got = climate.isd_hourly(s, FIRST, LAST)
                if got:
                    out[d] = {**s, "km": round(km, 1), "share_observed": round(got[3], 3), "counties": sorted(c["geoid"] for c in cs),
                              "center": [round(lat, 4), round(lon, 4)]}
                    break
        return out
    return _cached(f"{state_fips}_division_stations.json", fetch)


def cag_json(url, tries=6, wait=30):
    """A Climate at a Glance file. NOAA answers 429 when asked too quickly, so wait and ask again."""
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "waterledger"}), timeout=120))
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(wait * (i + 1))


def rain_in(state, counties):
    """{county FIPS: mean annual precipitation 1991-2020, inches}."""
    def fetch():
        out = {}
        for c in tqdm(counties, desc=f"{state} rainfall", unit="county", disable=None):
            url = CAG.format(st=state, county=c["geoid"][2:])
            try:
                d = cag_json(url)
                v = [x["value"] for x in d["data"].values()]
                out[c["geoid"]] = round(sum(v) / len(v), 2)
            except urllib.error.HTTPError as e:
                if e.code == 429:                  # still refused: a county must not go missing because NOAA was busy
                    raise
            except Exception:
                continue
        return out
    return _cached(f"{state}_county_rain.json", fetch)


def design_storms(counties):
    """{county FIPS: {"2", "10", "100": 24-hour depth, inches}} from NOAA Atlas 14 at each county's internal point."""
    out = {}
    for c in tqdm(counties, desc="design storms", unit="county", disable=None):
        try:
            pf, meta = climate.atlas14_depths(c["lat"], c["lon"], f"county_{c['geoid']}")
        except Exception:
            continue                      # outside Atlas 14 (older NOAA studies, when needed: design 0002 decision 5)
        out[c["geoid"]] = {str(k): pf["24-hr"][k] for k in (2, 10, 100)}
    return out
