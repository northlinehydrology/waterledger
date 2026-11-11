# Water Ledger

[![tests](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml)
[![nightly](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml)
[![PyPI](https://img.shields.io/pypi/v/waterledger.svg)](https://pypi.org/project/waterledger/)

Open Python tools for estimating the water and electricity that large new users add, starting with data
centers and battery cell plants, and for assembling the public U.S. water data around any place: water systems, watersheds, impaired waters,
sewer plants, weather and design storms.

- **Weather-driven cooling water model** for cooling towers, hybrid, closed loop, and dry coolers with adiabatic pre-cooling,
  hour by hour over decades of weather, with Monte Carlo uncertainty over published parameter ranges; plus lake-source
  (once-through) cooling and staff water.
- **Battery cell plant model**: the plant's heat, electricity, fuel and water hour by hour per GWh/yr of cells, on the same
  cooling towers, hybrid and dry coolers and Great Lake once-through cooling, for NMC and LFP cells; where the water
  returns (the sewer or the source); checked against every U.S. plant whose environmental assessment projects its water.
- **Power supply scenarios**: what serves a user's hourly electricity, hypothetical new gas plants (combined cycle, turbines,
  engines, fuel cells, each a water user on the same cooling physics), new solar and wind from the same hourly weather, or the
  grid, with the water each takes, unserved hours, and solar and wind projects' land, runoff and construction water.
- **Mass and energy balances** that close in every hour of every run, for every cooling design, held to it by `tests/test_balances.py`.
- **Hourly electricity from the same heat balance**, by design and weather, after Lei and Masanet (2022): average power, PUE,
  and the hottest hour with every computer at capacity.
- **Vectorized ensembles** as xarray Datasets, with dask across many locations.
- **CSDMS Basic Model Interface (BMI 2.0) components**, so coupling frameworks such as NOAA's NextGen can drive the
  models step by step.
- **Public data for any U.S. place**, fetched once and cached: Census, EPA, USGS, NOAA and EIA, with each place's
  downstream path traced across state lines. Michigan, Ohio, Virginia, Texas, Wisconsin and Indiana are published as checked snapshots.
- **Reproducible**: tests reproduce the published Water Ledger estimates exactly, and the data sources are checked nightly.

[waterledger.org](https://waterledger.org) is powered by these packages.

## Install

```bash
pip install waterledger
```

That installs all three packages. A framework that only needs the models can install `waterledger-models` (numpy
and numba), adding `[ensemble]`, `[bmi]`, `[stac]` or `[all]` for the optional parts.

| Package | Import | What it holds |
|---|---|---|
| `waterledger-models` | `waterledger_models` | the models: data center cooling water and electricity, lake-source cooling, staff water, site runoff quality; ensembles, BMI, STAC |
| `waterledger-data` | `waterledger_data` | public U.S. water data for any place, fetched once and cached |
| `waterledger` | `waterledger` | the objects (Place, Context, Facility, Site, Estimate), state providers and builders (`waterledger build mi`); `import waterledger as wl` brings everything |

## Quickstart

```python
import waterledger as wl

place = wl.place("Gaines charter township, MI")      # or wl.place(geoid="2608131240")
site = wl.Site(place=place, facility=wl.DataCenter(it_mw=300, cooling="hybrid"))
est = site.estimate()
warm = wl.Site(place=place, facility=wl.DataCenter(it_mw=300, cooling="hybrid", plant="warm")).estimate()   # the plant inside: shared (default), warm or chilled

est.water.withdrawn.avg          # Range(p10=..., p50=..., p90=...), million gallons a day
est.water.withdrawn.peak_day     # on a 1-in-10-year peak day
est.water.withdrawn_peak_full_capacity   # the same day with every computer at capacity all day: an upper case, not the main number
est.water.condensate.avg         # water a coil takes out of outside air; withdrawn + condensate = consumed + returned on the middle estimate
est.electricity.avg_mw           # average power, MW, from the hourly heat balance at this place's weather
est.electricity.peak_mw          # the 1-in-10-year hottest hour, every computer at capacity
est.electricity.peak_day_mw      # the 1-in-10-year peak day's average power (from model 1.9; None for lake-source cooling)
est.site.source, est.site.wastewater     # the choices, with defaults filled in
site.estimate(weather="local")   # the model run at the place's own point on Open-Meteo's best match instead of its ERA5 cell's results (about 30 seconds)
est.comparisons                  # against what is already there: the water system's connections, the county's water, the sewer plant and its spare room, the utilities and the state; a very small water system gets no percent
est.before_after                 # what changes at the place, today and after, as numbers
est.site_loads                   # sediment, phosphorus and nitrogen in runoff from the finished site alone, typical wet ponds and no controls; construction and cooling water phosphorus beside them
est.levels                       # the levels a reader sees on waterledger.org, by card; waterledger.levels has the bands and levels.compare the verdict against a reported figure
est.not_covered                  # what isn't covered yet for this state, in words

from waterledger_models.supply.scenario import Scenario, Gas   # power supply scenarios (design 0014): every plant hypothetical
est = site.estimate(supply={"own_gas": Scenario(residual="none", gas=Gas("cc", "towers", unit_mw=150)),
                            "pv_wind": Scenario(pv_share=0.6, wind_share=0.6)})     # runs at the place's ERA5 cell, about 30 seconds
est.supply["own_gas"].local_consumed     # water the campus's own gas plant evaporates, MGD, on the campus's source or system
est.supply["pv_wind"].share_grid         # the share of the year's MWh the grid still serves, hour by hour; also unserved_hours_annual, land
est.household_wells              # the aquifer most household wells draw from, how deep, the water level, where a state has well records
site.by_design().best            # the cooling design that evaporates least in total, campus and power plants; also .designs and the closed loop figures
est.equivalents.homes            # the water as homes at the state's own water for a home (.home_gpd: USGS 2015 over ACS 2015 households); also .golf_courses, .evaporated_share, .electricity_homes, .share_of_home_customers
est.power_plants["state_mix"].consumed   # water at power plants for one power option, MGD; also .withdrawn, .returned; est.site.power names the one in use
est.grid_water.consumed_peak_day         # the place's balancing authority, hour by hour (model 1.11): average day and peak day, average and marginal mix
est.model_dump_json()            # the whole estimate as JSON

ctx = place.context()            # the public water facts around the place, by category
ctx.supply.systems               # public water systems
ctx.wastewater.plants            # sewer plants, nearest first
ctx.receiving.downstream         # the path the water takes, with impaired waters and cleanup plans; a reach's .assessed says whether the state assessed it
ctx.climate.design_storms_in     # NOAA Atlas 14 design storms
ctx.climate.cell                 # the ERA5 cell the cooling weather comes from; .cell_land, .cell_moved, .weather_corrected
ctx.energy.utilities             # electric utilities and their loads
```

They are validated, round-trip through JSON, and are described in
[docs/design/0001-schema-and-api.md](docs/design/0001-schema-and-api.md).

### States

| State | Places | Weather | Methods |
|---|---|---|---|
| Michigan | 1,541 cities and townships | ERA5, each place's own cell (272 cells) | [waterledger.org/methods/mi](https://waterledger.org/methods/mi/), [brief](docs/methods/mi.pdf) |
| Ohio | 2,318 cities, villages, townships and counties | ERA5, each place's own cell (203 cells) | [waterledger.org/methods/oh](https://waterledger.org/methods/oh/), [brief](docs/methods/oh.pdf) |
| Virginia | 322 cities, towns and counties | ERA5, each place's own cell (148 cells) | [waterledger.org/methods/va](https://waterledger.org/methods/va/), [brief](docs/methods/va.pdf) |
| Texas | 1,481 cities, towns and counties | ERA5, each place's own cell (616 cells) | [waterledger.org/methods/tx](https://waterledger.org/methods/tx/), [brief](docs/methods/tx.pdf) |
| Wisconsin | 1,922 cities, villages, towns and counties | ERA5, each place's own cell (283 cells) | [waterledger.org/methods/wi](https://waterledger.org/methods/wi/), [brief](docs/methods/wi.pdf) |
| Indiana | 1,661 cities, towns, townships and counties | ERA5, each place's own cell (183 cells) | [waterledger.org/methods/in](https://waterledger.org/methods/in/), [brief](docs/methods/in.pdf) |

**Model 1.13** adds power supply scenarios ([design 0014](docs/design/0014-power-supply-scenarios.md)) and the shared Monte
Carlo runner, and changes no data center or place number, so it reads model 1.11's snapshots too:
- **The shared runner** (`waterledger_models.runs`): one Monte Carlo loop for every water user type: the draws, the standard
  loads (the run's, the peak day's, full capacity), the daily statistics, grid water and the result names
  ([design 0010](docs/design/0010-water-user-types.md)'s standard treatment). Data centers and battery cell plants run through
  it; every value matches their records from before, apart from the power figures, which differ in the last bit (at most
  5e-16 relative). `extra=` hands a caller each draw's hourly electricity.
- **New gas plants** (`waterledger_models.gas`): combined cycle (on towers, hybrid, assist, dry or lake cooling), simple-cycle
  turbines (dry low-NOx or water injection, inlet cooling as a setting), engines and fuel cells, units dispatched hour by hour
  with hot-weather derate, part load and outages, the condenser on the shared heat rejection. Wastewater goes where new plants'
  does (EIA-860 in aggregate): back to the source for a combined cycle on surface water, the sewer otherwise, with a stream
  discharge (the new `to_stream` return role) or zero discharge as settings. `GasPlantBmi`.
  - **Checked, not tuned:** a turbine's output at 100 F is 78% of its rating (EPA CHP Catalog, 80%); a combined cycle on towers
    at ISO weather gives 158 and 206 gal/MWh consumed and withdrawn against NETL's 186 and 240; against EIA's 2024 fleet, in
    aggregate, 21% under in the Great Lakes at a new plant's heat rate and 12% over at the fleet's own
    ([docs/methods/power_supply](docs/methods/power_supply/)); a year of weather lands inside the published ranges by design.
- **New solar and wind** (`waterledger_models.supply`): PV by the PVWatts chain, within 0.04% of the AC rating of pvlib's in
  every hour of a test year; wind through the IEA 3.4 MW reference turbine's curve; both from ERA5 radiation and 100 m wind
  at the user's own cell (`waterledger_data.era5.fetch_supply`). PV is scaled to what EIA's 2024 tracking fleet delivered (944
  plants, 24.1% against the chain's 28.5% on ERA5; model 1.14), so West Michigan's tracking PV runs near 19% and wind at 28%
  (wind not yet checked against its fleet).
  Land, runoff and one-time construction water and sediment by project size (`supply.land`).
- **Scenarios** (`supply.scenario`): resources and a residual rule (the grid by default, or islanded), dispatched hour by
  hour; plants sized once (gas N+1 at the design dry-bulb, renewables by share of annual MWh); surplus exported without water
  credit; unserved hours reported, with the longest run (gas outages last 48 hours on average [A], model 1.14). The grid-only scenario is today's grid water to the bit.
- At a place, `site.estimate(supply=...)` gives `est.supply` for data centers (waterledger 3.18.0); other types follow with design
  0010's facility contract. waterledger.org is unchanged.

**Model 1.12** adds battery cell plants ([design 0009](docs/design/0009-battery-cell-plants.md)) and changes no data
center or place number, so it skips the snapshots and reads model 1.11's (`waterledger_models.MODELS`):
- **The plant** (`waterledger_models.battery`): the energy to make a kWh of cells (nearly all of it electrode drying, dry
  rooms and formation), the share of it reaching the cooling water and the outdoor air load, hour by hour on the shared
  heat rejection; process water (anode slurry, water leaving in recovered NMP, boiler make-up, other purified water and the
  purification's reject) and staff water. Designs `dry`, `assist`, `hybrid`, `towers` and `lake`; full output by default,
  or a sampled utilization. LFP plants take 1.2-1.7 times the plant energy per
  kWh [A] (Degen et al. 2023: the same energy per m2 of electrode, about 1.67 times the area per kWh).
- **Returns by destination**: tower blowdown, process returns and staff water to the sewer; the lake design's once-through
  water, less its forced evaporation, to the source.
- **What data centers get, battery plants get** ([design 0010](docs/design/0010-water-user-types.md)'s standard treatment,
  Nov 10): water at the power plants (`grid=`, through the same `grid.RunWater`), the full-capacity peak day and highest
  hour, and every design the shared equipment allows. Still to come: the shared Monte Carlo runner, and water limits and
  dissolved mass in `BatteryCellBmi`.
- **Checked, not fit**, at the six U.S. plants with projected water in a DOE environmental assessment, each at its own
  location and size (`examples/battery_cell_plants_ea_check.py`): four inside the model's 80% range, Stanton, TN on the
  medians, Buckeye, AZ just above, and Delta Township (Lansing), MI well above, the most water per GWh/yr of any
  projection. No public figure checks the dry design.
- **Sensitivity** (Sobol' and Morris, `docs/methods/sensitivity/battery/`): with towers, the plant energy per kWh and its
  share to the cooling water carry about 85% of the variance in withdrawal; cycles of concentration carry the sewer flow;
  boiler make-up leads the dry and hybrid designs.
- **Shared by every water user**: the heat rejection with assist's pads (`heat_rejection`), Great Lake once-through cooling
  (`once_through`), daily statistics (`daily`) and water at the power plants in a run (`grid.RunWater`) moved out of
  `datacenter` unchanged, and the old names still import. Cycles of
  concentration and the hybrid's switch margin are each user's own (`heat_rejection.OPERATING`).
- The plant's place-based estimate (`wl.place(...)`) comes with design 0010's water user types; waterledger.org is
  unchanged.

**Model 1.11** adds the campus's water at the power plants hour by hour, and every state's cells are rerun for it
([design 0008](docs/design/0008-power-at-the-grid.md), part 1):
- **The grid component** (`waterledger_models.grid`, `GridWaterBmi`) turns any user's hourly electricity into water at the
  plants of a balancing authority (EIA-930 generation by fuel from 2019, with the BA's 2024 plant water per MWh by fuel and
  month), binned by month, hour and the temperature at the user, on the average mix and the marginal one.
- **In the cell runs**, for each BA serving the cell's places, so `est.grid_water` gives the place's BA's water for the
  campus's own electricity on the average day and the 1-in-10-year peak day. The table is fit on 2019-2024, the years the
  grid's hours and the cells' weather share, so it runs about 10-16% above 2024's plant water per MWh (methods log,
  Nov 9). Seven Virginia places have no utility in the snapshot and no hourly grid water. The annual power options in
  `est.power_plants` are unchanged.
- **A power plant's withdrawal is at least its consumption** in the state tables, as in the BA table: three plants that
  report consumption and no withdrawal (Florida 46.562 to 46.582 L/kWh withdrawn, North Carolina 33.057 to 33.077).

**Model 1.10** changes the numbers in three ways, and every state's snapshot is rebuilt for it ([design 0007](docs/design/0007-cooling-plants.md)):
- **The cooling plant inside the building is a choice** (`DataCenter(plant=...)`):
  - `shared`, the default: one facility water loop for the air handlers and the liquid racks;
  - `warm`: a separate warm-water loop for liquid-cooled computers;
  - `chilled`: a conventional chilled-water plant.

  Through model 1.9 every plant ran supply air at 27-35 C and liquid racks at 32-45 C, the warm-water best case. Each cell
  is now run for every plant, and the snapshots carry them all (`per_100mw` for the default, `per_100mw_plants` for the
  others). Against model 1.9, the default's hybrid and assist water rises 30-40% on the average day and about 20% on the
  peak day, towers' peak day 6-7%, and peak-day power 5-7 MW per 100 MW of IT; the warm plant stays within 2% of model
  1.9's water (methods log, Nov 8).
- **The weather correction maps the dew point itself** (qm-3), not the dew-point depression, so a hot-day temperature
  correction no longer makes peak days humid. The ERA5 check gains W7, a peak-day wet-bulb criterion.
- **The dry coolers' glycol** has propylene glycol's heat capacity and density (30-40% by volume; Dow's data sheet), not
  water's.

**Model 1.9** (3.12.0) changes the numbers in four ways, and every state's snapshot is rebuilt for it:
- **The dry coolers' glycol loop.** Dry, assist and hybrid plants carry a plate exchanger's approach and a glycol loop pump,
  as towers already did, so dry heat rejection costs more electricity than towers. In West Michigan at central values a dry
  plant takes 2.4% more on average, 7.8% more on the 1-in-10-year peak day and 7% more in the hottest hour. Assist and
  hybrid switch to wet sooner and use more water.
- **Peak-day power** (`power_mw_peak_day_1in10`): the 1-in-10-year peak day's average power at the peak-day load, beside the
  hottest hour at capacity.
- **Station correction on land cells.** Land cells (at least 90% land) are corrected toward the land stations within 100 km,
  as shore cells are toward shore stations ([design 0005](docs/design/0005-era5-quantile-mapping.md); methods log, Nov 6).
- **A place's own electric utility first**, where a larger one is drawn over whole counties (Madison, Bedford, Culpeper).

**Model 1.8** (3.10.0) changed where the cooling weather comes from. The cooling equations were unchanged.
- **Each place's own ERA5 cell.** Every place takes its weather from its ERA5 grid cell (0.25 degrees, about 10 km
  away), 1995-2024, in place of Michigan's eight regions and the other states' one NOAA station per climate division
  ([design 0004](docs/design/0004-era5-weather.md)).
- **The land rule.** Where a place's nearest cell is mostly water, it takes the nearest cell that is at least half land
  (189 places).
- **Shore correction.** Where a cell is under 90% land, its temperature and dew point are corrected toward NOAA and
  Environment and Climate Change Canada stations near the shore within 100 km (619 places;
  [design 0005](docs/design/0005-era5-quantile-mapping.md)).
- **Faster runs.** The runs work 4,096 hours at a time with the same numbers to the bit, about 40 s a cell at ten workers.
- **Snapshot format 3.** The snapshots carry each cell's results (`cells/`). Rainfall, road salt and golf stay with the
  regions and division stations.

Michigan has its own layers (state-reported water use, domestic wells, trout streams, lake-source cooling, state rules)
and matches [waterledger.org/mi](https://waterledger.org/mi/) exactly. The other states use national datasets only
([design 0002](docs/design/0002-national-tier.md)); any other state can be built locally with `waterledger build-state ST`.
Adding a state from start to publication, step by step with what each step writes and how to tell it's done, is in
[docs/add-a-state.md](docs/add-a-state.md).

### Data

Each state's data is a dated snapshot at [data.waterledger.org](https://data.waterledger.org), checked against its
manifest and cached on first use ([design 0003](docs/design/0003-data-releases.md)). A published snapshot never changes, and a
package reads the newest one for its own model version (or, for a version that skips the snapshots, the version it names
in `waterledger_models.MODELS`), so a new model's numbers don't reach an older package. An estimate's `model_version` is the model of the data it read. Offline, the newest cached snapshot is
used. If no snapshot can be had, the package can build the state from the public sources instead (15 to 30 minutes the
first time, resumable):

| Setting | Values |
|---|---|
| `WATERLEDGER_FALLBACK` | `ask` (default at a terminal), `build`, `fail` (default in scripts) |
| `WATERLEDGER_DATA` | `snapshot` (default) or `live` (skip snapshots, build from the sources) |
| `WATERLEDGER_DATA_DATE` | pin a snapshot date to reproduce an old result |
| `WATERLEDGER_WORKERS` | cooling runs at once in a local build: one by default, every core under `waterledger build-state` |

### The models directly

```python
from waterledger_models.datacenter import run_ensemble, summarize
from waterledger_models.weather import fetch_open_meteo

w = fetch_open_meteo(42.88, -85.52, cache=".cache/grand_rapids.json")     # 30 years of hourly weather, best match
ds = run_ensemble(w.time.values, w.air_temperature.values, w.relative_humidity.values, mw=300, n=400)
s = summarize(ds)                                    # (design, stat, quantile), staff water included
s["withdrawn"].sel(design="towers", stat="peak_1in10")      # million gallons on a 1-in-10-year peak day

from waterledger_models.datacenter import physics
physics.RANGES["switch_margin"], physics.SOURCES["switch_margin"]    # a parameter's range and where it comes from

from waterledger_models.battery import plant                             # a battery cell plant, per GWh/yr of cells
times = [str(t)[:16] for t in w.time.values]
r = plant.run_location(times, w.air_temperature.values, w.relative_humidity.values, gwh=43.75, chemistry="nmc")
r["towers"]["withdrawn_avg"]["p50"], r["towers"]["to_sewer_avg"]["p50"]  # MGD: the median withdrawal and flow to the sewer
```

### Step by step through BMI

```python
from waterledger_models.datacenter import CoolingWaterBmi
from waterledger_models.weather import design_dry_bulb

m = CoolingWaterBmi()
m.initialize({"design": "hybrid", "it_capacity_mw": 300,       # or a YAML file with the same keys
              "humidity": "specific",                            # NextGen's AORC: specific humidity and pressure, converted inside
              "parameters": {"design_db": design_dry_bulb(t2m)}})   # a hybrid's 0.4% design dry-bulb, from the place's hourly record
m.set_value("atmosphere_bottom_air__temperature", ...)           # this hour's inputs
m.update()                                                       # computes the hour; outputs change only here
m.get_value("data_center_cooling_water__withdrawal_volume_flux", ...)
```

Under a water rule, set `water_user_water__withdrawal_volume_flux_limit` (m3 s-1) or `water_user__dry_mode_flag` before
`update()`. The heat still goes: a hybrid or assist plant moves it to dry coolers and chillers, at more electricity, and a towers
plant sheds the load it can't cool. `data_center__unremoved_heat_power` reports what isn't removed. With intake concentrations
set, the component reports the dissolved mass in its return and the return's temperature (design 0006).

`waterledger_models.battery.bmi.BatteryCellBmi` runs a battery cell plant the same way (`design`, `capacity_gwh`,
`chemistry`), reporting the water user roles, the return split to the sewer and to the source, electricity and fuel burned
on site. It has no water limits yet. `waterledger_models.gas.bmi.GasPlantBmi` serves the demand set each step
(`power_plant__electric_power_demand`) and reports what it served and could not, its fuel and the water roles.

A component of your own at one point can build on `waterledger_models.datacenter.ScalarPointBmi`, which supplies every BMI
function but `initialize()`; its docstring has the contract. `waterledger_models.hydrology.stream_depletion` takes arrays,
for a well's response at every step of a run.

More in [examples/](examples/): a BMI coupling loop, eight Michigan locations in parallel, a STAC catalog of results, and the
battery cell plant model at every U.S. plant with projected water.

## Stability

The packages are in beta, whatever the 3.x number suggests. Within 3.x the API can still change in a minor release, and every such
change is listed under **Breaking** in [CHANGELOG.md](CHANGELOG.md). The numbers are versioned separately, by `MODEL_VERSION`
(below). From 3.10 on, a breaking change to the public API (`wl.place`, `Place`, `Context`, `Site`, `Estimate`, the BMI
components and the command line) waits for 4.0 and does not ship in a 3.x minor release.

## Model version

Three version numbers, each with one meaning:

- **Package versions** (semver) change with the code: a major version for breaking changes.
- **`waterledger_models.MODEL_VERSION`** (now 1.14) changes when the numbers change; the golden test fails until that is
  done deliberately. Every published estimate names the model version that produced it. One version covers every water
  user type. `waterledger_models.MODELS` records, from 1.12, which types a version changes and the model of the snapshots it
  reads: a version that leaves the snapshots' numbers alone (data centers, the places' water and power) skips them and reads
  the last rebuilt ones. Model 1.12 adds battery cell plants and reads model 1.11's snapshots and cell runs, so a data center
  estimate still names model 1.11. Model 1.13 adds gas plants and supply scenarios the same way, and model 1.14 changes them
  (outages that last days, PV against the 2024 fleet).
- **The snapshot format version** (now 3, in each snapshot's manifest) changes when the structure of a state's data
  files does. Format 3 (from model 1.8) carries cooling by ERA5 cell (`cells/`). The package still reads format 2, which the
  published model 1.7 snapshots are.

## Development

```bash
uv sync                  # one environment with all three packages, editable
uv run pytest            # unit tests, the golden model test and the ensemble-to-loop checks
uv run pytest -m live    # every public data source still answers
WATERLEDGER_FETCH=1 uv run pytest tests/test_reproduction.py    # reproduce the published estimates (downloads weather)
uv run waterledger build-state OH       # build any state, Michigan included, from the public sources (resumes from its cache)
uv run waterledger snapshot OH --out snapshots && uv run waterledger check-snapshot OH --dir snapshots
```

Checks: `tests` runs on every push (lint, tests on Python 3.11 to 3.13); `nightly` builds the packages, tests the built
wheels in a clean environment, checks the data sources and reproduces the published estimates, and opens an issue if
anything fails (the snapshot tests need the ERA5 cell runs, so they skip there and run where the runs are); `publish` releases to PyPI from a `v*` tag by trusted publishing; `build-state` builds a state's layers on
GitHub (its snapshot needs the ERA5 cell runs, so they are written and checked locally and published with `waterledger publish`).

Paths (download cache, site output) come from `WATERLEDGER_CACHE` / `WATERLEDGER_SITE` or a `waterledger.toml` (see
`waterledger_data.config`).

### The ERA5 runs

The cooling numbers come from one run per ERA5 cell and cooling plant: about 9 hours for the five states' 1,507 cells,
model 1.11's three plants and the grid's hourly water, at twelve workers on one machine, on the compiled hourly loop
(`datacenter.kernel`), in parts started by hand ([design 0004](docs/design/0004-era5-weather.md), section 3). Each part fetches its cells from Open-Meteo's open
copy of ERA5, corrects them toward nearby stations ([design 0005](docs/design/0005-era5-quantile-mapping.md)), runs them and writes
`CACHE/era5/runs/model<version>/<cell>.json` as each finishes, so a stopped part resumes where it stopped:

```bash
uv sync                                              # the workspace includes waterledger-data[era5] (omfiles, s3fs) for the open copy
uv run waterledger era5 cells TX --part 1/3           # what a part holds, and how much of it is done
uv run waterledger era5 run TX --part 1/3 --workers 10
```

Saving to R2 is optional and off unless set up. With it on, each raw cell series goes to the private bucket `waterledger-raw` at
`era5/<cell>/<fetch date>.npz` (with its request and checksum) and each result to `runs/era5/model<version>/<cell>.json` as it
finishes. A file R2 already has with the same checksum is skipped. Before a part starts, whatever R2 has and this machine
doesn't is pulled, so a part can be restarted on another machine. A failed upload warns and keeps the local file; it never
stops the run.

Publishing uses the same setup, with the public bucket `waterledger-data` behind data.waterledger.org: `waterledger publish ST --dir
snapshot --build build-report/ST_build.json` uploads a snapshot written and checked on this machine, the files first, then its
manifest, then `latest.json`. It stops before sending anything if the snapshot has no checks or its date is already published.

| Setting | R2 through |
|---|---|
| `WATERLEDGER_R2=wrangler` | the wrangler login on this machine (`npx wrangler login`) |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | R2's S3 API, with a token limited to the bucket (`uv sync --extra r2` for boto3) |
| `WATERLEDGER_R2=off`, or `--no-r2` | nothing: off |

## Contributing and project standards

Corrections, bug reports and proposals are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Contributions follow EPA's
guidance on environmental models and the federal Information Quality Act guidelines, and the
[data problem](https://github.com/northlinehydrology/waterledger/issues/new?template=data-problem.yml) form is the
project's request-for-correction process. Also: [governance](GOVERNANCE.md), [code of conduct](CODE_OF_CONDUCT.md),
[security policy](SECURITY.md) and [how to cite](CITATION.cff).

BSD 3-Clause. Copyright Northline Hydrology.
