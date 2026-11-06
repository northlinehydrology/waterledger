# 0006: Water limits, dry mode and return loads on the cooling component

Status: **decided Nov 4, 2026; built Nov 5, 2026 on branch `water-limits`, for the release after 3.10.0; not released.** With no
limit set nothing changes: every output of the cooling model and its BMI component is 3.10.0's to the bit. What was built, and where it
departs from the proposal below, is under *As built*.

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

**Release (Andrew, Nov 4, 2026, in the SWAT+ session).** 3.10.0 ships as it is; this comes in the release after, as one
change: the limit, dry mode, and intake concentrations with return loads. With no limit set, the cooling model gives exactly
3.10.0's numbers, held by a test. The return temperature (blowdown) assumption is decided on its own, as a method decision,
so the proposal below is for that decision.

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
  - the mass taken in is intake concentration x withdrawal, and it leaves only as liquid, in blowdown and drift;
  - return load = intake concentration x withdrawal x (1 - drift's share), in kg s-1, where drift's share is
    drift / (blowdown + drift): a few percent for towers, not the 0.1% this note first said (see *As built*);
  - blowdown concentration = intake concentration x cycles of concentration;
  - drift leaves as liquid at the blowdown concentration, and its mass is reported as a separate output, since it doesn't
    reach the sewer;
  - condensate carries none, so the return column (blowdown plus condensate) is not the basis for loads.
- **Results already published need no rerun for loads.** The return load is a constant multiple of withdrawal, so the
  stored percentiles of withdrawn carry over exactly. The blowdown concentration is a range from the cycles' range.
  (A note from the SWAT+ BMI session, Nov 4.)
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

## Reruns

- **None for the limit or dry mode.** Both are off by default. The identity check (no limit set: rerun a few cells and
  every stored value matches) proves it.
- **None for return loads** (above).
- **Return temperature depends on its basis.**
  - A fixed basis, such as the tower's cold water at the design wet-bulb plus approach, needs no rerun.
  - A temperature that follows the weather hour by hour needs new runs or new stored outputs, since the runs keep
    percentiles, not the draws.
  - That choice goes to Andrew with the method decision.

## Open

- **The capacity margin** and its range [A].
- **Whether a limit applies to the hour's mean flow or the step's.** The BMI step is the framework's.
- **Whether a towers plant with a cap should be allowed to shed load** (the realistic answer), or report it only. The
  proposal reports it.

## As built (Nov 5, 2026)

In `waterledger_models.datacenter.physics` (`hourly_limited`, `dissolved_mass_split`, `blowdown_temperature`) and `CoolingWaterBmi`.
Tests: `tests/test_water_limits.py` (physics) and the design 0006 section of `tests/test_bmi.py`.

- **Drift's share of the dissolved mass is a few percent, not 0.1%.** Drift is 0.005-0.02% of the water *circulating* through the
  tower, but blowdown is small beside that flow: drift's share of the liquid leaving is drift x circulation x (cycles - 1) /
  evaporation, about 1-16% across the ranges and 3-6% at the central values. The return load is still intake concentration x
  withdrawal x (1 - drift's share); the share is larger than first written. Basin Ledger's requests.md carried the same 0.1% and is
  corrected with this.
- **Hybrid:** the limit scales the wet mode's share of the heat (`wet_frac`), and the hour's heat balance is solved again at that
  share: the dry coolers take the rest, and air-cooled chillers above the loop's limit, as the model already does in dry hours.
- **Assist:** the pads' evaporation is cut in proportion and the air reaches the coil that much warmer. (Scaling only the pads'
  cooling would not cut the water: above the switch point plus the coil's rise the model evaporates the whole heat at any
  depression.)
- **Finding the share:** a fixed point on withdrawal, which is close to proportional to the wet duty; 12 iterations meet the limit to
  better than 1e-9 in the tests.
- **Towers:** a towers plant has no dry side and its chillers reject through the towers, so chillers can't help: the load the limit
  can't cool is shed, and reported as heat not removed. The proposal's "straight to chillers" is out for that reason.
- **Capacity [A]:** the dry coolers and chillers are sized for every computer at capacity (the hour's heat per IT kW over the run's
  utilization), all dry, at the location's design dry-bulb, times 1 + `dry_capacity_margin` (0-20%, central 10%). Above the design
  dry-bulb they lose `dry_derate_per_k` of it per K (1-2%, central 1.5%), a straight-line derating in place of the proposal's coil
  approach scaling. At these values a hybrid or assist plant in dry mode rarely sheds load: it has the dry capacity of a dry
  design, by construction. Neither is sampled in the Monte Carlo.
- **Shedding** scales the hour's cooling water (evaporation, drift, blowdown) and power by the share cooled. Loop top-ups,
  humidifiers and condensate don't follow the load in the hour and stay.
- **Dry mode** is a cooling limit of zero (`water_user__dry_mode_flag`). A hybrid or assist plant in dry mode draws the dry design's
  electricity, hour by hour, which the tests hold.
- **Dissolved mass:** blowdown carries the cooling makeup's mass to the sewer and drift to the air; top-ups (leaks), humidifiers and
  pads without bleed leave theirs behind. Staff water's mass splits as its water does, the returned share to the sewer [A]. The BMI
  reports the return's mass and the rest (`water_user_unreturned_water_<name>__mass_flux`), which add to the intake's every step.
- **Return temperature:** built hour by hour in the BMI, where it costs nothing: blowdown at the wet-bulb plus `tower_approach`,
  pad bleed at the wet-bulb, condensate at the 15 C indoor dew point limit, staff water at 20 C [A], mixed by flow. Nothing on the
  site or in a snapshot carries a return temperature, so no rerun is needed; publishing one is the open method decision.
- **Names:** `data_center__setpoint_lost_time` (hours, summed since initialize) for the proposal's `..._lost_hours`; the water-user
  names are aliases (Basin Ledger request 5), condensate as the gain.
- **Not built here:** the limit in the per-run builders (`cooling.py`) and the ensemble. A limit is a scenario for a coupled run;
  Water Ledger's estimates don't use one.

## Decisions (Andrew, Nov 6, 2026)

- **Dry capacity: kept as built** [A], said plainly: real hybrid and assist plants may carry less dry capacity than this, so
  they may shed heat sooner under a limit than the model says.
  - **Makers' tables, read before release.** Air-cooled chillers lose about 1.2-1.4% of capacity per K above their rating:
    Parker's GSFE table gives 0.95 at 30 C and 0.77 at 45 C, and a Titan process chiller 0.93 at 100 F and 0.83 at 113 F.
    That falls within `dry_derate_per_k`'s 1-2%.
  - **Dry coolers derate faster.** Their capacity goes with the initial temperature difference, the fluid in less the air in,
    so with a 10-15 K difference each K of warmer air takes about 7-10% (Liebert's drycooler selection guide sizes by
    load / ITD). The 1-2% range holds where chillers carry what the dry coolers can't. Where dry coolers carry nearly the
    whole dry side, the loss above the design dry-bulb is faster, and shedding in dry mode starts within a few K of it, not
    near 55 C. Those hours are rare, since the design dry-bulb is the 0.4% hour, and the range stays until a coupled study
    needs more.
- **Return temperature: not on waterledger.org.** It stays in the BMI, for the coupled studies; the Clam is the first that
  may use it.
- **Towers under a limit: they shed load and report it, as built.** A towers plant has no dry side to give the duty to.

Sources: Parker Hiross GSFE catalogue, ambient correction factors (divapps.parker.com/divapps/PFGE/GSFE/Catalogue/105/); Titan
IPC-0946 process chiller ambient corrections (catalog.compressedairsystems.com/item/process-chillers/titan-large-capacity-industrial-process-chillers/ipc-0946);
Liebert drycooler selection, 60 Hz (fitness.manualsonline.com/manuals/mfg/liebert/60_hz.html?p=7).
