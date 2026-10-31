"""Comparisons: a site's estimate against what is already there. These are results, on est.comparisons; a display words and rounds them."""
from waterledger.estimate import BeforeAfterRow, Comparison, DesignComparison, DesignTotal, Equivalents, Percent, PlantWater, Range
from waterledger_models import runoff as rq

# U.S. EPA WaterSense, How We Use Water: "The average American family uses more than 300 gallons of water per day at home."
HOUSEHOLD_GPD = 300


def water_homes(mgd):
    """Water (MGD) as homes, at EPA WaterSense's 300 gallons a day."""
    return mgd * 1e6 / HOUSEHOLD_GPD


def golf_courses(mgd, course_gpd):
    """Water (MGD) as typical golf courses, each its yearly water averaged over 365 days."""
    return mgd * 1e6 / course_gpd


def electricity_homes(mw, kwh_month):
    """Electricity (MW, around the clock) as homes, at the state's average residential use (EIA-861)."""
    return mw * 1000 / (kwh_month * 12 / 8760)


def share_of_customers(homes, customers):
    """Homes as a percent of the state's residential electricity customers."""
    return 100 * homes / customers


def plant_water(mw, gal_mwh):
    """Water at power plants (MGD) for electricity at `mw` around the clock, from a factor in gallons per MWh."""
    return mw * 24 * gal_mwh / 1e6


def evaporated_share(consumed, withdrawn):
    """Percent of the water taken that is lost to evaporation, middle estimates, full values."""
    return 100 * consumed / max(withdrawn, 1e-9)


def _range(fn, r):
    return Range(p10=fn(r.p10), p50=fn(r.p50), p90=fn(r.p90))


def plant_waters(power, options):
    """Water at power plants for each power option, consumed and withdrawn, MGD. Each end of a range pairs the campus's electricity at that end
    with the factor's at that end. Returned is what is withdrawn less what is consumed, on the middle estimates."""
    out = {}
    for k, o in options.items():
        band = lambda lo, mid, hi: Range(p10=plant_water(power.avg_mw.p10, lo), p50=plant_water(power.avg_mw.p50, mid), p90=plant_water(power.avg_mw.p90, hi))
        c, w = band(o["lo"], o["gal_mwh"], o["hi"]), band(o["wd_lo"], o["wd_gal_mwh"], o["wd_hi"])
        out[k] = PlantWater(option=k, label=o["label"], consumed=c, withdrawn=w, returned=max(w.p50 - c.p50, 0.0), sources=o["sources"])
    return out


def equivalents(est, ref):
    """An estimate in homes and golf courses. Water counts what is taken; for lake-source cooling, what the lake loses, since nearly all it takes
    goes back. `ref` is the state's reference values (the provider's `reference`): golf_gpd, home_kwh_month and home_customers, any of them None."""
    w, base = est.water, est.water.consumed.avg if est.water.lake_source else est.water.withdrawn.avg
    golf, kwh, cust, e = ref["golf_gpd"], ref["home_kwh_month"], ref["home_customers"], est.electricity
    homes_e = _range(lambda v: electricity_homes(v, kwh), e.avg_mw) if e and kwh else None
    return Equivalents(homes=_range(water_homes, base), homes_peak_day=_range(water_homes, w.withdrawn.peak_day),
                       golf_courses=_range(lambda v: golf_courses(v, golf), base) if golf else None, golf_course_gpd=golf,
                       evaporated_share=evaporated_share(w.consumed.avg.p50, w.withdrawn.avg.p50),
                       electricity_homes=homes_e, electricity_homes_peak=_range(lambda v: electricity_homes(v, kwh), e.peak_mw) if e and kwh else None,
                       share_of_home_customers=_range(lambda v: share_of_customers(v, cust), homes_e) if homes_e and cust else None)


def water_system_share(withdrawn, systems):
    """The campus's water (a Flow) as homes, as a percent of the connections of the largest public water system mapped in the place.
    Not a percent of the system's water use: connections include businesses, and the system's own gallons are not in the public data.
    None with no system mapped or no connection count."""
    if not systems:
        return None
    s = max(systems, key=lambda x: x.population or 0)
    if not s.connections:
        return None
    pct = lambda r: Range(**{q: 100 * (getattr(r, q) * 1e6 / HOUSEHOLD_GPD) / s.connections for q in ("p10", "p50", "p90")})
    return Comparison(against="water_system", name=s.name, measure="homes_vs_connections", existing=s.connections, unit="connections",
                      percent=Percent(avg=pct(withdrawn.avg), peak_day=pct(withdrawn.peak_day)),
                      basis=f"Campus water as homes at {HOUSEHOLD_GPD} gallons a day (EPA WaterSense), against the system's connections (EPA)")


def it_mw_from_contract(contract_mw, pue):
    """Computing capacity (MW) from a utility contract's total power, at the design's PUE; contracts cap the hottest hour, so use the top of its range."""
    return contract_mw / pue


def is_grid_average(option):
    return option["label"].endswith("grid average")


def offered_power(options, start):
    """The power options to choose among. A state with its own mix keeps grid averages for comparison only."""
    own = not is_grid_average(options[start])
    return [k for k, o in options.items() if not (own and is_grid_average(o))]


def thirstiest_power(options, start):
    """The offered option using the most water at power plants, other than wind and solar and the state's starting point. The first of a tie."""
    return max((k for k in offered_power(options, start) if k not in ("renew", start)), key=lambda k: options[k]["gal_mwh"], default=None)


def compare_designs(results, options, power, start):
    """The same campus across cooling designs: `results` is {design: (WaterUse, Electricity)}. The design order breaks a tie for `best`."""
    rows = {}
    for k, (water, e) in results.items():
        o = options[power]
        rows[k] = DesignTotal(design=k, evaporated=water.consumed.avg, at_power_plants=Range(p10=plant_water(e.avg_mw.p10, o["lo"]), p50=plant_water(e.avg_mw.p50, o["gal_mwh"]), p90=plant_water(e.avg_mw.p90, o["hi"])),
                              avg_mw=e.avg_mw, peak_mw=e.peak_mw)
    best = min(rows, key=lambda k: rows[k].total)
    dry, tw = rows.get("dry"), rows.get("towers")
    extra = {"closed_loop_more_power_pct": 100 * (dry.avg_mw.p50 / tw.avg_mw.p50 - 1), "closed_loop_more_peak_mw": dry.peak_mw.p50 - tw.peak_mw.p50,
             "closed_loop_saves_on_site": max(tw.evaporated.p50 - dry.evaporated.p50, 0.0)} if dry and tw else {}
    return DesignComparison(power=power, designs=rows, best=best, thirstiest_power=thirstiest_power(options, start), **extra)


def percent_of(value, existing):
    """`value` as a percent of what is already there."""
    return 100 * value / existing


def _of(r, existing):
    return _range(lambda v: percent_of(v, existing), r)


def utility_shares(power, utilities, state_avg_mw=None, limit=3):
    """The campus's electricity against the utilities that could serve the place, and against the whole state. Average power against a utility's average load
    (yearly sales over 8,760 hours), peak against its summer peak. A utility with no reported sales (delivery only, in a competitive market) can't be compared and is left out."""
    out = [Comparison(against="utility", name=u.name, measure="electricity", existing=u.avg_mw, unit="MW", percent=Percent(avg=_of(power.avg_mw, u.avg_mw), peak_day=_of(power.peak_mw, u.summer_peak_mw) if u.summer_peak_mw else None),
                      basis="Campus average against the utility's average load; campus peak against its summer peak (EIA-861)")
           for u in [x for x in utilities if x.avg_mw][:limit]]
    if state_avg_mw:
        out.append(Comparison(against="state", name="State", measure="electricity", existing=state_avg_mw, unit="MW", percent=Percent(avg=_of(power.avg_mw, state_avg_mw)),
                              basis="Campus average against the state's retail sales over 8,760 hours (EIA-861)"))
    return out


# What each county-use table calls public water, in the order to look for it, and the total it falls back on
COUNTY_PUBLIC = ("public_supply", "Public water systems", "Municipal (public systems and rural homes)")
COUNTY_ALL = ("total", "All reported withdrawals")


def county_public_mgd(uses):
    """The county's public water, million gallons a day, or None."""
    return next((uses[k] for k in COUNTY_PUBLIC if uses.get(k)), None)


def county_share(withdrawn, uses):
    """The campus's water as a percent of public water in the county; where a county's table has no public figure, of all reported withdrawals. None with neither."""
    pub = county_public_mgd(uses)
    base = pub or next((uses[k] for k in COUNTY_ALL if uses.get(k)), None)
    if not base:
        return None
    return Comparison(against="county_water", name="County", measure="public_water" if pub else "all_withdrawals", existing=base, unit="MGD", percent=Percent(avg=_of(withdrawn.avg, base)),
                      basis="Campus water on an average day against the county's reported figure")


def sewer_room(plant):
    """A plant's spare room: its design flow less last year's average, MGD. None where its flow isn't reported; zero or less means it has none."""
    return plant.design_mgd - plant.flow_mgd if plant.design_mgd and plant.flow_mgd else None


def sewer_shares(water, plant):
    """What the campus sends the sewer against a plant: as a percent of the plant's flow, and of its spare room on an average and a hottest day (lake-source
    cooling sends only its sanitary water, the same on both)."""
    out, send = [], water.to_sewer
    peak = send if water.lake_source else water.returned.peak_day
    if plant.flow_mgd:
        out.append(Comparison(against="sewer_plant", name=plant.name, measure="flow", existing=plant.flow_mgd, unit="MGD", percent=Percent(avg=_of(send, plant.flow_mgd)),
                              basis="Wastewater against the plant's average flow last year"))
    room = sewer_room(plant)
    if room is not None and room > 0:
        out.append(Comparison(against="sewer_spare_room", name=plant.name, measure="spare_room", existing=room, unit="MGD", percent=Percent(avg=_of(send, room), peak_day=_of(peak, room)),
                              basis="Wastewater against the plant's design flow less its average flow"))
    return out


def before_after(src, dest, w_avg, w_peak, used, sewer, acres, rain_in, before, imp, mw, power_mw=None, county_public=None, plant=None, lake=False, reuse=False, salt_events=None):
    """What changes at a place with the campus, as numbers; a display words them. Water, MGD: `w_avg` and `w_peak` taken, `used` evaporated, `sewer` to the sewer, each a
    Range. Runoff and loads from runoff.loads with ponds, Michigan's standard. Rows for water and wastewater follow the source and destination."""
    Row, rows = BeforeAfterRow, []
    today = county_public if src == "muni" else None
    rows.append(Row(key="water", today=today, after=w_avg.p50, after_low=w_avg.p10, after_high=w_avg.p90, percent=percent_of(w_avg.p50, today) if today else None, unit="MGD"))
    rows.append(Row(key="used", after=used.p50, after_low=used.p10, after_high=used.p90, unit="MGD"))
    if not reuse:
        if dest == "sewer" and plant is not None:
            rows.append(Row(key="sewer", today=plant.flow_mgd, after=sewer.p50, after_low=sewer.p10, after_high=sewer.p90, percent=percent_of(sewer.p50, plant.flow_mgd) if plant.flow_mgd else None, unit="MGD"))
        elif dest in ("water", "septic") and not (lake and dest == "water"):
            rows.append(Row(key="wastewater", after=sewer.p50, after_low=sewer.p10, after_high=sewer.p90, unit="MGD"))
    L, C, S, F = rq.loads(acres, rain_in, before, imp), rq.construction(acres), rq.salt(acres, imp, salt_events), rq.fuel(mw)
    rows.append(Row(key="runoff", today=L["runoff_gal"]["now"][1], after=L["runoff_gal"]["after"][1], unit="gallons a year"))
    for key, load, unit in (("mud", "tss_t", "tons a year"), ("p", "tp_lb", "pounds a year")):
        now, pond = L[load]["now"], L[load]["pond"]
        rows.append(Row(key=key, today=now[1], today_low=now[0], today_high=now[2], after=pond[1], after_low=pond[0], after_high=pond[2], unit=unit))
    rows.insert(-1, Row(key="build", today=L["tss_t"]["now"][1], after=C[1], after_low=C[0], after_high=C[2], unit="tons a year"))
    if S["salt_t"][1] > 0:
        rows.append(Row(key="salt", after=S["salt_t"][1], after_low=S["salt_t"][0], after_high=S["salt_t"][2], unit="tons a winter"))
    rows.append(Row(key="fuel", after=F["gal"][1], after_low=F["gal"][0], after_high=F["gal"][2], unit="gallons"))
    if power_mw:
        rows.append(Row(key="power", after=power_mw.p50, after_low=power_mw.p10, after_high=power_mw.p90, unit="MW"))
    return rows


def site_before_after(est, ref):
    """before_after for an estimate, with land defaults as the page starts: cities 50 acres already built, others 200 acres of farmland [A]."""
    s, w = est.site, est.water
    ctx, city = s.place.context(), s.place.kind == "city"
    plants = ctx.wastewater.plants
    rain = (ctx.climate.rain_in if ctx.climate else None) or ref.get("rain_median_in")
    return before_after(s.source, s.wastewater, w.withdrawn.avg, w.withdrawn.peak_day, w.consumed.avg, w.to_sewer, s.acres or (50 if city else 200), rain, s.land_before or ("built" if city else "farm"), s.impervious,
                        s.facility.it_mw, est.electricity.avg_mw if est.electricity else None, county_public_mgd(ctx.supply.county_use_mgd), plants[0] if plants else None, w.lake_source, w.reuse, ref.get("salt_events"))


def comparisons(est, ref=None):
    """Every comparison that applies to an estimate; one that doesn't apply is left out, not zero. A campus on its own wells or a lake takes
    nothing from the public system, and one not on the sewer sends a plant nothing."""
    out, s, ctx = [], est.site, est.site.place.context()
    if s.source == "muni":
        c = water_system_share(est.water.withdrawn, ctx.supply.systems)
        if c:
            out.append(c)
        if not est.water.lake_source:
            c = county_share(est.water.withdrawn, ctx.supply.county_use_mgd)
            if c:
                out.append(c)
    if s.wastewater == "sewer" and not est.water.reuse and ctx.wastewater.plants:
        out += sewer_shares(est.water, ctx.wastewater.plants[0])
    if est.electricity and ctx.energy:
        out += utility_shares(est.electricity, ctx.energy.utilities, (ref or {}).get("state_avg_mw"))
    return out
