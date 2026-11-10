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
