"""The lake-source BMI component (ported from dc-cooling-water): a daily run against NOAA GLERL temperatures."""
import json, os

import numpy as np
import pytest
import yaml

from waterledger_models.datacenter import lake
from waterledger_models.datacenter.bmi import LakeCoolingBmi

REF = json.load(open(os.path.join(os.path.dirname(__file__), "data", "water_ledger_lakes.json")))
WITHDRAWN = "data_center_cooling_water__withdrawal_volume_flux"
RETURNED = "data_center_cooling_water__return_volume_flux"
EVAP = "lake_water__forced_evaporation_volume_flux"
TEMP = "lake_water_surface__temperature"


def test_bmi_daily_run(tmp_path):
    temps = REF["Lake Michigan"]["temps"]
    (tmp_path / "t.csv").write_text("\n".join(str(t) for t in temps))
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"it_capacity_mw": 100, "forcing": str(tmp_path / "t.csv"), "wind_speed": 4.47}))
    m = LakeCoolingBmi()
    m.initialize(str(cfg))
    assert m.get_time_step() == 86400 and m.get_end_time() == len(temps) * 86400
    evap = []
    while m.get_current_time() < m.get_end_time():
        w, r, e = (m.get_value(n, np.empty(1))[0] for n in (WITHDRAWN, RETURNED, EVAP))
        assert w == r and 0 < e < w
        evap.append(e)
        m.update()
    p = {k: (a + b) / 2 for k, (a, b) in lake.RANGES.items()}
    expected = lake.forced_evaporation_m3s(100, p["utilization"], p["heat_factor"], np.array(temps), 4.47 * lake.MPH_PER_MS)
    np.testing.assert_allclose(evap, expected, rtol=1e-12)
    assert np.argmax(evap) > 150        # more evaporation from warm summer water
    m.set_value(TEMP, np.array([20.0]))
    warm = m.get_value(EVAP, np.empty(1))[0]
    m.set_value(TEMP, np.array([4.0]))
    assert warm > m.get_value(EVAP, np.empty(1))[0]
    m.finalize()


def test_bmi_rejects_unknown_parameters(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"parameters": {"coc": 4}}))
    with pytest.raises(ValueError):
        LakeCoolingBmi().initialize(str(cfg))
