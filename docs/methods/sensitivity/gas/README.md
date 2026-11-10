# Global sensitivity analysis of the gas plant model

Design 0014, Nov 10, 2026. `sensitivity.py` here; the CSVs and `run_info.json` are its full run. Sobol' indices (S1 by
Saltelli et al. 2010, ST by Jansen 1999, bootstrap 95% intervals) and Morris elementary effects, with the data center
analysis's functions (`../sensitivity.py`) unchanged. N = 2048, West Michigan weather 2023-2024, Lake Michigan's GLERL
temperatures. Each case is two 300 MW units asked for their full ISO rating every hour.

Total-order indices (ST), largest first:

| Case | Consumed per MWh | Withdrawn per MWh | Heat rate | Net output |
|---|---|---|---|---|
| Combined cycle, towers (p50 154 / 196 gal/MWh) | evaporative ratio 0.52, condenser share 0.37, heat rate 0.10 | cycles 0.38, evaporative ratio 0.32, condenser share 0.22 | ISO heat rate 0.95 | wet derate 1.00 |
| Combined cycle, hybrid (p50 5 / 7) | switch-on dry-bulb 0.96 | switch-on 0.95 | ISO heat rate 0.95 | dry derate 0.66, switch-on 0.29 |
| Combined cycle, lake (p50 88 / 14,590) | evaporation error 0.71, wind 0.14, condenser share 0.11 | temperature rise 0.86, condenser share 0.09 | ISO heat rate 0.96 | wet derate 1.01 |
| Simple cycle, water injection (p50 39 / 52) | water-to-fuel ratio 1.00 | water-to-fuel ratio 0.97, demineralizer recovery 0.04 | ISO heat rate 1.00 | derate 1.03 |

Reading:

- **On towers, the evaporative ratio leads consumption** (0.52), then the share of the losses that reaches the condenser
  (0.37). The ratio is the shared one (Rutberg et al. 2011, the `er_adj` range every user samples); it is also why the
  model runs about 15% under NETL B31A at ISO weather, where NETL evaporates more of the heat. A measured consumption at
  a tower-cooled combined cycle, by season, would test it better than any single parameter here.
- **A hybrid condenser's water is almost all its switch-on temperature** (0.96), which is an assumption, 20-30 C [A]: no
  source gives where power plant hybrids go wet. It is the parameter to source first for that design.
- **Cycles carry withdrawal on towers** (0.38) but not consumption, as for the other types.
- **The lake design's withdrawal is the temperature rise** (0.86); its consumption is the forced evaporation's error.
- **Simple cycle water is the NOx setting:** the water-to-fuel ratio carries it all. Dry low-NOx turbines use none.
- Heat rate and output follow their own ISO values and derates; weather moves them, but the ranges do most.
- Sums of S1 are within 0.05 of 1; the two simple-cycle water sums of 1.04-1.05 are sampling error (warnings in
  `run_info.json`).
