"""The national provider: answers for any state from federal data (design 0002), through the state's data (design 0003):
its hosted snapshot, or a local build as the fallback (waterledger.national.data)."""

import functools

from waterledger.national.data import state_data

SEWER_KM = 10           # with no water system mapped, a large plant this close is assumed reachable (as waterledger.scenario)
PLANTS_KM, PLANTS_MAX = 40, 10
UTILITY_KM = 50         # with no utility territory over a place, the nearest place that has one within this distance stands in [A]


def _places(state):
    return state_data(state).places()


def geoids(state):
    """Every place in the state, by Census ID."""
    return [str(g) for g in _places(state).geoid]


def shore_geoids(state):
    """The places within about 5 km of a Great Lake (none in a snapshot from before 3.9.0)."""
    sd = state_data(state)
    return [g for g in geoids(state) if sd.great_lake(g)]


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
    return Place(geoid=r.geoid, name=_display(r), kind=r.kind.lower(), level=r.level, state=state, county=r.county, county_fips=r.county_fips,
                 lat=round(float(r.lat), 4), lon=round(float(r.lon), 4))


def serves(systems):
    """Whether any of a place's systems ({"share": ...}) covers enough of it to be taken as there (supply.SERVES_SHARE)."""
    from waterledger_data.supply import SERVES_SHARE
    return any((w.get("share") or 0) >= SERVES_SHARE for w in systems)


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
    near, near_km = (None, None) if serves(mine) else sd.nearest_system(place.geoid)
    use, usgs = county_water_use(state, place.county_fips)
    supply = cx.Supply(provider="national", not_covered=["household_wells"], sources=["epa_sa", *dict.fromkeys(u.source for u in (use, usgs) if u)], systems=[sys_(w) for w in mine],
                       nearest_system=sys_(near) if near else None, nearest_system_km=near_km,
                       county_use_mgd=use.mgd if use else {}, county_water_use=use, county_water_use_usgs=usgs)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["name"], design_mgd=q["design_mgd"], flow_mgd=q["flow_mgd"], km=q["km"],
                            own=q["own"], system=q["system"], receiving_water=q["receiving"] or None, combined_sewer=q["cso"], lagoon=q["lagoon"])
              for q in ww.nearest(sd.plants(), place.lat, place.lon, base, km=PLANTS_KM, township="township" in place.name.lower(), system=ww.main_system(mine))[:PLANTS_MAX]]
    sheds = sd.sheds_for(place.geoid)
    shore = sd.great_lake(place.geoid)
    path = sd.downstream(sheds["h12"][0]["code"]) if sheds["h12"] else []
    receiving = cx.Receiving(provider="national", not_covered=["coldwater_streams"], sources=["usgs_wbd", "attains"],
                             watersheds=[cx.Watershed(huc12=w["code"], name=w["name"], share_of_place=w["share"]) for w in sheds["h12"]],
                             basin=cx.Watershed(huc12=sheds["h8"]["code"], name=sheds["h8"]["name"]) if sheds["h8"] else None,
                             great_lake=shore["lake"] if shore else None, great_lakes_basin=sheds["h12"][0]["code"].startswith("04") if sheds["h12"] else None,
                             downstream=[cx.Reach(huc12=p["code"], name=p["name"], impairments=[LABELS[g] for g, _, _ in p["listings"]],
                                                  tmdl=[LABELS[g] for g, t, _ in p["listings"] if t], assessed=p.get("assessed")) for p in path])
    jur = cx.Jurisdiction(provider="national", not_covered=["rules"], sources=["census_tiger"], name=place.name, kind=place.kind, county=place.county, state=state)
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
    pl = sd.places()
    row = pl[pl.geoid == place.geoid]
    own = {"base": row.base.iloc[0], "km2": float(row.to_crs(en.ALBERS).geometry.area.iloc[0]) / 1e6} if len(row) and "base" in row else None
    def utility(u):
        e = L.get(u["eia_id"]) or {}
        w = W.get(u["balancing_authority"]) or {}
        return cx.Utility(name=u["name"].title(), type=(u["type"] or "").title(), share_of_place=u["share"], customers=e.get("customers"),
                          avg_mw=e["mwh"] / 8760 if e.get("mwh") else None, summer_peak_mw=e.get("summer_mw"),
                          balancing_authority=u["balancing_authority"], power_plant_water_l_per_kwh=w.get("consumed_excl_hydro"))
    out = [utility(u) for u in en.ranked(sd.utilities_for(place.geoid), L, own)]
    near, near_km, near_out = None, None, []
    if not out:
        near, near_km = nearest_served(state, place.geoid)
        if near:
            near_out = [utility(u) for u in en.ranked(sd.utilities_for(near), L, None)]
            near = pl.set_index("geoid").name.get(near, near)
    return cx.Energy(provider="national", sources=["hifld_territories", "eia861", "siddik2024", "eia923_2024", "macknick2012"], utilities=out,
                     nearest_place=near, nearest_place_km=near_km, nearest_utilities=near_out, power_plant_water=_ppw(state))


@functools.lru_cache(maxsize=16)
def _served(state):
    """The state's places that a utility territory covers, as one frame in an equal-area projection."""
    from waterledger_data import energy as en
    sd = state_data(state)
    pl = sd.places()
    return pl[[bool(sd.utilities_for(g)) for g in pl.geoid]][["geoid", "geometry"]].to_crs(en.ALBERS)


def nearest_served(state, geoid):
    """(geoid, km) of the nearest place a utility territory covers, edge to edge, for a place none covers, within UTILITY_KM; (None, None)
    otherwise. The national territory layer leaves a few places out (Virginia's independent cities and some of its towns, islands)."""
    from waterledger_data import energy as en
    pl = state_data(state).places()
    row = pl[pl.geoid == geoid]
    if not len(row):
        return None, None
    served = _served(state)
    if not len(served):
        return None, None
    d = served.distance(row.to_crs(en.ALBERS).geometry.iloc[0]) / 1000.0
    i = d.idxmin()
    return (str(served.geoid[i]), round(float(d[i]), 1)) if d[i] <= UTILITY_KM else (None, None)


def _ppw(state):
    from waterledger import context as cx
    from waterledger_data import energy as en
    w = en.state_power_water(state)
    return cx.PowerPlantWater(consumed_l_per_kwh=w["consumed"], consumed_range=(w["consumed_lo"], w["consumed_hi"]),
                              withdrawn_l_per_kwh=w["withdrawn"], withdrawn_range=(w["withdrawn_lo"], w["withdrawn_hi"]),
                              withdrawn_fresh_l_per_kwh=w["withdrawn_fresh"], withdrawn_saline_l_per_kwh=w["withdrawn_saline"],
                              main_balancing_authority=w["main_ba"], import_share=w["import_share"]) if w else None


# Where a state's rules aren't reviewed there are no lines for well pumping. The Compact's 5 MGD belongs to the eight Great Lakes states and is used only for a place on the lakes or in their basin.
WITHDRAWALS = {"compact_use_mgd": 5.0}
NOT_COVERED = {"state_rules": "This state's water rules are not yet reviewed, so no legal line or level is shown."}


def home_gpd(state):
    """A state's water for a home, gallons a day, from the USGS layer its data carries; None without one (a snapshot from before water use was added)."""
    from waterledger_data import wateruse
    layer = (state_data(state).water_use() or {}).get("national")
    return wateruse.home_gpd(state, layer) if layer else None


def reference(state, place):
    """A state's values to compare an estimate with: its power options, the starting one, a typical golf course at the place, and its homes' electricity
    (None from a snapshot written before 3.7.0)."""
    from waterledger.national import power
    from waterledger_data import wateruse
    from waterledger_models import runoff as rq
    sd = state_data(state)
    options = power.options(state, sd.grid_water())
    G, res = wateruse.golf(state), sd.residential() or {}
    from waterledger.comparisons import default_power
    return {"power_options": options, "power": default_power(options, "state_mix" if "state_mix" in options else next(iter(options)), (lambda e: e.utilities or e.nearest_utilities)(place.context().energy)),
            "golf_gpd": G.get("by_region", {}).get(_division(state, place)[0], G["gpd"]), "golf_basis": G["basis"], "golf_note": G["note"],
            "home_gpd": home_gpd(state), "home_kwh_month": res.get("kwh_month"), "home_customers": res.get("customers"), "state_avg_mw": sd.state_avg_mw(),
            "rain_median_in": rq.rain_median(sd.rain()), "salt_events": sd.salt_events().get(_division(state, place)[0]), "withdrawals": WITHDRAWALS, "state_rules": False, "not_covered": NOT_COVERED}


def _division(state, place):
    sd = state_data(state)
    runs = sd.division_runs()
    d = sd.division_of(place.county_fips)
    if d not in runs:                     # a county NOAA leaves out: the nearest division's station
        d = min(runs, key=lambda k: (runs[k]["lat"] - place.lat) ** 2 + (runs[k]["lon"] - place.lon) ** 2)
    return d, runs


def _cooling(state, place):
    """(region, {region: results}) for an estimate's cooling: the place's ERA5 cell in a format 3 snapshot (model 1.8, design 0004), its
    climate division's station before. Rainfall, salt and golf stay by division in both."""
    sd = state_data(state)
    if sd.format() < 3:
        return _division(state, place)
    c = sd.cell_of(place.geoid)
    if c is None:
        raise ValueError(f"{state}'s data has no ERA5 cell for {place.name} ({place.geoid})")
    return c["cell"], {c["cell"]: sd.cell(c["cell"])}


def _climate(state, place):
    from waterledger import context as cx
    sd = state_data(state)
    d, runs = _division(state, place)
    cell = sd.cell_of(place.geoid) if sd.format() >= 3 else None
    extra = {} if cell is None else {k: cell[k] for k in ("cell", "cell_km", "cell_land", "cell_moved", "weather_corrected")}
    return cx.Climate(provider="national", sources=["noaa_isd", "noaa_cag", "noaa_atlas14", *(["era5"] if cell else [])], region=d, region_name=runs[d]["name"],
                      station=runs[d]["station"], rain_in=sd.rain().get(place.county_fips), rain_from=sd.rain_from().get(place.county_fips), design_storms_in=sd.storms().get(place.county_fips, {}),
                      **extra)


def default_source(ctx, evaporative):
    """Where a large water user's water most likely comes from [A], in every state (the page's WQ.srcFor, on a place's Context): a system EPA maps
    in the place; with none mapped, a sizable system within SEWER_KM for a design that isn't evaporative (it extends its pipes), new wells for an
    evaporative one, which avoid a utility's peak-day limits; nothing within reach, new wells. `evaporative`: the design is in the type's EVAPORATIVE."""
    mapped = serves([{"share": w.share_of_place} for w in ctx.supply.systems])
    reach = ctx.supply.nearest_system_km is not None and ctx.supply.nearest_system_km <= SEWER_KM
    return "muni" if mapped or (reach and not evaporative) else "wells"


def default_wastewater(ctx, evaporative, sewer_mgd, far=None):
    """Where its wastewater most likely goes [A], in every state (the page's WQ.destFor, on a place's Context): the sewer when a public water system is
    mapped in the place or the first sewer plant is within SEWER_KM, and for an evaporative design only if `sewer_mgd()` (the middle estimate to the
    sewer, called only when needed) fits in the plant's spare design flow. Otherwise `far`: by default an evaporative design's own discharge to
    a river or lake and a septic system for the rest."""
    mapped = serves([{"share": w.share_of_place} for w in ctx.supply.systems])
    q = ctx.wastewater.plants[0] if ctx.wastewater.plants else None
    reach = q is not None and (mapped or q.km <= SEWER_KM)
    room = (q.design_mgd - q.flow_mgd) if q and q.design_mgd and q.flow_mgd else None
    why = "far" if not reach else "full" if evaporative and room is not None and sewer_mgd() > room else ""
    return (far or ("water" if evaporative else "septic")) if why else "sewer"


def estimate(state, site):
    """Water use for a site anywhere: the cooling model at the place's ERA5 cell (format 3) or climate division station (format 2), plus staff water, or lake-source cooling on a Great Lake within about 5 km, with the
    page's rules for the water source and wastewater (waterledger.scenario), on national data."""
    import datetime

    from waterledger import scenario as sc
    from waterledger.estimate import Estimate, electricity, grid_water, water_use
    f, place = site.facility, site.place
    sd = state_data(state)
    d, runs = _cooling(state, place)
    D = {"regions": {**runs, d: sc.for_plant(runs[d], f.plant)}, "staff": {"runs": sd.staff_runs()}, "lake_source": sd.lake_source()}
    ctx = place.context()
    lake = ctx.receiving.great_lake
    src = site.source
    sc.check_lake(place.name, lake, f.cooling, src)
    if f.cooling == "lake" and lake not in D["lake_source"]:
        raise ValueError(f"{state}'s data has no lake-source results for {lake} (a snapshot from before 3.9.0)")
    flows = lambda dest: sc.lake_estimate(D, lake, d, f.it_mw, dest) if f.cooling == "lake" else sc.cooling_estimate(D, d, f.cooling, f.it_mw, dest)
    evap = f.cooling in f.EVAPORATIVE
    if src is None:
        src = default_source(ctx, evap)
    dest = site.wastewater
    if dest is None:
        dest = default_wastewater(ctx, evap, lambda: flows("sewer")["sewer"]["mid"])
    water = water_use(flows(dest))
    acres, before = sc.land_default(place.incorporated)
    resolved = site.model_copy(update={"source": src, "wastewater": dest, "acres": site.acres or acres, "land_before": site.land_before or before})
    power = electricity(sc.electricity(D, d, f.cooling, f.it_mw))
    ba = place_ba(ctx)
    grid = grid_water(sc.grid_water(D, d, f.cooling, f.it_mw, ba), ba)
    return Estimate(site=resolved, water=water, electricity=power, grid_water=grid, model_version=sd.model_version(), data_date=sd.date or datetime.date.today().isoformat())


def place_ba(ctx):
    """The place's balancing authority: its first utility's (the place's own first, then by area; energy.ranked), else the nearest served
    place's where no territory covers it (nearest_served), or None."""
    energy = getattr(ctx, "energy", None)
    if not energy:
        return None
    return next((u.balancing_authority for u in (energy.utilities or energy.nearest_utilities) if u.balancing_authority), None)
