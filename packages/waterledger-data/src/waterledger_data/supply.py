"""Public water systems in any state (national tier): EPA's Community Water System Service Area Boundaries (reported where
states supply them, modeled elsewhere), with population served and connections from SDWIS, joined to a state's places by
area. Cached under <cache>/supply/."""
import json, os

import geopandas as gpd
import shapely

from waterledger_data.config import CACHE
from waterledger_data.places import EPA_SA, _get

RAW = os.path.join(CACHE, "supply")
ALBERS = 5070                   # NAD83 / Conus Albers: equal-area, for shares of a place's area
MIN_SHARE = 0.005               # systems covering less than half a percent of a place are left out
SERVES_SHARE = 0.05             # [A] a system on 5% or more of a place is taken to be there; below that it is listed but the place counts as having none in reach. Michigan's sampled shares start at the same 5%
SYS_POP = 3300                  # [A] a "sizable" public water system serves more than this many people (EPA's medium size and up)


def water_systems(state):
    """A state's community water systems as a GeoDataFrame: pwsid, name, population, connections, geometry (WGS84)."""
    path = os.path.join(RAW, f"{state}_systems.json")
    if not os.path.exists(path):
        out, offset = [], 0
        while True:
            d = _get(EPA_SA, {"where": f"PWSID LIKE '{state}%'", "outFields": "PWSID,PWS_Name,Population_Served_Count,Service_Connections_Count",
                              "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.0003, "geometryPrecision": 5,
                              "resultOffset": offset, "resultRecordCount": 500, "orderByFields": "PWSID", "f": "json"}, post=True)
            feats = d.get("features", [])
            out += [{"a": f["attributes"], "rings": f["geometry"]["rings"]} for f in feats if f.get("geometry")]
            if len(feats) < 500 and not d.get("exceededTransferLimit"):
                break
            offset += len(feats)
        os.makedirs(RAW, exist_ok=True)
        json.dump(out, open(path, "w"))
    from waterledger_data.census import _polygon
    rows = [{"pwsid": f["a"]["PWSID"], "name": f["a"]["PWS_Name"], "population": f["a"]["Population_Served_Count"],
             "connections": f["a"]["Service_Connections_Count"], "geometry": _polygon(f["rings"])} for f in json.load(open(path))]
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    return g[g.geometry.notna() & ~g.geometry.is_empty].reset_index(drop=True)


def systems_by_place(state, places):
    """For each place (a GeoDataFrame from census.places), the water systems that cover part of it, the largest share first:
    {geoid: [{pwsid, name, population, connections, share}]}, share being the part of the place's area the system covers."""
    path = os.path.join(RAW, f"{state}_by_place.json")
    if os.path.exists(path):
        return json.load(open(path))
    sy = water_systems(state).to_crs(ALBERS)
    sy["geometry"] = shapely.make_valid(sy.geometry.values)          # reprojection can leave slivers invalid
    pl = places[["geoid", "geometry"]].to_crs(ALBERS)
    pl["geometry"] = shapely.make_valid(pl.geometry.values)
    pairs = gpd.sjoin(pl, sy, how="inner", predicate="intersects")
    geom_p = pl.set_index("geoid").geometry
    inter = shapely.intersection(geom_p.loc[pairs.geoid].values, sy.geometry.values[pairs.index_right.values])
    pairs["share"] = shapely.area(inter) / shapely.area(geom_p.loc[pairs.geoid].values)
    out = {}
    for r in pairs[pairs.share >= MIN_SHARE].sort_values(["share", "population", "pwsid"], ascending=False).itertuples():
        out.setdefault(r.geoid, []).append({"pwsid": r.pwsid, "name": r.name, "population": int(r.population or 0),
                                            "connections": int(r.connections or 0), "share": round(float(r.share), 3)})
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def nearest_sizable(state, points):
    """{geoid: ({pwsid, name, population, connections}, km)}, the nearest sizable system to each of `points` (a DataFrame with geoid, lat, lon), in every state: from the place's
    point to the edge of the system's service area, the length a pipe would have to run from the middle of the place, since where in the place a campus goes isn't known. 0 km where the point
    is inside a service area. Michigan measured from center to center, to the middle of a neighboring place a quarter or more covered by the system, which ran long beside a large township
    and missed a system on a place's edge [A]."""
    sy = water_systems(state)
    sy = sy[sy.population > SYS_POP].to_crs(ALBERS).reset_index(drop=True)
    if not len(sy):
        return {}
    pts = gpd.GeoDataFrame({"geoid": points.geoid.values}, geometry=gpd.points_from_xy(points.lon, points.lat), crs=4326).to_crs(ALBERS)
    hit = gpd.sjoin_nearest(pts, sy, how="left", distance_col="m").sort_values(["geoid", "population", "pwsid"], ascending=[True, False, True]).drop_duplicates("geoid")
    return {r.geoid: ({"pwsid": r.pwsid, "name": r.name, "population": int(r.population), "connections": int(r.connections or 0)}, round(float(r.m) / 1000, 1)) for r in hit.itertuples()}
