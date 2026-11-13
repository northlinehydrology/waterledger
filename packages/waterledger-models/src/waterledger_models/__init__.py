"""Water Ledger models: the water large new users take, use up and send back, starting with data centers, and runoff quality.

    datacenter.cooling   weather-driven cooling water by design, Monte Carlo over the published parameter ranges, staff water
    datacenter.lake      lake-source (once-through) cooling
    battery              battery cell plants: heat, power and water hour by hour, per GWh/yr of cells (design 0009)
    heat_rejection       cooling towers, hybrid and dry coolers, loops, chillers, pumps and fans, shared by every water user
    once_through         once-through cooling from a Great Lake: withdrawal, forced evaporation, GLERL temperatures, shared by every water user
    daily                daily totals and their statistics, shared by every water user
    runs                 the Monte Carlo at one location, shared by every water user: draws, loads, daily statistics, grid water, names
    gas                  new gas plants (combined cycle, turbines, engines, fuel cells): output, fuel and water hour by hour (design 0014)
    supply               power supply scenarios: new PV and wind generation, their land and runoff, and what serves a user's load (0014)
    grid                 water at the power plants supplying any user's electricity, hourly, at grid level (design 0008)
    runoff              runoff, sediment, nutrients, salt and fuel from a developed site
    hydrology            screening hydrology: curve-number storm runoff, Theis drawdown, Glover stream depletion
    quantile_mapping     an ERA5 cell's temperature and dew point corrected toward nearby stations (shore stations for cells under 90% land)
    weather              hourly weather from Open-Meteo's best match (ERA5, ERA5-Land, IFS HRES), as xarray, for the ensembles and BMI components

MODEL_VERSION is Water Ledger's model version (the numbers); __version__ is the package version (the code, semver).
They change independently. Every published estimate names the model version that produced it. One model version covers every
water user type; MODELS says which types a version changes and whether the states' snapshots are rebuilt for it.
"""
from waterledger_models import battery, datacenter, gas, grid, hydrology, quantile_mapping, runoff, runs, supply, weather

__all__ = ["battery", "datacenter", "gas", "grid", "hydrology", "quantile_mapping", "runoff", "runs", "supply", "weather", "MODEL_VERSION", "MODELS", "snapshot_model"]
MODEL_VERSION = "1.15"

# Each model version from 1.12 names the water user types whose numbers it changes and the model version of the snapshots it reads.
# A version that changes nothing the snapshots carry (data centers, the places' water and power) skips them and reads the last
# rebuilt ones, so no state is rebuilt to the same numbers. Every version before 1.12 changed the data center numbers and was rebuilt.
MODELS = {
    "1.12": {"types": ("battery",), "snapshots": "1.11"},
    "1.13": {"types": ("gas", "supply", "battery"), "snapshots": "1.11"},     # gas plants, supply scenarios; battery's stream return
    "1.14": {"types": ("gas", "supply"), "snapshots": "1.11"},                # outages that last days; PV against the 2024 fleet
    "1.15": {"types": ("supply",), "snapshots": "1.11"},                      # wind against the 2024 fleet
}


def snapshot_model(version=MODEL_VERSION):
    """The model version of the snapshots and cell runs that `version` reads: its own if it rebuilt them, else the one it names."""
    return MODELS.get(version, {}).get("snapshots", version)


__version__ = "3.22.0"
