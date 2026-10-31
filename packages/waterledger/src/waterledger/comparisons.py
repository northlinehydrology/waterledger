"""Comparisons: a site's estimate against what is already there. These are results, on est.comparisons; a display words and rounds them."""
from waterledger.estimate import Comparison, Percent, Range

# U.S. EPA WaterSense, How We Use Water: "The average American family uses more than 300 gallons of water per day at home."
HOUSEHOLD_GPD = 300


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
