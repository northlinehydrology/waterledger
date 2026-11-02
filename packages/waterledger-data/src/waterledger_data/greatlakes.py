"""Which Great Lake a place is on, in any state: the nearest within SHORE_KM of the place's boundary, by true distance between the place's polygon and the lake's (Census boundaries;
Natural Earth 1:50m lakes, whose generalized shoreline is a kilometer or so out in places, well inside the 5 km allowed). Lake St. Clair counts as on the lakes, as it has since Michigan's first
build. A state with no shoreline simply finds none. Cached under <cache>/places/."""
import json, os

from waterledger_data.config import CACHE
from waterledger_data.fetching import save

URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_lakes.geojson"
ALBERS = 5070
SHORE_KM = 5.0
NAMES = {"Lake Superior": "Lake Superior", "Lake Michigan": "Lake Michigan", "Lake Huron": "Lake Huron", "Lake Erie": "Lake Erie", "Lake Ontario": "Lake Ontario", "Lake Saint Clair": "Lake St. Clair"}


def lakes():
    """The lakes as a GeoDataFrame in meters: name, geometry."""
    import geopandas as gpd
    path = os.path.join(CACHE, "places", "lakes50.json")
    save(URL, path)
    feats = [f for f in json.load(open(path))["features"] if f["properties"].get("name") in NAMES]
    g = gpd.GeoDataFrame.from_features(feats, crs=4326).to_crs(ALBERS)
    g["name"] = g["name"].map(NAMES)
    return g[["name", "geometry"]].dissolve("name").reset_index()


def near(places, shore_lakes=None):
    """{geoid: {"lake", "km"}} for the places (a GeoDataFrame with geoid and geometry) within SHORE_KM of a Great Lake. On two lakes at once, the nearer; level, the first by name."""
    import geopandas as gpd
    import shapely
    L = lakes() if shore_lakes is None else shore_lakes
    pl = places[["geoid", "geometry"]].dropna(subset=["geometry"]).to_crs(ALBERS)
    pl["geometry"] = shapely.make_valid(pl.geometry.values)
    hits = gpd.sjoin(pl, L.assign(geometry=L.buffer(SHORE_KM * 1000)), how="inner", predicate="intersects")
    out = {}
    for r in hits.sort_values("name").itertuples():
        km = float(shapely.distance(pl.geometry.loc[r.Index], L.geometry.iloc[r.index_right])) / 1000
        if km <= SHORE_KM and (r.geoid not in out or km < out[r.geoid]["km"]):
            out[r.geoid] = {"lake": r.name, "km": round(km, 1)}
    return out
