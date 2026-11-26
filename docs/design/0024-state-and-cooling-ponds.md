# 0024: State on the BMI components, and a cooling pond that keeps it

Status: **built Nov 26, 2026** (PR #42). Andrew agreed on Nov 26 that some models should keep state, on one condition: no existing
estimate changes. Part 1 (state functions) and part 2 (a cooling pond) are built, and part 2's choices are decided (below).

Basin Ledger asked for this (`basinledger/docs/requests.md`, waterledger-models item 6): "State functions (`get_state`/`set_state`, after
CSDMS bmi PR #112), for any user model that keeps state between steps (ponds, tailings), so scenarios can start from a shared warm-up."

## Andrew's condition (Nov 26, 2026)

> I do like the idea of some models having state, we avoided that in the past, but it does make sense for certain use cases. This
> update would not touch any existing estimates would it?

It doesn't. Part 1 adds two methods to `ScalarPointBmi` and changes nothing that steps a model: `update`, `_advance`, `_compute` and
`update_until` are as they were. The pond in part 2 is a new component. It is not a design in the Monte Carlo runs, the stored results,
the snapshots or the site. The evidence is under *Unchanged*.

## Part 1: state functions on every component (built)

CSDMS bmi PR #112 (open, BMI 2.1) adds `get_state(out string)` and `set_state(in string)`. They carry "all information that forms the
state of the model ... as a single string". The format is the modeller's choice; JSON or NetCDF is suggested. The `_ptr` variants in the
proposal aren't built, since a state here is small. swatplus-bmi already has `get_state`/`set_state` under the same names, returning
bytes; Basin Ledger calls both.

`ScalarPointBmi.get_state()` returns JSON holding:
- the clock;
- every input and output value;
- the inputs set since the last update;
- the attributes a component names in `_STATE`: what it carries from step to step beyond its values;
- a fingerprint of its settings.

`set_state(text)` writes these back into the existing arrays, so pointers from `get_value_ptr` stay live.

- **Exact.** Floats are written as `float.hex`, so a state loads to the bit, infinity (the default limit) and NaN included, and the JSON
  stays standard. Arrays in `_STATE` are their bytes, base64.
- **The same component only.** The settings fingerprint is a sha256 over every attribute `initialize` set that stepping doesn't change:
  configuration, parameters, and forcing by its contents, not its file name. `set_state` refuses a state from another class, another
  configuration or other forcing, and any format version but its own (1).
- **Today's components carry almost nothing.** Their steps are computed from the step's inputs, parameters and forcing. Only the clock
  carries, plus one running sum: `CoolingWaterBmi`'s `data_center__setpoint_lost_time`, summed since `initialize`, which lives in the
  values and so is in the state. Their `_STATE` is empty.
- **Use:** initialize a component as the warm-up's was, `set_state` the warm-up's state, and step on. Every scenario then starts from
  the same point without stepping the warm-up again.

Tested in `tests/test_bmi_state.py` on every component (`CoolingWaterBmi` with towers under a binding limit, and hybrid on a forcing file;
`LakeCoolingBmi`, `BatteryCellBmi`, `GasPlantBmi`, `GridWaterBmi`):
- a run saved at step 12, loaded into a fresh component and run to step 30 matches the run that never stopped, every output to the bit;
- inputs set before the save carry;
- the states agree at the end;
- a state is refused for another capacity, design, parameter, time step, component, or forcing file of the same name with other
  weather.

### Unchanged

- The files that step models aren't touched. The diff to `datacenter/bmi.py` is the import and the two methods; `state.py` is new.
- The full test suite passes, the golden estimates (`tests/test_golden.py`) included, and the CSDMS bmi-tester passes on every
  component.
- Every output of every component, over a year of hourly steps on synthetic weather, is the same byte for byte on this branch and on
  `origin/main` (5345cf0). That is 19 cases: each cooling design with and without limits and dry mode, the warm and chilled plants, the
  lake, battery and gas designs, and the grid. The script is `tools/compare_bmi_outputs.py`.

## Part 2: a cooling pond (built)

Andrew (Nov 26) chose a cooling pond as the first model that keeps state: "storage pond would be more common but cooling pond more
applicable ... perhaps our learnings will be applicable to storage pond."

A cooling pond is a built pond or reservoir that a plant circulates: water drawn through the condensers or heat exchangers and returned
warmer, the heat leaving at the pond's surface. Power plants use them (EIA's pond class; North Anna's Lake Anna, on Nov 1's water body
rule, is one). A data center could use one with liquid cooling at warm supply temperatures. Its water use depends on what the pond held
yesterday. That is the case a stateless hour can't give.

### Proposed physics

- **State:** the pond's volume, its temperature (well mixed), and the dissolved mass of each constituent.
- **Heat in:** the plant's heat, all of it into the pond. For a data center it is IT × utilization × heat factor, as for the lake. Any
  user can give `heat_mw`, or set it each step as an input, so a gas plant or another component can drive the pond.
- **Heat out, at the surface,** in a full energy balance:
  - absorbed shortwave;
  - incoming longwave;
  - outgoing longwave at the pond's temperature;
  - evaporation and conduction, from a wind function times the vapor pressure and temperature differences.

  The new temperature is solved each step implicitly (backward Euler, Newton iterations), so the step is stable at hourly or daily steps
  and the energy closes with the fluxes at the new temperature. Inputs: air temperature, humidity, wind, shortwave and longwave down, and
  precipitation, the variables AORC and NWM forcing carry.
- **Wind function [A]:** Brady, Graves and Geyer (1969), fitted on cooling ponds and the usual choice for them (Edinger et al. 1974). This
  departs from `once_through`'s Ward (1980), which was kept for the Great Lakes. The spread between them is carried in an error range, as
  `evap_error` is.
- **Water:**
  - makeup (the withdrawal) holds the pond at its operating volume after evaporation, seepage and blowdown, less the precipitation on
    it (a gain);
  - blowdown (a return) holds the dissolved solids at a cycles of concentration limit, since evaporation leaves its mass behind;
  - seepage (a return to the ground, its own output so Basin Ledger can route it) is a rate over the bed [A].
- **Storage:** `water_user_water__volume`, the role design 0010 reserved for ponds. The balance held every step is withdrawal + gain =
  consumption + returns + change in storage, and each constituent's mass balance likewise.
- **Under a limit** (`water_user_water__withdrawal_volume_flux_limit`, dry mode as a limit of zero), makeup is cut and the pond draws
  down. Storage is the buffer, which is the point of the model for drought rules. A smaller pond warms faster. Below a minimum volume
  [A], the plant can't run, and that is reported.

### Decided (Andrew, Nov 26, 2026: as proposed)

Andrew's answers: "1. Count all, 2. Report, actions should be taken care of in the schedules part not automatically here. 3. Any
plant."

1. **Consumption: all of the pond's evaporation, or only what the plant's heat adds?** Proposed: all of it, since the pond is built
   for the plant. A shadow pond with no heat, run on the same weather, gives the natural evaporation beside it, so the forced part
   (Diehl and Harris 2014's measure) is reported too.
2. **A pond too warm for the plant:** report only, or act? Proposed for the first build: the heat still goes into the pond, so energy
   closes, and the hours above the plant's highest supply temperature [A] are reported (`water_user__setpoint_lost_time`). The pond
   doesn't act on it. Shedding load or turning the plant off belongs in a scenario's schedules (Basin Ledger's dated phases and scale
   multipliers), not in the pond.
3. **Who drives it:** data centers only, or any heat source? Proposed: any source (`heat_mw` or the input), with the data center's IT
   capacity as a shortcut.

### As built

`waterledger_models.ponds`: `physics.step` is the pond's step, as plain functions; `bmi.CoolingPondBmi` is the component. The variables are
in its module docstring. Every new name is [A: name], following the roles in 0010:
- returns split as `stream_return` (blowdown and spill) and `ground_return` (seepage);
- `water_user_water__volume` and its change rate;
- natural and forced evaporation;
- `water_user__waste_heat_power` in;
- `water_user__unremoved_heat_power` and `water_user__setpoint_lost_time` out;
- per constituent, the ground return's mass and the stored mass.

Choices made in the build, each [A] and each a parameter or input where it can be:
- **Wind:** given at 10 m (AORC, NWM) and taken to 2 m by a 1/7 power law (`wind_height_m`).
- **Geometry:** area = operating area × (volume / operating volume)^(2/3), a bowl of the same shape at every level (`area_exponent`).
  Area and depth at the operating volume are required: there is no default pond.
- **Defaults:** albedo 0.06, emissivity 0.97, cycles 4, seepage 1 mm a day, lowest workable volume 30% of the operating volume, highest
  supply temperature 35 C.
- **Temperatures:** rain falls at the air's temperature. Makeup comes in at the air's unless `water_user_intake_water__temperature` is
  set.
- **No condensation:** evaporation isn't let below zero. A pond colder than the air's dew point gains no water from it.
- **No ice:** the pond is held at 0 C, and the heat that takes is reported (`freeze_heat` in the step's terms), so the heat still closes.
- **Below the lowest volume,** the plant's heat isn't taken. It is reported as heat not removed, and the steps count as lost. The pond
  still evaporates and seeps. A pond that would go below empty in a step stops the run with an error saying the makeup is limited too
  long for its size.
- **Makeup** refills the pond to its operating volume within the step. Under a limit the shortfall comes first out of blowdown, then
  out of storage. Water above the operating volume spills to the stream return.
- **The heat solve** uses the step's starting area and volume. The new temperature solves the step's heat balance, every flux evaluated
  at it. Water leaving (blowdown, spill, seepage, evaporation) carries the new temperature's sensible heat.
- **The shadow pond** for natural evaporation has the pond's own volume and area each step and its own temperature, carried in the state
  (`natural_temperature`), with makeup unlimited.

Tested in `tests/test_cooling_pond.py`:
- water, heat and each constituent's mass close every step over 40 days of varied hourly weather, a limit, rain and a refill;
- a pond at its steady temperature holds the cycles' concentration exactly;
- with no plant heat, forced evaporation is zero;
- 500 MW into a 4 km2, 5 m pond on steady summer weather sends 40-90% of the added heat out as evaporation (about 64%). This is a
  check of size, not a calibration. Comparing it with USGS's pond figures (Diehl and Harris 2014) is still to do;
- hourly and daily steps settle at the same temperature (to 1e-6 C);
- a limit cuts blowdown before storage, then the pond draws down and warms;
- dry mode is a limit of zero;
- below the lowest volume the heat isn't taken; a hot pond counts lost steps but takes the heat;
- ice holds at 0 C; rain on a full pond spills; the heat set each step and the data center shortcut work;
- bad configurations are refused.

Its state carries to the bit in `tests/test_bmi_state.py`, through a limit and a refill. The CSDMS bmi-tester runs on it in CI
(`tests/bmi/pond.yaml`).

### Not in this design

The pond is a BMI component for coupled runs (Basin Ledger). It isn't a design in `DESIGNS`, the Monte Carlo runner, ERA5 cells, the
stored results or the site. Putting it there would follow the standard treatment (0010) and would be its own decision.

A storage pond (no heat: a reservoir between a source and a user, or a tailings pond) should come from the same pieces: the volume, mass
and makeup rules here without the heat. That is the reason to keep those parts separate from the surface energy balance.
