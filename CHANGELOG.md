# Changelog

Package changes (code). Changes to the numbers are listed by model version on the Water Ledger methods page.

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
