"""The national provider: answers for any state from federal data (design 0002). Each function takes the state it
answers for; the parts not built yet say which step of design 0002 brings them."""
import functools

from waterledger import states

STEPS = {}


class NotYet(NotImplementedError):
    """A national-tier part that is still being built."""


def _not_yet(part, state):
    raise NotYet(f"{state}: the national tier's {part} is not built yet; it comes in design 0002 {STEPS[part]}. Michigan is available now.")


@functools.lru_cache(maxsize=8)
def _places(state):
    from waterledger_data import census
    return census.places(next(f for f, s in states.FIPS.items() if s == state))


def _display(r):
    """How a place is written: cities, towns and villages by name, townships and counties with their kind."""
    return r["base"] if r["level"] == "place" else f"{r['base']} {r['kind'].title()}" if r["level"] == "township" else r["name"]


def find(state, name, county=None):
    """GEOID of a place by name ("Columbus city", "Columbus", "Loudoun County"), optionally within a county."""
    g = _places(state)
    n = name.lower().strip()
    if county:
        g = g[g.county.str.lower() == county.lower().replace(" county", "").strip()]
    exact = g[(g.name.str.lower() == n) | (g.base.str.lower() == n)]
    hits = exact if len(exact) else g[g.name.str.lower().str.startswith(n)]
    if len(hits) == 1:
        return hits.iloc[0].geoid
    opts = [f"{r.name} ({r.county} County)" for r in hits.head(6).itertuples()]
    raise KeyError(f"{name!r} in {state} matches {opts or 'nothing'}; give the full name (e.g. 'Columbus city'), a county, or the GEOID")


def place(state, geoid):
    from waterledger.place import Place
    g = _places(state)
    hit = g[g.geoid == str(geoid)]
    if not len(hit):
        raise KeyError(f"no {state} place with GEOID {geoid}")
    r = hit.iloc[0]
    return Place(geoid=r.geoid, name=_display(r), kind=r.kind.lower(), state=state, county=r.county, county_fips=r.county_fips,
                 lat=round(float(r.lat), 4), lon=round(float(r.lon), 4))


SYS_POP = 3300          # a "sizable" public water system serves more than this many people (as waterledger.scenario)
PLANTS_KM, PLANTS_MAX, DOWNSTREAM_HOPS = 40, 10, 25       # the downstream path lists up to 25 HUC12s, as Michigan's does


def context(state, place):
    """The national context for a place: jurisdiction, supply (EPA water systems), wastewater (CWNS and ECHO sewer plants),
    receiving waters (USGS watersheds; the downstream path with EPA ATTAINS impairments, across state lines). Climate and
    energy come in design 0002 steps 4 and 5."""
    import geopandas as gpd

    from waterledger import context as cx
    from waterledger_data import receiving as rc
    from waterledger_data import supply as sp
    from waterledger_data import wastewater as ww
    from waterledger_data.waters import LABELS
    pl = _places(state)
    r = pl[pl.geoid == place.geoid].iloc[0]
    sys_ = lambda w: cx.WaterSystem(pwsid=w["pwsid"], name=w["name"].title(), population=w.get("population"),
                                    connections=w.get("connections"), share_of_place=w.get("share"))
    mine = sp.systems_by_place(state, pl).get(place.geoid, [])
    near, near_km = None, None
    if not mine:                                    # the nearest sizable system, edge to edge
        sy = sp.water_systems(state)
        sy = sy[sy.population > SYS_POP].to_crs(sp.ALBERS)
        pt = gpd.GeoSeries(gpd.points_from_xy([place.lon], [place.lat]), crs=4326).to_crs(sp.ALBERS).iloc[0]
        if len(sy):
            d = sy.distance(pt)
            i = d.idxmin()
            near = sys_({"pwsid": sy.pwsid[i], "name": sy.name[i], "population": int(sy.population[i]), "connections": int(sy.connections[i] or 0)})
            near_km = round(float(d[i]) / 1000, 1)
    supply = cx.Supply(provider="national", sources=["epa_sa"], systems=[sys_(w) for w in mine], nearest_system=near, nearest_system_km=near_km)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["name"], design_mgd=q["design_mgd"], flow_mgd=q["flow_mgd"], km=round(q["km"], 1),
                            receiving_water=q["receiving"] or None, combined_sewer=q["cso"], lagoon=q["lagoon"])
              for q in ww.nearest(ww.plants(state), place.lat, place.lon, r.base, km=PLANTS_KM)[:PLANTS_MAX]]
    sheds = rc.watersheds_by_place(state, pl).get(place.geoid, {"h12": [], "h8": None})
    path = rc.downstream(sheds["h12"][0]["code"], hops=DOWNSTREAM_HOPS - 1) if sheds["h12"] else []   # the start and 24 more
    receiving = cx.Receiving(provider="national", sources=["usgs_wbd", "attains"],
                             watersheds=[cx.Watershed(huc12=w["code"], name=w["name"], share_of_place=w["share"]) for w in sheds["h12"]],
                             basin=cx.Watershed(huc12=sheds["h8"]["code"], name=sheds["h8"]["name"]) if sheds["h8"] else None,
                             downstream=[cx.Reach(huc12=p["code"], name=p["name"], impairments=[LABELS[g] for g, _, _ in p["listings"]],
                                                  tmdl=[LABELS[g] for g, t, _ in p["listings"] if t]) for p in path])
    jur = cx.Jurisdiction(provider="national", sources=["census_tiger"], name=place.name, kind=place.kind, county=place.county, state=state)
    return cx.Context(place=place, jurisdiction=jur, supply=supply,
                      wastewater=cx.Wastewater(provider="national", sources=["cwns2022", "echo"], plants=plants), receiving=receiving,
                      climate=_climate(state, place), energy=_energy(state, place))


def _energy(state, place):
    from waterledger import context as cx
    from waterledger_data import energy as en
    us = en.utilities_by_place(state, _places(state)).get(place.geoid, [])
    L, W = en.loads(state), en.grid_water()
    out = []
    for u in en.ranked(us, L):
        e = L.get(u["eia_id"]) or {}
        w = W.get(u["balancing_authority"]) or {}
        out.append(cx.Utility(name=u["name"].title(), type=(u["type"] or "").title(), share_of_place=u["share"], customers=e.get("customers"),
                              avg_mw=round(e["mwh"] / 8760, 1) if e.get("mwh") else None, summer_peak_mw=e.get("summer_mw"),
                              balancing_authority=u["balancing_authority"], power_plant_water_l_per_kwh=w.get("consumed_excl_hydro")))
    return cx.Energy(provider="national", sources=["hifld_territories", "eia861", "siddik2024"], utilities=out)


def _division(state, place):
    from waterledger.national import climate as nc
    from waterledger_data import divisions
    d = divisions.county_divisions().get(place.county_fips)
    runs = nc.division_runs(state)
    if d not in runs:                     # a county NOAA leaves out: the nearest division's station
        d = min(runs, key=lambda k: (runs[k]["lat"] - place.lat) ** 2 + (runs[k]["lon"] - place.lon) ** 2)
    return d, runs


def _climate(state, place):
    from waterledger import context as cx
    from waterledger.national import climate as nc
    d, runs = _division(state, place)
    storms, rain = nc.storms_and_rain(state)
    return cx.Climate(provider="national", sources=["noaa_isd", "noaa_cag", "noaa_atlas14"], region=d, region_name=runs[d]["name"],
                      station=runs[d]["station"], rain_in=rain.get(place.county_fips), design_storms_in=storms.get(place.county_fips, {}))


SEWER_KM = 10           # with no water system mapped, a large plant this close is assumed reachable (as waterledger.scenario)


def estimate(state, site):
    """Water use for a site anywhere: the cooling model at the place's climate division station, plus staff water, with the
    page's rules for the water source and wastewater (waterledger.scenario), on national data."""
    from waterledger import scenario as sc
    from waterledger.estimate import Estimate, Flow, Range, WaterUse
    from waterledger_models import MODEL_VERSION
    f, place = site.facility, site.place
    if f.cooling == "lake":
        raise ValueError("lake-source cooling is modeled for the Great Lakes only (Michigan); choose another design")
    d, runs = _division(state, place)
    D = {"regions": runs, "staff": {"runs": _staff_runs()}}
    ctx = place.context()
    src = site.source
    if src is None:
        reach = ctx.supply.nearest_system_km is not None and ctx.supply.nearest_system_km <= SEWER_KM
        src = "muni" if ctx.supply.systems or (reach and f.cooling not in ("towers", "hybrid")) else "wells"
    dest = site.wastewater
    if dest is None:
        sew = sc.cooling_estimate(D, d, f.cooling, f.it_mw, "sewer")["sewer"]["mid"]
        q = ctx.wastewater.plants[0] if ctx.wastewater.plants else None
        reach = q is not None and (bool(ctx.supply.systems) or q.km <= SEWER_KM)
        room = (q.design_mgd - q.flow_mgd) if q and q.design_mgd and q.flow_mgd else None
        evap = f.cooling in ("towers", "hybrid")
        why = "far" if not reach else "full" if evap and room is not None and sew > room else ""
        dest = ("water" if evap else "septic") if why else "sewer"
    E, R = sc.cooling_estimate(D, d, f.cooling, f.it_mw, dest), Range.from_band
    water = WaterUse(withdrawn=Flow(avg=R(E["wAvg"]), peak_day=R(E["wPeak"])), withdrawn_annual_mg=R(E["wAnn"]),
                     consumed=Flow(avg=R(E["cAvg"]), peak_day=R(E["cPeak"])), returned=Flow(avg=R(E["rAvg"]), peak_day=R(E["rPeak"])),
                     to_sewer=R(E["sewer"]), lake_source=False, reuse=E["reuse"])
    resolved = site.model_copy(update={"source": src, "wastewater": dest})
    import datetime
    return Estimate(site=resolved, water=water, model_version=MODEL_VERSION, data_date=datetime.date.today().isoformat())


@functools.lru_cache(maxsize=1)
def _staff_runs(n=200):
    from waterledger_models.datacenter import cooling as cw
    return cw.staff_runs(n)
