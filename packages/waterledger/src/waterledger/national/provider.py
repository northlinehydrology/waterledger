"""The national provider: answers for any state from federal data (design 0002), through the state's data (design 0003):
its hosted snapshot, or a local build as the fallback (waterledger.national.data)."""

from waterledger.national.data import state_data

SYS_POP = 3300          # a "sizable" public water system serves more than this many people (as waterledger.scenario)
SEWER_KM = 10           # with no water system mapped, a large plant this close is assumed reachable (as waterledger.scenario)
PLANTS_KM, PLANTS_MAX = 40, 10


def _places(state):
    return state_data(state).places()


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


def context(state, place):
    """The national context for a place: jurisdiction, supply (EPA water systems), wastewater (CWNS and ECHO sewer plants),
    receiving waters (USGS watersheds; the downstream path with EPA ATTAINS impairments, across state lines), climate and energy."""
    from waterledger import context as cx
    from waterledger_data import wastewater as ww
    from waterledger_data.waters import LABELS
    sd = state_data(state)
    base = _places(state).set_index("geoid").base.get(place.geoid, place.name)
    sys_ = lambda w: cx.WaterSystem(pwsid=w["pwsid"], name=w["name"].title(), population=w.get("population"),
                                    connections=w.get("connections"), share_of_place=w.get("share"))
    mine = sd.systems_for(place.geoid)
    near, near_km = (None, None) if mine else sd.nearest_system(place.geoid)
    supply = cx.Supply(provider="national", sources=["epa_sa"], systems=[sys_(w) for w in mine],
                       nearest_system=sys_(near) if near else None, nearest_system_km=near_km)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["name"], design_mgd=q["design_mgd"], flow_mgd=q["flow_mgd"], km=round(q["km"], 1),
                            receiving_water=q["receiving"] or None, combined_sewer=q["cso"], lagoon=q["lagoon"])
              for q in ww.nearest(sd.plants(), place.lat, place.lon, base, km=PLANTS_KM)[:PLANTS_MAX]]
    sheds = sd.sheds_for(place.geoid)
    path = sd.downstream(sheds["h12"][0]["code"]) if sheds["h12"] else []
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
    sd = state_data(state)
    L, W = sd.loads(), sd.grid_water()
    out = []
    for u in en.ranked(sd.utilities_for(place.geoid), L):
        e = L.get(u["eia_id"]) or {}
        w = W.get(u["balancing_authority"]) or {}
        out.append(cx.Utility(name=u["name"].title(), type=(u["type"] or "").title(), share_of_place=u["share"], customers=e.get("customers"),
                              avg_mw=round(e["mwh"] / 8760, 1) if e.get("mwh") else None, summer_peak_mw=e.get("summer_mw"),
                              balancing_authority=u["balancing_authority"], power_plant_water_l_per_kwh=w.get("consumed_excl_hydro")))
    return cx.Energy(provider="national", sources=["hifld_territories", "eia861", "siddik2024"], utilities=out)


def _division(state, place):
    sd = state_data(state)
    runs = sd.division_runs()
    d = sd.division_of(place.county_fips)
    if d not in runs:                     # a county NOAA leaves out: the nearest division's station
        d = min(runs, key=lambda k: (runs[k]["lat"] - place.lat) ** 2 + (runs[k]["lon"] - place.lon) ** 2)
    return d, runs


def _climate(state, place):
    from waterledger import context as cx
    sd = state_data(state)
    d, runs = _division(state, place)
    return cx.Climate(provider="national", sources=["noaa_isd", "noaa_cag", "noaa_atlas14"], region=d, region_name=runs[d]["name"],
                      station=runs[d]["station"], rain_in=sd.rain().get(place.county_fips), design_storms_in=sd.storms().get(place.county_fips, {}))


def estimate(state, site):
    """Water use for a site anywhere: the cooling model at the place's climate division station, plus staff water, with the
    page's rules for the water source and wastewater (waterledger.scenario), on national data."""
    import datetime

    from waterledger import scenario as sc
    from waterledger.estimate import Estimate, Flow, Range, WaterUse
    from waterledger_models import MODEL_VERSION
    f, place = site.facility, site.place
    if f.cooling == "lake":
        raise ValueError("lake-source cooling is modeled for the Great Lakes only (Michigan); choose another design")
    sd = state_data(state)
    d, runs = _division(state, place)
    D = {"regions": runs, "staff": {"runs": sd.staff_runs()}}
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
    return Estimate(site=resolved, water=water, model_version=MODEL_VERSION, data_date=sd.date or datetime.date.today().isoformat())
