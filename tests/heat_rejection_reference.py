"""Write tests/data/datacenter_before_heat_rejection.json: data center hourly water, power and heat at central parameters (shared plant) on the stored
West Michigan weather, at the record's 24 sampled hours, for every design. First written before the heat rejection code moved to heat_rejection.py
(model 1.11), by hand, and rewritten by hand at model 1.16; this script writes it from model 1.17 on, keeping the record's hours.
test_heat_rejection.py holds the code to it. Rerun only on a deliberate model change.

    uv run python tests/heat_rejection_reference.py
"""
import json
import os

import numpy as np

from waterledger_models import MODEL_VERSION, __version__
from waterledger_models.datacenter import physics as ph

HERE = os.path.dirname(__file__)
PATH = os.path.join(HERE, "data", "datacenter_before_heat_rejection.json")


def results(hours):
    w = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
    tdb, rh = np.array(w["temperature_2m"], dtype=float), np.array(w["relative_humidity_2m"], dtype=float)
    twb = ph.wet_bulb(tdb, rh)
    p = ph.for_location(ph.central_parameters(), tdb)
    out = {}
    for design in ph.DESIGNS:
        wd, c, r = ph.hourly_rates(tdb, twb, design, p, rh)
        power, heat = ph.hourly_heat_power(tdb, twb, design, p, rh)
        out[design] = {name: np.ravel(v)[hours].tolist() for name, v in (("withdrawn", wd), ("consumed", c), ("returned", r), ("power", power), ("heat", heat))}
    return out


if __name__ == "__main__":
    hours = json.load(open(PATH))["hours"]
    note = ("Data center hourly rates, heat and power at central parameters (shared plant) at West Michigan. First computed before the heat rejection code "
            "moved to heat_rejection.py (model 1.11, waterledger 3.15.0); rewritten at model 1.16 (air-cooled chillers, the switch setting) and at model "
            f"{MODEL_VERSION} (water-cooled chillers on 90.1's curve, the outside air design), waterledger-models {__version__}, by tests/heat_rejection_reference.py. "
            "tests/test_heat_rejection.py holds the code to them.")
    json.dump({"note": note, "hours": hours, "designs": results(hours)}, open(PATH, "w"))
    print("wrote", PATH)
