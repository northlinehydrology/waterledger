# Water Ledger

[![tests](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml)
[![nightly](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml)
[![PyPI](https://img.shields.io/pypi/v/waterledger)](https://pypi.org/project/waterledger/)

Open Python tools for estimating the water that large new users take, use up and send back, starting with data
centers, and for assembling the public U.S. water data around any place: water systems, watersheds, impaired waters,
sewer plants, weather and design storms.

- **Weather-driven cooling water model** for cooling towers, hybrid, and closed loop with or without evaporative assist,
  hour by hour over decades of weather, with Monte Carlo uncertainty over published parameter ranges; plus lake-source
  (once-through) cooling and staff water.
- **Vectorized ensembles** as xarray Datasets, with dask across many locations.
- **CSDMS Basic Model Interface (BMI 2.0) components**, so coupling frameworks such as NOAA's NextGen can drive the
  models step by step.
- **Public data for any place**, fetched once and cached: Census, EPA, USGS, NOAA and EIA.
- **Reproducible**: tests reproduce the published Water Ledger estimates exactly, and the data sources are checked nightly.

[waterledger.org](https://waterledger.org) is powered by these packages.

## Install

```bash
pip install waterledger
```

That installs all three packages. A framework that only needs the models can install `waterledger-models` (numpy
only), adding `[ensemble]`, `[bmi]`, `[stac]` or `[all]` for the optional parts.

| Package | Import | What it holds |
|---|---|---|
| `waterledger-models` | `waterledger_models` | the models: data center cooling water, lake-source cooling, staff water, site runoff quality; ensembles, BMI, STAC |
| `waterledger-data` | `waterledger_data` | public U.S. water data for any place, fetched once and cached |
| `waterledger` | `waterledger` | scenarios and the state builders (`waterledger build mi`); `import waterledger as wl` brings everything |

## Quickstart

```python
import waterledger as wl
from waterledger_models.weather import fetch_open_meteo

w = fetch_open_meteo(42.88, -85.52, cache=".cache/grand_rapids.json")     # 30 years of hourly ERA5 weather
ds = wl.models.datacenter.run_ensemble(w.time.values, w.air_temperature.values, w.relative_humidity.values, mw=300, n=200)
s = wl.models.datacenter.summarize(ds)              # (design, stat, quantile), staff water included
s["withdrawn"].sel(design="towers", stat="peak_1in10")     # million gallons on a 1-in-10-year peak day
```

Step by step through BMI:

```python
from waterledger_models.datacenter import CoolingWaterBmi

m = CoolingWaterBmi()
m.initialize("config.yaml")          # design, it_capacity_mw, forcing, parameter overrides
m.set_value("atmosphere_bottom_air__temperature", ...)
m.update()
m.get_value("data_center_cooling_water__withdrawal_volume_flux", ...)
```

More in [examples/](examples/): a BMI coupling loop, eight Michigan locations in parallel, and a STAC catalog of results.

## Model version

The model is versioned on its own: `waterledger_models.MODEL_VERSION` (now 1.2), and the `waterledger-models` package
version starts with it (1.2.x). A change to the numbers is a new model version; the golden test fails until it is made
deliberately. Every published estimate names the model version that produced it.

## Development

```bash
uv sync                  # one environment with all three packages, editable
uv run pytest            # unit tests, the golden model test and the ensemble-to-loop checks
uv run pytest -m live    # every public data source still answers
WATERLEDGER_FETCH=1 uv run pytest tests/test_reproduction.py    # reproduce the published estimates (downloads weather)
```

Checks: `tests` runs on every push (lint, tests on Python 3.11 to 3.13); `nightly` builds the packages, tests the built
wheels in a clean environment, checks the data sources and reproduces the published estimates, and opens an issue if
anything fails; `publish` releases to PyPI from a `v*` tag by trusted publishing.

Paths (download cache, site output) come from `WATERLEDGER_CACHE` / `WATERLEDGER_SITE` or a `waterledger.toml` (see
`waterledger_data.config`).

BSD 3-Clause. Copyright Northline Hydrology.
