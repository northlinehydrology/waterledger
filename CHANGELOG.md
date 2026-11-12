# Changelog

Package changes (code). Changes to the numbers are listed by model version on the Water Ledger methods page.

## Unreleased

- **Which sewer plant a place reaches** (`waterledger_data.wastewater.rank`, `named_for`, `system_town`, `main_system`; `nearest` and
  `waters.nearest_plants` take `township` and the place's water system, and `scenario._plants_near` uses the same order). Of a place's own
  plants (its name in the mailing city, within 10 km), the one named for the place comes first: Grand Rapids' own plant, not Sand Lake's
  lagoons, which mail from Grand Rapids; Lansing's, not Delta Township's. Of two named for it, a township's plant for a township. Then, new,
  the plant named for the town whose water system serves half the place or more (EPA service areas): Cascade Township, on Grand Rapids'
  water, reaches the Grand Rapids plant before Lowell's, which is nearer and full. Then the rest, nearest first, as before. 144 of 19,090
  places in the ten states change their first plant (Michigan 7). `SewerPlant.system` marks a plant chosen by its water system.
  `docs/methods/methods-log.md`, Nov 12.
- **Plant names** (`waters.plant_name`): WTW, WTP, WPCF, WPCP, WRF, WRP, WSA, SA (a sewer authority), CS, PFAS and the other plant
  abbreviations stay in capitals: "Cadillac Twp WTW", was "Cadillac Twp Wtw".

## 3.20.0 (Nov 12, 2026; model 1.15)

All three packages 3.20.0. Georgia and Illinois join the published states (snapshots dated 2026-11-12, model 1.11's numbers;
`docs/methods/era5-checks/`, the two-page briefs and known-place tests). No estimate changes.

- **Caches named for what made them**: Census places files by the query that fetched them (`census._features`), and the water
  system, watershed and utility joins by their place list (`census.places_key`, a hash of the sorted GEOIDs), so a file cached before a
  query or a state's place list changed is not read for the new one. A Census places file cached before 3.16.0 had no consolidated city
  balances, and joins built from it lacked those places. Older cache files are ignored, and each state's joins are worked out again on its
  next build.

## 3.19.0 (Nov 11, 2026; model 1.15)

All three packages 3.19.0.

- **Wind against the 2024 fleet, model 1.15** (design 0014, check 5; `docs/methods/power_supply/wind_check.py`): 1,069 onshore plants
  delivered 34.1% and the chain matches at a speed factor of 0.99, so `wind.RANGES["resource"]` is (0.93, 1.05), was (0.95, 1.10). A cell
  averaging under `wind.LOW_WIND_MS` (5.5 m/s at 100 m), where ridge and pass plants run far above the chain, is flagged: `est.supply`'s
  wind scenarios there carry a note in the new `SupplyScenarioEstimate.notes`, and `weather` gives the cell's mean speed.
- **Sewer plants a town's sewer can be** (`waterledger_data.wastewater.public_sewer`, `INSTITUTION`): ECHO's added plants leave out
  state, federal and school district facilities and anything not coded sewerage (drinking water plants), and both sources leave out
  plants named as prisons, U.S. Army posts, naval and Air Force bases, the National Guard, state parks and state hospitals. ECHO's POTW
  flag isn't used: Pennsylvania's municipal authorities are flagged NON-POTW. Pennsylvania 869 to 861 plants.

## 3.18.0 (Nov 11, 2026; model 1.14)

All three packages 3.18.0. Pennsylvania and Minnesota join the published states.

- **Power supply scenarios at a place** ([design 0014](docs/design/0014-power-supply-scenarios.md), step 6): `site.estimate(supply={name:
  Scenario})` adds `est.supply`, a `SupplyScenarioEstimate` per scenario at the site's size: shares of the year's MWh, annual matching,
  unserved hours and MWh, surplus, local water (the gas plant's and panel washing), the gas plant's water by role, the residual's
  `GridWater` at the place's balancing authority, PV and wind capacity factors, and the renewables' land, runoff and construction. It runs
  at the place's ERA5 cell with the snapshots' station correction (`waterledger.supply`), for data centers; other types follow with design
  0010's facility contract.
- **Model 1.14** (methods log, Nov 11): gas plants and supply scenarios only; no data center or place number changes, and it reads model
  1.11's snapshots (`MODELS["1.14"]`).
  - **PV against the 2024 fleet** (design 0014, check 5; `docs/methods/power_supply/pv_check.py`): over 944 tracking plants EIA reports 24.1%
    and the chain on ERA5 gives 28.5%, so `pv.RANGES["resource"]` is (0.76, 0.92), was (0.95, 1.05). It stands for delivered output over
    modeled: ERA5's bias with snow, curtailment, outages and age.
  - **Gas plant outages last days**: `gas.physics.outages` runs each unit up and out with geometric run lengths averaging `OUTAGE_HOURS`
    (48 [A]) at the sampled availability, not a fresh draw each hour; `mean_outage_hours` overrides it. `est.supply` adds
    `unserved_run_max_hours`, the longest run of hours short.
- **Places no utility territory covers** take the nearest served place's utilities within 50 km [A]: `Energy.nearest_place`,
  `nearest_place_km` and `nearest_utilities`, used for the place's grid region by the estimate, `est.supply` and the cell runs
  (`national.era5.cell_bas`). Seven places had none (six in Virginia, Michigan's St. James township).
- **WAPA's grid region by state** (`waterledger_data.energy.WAPA_BY_STATE`): the territory layer labels the Western Area Power
  Administration WALC wherever it draws it; in Minnesota, Iowa, the Dakotas and Nebraska it is SWPP. No estimate used it.
- **Sewer plants from ECHO where the survey is thin** (`waterledger_data.wastewater.echo_only`): ECHO's sewer plant permits that no CWNS
  record covers join the survey's, with ECHO's design flow. Pennsylvania's 2022 survey lists 195 facilities; it now has 869 plants. Every
  state gains some from its next snapshot.

## 3.17.0 (Nov 10, 2026; model 1.13)

waterledger-models and waterledger-data 3.17.0; waterledger is unchanged at 3.16.0.


- **The shared Monte Carlo runner** ([design 0010](docs/design/0010-water-user-types.md), step 2a). `waterledger_models.runs.run_location(model,
  times, temps, rhs, designs=None, grid=None, extra=None)` runs any water user type: it owns the draws loop, the standard loads (the run's, the
  peak day's, full capacity), the daily statistics, water at the power plants, the result names and the p10 / p50 / p90 / central summary. A type
  gives a small model (its designs, its draws, each draw's `runs.Hours`). `cooling.run_location` and `battery.plant.run_location` keep their
  signatures and results and now run through it. `extra(design, p, hours)` is called with every draw's hours, so a caller can work out more from
  each draw's hourly electricity; its results are summarized with the rest.
  - **Numbers.** The runner works every power figure from the hourly MW, one formula for every type, so `power_mw_avg` and `power_mw_peak_1in10`
    (and a cell plant's `power_mw_peak_day_1in10`) differ from the types' own loops in the last bit: at most 4.9e-16 relative. Every other value
    is identical to the bit, held by records of both types' Monte Carlos from before the move (Andrew agreed the last bit).
- **Power supply scenarios, model 1.13** ([design 0014](docs/design/0014-power-supply-scenarios.md); methods log, Nov 10). What
  serves a water user's hourly electricity, and the water that takes; every plant hypothetical. Model 1.13 changes no data
  center or place number and reads model 1.11's snapshots (`MODELS["1.13"]`).
  - **`waterledger_models.gas`**, new gas plants as a water user type: `physics.hourly` (combined cycle on `towers`, `hybrid`,
    `assist`, `dry` or `lake`; simple-cycle turbines with dry low-NOx or water injection and inlet cooling; engines; fuel
    cells; units dispatched hour by hour with derate, heat rate, part load and outages; energy and water close every hour),
    `plant.run_location` on the shared runner, `bmi.GasPlantBmi` (bmi-tester in CI). Wastewater by `discharge` (`sewer`,
    `source`, `stream`, `none`) with `default_discharge` by technology, design and water supply.
  - **`waterledger_models.supply`**: `pv` (the PVWatts chain in numpy, held to pvlib hour by hour in the tests), `wind` (the
    IEA 3.4 MW reference turbine's curve from NREL's turbine-models), `scenario` (`Scenario`, `Gas`, `size`, `Supply`, the
    runner's `extra`), `land` (solar and wind projects' land, runoff and construction water and sediment).
  - **`runs`**: `extra.setup` once per place, the draw's index, and `runs.Supplied`, whose hourly water and grid-served MW get
    the runner's own statistics and `grid.RunWater`.
  - **`waterledger_data.era5`**: `fetch_supply` and `supply` for global and direct radiation and the 100 m wind, into a raw
    cache of their own (`RAW_SUPPLY`), so `raw_path`'s temperature files are untouched.
  - **The `to_stream` return role** for every type: a permitted discharge to surface water other than the source. Gas plants
    and battery plants (`discharge="stream"`) report it; `returned = to_sewer + to_source + to_stream`. Battery results gain
    the `to_stream` statistics, zero by default.
  - `runoff.storm_mg` takes `cn_pervious` (default unchanged).
  - pvlib is a test-only dependency (the dev group); no package depends on it.
  - The place-based supply estimate (`est.supply`) comes with design 0010's facility contract.

## 3.16.0 (Nov 10, 2026; model 1.12)

- **Indiana** is the sixth state published as a checked snapshot (data.waterledger.org/IN/2026-11-10, model 1.11;
  1,661 places, 183 ERA5 cells), with its ERA5 check (`docs/methods/era5-checks/in.md`), its section in the national-tier
  notes and its two-page brief (`docs/methods/in.pdf`). Two fixes it needed:
  - **A consolidated city's balance is a place** (`waterledger_data.census`): Census FUNCSTAT F, such as "Indianapolis city
    (balance)", the land the consolidated government governs outside the cities that keep their own. FUNCSTAT A alone left
    it out. Its base name and kind come from the name. None of the five states published before has one; Louisville,
    Nashville, Augusta, Athens, Butte and Milford will.
  - **A new state's first ERA5 runs get the grid's water** (`national.era5.cell_bas`): before its first snapshot, the
    balancing authorities come from the state's local build through the call the snapshot makes, instead of every cell
    running with none.

- **Battery cell plants** ([design 0009](docs/design/0009-battery-cell-plants.md); methods log, Nov 10), the second water
  user. `waterledger_models.battery`: `physics.hourly`, the plant's heat, electricity, fuel and water hour by hour per
  GWh/yr of cells, for the `dry`, `assist`, `hybrid`, `towers` and `lake` designs; `plant.run_location`, the Monte Carlo at one
  location (full output by default, or `utilization="sampled"`; `settings=` fixes a plant's own values); `bmi.BatteryCellBmi`,
  BMI 2.0 on `ScalarPointBmi`, checked by the CSDMS bmi-tester in CI. Energy and mass close every hour, held by tests.
  - **Returns by destination**: `to_sewer` (tower blowdown, process returns, staff water) and `to_source` (the lake design's
    once-through water less its forced evaporation); `returned` is their sum.
  - **Chemistry**: `chemistry="nmc"` (NMC and NCA, the default) or `"lfp"`, which samples `lfp_factor` 1.2-1.7 [A] on the
    plant energy per kWh (Degen et al. 2023).
  - **As data centers have it** ([design 0010](docs/design/0010-water-user-types.md)'s standard treatment): water at the
    power plants through `grid=` (`grid_<BA>_<kind>_avg` and `_peak_1in10`); `withdrawn_peak_full_capacity` and
    `power_mw_peak_1in10`, the 1-in-10-year highest hour, at full output, so a sampled-utilization run is also worked at
    full output; and the `assist` design, the data centers' adiabatic pads on the plant's dry coolers.
  - **Not yet**, on the shared runner in a coming release: the Monte Carlo loop is still the type's own, and
    `BatteryCellBmi` has no withdrawal limit, dry mode or dissolved mass (design 0006), which need the plant's limited
    physics.
  - `examples/battery_cell_plants_ea_check.py` runs the model at the six U.S. plants with a DOE EA water projection;
    `docs/methods/sensitivity/battery/` holds its Sobol' and Morris analysis.
  - The place-based estimate (`wl.place(...)`) comes with design 0010; waterledger.org is unchanged.
- **Shared by every water user**, moved out of `datacenter` unchanged, the old names still importing:
  `heat_rejection` (towers, hybrid and dry coolers, loops, chillers, pumps and fans, psychrometrics, sampling), `once_through`
  (Great Lake once-through cooling, GLERL temperatures) and `daily` (`groups`, `daily_stats`, `summarize`); assist's pads
  (`heat_rejection.pad_depression`, `coil_air`, `pad_water`, and the `assist_eff` and `assist_bleed` ranges in `EQUIPMENT`);
  and water at the power plants, `grid.RunWater`, which the data center and battery runs both call. Cycles of
  concentration and the hybrid's switch margin are each user's own (`heat_rejection.OPERATING`); data centers keep 3-6.
  Every data center result is identical to the last bit, held by a record of the Monte Carlo from before the moves
  (`tests/data/datacenter_before_runner.json`: every plant and design, compiled and NumPy, with hourly grid water).
- **One model version for every type** (Andrew, Nov 10; design 0010, decision 6). `waterledger_models.MODELS` records,
  from 1.12, the types each version changes and the model of the snapshots it reads, and `snapshot_model()` gives it.
  Model 1.12 changes battery plants only and reads model 1.11's snapshots and cell runs: `national.data.snapshot_for_model`
  and `waterledger latest-json` key on `snapshot_model()`, so a 3.16.0 package reads the 2026-11-09 and 2026-11-10
  snapshots without the other-model note, and a data center estimate names model 1.11. Live builds, Michigan's site data
  and the station runs' cache are labeled with `snapshot_model()` too, so a snapshot rebuilt under 3.16.0 is filed under
  1.11, where 3.16.0 reads. Code that compared a snapshot's `model_version` with `MODEL_VERSION` should compare it with
  `snapshot_model()`.

## 3.15.0 (Nov 9, 2026; model 1.11)

- **The grid's water hour by hour** ([design 0008](docs/design/0008-power-at-the-grid.md), part 1; methods log, Nov 9).
  `Estimate.grid_water` (`GridWater`) is the water at the power plants of the place's balancing authority for the campus's
  own hourly electricity. It covers the average day and the 1-in-10-year peak day, consumed and withdrawn, for the average
  mix and the marginal mix. It is None for lake-source cooling and for data from before model 1.11. The annual power
  options are unchanged.
  - **Data.** `waterledger_data.grid930`: EIA-930 hourly demand and generation by fuel for every balancing authority,
    2019 on, and its plant water by BA, fuel class and month from the 2024 plant reports behind the state table.
  - **Model.** `waterledger_models.grid`: the table, binned by month, hour and the user's temperature, with
    `GridWaterBmi`.
  - **Cell runs.** `cooling.run_location(..., grid=)` and `run_plants(..., grid=)` add `grid_<BA>_<kind>_avg` and
    `_peak_1in10`. `era5.cell_bas` gives each cell its places' BAs; Michigan's cells take MISO and PJM. The table is fit on
    2019-2024, the years the grid's hours and the cells' weather share; that runs about 10-16% above 2024's plant water per
    MWh. The grid adds about 12% to a run. Every other cooling result matches model 1.10.
  - **Gap.** Seven Virginia places have no utility in the snapshot's energy data and have no hourly grid water.
- **A power plant's withdrawal is at least its consumption** [A], in the state table and the BA table. Three plants report
  water consumed and none withdrawn: Stanton, FL; Kings Mountain, NC; Ingleside Cogeneration, TX. Withdrawn L/kWh: Florida
  46.562 to 46.582, North Carolina 33.057 to 33.077. No other state changes.

## 3.14.0 (Nov 8, 2026; model 1.10)

- **The cooling plant inside the building is a choice** ([design 0007](docs/design/0007-cooling-plants.md); methods log, Nov 8).
  `physics.PLANTS`: `shared`, the default (one facility water loop for the air handlers and the liquid racks, supply air
  24-30 C [A]), `warm` (a separate warm liquid loop at 30-42 C [A], liquid share 0.7-1.0 [A]) and `chilled` (a conventional
  chilled-water plant, 7-13 C water, 18-22 C supply air). Through model 1.9 every plant ran the warm-water best case
  (supply air 27-35 C, liquid racks 32-45 C). `DataCenter(plant=)` through both providers, `weather='local'` and the BMI
  (`plant:`); `cooling.run_location(..., plant=)` and `cooling.run_plants`; `scenario.for_plant`. Each ERA5 cell's run covers
  every plant: `per_100mw` holds the default's results, as before, and `per_100mw_plants` the others'. Results from before
  model 1.10 answer only for their own plant. With the default, hybrid and assist water rises 30-40% on the average day and
  about 20% on the peak day against model 1.9, towers' peak day 6-7%, and peak-day power 5-7 MW per 100 MW of IT.
- **The weather correction maps the dew point** (`quantile_mapping` method `qm-3`), not the dew-point depression, so a
  hot-day temperature correction no longer makes peak days humid (model 1.9's Michigan peak days ran 0.72 C of wet bulb
  high). The lapse rate moves temperature only [A]. Station fits are cached by what they fit (`quantile_mapping.FIT`).
- **ERA5 check W7**: corrected cells' mean error in the 1-in-10-year peak day's mean wet bulb, at most 0.5 C [A]. All five
  states pass every criterion on model 1.10 (`docs/methods/era5-checks/`).
- **The dry coolers' glycol** has propylene glycol's heat capacity and density, 30-40% by volume [A] (Dow's DOWFROST data
  sheet), not water's.
- **The cooling runs are compiled** (`datacenter.kernel`, Numba): about 4.5x faster per draw, with the same numbers (a real
  cell matches all 1,512 values to the bit; the tests hold every hourly series to `physics.py`). `run_location(...,
  compiled=False)` runs `physics.py`. `waterledger-models` now requires `numba` (0.60 or later).
- **Sensitivity analysis by plant** (`--plant`). Its model 1.10 results follow this release.

## 3.13.0 (Nov 7, 2026; model 1.9)

- **Peak-day power on the estimate.** `Estimate.electricity.peak_day_mw`, the 1-in-10-year peak day's average power at the
  peak day's load, from the cell results' `power_mw_peak_day_1in10` (model 1.9); `scenario.electricity` returns it as
  `peak_day_mw`. None for lake-source cooling, whose model doesn't report it, and for older data. No number changes.
- **An ECHO record without its permit status no longer stops a build** (`wastewater`): read as a null status is, not
  terminated, as before. ECHO left the field out once (the Nov 7 nightly). No number changes.
- **Sensitivity analysis** (`docs/methods/sensitivity/sensitivity.py`): the peak day's average power is an output.

## 3.12.1 (Nov 7, 2026; model 1.9)

- **The nightly passes again.** `cells.runs` raises `cells.RunsMissing` (a `FileNotFoundError`, so callers are unchanged) when
  cells have no run here, and the snapshot tests skip on it on machines without the runs (GitHub's), checking format 3 where
  they are. The West Michigan reproduction reference is at model 1.9. No number changes.

## 3.12.0 (Nov 7, 2026; model 1.9)

- **The dry coolers' glycol loop** (methods log, Nov 6). Dry, assist and hybrid plants now carry a plate exchanger's
  approach (`hx_approach`) and a glycol loop pump at the tower loop's range and pressure [A], which towers already had.
  Dry heat rejection now costs more electricity than towers, as it should: in West Michigan at central values, PUE goes
  from 1.122 to 1.145 for dry, against 1.118 for towers. Assist's and hybrid's switch point falls by `hx_approach`, so
  they go wet more often and use more water (assist 0.018 to 0.030 gal per IT kWh). Towers are unchanged to the bit.
- **Peak-day power.** `cooling.run_location` reports `power_mw_peak_day_1in10`: the 1-in-10-year peak day's average
  power at the peak-day load, on the same basis as the peak-day water. In West Michigan at 100 MW (central run) a dry plant
  takes 89.5 MW on that day against towers' 83.1.
- **Station correction on land cells** (methods log, Nov 6; `quantile_mapping` method `qm-2`). Land cells (at least 90%
  land) are corrected toward the land stations within 100 km, at most 4, 1/d^2, with the lapse step, as shore cells are
  toward shore stations. Held out across the five states (146 land stations), ERA5's land bias in the design dry-bulb goes
  from -0.31 to -0.05 C and the median error from 0.45 to 0.37 C. `era5.candidates` finds the land stations, `era5_check`
  judges land cells as corrected, and runs go to `runs/era5/model1.9`.
- **A place's own electric utility first** (`energy.ranked` with the place; `is_own`). A utility named for the place, not a
  cooperative, covering at least half of it with at least 100 EIA customers per km2 of what it covers [A], is listed first:
  Madison Gas & Electric in Madison, the town utilities of Bedford and Culpeper. Before, a larger utility drawn over whole
  counties came first. Columbus, Ohio keeps AEP Ohio first. First utilities change in 12 (Virginia) to 79 (Ohio) places a state;
  Michigan's order comes from its own territory data and is unchanged.
- **Station years time out after 60 s** (ISD-Lite, ECCC), not 300, so a year a station never reported can't hold a build for
  15 minutes.

## 3.11.0 (Nov 6, 2026; model 1.8)

No estimate, parameter or snapshot changes: with no limit set, every output is 3.10.0's to the bit.
- **Water limits on the cooling model** ([design 0006](docs/design/0006-water-limits-and-return-loads.md)). `physics.hourly_limited`
  meets a cap on the cooling water hour by hour while the heat still goes. A hybrid's wet mode or assist's pads give up
  evaporative duty to the dry coolers and chillers, at more electricity. A towers plant, with no dry side, sheds the load it
  can't cool. Heat beyond the dry side's capacity is reported as heat not removed. New parameters, not sampled:
  `dry_capacity_margin` (0-20%) and `dry_derate_per_k` (1-2% per K) [A] (`physics.LIMITS`, `central_limits`).
- **Return water.** `physics.dissolved_mass_split` says where the dissolved mass in the water taken for cooling goes (blowdown,
  drift, leaks and scale), and `blowdown_temperature` gives the basin's or sump's temperature.
- **`CoolingWaterBmi`: new inputs.**
  - `water_user_water__withdrawal_volume_flux_limit` (m3 s-1, default infinity).
  - `water_user__dry_mode_flag`.
  - `water_user_intake_water_<name>__mass_concentration` for dissolved_solids, chloride and phosphorus (kg m-3).
- **`CoolingWaterBmi`: new outputs.**
  - `data_center__unremoved_heat_power` (MW) and `data_center__setpoint_lost_time` (h).
  - `water_user_return_water__temperature` (degC).
  - `water_user_return_water_<name>__mass_flux` and `water_user_unreturned_water_<name>__mass_flux` (kg s-1), which add to the intake's mass.
  - The water-user names as aliases: `water_user_water__withdrawal_volume_flux`, `__gain_` (condensate), `__consumption_`,
    `__return_` and `water_user__electric_power`.
- **`physics.hourly_rates`** now sums `_rate_parts`, the flows one by one; its results are unchanged.
- **`waterledger publish ST --dir SNAP`.** Uploads a snapshot written and checked on this machine to data.waterledger.org: the files, then the manifest, then `latest.json`. It stops before sending anything when the manifest has no checks or the date is already published. Model 1.8's snapshots are published this way, since the `build-state` workflow has no cell runs. `r2.from_env(bucket=...)` names the bucket, and `Store.publish` uploads with a content type and no checksum sidecar.
- **One list of states.** `states.toml` holds the states built, with each one's example place and ATTAINS agency. The tests' state markers and the methods briefs read it.

## 3.10.0 (Nov 5, 2026; model 1.8)

Model 1.8 changes the cooling weather and nothing else in the model.
- **Each place's own ERA5 cell.** Every place in every state, Michigan included, takes its cooling weather from its ERA5 grid cell, 1995-2024 ([design 0004](docs/design/0004-era5-weather.md)). The nearest cell that is at least half land is used where the nearest is mostly water.
- **Shore correction.** Cells under 90% land are corrected toward NOAA and ECCC stations near the shore ([design 0005](docs/design/0005-era5-quantile-mapping.md)).
- **Snapshots.** They carry each cell's results as format 3.
- **The same equations.** The cooling equations and parameters are model 1.7's; the golden numbers are unchanged, with only the version label moving to 1.8.

Also seven changes from coupling the BMI components in NOAA's NextGen (the Water Ledger NextGen Michigan example). The station check is in [docs/methods/era5-station-check.md](docs/methods/era5-station-check.md).

- **Texas water use downloads again** (the nightly failure since Nov 4). TWDB's server stopped sending the intermediate certificate that signed its own, so Python couldn't verify it. `wateruse.twdb_tls` adds that public intermediate (shipped in `tables/`) to certifi's roots, still verifying in full; certifi is now a declared dependency.
- **Beta, said plainly.** The README's new Stability section says the packages are beta despite the 3.x number. From here, a breaking change to the public API waits for 4.0. The classifiers say `Development Status :: 4 - Beta`.
- **`MODEL_VERSION` 1.8 and package version 3.10.0.** A 3.10 package reads the newest snapshot filed under model 1.8. Until those are published it reads the newest 1.7 snapshot and says so; 3.9 packages keep reading 1.7.
- **Shore stations near the water kept** (Nov 5, found at Galveston).
  - `climate.isd_sites` gives a spanning station a linked fallback, used only if it fails the 85% rule.
  - Pieces link within 8 km (was 5), and a year no piece lists is read from every piece.
  - A station is judged a shore station by its own nearest cell (`shore_land`), not the land rule's.
  - Stations that qualified before keep their records. 11 more shore stations qualify, and 8 more cells are corrected.
- **Michigan on ERA5 cells.**
  - `waterledger build mi` gives each place its cell (`e`) and writes the site's `data/cells/`, in place of the eight regions' Open-Meteo runs. The regions stay for salt, golf and the map, and the validation checks use each site's own cell.
  - The package's Michigan estimate takes the place's cell. Site data from before 1.8, with no `e`, still reads by region.
  - Michigan's snapshot is format 3.

- **BMI: outputs change on `update()`, not on `set_value`** (behavior change). `CoolingWaterBmi` and `LakeCoolingBmi` store inputs when they are set, and `update()` computes the step from the current time to the next from them, then moves the clock on. Outputs always describe the last step taken and read 0 before the first one, so a framework that sets the next step's inputs before reading this step's outputs gets this step's values. Code that set inputs and read outputs without calling `update()` must now call it in between (NextGen's order, set, update, read, is unchanged). With a forcing file, the outputs read at time t are for the hour from t - 1 h to t; they were for the hour from t. An input set with `set_value` wins over a forcing file for the step it was set for; the file's value returns the next step. With the same inputs, each hour's outputs are identical to 3.9.0's (checked against the 3.9.0 component over 1,440 hours in every design, and in `tests/test_bmi.py`). A hybrid campus without a design dry-bulb now stops at `initialize()`, and `initialize()` starts a component over, its inputs included.
- **BMI: specific humidity and surface pressure.** `CoolingWaterBmi` with `humidity: specific` takes `atmosphere_bottom_air_water_vapor__mass_fraction` (kg kg-1) and `land_surface_air__pressure` (Pa), what NextGen's AORC and NWM forcing carry, and converts them inside (Bolton 1980). `waterledger_models.weather` has `relative_humidity`, `specific_humidity` and `saturation_vapor_pressure`; the round trip is tested and stays within 0-100%.
- **BMI: settings without a file.** `initialize()` takes a dict as well as a YAML path, in both components (`bmi.read_config`).
- **BMI: the components import without pyyaml** (a bug in 3.9.0, found by Basin Ledger). `datacenter.bmi` imported yaml as it loaded, though pyyaml is only in the `[bmi]` extra, so with bmipy alone the components wouldn't import. yaml is now imported only to read a YAML file; a dict configuration needs none, and a file without pyyaml says to install `waterledger-models[bmi]`.
- **BMI: a public base.** `ScalarPointBmi` is the shared base for components at one point, with its contract in the docstring. `_ScalarPointBmi` stays as an alias.
- **BMI: the design dry-bulb.** `waterledger_models.weather.design_dry_bulb` gives a hybrid's 0.4% design dry-bulb from any hourly record (Dataset, DataArray or array), the value a forcing file gives the component, for frameworks that supply the weather. Use a long record: one Michigan year is up to 4.6 C off its 30 years.
- **`hydrology.stream_depletion` takes arrays** (numpy, with `hydrology.erfc` within 1e-13 of `math.erfc`) and gives the scalar form's values; at t = 0 the share is 0. Ten years of hourly well responses are one 6 ms call.
- **The BMI example runs again.** `examples/bmi_coupling.py` gives its hybrid a design dry-bulb (it failed under 3.9.0), and every example now runs in the tests (`tests/test_examples.py`; on synthetic weather offline, downloading under `-m live`).
- **Snapshot format 3** (design 0004, section 5): cooling by ERA5 cell in the state snapshots, national tier.
  - `waterledger snapshot ST` writes `cells/<cell>.json` from the cells' runs, plus `cells/index.json`, each place's cell fields and `weather_corrected`. The manifest gains `cells`, `cell_rule`, `weather` and `correction`, with ERA5's attribution, ISD's citation, and ECCC's licence and attribution where a Canadian station is used. `climate.json`'s divisions keep only their stations.
  - The package reads a place's cell from a format 3 snapshot, fetching the cell's file when needed, and its division from format 2. `Climate` gains `cell`, `cell_km`, `cell_land`, `cell_moved` and `weather_corrected`.
  - `check-snapshot` adds three checks: a cell with results for every place, each cell's central run closing, and each corrected cell's stations in the manifest.
  - `latest-json --dir` files a snapshot under its manifest's model, so model 1.7 packages keep reading format 2. Michigan's snapshot is not yet on cells.
- **`waterledger era5 check ST`**: design 0005's leave-one-station-out check for any state, with a pass or fail against the four states' worst plus a margin (`era5_check.CRITERIA`). It writes `check.json` and `check.md` and exits 1 on a fail. `era5 cells ST --json` says when every cell is done, and a state not yet published takes its local build's places. `docs/add-a-state.md` gives the steps from preflight to publishing.
- **Cooling runs worked 4,096 hours at a time** (`cooling.HOUR_BLOCK`): the same numbers to the bit, and no longer waiting on memory. A cell takes 31 s at ten workers in short tests (74 s at six before) and about 40 s over a long run. `waterledger era5` defaults to the performance cores. Ctrl-C stops a part cleanly, and a restart uploads finished results R2 doesn't have.
- **Model 1.8's ERA5 runs** (design 0004; the four states run from Nov 4, 2026): `waterledger era5 cells|fetch|run ST --part k/n --workers 10`.
  - `waterledger_data.era5`: `cell` is the land rule on ERA5's land-sea mask, shipped for the lower 48. `fetch` reads Open-Meteo's open copy into a raw cache with each cell's request and checksum (`waterledger-data[era5]`). `hourly` gives local standard time.
  - `waterledger.national.era5`: the state's cells and parts, the shore stations for quantile mapping, and the runs, one result file per cell as it finishes.
  - `waterledger_data.r2`: optional saving to the private R2 bucket `waterledger-raw`, through wrangler (`WATERLEDGER_R2=wrangler`) or R2's S3 API with credentials from the environment. Each file is skipped when R2 has it with the same checksum. Before a part starts, what R2 has is pulled, so it can resume on another machine. A failed upload warns and never stops the run. Off unless set up.
- **Quantile mapping** (`waterledger_models.quantile_mapping`, for model 1.8). It corrects an ERA5 cell's hourly temperature and dew-point depression toward the shore stations within 100 km, month by month and by 3-hour block, at the cell's elevation, for cells under 90% land. The dew point never passes the temperature, and each hour keeps its rank. `correct()` returns the corrected series and what it did (`applied`, `reason`, `stations`).
- **Stations across a change of ID.** `climate.isd_sites` links ISD pieces that share a USAF or WBAN within 5 km. `climate.eccc_sites` and `eccc_hourly` read Environment and Climate Change Canada's hourly records (MSC GeoMet, ECCC Data Servers End-use Licence 2.1; `climate.ECCC_ATTRIBUTION`), linked by place and name. Both go through `climate.screened_hourly`, the 85% rule and screens `isd_hourly` applies. `isd_stations` and `isd_hourly` are unchanged.
- **`__version__` matches each package.** 3.9.0 shipped with `__version__` 3.8.1, so every model 1.7 snapshot's manifest records packages 3.8.1 (2026-11-02 in Michigan, Virginia and Texas; 2026-11-02.2 in all four). The dated snapshots stay as they are; a test now holds `__version__` to `pyproject.toml`.

## 3.9.0 (Nov 2, 2026)

Model version 1.7: parity and defensibility for Michigan, Ohio, Virginia and Texas, with no Michigan leftovers in the shared method. Water taken on towers moves about 4% on average and 13% on the peak day. Hybrid moves most, down as much as 40% in hot places. Pollution loads change most of all. Every moved number is on the Water Ledger changelog and in the methods log.

- **`est.before_after` no longer has sediment, phosphorus or nitrogen.** They are in `est.site_loads` (`comparisons.site_loads`), because they cover the change in runoff from the finished site, not the whole project. It also carries phosphorus in construction sediment and in cooling wastewater. A site study can move all of it a lot.
- **`runoff.loads`** drops `roof_share`, and `PARAMS["emc"]` holds one whole-site concentration by pollutant.
- **Phosphorus and nitrogen by land cover.** Developed land and the campus: Simple Method runoff x one whole-site concentration (NSQD 4.02), plus the natural yield on the pervious share [A]. Farmland: USDA CEAP II's loss per acre by production region, surface and below ground, checked against MANAGE (`runoff.nutrient_yield`; `tn_lb["now_surface"]`). Natural land: measured basin yields (Clark et al. 2000).
- **Controls.** Wet ponds from CWP 2007's quartiles, down to an effluent floor, on the surface part only. Infiltration no longer counts total removal on top of volume loss, and the nitrogen it soaks in is reported as gone to groundwater (`to_ground`).
- **The cooling model.** Peak day at average load over a load factor (0.88-0.94), full capacity as its own upper case (`withdrawn_peak_full_capacity`). Cycles 3-6, tower range 7.2-10.8 F, drift from 0.005%. Hybrid fully evaporative at each location's own 0.4% design dry-bulb. Switch points tied to loop temperature. 400 Latin hypercube draws at each location, with linked parameters grouped. `max_90day` kept as a statistic.
- **One rule in every state:** road salt from a station's cold wet days x 0.6; a home's water from USGS 2015 over ACS 2015 households; which sewer plants count and how far they are; the nearest water system; a second system on a quarter of a place; land defaults on `Place.incorporated`; coal, nuclear and fresh and saline water at power plants; Great Lakes features and lake-source cooling in every lake state; weather times from longitude.
- **Levels outside reviewed rules:** no invented lines. The calculator is a what-if: the number stands, and `not_covered` says what isn't reviewed. Michigan's Part 327 is tested on the highest month and the Compact on the highest 90 days.
- **Station records:** a year counts with 85% of its hours, and bad readings are screened unless a nearby station backs them up.
- **Sediment on a yield basis.** Farmland by state from NRI 2022 and woods from EPA, x a delivery ratio [A]; construction from EPA's gross range x delivery, with and without basins.
- **Downloads (`waterledger_data.fetching.save`)** wait out a service that is down and are never left half written. `build-state` keeps its raw downloads across code changes and failed builds; changing sources refresh after a month, and records that don't change stay. ECHO and NOAA's county rainfall ride out long busy spells, and a failed manifest fetch no longer empties the cached copy.
- **Snapshot files** are written with sorted keys, so a file's checksum changes only when its data does.

## 3.8.1 (Nov 1, 2026)

Model version 1.6, from an independent review of model 1.5. Water taken moves by under 1%. Towers use about 1.5% less electricity on average. The wastewater shown moves by up to about 17% and the water evaporated by up to about 7%, because the middle estimate is now worked out differently. `docs/methods/methods-log.md` has the measured differences.

- **The middle estimate keeps wastewater at the model's median, and evaporated is what's left.** Withdrawn and returned are at their medians and consumed is withdrawn + condensate - returned, so the books close. Wastewater was the remainder, which ran 13 to 23% above its own median in the evaporating designs.
- **A tower's fans slow to the air the hour's heat needs**, by the fan laws with a 10% floor, as the dry cooler fans do. They ran at design air flow in every hour with evaporation.
- **Power losses and lighting are heat in the room's air.** Part of them was on the liquid loop.
- **A lake-source campus's peak-day homes count what the lake loses**, like its average day. They counted the water passing through.
- **A septic estimate leaves out condensate.** It is clean water and is assumed to go to a site drain or stormwater [A]. `to_sewer` and the septic rule take the flow without it; it stays in the returned water, so the books close.
- **The water system a place is compared with** is one covering at least half of the place (the largest share if more than one); otherwise the largest by population among those covering at least 5%; otherwise the largest by population [A] (`comparisons.main_system`). It was the largest by population, even at 0.8% overlap: Westerville, Ohio was set against Columbus, not its own system.
- **A very small water system gets no percent.** Where the main system has under 100 connections and covers under half of the place, `comparisons.tiny_system` says so and the comparison's `percent` is None, with the reason in `basis`: 75 places (13 Michigan, 40 Ohio, 6 Virginia, 16 Texas), such as a mobile home park inside a township. A small town's own system keeps its percent. `Comparison.percent` can now be None.
- **Reuse peak day.** Water taken with full reuse could go below zero on the peak day where condensate exceeds it (300 MW, closed loop, in Michigan), with its range inverted. It now stops at zero and the range stays in order.
- **`est.model_version` in Ohio, Virginia and Texas** reports the model of the data read, not the package's, as in Michigan. A package with no snapshot for its own model reads the newest there is and prints a note.
- **`cooling.run_locations` runs one place at a time by default.** `waterledger build-state` and `build` turn on every core; results are the same. A script with no `__main__` guard no longer breaks on macOS.
- **Publishing.** The upload step treats only a real not-found as absent, and reads the old pointer before writing anything.
- **Downloads are whole or they fail.** A map service's error body, or an answer cut off by its record limit, now stops the build (`places.checked`); every paged download goes on past a limit smaller than its page. Michigan's sewer plant download reads every page, and ECHO giving fewer plants than it counted is an error. Before this a Michigan trial lost household wells in 50 counties with no failure. Michigan's snapshot check also fails if household wells look short. Service limits and ECHO's Michigan count (479 plants) were checked: no published data was cut off by the paging.
- **A utility peak below its average load counts as missing**, in every state (`waterledger_data.power.usable_peak`). EIA's file has Duke Energy Ohio at a 914 MW summer peak against 2,252 MW on average.
- **`est.water.withdrawn_peak_full_capacity`**: the peak day with every computer at capacity all day, as an upper case. The main peak day stays at the run's average utilization.
- **A reach's `assessed`** on `ctx.receiving.downstream` says whether the state assessed that watershed, in every state, so no listing and not assessed can be told apart.
- **Published snapshots never change.** A second build on one day is `YYYY-MM-DD.2`, and the upload refuses a name in use. `latest.json` has `by_model`, and a package reads the newest snapshot for its own model, so a new model's numbers don't reach an older package. Packages before 3.8.1 stay on model 1.5's snapshots.
- **Michigan's snapshot job runs the statewide checks** and records them in its manifest, like the other states.
- **BMI: a condensate output**, `data_center_cooling_water__condensate_volume_flux`, and the descriptions of withdrawal, consumption and return now say what those hold.
- **Tests with values worked by hand**, including a lake case, catch a wrong constant that the balance tests can't; the water balance test now runs on weather that condenses.
- **Faster builds.** Each draw's heat balance runs once for its water and PUE, a state's places run at once, one process each, and `build-state` keeps NOAA's records for the month. The numbers don't change (Virginia, byte for byte in every data file but one, whose only difference is key order).

## 3.8.0 (Nov 1, 2026)

Model version 1.5: the cooling model's energy and mass now close, hour by hour, in every design. Tests in `tests/test_balances.py` hold them to it. Water and electricity estimates change by a few percent; `docs/methods/methods-log.md` has the measured differences.

- **Every kW is accounted for.** Facility power + the heat outside air brings = heat through the water or coil + the heat rejection fans. Pump heat now counts.
- **Outside air joins the balance** (`physics.OUTSIDE`, `hourly_outside_air_heat`, `hourly_water_with_air`), in place of Lei and Masanet's sensible heat ratio: its heat and moisture each hour, a coil's condensate above the indoor dew point limit, and humidifiers below it. **Withdrawn + condensate = consumed + returned**, with `est.water.condensate`. `hourly_rates` and `hourly_heat_power` take the hour's relative humidity as `rh`.
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
