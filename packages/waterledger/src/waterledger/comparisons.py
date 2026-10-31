"""Comparisons: a site's estimate against what is already there. These are results, on est.comparisons; a display words and rounds them."""
from waterledger.estimate import Comparison, Equivalents, Percent, PlantWater, Range

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


def comparisons(est):
    """Every comparison that applies to an estimate; one that doesn't apply is left out, not zero. A campus on its own wells or a lake takes
    nothing from the public system."""
    out = []
    if est.site.source == "muni":
        c = water_system_share(est.water.withdrawn, est.site.place.context().supply.systems)
        if c:
            out.append(c)
    return out
