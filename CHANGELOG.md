# Changelog

Package changes (code). Changes to the numbers are listed by model version on the Water Ledger methods page.

## Unreleased

Model version 1.5: the cooling model's energy and mass now close, hour by hour, in every design. Tests in `tests/test_balances.py` hold them to it. Water and electricity estimates change by a few percent; `docs/methods/methods-log.md` has the measured differences.

- **All the electricity leaves as heat.** Heat rejected through the water or coil is facility power less the heat rejection fans. Pump heat now counts, and the sensible heat ratio, which added heat with no energy behind it, is gone.
- **A hybrid's chiller rejects heat through the same split as everything else**: to evaporating water in the wet share and to air in the rest. It was water-cooled even in hours with no evaporation.
- **Drift follows the water through the wet part of a hybrid**, not all the heat.
- **Blowdown comes from the dissolved solids balance**: blowdown + drift = evaporation / (cycles - 1). It left drift out, which counted that water twice.
- **A tower's air flow is capped by what air can carry**, so its fans are not undercounted at high water-to-air ratios.
- **Lake-source cooling has its own electricity and heat from one balance.** The heat factor is its PUE, 1.05-1.17 (was 1.03-1.25), and cooling towers no longer stand in for its electricity.
- **Power plants generate the campus's electricity plus line losses** (`comparisons.LINE_LOSS`, 5%, EIA). Plant water factors are per MWh generated.
- **Farmland sediment keeps the small paved part of the land**, and lake and reuse annual totals use 365.25 days a year like the others.
- **Utilities tied on customers keep one order between builds** (`energy.ranked`): the larger share, then the name. Their order had depended on how the source returned them.

## 3.7.1 (Oct 31, 2026)

- **A state built live answers the same as one from a snapshot.** 3.7.0 added rainfall sources, salt events, residential electricity and state sales to snapshots only, so an estimate in a state without a published snapshot failed. Its power options now list only the state's grid regions, as a snapshot's do. A test holds the two data classes to the same methods.

## 3.7.0 (Oct 31, 2026)

Model version 1.4 stays. No water or power estimate changes. Everything here is at full value; waterledger.org works its comparisons from the rounded water it shows, so its figures can differ by that rounding.

- **`est.equivalents`**: the estimate in homes, golf courses and homes' electricity, the share of the state's home customers, and the share of water that evaporates. Full values; a display rounds them. `waterledger.comparisons` has the functions (`water_homes`, `golf_courses`, `electricity_homes`, `share_of_customers`, `plant_water`, `evaporated_share`).
- **`est.comparisons` covers the county's water, the sewer plant and its spare room, the utilities and the state**, and **`est.before_after`** gives the place's before-and-after as numbers. A utility reporting no sales is left out of the comparison.
- **`site.by_design()`**: the same campus with each cooling design, its totals at the campus and at power plants, which evaporates least, and what closed loop trades against cooling towers. `comparisons.it_mw_from_contract` turns a utility contract into computing capacity.
- **`comparisons.default_power` and `offered_power`** choose and list a site's power options; **`runoff.listed`** is the filter for impairments a site's runoff can add to; **`est.household_wells`** summarizes well records.
- **`waterledger.levels`**: the public levels and verdicts on waterledger.org, with their bands, and `est.levels`. `levels.compare` words a reported figure against an estimate.
- **`est.power_plants`**: water at power plants for each of the state's power options, consumed, withdrawn and returned. `Site(power=...)` chooses one and `est.site.power` names it.
- **`waterledger.national.power.options`**: a state's power options, moved here from Northline's site builder, with the same values. `energy.NEW_GAS`, `energy.wind_solar` and one conversion, `energy.L_KWH_TO_GAL_MWH`, are shared with Michigan.
- **An independent city NOAA has no record for takes its surrounding county's rainfall** (`Climate.rain_from` says which). Lexington, Virginia is the only one in the four published states: Rockbridge County, 44.79 inches. It had the state's median.
- **A county with no rainfall record is now an error.** Only NOAA's "no such record" leaves an area out for that step; any other failure stops the build.
- **Snapshots carry the state's residential electricity** and retail sales, and road salt events (additive). On a snapshot from before 3.7.0, electricity homes and the state comparison are left out and Michigan's salt assumption stands in.

## 3.6.2 (Oct 31, 2026)

Model version 1.4 stays. No estimate of water use changes.

- **Independent cities get rainfall and design storms.** The national tier asked NOAA only for rows at county level, so Virginia's 38 independent cities (Richmond, Virginia Beach, Norfolk and the rest) had none. `national.climate.climate_areas` adds them, for any state that has them. Cooling stations stay on counties.
- **The statewide check now covers rainfall and design storms**, so a gap like that fails the build.
- **NOAA's rate limit no longer loses a county.** `divisions.cag_json` waits and asks again on a 429; a county still refused fails the build instead of being skipped.
- **TWDB's report address is read from its report list** (`wateruse.twdb_report_url`). TWDB now issues new tokens, so the stored address stopped working.

## 3.6.1 (Oct 31, 2026)

- **One rule in every state for a place's own sewer plant** (`wastewater.is_own`): a plant carrying the place's name, within 10 km, comes first; otherwise the nearest plant. Michigan had put a name match first at any distance, and the national tier never did. `SewerPlant.own` says which.

## 3.6.0 (Oct 31, 2026)

Model version 1.4 stays. Estimates carry full values: a middle value that read 1.6 now reads 1.576.

- **Constants the site carried now come from the package**, through its data files: unit factors (`runoff.PARAMS["units"]`), curve numbers, `rain_median_in`, `home_customers` (Michigan's 2025 count), golf season days, withdrawal levels, and proposal sizes (`size_examples`). `national.climate.salt_events` moved here from the site's builder; `runoff.salt` takes `events`.
- **`runoff.storm_mg`**: one storm's runoff by curve number, the method waterledger.org now uses for storms.
- **`site.estimate(weather="local")`**: the model run at the place's nearest ERA5 grid cell instead of its region's stored results; `est.weather` says which. The default is unchanged and matches waterledger.org.
- **`physics.SOURCES`**: where each parameter's range comes from, by name (`physics.SOURCES["hybrid_on"]`), beside the tables; a test fails if a parameter has none.
- **`est.comparisons`**: the campus against what is already there, with what each comparison measures. First, the water system: water on an average day and on a peak day as homes (300 gallons a day, EPA WaterSense), as a percent of the connections of the largest system mapped in the place, the calculation waterledger.org makes on its water cards. `comparisons.HOUSEHOLD_GPD` is the one place for the 300.
- **The packages no longer round results.** `est.water` middle values were rounded to two significant figures for display (a Gaines hybrid peak day read 1.6 MGD; the model's value is 1.576). They are now full values, and returned is still withdrawn less consumed on the middle estimate. Distances to sewer plants and water systems, county water use and utility average load in `place.context()` are also full values. Displays round what they show. Place coordinates stay at 4 decimals.

## 3.5.0 (Oct 31, 2026)

Model version 1.4 stays; no estimate changes.

- **`waterledger build-state MI`** downloads Michigan's sources (`states/mi/fetch.py`) before it builds, skipping what is cached, so Michigan builds from an empty cache on GitHub like any other state, and its snapshot no longer waits for a site deploy. `waterledger build mi` stays, and builds from a cache.
- **EGLE's water-use file** ships in the package (`states/mi/inputs/`) with facility names removed; `python -m waterledger.states.mi.egle` reduces each year's download. `egle_use_file()` now returns this CSV, not the xlsx.
- **A place's main watershed** no longer depends on the order the service returns (`places._watersheds`).

## 3.4.0 (Oct 30, 2026)

Model version 1.4.

- **Electricity from hourly weather:** `physics.hourly_heat_power`, after Lei and Masanet (2022): the facility's power each hour, by design and weather, including how much of the campus is liquid-cooled. New outputs: `pue_avg`, `power_mw_avg`, `pue_peak_1in10` and `power_mw_peak_1in10` in `cooling.run_location` and `ensemble.run_ensemble`, `data_center__electric_power` in the BMI component, and `Estimate.electricity`.
- **Water from the same heat:** evaporation follows the heat rejected, which replaces the heat factor. `hf_econ`, `hf_chiller`, `wb_econ` and `wb_chiller` are gone from `physics.RANGES`, and new ones are in `physics.POWER`.
- **Rounding:** `scenario` middle values use one rule: withdrawn to two significant figures, consumed to the same place, returned the difference.
- `scenario.electricity` and `scenario.pue_by_design`; `states.mi.build.PUE_DESIGN` is gone.

## 3.3.0 (Oct 30, 2026)

- **`waterledger build-state MI`** runs Michigan's own build, not the national tier, so every state builds with the same command. `waterledger build mi` stays, and still builds one part at a time. No change to any number.
- **README** states model version 1.3 and snapshot format 2, and describes the assist design as dry coolers with adiabatic pre-cooling. It is now updated before every release, and a test checks the versions it states.
- **Releases:** every tag gets a GitHub release, its notes from this file.

## 3.2.1 (Oct 30, 2026)

- **State builds on a machine with no cache**: `power.utility_rtos` downloads EIA-861 when none is cached, as `utility_loads` does; in 3.2.0 `waterledger build-state` stopped at the energy stage with `FileNotFoundError`. No change to any number.

## 3.2.0 (Oct 30, 2026)

Model version 1.3: parameters checked against primary sources for publication (`docs/methods/methods-log.md`, Oct 30,
2026), and county water use. Snapshots move to format 2.

- **Utilization** (average IT draw / IT capacity) 0.60-0.90 to 0.50-0.80, cited to EPRI 2026 and IEA 2025 (LBNL 2024
  and its 2025 update for the method). Cooling-tower and hybrid water, electricity and power-plant water fall about 13%
  at the median.
- **Staff water**: gallons per person per calendar day 15-30 (no source) to 10-30 (EPA 2002 Table 3-4; Michigan septic
  design criteria; Gilroy); people per MW now cited to announced campuses; consumed share cited to USGS SIR 2007-5197
  Table 9. About 9% less staff water at 300 MW.
- **Power plants (Michigan build)**: consumption range 0.68-1.31 to 0.6-1.2 L/kWh and withdrawal range 50-61 L/kWh,
  both checked against EIA-923 2024 plant data and EGLE; the 57 L/kWh withdrawal re-cited to Michigan sources (it had
  been MISO's value in the Siddik et al. dataset); `power_supply` options gain withdrawal factors (`wd_gal_mwh`,
  `wd_lo`, `wd_hi`, Macknick et al. 2012 Table 3); nuclear weighted by 2024 generation (396 gal/MWh, was 403); wind and
  solar weighted by Michigan's generation (0.2, was 1).
- **Homes (Michigan build)**: 634.9 kWh/month (EIA-861 2025), was 618.2 (EIA Table 5A 2024).
- **Maintenance and other non-cooling water**: a campus base (0-2,000 gal/day) plus 2-20 gal/day per MW, 3-15% used
  up, bracketed by applicant projections; staff runs carry three more columns (runs of four read as no maintenance);
  `cooling.staff_q(runs, mw, part=None)` gives either part.
- **Cooling physics** traced or derived: hf_econ 1.03-1.10, wb_econ 5-12 and wb_chiller 14-22 °C, er_adj -0.10 to
  +0.05, range_f 7-15 °F, drift 0.0005-0.02%, fill 2,000-12,000 gal/MW, assist_on 27-32 °C, hybrid_on 21-28 °C. Towers
  about 16% and hybrid about 28% less water than 1.2 at the median.
- **Power-plant water for every state** (`waterledger_data`): `tables/state_power_water_2024.csv` and
  `energy.state_power_water(state)`, from 2024 plant data blended for imports, with ranges
  (`docs/methods/power_water/`); `Context.energy.power_plant_water` (`PowerPlantWater`) in every state; Michigan's mix
  reads the same table (0.94 L/kWh consumed, 58.7 withdrawn). `wind_solar(pv_share)` builds the wind-and-solar option
  from a state's own mix.
- **Fix**: utilities the territory layer lists with no control area get their balancing authority from EIA-861 Utility
  Data (`power.utility_rtos`); 475 Texas places had none (Oncor, CenterPoint, AEP Texas Central, TNMP).
  `fetch_eia861` also unpacks Utility_Data.
- Tests: golden file, lake reference and staff draws regenerated for 1.3; the West Michigan per-100 MW reference is
  refreshed from the published estimates at release.

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
- **Assist design** (`design="assist"`, not on the pages) is now dry coolers with adiabatic pre-cooling, calculated from pad effectiveness,
  wet-bulb depression, coil air rise and fan slowing: `assist_share` is replaced by `assist_eff`, `assist_on` is 20-30 °C, and
  `assist_dt_air` and `assist_bleed` are new (`physics.ADIABATIC`, their own random stream). No drift. It now overlaps hybrid. Other designs'
  draws are unchanged.
- Citations: Lei and Masanet's values cite the preprint they were read from; UPS range corrected to 90-99%; no numbers change.
- `tables/state_power_water_2024.csv`: central values and ranges now combine 2024 plant data (with a fill for non-reporting steam and combined-cycle plants) and 2022 reports and Siddik et al. on the same basis, by a lognormal update (`docs/methods/power_water/reconciliation.md`). Median change +6% consumed, +1% withdrawn; raw Siddik values leave the range.

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
