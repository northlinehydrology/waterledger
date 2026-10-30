# Reconciling plant-based and Siddik et al. power-plant water intensities

Scripts: `reconcile.py` (balancing-authority comparison, `recon_ba_2022_2024.csv`) and `combine.py` (state table,
`state_power_water_combined_2024.csv`). Status: proposal, not integrated into the package table or the methods log.

## Summary

The two estimates are not independent. Both rest on the same plant reports (EIA-923 Schedule 8D, published in EIA's
thermoelectric cooling water data), so the gap between them is mostly definition and data treatment, not measurement
disagreement. Averaging the published values would mix definitions and double count those reports. After conversion to a
common basis, the 2022 evidence is useful as a second year of plant reports, and it enters as a lognormal prior updated by
the 2024 data. The weight on 2022 is about 0.2 to 0.28 in most states.

## 1. What each estimate measures

Page references are to Siddik et al. (2024). "Reproduced" marks a point the paper does not state and that we inferred by
rebuilding their values from public data (section 2).

| Item | Siddik et al. WCI_NH, WWI_NH | Current plant-based method (A) |
|---|---|---|
| Year | 2022 (dataset covers 2018-2022, p. 5) | 2024 |
| Unit | Balancing authority (BA) | State, blended with its main BA by net import share |
| Basis | Consumption-based: "embedded in each unit of electricity consumption" (Table 3, p. 8) | Generation-based for in-state plants; net interstate imports at the main BA's generation-based value (EIA State Electricity Profiles, Table 10) |
| Interchange | Hourly, one step: direct imports at the exporter's generation mix (Eqs. 2-3, p. 7; EIA-930). No onward tracing | Annual net share, one region |
| Canadian and Mexican imports | Reproduced: dropped, with the mix normalized over U.S. sources (ISNE hydro 7.1% published, 7.5% rebuilt, with about 13% of load imported from Canada) | Not included |
| Hydropower | Zero water, generation kept in the denominator (Table 3, p. 8) | The same |
| Wind and PV | Meldrum et al. (2013) averages (p. 5); negligible (implied ERCO factors about 0.00 and 0.01 L/kWh) | Zero |
| Water | Reported cooling water from EIA's cooling data (Table 1, p. 4); all water types | The same source and scope. Neither includes other plant water or upstream fuel water |
| Implausible reports | Not screened; the authors note possible errors and outliers (p. 11, citing Peer and Sanders 2016). Reproduced: ERCO nuclear and coal factors match raw reports month by month | 181 plants in 2024 replaced with Macknick et al. (2012) medians by technology and cooling (consumption above withdrawal or 1,500 gal/MWh; zero consumption at once-through or pond plants; over 25,000 gal/MWh withdrawn at tower or pond plants) |
| Plants that do not report | "Average monthly water use intensity ... of all power plants of the same fuel type" (p. 5). Reproduced: national fuel-month ratio over reporting plants, applied to all such generation including combustion turbines; none for the "other" category | Zero water |
| Plants reporting zero consumption | Reproduced: treated as non-reporting, so they receive the fuel-wide average. Weighted absolute error against the published values falls from 17.9% to 4.4% with this rule | Macknick median for the plant's cooling class (nuclear once-through 269 gal/MWh, 1.02 L/kWh) |
| Fuel factors | Monthly by BA and fuel (Eq. 1, p. 6), applied to EIA-930 hourly fuel mix | None; annual plant water |
| Denominator | EIA-930 load, BA (Eq. 3, p. 7) | All net generation, state or BA (EIA) |
| Annual value | Load-weighted mean of hourly values (our aggregation; every row of `grid_water_2022.csv` matches to four decimals) | Annual water / annual generation |

Three differences matter most. First, both methods fill plants reporting zero consumption, by different rules: a fuel-wide average
that includes tower plants in Siddik et al., a cooling-specific median in ours. For nuclear the two are close (national ratio
1.2 L/kWh in 2022 against 1.02); for coal, the fuel-wide average is well above the once-through median of 0.95 L/kWh. Second, Siddik
et al. keep implausibly high reports (for example Bull Run in TVA, about 5,800 gal/MWh in 2022), which ours replaces. Third,
reservoir circulation reported as withdrawal is kept by Siddik et al. and replaced by makeup-water medians in ours.

## 2. Reproduction and decomposition

Their method was rebuilt from EIA's 2022 cooling detail, EIA-923 and EIA-930 (adjusted columns). The rebuilt hourly mix matches
theirs (PJM coal 19.91% in both; correlation 1.00 in most large BAs). With the reproduced rules, intensities for BAs over 10
TWh have r = 0.98 and 4.4% load-weighted absolute error for consumption; r = 0.93 and 8.1% for withdrawal. Withdrawal is
reproduced without the zero rule.

Each step changes one thing, in this order: year (2024 to 2022, our method); generation data (EIA-923 to EIA-930 fuel mix);
boundary (imports, Eq. 3); screening removed; non-reporter fill added; zero reports treated as missing; residual to the
published value. The steps are sequential, so an attribution depends somewhat on the order.

Consumed, L/kWh:

| BA | Siddik 2022 | Ours 2024 | Gap | Year | Gen. data | Boundary | Screening | Non-reporters | Zero reports | Residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PJM | 1.298 | 0.954 | 0.345 | 0.094 | 0.005 | -0.005 | -0.097 | 0.051 | 0.280 | 0.017 |
| MISO | 1.570 | 1.041 | 0.529 | -0.042 | 0.024 | -0.002 | 0.238 | 0.058 | 0.294 | -0.041 |
| ERCO | 0.730 | 0.773 | -0.044 | -0.086 | -0.001 | 0.001 | -0.020 | 0.043 | 0.106 | -0.086 |
| SWPP | 0.940 | 0.738 | 0.202 | 0.059 | 0.013 | -0.001 | 0.007 | 0.056 | 0.134 | -0.066 |
| SOCO | 1.517 | 1.197 | 0.320 | 0.110 | 0.037 | -0.047 | 0.090 | 0.108 | 0.024 | -0.002 |
| CISO | 0.641 | 0.248 | 0.393 | 0.030 | 0.011 | 0.131 | -0.096 | 0.102 | 0.213 | 0.003 |
| TVA | 0.955 | 0.776 | 0.179 | -0.257 | -0.009 | 0.061 | -0.029 | 0.014 | 0.367 | 0.032 |
| NYIS | 0.634 | 0.387 | 0.248 | -0.020 | 0.011 | 0.076 | -0.173 | 0.063 | 0.374 | -0.083 |
| ISNE | 0.629 | 0.432 | 0.197 | 0.025 | 0.009 | -0.002 | -0.297 | 0.061 | 0.566 | -0.165 |
| Load-weighted, BAs over 10 TWh | | | 0.242 | -0.003 | -0.003 | 0.010 | -0.022 | 0.068 | 0.226 | -0.035 |

Withdrawn, L/kWh:

| BA | Siddik 2022 | Ours 2024 | Gap | Year | Gen. data | Boundary | Screening | Non-reporters | Residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PJM | 52.27 | 39.61 | 12.67 | 4.03 | 0.25 | 0.44 | 5.55 | 2.86 | -0.46 |
| MISO | 54.80 | 43.33 | 11.46 | 4.84 | 0.58 | -0.30 | 7.12 | 2.07 | -2.85 |
| ERCO | 55.00 | 18.25 | 36.75 | 1.64 | 0.14 | 0.04 | 34.35 | 1.49 | -0.91 |
| SWPP | 41.24 | 24.74 | 16.50 | 0.90 | 0.68 | 0.06 | 13.41 | 2.42 | -0.97 |
| SOCO | 19.97 | 14.26 | 5.70 | -0.34 | -0.25 | 3.61 | 0.08 | 4.50 | -1.90 |
| NYIS | 48.77 | 36.87 | 11.91 | 2.99 | 11.66 | -0.72 | 0.61 | 15.10 | -17.73 |
| DUK | 170.05 | 95.62 | 74.43 | 2.01 | -2.04 | -6.60 | 1.70 | 13.88 | 65.48 |
| Load-weighted, BAs over 10 TWh | | | 14.47 | 2.95 | 0.58 | -0.48 | 8.12 | 3.50 | -0.20 |

Findings:

- **Year does not explain the consumption gap.** Load-weighted it is -0.003 L/kWh, about -1% of the gap. It runs in the expected
  direction in PJM and SOCO, where coal fell (PJM coal 159 to 116 TWh, EIA-923), and against it in MISO, ERCO and TVA, because
  reported intensities changed as well as the mix. TVA's -0.257 is largely Sequoyah, which reported zero in 2022 and 2023 and
  about 1,150 gal/MWh in 2024. Year accounts for about 20% of the withdrawal gap.
- **Imports are a small part of it** for large regions (about 4% of the consumption gap, and -3% of the withdrawal gap). They
  matter in CISO and NYIS for consumption and in SOCO, CISO and TVA for withdrawal.
- **Treatment of reports accounts for most of the consumption gap.** The screening and zero-report steps must be read together,
  since ours fills zeros inside screening and removing that fill is then reversed by the zero step: net 0.204 L/kWh, about 84% of the
  gap (PJM 0.183, MISO 0.532, ISNE 0.269, TVA 0.338). Non-reporter fill adds about 28%, and the residual offsets about 14%.
- **Screening accounts for most of the withdrawal gap** (about 56%; 34 of ERCO's 37 L/kWh), then non-reporter fill (24%).
- **Residual.** It is small in most large BAs but not all. Consumption, ratio published to rebuilt, is below 0.8 in ISNE, SCEG,
  JEA and NEVP. Withdrawal is far off in DUK (1.63), PNM (2.62), TEPC (2.25), and NYIS (0.73). EIA's 2022 files were revised
  after the paper (the EIA-923 2022 "Final Revision" files are dated Oct 2024) and the paper's EIA data are cited as retrieved
  in May 2023, so revisions may explain part of this. That was not tested.

## 3. Combination

**Target quantity.** Water at power plants per kWh used in the state in 2024, excluding hydropower reservoirs and international
imports, with implausible reports screened and non-reporting plants filled by technology.

**Why not a direct average.** Inverse-variance weighting assumes errors that are independent or of known correlation. If an
estimate equals another plus independent noise, its optimal weight is zero; that is close to the situation here for the part
of Siddik et al.'s value that comes from the same reports and from known rule differences. The raw values also differ in
definition (section 1), and a BA value is a different geography from a state.

**Common basis.**

- Non-reporting steam and combined-cycle generation, about 148 TWh or 3.4% of U.S. generation, is assigned Macknick tower medians
  (Table 2, Table 3); combustion turbines and engines stay at zero. This adds about 5.9% to national consumption. It is an upper
  estimate where such plants are dry-cooled, and it is included in both estimates. Siddik et al.'s fill and this one add similar
  amounts (about 0.07 L/kWh and 0.05-0.06 in PJM and MISO), by different routes.
- E1: the current central value plus that fill.
- E2: the same calculation with each plant's 2024 intensity replaced by its screened 2022 intensity, at 2024 generation, so
  mix and year of generation match E1; times r, the BA's published-to-rebuilt ratio (`r_c`, `r_w`). Plants without a 2022 record
  keep 2024 values. After conversion, r is the only channel through which the published value itself enters, and it is applied to
  the state by assuming the BA ratio holds there.

**Update.** Lognormal, with E2 as the prior and E1 as the data:

    ln(theta) = (1 - w) ln(E1) + w ln(E2),    w = (1/s2^2) / (1/s1^2 + 1/s2^2)

Variances come from the plants' own year-to-year scatter:

- v = sum over plants of (W2024 - W2022)^2, in L/kWh, with state and BA terms combined by import share.
- Scatter is split into noise and real change using three years, with D(lag) = 2 noise + lag x drift (random walk), summed over
  plants present in 2022, 2023 and 2024. Real change is phi = 0.45 of the two-year difference for consumption and 0.60 for
  withdrawal. Real change counts against the older year only.
- s1^2 = (1 - phi) v / 2 / E1^2 and s2^2 = (1 + phi) v / 2 / E1^2 + (ln r)^2, each relative error floored at 0.02 [A].
- With r = 1, w = (1 - phi) / 2: 0.275 for consumption and 0.20 for withdrawal. A BA with a large unexplained residual
  down-weights itself (w is below 0.01 for ISNE consumption and for DUK and PNM withdrawal).

**Normal or lognormal.** Lognormal: intensities are positive and right-skewed across states and errors scale with the value.
Over this range the two differ little in the central value.

**Shared error.** Errors common to both years cannot be reduced by combining, so they widen the interval only:
s_shared^2 = s_lit^2 + (f_flag x 0.35)^2 + (f_fill x 0.5)^2. Here s_lit is ln(1.08) for consumption and ln(1.24) for withdrawal, the size of
the difference between EIA-reported totals and modeled totals in Diehl and Harris (2014) for 2010, used as a scale [A]. f_flag is the
share of water from Macknick-filled plants; 0.35 is ln(400/100)/4 from Macknick's nuclear once-through range [A]. f_fill is the fill's
share; 0.5 reflects unknown cooling at non-reporters [A]. Peer and Sanders (2016) show how common outliers are, especially
consumption at once-through plants (75 of 119 coal values in their Table 3), but give no overall error rate that could be used
directly.

**Range.** lo and hi are the envelope of the 95% interval, E1, E2 and a Macknick bottom-up on the same basis (blended, with the
fill). `lo_stat` and `hi_stat` are the interval alone. The bottom-up is the one estimate whose water values do not come from the same
reports; it falls inside the interval in 80% of states for consumption and 68% for withdrawal, so the interval alone is too narrow
as a statement of total uncertainty. The raw Siddik value is no longer in the range, since it is not on the same basis.

**Where the raw values should not be combined.**

- Withdrawal where reservoir circulation is reported as withdrawal: ERCO, SWPP, FPL, SCEG, SC and CPLE (screening step in
  `recon_ba_2022_2024.csv`). The published values there measure a different quantity from makeup water.
- Consumption in ISNE and NYIS, and in other regions dominated by once-through plants reporting zero, where the published value
  rests on the zero rule.
- BAs with large residuals (DUK, NYIS, PNM, TEPC and others listed above); r stays in the formula and its weight goes to nearly zero.
- States far from their BA average (SD, IA, ID, NV against SWPP, MISO, IPCO, NEVP): the BA value says little about in-state plants.
  In the proposal, the state's own plants carry the estimate and the BA enters through the import share and r.
- Alaska and Puerto Rico have no figure. Hawaii has no BA value, so r = 1.

## 4. Results

L/kWh; central (range). All states are in `state_power_water_combined_2024.csv`.

| State | Consumed, current | Consumed, proposed | Withdrawn, current | Withdrawn, proposed |
|---|---|---|---|---|
| Michigan | 0.94 (0.76-1.57) | 1.01 (0.74-1.38) | 58.7 (54.8-58.8) | 58.5 (38.2-89.6) |
| Ohio | 1.03 (0.96-1.30) | 1.06 (0.89-1.25) | 24.6 (21.2-52.3) | 24.3 (15.9-37.2) |
| Virginia | 0.59 (0.42-1.30) | 0.67 (0.48-0.95) | 51.2 (48.4-56.3) | 51.9 (33.9-79.4) |
| Texas | 0.78 (0.73-0.78) | 0.77 (0.62-0.94) | 19.1 (13.2-55.0) | 19.2 (11.8-31.2) |

Across states the median change in the central value is +6.1% for consumption (10th to 90th percentile -0.1% to +36%) and +0.6%
for withdrawal (-2.2% to +12%). Most of the consumption change is the non-reporter fill, not the 2022 evidence. The largest
relative changes are in states with few reporting plants (Hawaii, South Dakota, Massachusetts, Rhode Island, Maine). The median
effect of r is about 0.5%. Ranges are not uniformly narrower: withdrawal ranges now reflect reporting error, where before they
reflected mostly the spread between methods.

## 5. Limits

- The zero rule and the fill rule are inferred from the data, not read from the authors' code. Their notebook on HydroShare would
  settle them; we did not use it. Plant water is assigned to the plant's main fuel, which is an approximation of Eq. 1.
- The screen does not catch implausibly low reports at tower plants (15 plants, 34 TWh in 2024, under a quarter of Macknick's
  median; for example Kendall County, Batesville, Spurlock) or high reports below 1,500 gal/MWh at once-through plants (Sequoyah,
  about 1,150 in 2024). This affects Tennessee, Mississippi, Kentucky, Illinois and others. Bounds by cooling class would be
  a better screen and should be applied to every state and year; it is not part of this proposal.
- When consumption exceeds withdrawal, `states.py` caps the Macknick value at reported withdrawal, even if the withdrawal is the
  bad figure. Big Stone in South Dakota (1,029 Mgal consumed, 66 withdrawn) is left at 66, which is why South Dakota's consumption is
  about 0.02 L/kWh against a bottom-up of about 0.16. The rule was kept here so that E1 matches the current table.
- Hawaii's central value doubles on the fill alone (oil-fired combined cycle and steam at tower medians), and its reporting plants
  use seawater. The same rule applies to every state, but this value is weak.
- The noise and drift split rests on three years, is national, and is dominated by large plants. Real change and noise are not
  separately identified at state level.
- Applying r to a state assumes the BA's residual holds there.
- s_lit is from 2010 data and is a scale, not an error estimate for screened 2024 data.
- Sequential attribution depends on the order of steps. "Year" combines changes in mix with changes in reports.

## References

Diehl, T.H., and Harris, M.A. (2014). Withdrawal and consumption of water by thermoelectric power plants in the United States, 2010.
U.S. Geological Survey Scientific Investigations Report 2014-5184. https://doi.org/10.3133/sir20145184

Macknick, J., Newmark, R., Heath, G., and Hallett, K.C. (2012). Operational water consumption and withdrawal factors for electricity
generating technologies: A review of existing literature. Environmental Research Letters, 7(4), 045802.
https://doi.org/10.1088/1748-9326/7/4/045802

Meldrum, J., Nettles-Anderson, S., Heath, G., and Macknick, J. (2013). Life cycle water use for electricity generation: A review and
harmonization of literature estimates. Environmental Research Letters, 8(1), 015031. https://doi.org/10.1088/1748-9326/8/1/015031

Peer, R.A.M., and Sanders, K.T. (2016). Characterizing cooling water source and usage patterns across US thermoelectric power plants: A
comprehensive assessment of self-reported cooling water data. Environmental Research Letters, 11(12), 124030.
https://doi.org/10.1088/1748-9326/aa51d8

Siddik, M.A.B., Shehabi, A., Rao, P., and Marston, L.T. (2024). Spatially and temporally detailed water and carbon footprints of U.S.
electricity generation and use. Water Resources Research, 60, e2024WR038350. https://doi.org/10.1029/2024WR038350

U.S. Energy Information Administration. Thermoelectric cooling water data, 2022-2024; Form EIA-923, 2022-2024; Form EIA-930 six-month
files, 2022 and 2024; State Electricity Profiles, 2024.
