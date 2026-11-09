"""Model 1.8's cooling results by ERA5 cell in a state's snapshot (snapshot format 3, design 0004, section 5; correction from 0005).

    cells/<cell>.json   one cell's results: per_100mw (the structure the divisions and regions carry), its center, land fraction and
                        ERA5 elevation, the design dry-bulb, period, hours, source and attribution, and 0005's correction block
    cells/index.json    every cell's center, land fraction, places and the places the land rule moved there, and its file's checksum
    places.json         each place gains cell, cell_km, cell_land, cell_moved (and nearest_* when moved) and weather_corrected

A cell's results come from its run file (waterledger.national.era5, CACHE/era5/runs/model1.8/<cell>.json): `waterledger era5 run ST`
writes them, part by part. A cell shared across a state line is in both states' snapshots, from the same run file.
"""
import hashlib, json, os

FORMAT = 3
CELL_FORMAT = 1
CLOSE_REL = 1e-9          # the central run's withdrawn + condensate against consumed + returned: the same numbers, rounding aside
CELL_KEYS = ("lat", "lon", "land", "elev_m", "design_dry_bulb_c", "model_version", "draws", "seed", "mw", "period", "hours", "time", "correction")


def _write(path, obj):
    from waterledger.national.snapshot import _write as w
    w(path, obj)


def record(run):
    """A cell's snapshot record from its run file (a dict): what the page and the package read for a place in that cell."""
    w = run["weather"]
    plants = {k: run[k] for k in ("plant", "per_100mw_plants", "grid") if k in run}  # model 1.10: the default plant's results and the others'; 1.11: the grid's BAs
    return {"format": CELL_FORMAT, "cell": run["cell"], **{k: run[k] for k in CELL_KEYS}, "per_100mw": run["per_100mw"], **plants,
            "source": {"dataset": "ERA5 hourly 2 m temperature and dew point", "copy": w["source"], "fetched": w["fetched"], "sha256": w["sha256"],
                       "citation": w["citation"], "licence": "CC-BY-4.0"},
            "attribution": w["attribution"]}


def assign(places):
    """{geoid: era5.cell's record} for the state's places (rows with geoid, lat and lon)."""
    from waterledger_data import era5
    return {p["geoid"]: era5.cell(float(p["lat"]), float(p["lon"])) for p in places}


def place_fields(c, corrected):
    """A place's cell fields in places.json, from era5.cell's record and whether its cell's weather was corrected."""
    out = {"cell": c["id"], "cell_km": round(c["km"], 2), "cell_land": round(c["land"], 4), "cell_moved": c["moved"], "weather_corrected": corrected}
    if c["moved"]:
        out |= {"nearest_cell": c["nearest"]["id"], "nearest_km": round(c["nearest"]["km"], 2), "nearest_land": round(c["nearest"]["land"], 4)}
    return out


def for_regions(points, place_cells):
    """{region: cell} for a page's regions or climate divisions, where it shows one with no place chosen: the cell at the region's own point
    (`points` {region: (lon, lat)}, already as the places' points are), if a place uses it, else the cell most of the region's places use.
    `place_cells`: [(region, cell)] for every place."""
    from collections import Counter

    from waterledger_data import era5
    used = {c for _, c in place_cells}
    out = {}
    for rid, (lon, lat) in points.items():
        own = era5.cell(round(lat, 5), round(lon, 5))["id"]
        mine = Counter(c for r, c in place_cells if r == rid)
        out[rid] = own if own in used else mine.most_common(1)[0][0] if mine else None
    return out


class RunsMissing(FileNotFoundError):
    """Cells with no run here. The runs are on the machine that made them and in the private bucket `waterledger-raw`, so a
    machine without them (GitHub's) can't build a format 3 snapshot or a live cell record."""


def runs(ids, runs_dir=None):
    """{cell: its run file, read}; raises RunsMissing naming the cells with no run, which `waterledger era5 run` makes."""
    from waterledger.national import era5 as E
    runs_dir = runs_dir or E.RUNS
    missing = [c for c in ids if not os.path.exists(os.path.join(runs_dir, f"{c}.json"))]
    if missing:
        raise RunsMissing(f"{len(missing)} of {len(ids)} cells have no model {E.RUN_MODEL} run in {runs_dir} (first: {', '.join(missing[:5])}); "
                                "run `waterledger era5 run ST` first, or pull them from R2")
    return {c: json.load(open(os.path.join(runs_dir, f"{c}.json"))) for c in ids}


def _fetched(site):
    """The first and last dates a station's raw files were downloaded (ISD-Lite years, or ECCC's), from the cache."""
    import datetime

    from waterledger_data import climate
    parts = [p["id"] for p in site.get("parts") or [{"id": site["id"]}]]
    if site.get("source") == "eccc":
        files = [os.path.join(climate.RAW, "eccc", "hourly", f) for f in os.listdir(os.path.join(climate.RAW, "eccc", "hourly")) if f.split("-")[0] in parts] \
            if os.path.isdir(os.path.join(climate.RAW, "eccc", "hourly")) else []
    else:
        d = os.path.join(climate.RAW, "isd", "lite")
        files = [os.path.join(d, f) for f in os.listdir(d) if any(f.startswith(p + "-") for p in parts)] if os.path.isdir(d) else []
    t = sorted(os.path.getmtime(f) for f in files)
    return [datetime.date.fromtimestamp(x).isoformat() for x in (t[0], t[-1])] if t else None


def write(folder, places, runs_dir=None):
    """Write cells/ and return (each place's cell fields {geoid: {...}}, the manifest's "cells" files, its "weather" block, its "correction"
    block). `places`: rows with geoid, lat and lon."""
    from waterledger.national import era5 as E
    from waterledger_data import era5
    from waterledger_models import quantile_mapping as Q
    at = assign(places)
    by_cell = {}
    for g, c in at.items():
        by_cell.setdefault(c["id"], []).append(g)
    got = runs(sorted(by_cell), runs_dir)
    os.makedirs(os.path.join(folder, "cells"), exist_ok=True)
    files, index, anchors = {}, {}, {}
    for cid in sorted(by_cell):
        rec = record(got[cid])
        path = os.path.join(folder, "cells", f"{cid}.json")
        _write(path, rec)
        data = open(path, "rb").read()
        files[f"cells/{cid}.json"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        index[cid] = {"lat": rec["lat"], "lon": rec["lon"], "land": rec["land"], "places": sorted(by_cell[cid]),
                      "moved": sorted(g for g in by_cell[cid] if at[g]["moved"]), "corrected": rec["correction"]["applied"],
                      "sha256": files[f"cells/{cid}.json"]["sha256"]}
        for s in rec["correction"]["stations"]:
            anchors.setdefault(s["id"], {k: s.get(k) for k in ("id", "name", "source", "elev_m")})
    _write(os.path.join(folder, "cells", "index.json"), {"format": CELL_FORMAT, "cells": index})
    data = open(os.path.join(folder, "cells", "index.json"), "rb").read()
    files["cells/index.json"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    fields = {g: place_fields(c, index[c["id"]]["corrected"]) for g, c in at.items()}
    fetched = sorted(got[c]["weather"]["fetched"] for c in got)
    weather = {"dataset": "ERA5 hourly data on single levels, 2 m temperature and dew point", "citation": era5.CITATION, "doi": "10.24381/cds.adbb2d47",
               "licence": "CC-BY-4.0", "attribution": era5.ATTRIBUTION, "copy": f"s3://{era5.OPEN_COPY}", "period": f"{era5.FIRST}-{era5.LAST}",
               "fetched": [fetched[0], fetched[-1]], "model_version": E.RUN_MODEL, "cells": len(by_cell)}
    sites = {}
    for p in os.listdir(E.ANCHORS) if os.path.isdir(E.ANCHORS) else []:
        if p.endswith(".json") and p[:-5] in anchors:
            sites[p[:-5]] = json.load(open(os.path.join(E.ANCHORS, p)))
    used = []
    for sid, a in sorted(anchors.items()):
        meta = sites.get(sid, {})
        used.append({**a, "lat": meta.get("lat"), "lon": meta.get("lon"), "cell_land": meta.get("cell_land"), "share_observed": meta.get("share_observed"),
                     "parts": [p["id"] for p in meta["parts"]] if meta.get("parts") else None, "fetched": _fetched({**meta, **a}) if meta else None})
    from waterledger_data import climate
    correction = {"method": Q.METHOD, "design": "0005", "cells_corrected": sum(v["corrected"] for v in index.values()),
                  "rule": {"shore_cell_land_below": Q.SHORE_LAND,
                           "stations": f"shore cells: shore stations (own cell under {Q.SHORE_LAND:.0%} land) within {Q.R_KM:.0f} km; land cells: land stations (own cell at least {Q.SHORE_LAND:.0%} land) within {Q.R_KM:.0f} km; at most {Q.K}, 1/d^2",
                           "lapse_c_per_m": Q.LAPSE, "bins": "calendar month (with the months either side) x 3-hour block of local standard time, 99 quantiles"},
                  "anchors": used, "isd": "NOAA NCEI Integrated Surface Database, ISD-Lite (https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)"}
    if any(a["source"] == "eccc" for a in used):
        correction["eccc"] = {"licence": "Environment and Climate Change Canada Data Servers End-use Licence, version 2.1", "licence_url": climate.ECCC_LICENCE,
                              "attribution": climate.ECCC_ATTRIBUTION, "source": "MSC GeoMet (api.weather.gc.ca), collection climate-hourly"}
    return fields, files, weather, correction


def closes(per_100mw, rel=CLOSE_REL):
    """The designs whose central run doesn't close: withdrawn + condensate = consumed + returned, on the average day and over the year.
    Not on the peak day: each flow's 1-in-10-year peak is taken on its own days (on cell 41.75_-83.50 assist's are 1% apart), and the estimate
    closes its middle peak by taking consumed as what is left (scenario.cooling_estimate)."""
    bad = []
    for d, r in per_100mw.items():
        for when in ("avg", "annual_mg"):
            w, n, c, o = (r[f"{k}_{when}"]["central"] for k in ("withdrawn", "condensate", "consumed", "returned"))
            if abs((w + n) - (c + o)) > rel * max(abs(w + n), 1e-12):
                bad.append(f"{d} {when}")
    return bad


def check(sd, places):
    """Format 3's statewide checks on a snapshot `sd` (data.SnapshotData) for its `places` (geoids): every place has a cell with results,
    every cell's flows close, and every corrected cell names its stations. {"cells": n, "places_with_cell": share, "unclosed": [...], "corrected_without_stations": [...]}."""
    ids, have = {}, 0
    for g in places:
        c = sd.cell_of(g)
        if c:
            ids.setdefault(c["cell"], []).append(g)
    unclosed, bare, missing = [], [], []
    for cid in sorted(ids):
        try:
            rec = sd.cell(cid)
        except Exception as e:                                  # noqa: BLE001  reported, with the cell
            missing.append(f"{cid}: {type(e).__name__}")
            continue
        have += len(ids[cid])
        unclosed += [f"{cid} {x}" for x in closes(rec["per_100mw"])]
        corr = rec["correction"]
        if corr["applied"] and not all(s.get("id") and s.get("name") and s.get("km") is not None for s in corr["stations"] or [{}]):
            bare.append(cid)
    return {"cells": len(ids), "places_with_cell": have / max(len(places), 1), "cells_missing": missing, "unclosed": unclosed,
            "corrected_without_stations": bare}
