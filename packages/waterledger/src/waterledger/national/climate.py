"""The national tier's cooling results: the cooling Monte Carlo run on each climate division's NOAA station record (design
0002 decision 4), in the same per-100 MW form as Michigan's eight regions, cached per state and model version."""
import functools, json, os

from waterledger import states


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


def division_runs(state, n=200):
    """{division id: {"name", "station", "lat", "lon", "per_100mw"}}, per_100mw as cooling.run_location returns it."""
    from waterledger_data import climate, divisions
    from waterledger_data.config import CACHE
    from waterledger_models import MODEL_VERSION
    from waterledger_models.datacenter import cooling as cw
    path = os.path.join(CACHE, "climate", f"{state}_runs_model{MODEL_VERSION}_n{n}.json")
    if os.path.exists(path):
        return json.load(open(path))
    fips = next(f for f, s in states.FIPS.items() if s == state)
    from tqdm.auto import tqdm
    out = {}
    for d, s in tqdm(divisions.division_stations(fips, counties(state)).items(), desc=f"{state} cooling runs", unit="division", disable=None):
        t, T, RH, _ = climate.isd_hourly(s, divisions.FIRST, divisions.LAST)
        out[d] = {"name": f"{state} climate division {int(d[2:])}", "station": s["name"], "station_id": s["id"],
                  "lat": s["lat"], "lon": s["lon"], "share_observed": s["share_observed"], "per_100mw": cw.run_location(t, T, RH, n=n, mw=100.0)}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


@functools.lru_cache(maxsize=8)
def storms_and_rain(state):
    from waterledger_data import divisions
    cs = climate_areas(state)
    return divisions.design_storms(cs), divisions.rain_in(state, cs)


def salt_events(regions, first=2005, last=2024):
    """Road salt events a winter for each climate division [A]: the median winter's days with precipitation at 1 C or below at the division's station
    (NOAA ISD-Lite), x 0.6, which brings West and southeast Michigan's stations (72 and 59 days) to Michigan's assumed 40, with the same +/-50% range."""
    import gzip

    from waterledger_data import climate
    memo, out = {}, {}
    for rid, r in regions.items():
        sid = r["station_id"]
        if sid not in memo:
            usaf, wban = sid.split("-")
            days, winters = {}, set()
            for y in range(first, last + 1):
                path = os.path.join(climate.RAW, "isd", "lite", f"{sid}-{y}.gz")
                climate._fetch(climate.ISD_LITE.format(y=y, usaf=usaf, wban=wban), path)
                with gzip.open(path, "rt") as f:
                    for ln in f:
                        p = ln.split()
                        t, pr, m = int(p[4]), int(p[10]), int(p[1])
                        w = y + (m >= 7)
                        winters.add(w)
                        if t != -9999 and t <= 10 and (pr > 0 or pr == -1):
                            days.setdefault(w, set()).add((y, m, p[2]))
            whole = sorted(winters)[1:-1]         # the first and last winters are partial
            memo[sid] = sorted(len(days.get(w, ())) for w in whole)[len(whole) // 2]
        mid = 0.6 * memo[sid] if memo[sid] >= 2 else 0.0      # snow and ice this rare: no salt season to speak of
        out[rid] = [0.5 * mid, mid, 1.5 * mid]
    return out
