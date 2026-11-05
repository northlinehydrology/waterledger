"""Michigan's snapshot (design 0003, decision 8): the shared snapshot files, filled from Water Ledger Michigan's own data,
plus Michigan's site files carried as they are (michigan/*.json), which Michigan's provider keeps reading. Every Michigan
answer therefore stays identical, while anything generic (statewide studies, future state pages) reads Michigan like any
other state.

Inputs: the site's data files (the local site if there is one, else the ones waterledger.org publishes) and Michigan's
municipal boundaries (Census, via waterledger_data.places).

    waterledger snapshot MI --out DIR
"""
import hashlib, os

from waterledger import scenario as sc
from waterledger.national.snapshot import DOWNSTREAM_HUCS, FORMAT, _write

SITE_FILES = ("places", "estimates", "waters", "power")


def write(out, date=None, runs_dir=None):
    import datetime

    import geopandas as gpd

    import waterledger
    import waterledger_data
    import waterledger_models
    from waterledger.national.data import FILES
    from waterledger_data import energy, power
    from waterledger_data import places as pl
    date = date or datetime.date.today().isoformat()
    folder = os.path.join(out, "MI", date)
    os.makedirs(os.path.join(folder, "michigan"), exist_ok=True)
    P, E, W, PW = (sc.data(n) for n in SITE_FILES)

    # Michigan's own files, as the site publishes them
    for n in SITE_FILES:
        _write(os.path.join(folder, "michigan", n + ".json"), sc.data(n))

    if not all(r.get("e") for r in P["places"]):
        raise ValueError("Michigan's site files are from before model 1.8 (no place names its ERA5 cell): rebuild them with `waterledger build mi` first")
    places = []
    for r in P["places"]:
        p = sc.place(r["g"])
        lon, lat = sc.lonlat(r)
        places.append({"geoid": r["g"], "name": r["n"], "base": p["base"], "kind": r["k"], "level": "place" if r["k"] == "city" else "township",
                       "county": r["c"], "county_fips": r["cf"], "lat": round(lat, 5), "lon": round(lon, 5), "division": r["r"]})
    # format 3: each place's ERA5 cell and the cells' results, as every state's (national.cells); the site's own cells/ are the same records
    from waterledger.national import cells
    at, cell_files, weather, correction = cells.write(folder, places, runs_dir)
    bad = [r["g"] for r in P["places"] if at[r["g"]]["cell"] != r["e"]]
    if bad:
        raise ValueError(f"{len(bad)} Michigan places' cells in the site files differ from their points' (first: {bad[:3]}): rebuild the site files")
    places = [{**q, **at[q["geoid"]]} for q in places]
    _write(os.path.join(folder, "places.json"), {"places": places})
    bounds = pl.boundaries(pl.counties())
    from waterledger_data.census import _polygon
    g = gpd.GeoDataFrame([{**q, "geometry": _polygon(bounds[q["geoid"]]) if q["geoid"] in bounds else None} for q in places], geometry="geometry", crs=4326)
    g.to_parquet(os.path.join(folder, "places.parquet"))

    systems, by_place, nearest = {}, {}, {}
    for r in P["places"]:
        for w in r["w"]:
            systems[w["pwsid"]] = {"name": w["name"], "population": int(w.get("pop") or 0), "connections": int(w.get("connections") or 0)}
        if r["w"]:
            by_place[r["g"]] = [[w["pwsid"], w.get("share")] for w in r["w"]]
        else:
            n = sc.near_system(r)                      # the nearest sizable one (scenario.near_system)
            if n:
                systems.setdefault(n["w"]["pwsid"], {"name": n["w"]["name"], "population": int(n["w"].get("pop") or 0),
                                                      "connections": int(n["w"].get("connections") or 0)})
                nearest[r["g"]] = [n["w"]["pwsid"], round(n["km"], 1)]
    _write(os.path.join(folder, "supply.json"), {"systems": systems, "by_place": by_place, "nearest": nearest})

    plants = []
    for q in W["plants"]:
        lon, lat = sc.lonlat(q)
        plants.append({"id": q["id"], "name": q["n"], "city": q["city"], "lat": round(lat, 5), "lon": round(lon, 5), "design_mgd": q["design"],
                       "flow_mgd": q.get("flow"), "major": q["major"], "cso": q["cso"], "receiving": q.get("recv") or None, "huc12": q.get("h12"),
                       "lagoon": q["lagoon"]})
    _write(os.path.join(folder, "wastewater.json"), {"plants": plants})

    H = W["h12"]
    sheds = {r["g"]: {"h12": [{"code": w["code"], "name": w["name"], "share": w.get("share")} for w in r["h12"]], "h8": r.get("h8")} for r in P["places"]}
    paths = {}
    for v in sheds.values():
        if v["h12"] and v["h12"][0]["code"] not in paths:
            path, h = [], v["h12"][0]["code"]
            while h and h in H and len(path) < DOWNSTREAM_HUCS:
                path.append(h)
                h = H[h]["t"]
            paths[v["h12"][0]["code"]] = path
    used = {c for p in paths.values() for c in p}
    _write(os.path.join(folder, "receiving.json"), {"by_place": sheds, "reaches": {c: {"n": H[c]["n"], "i": H[c].get("i", []), "a": H[c].get("a", 0)} for c in used},
                                                     "downstream": paths, "great_lakes": {r["g"]: r["gl"] for r in P["places"] if r.get("gl")}, "attains": {"organization": "21MICH", "cycle": W.get("cycle")}})

    divisions = {k: {"name": v["name"], "station": v["station"], "station_id": None, "lat": v["lat"], "lon": v["lon"], "share_observed": None}
                 for k, v in E["regions"].items()}          # format 3: the regions' names and points; cooling is by cell
    _write(os.path.join(folder, "climate.json"), {"divisions": divisions, "staff_runs": E["staff"]["runs"],
                                                   "design_storms_in": {k: {str(a): b for a, b in v.items()} for k, v in E["county_storms_in"].items()},
                                                   "rain_in": W["rain_in"], "lake_source": E["lake_source"]})

    U = PW["utilities"]
    from waterledger.states.mi.provider import balancing_authority as ba
    by_u = {gid: energy.in_order([{"eia_id": power.EIA_ID.get(U[i]["n"]), "name": U[i]["n"], "type": U[i]["type"], "balancing_authority": ba(U[i]["n"]), "share": sh}
                                  for i, sh in v]) for gid, v in PW["places"].items()}
    loads = {str(power.EIA_ID[u["n"]]): {"mwh": round(u["avg_mw"] * 8760, 1) if u.get("avg_mw") is not None else None, "customers": u.get("cust"),
                                         "summer_mw": u.get("summer_mw"), "winter_mw": u.get("winter_mw")} for u in U if u["n"] in power.EIA_ID}
    gw = energy.grid_water()
    _write(os.path.join(folder, "energy.json"), {"by_place": by_u, "loads": loads, "grid_water": {b: gw[b] for b in ("MISO", "PJM")}})

    from waterledger.national.snapshot import write_water_use
    from waterledger.states.mi.provider import egle_layer
    wu_source, inputs, wu_years = write_water_use("MI", folder, state_layer=egle_layer())

    files = {}
    for name in [*FILES, *(f"michigan/{n}.json" for n in SITE_FILES)]:
        data = open(os.path.join(folder, name), "rb").read()
        files[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    _write(os.path.join(folder, "manifest.json"), {
        "format": FORMAT, "state": "MI", "fips": "26", "date": date, "model_version": E["model_version"],
        "data_generated": {n: sc.data(n).get("generated") or sc.data(n).get("updated") for n in SITE_FILES},
        "packages": {"waterledger": waterledger.__version__, "waterledger-data": waterledger_data.__version__, "waterledger-models": waterledger_models.__version__},
        "sources": {"places": "Census TIGERweb county subdivisions (Michigan's 1,541 cities and townships)", "supply": "EPA CWS service areas, SDWIS",
                    "wastewater": "EPA CWNS 2022, ECHO (with state-permitted plants)", "receiving": "USGS WBD, EPA ATTAINS (Michigan 2026 Integrated Report)",
                    "climate": "NOAA Atlas 14, Climate at a Glance; the eight Michigan regions' names, for salt and golf", "energy": "MPSC territories, EIA-861",
                    "cooling_weather": "Copernicus ERA5 (Open-Meteo's open copy), corrected near the shore toward NOAA ISD and ECCC stations (designs 0004, 0005)",
                    "wateruse": wu_source, "michigan": "Water Ledger Michigan's site files, carried as published"},
        "water_use_years": wu_years, "files": files, "inputs": inputs, "checks": None,
        "cells": cell_files, "cell_rule": {"land_at_least": 0.5}, "weather": weather, "correction": correction})
    return folder
