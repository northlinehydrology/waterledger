"""Smoke tests for the three packages: they import as one, the model runs on synthetic weather, paths resolve."""
import os, subprocess, sys

import numpy as np


def test_import_as_wl():
    import waterledger as wl
    assert wl.models.MODEL_VERSION == "1.2"
    assert wl.models.datacenter.cooling.run_location
    assert wl.data.places.__name__ == "waterledger_data.places"


def test_cooling_runs_on_synthetic_weather():
    from waterledger_models.datacenter import cooling as cw
    hours = np.arange(2 * 8760)
    t = [f"{2001 + h // 8760}-{1 + (h % 8760) // 744:02d}-{1 + (h % 744) // 24:02d}T{h % 24:02d}:00" for h in hours]
    T = 12 + 14 * np.sin(2 * np.pi * (hours % 8760) / 8760 - np.pi / 2) + 5 * np.sin(2 * np.pi * hours / 24)
    out = cw.run_location(t, T.tolist(), [70.0] * len(t), n=8)
    assert out["towers"]["withdrawn_avg"]["p50"] > out["hybrid"]["withdrawn_avg"]["p50"] > out["dry"]["withdrawn_avg"]["p50"] > 0


def test_paths_from_environment(tmp_path):
    env = dict(os.environ, WATERLEDGER_CACHE=str(tmp_path / "c"), WATERLEDGER_SITE=str(tmp_path / "s"))
    code = "from waterledger_data import config as c; print(c.CACHE); print(c.SITE)"
    out = subprocess.run([sys.executable, "-c", code], env=env, cwd=tmp_path, capture_output=True, text=True, check=True).stdout.split()
    assert out == [str(tmp_path / "c"), str(tmp_path / "s")]


def test_paths_from_waterledger_toml(tmp_path):
    (tmp_path / "waterledger.toml").write_text('[paths]\ncache = "raw"\nsite = "web"\n')
    (tmp_path / "sub").mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith("WATERLEDGER_")}
    code = "from waterledger_data import config as c; print(c.CACHE); print(c.SITE)"
    out = subprocess.run([sys.executable, "-c", code], env=env, cwd=tmp_path / "sub", capture_output=True, text=True, check=True).stdout.split()
    assert out == [str(tmp_path / "raw"), str(tmp_path / "web")]


def test_entry_points_load_on_first_use():
    import waterledger as wl
    dc = wl.models.datacenter
    assert dc.run_ensemble.__module__ == "waterledger_models.datacenter.ensemble"
    assert dc.CoolingWaterBmi.__name__ == "CoolingWaterBmi" and dc.stac.write_catalog
