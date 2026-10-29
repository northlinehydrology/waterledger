"""Open-Meteo responses load as an xarray Dataset the ensembles and BMI components can read."""
import json

import numpy as np

from waterledger_models.weather import from_open_meteo_json


def test_reads_a_saved_response(tmp_path):
    payload = {"latitude": 42.9, "longitude": -85.5, "hourly": {"time": ["2024-07-01T00:00", "2024-07-01T01:00"],
                                                                 "temperature_2m": [21.5, 20.9], "relative_humidity_2m": [80, 84]}}
    f = tmp_path / "w.json"
    f.write_text(json.dumps(payload))
    for src in (payload, str(f)):
        ds = from_open_meteo_json(src)
        assert list(ds.air_temperature.values) == [21.5, 20.9] and ds.relative_humidity.attrs["units"] == "%"
        assert ds.time.values[1] - ds.time.values[0] == np.timedelta64(60, "m") and ds.attrs["latitude"] == 42.9
