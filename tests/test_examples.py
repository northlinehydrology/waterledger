"""Every script in examples/ runs. The BMI loop runs as it is; the weather examples run on synthetic weather in place of the
download, so a change to the package's API breaks a test, not a reader's first try. Live runs download as a reader would."""
import pathlib
import runpy

import pytest
import xarray as xr

from test_physics_properties import synthetic_weather

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"
WEATHER = ("michigan_eight_locations.py", "build_stac_catalog.py", "battery_cell_plants_ea_check.py")
NETWORK = ("trace_plaster_creek_map.py",)


def test_every_example_is_tested():
    assert {p.name for p in EXAMPLES.glob("*.py")} == {"bmi_coupling.py", *WEATHER, *NETWORK}


def test_bmi_coupling(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(EXAMPLES / "bmi_coupling.py"), run_name="__main__")
    assert "Water withdrawn over the week" in capsys.readouterr().out


def _synthetic(lat, lon, cache=None, **kw):
    time, t, rh = synthetic_weather(365, seed=int(abs(lat * 100)))
    return xr.Dataset({"air_temperature": ("time", t), "relative_humidity": ("time", rh)}, coords={"time": time})


@pytest.mark.parametrize("name", WEATHER)
def test_weather_examples_on_synthetic_weather(name, tmp_path, monkeypatch):
    pystac = pytest.importorskip("pystac")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("waterledger_models.weather.fetch_open_meteo", _synthetic)
    monkeypatch.setattr(pystac.Catalog, "validate_all", lambda self: 0)     # validating fetches the STAC schemas; the live run does it
    runpy.run_path(str(EXAMPLES / name), run_name="__main__")


@pytest.mark.live
@pytest.mark.parametrize("name", WEATHER + NETWORK)
def test_examples_live(name, tmp_path, monkeypatch):
    if name in NETWORK:
        pytest.importorskip("matplotlib")
        pytest.importorskip("geopandas")
        (tmp_path / "docs").mkdir()
    else:
        pytest.importorskip("jsonschema")
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(EXAMPLES / name), run_name="__main__")
