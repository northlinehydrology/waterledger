"""ERA5 hourly weather at a place's 0.25-degree grid cell, 1995-2024 (design 0004, model 1.8).

    cell(lat, lon)          the cell a place uses: its nearest, or the nearest at least half land when the nearest is mostly water
    fetch(cells)            each cell's hourly 2 m temperature and dew point, as fetched, into the raw cache (needs waterledger-data[era5])
    hourly(cell)            (times, temp_c, rh_pct) in local standard time, the form climate.isd_hourly and cooling.run_location use

The source is Open-Meteo's open-data copy of Copernicus ERA5 on AWS (s3://openmeteo/data/copernicus_era5; anonymous, no key,
CC-BY 4.0; values stored to 0.05 C), the copy the station check and the quantile-mapping prototype used. CDS's time-series
dataset, 0004's other source, needs an ECMWF key and is not built here. The raw cache keeps each cell as fetched, in UTC:
CACHE/era5/raw/<cell>/<fetch date>.npz with a .json beside it (the request, the file's sha256, the source and attribution).
"""
import datetime, functools, hashlib, json, math, os

import numpy as np

from waterledger_data.config import CACHE

LAND = 0.5                              # decision 3 of 0004 (Nov 3, 2026): a nearest cell under this land fraction is skipped for the nearest at least this
FIRST, LAST = 1995, 2024
OPEN_COPY = "openmeteo/data/copernicus_era5"
VARIABLES = ("temperature_2m", "dew_point_2m")
START = np.datetime64(f"{FIRST}-01-01T00", "h")             # UTC; a day past the end, so local standard time reaches Dec 31 everywhere west of Greenwich
END = np.datetime64(f"{LAST + 1}-01-02T00", "h")
CHUNK_FROM = 2022                                           # the open copy: one file a year to 2021, then 504-hour chunks from 1970-01-01
ATTRIBUTION = ("Generated using Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF is responsible "
               "for any use that may be made of the Copernicus information or data it contains.")
CITATION = ("Hersbach, H., et al. (2023). ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) "
            "Climate Data Store. doi:10.24381/cds.adbb2d47")
MAGNUS = 17.625, 243.04                                     # Alduchov and Eskridge (1996), as climate.isd_hourly uses
RAW = os.path.join(CACHE, "era5", "raw")


@functools.lru_cache(maxsize=1)
def _grid():
    z = np.load(os.path.join(os.path.dirname(__file__), "tables", "era5_conus.npz"))
    return z["lsm"], z["orog_m"], int(z["ci0"]), int(z["cj0"])


def _at(field, ci, cj):
    lsm, orog, ci0, cj0 = _grid()
    a = {"lsm": lsm, "orog": orog}[field]
    i, j = ci - ci0, cj - cj0
    if not (0 <= i < a.shape[0] and 0 <= j < a.shape[1]):
        raise ValueError(f"cell {cell_id(ci, cj)} is outside the shipped grid (24-50 N, 125-66 W)")
    return float(a[i, j])


def cell_id(ci, cj):
    """"43.00_-85.50" for the cell at latitude ci / 4 and longitude cj / 4."""
    return f"{ci / 4:.2f}_{cj / 4:.2f}"


def indexes(cid):
    lat, lon = (float(x) for x in cid.split("_"))
    return round(lat * 4), round(lon * 4)


def land(cid):
    """The cell's ERA5 land-sea mask, 0 (water) to 1 (land)."""
    return _at("lsm", *indexes(cid))


def elevation(cid):
    """The cell's ERA5 surface elevation (m): geopotential at the surface / 9.80665."""
    return _at("orog", *indexes(cid))


def km(a_lat, a_lon, b_lat, b_lon):
    p = math.pi / 180
    h = math.sin((b_lat - a_lat) * p / 2) ** 2 + math.cos(a_lat * p) * math.cos(b_lat * p) * math.sin((b_lon - a_lon) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _nearest_land(lat, lon, need):
    """Rings of cells outward; a ring k cells out is at least k x 27.8 km x cos(lat) away, so the search stops once that passes the best
    found. Ties go to the lower latitude, then the lower longitude. The search of design 0004's land_rule.py."""
    ci0, cj0 = round(lat * 4), round(lon * 4)
    best = None
    for k in range(1, 40):
        for a in range(-k, k + 1):
            for b in range(-k, k + 1):
                if max(abs(a), abs(b)) != k or _at("lsm", ci0 + a, cj0 + b) < need:
                    continue
                c = (km(lat, lon, (ci0 + a) / 4, (cj0 + b) / 4), ci0 + a, cj0 + b)
                best = min(best, c) if best else c
        if best and best[0] < (k - 0.5) * 27.8 * math.cos(math.radians(lat + 1)):
            break
    return best[1], best[2]


def cell(lat, lon, land=LAND):
    """The cell a place at (lat, lon) uses (decision 3 of 0004): {id, lat, lon, km, land, moved, nearest {id, km, land}}. `moved` is true
    when the nearest cell is under `land` and the nearest cell at least `land` is used instead; `land=None` takes the nearest always."""
    ni, nj = round(lat * 4), round(lon * 4)
    near = {"id": cell_id(ni, nj), "km": km(lat, lon, ni / 4, nj / 4), "land": _at("lsm", ni, nj)}
    moved = land is not None and near["land"] < land
    ci, cj = _nearest_land(lat, lon, land) if moved else (ni, nj)
    return {"id": cell_id(ci, cj), "lat": ci / 4, "lon": cj / 4, "km": km(lat, lon, ci / 4, cj / 4), "land": _at("lsm", ci, cj),
            "moved": moved, "nearest": near}


def raw_path(cid):
    """The cell's newest raw file, or None."""
    d = os.path.join(RAW, cid)
    got = sorted(f for f in os.listdir(d) if f.endswith(".npz")) if os.path.isdir(d) else []
    return os.path.join(d, got[-1]) if got else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _files():
    """The open copy's files over START..END: (kind, key, first hour) with kind "year" or "chunk"."""
    hours = lambda t: int(t.astype("datetime64[h]").astype(np.int64))
    out = [("year", y, hours(np.datetime64(f"{y}-01-01T00"))) for y in range(FIRST, CHUNK_FROM)]
    k0, k1 = hours(np.datetime64(f"{CHUNK_FROM}-01-01T00")) // 504, (hours(END) - 1) // 504
    return out + [("chunk", k, k * 504) for k in range(k0, k1 + 1)]


def _read(fs, var, kind, key, cells):
    import omfiles
    path = f"{OPEN_COPY}/{var}/" + (f"year_{key}.om" if kind == "year" else f"chunk_{key}.om")
    r = omfiles.OmFileReader.from_fsspec(fs, path)
    return {c: np.asarray(r[indexes(c)[0] + 360, indexes(c)[1] + 720, :], dtype=np.float32) for c in cells}


def fetch(cells, workers=16, today=None):
    """Fetch the cells not yet in the raw cache from the open copy, all of them per file read, and return {cell: raw path}. A cell
    already cached is not fetched again (a new fetch date only on purpose: delete the old file). Needs waterledger-data[era5]."""
    import fsspec
    from concurrent.futures import ThreadPoolExecutor
    cells = sorted(set(cells))
    out = {c: raw_path(c) for c in cells}
    todo = [c for c in cells if not out[c]]
    if not todo:
        return out
    fs = fsspec.filesystem("s3", anon=True)
    jobs = [(v, kind, key, t0) for v in VARIABLES for kind, key, t0 in _files()]
    with ThreadPoolExecutor(workers) as pool:
        got = list(pool.map(lambda j: (j[0], j[3], _read(fs, j[0], j[1], j[2], todo)), jobs))
    today = today or datetime.date.today().isoformat()
    s, e = int(START.astype(np.int64)), int(END.astype(np.int64))
    for c in todo:
        series = {}
        for var in VARIABLES:
            x = np.full(e - s, np.nan, dtype=np.float32)
            for v, t0, vals in got:
                if v == var:
                    lo, hi = max(t0, s), min(t0 + len(vals[c]), e)
                    if hi > lo:
                        x[lo - s:hi - s] = vals[c][lo - t0:hi - t0]
            series[var] = x
        out[c] = write_raw(c, series, today, {"source": f"s3://{OPEN_COPY}", "variables": list(VARIABLES), "grid_index": [indexes(c)[0] + 360, indexes(c)[1] + 720],
                                              "start_utc": str(START), "end_utc_exclusive": str(END)})
    return out


def write_raw(cid, series, date, request):
    """Save a cell's series as fetched (float32, hourly from START in UTC) and its record: request, sha256, missing hours, attribution."""
    d = os.path.join(RAW, cid)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{date}.npz")
    np.savez_compressed(path + ".part.npz", start_utc=str(START), **series)
    os.replace(path + ".part.npz", path)
    meta = {"cell": cid, "fetched": date, "request": request, "sha256": sha256(path), "hours": int(len(next(iter(series.values())))),
            "missing": {k: int(np.isnan(v).sum()) for k, v in series.items()}, "licence": "CC-BY-4.0", "attribution": ATTRIBUTION, "citation": CITATION}
    json.dump(meta, open(os.path.join(d, f"{date}.json"), "w"), indent=1)
    return path


def series(cid):
    """(UTC hours as datetime64[h], T, Td) from the cell's newest raw file."""
    path = raw_path(cid)
    if not path:
        raise FileNotFoundError(f"ERA5 cell {cid} is not in the raw cache; era5.fetch([{cid!r}]) first")
    z = np.load(path)
    t = z["temperature_2m"].astype(float)
    return np.datetime64(str(z["start_utc"]), "h") + np.arange(len(t)), t, z["dew_point_2m"].astype(float)


def rh_from(t, td):
    a = lambda x: np.exp(MAGNUS[0] * x / (MAGNUS[1] + x))
    return np.clip(100 * a(np.asarray(td, float)) / a(np.asarray(t, float)), 1, 100)


def local(cid, first=FIRST, last=LAST):
    """(times, T, Td) in local standard time at the cell's longitude (round(lon / 15) hours from UTC, isd_hourly's rule), whole days
    first..last. Raises if any hour kept is missing."""
    utc, t, td = series(cid)
    lst = utc + np.timedelta64(round(indexes(cid)[1] / 4 / 15), "h")
    days = lst.astype("datetime64[D]")
    keep = (days >= np.datetime64(f"{first}-01-01")) & (days <= np.datetime64(f"{last}-12-31"))
    if np.isnan(t[keep]).any() or np.isnan(td[keep]).any():
        raise ValueError(f"ERA5 cell {cid}: hours missing in {first}-{last}")
    return [str(x)[:16] for x in lst[keep].astype("datetime64[m]")], t[keep], td[keep]


def hourly(cid, first=FIRST, last=LAST, correct=None):
    """(times, temp_c, rh_pct) in local standard time. `correct(times, t, td) -> (t, td)` is applied first (quantile mapping, 0005)."""
    times, t, td = local(cid, first, last)
    if correct:
        t, td = correct(times, t, td)
    return times, list(t), list(rh_from(t, td))
