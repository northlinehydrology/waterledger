# 0019: Fuel cells as data centers use them (solid oxide on natural gas)

Status: **proposed Nov 16, 2026, for Andrew; nothing built.** Branch `supply-on-aorc`, beside 0018 (solar and wind on a
study's forcing). Andrew (Nov 16, relayed by the Clam River session): "we should add fuel cells to the power types work
with solar and wind." It does not depend on 0018: a fuel cell barely answers to the weather.

## Why

The Clam River study will add solar, wind and fuel cells together. Fuel cells are 6% of the gas capacity disclosed in
"bring your own power" proposals (Earthjustice, Oct 2026), used mostly as bridge power while the grid connection is built.
The units data centers buy are solid oxide fuel cells on pipeline gas, nearly all from one manufacturer (Bloom Energy).

Today `gas.physics` has `fuel_cell`, design `dry`, from the EPA CHP Catalog (2017): heat rate 6,300-9,950 Btu/kWh HHV,
which mixes phosphoric acid, molten carbonate and solid oxide units of 0.7-1,400 kW, no derate, a 0-5% part-load
penalty at half load, and no water ("product water is recovered; water at start-up is not quantified", 0014). That range
is too wide and centred too high for a solid oxide plant, and the water is left at zero.

## What the sources say

| Item | Figure | Source | Kind |
|---|---|---|---|
| Heat rate | 5,811-7,127 Btu/kWh HHV; "cumulative electrical efficiency 65-53% (LHV net AC)" | Bloom Energy Server 6.5 datasheet (Feb 2026), 325 kW per server | vendor |
| What the range is | stack life: 65% new, 53% before the stacks are replaced [A: the datasheet doesn't say so; 5,811 and 7,127 HHV are 65% and 53% LHV at an LHV/HHV of 0.90] | as above | reading |
| Stack replacement | "approximately every five years" | a 2023 state air filing for a 24.3 MW data center installation (the manufacturer's records, as filed) | vendor, filed |
| Measured heat rate | 2024 EIA-923 over EIA-860's gas fuel cell plants (prime mover FC, NG), in aggregate: 98 plants not CHP and over 50% capacity factor, 264 MW, fleet 7,496 Btu/kWh; median plant 7,109, middle half 6,937-7,295; the 84 plants of 1-5 MW 7,290 | computed for this note | independent, aggregate |
| By age | fleet 7,782 (online by 2015, 19 plants), 7,274 (2016-2020, 64), 7,430 (2021-2023, 14) | the same | aggregate |
| Water, normal operation | "None during normal operation" | datasheet | vendor |
| Water, start-up and restarts | a Water Distribution Module "to supply water to the [power modules] during start-up" (brochure 2024); about 780 gal a year per 10 MW for restarts after service (Bloom blog, 2026); 0.69 gal/MWh (the same 2023 state filing) | Bloom | vendor; the two differ about 75-fold |
| Part load | "load fluctuation has minimal impact on the efficiency"; 40% to 100% load almost at once ("Be Flexible", Feb 2024) | Bloom | vendor; no independent figure found |
| Temperature | operates -20 to 45 C; no derate given | datasheet | vendor |
| Fuel and CO2 in filings | 4,100 MMBtu/day for 24.3 MW (7,030 Btu/kWh); 679-833 lb CO2e/MWh, which is the datasheet's heat rate range at 116.9 lb CO2/MMBtu | the 2023 state filing | the vendor's figures, filed |

Readings:

- **The measured fleet sits at the top of the datasheet's range.** EIA's median plant (7,109) is at the datasheet's
  end-of-life figure (7,127); the fleet's average over stack ages is about 7,300-7,500. A stack aging linearly from 5,811
  to 7,127 over five years would average about 6,470. Either the fleet runs nearer end of life than linear aging gives,
  or reported fuel is not metered apart from the vendor's own numbers (the middle half of plants is unusually tight). EIA
  names no manufacturer, so "1-5 MW, not CHP" stands in for solid oxide [A]; the larger plants include molten carbonate
  units, which run at about 7,800.
- **Air filings are not an independent check on fuel.** The one read here gives the datasheet's own figures: its heat input
  is the end-of-life heat rate and its CO2 range is the datasheet's range times the fuel's carbon. A permit is sized to
  the worst case, not measured. The independent figure is EIA-923.
- **Water is small either way.** At the higher vendor figure, 0.69 gal/MWh, a 300 MW plant at full output uses about
  5,000 gal a day, against roughly 150-300 gal/MWh for a combined cycle on towers.

## The scope rule and the air permits

Andrew suggested air permits as an independent check (a utility's fuel cells for two data center operators in central Ohio,
and Project Jupiter in New Mexico, refiled as a minor source after a switch from turbines to fuel cells). Design 0014's
scope rule (1 and 2) keeps any real plant out of the packages: no plant named or profiled, reported data only in
aggregate over five or more plants. A permit is one project's data, so its figures can't be cited by project in the
package, and they repeat the vendor's anyway (above). Proposed: the package cites the datasheet (a product, as the research
note's S6 already does) and the EIA-923 aggregate; permits stay in the study's own notes, where the projects are already
named (decision 4).

## Proposed model

A new technology, **`sofc`**, design `dry`, beside the existing ones. `fuel_cell` keeps its CHP Catalog range and its
numbers, for any fuel cell; `sofc` is the data center case. Everything else in `gas.physics` applies as it is: no
condenser, its heat in the exhaust ("other"), and the energy balance fuel = net + auxiliary + other closing every hour.

| Parameter | `sofc` | Set from |
|---|---|---|
| Heat rate, HHV | 6,500-7,500 Btu/kWh, sampled | from the datasheet's life average under linear aging (about 6,470) to EIA's 2024 fleet (7,290-7,496); the datasheet's new-stack 5,811 is outside it [A] |
| Aging | none hour by hour; the heat rate range is a life average [A] | a run is decades of weather for a plant of one age; stacks are replaced about every five years |
| Derate, heat-rate slope | 0 | datasheet: -20 to 45 C, no derate given [A] |
| Part-load penalty at half load | 0-0.05, as `fuel_cell` | vendor claim of little change; no independent figure [A] |
| Auxiliary share | 0.01-0.03, as `fuel_cell` | the datasheet's output is already net AC [A] |
| Availability | 0.90-0.97, shared | [A], as every technology |
| Process water | 0.01-0.69 gal/MWh, sampled, withdrawn and consumed (to the reformer and the exhaust) | Bloom's two figures (restarts, about 780 gal/yr per 10 MW; the state filing's 0.69) [A: consumed, none returned] |
| Unit | a block of servers, default 10 MW [A], for outages and N + k | 325 kW servers; a 300 MW plant would be about 920, and N + 1 on that many is no reserve |

- **Water balance:** the new process water joins the existing terms; withdrawn = consumed + returned still closes, with
  nothing returned from it.
- **Sizing:** N + k as for the other technologies, in blocks [A]; for an islanded campus that is a reserve of about 3-7%
  at 150-300 MW, with k a setting.
- **BMI:** `GasPlantBmi` takes `technology="sofc"` with nothing else changed.

## Checks

- **F1, EIA-923 in aggregate** (`docs/methods/power_supply/fuel_cell_check.py`): the computation above as a script,
  writing only aggregates over five or more plants (by size, CHP, online cohort and state), against the `sofc` range.
- **F2, balances:** energy and water every hour, every draw, in `tests/test_gas.py`, as for the other technologies; the
  shared conformance test.
- **F3, against the datasheet:** at central parameters, fuel per MWh within the datasheet's 5,811-7,127 range or above it,
  never below.

## Version

A new technology changes no existing number (`fuel_cell` keeps its range); public API in the release that carries it,
with 0018.

## Decisions for Andrew

1. **A new technology `sofc`**, keeping `fuel_cell` as it is (proposed), or replace `fuel_cell`'s range with solid oxide's
   (changes its numbers; a model version step).
2. **Heat rate 6,500-7,500 Btu/kWh HHV**, the stack-life average to EIA's measured fleet, with no aging hour by hour
   (proposed); or the datasheet's full 5,811-7,127; or a stack-age setting.
3. **Process water 0.01-0.69 gal/MWh**, consumed (proposed).
4. **Air permits** stay in the study's notes, not in the package (proposed, per 0014's scope rule); or an aggregate of
   five or more permits, unnamed, as a range.
5. **Blocks of 10 MW** as the unit for outages and N + k (proposed).

## References

- Bloom Energy (2026). The Bloom Energy Server 6.5, data sheet (Feb 2026). Bloom Energy (2024). Energy Server brochure.
  Bloom Energy (2024). Bloom Energy introduces load following capability (Feb 12, 2024). Bloom Energy (2026). Communities
  are right to ask about the water use of AI infrastructure (blog).
- Earthjustice (2026). The AI Gas Rush (Oct 2026).
- U.S. EIA: Forms EIA-860 and EIA-923, 2024 (aggregate only).
- U.S. EPA (2017). Catalog of CHP Technologies, section 6.
