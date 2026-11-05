"""The national tier's cooling results: the cooling Monte Carlo run on each climate division's NOAA station record (design
0002 decision 4), in the same per-100 MW form as Michigan's eight regions, cached per state and model version."""
import functools, json, os

from waterledger import states
from waterledger_models.datacenter.physics import DRAWS


@functools.lru_cache(maxsize=8)
def counties(state):
    from waterledger_data import census
    pl = census.places(next(f for f, s in states.FIPS.items() if s == state))
    return [{"geoid": r.geoid, "lat": float(r.lat), "lon": float(r.lon)} for r in pl[pl.level == "county"].itertuples()]


def climate_areas(state):
    """The areas NOAA reports rainfall and storms for: every county, and the independent cities (Virginia's, Baltimore,
    St. Louis, Carson City), which are county equivalents listed as places. A city stands at its own point."""
    from waterledger_data import census
    pl = census.places(next(f for f, s in states.FIPS.items() if s == state))
    rows = pl[pl.level == "county"]
    cities = pl[~pl.county_fips.isin(rows.geoid) & pl.county_fips.notna()].drop_duplicates("county_fips")
    return ([{"geoid": r.geoid, "lat": float(r.lat), "lon": float(r.lon)} for r in rows.itertuples()]
            + [{"geoid": r.county_fips, "lat": float(r.lat), "lon": float(r.lon)} for r in cities.itertuples()])


def division_stations(state):
    """{division id: {"name", "station", "station_id", "lat", "lon", "share_observed", "screen"}}: each climate division's NOAA station,
    which model 1.8 keeps for rainfall, road salt and golf; its cooling comes from each place's ERA5 cell instead (snapshot format 3)."""
    from waterledger_data import climate, divisions
    from waterledger_data.config import CACHE
    path = os.path.join(CACHE, "climate", f"{state}_division_station_records.json")
    if os.path.exists(path):
        return json.load(open(path))
    fips = next(f for f, s in states.FIPS.items() if s == state)
    stations = divisions.division_stations(fips, counties(state))
    got = {d: climate.isd_hourly(s, divisions.FIRST, divisions.LAST) for d, s in stations.items()}
    out = {d: {"name": f"{state} climate division {int(d[2:])}", "station": s["name"], "station_id": s["id"], "lat": s["lat"], "lon": s["lon"],
               "share_observed": s["share_observed"], "screen": got[d][4]} for d, s in stations.items()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def division_runs(state, n=DRAWS):
    """{division id: {"name", "station", "lat", "lon", "per_100mw"}}, per_100mw as cooling.run_location returns it."""
    from waterledger_data import climate, divisions
    from waterledger_data.config import CACHE
    from waterledger_models import MODEL_VERSION
    from waterledger_models.datacenter import cooling as cw
    path = os.path.join(CACHE, "climate", f"{state}_runs_model{MODEL_VERSION}_n{n}.json")
    if os.path.exists(path):
        return json.load(open(path))
    fips = next(f for f, s in states.FIPS.items() if s == state)
    stations = divisions.division_stations(fips, counties(state))
    got = {d: climate.isd_hourly(s, divisions.FIRST, divisions.LAST) for d, s in stations.items()}
    runs = cw.run_locations({d: g[:3] for d, g in got.items()}, n=n, mw=100.0)
    out = {d: {"name": f"{state} climate division {int(d[2:])}", "station": s["name"], "station_id": s["id"], "lat": s["lat"], "lon": s["lon"],
               "share_observed": s["share_observed"], "screen": got[d][4], "per_100mw": runs[d]} for d, s in stations.items()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


# NOAA GLERL's daily long-term average surface temperatures have the five lakes; Lake St. Clair isn't in the series, and Lake Erie's stand in, as they do in Michigan's build.
LAKE_TEMPERATURES = {"Lake Michigan": "m", "Lake Superior": "s", "Lake Huron": "h", "Lake Erie": "e", "Lake Ontario": "o", "Lake St. Clair": "e"}


def lake_results(lakes, temperatures, n=DRAWS):
    """Lake-source cooling results by lake, with the note, ranges and power block a reader needs: lake.run_lake on each lake's temperatures. `temperatures`: GLERL's table (lake, dayOfYear, temperature)."""
    from waterledger_models.datacenter import lake as lc
    out = {}
    for name in lakes:
        out[name] = lc.run_lake(temperatures[temperatures["lake"] == LAKE_TEMPERATURES[name]].sort_values("dayOfYear")["temperature"].values, n=n)
    if "Lake St. Clair" in out:
        out["note"] = "Lake St. Clair is not in the GLERL series; Lake Erie temperatures stand in for it."
    out["ranges"] = {k: list(v) for k, v in lc.RANGES.items()}
    if lakes:
        out["power"] = {k: out[lakes[0]][k] for k in ("power_mw_avg", "power_mw_peak_1in10", "pue_avg", "pue_peak_1in10")}   # the same draws at every lake
    return out


def lake_source(lakes, n=DRAWS):
    """lake_results for the lakes on a state's shore, from GLERL's table (fetched once). Empty for a state with no shoreline."""
    if not lakes:
        return {}
    import pandas as pd

    from waterledger_data import climate
    from waterledger_data.config import CACHE
    from waterledger_models.datacenter import lake as lc
    return lake_results(lakes, pd.read_csv(climate._fetch(lc.GLERL, os.path.join(CACHE, "climate", "glerl_lt_avg_temp.csv")), skiprows=[1]), n)


def surrounding_county(pl, fips):
    """The county that surrounds an independent city: the one covering most of a narrow ring around it."""
    m = pl.to_crs(5070)                 # CONUS Albers, so areas and the 1 km ring are in meters
    city = m[m.county_fips == fips].geometry.union_all().buffer(1000)
    rows = m[m.level == "county"]
    return pl.loc[rows.geometry.intersection(city).area.idxmax()]


def fill_rain(rain, pl, areas):
    """Rainfall for every area, and {city: county name} where a county's record stands in for an independent city NOAA has none for (Lexington,
    Virginia, inside Rockbridge County). A county with no record, or a city whose county has none, is an error, not a gap."""
    rows = set(pl[pl.level == "county"].geoid)
    out, used = dict(rain), {}
    for a in areas:
        if a["geoid"] in out:
            continue
        if a["geoid"] in rows:
            raise RuntimeError(f"NOAA has no rainfall record for county {a['geoid']}")
        c = surrounding_county(pl, a["geoid"])
        if c.geoid not in rain:
            raise RuntimeError(f"NOAA has no rainfall record for {a['geoid']} or its surrounding county {c.geoid}")
        out[a["geoid"]], used[a["geoid"]] = rain[c.geoid], c.base
    return out, used


@functools.lru_cache(maxsize=8)
def _rain(state):
    from waterledger_data import census, divisions
    return fill_rain(divisions.rain_in(state, climate_areas(state)), census.places(next(f for f, s in states.FIPS.items() if s == state)), climate_areas(state))


def rain_from(state):
    """{independent city FIPS: the surrounding county's name}, where the county's record stands in for the city's."""
    return _rain(state)[1]


@functools.lru_cache(maxsize=8)
def storms_and_rain(state):
    from waterledger_data import divisions
    return divisions.design_storms(climate_areas(state)), _rain(state)[0]


MIN_PRECIP_DAYS = 183


def _median_cold_precip_days(sid, first=2005, last=2024):
    """The median whole winter's days with precipitation at 1 C or below at a station (NOAA ISD-Lite). A station's missing years are skipped."""
    import gzip
    import urllib.error

    from waterledger_data import climate
    usaf, wban = sid.split("-")
    days, reported = {}, {}
    for y in range(first, last + 1):
        path = os.path.join(climate.RAW, "isd", "lite", f"{sid}-{y}.gz")
        try:
            climate._fetch(climate.ISD_LITE.format(y=y, usaf=usaf, wban=wban), path, tries=3, wait=20)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
        with gzip.open(path, "rt") as f:
            for ln in f:
                p = ln.split()
                t, pr, m = int(p[4]), int(p[10]), int(p[1])
                w = y + (m >= 7)
                if pr != -9999:
                    reported.setdefault(w, set()).add((y, m, p[2]))
                if t != -9999 and t <= 10 and (pr > 0 or pr == -1):
                    days.setdefault(w, set()).add((y, m, p[2]))
    whole = [w for w, d in reported.items() if len(d) >= MIN_PRECIP_DAYS]     # a July-June year counts only with precipitation reported on half its days: some stations report temperature alone, or little else
    if not whole:
        raise RuntimeError(f"station {sid} reports no precipitation; choose another for road salt")
    return sorted(len(days.get(w, ())) for w in whole)[len(whole) // 2]


def salt_events(regions, first=2005, last=2024):
    """Road salt events a winter for each region [A], by runoff.salt_events: the same method in every state, Michigan included."""
    from waterledger_models import runoff as rq
    memo, out = {}, {}
    for rid, r in regions.items():
        sid = r["station_id"]
        if sid not in memo:
            memo[sid] = _median_cold_precip_days(sid, first, last)
        out[rid] = rq.salt_events(memo[sid])
    return out
