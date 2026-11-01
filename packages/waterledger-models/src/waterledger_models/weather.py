"""Hourly weather for the models: ERA5 temperature and humidity from the Open-Meteo archive, as an xarray Dataset (needs
waterledger-models[ensemble]). waterledger_data.climate has the other sources (NOAA stations, NASA POWER) for the builders."""
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
                      attrs={"source": "ERA5 reanalysis via the Open-Meteo archive API", "latitude": payload.get("latitude"),
                             "longitude": payload.get("longitude")})


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
    """Download hourly ERA5 temperature and humidity for one point (about 7 MB for 30 years), in local standard time at the point unless `tz` names a time zone. With cache,
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
