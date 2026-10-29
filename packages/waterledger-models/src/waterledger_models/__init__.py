"""Water Ledger models: the water large new users take, use up and send back, starting with data centers, and runoff quality.

    datacenter.cooling   weather-driven cooling water by design, Monte Carlo over the published parameter ranges, staff water
    datacenter.lake      lake-source (once-through) cooling
    runoff               runoff, sediment, nutrients, salt and fuel from a developed site
    weather              hourly ERA5 weather from Open-Meteo, as xarray, for the ensembles and BMI components

MODEL_VERSION is Water Ledger's model version; every published estimate names the version that produced it.
"""
from waterledger_models import datacenter, runoff, weather

__all__ = ["datacenter", "runoff", "weather", "MODEL_VERSION"]
MODEL_VERSION = "1.2"
__version__ = "1.2.1"
