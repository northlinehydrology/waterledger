# Changelog

Package changes (code). Changes to the numbers are listed by model version on the Water Ledger methods page.

## Unreleased

Model version 1.2; no estimate changes. Michigan's numbers are unchanged.

- **`waterledger_data.wateruse`**: water use by county and category for any state, each layer with a basis block
  (source, year, reported or estimate, withdrawals or use, threshold, what each category holds, caveats):
  - `usgs_2015(state=None)`: USGS's revised 2015 county estimates (Sleckman, Ross and Cook 2026, doi:10.5066/P14Q6AVK),
    fresh plus saline, ground and surface, and public supply delivered to homes; labeled an estimate.
  - `ohio(year=None)`: ODNR Water Withdrawal Facility Registration, facility reports totaled by county and primary use
    (latest complete year, 2024; years since 2015 cached).
  - `texas(year=None, path=None)`: TWDB Water Use Survey historical estimates by county (report 7), downloaded through
    TWDB's report viewer into dated copies (`fetch_twdb`); a clear error says what to do if the viewer changes.
  - `virginia(year=2024)`: DEQ's locality totals (Annual Water Resources Report, Table 21; excluding power), read from
    the report PDF; totals only.
  - Categories are a fixed set: public_supply, domestic, commercial, industrial, irrigation, golf, livestock,
    aquaculture, mining, thermoelectric, other, total. Each source's own categories are kept in `source_values`.
  - `pypdf` becomes a dependency of `waterledger-data` (pure Python, no dependencies of its own).
- **`place.context().supply`** gains `county_water_use` (the state's own figures where Water Ledger has them, else
  USGS's) and `county_water_use_usgs` (USGS's 2015 estimates, with deliveries to homes), as `CountyWaterUse` records;
  the national tier also fills `county_use_mgd`. Michigan's `county_water_use` is EGLE's reported withdrawals (the
  figures waterledger.org/mi shows, in the shared categories); its `county_use_mgd` is unchanged.
- **Snapshot format 2:** a `wateruse.json` (format 1 of that file: `national` and `state` layers) and the downloaded
  inputs behind it under `inputs/wateruse/`, listed in the manifest's `inputs` with checksums (not downloaded by the
  package); the manifest records the water-use sources and `water_use_years`. Snapshots in format 1 read as having no
  county water use. `waterledger build-state` gains a `wateruse` stage, and the statewide checks a `county_water_use`
  coverage minimum.

## 3.1.0 (Oct 30, 2026)

Model version 1.2; no numbers change.

- `waterledger_data.power.state_retail_mwh(state, year=None)`: all retail electricity sold in any state in a year
  (EIA-861 Parts A, B and D, as EIA sums them for a state). `michigan_retail_mwh` now uses it and gives the same answer.
- `waterledger_data.power.residential(state, year=None)`: a state's residential customers and average monthly use per
  home, from the same EIA-861 file.
- `waterledger_data.power.latest_eia861()`: the newest EIA-861 year on disk, or the newest year EIA has posted.
- Methods briefs (`docs/methods/`): an overall method shared by every state, then what is specific to each state.

## 3.0.0 (Oct 29, 2026)

Water Ledger for any state. Model version 1.2; Michigan's numbers unchanged.

- **Breaking:** `waterledger.states.mi.build_moratoria` and the `moratoria` part of `waterledger build mi` are removed.
  Proposal and moratorium trackers are maintained with waterledger.org, not in the packages.
- **The national tier** ([design 0002](docs/design/0002-national-tier.md)): `wl.place()`, `place.context()` and
  `site.estimate()` in any state, from national datasets: Census places, EPA water systems, CWNS and ECHO sewer plants,
  USGS watersheds with EPA ATTAINS impairments, NOAA ISD weather by climate division with Atlas 14 design storms, and
  HIFLD and EIA-861 electric utilities with power-plant water per kWh by grid region. `wl.place(lat=, lon=)` returns the
  most local government at a point. Utilities gain `balancing_authority` and `power_plant_water_l_per_kwh`.
- **State snapshots** ([design 0003](docs/design/0003-data-releases.md)): each state's data is a dated, checksummed
  snapshot at data.waterledger.org, downloaded and cached on first use; offline, the newest cached snapshot is used. With
  no snapshot, `WATERLEDGER_FALLBACK` decides whether to ask, build locally or fail. `WATERLEDGER_DATA=live` and
  `WATERLEDGER_DATA_DATE` select live data or a pinned snapshot. Michigan, Ohio, Virginia and Texas are published;
  Michigan's snapshot carries its site files, so its answers are identical either way.
- **Commands:** `waterledger build-state ST` builds any state stage by stage with progress bars, resuming where it
  stopped, and runs statewide checks (layer coverage minimums; 50 random places through every step and design).
  `waterledger snapshot ST --out DIR` and `waterledger check-snapshot ST --dir DIR` write and check a snapshot.
- **`waterledger_data`:** new `census`, `supply`, `wastewater`, `receiving`, `divisions` and `energy` modules for any state;
  the watershed tracer (formerly the separate attains-trace package) as `waterledger_data.trace`, with the
  `waterledger-trace` command; geopandas, shapely, pyarrow and tqdm become dependencies; matplotlib is dropped.
- **`waterledger_models.hydrology`:** SCS curve-number runoff, Theis drawdown and Glover stream depletion.
- A cause counts as having a TMDL when any assessment unit listing it is in category 4A, on every path.
- Methods: a page per state at [waterledger.org/methods](https://waterledger.org/methods/) and a two-page brief per state
  in [docs/methods](docs/methods/).

## 2.0.0 (Oct 29, 2026)

The 2.0 API, per [design 0001](docs/design/0001-schema-and-api.md). Model version 1.2; numbers unchanged.

- **New front door** in `waterledger`: `wl.place()`, `Place`, `Context` (jurisdiction, supply, wastewater, receiving,
  climate, energy), `DataCenter`, `Site`, `site.estimate()` returning an `Estimate`, and `site.to_bmi_config()`. All are
  validated pydantic models that round-trip through JSON. Michigan is available; other states come through the national
  tier in 2.x.
- **States as folders** (`waterledger.states.<st>`), each with a builder and a provider; Michigan's builder moved to
  `states/mi/build.py`, and existing imports still work.
- **Published data:** without a local site, Michigan's published data files are downloaded and cached.
- **Models** (`waterledger-models`): one physics module; xarray ensembles with dask; lake-source ensembles; CSDMS BMI 2.0
  components checked by `bmi-tester` in CI; STAC publishing; an Open-Meteo weather loader. Optional installs:
  `[ensemble]`, `[bmi]`, `[stac]`, `[all]`.
- **Versions decoupled:** package versions follow semver; `MODEL_VERSION` tracks the numbers.

## 0.1.x and 1.2.x (Oct 29, 2026)

First releases: the models, public data ingest and Michigan builder moved out of Northline's engine.
