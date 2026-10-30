# Water Ledger

[![tests](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml)
[![nightly](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml)
[![PyPI](https://img.shields.io/pypi/v/waterledger.svg)](https://pypi.org/project/waterledger/)

Open Python tools for estimating the water that large new users take, use up and send back, starting with data
centers, and for assembling the public U.S. water data around any place: water systems, watersheds, impaired waters,
sewer plants, weather and design storms.

- **Weather-driven cooling water model** for cooling towers, hybrid, closed loop, and dry coolers with adiabatic pre-cooling,
  hour by hour over decades of weather, with Monte Carlo uncertainty over published parameter ranges; plus lake-source
  (once-through) cooling and staff water.
- **Vectorized ensembles** as xarray Datasets, with dask across many locations.
- **CSDMS Basic Model Interface (BMI 2.0) components**, so coupling frameworks such as NOAA's NextGen can drive the
  models step by step.
- **Public data for any U.S. place**, fetched once and cached: Census, EPA, USGS, NOAA and EIA, with each place's
  downstream path traced across state lines. Michigan, Ohio, Virginia and Texas are published as checked snapshots.
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
| `waterledger` | `waterledger` | the objects (Place, Context, Facility, Site, Estimate), state providers and builders (`waterledger build mi`); `import waterledger as wl` brings everything |

## Quickstart

```python
import waterledger as wl

place = wl.place("Gaines charter township, MI")      # or wl.place(geoid="2608131240")
site = wl.Site(place=place, facility=wl.DataCenter(it_mw=300, cooling="hybrid"))
est = site.estimate()

est.water.withdrawn.avg          # Range(p10=..., p50=..., p90=...), million gallons a day
est.water.withdrawn.peak_day     # on a 1-in-10-year peak day
est.site.source, est.site.wastewater     # the choices, with defaults filled in
est.model_dump_json()            # the whole estimate as JSON

ctx = place.context()            # the public water facts around the place, by category
ctx.supply.systems               # public water systems
ctx.wastewater.plants            # sewer plants, nearest first
ctx.receiving.downstream         # the path the water takes, with impaired waters and cleanup plans
ctx.climate.design_storms_in     # NOAA Atlas 14 design storms
ctx.energy.utilities             # electric utilities and their loads
```

They are validated, round-trip through JSON, and are described in
[docs/design/0001-schema-and-api.md](docs/design/0001-schema-and-api.md).

### States

| State | Places | Weather | Methods |
|---|---|---|---|
| Michigan | 1,541 cities and townships | ERA5 at eight regions | [waterledger.org/methods/mi](https://waterledger.org/methods/mi/), [brief](docs/methods/mi.pdf) |
| Ohio | 2,318 cities, villages, townships and counties | NOAA stations, 10 climate divisions | [waterledger.org/methods/oh](https://waterledger.org/methods/oh/), [brief](docs/methods/oh.pdf) |
| Virginia | 322 cities, towns and counties | NOAA stations, 6 climate divisions | [waterledger.org/methods/va](https://waterledger.org/methods/va/), [brief](docs/methods/va.pdf) |
| Texas | 1,481 cities, towns and counties | NOAA stations, 10 climate divisions | [waterledger.org/methods/tx](https://waterledger.org/methods/tx/), [brief](docs/methods/tx.pdf) |

Michigan has its own layers (state-reported water use, domestic wells, trout streams, lake-source cooling, state rules)
and matches [waterledger.org/mi](https://waterledger.org/mi/) exactly. The other states use national datasets only
([design 0002](docs/design/0002-national-tier.md)); any other state can be built locally with `waterledger build-state ST`.

### Data

Each state's data is a dated snapshot at [data.waterledger.org](https://data.waterledger.org), checked against its
manifest and cached on first use ([design 0003](docs/design/0003-data-releases.md)). Offline, the newest cached snapshot is
used. If no snapshot can be had, the package can build the state from the public sources instead (15 to 30 minutes the
first time, resumable):

| Setting | Values |
|---|---|
| `WATERLEDGER_FALLBACK` | `ask` (default at a terminal), `build`, `fail` (default in scripts) |
| `WATERLEDGER_DATA` | `snapshot` (default) or `live` (skip snapshots, build from the sources) |
| `WATERLEDGER_DATA_DATE` | pin a snapshot date to reproduce an old result |

### The models directly

```python
from waterledger_models.datacenter import run_ensemble, summarize
from waterledger_models.weather import fetch_open_meteo

w = fetch_open_meteo(42.88, -85.52, cache=".cache/grand_rapids.json")     # 30 years of hourly ERA5 weather
ds = run_ensemble(w.time.values, w.air_temperature.values, w.relative_humidity.values, mw=300, n=200)
s = summarize(ds)                                    # (design, stat, quantile), staff water included
s["withdrawn"].sel(design="towers", stat="peak_1in10")      # million gallons on a 1-in-10-year peak day
```

### Step by step through BMI

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

Three version numbers, each with one meaning:

- **Package versions** (semver) change with the code: a major version for breaking changes.
- **`waterledger_models.MODEL_VERSION`** (now 1.4) changes when the numbers change; the golden test fails until that is
  done deliberately. Every published estimate names the model version that produced it.
- **The snapshot format version** (now 2, in each snapshot's manifest) changes when the structure of a state's data
  files does.

## Development

```bash
uv sync                  # one environment with all three packages, editable
uv run pytest            # unit tests, the golden model test and the ensemble-to-loop checks
uv run pytest -m live    # every public data source still answers
WATERLEDGER_FETCH=1 uv run pytest tests/test_reproduction.py    # reproduce the published estimates (downloads weather)
uv run waterledger build-state OH       # build a state from the public sources (cached by stage, resumable)
uv run waterledger snapshot OH --out snapshots && uv run waterledger check-snapshot OH --dir snapshots
```

Checks: `tests` runs on every push (lint, tests on Python 3.11 to 3.13); `nightly` builds the packages, tests the built
wheels in a clean environment, checks the data sources and reproduces the published estimates, and opens an issue if
anything fails; `publish` releases to PyPI from a `v*` tag by trusted publishing; `build-state` builds, checks and (when
asked) publishes a state's snapshot.

Paths (download cache, site output) come from `WATERLEDGER_CACHE` / `WATERLEDGER_SITE` or a `waterledger.toml` (see
`waterledger_data.config`).

## Contributing and project standards

Corrections, bug reports and proposals are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Contributions follow EPA's
guidance on environmental models and the federal Information Quality Act guidelines, and the
[data problem](https://github.com/northlinehydrology/waterledger/issues/new?template=data-problem.yml) form is the
project's request-for-correction process. Also: [governance](GOVERNANCE.md), [code of conduct](CODE_OF_CONDUCT.md),
[security policy](SECURITY.md) and [how to cite](CITATION.cff).

BSD 3-Clause. Copyright Northline Hydrology.
