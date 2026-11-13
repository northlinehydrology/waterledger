# 0010: Water user types: one contract for every large water user

Status: **proposed, Nov 9, 2026. Decisions 1, 2, 3, 4, 7 and 8 agreed (Andrew, Nov 9); 6 decided Nov 10 (one model
version, with `MODELS`, built in 3.16.0); 5 explained further, for review. Steps 1 and 3-6 built Nov 12 on branch `battery-facility`, ahead of
0011, with decision 5's provider split left for 0011 (below).** Battery cell plants (0009) are the first type added under the contract rather
than beside it. Cathode materials plants move to 0012.

**Nov 12, 2026: the battery facility before 0011.** 0011 (Michigan on the base path) has no code yet and is a large refactor. Andrew chose
(Nov 12, on the question whether to build the battery facility now and leave the provider split for 0011): "Battery now". So the contract is
built with the providers as they are: `DataCenter.results` asks the place's provider, as `Site.estimate` did, and a cell plant computes at
the place with the place-side rules every state shares (`national.provider.default_source` and `default_wastewater`, taken out of the
national estimate unchanged). Decision 5's split, providers to the place side only, comes with 0011, when Michigan reads through the
national provider; nothing downstream changes then.

## Why

The packages are the product, and the point of them is every large new water user, not data centers alone: battery
cell and materials plants next, then mines, fabs, food processing, hydrogen, and the declared "ghost" user for cases
where modeling the process would take irresponsible assumptions. Andrew (Nov 9): adding a type in a way that makes
sense, for this one and the ones after, matters more than speed.

0001 already promised this: "`Facility` is a small protocol: inputs, `water_use(climate) -> WaterUse`,
`electricity()`, and `land()` ... Battery plants, chip fabs, food processing and hydrogen can be added later without
changing `Site` or `Estimate`." It was never built. `Facility` has one subclass, and data center fields are read in
14 places outside it:

| Where | What it reads |
|---|---|
| `site.py`: `Site.facility` | typed as `DataCenter` |
| `site.py`: `local_weather` | calls `datacenter.cooling.run_location`; `f.cooling`, `f.plant`, `f.it_mw` |
| `site.py`: `by_design` | data center designs |
| `site.py`: `to_bmi_config` | `CoolingWaterBmi`, `LakeCoolingBmi`, `it_mw` |
| `states/mi/provider.py`: `estimate` | `scenario.scenario(mw=, cool=, plant=)`, `sc.electricity`, `sc.grid_water` with `it_mw` |
| `national/provider.py`: `estimate` | stored data center results, `f.cooling`, `f.plant`, `f.it_mw`; source and wastewater rules on "towers or hybrid" |
| `comparisons.py`: `site_before_after` | `s.facility.it_mw`, for backup generator fuel |
| `comparisons.py`: `site_runoff_loads` | `s.facility.cooling == "towers"`, for blowdown phosphorus |
| `estimate.py`: `Electricity` | requires `pue` and `peak_pue` |

Adding battery plants by branching on type in each of these would work once. By the fourth type, every downstream
function would carry a branch per type, and a change to one type could quietly move another's numbers. The waterledger
packages are what Northline, Water Ledger and Basin Ledger are all built on, so the way types are added should be
settled once, here.

## Principles

1. **One set of roles, at every level, and they are Basin Ledger's.** Basin Ledger already reads any water user
   through roles (`basinledger/users.py`), and `CoolingWaterBmi` already reports them as aliases:

   | Role | BMI name (Basin Ledger) | In results |
   |---|---|---|
   | withdrawal | `water_user_water__withdrawal_volume_flux` | `withdrawn` |
   | gain | `water_user_water__gain_volume_flux` | `gain` (a data center's condensate; ore moisture at a mine) |
   | consumption | `water_user_water__consumption_volume_flux` | `consumed` |
   | return | `water_user_water__return_volume_flux` | `returned`, split by destination (below) |
   | storage | `water_user_water__volume` | `storage` (ponds, tailings), optional |
   | temperature | `water_user_return_water__temperature` | optional |
   | power | `water_user__electric_power` | `power_mw` |
   | constituents | `water_user_return_water_<name>__mass_flux` | optional, one per constituent |

   Two additions, both needed by battery plants and both general:
   - **Return by destination.** `to_sewer` (wastewater: blowdown, process, sanitary), `to_source` (water handed
     back where it came from: once-through lake water) and, from Nov 10 (Andrew, design 0014 decision 10), `to_stream`
     (a permitted direct discharge to surface water other than the source, as 13% of new tower-cooled gas plants have).
     `returned = to_sewer + to_source + to_stream`; `to_stream` is used only where a default or a setting chooses it. Today a data center's lake
     design is the only `to_source`, and it is handled by a special case (`lake_estimate`).
   - **Fuel.** `fuel_mw`, energy burned on site (a cell plant's ovens and boilers). Zero for data centers, apart from
     generators, which stay their own item.

   The balance closes at every level, every step, and is held by tests:
   withdrawn + gain = consumed + returned + change in storage.

2. **A type is three pieces, one per layer, and nothing else changes when one is added.**
   - **Model** (`waterledger_models/<type>/`, numpy only): the hourly physics, the Monte Carlo at a location, and a BMI
     component reporting the roles.
   - **Facility** (`waterledger/facilities/<type>.py`, pydantic): the inputs in the industry's own unit, the designs,
     what the default rules need to know about the type, how results are obtained, and the type's own extras.
   - **Tests**: the type's own (balance, physics), plus one shared conformance test run over every registered type.

3. **Shared physics stays shared** (0009, decisions 1, 6 and 7): `heat_rejection`, `once_through`, `daily`, `grid`.
   A type keeps only what is its own. Operating settings are the type's own ranges; every parameter is sampled, set or
   an input.

4. **Downstream reads only the roles.** Comparisons, equivalents, before/after, runoff loads, levels, power plant
   water, grid water, the brief and the site never read a facility's own fields. What they need from a type comes
   through a short list of declared hooks (below), each with a default that means "this type has none".

5. **Types are registered by kind.** `Site.facility` accepts any registered type (a pydantic union discriminated on
   `kind`). Adding a type is writing its three pieces and registering it.

## The standard treatment (Nov 10, 2026; agreed by Andrew the same day)

Andrew (Nov 10): the aim is one standard way to add large water users to the packages and to waterledger.org, a modular
system with calculations compatible across types, so the site stays honest and useful. Data centers came first; the same
work is being done for a group of large users. New models are not patched in one at a time.

Battery cell plants showed the gap. The model was built beside the data centers' and lacked three things they have: water
at the power plants, a full-capacity peak when utilization is sampled, and the assist design. Each was missing because each
type wrote its own Monte Carlo loop. So:

**Every type gets what data centers get, from shared code, unless its physics has no counterpart.** An exception is
written down with its reason. The type supplies only what is its own: its hourly physics, its parameters and their
evidence, and its checks.

| | What every type gets | Where it comes from |
|---|---|---|
| 1 | Every design the shared equipment allows: `dry`, `assist`, `hybrid`, `towers` (`heat_rejection`), and `lake` (`once_through`) | shared; a type leaves one out only for a stated physical reason |
| 2 | One Monte Carlo runner: Latin hypercube draws with the central run, every design, the standard loads, daily statistics, grid water, the standard statistic names | shared (`waterledger_models.runs`, new); the type passes its `hourly` and its parameter space |
| 3 | The standard loads: the run's own (full output or sampled utilization), the peak day at the peak load, and full capacity | shared runner |
| 4 | Water at the power plants for the user's own hourly electricity, by balancing authority | shared (`grid`), through the runner |
| 5 | Mass and energy balances that close every hour, and the role and statistic names | the type's physics; held for every type by the shared conformance test |
| 6 | A BMI component reporting the roles, with a withdrawal limit, dry mode, and intake concentrations giving the return's dissolved mass and temperature (0006) | `ScalarPointBmi` and shared limit and mass code; the type supplies where its heat goes under a cap |
| 7 | Runs on every state's ERA5 cells and stored results in the snapshots, when stored results are decided for the type | one cell runner over any registered type; `MODELS` records the snapshot rebuild |
| 8 | A place-based estimate (`Site`, `Estimate`) through the facility contract below | shared; the type writes its facility |
| 9 | Parameters with ranges and sources, each sampled, set or an input, with a research note | the type's own evidence |
| 10 | A check against real figures (projections, permits, metered use), nothing tuned | the type's own evidence, as a script in `examples/` |
| 11 | Sobol' and Morris sensitivity with the shared functions | the type's own run of `docs/methods/sensitivity/` |
| 12 | The methods log entry, long and short; the site's pages when the type goes on the site | the type's own; the site standard is note 0013 (below) |

**Exceptions so far.** Data centers' cooling plant inside the building (`PLANTS`: shared loop, warm loop, chilled water)
is about how computer racks are cooled and has no counterpart at a cell plant, whose internal split (chilled water for
formation, dry rooms and NMP condensers; a warmer process loop) is sampled instead. Staff water stays outside the per-size
results for data centers because it doesn't scale with size; that is how they store results, not a difference in what
is reported.

**Battery cell plants against the list** (Nov 10, for 3.16.0): 1, 3, 4, 5, 9, 10 and 11 done (assist through the shared
pads, the full-capacity peak and grid water through the shared `grid.RunWater`); 2 waits for the shared runner (the loop
is still the type's own); 6 has the roles but no limit or dissolved mass; 7, 8 and 12 wait on this note and the site
decision.

**The shared runner.** `runs.run_location(model, times, temps, rhs, size, designs=None, utilization=..., settings=None,
water_temps=None, grid=None, n, seed)`. `model` is the type's module: `DESIGNS`, its parameter space, `hourly` (per unit
of size, every role and electricity, for a load), and how its size scales. The runner owns the draws, the loads, the
blocks of hours, the daily statistics, the grid water and the names, so they are the same for every type. Data centers
pass their compiled kernel as their hourly, and their numbers stay identical to the last bit (the identity test). A type
that needs more speed compiles its own hourly; the runner doesn't change.

**The site standard (0013, before any second type goes on waterledger.org).** Every type on the site shows the same
things from the roles: the calculator's before-and-after table, the same comparisons and equivalents, power plant and
grid water, the same rounding, a methods page per type built from the package. What is specific to a type (its size
unit, its designs, its own measures such as PUE) is declared by the facility, so the pages are generated rather than
written per type.

## The contract

### Level 1: the model (`waterledger-models`)

Each type's module provides:

- `DESIGNS`; `RANGES` and `SOURCES` for its own parameters, including its operating settings; `sample_parameters`,
  `central_parameters`. Shared equipment ranges come from `heat_rejection.EQUIPMENT` and `once_through.RANGES`.
- `hourly(...)`: one run's hours, a dict keyed by role (and the type's own parts), per unit of size. The balance closes
  hour by hour.
- `run_location(times, temps, rhs, <size>, designs=None, settings=None, water_temps=None, grid=None, n, seed)`, the
  size in the type's own unit and by its own name (`mw` for data centers, as today; `gwh` for cell plants), returning
  `{design: {stat: {p10, p50, p90, central}}}` with the standard statistic names:
  - water: `<role>_<stat>` for `withdrawn`, `consumed`, `returned`, `to_sewer`, `gain`, with `avg`, `peak_1in10`,
    `record`, `annual_mg`, and for withdrawn and consumed `max_month`, `max_90day`, `worst_year_mg`;
  - power: `power_mw_avg`, `power_mw_peak_1in10` (hour), `power_mw_peak_day_1in10`, `fuel_mw_avg`;
  - grid: `grid_<BA>_<kind>_avg` and `_peak_1in10`, from one shared function that takes any user's hourly electricity
    (today it lives inside the data center's run loop);
  - the type's own, under its own names: `pue_avg` for data centers, `site_kwh_per_kwh` for cell plants.
  The results are the user's whole water at that size, staff included. How a type stores results for reuse is its own
  business: data centers keep "per 100 MW plus staff runs", because staff water doesn't scale with size.
- A BMI component on `ScalarPointBmi` reporting the roles' names: `CoolingWaterBmi` and `LakeCoolingBmi` today,
  `BatteryCellBmi` next. `bmi-tester` runs on each in CI (0001, decision 7).

### Level 2: the facility (`waterledger`)

```python
class Facility(BaseModel):
    kind: str                       # the registry key
    design: str                     # one of the type's DESIGNS (DataCenter keeps `cooling` as its name for it)

    DESIGNS: ClassVar[tuple]        # what by_design iterates
    EVAPORATIVE: ClassVar[tuple]    # designs whose wastewater is mostly cooling blowdown (default-rule input)
    size: (value, unit)             # for display: (300, "MW of IT capacity"), (43.75, "GWh/yr of cells")

    def results(self, site, weather) -> Results        # standard bands for every role, plus the type's extras
    def bmi_config(self, ...) -> (entry, cfg)         # site.to_bmi_config delegates here
    # hooks, each defaulting to "none"
    def backup_generator_mw(self) -> float | None     # before/after's fuel row
    def cooling_blowdown(self, results) -> Range | None   # runoff loads' blowdown phosphorus
```

**Where results come from is the type's choice.** A data center reads stored results: Michigan's site files through
`scenario` (which the page mirrors, so its parity tests stay), and the snapshots' cells elsewhere, or a run at the
place with `weather="local"`. A cell plant has no stored results, so it runs at the place every time (Open-Meteo's
best match, and GLERL temperatures for the lake design, both cached). A type can gain stored results later without
changing anything downstream.

**What a state provider does.** Today each provider computes the whole data center estimate. Under the contract a
provider supplies the place: stored results for types that have them, the reference values, and the data the default
rules use (systems mapped in the place, the nearest sizable system, the sewer plant and its spare design flow). The
facility computes. Michigan keeps its rule code where the page mirrors it.

**Default source and wastewater.** One rule in each place, fed by the type: "evaporative designs go to wells when no
system is mapped" becomes `design in facility.EVAPORATIVE`, and "does the wastewater fit in the plant's spare design
flow" uses the type's own `to_sewer`. For data centers this is what it is today.

### Level 3: the estimate

`Estimate` keeps its shape: `water` (`WaterUse`) and `electricity` (`Electricity`) are the roles at the site's size, and
everything after them reads only those. Two changes:

- `WaterUse` gains `to_source` (a `Flow`, None for types and designs that hand nothing back). `lake_source` keeps its
  meaning, once-through cooling on a Great Lake, for every type.
- `Electricity` gains `fuel_mw` (optional). PUE is a data center's own measure: see decision 4.

## What changes for data centers

Nothing in the numbers. Every item in the table above moves behind the facility or a hook:

- `DataCenter.results()` holds what the two providers' `estimate` and `local_weather` do now.
- `DataCenter.bmi_config()` holds `to_bmi_config`'s body; `backup_generator_mw()` is `it_mw` times the generator
  ratio `runoff.fuel` uses; `cooling_blowdown()` is today's towers-only `returned.avg.p50`.
- The providers keep the place-side parts.

**Identity test, every state.** Before any of this moves, the full `Estimate` JSON is saved for a set of places in each
published state (Michigan, Ohio, Virginia, Texas, Wisconsin): every design, every wastewater choice and both weather
modes. After each step it must match to the last bit, as for the heat rejection move. The Michigan page parity tests
must also stay green.

## Battery cell plants as the first new type

`BatteryCellPlant(capacity_gwh, design, chemistry="nmc", utilization="full", settings={})`, designs dry, assist, hybrid,
towers and lake, runs at the place. Extras: site energy per kWh of cells, and water withdrawn and consumed per kWh.
Grid water comes through the shared function, from the plant's own hourly electricity. Backup generators: none until a
source sizes them [A]. Blowdown phosphorus: the plant's tower blowdown.

**As built (Nov 12).** Run at the place every time (about 20 seconds a design after the weather download), with `weather` either way:
the estimate says `local`. Designs dry, assist, hybrid, towers (the default: wet towers at most plants in DOE's EAs [A]) and lake (GLERL's
temperatures for the place's lake, and lake surface water as the source, as for data centers). Grid water from the place's balancing
authority, fit as a data center cell's is (`national.era5.grid_factors_at`). Wastewater goes to the sewer or, with `wastewater="water"`,
to its own discharge, the same volume; where the defaults find no sewer in reach it goes to its own discharge, never a septic system,
and septic or reuse given by hand are refused [A]. Consumed on the middle estimate is withdrawn less returned, so the books close, as for
data centers. Extras: `site_kwh_per_kwh`, `withdrawn_l_per_kwh`, `consumed_l_per_kwh` and `blowdown_avg`, the towers' own blowdown, new in
the model's results (no number changes), which `cooling_blowdown` gives runoff loads instead of the whole return. Not yet: supply
scenarios at the place (`supply.py` still runs data centers only), stored results, the site.

**The check that the contract works:** battery plants go in without touching `Site`, the comparisons, the levels or the
providers, apart from registering the type. If anything downstream needs an edit, the contract is wrong there, and it
is fixed in the contract, for every type.

**Later, the declared user.** A type with no process model: withdrawal, return fraction and destination,
concentrations and power, as declared ranges. Not built now; it is the test that the contract isn't shaped by cooling.
If it can be written as a facility with `results()` from declared numbers, the contract is general enough.

## Stability under 3.x

The packages are at 3.x, and from 3.10 the README promises that a breaking change to the public API waits for 4.0.
The number came early, but it is what users see, so the packages are held to it (Andrew, Nov 9). In practice:

- **Additions only.** Everything here is added beside what exists: `Site.facility` widens from `DataCenter` to any
  registered type; `WaterUse` and `Electricity` gain optional fields; `DataCenter` keeps every field, including
  `cooling` and `it_mw`; `Site.estimate`, `by_design` and `to_bmi_config` keep their signatures; `CoolingWaterBmi`
  and `LakeCoolingBmi` keep their names. `Electricity.pue` becomes optional in its type, but is always set for a data
  center, as now.
- **The contract becomes public API when it ships**, and is listed in the README beside `Place`, `Context`, `Site` and
  `Estimate`: the `Facility` contract and its hooks, the role names, the standard statistic names and the BMI role
  names. A change to any of them after the release that carries the contract waits for 4.0. This is the reason to settle it carefully now.
- **Deprecation, not removal.** A name replaced in 3.x keeps working, raises a `DeprecationWarning` that names its
  replacement, and is listed under **Deprecated** in the CHANGELOG. It is removed only in 4.0.
- **The README's "in beta, whatever the 3.x number suggests" line goes.** The Stability section says what is public,
  what may change in a minor release (internal modules and functions with a leading underscore), and the deprecation
  rule. Model results are versioned by `MODEL_VERSION`, not semver, as now.
- **Numbers and API stay apart.** None of steps 1-5 changes a number; the identity test proves it. A change to any
  type's numbers raises the one model version, and `MODELS` records the type (decision 6).

## Not in this note

- **waterledger.org.** The site format stays data-center-only for now; whether battery plants go on the site is decided
  later (0009, decision 5). How any type goes on the site is note 0013, part of the same plan (the standard treatment,
  above).
- **Cathode materials plants:** 0012, on this contract.
- **Michigan's own path:** 0011, done before this note's steps.

## Order of work, each step its own commit with the identity test green

1. The identity snapshot of today's estimates in every state.
2. Grid water as a shared function on any hourly electricity; the data center run calls it. **Done Nov 10**
   (`grid.RunWater`; the battery run calls it too). With it, assist's pads moved to `heat_rejection`, and battery plants
   took both, with the full-capacity peak: the data center Monte Carlo matches its record to the bit.
2a. The shared runner (`runs`), with the standard loads; data centers onto it with their kernel; battery cell plants onto it.
   **Done Nov 10** (branch shared-runner, for the release after 3.16.0 with the power supply types). A type gives a small model:
   its designs, its draws with the central run last, a per-location setup, and each draw's `runs.Hours` (water by role with its scale, at
   the run's load and, where it differs, the peak day's and full capacity's; hourly MW at each; its own measures). The runner works the
   rest the same for every type, and `extra(design, p, hours)` hands a caller each draw's hours (the supply scenarios' hook).
   - **Numbers.** Against records of both types' Monte Carlos from before the move, every value is identical to the bit except the power
     figures, which the runner works from the hourly MW with one formula for every type: data centers' `power_mw_avg` and
     `power_mw_peak_1in10` within 4.1e-16 relative, cell plants' three within 4.9e-16. Keeping each type's own order of multiplication
     would mean a scale per statistic in the contract; the last bit is not worth that (Andrew agreed, Nov 10).
   - **Not moved:** data centers' lake-source cooling (`datacenter.lake`) keeps its own loop; it comes onto the runner with the facility
     contract (step 3), where its `to_source` return is handled for every type.
3. The registry and the `Facility` contract; `DataCenter` onto it (`results`, `bmi_config`, hooks); providers reduced to
   the place side. **Built Nov 12** (`waterledger.facilities`), the providers' reduction left for 0011 (above). The record of step 1 is
   `tests/data/estimates_before_contract.json` (ten states, two places each, every design, wastewater choice and cooling plant, by_design,
   to_bmi_config and the model run at the place), written from 3.21.0 by `tests/contract_reference.py`; `tests/test_contract_identity.py`
   holds every recorded value to the bit.
4. Downstream onto the hooks: `before_after`, runoff loads, `by_design`, `to_bmi_config`. **Built Nov 12.** `before_after` takes
   `gen_mw` (`runoff.generators`); with no generators known, no fuel row.
5. The conformance test, over every registered type. **Built Nov 12** (`tests/test_facility_contract.py`).
6. Battery cell plants: the facility and its tests. **Built Nov 12** (`waterledger.facilities.battery_cell`; below). The model's pieces are done ahead of steps 1-5 (Andrew, Nov 10:
   battery work before the Michigan work): sewer and source returns, peak-hour power, chemistry, `BatteryCellBmi`, the
   check at every EA plant and the sensitivity analysis (0009).
7. READMEs, docs, CHANGELOG, the methods log; then a release on Andrew's word.

## Decisions to agree

1. **Roles. Agreed (Andrew, Nov 9).** Basin Ledger's roles at every level, plus return by destination (`to_sewer`, `to_source`) and `fuel_mw`.
2. **Three pieces per type, a registry and a shared conformance test. Agreed (Andrew, Nov 9).** A type is added by writing its model, facility
   and tests and registering it.
3. **Downstream reads only roles and hooks. Agreed (Andrew, Nov 9).** The hooks to start: `backup_generator_mw` and `cooling_blowdown`. New
   hooks are added to the contract, with a "none" default, never as a branch on type.
4. **Type-specific measures. Agreed (Andrew, Nov 9).** `Estimate.extras`, a dict of named ranges (`pue`, `peak_pue` for data centers;
   `site_kwh_per_kwh` for cell plants). `Electricity.pue` and `peak_pue` stay as they are for data centers through 3.x,
   so nothing that reads them breaks, and are None for other types. They move to `extras` only at 4.0.
5. **Providers supply the place; facilities compute.** Today each provider does two jobs: the place's (stored results
   for its cell, staff runs, lake results, the facts the default rules read: systems mapped, the nearest sizable
   system, the nearest sewer plant and its spare design flow) and the data center's (which results for the design,
   scaled by `it_mw`; the default rules on "towers or hybrid"; electricity and grid water). With both in each provider,
   every provider must know every type: providers times types. Split, a provider knows places and a facility knows
   its type, so adding a type touches no provider and adding a state touches no type. Michigan has no exception: it
   reads through the national provider with its own layers once 0011 is done (Andrew, Nov 9, asked to bring Michigan
   in line rather than carry it beside). The alternative, facilities reading snapshots themselves, would put each
   state's file layout into every type.
6. **One model version, with a record of what each version changes. Decided (Andrew, Nov 10), replacing the Nov 9
   revision.** The Nov 9 revision gave each type its own model version. Andrew set it aside on Nov 10: separate versions
   would get awkward as types are added. Most changes to the numbers are to pieces no single type owns (the shared heat
   rejection, the grid component, the weather correction, the places' water and power data), so they would raise
   several versions at once, and the place data would need a version of its own. A coupled run would cite a set of
   versions instead of one.
   - **`waterledger_models.MODEL_VERSION` is the one version** for every type and is raised by a minor step when any
     number changes.
   - **`waterledger_models.MODELS`** records, from 1.12, the types each version changes and the model of the snapshots
     it reads. A version that changes nothing the snapshots carry skips them and reads the last rebuilt ones
     (`snapshot_model()`), so no state is rebuilt to the same numbers and no package prints the other-model note. Model
     1.12 (battery cell plants) reads model 1.11's snapshots and cell runs.
   - **Snapshots stay data releases on their own cadence** (0003), dated and never changed. `by_model` is keyed by the
     snapshot model, and `Estimate.model_version` is the model of the data it read, as now, so a data center estimate
     under model 1.12 names 1.11.
   - **Stored results for a new type** come when they are worth precomputing (for battery plants, Andrew's call, with
     the site decision). A version that adds them, or changes numbers a snapshot carries, rebuilds the snapshots.
7. **Release. Agreed (Andrew, Nov 9); revised Nov 10.** Steps 1-5 change no numbers and add to the public API without
   breaking it, so they ship as a minor release with the battery cell plant facility. The battery model itself went
   first, in 3.16.0 (model 1.12), on Andrew's word of Nov 10 to put battery work ahead of the Michigan work.
8. **Stability. Agreed (Andrew, Nov 9).** The contract is public API from the release that carries it, under the 3.x promise (public API has
   been committed since 1.x, and following it mostly serves the project); deprecations warn and wait for 4.0; the
   README's beta line is replaced by the policy above. Where following it would hold the project up, the maintainer
   can make an explicit exception, recorded in the CHANGELOG and the design note with the reason.
