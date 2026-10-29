"""place.context() from the national tier for the test states (nightly; pytest -m live)."""
import pytest

import waterledger as wl

pytestmark = pytest.mark.live


@pytest.mark.parametrize("query, system, plant, reaches", [
    ("Columbus city, OH", "Columbus Public Water System", "COLUMBUS JACKSON PIKE WWTP & SEWERS", "Scioto River"),
    ("Loudoun County, VA", "Loudoun Water - Central System", "BROAD RUN REG. RECL. FAC.", "Potomac River"),
    ("Austin city, TX", "City Of Austin Water & Wastewater", "WALNUT CREEK WWTP", "Colorado River"),
])
def test_context(query, system, plant, reaches):
    c = wl.place(query).context()
    assert c.supply.provider == "national" and c.supply.systems[0].name == system
    assert plant in [p.name for p in c.wastewater.plants]
    assert c.receiving.basin and any(reaches in r.name for r in c.receiving.downstream) and len(c.receiving.downstream) <= 25
    assert c.climate is None and c.energy is None          # steps 4 and 5
    assert wl.Context.model_validate_json(c.model_dump_json()) == c
