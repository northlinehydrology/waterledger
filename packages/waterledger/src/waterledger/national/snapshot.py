"""Write a state's snapshot (design 0003): the files the package and waterledger.org read, plus a manifest.

    <out>/<ST>/<date>/manifest.json   what the snapshot is: state, date, format and model versions, sources, files with
                                      sizes and checksums, and the build's statewide checks
                      places.json     every place: Census ID, name, kind, level, county, point, climate division
                      places.parquet  the same places with boundaries (GeoParquet, for point lookups and maps in Python)
                      supply.json     water systems, and the ones serving each place with their shares
                      wastewater.json sewer plants
                      receiving.json  each place's watersheds; impairments and TMDLs by HUC12; each place's downstream path
                      climate.json    climate divisions (station, cooling results per 100 MW), staff water draws, design
                                      storms and rainfall by county
                      energy.json     utilities by place, their loads, grid region and power-plant water per kWh

Run after `waterledger build-state` (which fills the cache): `waterledger snapshot OH --out DIR`.
"""
import datetime, hashlib, json, os

from waterledger import states

FORMAT = 1
DOWNSTREAM_HUCS = 25


def _write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"))


def _downstream(state, starts):
    """{start huc12: [codes, up to DOWNSTREAM_HUCS]} and {code: {"n", "i"}} for every reach on those paths. Paths follow the
    state's own WBD links and continue through the tracer only where the water leaves the state (once per exit)."""
    from waterledger_data import receiving as rc
    H = rc.by_huc12(state)
    reaches = {h: {"n": v["n"], "i": v.get("i", [])} for h, v in H.items()}
    exits = {}
    paths = {}
    for s in starts:
        path, h = [], s
        while h and len(path) < DOWNSTREAM_HUCS:
            if h in H:
                path.append(h)
                nxt = H[h]["t"]
                if nxt is None and h not in exits:                        # leaves the state (or ends): continue with the tracer
                    exits[h] = rc.downstream(h, hops=DOWNSTREAM_HUCS)
                h = nxt if nxt is not None else None
                if nxt is None and len(exits[path[-1]]) > 1:
                    for r in exits[path[-1]][1:DOWNSTREAM_HUCS - len(path) + 1]:
                        path.append(r["code"])
                        reaches.setdefault(r["code"], {"n": r["name"], "i": r["listings"]})
            else:
                break
        paths[s] = path
    used = {c for p in paths.values() for c in p}
    return paths, {c: reaches[c] for c in used if c in reaches}


def write(state, out, date=None, checks=None):
    """Write the snapshot for `state` under out/<ST>/<date>/ from the cached layers; returns the snapshot folder."""
    from waterledger.national import climate as nc
    from waterledger_data import divisions, energy, receiving, supply, wastewater
    from waterledger_models import MODEL_VERSION
    from waterledger_models.datacenter import cooling as cw
    import waterledger
    import waterledger_data
    import waterledger_models
    state = state.upper()
    date = date or datetime.date.today().isoformat()
    folder = os.path.join(out, state, date)
    os.makedirs(folder, exist_ok=True)
    from waterledger.national.data import LiveData as _Live
    pl = _Live(state).places()
    cd = divisions.county_divisions()

    pl.to_parquet(os.path.join(folder, "places.parquet"))
    _write(os.path.join(folder, "places.json"), {"places": [
        {"geoid": r.geoid, "name": r.name, "base": r.base, "kind": r.kind.lower(), "level": r.level, "county": r.county,
         "county_fips": r.county_fips, "lat": round(float(r.lat), 5), "lon": round(float(r.lon), 5), "division": cd.get(r.county_fips)}
        for r in pl.itertuples()]})

    sy = supply.water_systems(state)
    by = supply.systems_by_place(state, pl)
    from waterledger.national.data import LiveData
    live = LiveData(state)
    # places with no system mapped: the nearest sizable one, edge to edge
    nearest = {g: [w["pwsid"], km] for g, (w, km) in live.nearest_systems([g for g in pl.geoid if g not in by]).items() if w}
    _write(os.path.join(folder, "supply.json"), {
        "systems": {r.pwsid: {"name": r.name, "population": int(r.population or 0), "connections": int(r.connections or 0)} for r in sy.itertuples()},
        "by_place": {g: [[w["pwsid"], w["share"]] for w in ws] for g, ws in by.items()}, "nearest": nearest})

    _write(os.path.join(folder, "wastewater.json"), {"plants": wastewater.plants(state)})

    sheds = receiving.watersheds_by_place(state, pl)
    starts = sorted({v["h12"][0]["code"] for v in sheds.values() if v["h12"]})
    paths, reaches = _downstream(state, starts)
    _write(os.path.join(folder, "receiving.json"), {"by_place": sheds, "reaches": reaches, "downstream": paths,
                                                     "attains": dict(zip(("organization", "cycle"), receiving.organization(state)))})

    storms, rain = nc.storms_and_rain(state)
    _write(os.path.join(folder, "climate.json"), {"divisions": nc.division_runs(state), "staff_runs": cw.staff_runs(200),
                                                   "design_storms_in": storms, "rain_in": rain})

    us = energy.utilities_by_place(state, pl)
    loads = energy.loads(state)
    bas = {u["balancing_authority"] for v in us.values() for u in v if u["balancing_authority"]}
    _write(os.path.join(folder, "energy.json"), {"by_place": us, "loads": {str(k): v for k, v in loads.items()},
                                                  "grid_water": {b: w for b, w in energy.grid_water().items() if b in bas}})

    files = {}
    for name in sorted(os.listdir(folder)):
        if name == "manifest.json":
            continue
        data = open(os.path.join(folder, name), "rb").read()
        files[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    manifest = {"format": FORMAT, "state": state, "fips": next(f for f, s in states.FIPS.items() if s == state), "date": date,
                "model_version": MODEL_VERSION, "packages": {"waterledger": waterledger.__version__, "waterledger-data": waterledger_data.__version__,
                                                              "waterledger-models": waterledger_models.__version__},
                "sources": {"places": "Census TIGERweb", "supply": "EPA CWS service areas, SDWIS", "wastewater": "EPA CWNS 2022, ECHO",
                            "receiving": "USGS WBD, EPA ATTAINS (assessments by HUC12)", "climate": "NOAA ISD, NCEI climate divisions, Atlas 14, Climate at a Glance",
                            "energy": "HIFLD retail service territories (PNNL), EIA-861, Siddik et al. 2024"},
                "files": files, "checks": checks}
    _write(os.path.join(folder, "manifest.json"), manifest)
    return folder
