# 0025: A tailings pond, and the mill's water around it

Status: **built Nov 26, 2026** on branch `claude/tailings-pond`. Andrew chose a tailings or process pond as the second pond that keeps state
("Let's do the tailing process pond") and agreed the five choices below as proposed. It is a new BMI component, built on design 0024's
state functions and the cooling pond's surface energy balance. No existing estimate changes: the cooling pond and every other component are
untouched.

Basin Ledger asked for state "for any user model that keeps state between steps (ponds, tailings)" (`basinledger/docs/requests.md`,
waterledger-models item 6). Design 0010 left the slots: ore moisture as a mine's gain, and `water_user_water__volume` as the storage role
for "ponds, tailings".

## What it is

A mine's mill grinds the ore and separates the concentrate. What's left, the tailings, goes to an impoundment as a slurry. The solids settle
and keep water in their pores. The free water collects in a pool on the deposit, which is pumped back to the mill (reclaim). The mill's fresh
makeup, its withdrawal from a river or wells, covers what reclaim can't. What the pool held yesterday decides today's makeup, and the
tailings fill the impoundment over the mine's life, so the pond keeps state: the pool's volume, its temperature, its dissolved mass, and the
tailings' volume.

## Decided (Andrew, Nov 26, 2026: as proposed)

1. **Who drives it:** the slurry, given as a tailings solids rate (`tailings_t_per_day`, or `water_user_tailings__mass_flux` set each
   step) and the slurry's solids share. Any process can drive it. A mine and mill model is its own later step.
2. **Water locked in the tailings:** consumption, reported on its own (`water_user_water__entrained_volume_flux`) beside evaporation.
3. **Where the boundary sits:** the pond and the mill's makeup are one component. The mill's water demand follows from the solids, reclaim
   comes first, makeup covers the rest, and a drought limit cuts the makeup. Demand neither can meet is reported.
4. **Release:** water above the impoundment's operating capacity, less the tailings in it, goes to a stream. With `discharge: zero`, it is
   held and reported as freeboard used, and only water above the crest is released.
5. **Filling with tailings:** the deposit grows by the solids over their dry density, so the room for water shrinks over the mine's life.

## As built

`waterledger_models.ponds`: `tailings.step` is the step, as plain functions; `bmi.TailingsPondBmi` is the component. Its variables are in its
docstring. The cooling pond's `physics.surface`, `_solve` and `wind_at_2m` are imported, not copied or changed.

Each step:
- **The mill** needs the slurry's water, the solids rate x (1 - solids share) / solids share, plus any other use (`mill_other_m3_t`,
  consumed), less the ore's moisture (`ore_moisture_m3_t`, a gain). Reclaim takes what it can: the pool above its lowest workable volume,
  at most the reclaim pumps' capacity. Makeup covers the rest, up to the limit.
- **Short of water,** the mill processes only the ore its water allows. That is a physical limit, not an operating rule. The shortfall is
  reported as unmet demand, and its hours as `water_user__lost_production_time`. To slow or stop the mill on purpose, a scenario's
  schedules set the solids rate, following Andrew's answer on the cooling pond: "actions should be taken care of in the schedules part not
  automatically here."
- **The tailings** settle at a dry density. Their pores hold saturation x void ratio / specific gravity m3 of water a tonne, about 0.34 m3
  at the defaults. The rest of the slurry's water joins the pool.
- **The pool** also gains rain on it, and runoff from the beach (the deposit's surface outside the pool) and from a catchment, at a runoff
  coefficient. It loses evaporation, seepage, reclaim and release. Its area is its volume over a mean depth, at most the impoundment's
  surface at its fill.
- **Heat:** the cooling pond's surface energy balance with no plant heat, solved implicitly in the pool's new temperature. Slurry, rain and
  runoff come in at the air's temperature. Ice is held at 0 C, and the heat that takes is reported, as in the cooling pond.
- **Mass:** each constituent is mixed through the pool. The mill's water mixes makeup and reclaim, plus what the solids release a tonne
  (`solids_release`, sulfate from oxidation for example). What the tailings lock, and the mill's other use, leave at the mill water's
  concentration (`water_user_tailings_water_<name>__mass_flux`). Seepage and release leave at the pool's new concentration.

Water roles, holding withdrawal + gain = consumption + return + change in storage every step:
- withdrawal: the makeup;
- gain: rain on the pool, runoff, the ore's moisture;
- consumption: evaporation, the locked pore water, the mill's other use;
- returns: release to a stream (`stream_return`), seepage (`ground_return`);
- storage: the pool.

Defaults [A], each a parameter:
- solids share 0.35 (conventional tailings; thickened tailings run 0.5-0.7);
- dry density 1.4 t m-3, solids specific gravity 2.7, saturation 1;
- pool depth 2 m;
- runoff coefficient 0.5;
- ore moisture and other mill use 0;
- seepage 1 mm a day under the pool;
- freeboard 10% of the operating capacity (zero discharge only);
- the lowest workable pool, a quarter of the initial pool (a setting).

The capacity, its area, the solids rate and the initial pool are required: there is no default mine.

## Tests

`tests/test_tailings_pond.py`:
- water, heat and each constituent's mass close every step, over 60 days of varied hourly weather, with a limit, a slowed mill, a
  catchment, ore moisture, other mill use and solids release;
- the pore water and the deposit's growth match the formulas;
- reclaim comes before makeup, and makeup takes over at the pool's lowest volume;
- under a limit the mill processes only what its water allows, and dry mode stops it;
- release above the operating capacity; zero discharge holds to the crest, then releases;
- the tailings fill the impoundment, and a full one stops the run;
- the solids rate set each step holds, and NaN goes back to the configured rate;
- the pool concentrates as it evaporates;
- bad configurations are refused.

Its state carries to the bit in `tests/test_bmi_state.py`, through a limit and a slowed mill. The CSDMS bmi-tester runs on it in CI
(`tests/bmi/tailings.yaml`).

## Not in this design

- A mine or mill model (ore, concentrate, energy), and a mine as a water user type under 0010. Both would be their own decisions.
- Beach evaporation, and water held in the beach above the pool: only the pool evaporates [A].
- A stormwater pond (filled by runoff, drained through an outlet), and a managed supply pond. Both can come from the same pieces.
