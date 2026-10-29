"""Places in any state from the Census Bureau (TIGERweb), for the national tier (design 0001, decision 6; design 0002).

A state's places are the units that decide land use:
  incorporated places    cities, towns, villages and boroughs (FUNCSTAT A)
  county subdivisions    only those the Census marks as active governments (FUNCSTAT A): the townships and towns of the
                         roughly 20 states that have them. Fictitious subdivisions (F) that repeat a city are skipped, as
                         are statistical (S) and nonfunctioning (N) ones such as Texas census county divisions and
                         Virginia magisterial districts.
  counties               every county, standing for the unincorporated land it governs. Independent cities (Virginia's,
                         Baltimore, St. Louis, Carson City) are county-equivalents too; they are listed once, as cities,
                         and still used to assign counties.

Each comes with its Census GEOID (7 digits for places, 10 for subdivisions, 5 for counties), name, kind (from the Census
name, e.g. "city", "charter township", "County"), internal point, county, and a generalized boundary. Responses are
cached under <cache>/census/.
"""
import json, os

import geopandas as gpd
import shapely

from waterledger_data.config import CACHE
from waterledger_data.places import TIGER, _get

RAW = os.path.join(CACHE, "census")
LAYERS = {"place": f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/4/query",
          "cousub": f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/1/query",
          "county": f"{TIGER}/State_County/MapServer/1/query"}
SIMPLIFY_DEG = 0.0003           # about 30 m: enough for joins with water systems and watersheds


def _features(kind, state_fips):
    """Every active feature of one layer in a state, with geometry in WGS84, paged and cached."""
    path = os.path.join(RAW, f"{state_fips}_{kind}.json")
    if os.path.exists(path):
        return json.load(open(path))
    where = f"STATE='{state_fips}'" + ("" if kind == "county" else " AND FUNCSTAT='A'")
    out, offset = [], 0
    while True:
        d = _get(LAYERS[kind], {"where": where, "outFields": "GEOID,NAME,BASENAME,LSADC,FUNCSTAT,INTPTLAT,INTPTLON",
                                "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": SIMPLIFY_DEG, "geometryPrecision": 5,
                                "resultOffset": offset, "resultRecordCount": 500, "orderByFields": "GEOID", "f": "json"}, post=True)
        feats = d.get("features", [])
        out += [{"a": f["attributes"], "rings": f["geometry"]["rings"]} for f in feats if f.get("geometry")]
        if len(feats) < 500 and not d.get("exceededTransferLimit"):
            break
        offset += len(feats)
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def _polygon(rings):
    """Census rings as one shapely geometry, even-odd (holes and separate parts), cleaned of any self-intersection."""
    geom = None
    for r in rings:
        if len(r) >= 4:
            p = shapely.make_valid(shapely.Polygon(r))
            geom = p if geom is None else geom.symmetric_difference(p)
    return geom


def _kind(a):
    base, name = a["BASENAME"], a["NAME"]
    return name[len(base):].strip() if name.startswith(base) else name


def places(state_fips):
    """A state's places as a GeoDataFrame: geoid, name (as Census writes it), base, kind, level (place, township or county),
    county and county_fips (for places and townships, the county holding the internal point), lat, lon, geometry (WGS84)."""
    rows = []
    for kind in ("place", "cousub", "county"):
        for f in _features(kind, state_fips):
            a = f["a"]
            rows.append({"geoid": a["GEOID"], "name": a["NAME"], "base": a["BASENAME"], "kind": _kind(a),
                         "level": {"place": "place", "cousub": "township", "county": "county"}[kind],
                         "lat": float(a["INTPTLAT"]), "lon": float(a["INTPTLON"]), "geometry": _polygon(f["rings"])})
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    counties = g[g.level == "county"][["geoid", "base", "geometry"]].rename(columns={"geoid": "county_fips", "base": "county"})
    pts = gpd.GeoDataFrame(g[["geoid"]], geometry=gpd.points_from_xy(g.lon, g.lat), crs=4326)
    hit = gpd.sjoin(pts, counties, how="left", predicate="within").drop_duplicates("geoid").set_index("geoid")
    g["county"] = g.geoid.map(hit["county"])
    g["county_fips"] = g.geoid.map(hit["county_fips"])
    is_county = g.level == "county"
    g.loc[is_county, "county"] = g.loc[is_county, "base"]
    g.loc[is_county, "county_fips"] = g.loc[is_county, "geoid"]
    g = g[~(is_county & (g.kind.str.lower() == "city"))]          # independent cities: already listed as places
    return g.sort_values(["name", "county"]).reset_index(drop=True)
