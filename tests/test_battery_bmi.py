"""BatteryCellBmi (design 0009): step by step it gives what the hourly physics gives for the same hours, its balances close every step, and its
configuration is checked."""
import json
import os

import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models import once_through as ot
from waterledger_models.battery import physics as bp
from waterledger_models.battery.bmi import INPUTS, OUTPUTS, WATER, BatteryCellBmi

HERE = os.path.dirname(__file__)
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)
_TIMES = np.datetime64(_W["start"][:13]) + np.arange(len(TDB)).astype("timedelta64[h]")
TEMP, HUM = "atmosphere_bottom_air__temperature", "atmosphere_bottom_air_water_vapor__relative_saturation"
LAKE_T = "lake_water_surface__temperature"


@pytest.fixture(scope="module")
def FORCING(tmp_path_factory):
    """The West Michigan hours as an Open-Meteo file, the forcing format the components read."""
    path = tmp_path_factory.mktemp("forcing") / "weather.json"
    path.write_text(json.dumps({"hourly": {"time": [str(x) for x in _TIMES.astype("datetime64[m]")],
                                           "temperature_2m": TDB.tolist(), "relative_humidity_2m": RH.tolist()}}))
    return str(path)


def get(m, name):
    return float(m.get_value(name, np.empty(1))[0])


@pytest.mark.parametrize("design", ("dry", "hybrid", "towers"))
def test_steps_match_the_hourly_physics(design, FORCING):
    """With the forcing file, each step is that hour of physics.hourly at the plant's size, from the same located central parameters."""
    m = BatteryCellBmi()
    m.initialize({"design": design, "capacity_gwh": 43.75, "forcing": FORCING})
    p = bp.for_location({**bp.central_parameters(), "utilization": 1.0}, TDB, RH)
    hours = slice(4300, 4348)                       # two July days
    h = bp.hourly(TDB[hours], hr.wet_bulb(TDB[hours], RH[hours]), RH[hours], design, p)
    m.update_until(hours.start * 3600.0)
    to_m3s = 43.75 / ot.GAL_M3 / 3600.0
    for i in range(hours.stop - hours.start):
        m.update()
        for key, name in WATER.items():
            assert get(m, name) == pytest.approx(h[key][i] * to_m3s, rel=1e-12, abs=1e-15)
        assert get(m, "water_user__electric_power") == pytest.approx(h["electricity"][i] * 43.75 / 1000, rel=1e-12)
        assert get(m, "water_user__fuel_power") == pytest.approx(h["fuel"][i] * 43.75 / 1000, rel=1e-12)


@pytest.mark.parametrize("design", bp.DESIGNS)
def test_balances_close_every_step(design):
    m = BatteryCellBmi()
    m.initialize({"design": design, "capacity_gwh": 10, "parameters": {"design_h": 70.0, "design_db": 31.0}})
    for t, rh, lake in ((-5.0, 80.0, 2.0), (18.0, 60.0, 12.0), (33.0, 45.0, 24.0)):
        m.set_value(TEMP, np.array([t]))
        m.set_value(HUM, np.array([rh]))
        m.set_value(LAKE_T, np.array([lake]))
        m.update()
        w, c, r = (get(m, WATER[k]) for k in ("withdrawn", "consumed", "returned"))
        assert w == pytest.approx(c + r, rel=1e-12) and w > 0
        assert r == pytest.approx(get(m, WATER["to_sewer"]) + get(m, WATER["to_source"]), rel=1e-12)
        assert get(m, "water_user_water__gain_volume_flux") == 0.0
        assert (get(m, WATER["to_source"]) > 0) == (design == "lake")


def test_lake_reads_the_lake_and_wind():
    m = BatteryCellBmi()
    m.initialize({"design": "lake", "capacity_gwh": 10, "parameters": {"design_h": 70.0}})
    m.set_value(TEMP, np.array([25.0]))
    m.set_value(HUM, np.array([50.0]))
    evap = []
    for lake, wind in ((5.0, 3.0), (22.0, 3.0), (22.0, 8.0)):
        m.set_value(LAKE_T, np.array([lake]))
        m.set_value("atmosphere_bottom_air_flow__speed", np.array([wind]))
        m.update()
        evap.append(get(m, WATER["consumed"]))
    assert evap[0] != evap[1] != evap[2]


def test_lfp_and_configuration(FORCING):
    nmc, lfp = BatteryCellBmi(), BatteryCellBmi()
    nmc.initialize({"forcing": FORCING})
    lfp.initialize({"forcing": FORCING, "chemistry": "lfp"})
    nmc.update()
    lfp.update()
    assert get(lfp, "water_user__fuel_power") == pytest.approx(1.45 * get(nmc, "water_user__fuel_power"), rel=1e-12)
    assert len(nmc.get_input_var_names()) == len(INPUTS) and len(nmc.get_output_var_names()) == len(OUTPUTS)
    for bad in ({"design": "stream"}, {"chemistry": "sodium"}, {"parameters": {"cycles": 3}}, {},
                {"design": "hybrid", "parameters": {"design_h": 70.0}}, {"parameters": {"design_h": 70.0, "lfp_factor": 1.5}}):
        with pytest.raises(ValueError):
            BatteryCellBmi().initialize(bad)
