"""The national tier's cooling results: the cooling Monte Carlo run on each climate division's NOAA station record (design
0002 decision 4), in the same per-100 MW form as Michigan's eight regions, cached per state and model version."""
import functools, json, os

from waterledger import states


@functools.lru_cache(maxsize=8)
def counties(state):
    from waterledger.national.provider import _places
    pl = _places(state)
    return [{"geoid": r.geoid, "lat": float(r.lat), "lon": float(r.lon)} for r in pl[pl.level == "county"].itertuples()]


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
    out = {}
    for d, s in divisions.division_stations(fips, counties(state)).items():
        t, T, RH, _ = climate.isd_hourly(s, divisions.FIRST, divisions.LAST)
        out[d] = {"name": f"{state} climate division {int(d[2:])}", "station": s["name"], "station_id": s["id"],
                  "lat": s["lat"], "lon": s["lon"], "share_observed": s["share_observed"], "per_100mw": cw.run_location(t, T, RH, n=n, mw=100.0)}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


@functools.lru_cache(maxsize=8)
def storms_and_rain(state):
    from waterledger_data import divisions
    cs = counties(state)
    return divisions.design_storms(cs), divisions.rain_in(state, cs)
