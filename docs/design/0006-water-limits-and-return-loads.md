# 0006: Water limits, dry mode and return loads on the cooling component

Status: **decided Nov 4, 2026, to build after v3.10.0 is tagged; not built.** Nothing here changes a model, parameter or
snapshot in 3.10.0 (model 1.8).

Basin Ledger asked for these, so curtailment, drought rules and quality balances can drive the data center component
(`~/repos/basin-ledger/docs/requests.md`, items 2-4, Nov 4):
- a withdrawal limit input on `CoolingWaterBmi`;
- a dry mode;
- intake concentrations in, with return loads and return temperature out.

## Decision (Andrew, Nov 4, 2026)

> the withdrawal limit should follow realistic operation as much as possible, same with dry mode and return loads ... the
> data center has to be at a certain temperature, like enough heat has to be removed. So considering something like that we
> should be able to operate the usage caps on the things that keep it cool.

1. **The heat to be removed is fixed.** It is set by the IT load, the power losses and the setpoint (the hour's heat from
   `physics.hourly_heat_power`). A cap never lowers it.
2. **A cap limits the evaporative duty:** the towers, the adiabatic pads, and the hybrid's wet mode.
3. **The heat taken off the wet side moves** first to dry rejection, then to chillers, at the electricity those take that
   hour.
4. **Dry and chiller capacity is finite.** It is a design input [A], sized from the design dry-bulb.
5. **Heat beyond that capacity in an hour is reported as heat not removed.** It is the IT load that would have to be shed,
   or the hours the setpoint is lost, and is never dropped silently.
6. **Dry mode is a cap of zero,** under the same capacity limit. Hot hours with no water may show unmet heat; that is the
   realistic result, and it is flagged.
7. **Return loads come from a mass balance** with the cycles of concentration: blowdown carries the intake's
   concentration times the cycles, and evaporation removes no dissolved solids.
8. **Energy and water close every hour,** and tests hold them to it.

## Design (proposed)

### Inputs

| Name | Units | Meaning |
|---|---|---|
| `water_user_water__withdrawal_volume_flux_limit` | m3 s-1 | the most the campus may withdraw this step; infinity (the default) is no limit, 0 is dry mode |
| `water_user_intake_water_<name>__mass_concentration` | kg m-3 | dissolved solids, chloride, phosphorus in what is taken in (default 0) |

The data center names (`data_center_cooling_water__*`) stay; the common water-user names (Basin Ledger request 5) are added
as aliases.

### Each hour, with a limit

1. Solve the hour as now (`hourly_heat_power`, `hourly_rates`), giving withdrawal W and its wet share w of the heat.
2. **If W is within the limit,** nothing changes: the results are model 1.8's, to the bit.
3. **If W exceeds the limit L,** find the wet share w' at most w at which withdrawal equals L. Withdrawal is linear in the
   evaporated heat at fixed weather, so this is one division and needs no search, apart from top-ups and humidifier water,
   which don't depend on w and come off L first.
   - **Towers and hybrid:** the evaporated share of the heat falls from w to w'.
   - **Assist:** the pads' evaporation is capped the same way, the air reaching the coil warmer.
4. **The heat taken off the wet side, (w - w') x heat,** goes to the dry coolers, up to their capacity at the hour's dry-bulb.
   Their capacity is the design heat at the design dry-bulb, scaled by the coil's approach to the air: a dry coil rejects
   less as the air warms toward the loop's return.
5. **What the dry coolers can't take goes to chillers,** air-cooled, up to their capacity, at the hour's COP
   (`_loop`'s air-cooled COP). Their power is heat that is rejected too, so it is added to the dry side's load and the
   hour is solved again.
6. **Heat still left is heat not removed,** in MW: the output `data_center__unremoved_heat_power`. The electricity counts
   only the heat actually removed; the unremoved heat is reported beside it, and isn't added to anything.
7. **Hours with unremoved heat** are counted in `data_center__setpoint_lost_hours` (cumulative).

**Capacity [A].**
- The dry coolers and chillers of a design are sized to carry the full heat at the design dry-bulb: 0.4%, plus a margin
  that is a parameter, `dry_capacity_margin`, with range 0 to 20% [A].
- A towers design has no dry coolers, so its dry capacity is 0 unless configured. A limit there goes straight to chillers
  or to unmet heat.
- This is the realistic case: a tower plant has no dry cooling to fall back on.

**Dry mode** is a limit of 0 for the cooling water. Top-ups and staff water still count; they are not cooling duty.

### Return loads and return temperature

- **Mass.** For each constituent, the mass in equals the mass out, every hour, and none leaves with evaporation:
  - return load = intake concentration x (withdrawal - evaporation), in kg s-1;
  - blowdown concentration = intake concentration x cycles of concentration;
  - drift leaves as liquid at the blowdown concentration, and its mass is reported as a separate output, since it doesn't
    reach the sewer;
  - condensate carries none.
- **Temperature (proposed method).** Blowdown leaves at the tower's cold-water temperature, wet-bulb plus the approach
  (`tower_approach`). Pad bleed from assist leaves at the sump's temperature, about the wet-bulb. Condensate leaves at the
  coil's leaving-air dew point.
  - The return temperature is these flows' mixed temperature, weighted by flow.
  - Staff and maintenance water leave at a fixed [A] 20 C.
  - A closed loop's return is staff water only.

## Short note for the methods pages (proposed, for when it ships)

> **Water limits.** When a rule caps a campus's water, the heat its computers make still has to go: the cap moves cooling
> from evaporation to dry coolers and chillers, which use more electricity. Where the dry equipment can't carry the heat on
> a hot hour, the model reports the heat not removed and the hours the campus couldn't hold its temperature, rather than
> hiding them. What goes back to the sewer carries the minerals the campus took in, concentrated by evaporation, at about
> the temperature of the tower's cooled water.

## Long note (proposed, for the methods log when it is built)

- **The return temperature, cited.** The cold water leaving a cooling tower approaches the inlet air's wet-bulb, and the
  approach is a design choice: the model's `tower_approach` is 2.8-6.7 K, from Lei and Masanet's Table 3. Blowdown is
  drawn from the cold-water basin, so it leaves at that temperature. The towers and evaporative chapters of the ASHRAE
  Handbook (HVAC Systems and Equipment) and Kröger (2004) are to be checked when this is built, and cited by page.
- **Sump and condensate.** An evaporative pad's sump water runs near the wet-bulb, and coil condensate leaves near the
  coil's leaving-air dew point.
- **Mass by construction.** Dissolved solids, chloride and phosphorus are conserved through evaporation, which takes only
  water. So blowdown carries the intake's mass at the cycles' concentration (Lei and Masanet Eq. 7; DOE FEMP BMP #10), and
  the return load is mass balance by construction.

## Tests (to build with it)

- **No change below the limit.** With an infinite limit, every output is identical to 3.10.0's, to the bit.
- **Water closes** under any limit: withdrawal + condensate = consumption + return.
- **Energy closes:** facility power + outside air's heat = heat removed + fan heat, and heat removed + heat not removed =
  the heat to be removed.
- **Mass closes** for every constituent: intake mass = return mass + drift mass, none in evaporation.
- **The cap is met:** withdrawal is at most the limit in every hour, top-ups and staff water aside.
- **Electricity follows:** it rises monotonically as the limit tightens, at fixed weather.
- **Dry mode on a hot record** shows unremoved heat only above the dry and chiller capacity, and none in cool hours.

## Open

- **The capacity margin** and its range [A].
- **Whether a limit applies to the hour's mean flow or the step's.** The BMI step is the framework's.
- **Whether a towers plant with a cap should be allowed to shed load** (the realistic answer), or report it only. The
  proposal reports it.
