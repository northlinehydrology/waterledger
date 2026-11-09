"""Water Ledger models: the water large new users take, use up and send back, starting with data centers, and runoff quality.

    datacenter.cooling   weather-driven cooling water by design, Monte Carlo over the published parameter ranges, staff water
    datacenter.lake      lake-source (once-through) cooling
    battery              battery cell plants: heat, power and water hour by hour, per GWh/yr of cells (design 0009)
    heat_rejection       cooling towers, hybrid and dry coolers, loops, chillers, pumps and fans, shared by every water user
    once_through         once-through cooling from a Great Lake: withdrawal, forced evaporation, GLERL temperatures, shared by every water user
    daily                daily totals and their statistics, shared by every water user
    grid                 water at the power plants supplying any user's electricity, hourly, at grid level (design 0008)
    runoff              runoff, sediment, nutrients, salt and fuel from a developed site
    hydrology            screening hydrology: curve-number storm runoff, Theis drawdown, Glover stream depletion
    quantile_mapping     an ERA5 cell's temperature and dew point corrected toward nearby stations (shore stations for cells under 90% land)
    weather              hourly weather from Open-Meteo's best match (ERA5, ERA5-Land, IFS HRES), as xarray, for the ensembles and BMI components

MODEL_VERSION is Water Ledger's model version (the numbers); __version__ is the package version (the code, semver).
They change independently. Every published estimate names the model version that produced it.
"""
from waterledger_models import battery, datacenter, grid, hydrology, quantile_mapping, runoff, weather

__all__ = ["battery", "datacenter", "grid", "hydrology", "quantile_mapping", "runoff", "weather", "MODEL_VERSION"]
MODEL_VERSION = "1.11"
__version__ = "3.15.0"
