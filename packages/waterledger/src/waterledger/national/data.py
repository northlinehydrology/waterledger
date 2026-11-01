"""Where the national tier's data comes from (design 0003): a state's hosted snapshot first, a local build as the fallback.

    state_data("OH")          -> SnapshotData (data.waterledger.org, verified and cached) or, if that can't be reached,
                                 LiveData (built here from the public sources), as the fallback setting allows

Settings (arguments to state_data, or environment variables):
    fallback   WATERLEDGER_FALLBACK   "ask" (the default when someone is at the keyboard), "build", or "fail" (the default
                                      in scripts and CI)
    source     WATERLEDGER_DATA       "snapshot" (default) or "live" (skip snapshots; build from the public sources)
    date       WATERLEDGER_DATA_DATE  a snapshot date to pin, for reproducing an old result (default: the latest)
    url        WATERLEDGER_DATA_URL   where snapshots live (default https://data.waterledger.org)

Both kinds answer the same questions, so the provider doesn't care which it has.
"""
import functools, hashlib, json, math, os, re, sys, urllib.request

from waterledger import states

DATA_URL = "https://data.waterledger.org"
BUILD_MINUTES = "15 to 30"
SYS_POP = 3300            # a "sizable" public water system serves more than this many people (as waterledger.scenario)
FILES = ("places.json", "places.parquet", "supply.json", "wastewater.json", "receiving.json", "climate.json", "energy.json", "wateruse.json")


class DataUnavailable(RuntimeError):
    """A state's data could not be had: no snapshot reachable, and building locally was not allowed or failed."""


def _fips(state):
    return next(f for f, s in states.FIPS.items() if s == state)


def _km(a_lat, a_lon, b_lat, b_lon):
    dlat, dlon = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


class SnapshotData:
    """A state's data from its snapshot folder (manifest checked)."""

    def __init__(self, state, folder):
        self.state, self.folder = state, folder
        self.manifest = json.load(open(os.path.join(folder, "manifest.json")))
        self.date = self.manifest["date"]
        self._j = {}

    def _json(self, name):
        if name not in self._j:
            self._j[name] = json.load(open(os.path.join(self.folder, name + ".json")))
        return self._j[name]

    @functools.cached_property
    def _places(self):
        import geopandas as gpd
        return gpd.read_parquet(os.path.join(self.folder, "places.parquet"))

    def places(self):
        return self._places

    def division_of(self, county_fips):
        return {p["county_fips"]: p["division"] for p in self._json("places")["places"]}.get(county_fips)

    def systems_for(self, geoid):
        S = self._json("supply")
        return [{"pwsid": p, **S["systems"][p], "share": sh} for p, sh in S["by_place"].get(geoid, [])]

    def nearest_system(self, geoid):
        n = self._json("supply").get("nearest", {}).get(geoid)
        return ({"pwsid": n[0], **self._json("supply")["systems"][n[0]]}, n[1]) if n else (None, None)

    def plants(self):
        return self._json("wastewater")["plants"]

    def sheds_for(self, geoid):
        return self._json("receiving")["by_place"].get(geoid, {"h12": [], "h8": None})

    def downstream(self, huc12):
        R = self._json("receiving")
        return [{"code": c, "name": R["reaches"][c]["n"], "listings": R["reaches"][c]["i"], "assessed": bool(R["reaches"][c]["a"]) if "a" in R["reaches"][c] else None}
                for c in R["downstream"].get(huc12, []) if c in R["reaches"]]

    def division_runs(self):
        return self._json("climate")["divisions"]

    def staff_runs(self):
        return self._json("climate")["staff_runs"]

    def storms(self):
        return self._json("climate")["design_storms_in"]

    def rain(self):
        return self._json("climate")["rain_in"]

    def rain_from(self):
        """{independent city FIPS: the surrounding county's name}, where NOAA has no record for the city; empty in a snapshot from before 3.7.0."""
        return self._json("climate").get("rain_from", {})

    def salt_events(self):
        """{division: [lo, mid, hi] road salt events a winter}; empty in a snapshot from before 3.7.0, when Michigan's assumption stands in."""
        return self._json("climate").get("salt_events", {})

    def residential(self):
        """The state's residential electricity {"customers", "mwh", "kwh_month"} (EIA-861); None in a snapshot from before 3.7.0."""
        return self._json("energy").get("residential")

    def state_avg_mw(self):
        """The state's retail electricity sales over 8,760 hours, MW (EIA-861); None in a snapshot from before 3.7.0."""
        mwh = self._json("energy").get("state_retail_mwh")
        return mwh / 8760 if mwh else None

    def utilities_for(self, geoid):
        return self._json("energy")["by_place"].get(geoid, [])

    def loads(self):
        return {int(k): v for k, v in self._json("energy")["loads"].items()}

    def grid_water(self):
        return self._json("energy")["grid_water"]

    def water_use(self):
        """{"national": USGS layer, "state": the state's own layer or None}, each {"basis", "counties"}; None for a snapshot
        written before water use was added (format 1)."""
        if "wateruse.json" not in self.manifest.get("files", {}):
            return None
        return self._json("wateruse")


class LiveData:
    """A state's data built here from the public sources (each layer cached as it finishes, so a stopped build resumes)."""

    def __init__(self, state):
        self.state, self.date = state, None

    @functools.cached_property
    def _pl(self):
        from waterledger_data import census
        return census.places(_fips(self.state))

    def places(self):
        return self._pl

    def division_of(self, county_fips):
        from waterledger_data import divisions
        return divisions.county_divisions().get(county_fips)

    def systems_for(self, geoid):
        from waterledger_data import supply
        return supply.systems_by_place(self.state, self._pl).get(geoid, [])

    @functools.cached_property
    def _sizable(self):
        from waterledger_data import supply
        sy = supply.water_systems(self.state)
        return sy[sy.population > SYS_POP].to_crs(supply.ALBERS).reset_index(drop=True)

    def nearest_systems(self, geoids):
        """{geoid: (system, km)} for many places at once: the nearest sizable system to each place's point, edge to edge."""
        import geopandas as gpd

        from waterledger_data import supply
        sy = self._sizable
        if not len(sy):
            return {}
        pl = self._pl[self._pl.geoid.isin(list(geoids))]
        pts = gpd.GeoDataFrame({"geoid": pl.geoid.values}, geometry=gpd.points_from_xy(pl.lon, pl.lat), crs=4326).to_crs(supply.ALBERS)
        hit = gpd.sjoin_nearest(pts, sy, how="left", distance_col="m").drop_duplicates("geoid")
        return {r.geoid: ({"pwsid": r.pwsid, "name": r.name, "population": int(r.population), "connections": int(r.connections or 0)},
                          round(float(r.m) / 1000, 1)) for r in hit.itertuples()}

    def nearest_system(self, geoid):
        return self.nearest_systems([geoid]).get(geoid, (None, None))

    def plants(self):
        from waterledger_data import wastewater
        return wastewater.plants(self.state)

    def sheds_for(self, geoid):
        from waterledger_data import receiving
        return receiving.watersheds_by_place(self.state, self._pl).get(geoid, {"h12": [], "h8": None})

    def downstream(self, huc12):
        """The same path a snapshot stores: the state's own watershed links, and the tracer past the state line."""
        from waterledger.national.snapshot import _downstream
        paths, reaches = _downstream(self.state, [huc12])
        return [{"code": c, "name": reaches[c]["n"], "listings": reaches[c]["i"], "assessed": bool(reaches[c]["a"])} for c in paths[huc12] if c in reaches]

    def division_runs(self):
        from waterledger.national import climate as nc
        return nc.division_runs(self.state)

    def staff_runs(self):
        from waterledger_models.datacenter import cooling as cw
        return cw.staff_runs(200)

    def storms(self):
        from waterledger.national import climate as nc
        return nc.storms_and_rain(self.state)[0]

    def rain(self):
        from waterledger.national import climate as nc
        return nc.storms_and_rain(self.state)[1]

    def utilities_for(self, geoid):
        from waterledger_data import energy
        return energy.utilities_by_place(self.state, self._pl).get(geoid, [])

    def loads(self):
        from waterledger_data import energy
        return energy.loads(self.state)

    def grid_water(self):
        """The grid regions serving the state, as a snapshot stores them."""
        from waterledger_data import energy
        bas = {u["balancing_authority"] for v in energy.utilities_by_place(self.state, self._pl).values() for u in v if u["balancing_authority"]}
        return {b: w for b, w in energy.grid_water().items() if b in bas}

    def rain_from(self):
        from waterledger.national import climate as nc
        return nc.rain_from(self.state)

    @functools.cached_property
    def _salt_events(self):
        from waterledger.national import climate as nc
        return nc.salt_events(self.division_runs())

    def salt_events(self):
        return self._salt_events

    @functools.cached_property
    def _residential(self):
        from waterledger_data import power as pw
        return pw.residential(self.state, pw.latest_eia861())

    def residential(self):
        return self._residential

    @functools.cached_property
    def _state_avg_mw(self):
        from waterledger_data import power as pw
        return pw.state_retail_mwh(self.state, pw.latest_eia861()) / 8760

    def state_avg_mw(self):
        return self._state_avg_mw

    @functools.cached_property
    def _water_use(self):
        """Both water-use layers; a layer whose source can't be had is left out (None) with a note, as design 0003 asks."""
        from waterledger_data import wateruse
        out = {}
        for k, fn in (("national", lambda: wateruse.usgs_2015(self.state)), ("state", lambda: wateruse.state_layer(self.state))):
            try:
                out[k] = fn()
            except Exception as e:                       # noqa: BLE001  a source down: that layer is empty
                print(f"Water Ledger: {self.state} county water use ({k}) unavailable: {type(e).__name__}: {e}"[:300], file=sys.stderr)
                out[k] = None
        return out

    def water_use(self):
        return self._water_use


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "waterledger (python package)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_snapshot(state, date=None, url=None):
    """Download a state's snapshot (the latest, or `date`) into the cache, check every file against the manifest, and return
    its folder. A snapshot already cached and complete is used without downloading."""
    from waterledger_data.config import CACHE
    url = (url or os.environ.get("WATERLEDGER_DATA_URL") or DATA_URL).rstrip("/")
    date = date or os.environ.get("WATERLEDGER_DATA_DATE") or json.loads(_get(f"{url}/{state}/latest.json"))["latest"]
    folder = os.path.join(CACHE, "snapshots", state, date)
    os.makedirs(folder, exist_ok=True)
    mpath = os.path.join(folder, "manifest.json")
    try:                                    # always the published manifest (small), so a same-date republish is picked up
        open(mpath, "wb").write(_get(f"{url}/{state}/{date}/manifest.json"))
    except Exception:
        if not os.path.exists(mpath):
            raise
    manifest = json.load(open(mpath))
    for name, f in manifest["files"].items():
        path = os.path.join(folder, name)
        ok = os.path.exists(path) and hashlib.sha256(open(path, "rb").read()).hexdigest() == f["sha256"]
        if not ok:
            data = _get(f"{url}/{state}/{date}/{name}", timeout=300)
            if hashlib.sha256(data).hexdigest() != f["sha256"]:
                raise DataUnavailable(f"{state} snapshot {date}: {name} does not match its manifest checksum")
            os.makedirs(os.path.dirname(path), exist_ok=True)       # Michigan's site files sit in michigan/
            open(path, "wb").write(data)
    return folder


def _newest_cached(state):
    from waterledger_data.config import CACHE
    root = os.path.join(CACHE, "snapshots", state)
    dates = sorted(d for d in os.listdir(root) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)
                   and os.path.exists(os.path.join(root, d, "manifest.json"))) if os.path.isdir(root) else []
    for d in reversed(dates):
        m = json.load(open(os.path.join(root, d, "manifest.json")))
        if all(os.path.exists(os.path.join(root, d, n)) for n in m["files"]):
            return os.path.join(root, d)
    return None


@functools.lru_cache(maxsize=16)
def state_data(state, source=None, fallback=None, date=None):
    """The data for `state`: its snapshot, else (offline) the newest complete cached snapshot, else a local build as
    `fallback` allows ("ask", "build" or "fail")."""
    state = state.upper()
    source = source or os.environ.get("WATERLEDGER_DATA", "snapshot")
    if source == "live":
        return LiveData(state)
    try:
        return SnapshotData(state, fetch_snapshot(state, date))
    except Exception as e:                                  # noqa: BLE001  unreachable, missing or bad: decide below
        reason = f"{type(e).__name__}: {e}"[:200]
    cached = None if date else _newest_cached(state)
    if cached:
        print(f"Water Ledger: using the cached {state} snapshot from {os.path.basename(cached)} ({reason})", file=sys.stderr)
        return SnapshotData(state, cached)
    fallback = fallback or os.environ.get("WATERLEDGER_FALLBACK") or ("ask" if sys.stdin.isatty() else "fail")
    if fallback == "ask":
        ans = input(f"Water Ledger's data for {state} isn't reachable ({reason}).\nBuild it locally from the public sources instead? "
                    f"This takes about {BUILD_MINUTES} minutes the first time and is saved for later. [y/N] ")
        fallback = "build" if ans.strip().lower() in ("y", "yes") else "fail"
    if fallback == "build":
        from waterledger.national.build import build
        build(state)
        return LiveData(state)
    raise DataUnavailable(f"No data for {state}: {reason}. To build it locally from the public sources (about {BUILD_MINUTES} "
                          f"minutes, resumable), set WATERLEDGER_FALLBACK=build or pass fallback='build'.")
