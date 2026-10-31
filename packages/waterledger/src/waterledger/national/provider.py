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
    use, usgs = county_water_use(state, place.county_fips)
    supply = cx.Supply(provider="national", sources=["epa_sa", *dict.fromkeys(u.source for u in (use, usgs) if u)], systems=[sys_(w) for w in mine],
                       nearest_system=sys_(near) if near else None, nearest_system_km=near_km,
                       county_use_mgd=use.mgd if use else {}, county_water_use=use, county_water_use_usgs=usgs)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["name"], design_mgd=q["design_mgd"], flow_mgd=q["flow_mgd"], km=q["km"],
                            own=q["own"], receiving_water=q["receiving"] or None, combined_sewer=q["cso"], lagoon=q["lagoon"])
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


def water_use_record(rec, basis, county_fips):
    """A CountyWaterUse from one county's record in a water-use layer and the layer's basis (waterledger_data.wateruse)."""
    from waterledger import context as cx
    return cx.CountyWaterUse(county=rec.get("name"), county_fips=county_fips, source=basis["source"], citation=basis["citation"],
                             url=basis.get("url"), year=basis["year"], kind=basis["kind"], measure=basis["measure"], units=basis["units"],
                             mgd=rec["mgd"], ground_mgd=rec.get("ground_mgd") or {}, surface_mgd=rec.get("surface_mgd") or {},
                             reuse_mgd=rec.get("reuse_mgd") or {}, delivered_to_homes_mgd=rec.get("delivered_to_homes_mgd"),
                             threshold=basis.get("threshold"), categories=basis.get("categories") or {}, caveats=basis.get("caveats") or [])


def county_water_use(state, county_fips):
    """(the county's water use from the state's own source if it has one, else USGS's 2015 estimate; USGS's estimate), each
    a CountyWaterUse or None."""
    W = state_data(state).water_use() or {}
    got = {}
    for k in ("state", "national"):
        layer = W.get(k)
        if layer and county_fips in layer["counties"]:
            got[k] = water_use_record(layer["counties"][county_fips], layer["basis"], county_fips)
    usgs = got.get("national")
    return got.get("state") or usgs, usgs


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
                              avg_mw=e["mwh"] / 8760 if e.get("mwh") else None, summer_peak_mw=e.get("summer_mw"),
                              balancing_authority=u["balancing_authority"], power_plant_water_l_per_kwh=w.get("consumed_excl_hydro")))
    return cx.Energy(provider="national", sources=["hifld_territories", "eia861", "siddik2024", "eia923_2024", "macknick2012"], utilities=out,
                     power_plant_water=_ppw(state))


def _ppw(state):
    from waterledger import context as cx
    from waterledger_data import energy as en
    w = en.state_power_water(state)
    return cx.PowerPlantWater(consumed_l_per_kwh=w["consumed"], consumed_range=(w["consumed_lo"], w["consumed_hi"]),
                              withdrawn_l_per_kwh=w["withdrawn"], withdrawn_range=(w["withdrawn_lo"], w["withdrawn_hi"]),
                              main_balancing_authority=w["main_ba"], import_share=w["import_share"]) if w else None


def reference(state, place):
    """A state's values to compare an estimate with: its power options, the starting one, a typical golf course at the place, and its homes' electricity
    (None from a snapshot written before 3.7.0)."""
    from waterledger.national import power
    from waterledger_data import wateruse
    sd = state_data(state)
    options = power.options(state, sd.grid_water())
    G, res = wateruse.golf(state), sd.residential() or {}
    return {"power_options": options, "power": "state_mix" if "state_mix" in options else next(iter(options)),
            "golf_gpd": G.get("by_region", {}).get(_division(state, place)[0], G["gpd"]) if G else None,
            "home_kwh_month": res.get("kwh_month"), "home_customers": res.get("customers")}


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
                      station=runs[d]["station"], rain_in=sd.rain().get(place.county_fips), rain_from=sd.rain_from().get(place.county_fips), design_storms_in=sd.storms().get(place.county_fips, {}))


def estimate(state, site):
    """Water use for a site anywhere: the cooling model at the place's climate division station, plus staff water, with the
    page's rules for the water source and wastewater (waterledger.scenario), on national data."""
    import datetime

    from waterledger import scenario as sc
    from waterledger.estimate import Estimate, electricity, water_use
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
    water = water_use(sc.cooling_estimate(D, d, f.cooling, f.it_mw, dest))
    resolved = site.model_copy(update={"source": src, "wastewater": dest})
    power = electricity(sc.electricity(D, d, f.cooling, f.it_mw))
    return Estimate(site=resolved, water=water, electricity=power, model_version=MODEL_VERSION, data_date=sd.date or datetime.date.today().isoformat())
