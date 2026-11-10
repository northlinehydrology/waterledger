# Global sensitivity analysis of the battery cell plant model

Design 0009, Nov 10, 2026. `sensitivity.py` here; the CSVs and `run_info.json` are its full run. Sobol' indices (S1 by
Saltelli et al. 2010, ST by Jansen 1999, bootstrap 95% intervals) and Morris elementary effects, with the data center
analysis's functions (`../sensitivity.py`) unchanged.

The plant runs at full output (the headline, decision 2) and makes NMC cells. 40 parameters for dry, hybrid and towers
(the plant's 20 less utilization, and the 20 shared equipment parameters); 43 for the lake (and the lake's 3). N = 4096,
West Michigan weather 2023-2024, Lake Michigan's GLERL temperatures. Outputs per 10 GWh/yr of cells.

Total-order indices (ST), largest first:

| Design | Withdrawn, average day | Withdrawn, 1-in-10 peak day | Consumed, average day | To sewer | Electricity, average |
|---|---|---|---|---|---|
| Dry | boiler make-up 0.27, anode water 0.16, shipped water 0.16 | the same (no weather in it) | boiler make-up 0.46, anode water 0.25, shipped water 0.25 | staff gpcd 0.27, other purified 0.25, staff per GWh 0.22 | energy 0.51, electricity share 0.50 |
| Hybrid | boiler make-up 0.19, energy 0.12, anode water 0.11 | energy 0.42, share to water 0.29, outdoor air 0.10 | boiler make-up 0.25, energy 0.18, anode water 0.14 | staff gpcd 0.25, other purified 0.22, staff per GWh 0.20 | energy 0.50, electricity share 0.50 |
| Towers | energy 0.50, share to water 0.35, cycles 0.07 | energy 0.45, share to water 0.31, outdoor air 0.13 | energy 0.54, share to water 0.37, evaporative ratio 0.06 | cycles 0.56, energy 0.21, share to water 0.14 | electricity share 0.52, energy 0.48 |
| Lake | energy 0.41, temperature rise 0.33, share to water 0.29 | energy 0.37, rise 0.29, share to water 0.27 | energy 0.42, share to water 0.31, evaporation error 0.23 | staff gpcd 0.28, other purified 0.26, staff per GWh 0.22 | electricity share 0.56, energy 0.49 |

Reading:

- **For towers, two parameters carry about 85% of the variance:** the plant's energy per kWh of cells and the share
  of it that reaches the cooling water. Both are set from whole-plant energy figures and a step-by-step estimate [A].
  Narrowing either narrows the headline; a measured plant energy figure would do more than any tower parameter.
- **Cycles of concentration matter for the sewer, not the withdrawal:** 0.56 of the sewer flow's variance and 0.07 of
  the withdrawal's. That is why Lansing's own 3 cycles moved its discharge onto the EA's figure.
- **Where the cooling takes little water (dry, and hybrid on most days), process water leads,** and boiler make-up
  (0.2-2.0 L/kWh [A], the widest estimate in the model) leads it. It is the parameter to source next for those designs.
- **The outdoor air share moves only the peak day** (0.10-0.13), as it should: it is the weather-driven load.
- The equipment parameters shared with data centers barely register here; the evaporative ratio is the one that does
  (0.06 of towers' consumption).
- Sums of S1 are 0.92-1.05, so the model is close to additive over these ranges. The two lake withdrawals' sums of
  1.03-1.05 are sampling error in S1 (the warnings in `run_info.json`).
