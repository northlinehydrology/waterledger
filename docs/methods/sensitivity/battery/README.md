# Global sensitivity analysis of the battery cell plant model

Design 0009, Nov 10, 2026. `sensitivity.py` here; the CSVs and `run_info.json` are its full run. Sobol' indices (S1 by
Saltelli et al. 2010, ST by Jansen 1999, bootstrap 95% intervals) and Morris elementary effects, with the data center
analysis's functions (`../sensitivity.py`) unchanged.

The plant runs at full output (the headline, decision 2) and makes NMC cells. 42 parameters for dry, assist, hybrid and
towers (the plant's 20 less utilization, and the 22 shared equipment parameters); 45 for the lake (and the lake's 3). N =
4096, West Michigan weather 2023-2024, Lake Michigan's GLERL temperatures. Outputs per 10 GWh/yr of cells.

Rerun Nov 10, 2026 with the assist design (design 0010's standard treatment), whose pads' effectiveness and bleed joined
the shared equipment. Adding two parameters changes the Saltelli sample for every design, so the other designs' indices
moved by sampling noise only: at most 0.034 on any index (lake electricity), less than the width of the earlier run's
95% intervals for those indices (0.04-0.05); no warnings.

Total-order indices (ST), largest first:

| Design | Withdrawn, average day | Withdrawn, 1-in-10 peak day | Consumed, average day | To sewer | Electricity, average |
|---|---|---|---|---|---|
| Dry | boiler make-up 0.28, shipped water 0.17, anode water 0.17 | the same (no weather in it) | boiler make-up 0.46, shipped water 0.26, anode water 0.25 | staff gpcd 0.29, other purified 0.26, staff per GWh 0.23 | energy 0.52, electricity share 0.50 |
| Assist | energy 0.16, boiler make-up 0.15, share to water 0.11 | energy 0.35, share to water 0.24, pad bleed 0.16, coil air rise 0.12 | energy 0.22, boiler make-up 0.19, share to water 0.15 | pad bleed 0.23, staff gpcd 0.21, other purified 0.18 | energy 0.52, electricity share 0.50 |
| Hybrid | boiler make-up 0.19, energy 0.13, shipped water 0.11 | energy 0.42, share to water 0.28, outdoor air 0.10 | boiler make-up 0.26, energy 0.18, shipped water 0.14 | staff gpcd 0.26, other purified 0.23, staff per GWh 0.20 | energy 0.52, electricity share 0.50 |
| Towers | energy 0.52, share to water 0.35, cycles 0.07 | energy 0.46, share to water 0.31, outdoor air 0.13 | energy 0.56, share to water 0.38, evaporative ratio 0.06 | cycles 0.59, energy 0.22, share to water 0.15 | electricity share 0.52, energy 0.50 |
| Lake | energy 0.41, temperature rise 0.33, share to water 0.30 | energy 0.37, rise 0.29, share to water 0.28 | energy 0.43, share to water 0.31, evaporation error 0.23 | staff gpcd 0.29, other purified 0.28, staff per GWh 0.23 | electricity share 0.52, energy 0.46 |

Reading:

- **For towers, two parameters carry about 85% of the variance:** the plant's energy per kWh of cells and the share
  of it that reaches the cooling water. Both are set from whole-plant energy figures and a step-by-step estimate [A].
  Narrowing either narrows the headline; a measured plant energy figure would do more than any tower parameter.
- **Cycles of concentration matter for the sewer, not the withdrawal:** 0.59 of the sewer flow's variance and 0.07 of
  the withdrawal's. That is why Lansing's own 3 cycles moved its discharge onto the EA's figure.
- **Where the cooling takes little water (dry, and hybrid on most days), process water leads,** and boiler make-up
  (0.2-2.0 L/kWh [A], the widest estimate in the model) leads it. It is the parameter to source next for those designs.
- **Assist sits between:** the plant energy and its share to the water lead, since the pads evaporate in proportion to
  the heat, with boiler make-up close behind. The pads' bleed (0-0.5 of their evaporation, once-through to recirculating
  pads [A]) leads its sewer flow and moves its peak day; the coil's air rise (9-13 K [A]) moves the peak day too.
- **The outdoor air share moves only the peak day** (0.10-0.13), as it should: it is the weather-driven load.
- The other equipment parameters shared with data centers barely register here; the evaporative ratio is the one that
  does (0.06 of towers' consumption).
- Sums of S1 are 0.95-1.02, so the model is close to additive over these ranges.
