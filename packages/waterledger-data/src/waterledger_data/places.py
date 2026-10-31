"""Michigan municipalities and their public water context, cached under engine/data/raw/places/.

Sources (all public):
  Census TIGERweb   county subdivisions (every city and township) and counties
  EPA               Community Water System Service Area Boundaries (reported or modeled), via ArcGIS REST
  USGS              Watershed Boundary Dataset HUC12 and HUC8, via The National Map REST
  NOAA              Atlas 14 precipitation frequency (24-hour depths), via the PFDS service
"""
import concurrent.futures as cf, json, os, time, urllib.parse, urllib.request

import numpy as np

from waterledger_data.config import CACHE
import shapely

from waterledger_data.climate import atlas14_depths

RAW = os.path.join(CACHE, "places")
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
EPA_SA = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/Water_System_Boundaries/FeatureServer/0/query"
WBD = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer"
LSAD = {"25": "city", "44": "township", "49": "charter township"}


def _get(url, params, retries=5, post=False):
    data = urllib.parse.urlencode(params).encode() if post else None
    q = url if post else url + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(q, data=data, timeout=120) as r:
                d = json.load(r)
            if isinstance(d, dict) and "error" in d:
                raise RuntimeError(str(d["error"])[:200])
            return d
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(3 * (i + 1))


def _cached(name, fn):
    path = os.path.join(RAW, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    os.makedirs(RAW, exist_ok=True)
    data = fn()
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def counties():
    def fetch():
        d = _get(f"{TIGER}/State_County/MapServer/1/query", {"where": "STATE='26'", "outFields": "GEOID,NAME,BASENAME,COUNTY,INTPTLAT,INTPTLON",
                                                            "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.01, "geometryPrecision": 3, "f": "json"})
        return [{"geoid": f["attributes"]["GEOID"], "name": f["attributes"]["BASENAME"], "lat": float(f["attributes"]["INTPTLAT"]),
                 "lon": float(f["attributes"]["INTPTLON"]), "rings": f["geometry"]["rings"]} for f in d["features"]]
    return _cached("counties.json", fetch)


def municipalities():
    def fetch():
        d = _get(f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/1/query", {"where": "STATE='26'", "outFields": "GEOID,NAME,BASENAME,COUNTY,LSADC,INTPTLAT,INTPTLON,AREALAND",
                                                                            "returnGeometry": "false", "resultRecordCount": 5000, "f": "json"})
        out = []
        for f in d["features"]:
            a = f["attributes"]
            if a["LSADC"] not in LSAD or not a["AREALAND"]:
                continue
            out.append({"geoid": a["GEOID"], "name": a["NAME"], "base": a["BASENAME"], "kind": LSAD[a["LSADC"]], "county_fips": "26" + a["COUNTY"],
                        "lat": round(float(a["INTPTLAT"]), 4), "lon": round(float(a["INTPTLON"]), 4)})
        return out
    return _cached("municipalities.json", fetch)


def boundaries(cnties):
    """Generalized municipal boundary polygons (Census TIGERweb), fetched county by county."""
    def fetch():
        out = {}
        for c in cnties:
            d = _get(f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/1/query", {"where": f"STATE='26' AND COUNTY='{c['geoid'][2:]}'", "outFields": "GEOID",
                                                                                "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.002, "geometryPrecision": 4, "f": "json"})
            for f in d["features"]:
                out[f["attributes"]["GEOID"]] = f["geometry"]["rings"]
        return out
    return _cached("boundaries.json", fetch)


def _poly(rings):
    return json.dumps({"rings": rings, "spatialReference": {"wkid": 4326}})


def _inside(x, y, rings):
    c = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c


def _inside_many(pts, rings):
    """Even-odd point-in-polygon for many points at once (holes and multipart rings handled by parity)."""
    pts = np.asarray(pts, dtype=float)
    hits = np.zeros(len(pts), dtype=int)
    for ring in rings:
        if len(ring) >= 3:
            hits += shapely.contains_xy(shapely.Polygon(np.asarray(ring, dtype=float)[:, :2]), pts[:, 0], pts[:, 1])
    return hits % 2 == 1


def _samples(rings, n=24):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pts = [(x0 + (i + 0.5) * (x1 - x0) / n, y0 + (j + 0.5) * (y1 - y0) / n) for i in range(n) for j in range(n)]
    return [p for p, ok in zip(pts, _inside_many(pts, rings)) if ok]


def _overlaps(url, rings, fields, extra_where=None):
    params = {"geometry": _poly(rings), "geometryType": "esriGeometryPolygon", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
              "outFields": fields, "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.002, "geometryPrecision": 4, "f": "json"}
    if extra_where:
        params["where"] = extra_where
    d = _get(url, params, post=True)
    pts = _samples(rings)
    out = []
    for f in d.get("features", []):
        g = (f.get("geometry") or {}).get("rings")
        if not g or not pts:
            continue
        share = _inside_many(pts, g).mean()
        if share >= 0.05:
            out.append((float(share), f["attributes"]))
    out.sort(key=lambda t: -t[0])
    return out


def _water_systems(rings):
    """Community water systems serving the municipality, with the share of its area each service area covers (EPA; reported or modeled boundaries)."""
    rows = _overlaps(EPA_SA, rings, "PWSID,PWS_Name,Population_Served_Count,Service_Connections_Count,Data_Provider_Type", "PWSID LIKE 'MI%'")
    return [{"pwsid": a["PWSID"], "name": a["PWS_Name"], "pop": a.get("Population_Served_Count"), "connections": a.get("Service_Connections_Count"),
             "boundary": a.get("Data_Provider_Type"), "share": round(sh, 2)} for sh, a in rows[:4]]


MI_ENVELOPE = "-90.5,41.6,-82.1,48.4"


def _layer_polys(layer, fields, name, page=500):
    """Every WBD polygon in a layer that intersects Michigan, generalized, fetched in pages and cached."""
    def fetch():
        out, off = [], 0
        while True:
            d = _get(f"{WBD}/{layer}/query", {"where": "1=1", "geometry": MI_ENVELOPE, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                             "spatialRel": "esriSpatialRelIntersects", "outFields": fields, "returnGeometry": "true", "outSR": 4326,
                                             "maxAllowableOffset": 0.002, "geometryPrecision": 4, "orderByFields": "OBJECTID",
                                             "resultOffset": off, "resultRecordCount": page, "f": "json"}, post=True)
            feats = d.get("features", [])
            for f in feats:
                if (f.get("geometry") or {}).get("rings"):
                    out.append({**f["attributes"], "rings": f["geometry"]["rings"]})
            print(name, len(out))
            if len(feats) < page:
                return out
            off += page
    polys = _cached(name, fetch)
    for q in polys:
        xs = [pt[0] for r in q["rings"] for pt in r]
        ys = [pt[1] for r in q["rings"] for pt in r]
        q["bbox"] = (min(xs), min(ys), max(xs), max(ys))
    return polys


def _local_shares(rings, polys, pts=None):
    """Share of a municipality's sampled points inside each polygon (bounding boxes first), shares under 5% dropped."""
    pts = pts if pts is not None else _samples(rings)
    if not pts:
        return []
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    out = []
    for q in polys:
        b = q["bbox"]
        if b[0] > x1 or b[2] < x0 or b[1] > y1 or b[3] < y0:
            continue
        share = _inside_many(pts, q["rings"]).mean()
        if share >= 0.05:
            out.append((float(share), q))
    out.sort(key=lambda t: -t[0])
    return out


def _watersheds(rings, lat, lon, h12, h8):
    """HUC12 subwatersheds covering the municipality with their shares, and the HUC8 at its internal point (USGS WBD)."""
    rows = _local_shares(rings, h12)
    at = sorted((q for q in h8 if q["bbox"][0] <= lon <= q["bbox"][2] and q["bbox"][1] <= lat <= q["bbox"][3] and _inside(lon, lat, q["rings"])), key=lambda q: q["huc8"])   # the lowest code where two overlap, whatever order the service returned
    return {"huc12": [{"code": q["huc12"], "name": q["name"], "share": round(sh, 2)} for sh, q in rows[:5]],
            "huc8": {"code": at[0]["huc8"], "name": at[0]["name"]} if at else None}


def enrich(munis, bounds, workers=8):
    """Water systems (EPA query per place) and watersheds (local overlap with bulk USGS polygons) for each municipality. Cached per GEOID; safe to re-run."""
    path = os.path.join(RAW, "enrich.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    cache = {k: v for k, v in cache.items() if "error" not in v}
    todo = [m for m in munis if m["geoid"] not in cache and m["geoid"] in bounds]
    h12 = _layer_polys(6, "huc12,name", "wbd_huc12_mi.json")
    h8 = _layer_polys(4, "huc8,name", "wbd_huc8_mi.json")

    def one(m):
        try:
            rings = bounds[m["geoid"]]
            return m["geoid"], {"water": _water_systems(rings), "watershed": _watersheds(rings, m["lat"], m["lon"], h12, h8)}
        except Exception as e:
            return m["geoid"], {"error": str(e)[:200]}

    with cf.ThreadPoolExecutor(workers) as ex:
        for i, (gid, res) in enumerate(ex.map(one, todo), 1):
            cache[gid] = res
            if i % 100 == 0:
                json.dump(cache, open(path, "w"))
                print("enriched", i, "of", len(todo))
    json.dump(cache, open(path, "w"))
    return cache


def county_design_storms(cnties):
    """NOAA Atlas 14 24-hour depths (2-, 10-, 100-year) at each county's internal point."""
    out = {}
    for c in cnties:
        pf, meta = atlas14_depths(c["lat"], c["lon"], f"county_{c['geoid']}")
        out[c["geoid"]] = {k: pf["24-hr"][k] for k in (2, 10, 100)}
    return out
