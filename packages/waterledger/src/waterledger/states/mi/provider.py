"""Michigan's provider: answers for Michigan places from Water Ledger Michigan's data files (the same ones waterledger.org/mi
reads), through waterledger.scenario, so the package and the page agree."""
from waterledger import scenario as sc
from waterledger.national.provider import PLANTS_MAX, home_gpd, water_use_record

# EGLE's groups on waterledger.org/mi -> the county water-use categories (waterledger_data.wateruse.CATEGORIES)
EGLE_CATS = {"Public water systems": "public_supply", "Industry": "industrial", "Bottled water": "industrial", "Farm irrigation": "irrigation",
             "Golf courses": "golf", "Livestock": "livestock", "Mining and dewatering": "mining", "Power plants": "thermoelectric", "Other": "other"}

# Median winter's days with precipitation at 1 C or below, by region, from NOAA ISD-Lite 2005-2024 (national.climate._median_cold_precip_days), the same method as every other state: Ann Arbor 725374-94889,
# Kalamazoo 726357-94815, Grand Rapids 726350-94860, Lansing 725390-14836, Saginaw 726379-14845, Traverse City 726387-14850, Alpena 726390-94849, and Hancock 727440-14858 for the Upper Peninsula:
# the regions' weather itself is Open-Meteo's best match, and Marquette's airports report no precipitation in ISD-Lite.
SALT_DAYS = {"southeast": 59, "southwest": 64, "west": 72, "central": 71, "thumb": 64, "north": 89, "northeast": 88, "up": 119}


def find(name, county=None):
    return sc.find(name, county)


def geoids():
    return [p["g"] for p in sc.data("places")["places"]]


def shore_geoids():
    return [p["g"] for p in sc.data("places")["places"] if p.get("gl")]


def place(geoid):
    from waterledger.place import Place
    r = sc.place(geoid)
    lon, lat = sc.lonlat(r)
    return Place(geoid=r["g"], name=r["base"], kind=r["k"], level="place" if r["k"] == "city" else "township", state="MI", county=r["c"], county_fips=r["cf"], lat=round(lat, 4), lon=round(lon, 4))


def estimate(site):
    """Water use for a site at a Michigan place, through waterledger.scenario (the page's est())."""
    from waterledger.estimate import Estimate, electricity, grid_water, water_use
    from waterledger.national.provider import place_ba
    f = site.facility
    S = sc.scenario(site.place.geoid, mw=f.it_mw, cool=f.cooling, src=site.source, dest=site.wastewater, acres=site.acres,
                    before=site.land_before, imp=site.impervious, plant=f.plant)
    water = water_use(S["E"])
    resolved = site.model_copy(update={"source": S["src"], "wastewater": S["dest"], "acres": S["acres"], "land_before": S["before"]})
    D = sc.data("estimates")
    Dc, region = sc.cooling(S["place"], D, f.plant)
    power = electricity(sc.electricity(Dc, region, f.cooling, f.it_mw))
    ba = place_ba(site.place.context())
    grid = grid_water(sc.grid_water(Dc, region, f.cooling, f.it_mw, ba), ba)
    return Estimate(site=resolved, water=water, electricity=power, grid_water=grid, model_version=D["model_version"], data_date=D["generated"])


# Michigan's utilities in PJM, from the same sources as every state: the service territory layer's control area (HIFLD: Dowagiac, Midwest Energy Cooperative, Niles, Paw Paw,
# South Haven, Sturgis) and EIA-861 where that layer has none (Indiana Michigan Power). The rest are MISO; that layer lists none for Bayfield and Northern States Wisconsin,
# in MISO's Wisconsin zone.
PJM = {"City of Dowagiac", "City of Niles", "City of South Haven", "City of Sturgis", "Indiana Michigan Power Company", "Midwest Energy Cooperative", "Village of Paw Paw"}


def nearest_served(r):
    """(place, km) of the nearest Michigan place an MPSC territory covers, center to center, for one none covers (Beaver Island's St. James
    township), within the national tier's UTILITY_KM; None otherwise."""
    import math
    from waterledger.national.provider import UTILITY_KM
    P = sc.data("power")
    lon, lat = sc.lonlat(r)
    k = math.cos(math.radians(lat))
    km = lambda q: math.hypot((sc.lonlat(q)[0] - lon) * k, sc.lonlat(q)[1] - lat) * 111.2
    best = min(((km(q), q["g"], q) for q in sc.data("places")["places"] if P["places"].get(q["g"])), default=None)
    return (best[2], round(best[0], 1)) if best and best[0] <= UTILITY_KM else None


def balancing_authority(name):
    return "PJM" if name in PJM else "MISO"


def reference(place):
    """Michigan's values to compare an estimate with: its power options, the starting one, a typical golf course, and its homes' electricity."""
    from waterledger_models import runoff as rq
    D, P, W = sc.data("estimates"), sc.data("power"), sc.data("waters")
    T = P.get("total") or P["michigan"]
    options = {"state_mix" if k == "mi_mix" else k: v for k, v in D["power_supply"].items()}      # data built before 3.9.0 calls the state's mix mi_mix
    return {"power_options": options, "power": "state_mix", "golf_gpd": D["golf"]["golf_median_gpd"], "golf_basis": "state reports", "golf_note": "The median of Michigan courses reporting to EGLE. Only facilities able to withdraw 100,000 gallons a day report.", "home_gpd": home_gpd("MI"), "home_kwh_month": D["home_kwh_month"],
            "home_customers": D["home_customers"], "state_avg_mw": T["avg_mw"], "rain_median_in": W.get("rain_median_in"), "salt_events": rq.salt_events(SALT_DAYS[sc.place(place.geoid)["r"]]), "withdrawals": D["context"].get("withdrawals"), "state_rules": True}


def _usgs_water_use(county_fips):
    """USGS's 2015 estimate for a county from Michigan's snapshot, which carries it; None where the snapshot can't be had, so Michigan's answers don't depend on it."""
    from waterledger.national.provider import county_water_use
    try:
        return county_water_use("MI", county_fips)[1]
    except Exception:                                   # noqa: BLE001  no snapshot, or one without water use
        return None


def context(place):
    """Michigan's context for a place: every category from Water Ledger Michigan's data (EGLE, EPA, USGS, NOAA, MPSC, EIA)."""
    from waterledger import context as cx
    r, E, Wd, P = sc.place(place.geoid), sc.data("estimates"), sc.data("waters"), sc.data("power")
    sys_ = lambda w: cx.WaterSystem(pwsid=w["pwsid"], name=w["name"].title(), population=w.get("pop"), connections=w.get("connections"), share_of_place=w.get("share"))
    near = None if r["w"] else sc.near_system(r)
    wells = Wd["wells"].get(r["g"])
    L = egle_layer()
    egle = L["counties"].get(r["cf"])
    usgs = _usgs_water_use(r["cf"])
    supply = cx.Supply(provider="MI", sources=["epa_sa", "egle2025", "wellogic", *(["usgs_wu2015"] if usgs else [])], systems=[sys_(w) for w in r["w"]],
                       nearest_system=sys_(near["w"]) if near else None, nearest_system_km=near["km"] if near else None,
                       county_use_mgd=E["county_uses_mgd"].get(r["c"], {}),
                       county_water_use=water_use_record(egle, L["basis"], r["cf"]) if egle else None, county_water_use_usgs=usgs,
                       household_wells=dict(zip(("drift_n", "drift_depth_ft", "drift_level_ft", "rock_n", "rock_depth_ft", "rock_level_ft"), wells)) if wells else None)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["n"], design_mgd=q.get("design"), flow_mgd=q.get("flow"), km=q["km"],
                            own=bool(q.get("own")), system=bool(q.get("system")), receiving_water=q.get("recv") or None, combined_sewer=bool(q.get("cso")), lagoon=bool(q.get("lagoon")))
              for q in sc._plants_near(r)[:PLANTS_MAX]]
    G = Wd["groups"]
    path, h = [], (r["h12"][0]["code"] if r["h12"] else None)
    while h and h in Wd["h12"] and len(path) < 25:
        x = Wd["h12"][h]
        path.append(cx.Reach(huc12=h, name=x["n"], assessed=bool(x["a"]) if "a" in x else None, impairments=[G[i[0]] for i in x.get("i", [])], tmdl=[G[i[0]] for i in x.get("i", []) if i[1]],
                             coldwater_streams=x["tr"][1] if x.get("tr") else []))
        h = x["t"]
    receiving = cx.Receiving(provider="MI", sources=["usgs_wbd", "attains2026", "mdnr_trout"],
                             watersheds=[cx.Watershed(huc12=w["code"], name=w["name"], share_of_place=w.get("share")) for w in r["h12"]],
                             basin=cx.Watershed(huc12=r["h8"]["code"], name=r["h8"]["name"]) if r.get("h8") else None,
                             great_lake=(r.get("gl") or {}).get("lake"), great_lakes_basin=r["h12"][0]["code"].startswith("04") if r["h12"] else None, downstream=path)
    meta = E["region_meta"][r["r"]]
    cell = {}
    if r.get("e"):                                      # model 1.8: the place's ERA5 cell, the same fields as the national tier's
        from waterledger.national import cells
        from waterledger_data import era5
        lon, lat = sc.lonlat(r)
        c = era5.cell(round(lat, 5), round(lon, 5))
        cell = {k: v for k, v in cells.place_fields(c, sc.cell(r["e"])["correction"]["applied"]).items() if k in ("cell", "cell_km", "cell_land", "cell_moved", "weather_corrected")}
    climate = cx.Climate(provider="MI", sources=["era5", "noaa_cag", "noaa_atlas14"], region=r["r"], region_name=meta["name"], station=meta["station"],
                         rain_in=Wd["rain_in"].get(r["cf"]), design_storms_in=E["county_storms_in"].get(r["cf"], {}), **cell)
    U = P["utilities"]
    from waterledger.national.provider import _ppw
    from waterledger_data.energy import grid_water
    GW = grid_water()
    utility = lambda i, sh: cx.Utility(name=U[i]["n"], type=U[i]["type"], share_of_place=sh, customers=U[i].get("cust"), avg_mw=U[i].get("avg_mw"),
                                       summer_peak_mw=U[i].get("summer_mw"), balancing_authority=balancing_authority(U[i]["n"]),
                                       power_plant_water_l_per_kwh=GW[balancing_authority(U[i]["n"])]["consumed_excl_hydro"])
    near = None if P["places"].get(r["g"]) else nearest_served(r)
    energy = cx.Energy(provider="MI", sources=["mpsc_territory", "eia861", "eia923_2024", "macknick2012", "siddik2024"], power_plant_water=_ppw("MI"),
                       utilities=[utility(i, sh) for i, sh in P["places"].get(r["g"], [])],
                       nearest_place=near[0]["n"] if near else None, nearest_place_km=near[1] if near else None,
                       nearest_utilities=[utility(i, sh) for i, sh in P["places"][near[0]["g"]]] if near else [])
    jur = cx.Jurisdiction(provider="MI", not_covered=["rules"], sources=["census_tiger"], name=place.name, kind=place.kind, county=place.county, state="MI")
    return cx.Context(place=place, jurisdiction=jur, supply=supply, wastewater=cx.Wastewater(provider="MI", sources=["echo", "cwns2022"], plants=plants),
                      receiving=receiving, climate=climate, energy=energy)


def place_at(lat, lon):
    """Michigan places are its county subdivisions (cities and townships), so a point maps to the subdivision containing it."""
    from waterledger_data.census import LAYERS
    from waterledger_data.places import _get
    d = _get(LAYERS["cousub"], {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "false", "f": "json"})
    f = d.get("features", [])
    return f[0]["attributes"]["GEOID"] if f else None


def egle_layer():
    """EGLE's reported withdrawals by county as a water-use layer (waterledger_data.wateruse's shape), from the numbers
    waterledger.org/mi shows (estimates.json county_uses_mgd); EGLE's own groups are kept in source_values."""
    from waterledger_data.wateruse import CATEGORIES
    E = sc.data("estimates")
    fips = {p["c"]: p["cf"] for p in sc.data("places")["places"]}
    src = E["sources"]["egle2025"]
    out = {}
    for county, groups in E["county_uses_mgd"].items():
        if county not in fips:
            continue
        mgd = {}
        for g, v in groups.items():
            c = EGLE_CATS.get(g, "other")
            mgd[c] = mgd.get(c, 0.0) + v
        mgd = {c: mgd[c] for c in CATEGORIES if c in mgd}
        mgd["total"] = sum(mgd.values())
        out[fips[county]] = {"name": f"{county} County", "mgd": mgd, "source_values": groups}
    basis = {"source": "egle2025", "kind": "reported", "measure": "withdrawals", "year": 2025, "units": "Mgal/d", "source_units": "gallons per year",
             "citation": src["citation"], "url": src["url"],
             "threshold": "facilities able to withdraw 100,000 gallons a day or more (Part 327, NREPA) report each year",
             "categories": {v: k for k, v in EGLE_CATS.items() if k != "Bottled water"} | {"industrial": "Industry, and bottled water"},
             "caveats": ["Golf courses are irrigation facilities whose names mark them as golf or country clubs",
                         "Entries far outside the range of their kind are left out as likely reporting errors (see the methods page)",
                         "Gallons a year averaged over 365 days"]}
    return {"basis": basis, "counties": dict(sorted(out.items()))}
