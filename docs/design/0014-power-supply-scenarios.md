# 0014: Power supply scenarios: what serves a user's hourly electricity, and the water it takes

Status: **decided Nov 10, 2026 (Andrew; all eleven decisions agreed, with his notes on 2, 5, 9 and 10 below). Steps 1-5 built Nov 10 on branch
shared-runner (model 1.13; methods log, Nov 10); `est.supply` built for data centers Nov 10 (waterledger.supply); the `GasPlant` facility and other types'
`est.supply` wait on design 0010's facility contract.** Evidence: `docs/research/power-supply-water.md`.
Builds on 0008 (power at the grid), 0010 (water user types and the standard treatment) and the shared Monte Carlo runner
(`waterledger_models.runs`, branch `shared-runner`, not merged). 0012 (cathode plants) and 0013 (the site standard) are
reserved, so this is 0014.

## Why

Today a user's electricity is served by the grid: `waterledger_models.grid` turns each hour's MW into water at the
plants of the user's balancing authority (0008, part 1). Andrew (Nov 10, 2026) widened the scope. Many data center
proposals say they will bring their own power, and renewable developers look for power purchase agreements at new
campuses. A community reading a proposal needs to know what each of those choices means for water, and where that water
is taken: a new gas plant on the site draws on the same source as the campus, while the grid's plant water is spread
over a region.

So a user's supply becomes a scenario:

- (a) the existing grid serves it (today's numbers, unchanged);
- (b) one or more new gas plants on the site or nearby;
- (c) one or more new solar and wind projects under a PPA;
- (d) mixes, with each scenario's unserved hours going to the grid or to gas.

Grid battery storage stays part of the grid component (0008). Every plant in a scenario is hypothetical and modeled from
public data.

## The scope rule

This holds for the code, the tables, the tests, the examples and the methods pages:

1. **No real power plant, transmission line, substation or route is named, profiled or laid out**, even though the data
   is public. A scenario describes technology, size and cooling ("four 35 MW aeroderivative turbines, water injection,
   towers"), never a project. Its location is the user's own place, which sets the weather; nothing is sited, routed
   or interconnected.
2. **Real plants' reported data (EIA-923, EIA-860) are used only in aggregate**, to check per-MWh factors: by technology,
   cooling type, region and month, and only in cells holding at least five plants [A: the threshold keeps one plant from
   being read out of a cell]. No output lists a plant. Scripts that build the aggregates write only the aggregates.
3. **Trackers stay Northline's.** A proposal record may say a campus plans on-site gas; the package takes a scenario,
   not the record, and does not carry the project's name.
4. Nothing that is or depends on critical energy infrastructure information (CEII), as in 0008.

## Scenarios

A scenario is a list of **resources** and a **residual rule**.

| Resource | What it is | Sized by |
|---|---|---|
| `gas` | a new gas plant of one technology (`cc`, `ct`, `engine`, `fuel_cell`), a number of identical units, one cooling design | units × unit MW, or a rule (below) |
| `pv` | a new solar PV project, single-axis tracking or fixed tilt | MW AC, or a share of the user's annual MWh |
| `wind` | a new onshore wind project | MW, or a share of the user's annual MWh |

The **residual** is the user's hourly load left after the resources: `"grid"` (the grid component serves it, at the
average and marginal mix, as 0008), `"gas"` (a gas resource in the scenario takes it, up to its available capacity, and
what remains is unserved), or `"none"` (islanded: what remains is unserved and reported). A gas resource can also be
**firm** at a set MW (grid-parallel operation), with the residual going to the grid.

| Scenario | Resources | Residual | Reads as |
|---|---|---|---|
| a | none | grid | today |
| b1 | gas, N+k units | none | islanded campus on its own plant |
| b2 | gas, firm MW | grid | grid-parallel plant carrying part of the load |
| c1 | pv and/or wind at 100% of annual MWh | grid | annual-matched PPA |
| c2 | pv and wind at a higher share | grid | toward hourly matching |
| d1 | pv and wind | gas | renewables firmed by gas |
| d2 | pv, wind and gas | grid | all three, grid for what remains |

**Physical and contractual.** A virtual PPA does not change which plants run in an hour; a co-located or physically
delivered one does. Proposed: resources serve the load hour by hour (the physical reading, which is also how hourly
matching is scored), and the annual-matching figure is reported beside it. **Surplus** hours (renewables above the load)
are exported: their MWh are reported, with no water credit by default and the grid water they would displace at the
marginal mix beside (decision 4).

## The gas plant as a water user type

A new gas plant is a water user like any other: it withdraws and consumes water to reject heat, it burns fuel, and its
condenser uses the shared heat rejection. So it is added under 0010's standard treatment, as three pieces.

**Model** (`waterledger_models/gas/`, numpy only). `hourly(...)` takes the plant's hourly output demand (net MW), the
hour's weather and the draw's parameters, and returns per unit of size each hour: net output, unserved, fuel (`fuel_mw`),
heat to the condenser, and the water roles. Hour by hour:

1. **Available capacity** of a unit: its ISO rating × (1 − derate × max(0, T − T_ref)), with T the dry-bulb, or the
   inlet temperature after evaporative cooling where the design has it (inlet cooling toward the wet-bulb at a sampled
   effectiveness).
2. **Units online**: enough to carry the hour, up to the units available after outages; each runs at the hour's share of
   its available capacity. What the units cannot carry is unserved.
3. **Heat rate**: ISO heat rate × (1 + heat-rate slope × max(0, T − T_ref)) × a part-load factor.
4. **Fuel** = net output × heat rate. **Condenser heat** (combined cycle only) = the share of the losses that goes to
   the condenser. The energy balance closes each hour: fuel = net output + auxiliary load + condenser heat + stack and
   other losses.
5. **Water**: the condenser heat goes to `heat_rejection` (`towers`, `hybrid`, `assist`, `dry`) or to `once_through`
   (`lake`) exactly as a data center's or a cell plant's heat does, at the hour's dry-bulb and wet-bulb. Process water is
   added where the technology has it: NOx injection water (water-to-fuel ratio × fuel mass) and its demineralization
   reject, and inlet cooling water (air flow × the rise in humidity ratio). Tower blowdown, demineralization reject and
   unevaporated inlet water go to the return. The water balance closes each hour: withdrawn = consumed + returned.

**Parameters** (ranges in the research note; sampled, set or an input, each with its source):

| Parameter | Range or value | Source |
|---|---|---|
| ISO heat rate, Btu/kWh HHV | cc 6,200-6,450; ct 9,100-10,500; engine 8,200-9,900; fuel cell 6,300-9,950 | EIA AEO2023 Table 1; NETL Rev. 4a ES-4; EPA CHP Catalog Tables 2-2, 3-2, 6-3 |
| Capacity derate above 15 °C, per K | ct 0.9-1.0%; cc wet 0.3-0.5%, dry about 0.7%; engine 0.18% above 25 °C; fuel cell about 0 | EPA CHP Catalog p. 3-10, p. 2-12; Sathaye et al. (2011) p. 11 |
| Heat-rate slope above 15 °C, per K | ct about 0.35%; cc 0.05-0.2% [A] | EPA CHP Catalog p. 3-10; Meng and Sanders (2019) §4 |
| Part-load heat rate at half load | engine +8-10%; ct and cc +15-25% [A for cc]; linear between [A] | EPA CHP Catalog p. 2-11 |
| Condenser share of losses, cc | 0.62 at ISO (NETL B31A: 391 of 628 MW of losses), sampled 0.55-0.65 [A] | NETL Rev. 4a Exhibit 5-9 p. 564 |
| Auxiliary load, cc | 1.9% of gross at ISO (B31A: 14 of 740 MW) plus the heat rejection's fans and pumps from `heat_rejection` | NETL Rev. 4a ES-4 |
| NOx water-to-fuel mass ratio | 0 (dry low-NOx) or 0.5-1.0 (water injection), a setting | AP-42 §3.1.4.1 p. 3.1-6 |
| Inlet cooling effectiveness | 0.85-0.95 [A]; air flow 8,040 kg/h per MW of turbine output (NETL B31A) | research note S4 |
| Demineralization recovery | 0.70-0.80 [A] | none found |
| Unit availability | 0.90-0.97 [A], outages drawn by hour | none found in this note; NERC GADS is the place to look |
| Cycles of concentration | operating setting, 3-6, central 4 | NETL Rev. 4a p. 35; Diehl and Harris (2014) p. 12 |

**Designs.** Every design the shared equipment allows, with exceptions written down (0010, item 1):

| Technology | Designs | Exception and reason |
|---|---|---|
| `cc` | `towers`, `hybrid`, `dry`, `assist`, `lake` | `assist` is an air-cooled condenser with evaporative pre-cooling of its inlet air, the counterpart of the data centers' pads [A: no cost or water figure for power plants found] |
| `ct` | one design, `none`, plus inlet cooling and NOx water as settings | no condenser: a simple-cycle turbine rejects its heat in the exhaust |
| `engine` | `dry` (radiators); `towers` allowed | jacket water usually goes to radiators (EPA CHP Catalog p. 2-8) |
| `fuel_cell` | `dry` | product water is recovered; water at start-up is not quantified |

**Facility** (`waterledger/facilities/gas_plant.py`): `GasPlant(mw, technology, design, units=None, nox="dln",
inlet_cooling=False, settings={})`, registered as `kind="gas_plant"`. It can stand alone (a proposed peaker, evaluated
at a set capacity factor) or serve a user as a resource in a supply scenario. Extras: heat rate, capacity factor, fuel
(MMBtu), and water per MWh withdrawn and consumed. Its own electricity is not drawn from the grid, so item 4 of the
standard treatment (grid water for the user's own hourly electricity) does not apply; that is its stated exception.

**Tests.** The hourly water and energy balances; the NETL check at ISO weather; the derate curve against the CHP
Catalog's 80% at 100 °F; and the shared conformance test over every registered type. A BMI component, `GasPlantBmi` on
`ScalarPointBmi`, reports the roles (withdrawal, consumption, return, temperature for `lake`, power as negative demand
[A: or a separate generation name], fuel).

## Renewables' hourly generation

Solar and wind use little water, so they are generation profiles, not water user types: `waterledger_models/supply/`
with `pv.py` and `wind.py`, numpy only.

- **Weather.** ERA5 from the open copy the packages already read (0004) carries `shortwave_radiation`,
  `direct_radiation` and the 100 m wind components. `waterledger_data.era5` fetches them for the cells a supply run
  needs, into the same raw cache, on the same 30 years and hours, so a heat wave meets the campus's load, the turbines'
  derate and the panels' output in the same hours.
- **PV**: the PVWatts method (Dobos 2014): sun position at mid-hour (ERA5 radiation is a preceding-hour mean), beam and
  diffuse from ERA5 directly (no decomposition model), plane of array for single-axis tracking or fixed tilt, cell
  temperature, temperature coefficient, inverter loading ratio and clipping, and system losses. pvlib is a test
  dependency only: the numpy code must match pvlib's PVWatts chain hour by hour on the same inputs.
- **Wind**: 100 m speed to hub height by a power law [A], a published reference power curve [A], and plant losses for
  wakes, availability and electrical losses, sampled 10-20% [A].
- **Water**: panel washing as a factor (0-5 gal/MWh where operators do not wash, to 26 where they do; Macknick et al.
  2012, Meldrum et al. 2013), a setting by region [A]; wind 0-2 gal/MWh. Construction water is a one-time total per MW
  (PV) or per turbine (wind), reported apart from annual water.
- **Parameters** are sampled per draw like any other: system losses, temperature coefficient, wind losses, and a bias
  factor on the resource until the check below says whether ERA5 needs one at the packages' cells.

## Dispatch and unserved hours

For each draw, at the run's load and again at the peak-day load:

1. Renewables' output for the hour (their profile × size × the draw's factors) serves the load first.
2. A firm gas resource serves its set MW, up to its available capacity.
3. The residual goes by the scenario's rule: to the grid; to gas, up to the units available, with what remains
   unserved; or, islanded, unserved.
4. Surplus (renewables above the load) is exported and counted.

The balance closes every hour: load = served by each resource + residual to the grid + unserved, and generation =
served + surplus. Unserved hours are reported, never filled silently (decision 5).

**Sizing defaults** (each can be set instead):

- **Gas, islanded:** units = N + k, with N from the user's 1-in-10-year highest hour at full capacity divided by a
  unit's available capacity at the place's 0.4% design dry-bulb (`heat_rejection.design_dry_bulb`); k = 1 by default
  (Tier III's N+1, Uptime Institute), 2 as an option. The research note's arithmetic shows this landing inside the IEA's
  30-70% overbuild once derate and ratings are counted.
- **Gas, grid-parallel:** a firm MW, or a share of the average load.
- **Renewables:** nameplate so that the central run's annual generation is a set share of the user's annual MWh (100%
  for annual matching).

A plant is sized once, not per draw. The runner calls the central draw last, so sizing comes from a first pass: the
caller runs the user's central draw alone, sizes the scenario from it, then runs the Monte Carlo with the sizes fixed.
That costs one extra draw and needs no change to the runner.

## How it runs: on the shared runner

The hook as built (`runs.run_location(model, times, temps, rhs, designs=None, grid=None, extra=None)`) calls
`extra(design, p, hours)` once per draw, central last, with the draw's `Hours`: `.mw` (hourly MW at the run's load),
`.mw_peak` (at the peak-day load, or None), `.mw_full` (at full capacity, or None), `.water`, `.utilization`. It returns
`{stat: value}`, which the runner summarizes as p10, p50, p90 and central with the rest. A supply scenario fits it: it is
a function of the draw's hourly MW and the place's weather.

`Supply(scenarios, grid, weather)` is a callable built by the caller with the place's radiation and wind for the same
`times`, the grid factors for the residual, and the fixed sizes from the first pass. Called with a draw's hours, it
dispatches `mw` and `mw_peak` for each scenario and returns that draw's statistics.

Four changes to the hook would keep one code path for what the runner already owns. Each is an addition; existing
callers are unaffected:

1. **`extra.setup(times, tdb, twb, rh)`, called once if present**, as `model.setup` is, so the supply uses the runner's
   wet-bulb and precomputes its weather terms (sun position, plane-of-array irradiance, the gas units' hourly derate)
   once per place rather than once per draw.
2. **The draw's index**: `extra(design, p, hours, i)`, with the central draw last. The supply's own parameters (heat
   rate, derate, losses, outages) are drawn by their own Latin hypercube and paired with the user's draws by index.
   Without it, the supply would have to count calls, which breaks if the runner's order changes; folding the supply's
   parameters into the type's own draws would tie every type to the supply.
3. **Hourly series summarized by the runner.** `extra` may return, besides scalars, hourly water as `(hourly, scale)`
   pairs at the run's load and at the peak-day load, as `Hours.water` and `Hours.peak` are, and the runner applies
   `daily_stats` to them under the names given (`supply_<scenario>_gas_withdrawn_avg`, `_peak_1in10`, `_annual_mg`,
   `_max_month`, ...). Otherwise the supply would copy the daily statistics.
4. **Residual grid water through `RunWater`.** `extra` may return the residual MW the grid serves, at the run's load and
   at the peak-day load, and the runner computes its plant water with the same `RunWater` as the user's own, under
   `supply_<scenario>_grid_<BA>_<kind>`. Grid water then has one implementation, average and marginal.

A small return type, `runs.Supplied(water, peak, grid_mw, grid_mw_peak, scalars)`, would carry 3 and 4. Runs stay on
Andrew's machine; the dispatch is vectorized over the 30 years of hours, and the cost per draw is about one more
heat-rejection call per gas scenario [A: to be timed].

## What each scenario reports

Per scenario and user design, each as p10, p50, p90 and central:

| Group | Statistics |
|---|---|
| What served the load | `share_gas`, `share_pv`, `share_wind`, `share_grid` of annual MWh; `unserved_mwh_annual`, `unserved_hours_annual`, `unserved_mw_max`; `surplus_mwh_annual` |
| The gas plant | its water roles with the standard names and statistics (`gas_withdrawn_avg`, `_peak_1in10`, `_record`, `_annual_mg`, `_max_month`, `_max_90day`, `_worst_year_mg`; `gas_consumed_...`; `gas_returned_...`, `gas_to_sewer_...`); `gas_fuel_mw_avg`; `gas_mmbtu_annual`; `gas_capacity_factor`; `gas_unit_hours_annual`; withdrawn and consumed per MWh |
| Renewables | `pv_mwh_annual`, `wind_mwh_annual`, their capacity factors; panel washing water; construction water as a one-time total (by size, so central only) |
| The grid's share | `grid_<BA>_<kind>_avg` and `_peak_1in10` for the residual, average and marginal (0008) |
| Totals | power water, withdrawn and consumed: **local** (gas plant and panel washing, on the campus's own source or system) and **grid** (spread over the BA), and their sum, for the average day and the peak day, beside scenario (a)'s `grid_` figures |

Every name carries the prefix `supply_<scenario>_`. Scenario (a) needs no supply code: its numbers are today's `grid_`
statistics, and they must not change by a bit when supply scenarios are added (the identity test).

At the estimate, `est.supply[scenario]` carries the same as bands at the site's size. Supply scenarios need the user's
hours, so they run at the place (`weather="local"`), as cell plants do; they are not stored in the snapshots (decision 9).

## Checks against public figures

Nothing is tuned. Each check is a script in `examples/` or `docs/methods/power_supply/`, its results in the methods log.

1. **NETL at ISO weather:** a tower-cooled F-class combined cycle held at 15 °C and 60% relative humidity, 4 cycles,
   reproduces NETL B31A's 3.1 gpm/MW consumed and 4.0 withdrawn (186 and 240 gal/MWh) within 10% [A: the tolerance].
2. **A year of weather, by design,** inside the published ranges: towers 130-300 consumed and 150-290 withdrawn
   (Macknick, Meldrum, USGS); dry 0-4; once-through 7,200-21,000 withdrawn and 20-230 consumed; hybrid between dry and
   towers.
3. **EIA-923 in aggregate:** generation-weighted monthly water per MWh for combined cycle on towers, by region, in
   cells of five or more plants, against the model's monthly values at a cell in the same region: the seasonal shape and
   the level. Gas as a whole in the package's BA table runs 150-223 gal/MWh consumed by month in MISO (2024).
4. **Derate:** turbine output at 100 °F within 3 points of the CHP Catalog's 80%; combined cycle 0.3-0.5% per K (wet),
   about 0.7% (dry); dry against wet near 4% of rating on the 1% dry-bulb day (Maulbetsch and DiFilippo 2018).
5. **PV and wind:** capacity factors at the cells against EIA's (U.S. wind 34.3% and PV 23.2% in 2024; state wind by
   the research note's estimate) and LBNL's regional PV values; the hourly shape against EIA-930's hourly solar and
   wind generation for the BA, normalized by its capacity (aggregate, no plant), by hour of day and month; ERA5's hourly
   error against Davidson and Millstein (2022).
6. **Overbuild:** islanded N+1 and N+2 at the design dry-bulb, against the IEA's 30-70%.
7. **Balances, every hour, every draw:** energy (load, served, residual, unserved, surplus; fuel, output, condenser
   heat, losses) and water (withdrawn = consumed + returned), held by tests as the other types are.

## Version and stability

Adding supply scenarios changes no existing number: scenario (a) is today's grid water, held by the identity test. The
new numbers raise `MODEL_VERSION` one minor step, and `MODELS` records the gas plant type and supply scenarios as what
it changes; the snapshots are skipped (0010, decision 6). The scenario inputs, the statistic names and `GasPlant`
become public API in the release that carries them, under the 3.x rules (0010, decision 8).

## Not in this note

- Battery storage paired with a PPA or on the campus: grid storage stays in the grid component (0008); a campus battery
  would be its own resource later.
- On-site diesel generators for outages and testing: 0008, part 4.
- Which plants the region builds or keeps for the load: 0008, part 2 (PyPSA-USA).
- Air emissions: as 0008, decision 3, run hours and fuel only.
- Upstream fuel water (gas production), outside the boundary (research note, §1d).
- Nuclear, geothermal and hydrogen supply: the same contract would take them as further technologies or types.
- How scenarios show on waterledger.org: 0013.

## Order of work, each step its own commit

1. The hook changes in `runs` (setup, index, `Supplied`), with the runner's identity test green.
2. The gas model: physics, parameters, `GasPlantBmi`, checks 1, 2 and 4, the sensitivity analysis; first, the research on where
   new gas plants' blowdown goes (decision 10).
3. ERA5 radiation and 100 m wind in `waterledger_data.era5`; `supply/pv.py` and `supply/wind.py` against pvlib; check 5; then
   renewables' land, runoff and construction (decision 2's note: the research first, the runoff through `runoff`).
4. Dispatch and scenarios as the runner's `extra`; balance tests; check 6.
5. The EIA aggregate check (3), as a methods script writing only aggregates.
6. `GasPlant` as a registered facility and `est.supply`; READMEs, docs, the methods log; a release on Andrew's word.

## Decisions (agreed by Andrew, Nov 10, 2026)

1. **A scenario is resources plus a residual rule** (`grid`, `gas`, `none`), with scenario (a) unchanged. Agreed.
2. **The gas plant is a water user type on the standard treatment** (`waterledger_models/gas/`, `GasPlant`), with four
   technologies (`cc`, `ct`, `engine`, `fuel_cell`) and the design exceptions in the table above. Agreed, with Andrew's
   note: **solar has runoff implications, and both solar and wind have construction implications; wind generally has the
   lowest land impact.** So renewables get a land, runoff and construction part (below), not only a generation profile.
3. **Renewables are generation profiles, not types** (`waterledger_models/supply/`), from ERA5 radiation and 100 m wind
   in the open copy, fetched for the cells supply runs need rather than for every cell. Agreed; with decision 2's note,
   a project also carries its land, runoff and construction water.
4. **Resources serve the load hour by hour;** annual matching is reported beside. Surplus is exported with no water
   credit by default, and the grid water it would displace at the marginal mix is shown beside. Agreed.
5. **Unserved hours are reported, never filled silently.** Agreed, with Andrew's note: most campuses with on-site or
   nearby power will likely stay connected to the grid, so **`grid` is the default residual**: the grid serves what the
   resources don't, and nothing is unserved. Islanded operation (`none`) is a real option, not a corner case: off-grid
   builds are being planned (Andrew cites Alphabet's purchase of Intersect Power, announced late 2025, to verify). An
   islanded scenario says how many hours and MWh its plant cannot carry.
6. **Sizing defaults:** gas N+1 at the 0.4% design dry-bulb from the 1-in-10-year full-capacity peak hour (N+2 as an
   option); renewables by share of annual MWh; plants sized once, from a first pass on the central draw. Agreed.
7. **Four additions to the runner's hook:** `extra.setup`, the draw index, hourly series summarized by the runner, and
   the residual's grid water through `RunWater`. Agreed.
8. **On-site plant water is local water and is reported as such:** beside the user's own roles and in a combined
   campus-plus-power line, not merged into the user's `withdrawn`. Agreed.
9. **Supply scenarios run at the place** and are not stored in the snapshots. Agreed for now. Andrew's framing: the
   calculator's values have limits and are mostly illustrative, but are meant to be accurate to a level that is
   valuable.
10. **The gas plant's return** follows the place's default wastewater rule like every type (sewer where it fits); a
    direct discharge to the water it draws from is `to_source`. No new role. Agreed **as long as it is realistic**: the
    research note is to check where new gas plants' blowdown actually goes (a municipal sewer, a permitted discharge to
    a stream, zero liquid discharge), by plant size and technology, before the default is set. A permitted discharge to
    a different stream than the intake is neither `to_sewer` nor `to_source` as those roles read now; if it is common,
    that is a gap in the roles to settle for every type, not a gas plant special case.
    **Research done (research note §8, Nov 10); the defaults below agreed by Andrew the same day ("all as proposed").** The steam
    electric guidelines (40 CFR 423) cover combined cycle only. Of 108 tower-cooled combined cycle plants in service
    since 2005 (EIA-860, aggregate), 42 discharge to the same water body as the intake, 18 to a sewer, 14 to a different
    water body and 11 nothing (ZLD, ponds, injection); 23 do not say. Proposed: combined cycle on towers or hybrid
    drawing surface water returns `to_source`; on groundwater or a utility's water it follows the place's wastewater
    rule (`to_sewer`), with a stream discharge and no discharge as settings (15, 10 and 10 of 35 such plants), ZLD more
    likely in the arid West; dry combined cycle, simple-cycle turbines, engines and fuel cells send their small process
    flows `to_sewer` [A]. The different-water case is 13% of new tower plants, mostly wells or utility water discharged
    to a local stream, so it is common enough to be the roles gap for every type that this decision anticipated.
    **Settled (Andrew, Nov 10): a new optional return role for every type, `to_stream`**, a permitted direct discharge to
    surface water other than the source, so returned = to_sewer + to_source + to_stream. It is used only where a
    default or a setting chooses it (0010, principle 1). A zero-discharge plant evaporates its blowdown, which then
    counts as consumed.
11. **Construction water is a one-time total**, reported apart from annual water; upstream fuel water is not added.
    Agreed: construction is always separate.

## Land, runoff and construction for renewables (from decision 2's note; research in the research note §9)

- **Solar.** An array changes how its site sheds water: panel drip lines concentrate rain, access roads, inverter and
  substation pads are impervious, grading compacts soil, and the ground cover under the panels changes. The site's
  runoff, sediment and nutrients go through the shared `waterledger_models.runoff`, as for any developed site, with
  PV-specific land cover and imperviousness from the literature [A]. Construction disturbs the whole fenced area for a
  season: construction stormwater and sediment, and dust control water (the research note's one-time totals).
- **Wind.** The smallest footprint per MWh: turbine pads, crane paths and access roads, and the collection system.
  Construction water is mostly foundation concrete. The runoff change is small and local to the roads and pads.
- **Sourced (research note §9, Nov 10).** Reported per project as land, a change in annual runoff and sediment, and
  one-time construction water, all apart from annual operating water. **Defaults agreed by Andrew, Nov 10 ("all as proposed")**
  (ranges and sources in §9d):
  - PV array area 5.5 acres/MWac tracking and 3.6 fixed (LBNL's 2019 medians at an inverter loading ratio of 1.3 [A]);
    fenced area the array ÷ 0.7 [A]; roads, pads and substation 4% of the fenced area [A].
  - PV runoff: the array area at an effective impervious share of 0.10 with rows along the contours, 0.20 diagonal,
    0.45 across them on vegetated ground, 0.60 on gravel (Mile High Flood District, 2023), plus roads and pads as
    impervious; pervious cover CN 69 on soil group B (open space, fair, for compaction) or one soil group up for the
    Simple Method [A]; all through `runoff.loads` and `runoff.storm_mg` as for any site.
  - Wind: total area 34.5 ha/MW, permanent direct area 0.3 ha/MW counted impervious, temporary 0.7 ha/MW for
    construction (NREL 2009); runoff change only on the permanent area.
  - Construction: PV disturbs the fenced area (Maryland's rule) with 0.6 of it bare for a year [A], sediment by the
    existing `runoff.construction` yields; dust control water 0.5 AF/MW [A] with the desert's 5.7 as the high end;
    wind foundation concrete 700 m³ per turbine [A] (386-1,334 sourced), about 30,000 gal of mix water [A].
  - Not sourced: measured runoff or sediment from solar sites, the road and pad share, wind land for projects since
    2009, humid-climate dust water, and Michigan solar stormwater guidance.

## References

- Davidson, M. R., and Millstein, D. (2022). Limitations of reanalysis data for wind power applications. Wind Energy
  25(9):1646-1653.
- Diehl, T. H., and Harris, M. A. (2014). USGS SIR 2014-5184. Harris, M. A., and Diehl, T. H. (2019). USGS SIR 2019-5103.
- Dobos, A. P. (2014). PVWatts Version 5 Manual. NREL/TP-6A20-62641.
- IEA (2026). Key Questions on Energy and AI.
- Macknick, J., et al. (2011). NREL/TP-6A20-50900; (2012) Environ. Res. Lett. 7:045802.
- Maulbetsch, J. S., and DiFilippo, M. N. (2018). Evaluating Cost, Performance and Water Conserving Capability of Hybrid
  Cooling. CEC-500-2018-015.
- Meldrum, J., et al. (2013). Life cycle water use for electricity generation. Environ. Res. Lett. 8:015031.
- Meng, M., and Sanders, K. T. (2019). Applied Energy 253:113486.
- NETL (2022). Cost and Performance Baseline for Fossil Energy Plants, Vol. 1, Rev. 4a. DOE/NETL-2023/4320.
- Sathaye, J., et al. (2011). Estimating Risk to California Energy Infrastructure from Projected Climate Change. LBNL.
- U.S. EIA: AEO2023 cost and performance characteristics, Table 1; Electric Power Monthly Table 6.07.B; Forms EIA-860,
  EIA-923 and EIA-930.
- U.S. EPA (2000). AP-42 §3.1, Stationary Gas Turbines. U.S. EPA (2017). Catalog of CHP Technologies.
- Uptime Institute, Tier Standard: Topology (as presented by Traver, 2020).
