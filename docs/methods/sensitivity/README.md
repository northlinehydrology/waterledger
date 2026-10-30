# Global sensitivity analysis of the data center water model (model 1.3)

Oct 30, 2026. Code: `sensitivity.py` in this folder. Results: `sobol_indices.csv`, `morris.csv`, `convergence.csv`,
`output_summary.csv`, `run_info.json`.

## Purpose

Water Ledger's cooling-water estimate is a Monte Carlo over independent uniform parameter ranges (model 1.3,
`waterledger_models.datacenter.physics.RANGES`, `TOPUP` and `STAFF`; sources in `docs/methods/methods-log.md`, entry of
Oct 30, 2026). Several of those ranges are derived from sourced inputs rather than published directly, and a few are
assumptions with no published value. This note apportions the variance of the model's outputs among the parameters, so
that the effort spent on better data goes to the parameters that move the answer.

## Model and outputs

The model is the package's own `physics.hourly_rates`, called with parameter arrays of shape (runs, 1) against hourly
weather, as Water Ledger's builders call it. For each run, hourly gallons per IT kWh are multiplied by the IT load
(100 MW of IT capacity times utilization) and summed by day. Three outputs are computed for each of the four designs
(dry closed loop, closed loop with evaporative assist, hybrid, cooling towers), in gallons per day per 100 MW of IT
capacity: the annual average consumed (evaporation, drift and loop top-ups), the annual average withdrawn (consumed plus
blowdown), and the peak-day withdrawn as the package defines it (the 90th percentile of annual maximum days,
`cooling.daily_stats`). The script checks its vectorized daily statistics against `cooling.daily_stats` for three random
parameter sets per design before it runs (relative tolerance 1e-9). The non-cooling term (staff water plus maintenance,
`physics.staff_water`) is analysed separately at 300 MW of IT capacity, withdrawn and consumed, in gallons per day.

The cooling analysis has 15 parameters: the 14 entries of `RANGES` and the loop top-up share `topup` (`TOPUP`, 1-5% of
the loop volume a year), which the package keeps outside `RANGES` and samples on its own stream; here every parameter is
an independent uniform over its range. The non-cooling analysis has the seven `STAFF` parameters. Every parameter enters
every design's analysis; parameters a design does not use (for example `hybrid_on` for cooling towers) return indices
of exactly zero, which serves as a check on the estimators. The parameter list and ranges are read from the package at
run time, so the analysis can be rerun unchanged after a range or the physics is revised (the assist design's
`assist_on`, `assist_share` and drift handling are under review).

Weather is the repository's stored test weather: ERA5 hourly 2 m temperature and relative humidity at 42.88 N, 85.52 W
(West Michigan), 2023-2024, 17,544 hours (Hersbach et al., 2020; via the Open-Meteo archive). Wet-bulb temperature is
the package's Stull (2011) approximation. Dry-bulb temperature exceeded 21 °C for 1,569 hours a year, 27 °C for 364,
32 °C for 18.5, with a maximum of 33.9 °C. The repository holds no hotter climate's hourly weather, so the analysis is
for West Michigan only.

## Method

Variance-based indices (Sobol', 1993, 2001; Homma and Saltelli, 1996) were estimated with the radial sampling design of
Saltelli et al. (2010): two independent N x k matrices A and B of uniform draws, and k matrices AB_i equal to A with
column i taken from B, giving N(k + 2) model runs. The first-order index S1_i (the share of output variance explained
by parameter i alone) used the estimator of Saltelli et al. (2010, Table 2, (b)),
V_i = (1/N) sum f(B)[f(AB_i) - f(A)]; the total index ST_i (the share explained by i including all its interactions)
used Jansen's (1999) estimator, V_Ti = (1/2N) sum [f(A) - f(AB_i)]^2 (Saltelli et al., 2010, Table 2, (f)). Both are
divided by the variance of the pooled f(A) and f(B). Outputs were centred on the pooled mean before estimation, which
leaves the indices unchanged in expectation but removes a component of the S1 estimator's sampling error that grows with
the output's mean (towers withdraw about 660,000 gal/day per 100 MW with a standard deviation of about 106,000). Ninety-
five percent intervals are percentiles of 1,000 bootstrap resamples of the N rows (Archer et al., 1997).

Elementary effects (Morris, 1991) were computed as a screening check on the variance-based ranking: r = 100 random
one-at-a-time trajectories on a four-level grid with step 2/3 of each range, giving r(k + 1) runs. The trajectories
were not selected for spread (the selection procedure of Campolongo et al., 2007, was not used).
The summary statistics are mu* (the mean absolute elementary effect; Campolongo et al., 2007) and sigma (the standard
deviation of the effects, an indicator of non-linearity and interaction), both in output units per full parameter
range, and mu*/sd(output) for comparison across outputs.

Sample sizes: N = 8,192 for the cooling model (139,264 runs per design, plus 1,600 Morris runs; 563,456 runs over the
four designs) and N = 32,768 for the non-cooling term (294,912 runs, plus 800 Morris runs). Seeds are fixed (`SEED = 20261030`). The full run
takes about three minutes on a laptop (177 s on a 14-core Apple machine, numpy 2.5.4).

**Convergence.** Indices were recomputed on nested subsamples of N/8, N/4 and N/2 rows (`convergence.csv`). Between
N = 4,096 and N = 8,192 the largest change in any cooling index was 0.029 (S1) and 0.026 (ST), and the largest
bootstrap half-width at N = 8,192 was 0.031; for the non-cooling term the largest changes between N = 4,096 and
N = 32,768 were 0.030 and 0.012, with half-widths of 0.010 or less. Every index lies in [0, 1] within 0.03, the sum of
S1 is between 0.92 and 1.01 for every output, and ST is at least S1 within 0.002 for every parameter. The smallest S1 is
-0.0002. The leading three parameters by mu* match those by ST, in order, for every output but one: for non-cooling
consumption mu* puts `staff_maint_per_mw` just ahead of `staff_maint_used` (mu* 512 and 500; ST 0.34 and 0.38) and
`staff_used` just ahead of `staff_gpcd`, whose ST values tie at 0.099.

## Results

Means and standard deviations are over the pooled A and B samples (16,384 runs; 65,536 for the non-cooling term).
Indices are shown as ST [95% interval] (S1).

| Design | Output | Mean (sd), gal/day | First | Second | Third |
|---|---|---|---|---|---|
| Towers | Consumed, average | 516,900 (75,300) | utilization 0.85 [0.82, 0.87] (0.84) | er_adj 0.15 [0.15, 0.16] (0.14) | hf_econ 0.01 (0.01) |
| Towers | Withdrawn, average | 657,300 (106,400) | utilization 0.69 [0.67, 0.71] (0.68) | coc 0.18 [0.18, 0.19] (0.17) | er_adj 0.12 [0.12, 0.13] (0.11) |
| Towers | Withdrawn, peak day | 801,300 (128,900) | utilization 0.70 [0.68, 0.72] (0.69) | coc 0.19 [0.18, 0.19] (0.18) | er_adj 0.10 [0.10, 0.10] (0.09) |
| Hybrid | Consumed, average | 23,700 (10,800) | hybrid_on 0.86 [0.84, 0.88] (0.85) | utilization 0.10 [0.10, 0.11] (0.09) | hybrid_full 0.05 [0.05, 0.06] (0.05) |
| Hybrid | Withdrawn, average | 30,000 (13,800) | hybrid_on 0.84 [0.82, 0.87] (0.83) | utilization 0.10 [0.10, 0.11] (0.08) | hybrid_full 0.05 [0.05, 0.05] (0.04) |
| Hybrid | Withdrawn, peak day | 383,900 (85,300) | hybrid_on 0.43 [0.42, 0.44] (0.43) | utilization 0.38 [0.36, 0.39] (0.36) | coc 0.10 [0.09, 0.10] (0.09) |
| Assist | Consumed, average | 1,020 (880) | assist_on 0.91 [0.88, 0.94] (0.81) | assist_share 0.13 [0.13, 0.14] (0.07) | utilization 0.04 [0.04, 0.04] (0.02) |
| Assist | Withdrawn, average | 1,250 (1,110) | assist_on 0.91 [0.88, 0.94] (0.81) | assist_share 0.14 [0.13, 0.15] (0.08) | utilization 0.04 [0.03, 0.04] (0.02) |
| Assist | Withdrawn, peak day | 45,200 (23,100) | assist_on 0.63 [0.60, 0.65] (0.54) | assist_share 0.33 [0.32, 0.35] (0.28) | utilization 0.08 [0.08, 0.09] (0.07) |
| Dry | Consumed = withdrawn, average and peak | 57 (34) | fill_gal_per_mw 0.59 [0.57, 0.61] (0.50) | topup 0.50 [0.48, 0.52] (0.42) | none (all others 0) |
| Non-cooling, 300 MW | Withdrawn | 6,900 (2,000) | maint_per_mw 0.62 [0.61, 0.63] (0.62) | gpcd 0.15 [0.15, 0.16] (0.15) | per_mw 0.13 [0.13, 0.13] (0.12) |
| Non-cooling, 300 MW | Consumed | 650 (260) | maint_used 0.38 [0.37, 0.39] (0.34) | maint_per_mw 0.34 [0.33, 0.35] (0.30) | gpcd 0.10 [0.10, 0.10] (0.09) |

Total indices of the derived and assumed cooling parameters, by design and output (consumed average / withdrawn average /
withdrawn peak day):

| Parameter | Status (methods log, model 1.3) | Towers | Hybrid | Assist |
|---|---|---|---|---|
| utilization | sourced range over measured and modelled ratios that are not all the same quantity | 0.85 / 0.69 / 0.70 | 0.10 / 0.10 / 0.38 | 0.04 / 0.04 / 0.08 |
| er_adj | sourced error band, asymmetry a judgment | 0.15 / 0.12 / 0.10 | 0.01 / 0.01 / 0.05 | 0.00 / 0.00 / 0.01 |
| hf_econ | derived | 0.007 / 0.006 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| hf_chiller | derived | 0.004 / 0.003 / 0.023 | 0.003 / 0.003 / 0.012 | 0.001 / 0.001 / 0.002 |
| wb_econ | derived | 0.001 / 0.001 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| wb_chiller | derived | 0.002 / 0.001 / 0.000 | 0.000 / 0.000 / 0.001 | 0.000 / 0.000 / 0.001 |
| hybrid_on | sourced setpoint range, narrowed | | 0.86 / 0.84 / 0.43 | |
| hybrid_full | assumption, no published value | | 0.05 / 0.05 / 0.07 | |
| assist_on | sourced from a different design | | | 0.91 / 0.91 / 0.63 |
| assist_share | assumption, no published value | | | 0.13 / 0.14 / 0.33 |

Cycles of concentration (`coc`) affects only blowdown, so it has no effect on consumption and accounts for 0.18-0.19 of
tower withdrawal variance. Drift, tower range, loop volume and top-ups have total indices below 0.01 for every wet
design. The sums of ST exceed the sums of S1 by at most 0.19 (assist; 0.16 for dry); the model is close to additive for towers
(at most 0.03) and hybrids (at most 0.04).

## Interpretation

**Cooling towers.** Utilization explains 70-85% of the variance. It scales IT energy, so it matters in proportion to
the result; it is a property of the campus's load rather than of the cooling physics, and it drops out when a site's
expected IT load, rather than its IT capacity, is known. Where an estimate starts from announced capacity, a better
utilization range is the most valuable improvement for towers. The evaporative ratio adjustment is second for consumption
(ST 0.15): Rutberg et al.'s relation is applied here outside its fit conditions, and the asymmetric -0.10 to +0.05 range
is a judgment from the USGS error bands. A direct check of the relation against metered tower makeup and blowdown at a
data center in a cold climate would narrow it. Cycles of concentration are second for withdrawal; where an applicant
states them or water chemistry and discharge limits constrain them, they are better taken from the site than from a
range. The four
derived heat-factor and economizer parameters (hf_econ, hf_chiller, wb_econ, wb_chiller) together explain about 1% of
annual tower water and about 2% of the peak day (hf_chiller, the chiller-mode heat factor). Their derived ranges are
adequate for this model; more precise values would not change the estimates materially.

**Hybrid.** The temperature at which the dry coolers switch to wet operation (`hybrid_on`) explains 85% of the variance
of the hybrid's annual water and 43% of its peak day. Its range (21-28 °C) is narrower than its source, a patent that
lets the operator set the switch point anywhere from 21 to 35 °C. The index would likely be larger with the source's
full range; that was not run, because a switch point above `hybrid_full` (30-33 °C) would invert the model's ramp. Because the switch point is an operating choice rather than an uncertain physical quantity, it is better treated
as a design input, taken from the applicant's specification where one exists and shown as a scenario where it does not,
than as part of the uncertainty band. The assumed full-evaporation temperature (`hybrid_full`, no published value)
explains 5-7% and is a low priority. On the peak day the hybrid is wet for part of the day (its peak is about half the towers'), and utilization (0.38) and
cycles of concentration (0.10) matter as they do for towers.

**Closed loop with evaporative assist.** The assist start temperature explains 91% of the variance of annual assist
water and 63% of its peak day; the assist share explains 13-14% and 33%. The model's annual assist water is set by
where the start temperature falls in the upper tail of the temperature distribution: in this weather, 27 °C is exceeded
364 hours a year and 32 °C 18.5 hours. Neither parameter has a source for this design: the start temperature comes from
Microsoft's direct-air evaporative design, a different system, and the share has no published value. These are the two
parameters with the largest indices that rest on assumption. Operator water use effectiveness for closed-loop campuses
with assist, or applicant specifications of the assist setpoint and capacity, would constrain both. The absolute
amounts are small on average (about 1,000 gal/day per 100 MW) but the peak day is about 45,000 gal/day per 100 MW, so
the assumption matters for peak-day utility capacity more than for annual totals. Drift in the assist design is applied
at the full circulating rate in every hour with any assist; its total index is below 0.01 for every assist output, so a
revision of that treatment will not change this ranking.

**Dry closed loop.** Only the loop volume per MW and the annual top-up share act (ST 0.59 and 0.50; their product
gives an interaction of about 0.08). Utilization cancels because top-ups are per MW of capacity, not per kWh. The 1%
top-up floor is an assumption; the amounts are very small (mean 57 gal/day per 100 MW).

**Non-cooling water.** Maintenance water per MW explains 62% of non-cooling withdrawal at 300 MW; for consumption, the maintenance share used
up and maintenance water per MW lead (ST 0.38 and 0.34). Both are bracketed by applicants' projections rather than measured,
so metered non-cooling use at an operating campus is the most useful single datum for this term. Gallons per person and
people per MW follow (0.15 and 0.13 of withdrawal).

**Which parameters most need better data.** In order of their effect on the published estimates: utilization (towers
and hybrid peaks; a load question, not a cooling question), the hybrid switch temperature (better handled as an
applicant input), the assist start temperature and assist share (unsourced for this design and dominant for it), the
evaporative ratio adjustment (towers), and maintenance water per MW (non-cooling). The derived parameters hf_econ,
hf_chiller, wb_econ and wb_chiller do not need further work for this model at its present resolution, and neither do
drift, tower range or loop top-ups for the wet designs.

## Limitations

The indices are conditional on the ranges and on independent uniform distributions; a different range changes the
apportionment, which is why the hybrid switch temperature's narrowed range matters. Only one climate was analysed:
in a hotter climate more hours exceed the hybrid and assist setpoints, so the setpoints would likely explain less of the
variance and utilization and the evaporative ratio more, which has not been tested. With two years of weather, the
"1-in-10-year" peak day is the 90th percentile of two annual maxima, close to the hotter year's record day, not a
1-in-10-year statistic. Year-to-year weather variability is not treated as an uncertain input. The indices describe the
model, not the real systems: a structural error in the model (for example, applying a tower evaporation relation to
adiabatic pads in the assist and hybrid designs) is not visible to a parameter sensitivity analysis.

## Reproduction

    python docs/methods/sensitivity/sensitivity.py            # about 3 minutes; writes the CSVs and run_info.json here
    python docs/methods/sensitivity/sensitivity.py --quick    # N = 512, about 12 s, prints only, for checking the script

The script imports `waterledger_models` from this checkout's `packages/waterledger-models/src` and needs only numpy.
`run_info.json` records the model version, code commit, seeds, sample sizes, parameter ranges, runtime and any sanity
warnings. Columns: `sobol_indices.csv` has design, output, parameter, range, S1 and ST with their 2.5 and 97.5
percentile bounds; `morris.csv` has mu, mu*, sigma, mu*/sd and the mu* rank; `convergence.csv` has the largest change
in S1 and ST from the full-sample values, and the sums, at each nested subsample size; `output_summary.csv` has each
output's mean, standard deviation, 10th, 50th and 90th percentiles and the sums of S1 and ST.

## References

Archer, G.E.B., Saltelli, A., and Sobol', I.M. (1997). Sensitivity measures, ANOVA-like techniques and the use of
bootstrap. Journal of Statistical Computation and Simulation, 58(2), 99-120. https://doi.org/10.1080/00949659708811825

Campolongo, F., Cariboni, J., and Saltelli, A. (2007). An effective screening design for sensitivity analysis of large
models. Environmental Modelling and Software, 22(10), 1509-1518. https://doi.org/10.1016/j.envsoft.2006.10.004

Hersbach, H., Bell, B., Berrisford, P., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal
Meteorological Society, 146(730), 1999-2049. https://doi.org/10.1002/qj.3803

Homma, T., and Saltelli, A. (1996). Importance measures in global sensitivity analysis of nonlinear models. Reliability
Engineering and System Safety, 52(1), 1-17. https://doi.org/10.1016/0951-8320(96)00002-6

Jansen, M.J.W. (1999). Analysis of variance designs for model output. Computer Physics Communications, 117(1-2), 35-43.
https://doi.org/10.1016/S0010-4655(98)00154-4

Morris, M.D. (1991). Factorial sampling plans for preliminary computational experiments. Technometrics, 33(2), 161-174.
https://doi.org/10.1080/00401706.1991.10484804

Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M., and Tarantola, S. (2010). Variance based sensitivity
analysis of model output. Design and estimator for the total sensitivity index. Computer Physics Communications, 181(2),
259-270. https://doi.org/10.1016/j.cpc.2009.09.018

Sobol', I.M. (1993). Sensitivity estimates for nonlinear mathematical models. Mathematical Modeling and Computational
Experiment, 1(4), 407-414.

Sobol', I.M. (2001). Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates.
Mathematics and Computers in Simulation, 55(1-3), 271-280. https://doi.org/10.1016/S0378-4754(00)00270-6

Stull, R. (2011). Wet-bulb temperature from relative humidity and air temperature. Journal of Applied Meteorology and
Climatology, 50(11), 2267-2269. https://doi.org/10.1175/JAMC-D-11-0143.1

Parameter sources (EPRI 2026, IEA 2025, LBNL 2024, Lei and Masanet 2022, DOE FEMP, Rutberg et al. 2011, USGS SIR
2013-5188, EPA, NIH 2023, US Patent 12,426,214 B1 and the applicant projections behind the non-cooling term) are cited in
`docs/methods/methods-log.md` (Oct 30, 2026, model 1.3) and in the comments of
`packages/waterledger-models/src/waterledger_models/datacenter/physics.py`.
