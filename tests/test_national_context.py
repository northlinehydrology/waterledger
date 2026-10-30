"""place.context() from the national tier for the test states (nightly; pytest -m live)."""
import pytest

import waterledger as wl

pytestmark = pytest.mark.live


@pytest.mark.parametrize("query, system, plant, reaches, utility, ba, use", [
    ("Columbus city, OH", "Columbus Public Water System", "COLUMBUS JACKSON PIKE WWTP & SEWERS", "Scioto River", "Ohio Power Co", "PJM", "odnr_wwfr"),
    ("Loudoun County, VA", "Loudoun Water - Central System", "BROAD RUN REG. RECL. FAC.", "Potomac River", "Virginia Electric & Power Co", "PJM", "va_deq_awrr"),
    ("Austin city, TX", "City Of Austin Water & Wastewater", "WALNUT CREEK WWTP", "Colorado River", "Austin Energy", "ERCO", "twdb_wus"),
])
def test_context(query, system, plant, reaches, utility, ba, use):
    c = wl.place(query).context()
    w, u = c.supply.county_water_use, c.supply.county_water_use_usgs
    if w is not None:                                   # snapshots before format 2 have no water use
        assert w.source == use and w.year >= 2024 and w.mgd["total"] > 10 and c.supply.county_use_mgd == w.mgd
        assert (u.source, u.year, u.kind) == ("usgs_wu2015", 2015, "estimate") and u.delivered_to_homes_mgd > 25
    assert c.supply.provider == "national" and c.supply.systems[0].name == system
    assert plant in [p.name for p in c.wastewater.plants]
    assert c.receiving.basin and any(reaches in r.name for r in c.receiving.downstream) and len(c.receiving.downstream) <= 25
    u = c.energy.utilities[0]
    assert (u.name, u.balancing_authority) == (utility, ba) and u.customers > 100000 and 0.5 < u.power_plant_water_l_per_kwh < 2
    assert wl.Context.model_validate_json(c.model_dump_json()) == c
