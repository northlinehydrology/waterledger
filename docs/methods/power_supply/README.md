# Checks of the power supply models (design 0014)

`eia_check.py` is 0014's check 3: the gas plant model against EIA-reported water at combined cycle plants on cooling
towers, in aggregate only (two regions, region-months with five or more plants; no plant named). `eia_check.csv` is its
output. The other checks are tests: NETL at ISO weather and the derate in `tests/test_gas.py`, a year of weather against
the published ranges there too, PV against pvlib in `tests/test_supply.py`, and N + 1 sizing in `tests/test_scenarios.py`.

## Check 3, Nov 10, 2026 (EIA 2024 cooling detail; model at central values, nothing tuned)

| Region (plants a month) | EIA consumed / withdrawn, gal/MWh | Model, new plant's heat rate | Fleet heat rate | Model at the fleet's heat rate |
|---|---|---|---|---|
| Great Lakes (40-45) | 195 / 242 | 155 / 196 (0.79 / 0.81) | 7,507 Btu/kWh | 218 / 275 |
| Texas (35-40) | 203 / 241 | 170 / 215 (0.84 / 0.89) | 8,342 Btu/kWh | 286 / 362 |

Reading:

- **The level is mostly the heat rate.** The model's heat rate is a new F-class plant's, 6,200-6,450 Btu/kWh (EIA AEO2023,
  NETL), because supply scenarios build new plants. The 2024 fleet runs at about 7,500 in the Great Lakes, so it sends
  more heat to its condensers per MWh. EIA's Great Lakes figures sit between the model at the two heat rates: 21% under
  it at a new plant's, 12% over at the fleet's. For a new plant the model's figure is the one to use.
- **Texas's fleet heat rate is high** (8,342), most likely because many of its combined cycles are cogeneration plants,
  which send steam to industry instead of the condenser, so less heat reaches the towers per MWh than the heat rate
  suggests; at that heat rate the model overshoots. The file doesn't mark cogeneration, so this is not separated here.
- **The seasonal swing is smaller in the model:** summer over winter 1.16 against EIA's 1.34 in the Great Lakes (1.19
  against 1.23 in Texas). The model's heat rate rises little with temperature (0.05-0.2% per K for combined cycle [A]) and
  it holds the plant at full output; the fleet runs duct burners and part load in summer and evaporates more of its heat
  in warm weather than the shared evaporative ratio gives (the gas sensitivity analysis puts that ratio first on towers).
  Both are open: a measured seasonal split at new plants would settle which.
- With the NETL check at ISO weather (158 against 186 gal/MWh consumed), three independent figures put a new plant on
  towers 15-20% under the reported fleet or design case at a new plant's heat rate. It is stated, not tuned.

## Check 5 with curtailment added back, Nov 17, 2026

EIA-923's net generation is what plants delivered, with the grid's curtailment already taken out. A supply scenario takes
curtailment out again: PV and wind serve the campus first, and their surplus is exported with no credit. A factor fitted
to delivered output therefore counted curtailment twice.

`curtailment.py` adds each plant's balancing authority's 2024 curtailment back before the fit.
- **Solar:** Berkeley Lab's 2025 data update gives ERCOT 7.1%, CAISO 3.7% and SPP 2.8%; other balancing authorities report
  none.
- **Wind:** Berkeley Lab's 2025 technology update, figure file p. 47, gives SPP 10.5%. ERCOT about 4.6%, MISO 3.4%, NYISO
  1.1%, CAISO 0.7% and ISO-NE 0.65% are read off the chart.
- That adds 2.85% to the PV fleet's delivered output and 4.91% to wind's.

The fleet factors rise:
- **PV:** 0.84 to 0.86. Texas 0.81 to 0.88, California 0.84 to 0.87.
- **Wind, at 110 m:** 0.99 to 1.01. Texas 0.93 to 0.95, Oklahoma 0.93 to 0.99.

The sampled ranges stand, because their ends are states that report no curtailment:
- **PV:** Ohio and Wisconsin 0.76, Nevada 0.94, Georgia 0.91.
- **Wind:** Minnesota and Wyoming 0.93, Illinois and the newest interior plants 1.05-1.06.

The delivered-basis results are kept as `*_delivered.csv`. The checks now run the chain at a resource factor of 1.0 whatever
`RANGES` holds. Before, they read the range's midpoint, which changed once the range was set from them.
