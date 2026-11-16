# 0019: Fuel cells as data centers use them (solid oxide on natural gas)

Status: **decided Nov 16, 2026 (Andrew; all five decisions, below); nothing built.** Branch `supply-on-aorc`, beside 0018 (solar and wind on a
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
| By age, the same plants over three years | 73 plants of 1-5 MW, not CHP, over 50% capacity factor in each of 2022, 2023 and 2024; fleet 7,279 / 7,318 / 7,247. By the year they came online, fleet heat rate 2022/2023/2024: 2021, 6,685 / 6,633 / 7,010 (6 plants, 1-3 years old); 2020, 6,822 / 7,188 / 6,947 (7); 2019, 7,157 / 7,122 / 7,050 (14); 2018, 7,393 / 7,294 / 7,296 (13); 2016-2017, 7,442 / 7,268 / 7,359 (21). A plant's own change 2022 to 2024: median -0.9%, p10-p90 -7.6% to +5.6%; 70 of the 73 heat rates are distinct | EIA-923 2022-2024, EIA-860 2024, computed for this note | independent, aggregate |
| Power modules | stacks combined into 50 kW power modules; a server is power modules, a fuel processor and an AC module | Bloom Energy, Form S-1 (2018) | vendor, filed |
| Availability | "native redundancy"; 99.9% to 99.999% claimed, "up to" Tier IV as primary power | Bloom data center pages | vendor; no independent figure found |
| Water, normal operation | "None during normal operation" | datasheet | vendor |
| Water, start-up and restarts | a Water Distribution Module "to supply water to the [power modules] during start-up" (brochure 2024); about 780 gal a year per 10 MW for restarts after service (Bloom blog, 2026); 0.69 gal/MWh (the same 2023 state filing) | Bloom | vendor; the two differ about 75-fold |
| Part load | "load fluctuation has minimal impact on the efficiency"; 40% to 100% load almost at once ("Be Flexible", Feb 2024) | Bloom | vendor; no independent figure found |
| Temperature | operates -20 to 45 C; no derate given | datasheet | vendor |
| Fuel and CO2 in filings | 4,100 MMBtu/day for 24.3 MW (7,030 Btu/kWh); 679-833 lb CO2e/MWh, which is the datasheet's heat rate range at 116.9 lb CO2/MMBtu | the 2023 state filing | the vendor's figures, filed |

Readings:

- **The measured fleet sits at the top of the datasheet's range.** EIA's median plant (7,109) is at the datasheet's
  end-of-life figure (7,127); the fleet's average over stack ages is about 7,300-7,500. A stack aging linearly from 5,811
  to 7,127 over five years would average about 6,470. EIA names no manufacturer, so "1-5 MW, not CHP" stands in for
  solid oxide [A]; the larger plants include molten carbonate units, which run at about 7,800.
- **Aging shows in the field, but not as the datasheet's curve.** Plants one to three years old run about 6,650-7,000,
  plants six to eight years old about 7,250-7,400; none is near the new-stack 5,811. Within a plant, heat rates move both
  ways from year to year, as modules are swapped. The cohorts are also product generations, so age and model are mixed.
  The heat rates are the plants' own (70 of 73 distinct), not one vendor default.
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

**`fuel_cell` becomes the solid oxide plant on gas** (decision 1), design `dry`; the CHP Catalog's mixed range goes. Everything else in `gas.physics` applies as it is: no
condenser, its heat in the exhaust ("other"), and the energy balance fuel = net + auxiliary + other closing every hour.

| Parameter | `sofc` | Set from |
|---|---|---|
| Heat rate, HHV | 6,600-7,500 Btu/kWh, sampled | EIA's plants by age, 2022-2024: about 6,650 at one to three years to 7,400 at six to eight; each draw is a plant at some point in its life [A]. The datasheet's new-stack 5,811 is outside it |
| Aging | in the draws, and `age_years` an optional setting; never state (decision 2) | a run's decades of weather are samples of the climate, not a plant's years |
| Derate, heat-rate slope | 0 | datasheet: -20 to 45 C, no derate given [A] |
| Part-load penalty at half load | 0-0.05, as `fuel_cell` | vendor claim of little change; no independent figure [A] |
| Auxiliary share | 0.01-0.03, as `fuel_cell` | the datasheet's output is already net AC [A] |
| Availability | 0.90-0.97, shared | [A], as every technology |
| Process water | 0.01-0.69 gal/MWh, sampled, withdrawn and consumed | Bloom's two figures (restarts, about 780 gal/yr per 10 MW; the state filing's 0.69). Consumed, not drained: start-up water is raised to steam for the reformer until the anode's own product water takes over, and leaves reacted or as vapor in the exhaust; the water is deionized in exchange tanks swapped at service (the state filing), so there is no reject on site |
| Unit | the 325 kW Energy Server | the product's unit (datasheet); outages drawn per server (about 0.5 s a draw for 1,000 servers over 24 years) |
| Outage length | 24 hours mean [A] | modules are swapped with the server running (S-1; the state filing); shorter than a turbine's 48 [A] |

- **Water balance:** the new process water joins the existing terms; withdrawn = consumed + returned still closes, with
  nothing returned from it.
- **Sizing (decision 5, "realistic implementations"):** modular plants carry a reserve share, not a spare unit. N servers
  carry the campus's 1-in-10-year highest hour (as now); the plant gets the fewest more servers M such that, with each up
  at the central availability, the chance that fewer than N are up in an hour is under 1 in 10,000 (binomial) [A: about
  four nines, inside the vendor's claims]. At 920 servers and 0.935 availability that is 1,017 servers, a reserve
  of 10.5% (5.5% at 0.97, 15.7% at 0.90). The other technologies keep N + k.
- **BMI:** `GasPlantBmi` takes `technology="sofc"` with nothing else changed.

## Checks

- **F1, EIA-923 in aggregate** (`docs/methods/power_supply/fuel_cell_check.py`): the computation above as a script,
  writing only aggregates over five or more plants (by size, CHP, online cohort and state), against the `sofc` range.
- **F2, balances:** energy and water every hour, every draw, in `tests/test_gas.py`, as for the other technologies; the
  shared conformance test.
- **F3, against the datasheet:** at central parameters, fuel per MWh within the datasheet's 5,811-7,127 range or above it,
  never below.

## Version

`fuel_cell` becomes the solid oxide plant (decision 1), so its numbers change: a model version step (1.17 if 3.24.0 is
model 1.16), and `MODELS` records it. No study has run `fuel_cell` yet.

## Decisions (Andrew, Nov 16, 2026)

1. **`fuel_cell`'s range is replaced by solid oxide's** ("it's early, we can change fuel cells' range"), not a new
   technology.
2. **Aging:** open; Andrew asked how hard it is. Coding a heat rate that climbs between stack swaps is half a day with
   tests. What it would mean is the harder part: a run's 23-30 years of weather are samples of the climate, not a plant's
   years, so aging along the run would tie stack age to particular weather years. Proposed: the age in the draws (the
   range above, from EIA's plants by age), and, if wanted, an `age_years` setting that picks the part of the range for a
   plant of that age (1-3 years: 6,600-7,000; 6-8: 7,200-7,500) [A].
   **Settled (Andrew, Nov 16): no state.** Asked whether `age_years` would be state the model holds: no, a setting read
   once, as `technology` or `units` are; aging along the run would be (hours since the last swap, carried step to step
   and through a restart). Andrew: that is "from a model and code perspective the most important change", so the model
   stays a function of the hour's inputs and fixed settings. Built: the age in the draws (6,600-7,500) and `age_years`
   as an optional setting.
3. **Start-up water is consumed**, as it is: evaporated or reacted, not drained (Andrew: "whichever it is"). Above.
4. **Air permits stay in the study's notes, not in the package.** Agreed.
5. **The unit and reserve as real plants are built** ("should reflect realistic implementations"): the 325 kW server,
   outages per server, and a reserve share from the servers' availability, above.

## References

- Bloom Energy (2026). The Bloom Energy Server 6.5, data sheet (Feb 2026). Bloom Energy (2024). Energy Server brochure.
  Bloom Energy (2024). Bloom Energy introduces load following capability (Feb 12, 2024). Bloom Energy (2026). Communities
  are right to ask about the water use of AI infrastructure (blog).
- Earthjustice (2026). The AI Gas Rush (Oct 2026).
- U.S. EIA: Forms EIA-860 and EIA-923, 2024 (aggregate only).
- U.S. EPA (2017). Catalog of CHP Technologies, section 6.
