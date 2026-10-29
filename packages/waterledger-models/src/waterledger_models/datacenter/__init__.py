"""Data centers: cooling water (towers, hybrid, closed loop with or without evaporative assist) and lake-source cooling.

    physics    the equations and parameter ranges, vectorized (numpy only)
    cooling    Water Ledger's per-run Monte Carlo (numpy only): run_location, staff water
    lake       lake-source (once-through) cooling: run_lake, and run_lake_ensemble as xarray
    ensemble   vectorized ensembles as xarray, dask across locations      (waterledger-models[ensemble])
    bmi        CoolingWaterBmi and LakeCoolingBmi, CSDMS BMI 2.0          (waterledger-models[bmi])
    stac       publish ensemble results as zarr with a STAC catalog       (waterledger-models[stac])

The modules that need optional packages load on first use, and the common entry points are here too:
run_ensemble, summarize, run_locations, CoolingWaterBmi, LakeCoolingBmi.
"""
import importlib

from waterledger_models.datacenter import cooling, lake, physics

__all__ = ["cooling", "lake", "physics", "ensemble", "bmi", "stac", "run_ensemble", "summarize", "run_locations",
           "CoolingWaterBmi", "LakeCoolingBmi"]
_LAZY = {"ensemble": None, "bmi": None, "stac": None, "run_ensemble": "ensemble", "summarize": "ensemble",
         "run_locations": "ensemble", "CoolingWaterBmi": "bmi", "LakeCoolingBmi": "bmi"}


def __getattr__(name):
    if name not in _LAZY:
        raise AttributeError(name)
    mod = importlib.import_module(f"waterledger_models.datacenter.{_LAZY[name] or name}")
    return mod if _LAZY[name] is None else getattr(mod, name)
