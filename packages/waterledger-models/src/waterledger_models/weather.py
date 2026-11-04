"""Hourly weather for the models: temperature and humidity from the Open-Meteo archive, as an xarray Dataset (needs waterledger-models[ensemble]). The request sets no
`models`, so Open-Meteo's "best match" applies, which by its documentation combines IFS HRES (from 2017), ERA5 and ERA5-Land: a reanalysis-based record, not ERA5 alone.
waterledger_data.climate has the other sources (NOAA stations, NASA POWER) for the builders."""
import json
import os
import urllib.request

import numpy as np

OPEN_METEO = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
              "&hourly=temperature_2m,relative_humidity_2m&temperature_unit=celsius&timezone={tz}")


def from_open_meteo_json(payload):
    """An Open-Meteo archive response (dict or path to a saved JSON file) as a Dataset with 'air_temperature' (C)
    and 'relative_humidity' (%) on local hourly time."""
    if isinstance(payload, (str, os.PathLike)):
        with open(payload) as f:
            payload = json.load(f)
    import xarray as xr
    h = payload["hourly"]
    time = np.array(h["time"], dtype="datetime64[m]")
    return xr.Dataset({"air_temperature": ("time", np.array(h["temperature_2m"], dtype=float), {"units": "degC"}),
                       "relative_humidity": ("time", np.array(h["relative_humidity_2m"], dtype=float), {"units": "%"})},
                      coords={"time": time},
                      attrs={"source": "Open-Meteo archive API, best match (IFS HRES from 2017, ERA5 and ERA5-Land combined)", "latitude": payload.get("latitude"),
                             "longitude": payload.get("longitude")})


def design_dry_bulb(record):
    """The 0.4% design dry-bulb, C, of an hourly weather record: the temperature exceeded in 0.4% of its hours (ASHRAE's definition), which a
    hybrid campus needs as design_db. `record` is a Dataset with air_temperature (as from_open_meteo_json gives), a DataArray, or an array
    of hourly temperatures in C. Water Ledger computes it this way from each location's whole hourly record (physics.design_dry_bulb).

    For a coupling framework that supplies the weather itself (NextGen's AORC, for example), compute it once from the forcing for the place
    before the run and pass it in the component's parameters. Use a long record (Water Ledger uses 1995-2024): at Michigan's eight
    regions one year's value fell 1.9 to 2.8 C below to 0.8 to 1.5 C above the 30 years' in 80% of years, and up to 4.6 C off.
    AORC's temperature is in K, so subtract 273.15 first.

        from waterledger_models.weather import design_dry_bulb
        CoolingWaterBmi().initialize({"design": "hybrid", "parameters": {"design_db": design_dry_bulb(t2m_k - 273.15)}})
    """
    from waterledger_models.datacenter.physics import design_dry_bulb as from_hours
    if hasattr(record, "data_vars"):
        record = record["air_temperature"]
    return from_hours(getattr(record, "values", record))


EPSILON = 0.622        # ratio of the molar masses of water vapor and dry air (Bolton 1980; 0.378 = 1 - EPSILON)


def saturation_vapor_pressure(t_c):
    """Saturation vapor pressure over water, Pa, at air temperature t_c (C): Bolton (1980) eq. 10, within 0.1% from -30 to 35 C."""
    t_c = np.asarray(t_c, dtype=float)
    return 611.2 * np.exp(17.67 * t_c / (t_c + 243.5))


def relative_humidity(t_c, q, p):
    """Relative humidity, percent, from air temperature (C), specific humidity (kg kg-1) and surface pressure (Pa), the pair NextGen's AORC and NWM
    forcing carries: vapor pressure e = q p / (0.622 + 0.378 q) over saturation (Bolton 1980). Kept within 0-100: a reanalysis can be slightly
    supersaturated, and a negative q from interpolation is read as dry air."""
    q = np.clip(np.asarray(q, dtype=float), 0.0, None)
    e = q * np.asarray(p, dtype=float) / (EPSILON + (1 - EPSILON) * q)
    return np.clip(100.0 * e / saturation_vapor_pressure(t_c), 0.0, 100.0)


def specific_humidity(t_c, rh, p):
    """Specific humidity, kg kg-1, from air temperature (C), relative humidity (percent) and surface pressure (Pa): the inverse of
    relative_humidity, q = 0.622 e / (p - 0.378 e) with e = rh/100 x saturation vapor pressure (Bolton 1980)."""
    e = np.clip(np.asarray(rh, dtype=float), 0.0, 100.0) / 100.0 * saturation_vapor_pressure(t_c)
    return EPSILON * e / (np.asarray(p, dtype=float) - (1 - EPSILON) * e)


def local_standard_offset(lon):
    """Hours from UTC to local standard time at a longitude, the same rule the NOAA station records use, for any place. No daylight time, so every day has 24 hours."""
    return round(lon / 15)


def to_local_standard(times, lon, start=None, end=None):
    """ISO hours in UTC to local standard time at `lon`: (times, the indexes kept), kept within the dates start..end if given, so each date kept is whole."""
    t = np.array(times, dtype="datetime64[m]") + np.timedelta64(local_standard_offset(lon) * 60, "m")
    days = t.astype("datetime64[D]")
    keep = np.ones(len(t), dtype=bool)
    if start:
        keep &= days >= np.datetime64(start)
    if end:
        keep &= days <= np.datetime64(end)
    return [str(x)[:16] for x in t[keep]], np.flatnonzero(keep)


def open_meteo_local_standard(payload, lon, start=None, end=None):
    """An Open-Meteo response asked for in UTC, moved to local standard time at `lon` and trimmed to whole days."""
    h = payload["hourly"]
    times, keep = to_local_standard(h["time"], lon, start, end)
    hourly = {k: ([v[i] for i in keep] if k != "time" else times) for k, v in h.items()}
    return {**payload, "hourly": hourly, "timezone": f"local standard time, UTC{local_standard_offset(lon):+d}"}


def _wider(start, end):
    d = lambda x: str(x)
    return d(np.datetime64(start) - 1), d(np.datetime64(end) + 1)


def fetch_open_meteo(lat, lon, start="1995-01-01", end="2024-12-31", tz=None, cache=None):
    """Download hourly temperature and humidity for one point from Open-Meteo's best match (about 7 MB for 30 years), in local standard time at the point unless `tz` names a time zone. With cache,
    a path to a JSON file, the response is saved there and reused."""
    if cache and os.path.exists(cache):
        return from_open_meteo_json(cache)
    if tz:
        url = OPEN_METEO.format(lat=lat, lon=lon, start=start, end=end, tz=tz.replace("/", "%2F"))
        with urllib.request.urlopen(url, timeout=300) as r:
            payload = json.load(r)
    else:
        a, b = _wider(start, end)
        with urllib.request.urlopen(OPEN_METEO.format(lat=lat, lon=lon, start=a, end=b, tz="GMT"), timeout=300) as r:
            payload = open_meteo_local_standard(json.load(r), lon, start, end)
    if cache:
        os.makedirs(os.path.dirname(os.path.abspath(cache)), exist_ok=True)
        with open(cache, "w") as f:
            json.dump(payload, f)
    return from_open_meteo_json(payload)
