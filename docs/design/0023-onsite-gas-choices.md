# 0023: On-site gas as a choice of plant and cooling, its shortfall, and its air emissions

Status: **proposed Nov 20, 2026; nothing built.** Andrew (Nov 20, after seeing a 1,500 MW off-grid gas campus estimated at about
the campus's own water): make the plant a choice ("engines" or "combined cycle"), with cooling options "in the same vein" as the
campus's; show the power shortfall to expect when the plant is too big for its units; and show something about air emissions,
"so fuel [cells] don't look like a magic solution, even if they are operationally better." Builds on 0014 (supply scenarios),
0019 (fuel cells) and 0020 proposal 2 (stored runs for every design).

## Why

waterledger.org's on-site power runs (Northline's `engine/products/onsite_power.py`) fix one plant per grid choice:

| Choice | Plant | Cooling | Unit | Water, 1,500 MW campus (Ohio, dry with pads) |
|---|---|---|---|---|
| Gas, connected | `cc` | `towers` | 150 MW | about 4.7 million gal/day evaporated |
| Gas, off grid | `engine` | `dry` (radiators) | 18 MW | about zero |

The difference a reader sees between "connected" and "off grid" is the plant, not the grid. Both pairs are defensible on their
own: islanded gas built so far at data centers has mostly been engines or simple-cycle turbines, often as bridge power, and
neither evaporates cooling water. But a campus that runs off grid on gas for decades at a gigawatt or more has a strong reason
to build combined cycle (roughly 6,200-6,450 Btu/kWh against engines' 8,200-9,900, 0014's table), and combined cycle's water
runs from little (air-cooled condenser) to millions of gallons a day (wet towers). An applicant who hasn't said which plant
they'll build hasn't ruled out the wet one. Today the page shows the engines' near zero and raises no alert; since PR #52 it
adds one line with the combined-cycle figure, information only.

Fuel cells look best of all on the page: almost no water, no grid. That is true of their water, but they burn the same gas.
Nothing on the page says what any on-site plant puts in the air, so a reader can't weigh it.

## Proposal 1: the plant and its cooling are choices

The package already models every piece (0014): `Gas(technology, design, unit_mw)` with `cc` on `towers`, `hybrid`, `dry`,
`assist` and `lake`; `ct` (simple cycle, `none`); `engine` on `dry` (or `towers`); `fuel_cell` on `dry`. What's missing is
the choice on the page and the stored runs behind it.

**The choices, in the campus's own words** (the same names the cooling buttons use, 0022):

| Plant | Cooling | Reads as |
|---|---|---|
| Engines | Radiators (`dry`) | engine generators, many small units |
| Turbines | none | simple-cycle gas turbines, few medium units, exhaust heat to air |
| Combined cycle | Towers, Hybrid, Dry with pads, Dry (air-cooled condenser) | gas turbines plus a steam cycle, few large units |
| Fuel cells | none | as now (0019) |

Each choice works connected or off grid; the grid choice only decides what covers the hours the plant can't (0014's
`residual`: `"grid"` or `"none"`).

**Where it shows.** The simple calculator keeps one Gas button and gains a plant choice (Engines, Turbines, Combined cycle)
that appears when Gas is pressed. Combined cycle's cooling sits in the detailed calculator, starting from towers, as the
loop picker does (Nov 8 decision on loop temperatures). [Decision 2]

**Default.** Two readings:

- a. Keep today's pairs as the starting choice (connected: combined cycle on towers; off grid: engines), now visible and
  changeable.
- b. An unnamed gas plant starts as a range, low end engines, high end combined cycle on towers, with the card's level set
  from the high end, as an undefined "closed loop" starts from pads with dry as its low end (Nov 15). Naming a plant
  replaces the range with that plant.

Proposed: **b** for any gas plant whose plant isn't chosen, because it states what isn't known and keeps the alert where the
water risk is. [Decision 1]

**Runs.** One `est.supply` run per plant and cooling pair, connected and off grid, at each region cell and size already
stored (100, 300 and 1,000 MW): 2 pairs today, 12 with all of the table (engines, turbines, combined cycle on four coolings,
each twice; fuel cells unchanged). Gas runs are about 30 s each at 100 draws, so the gas part of a state's build grows about
sixfold, run locally (compute stays on Andrew's machine). Fewer pairs if Decision 2 leaves some cooling out of the site.
Proposal 2 of 0020 (stored runs for every design) is the long-run home; until then these sit in `onsite_power.json` as today.

## Proposal 2: the shortfall to expect

An islanded plant is sized N + k (0014: N from the 1-in-10-year highest hour over a unit's capacity at the 0.4% design
dry-bulb, k = 1). The runs already report unserved hours and the longest run of them (`unserved_hours_annual`,
`unserved_run_max_hours`). What the page doesn't say is why the number moves with the plant:

- **Unit size.** Losing one unit loses 1/N of the plant. 80 engines of 18 MW lose about 1% each; ten 150 MW combined-cycle
  units lose 10% each, and two out at once (k = 1) is a shortfall. Unit size is a setting with a sourced default per plant
  (0014's `unit_mw`); for combined cycle the default should be read from built blocks, not the 150 MW used today [A].
- **Heat.** Combined cycle and turbines derate in hot weather (0014: ct 0.9-1.0% per K above 15 °C, cc wet 0.3-0.5%, dry about
  0.7%), and the hottest hours are the campus's highest load. A dry-cooled combined cycle derates most on the day it's needed
  most; N is set at the design dry-bulb, so hours above it can come up short.
- **Fuel.** An islanded plant has no backup for its gas. The runs assume the pipeline always delivers. The page should give
  the plant's gas use (MMcf a day, from the run's fuel) and say plainly that pipeline curtailment in a cold snap is not
  modeled. No figure for that risk until a source can be found and cited [A: none found yet].

**What the page shows.** For an off-grid plant: hours a year without enough power (median and the draws' range), the
longest such run, the share of the plant one unit is, and the gas a day. A plant "too big" for its units (one unit over a set
share of the load, proposed 10%) gets a note that a second spare unit (k = 2, already an option) would cut the shortfall,
with the hours both ways. [Decision 3]

**Balance.** Unchanged from 0014: load = served + residual to the grid + unserved, every hour; tested as now.

## Proposal 3: air emissions, from the limits a plant would be permitted to

The aim is one honest line per plant, not an air quality model. Each run already has the plant's fuel (MMBtu); emissions are
fuel times a rate.

**Carbon dioxide.** Fuel × 53.06 kg CO2/MMBtu for pipeline natural gas (EPA, 40 CFR 98 Subpart C, Table C-1) [to confirm the
table value when built]. Per MWh this follows heat rate: combined cycle and solid oxide fuel cells land close together, engines
and simple cycle higher. This is the line that keeps fuel cells from reading as free: same gas, same kind of carbon, at about a
combined-cycle rate.

**NOx, and the permit line.** Two ways:

- a. **The rate a new plant would be permitted to** (federal new source performance standards: NSPS KKKK for combustion
  turbines, JJJJ for spark-ignition engines; fuel cells from their filed rates, 0019's air filing), as a ceiling. No
  modeling of controls, and every number traces to a rule. A best-available-control permit would often be lower, so this is
  an upper bound, said so.
- b. AP-42 factors with stated controls (selective catalytic reduction or not). Closer to a central estimate, but each
  control choice is an [A].

Proposed: **a**, relying on the rules' limits, with the plant's yearly tons compared with the federal major-source lines
(Title V's 100 tons a year; prevention of significant deterioration at 100 or 250 tons depending on the source category) as
context for "this needs a major air permit." Each limit and line is to be read against the rule text when built, as the state
rules were (Nov 20). Fuel cells' NOx is near zero, and the line says so; their carbon line is what shows the trade.
[Decision 4]

**Scope.** Tons a year and the permit lines only. No dispersion, no concentrations at a home, no health figures: that is
air quality modeling, not a calculator line. Under 0010's same-treatment rule, a gas plant as its own water user type gets
the same emissions output.

## What it touches

- waterledger-models: `supply.scenario.Gas` unchanged; an emissions helper on the run's fuel (`gas.physics`), with its
  rates as sourced constants.
- waterledger: `est.supply` reports CO2 and NOx (tons a year, average and peak day) and gas a day; `levels` gains no air
  levels unless Decision 4 adds the major-source line as one.
- Northline: `onsite_power.py` runs the pairs; the calculator's power choice, the drawing's plant (combined cycle already has
  its own drawing; turbines need one), the electricity card's lines; methods page and changelog (a calculation change).

## Checks

- Water: each pair's water against 0014's NETL check (combined cycle on towers) and against EIA-923's reported consumption
  for built plants of each type, in aggregate.
- Shortfall: islanded N+1 and N+2 hours against 0014's overbuild check; a test that a larger unit size never lowers the
  unserved hours at the same N + k.
- Emissions: CO2 per MWh against EIA-923 fleet figures by prime mover; a test that tons = fuel × rate closes.

## Decisions for Andrew

1. Default for an unnamed gas plant: (a) today's pairs, visible; (b) a range, engines to combined cycle on towers, level from
   the high end. Proposed: b.
2. Which choices show on the simple calculator (proposed: Engines, Turbines, Combined cycle) and which coolings for combined
   cycle in the detailed one (proposed: all four).
3. The "too big" share for one unit (proposed 10%) and whether the page offers k = 2 as a button or a note (proposed: a note
   with both figures).
4. Air emissions by permit limits (a, proposed) or AP-42 factors with controls (b); and whether the major-source line is a
   card level or context only (proposed: context only).
5. Whether turbines (simple cycle) join the choices at all, or engines and combined cycle are enough for a first release.
