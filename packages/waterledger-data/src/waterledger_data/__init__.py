"""Water Ledger data: public U.S. data for any place, fetched once and cached (see waterledger_data.config).

    climate   hourly weather (ERA5 via Open-Meteo, NOAA ISD stations, NASA POWER) and NOAA Atlas 14 design storms
    places    Census cities and townships, EPA water system service areas, USGS watersheds
    waters    EPA ATTAINS impaired waters, ECHO and CWNS sewer plants, county rainfall, household wells
    power     electric utility territories and EIA-861 loads

Submodules load on first use, so `import waterledger_data` stays light.
"""
import importlib

__version__ = "3.0.0"
_SUB = ("climate", "config", "places", "power", "waters")


def __getattr__(name):
    if name in _SUB:
        return importlib.import_module(f"waterledger_data.{name}")
    raise AttributeError(name)
