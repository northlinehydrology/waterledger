# Global sensitivity analysis of the data center water model (model 1.3)

Oct 30, 2026. Code: `sensitivity.py` in this folder. Results: `sobol_indices.csv`, `morris.csv`, `convergence.csv`,
`output_summary.csv`, `run_info.json`.

## Purpose

Water Ledger's cooling-water estimate is a Monte Carlo over independent uniform parameter ranges (model 1.3,
`waterledger_models.datacenter.physics.RANGES`, `TOPUP`, `ADIABATIC` and `STAFF`; sources in `docs/methods/methods-log.md`, entry of
Oct 30, 2026). Several of those ranges are derived from sourced inputs rather than published directly, and a few are
assumptions with no published value. This note apportions the variance of the model's outputs among the parameters, so
that the effort spent on better data goes to the parameters that move the answer.

## Model and outputs

The model is the package's own `physics.hourly_rates`, called with parameter arrays of shape (runs, 1) against hourly
weather, as Water Ledger's builders call it. For each run, hourly gallons per IT kWh are multiplied by the IT load
(100 MW of IT capacity times utilization) and summed by day. Three outputs are computed for each of the four designs
(dry closed loop, dry coolers with adiabatic pre-cooling or "assist", hybrid, cooling towers), in gallons per day per 100 MW of IT
capacity: the annual average consumed (evaporation, drift and loop top-ups), the annual average withdrawn (consumed plus
blowdown), and the peak-day withdrawn as the package defines it (the 90th percentile of annual maximum days,
`cooling.daily_stats`). The script checks its vectorized daily statistics against `cooling.daily_stats` for three random
parameter sets per design before it runs (relative tolerance 1e-9). The non-cooling term (staff water plus maintenance,
`physics.staff_water`) is analysed separately at 300 MW of IT capacity, withdrawn and consumed, in gallons per day.

The cooling analysis has 17 parameters, those of `physics.PARAMETERS`: the 14 entries of `RANGES`, the loop top-up share
`topup` (`TOPUP`, 1-5% of the loop volume a year) and the two entries of `ADIABATIC` (`assist_dt_air`, `assist_bleed`).
The package samples `topup` and `ADIABATIC` on their own streams; here every parameter is an independent uniform over its
range on one design. The non-cooling analysis has the seven `STAFF` parameters. Every parameter enters every design's
analysis; parameters a design does not use (for example `hybrid_on` for cooling towers) return indices of exactly zero,
which serves as a check on the estimators. The parameter list and ranges are read from the package at run time, so the
analysis can be rerun unchanged after a range or the physics is revised. This run is on the assist design as revised on
Oct 30, 2026: dry coolers with adiabatic pre-cooling, whose water share of the heat is d / (on + rise - T + d), with
d = `assist_eff` x wet-bulb depression, no drift, and bleed as a share of evaporation.

Weather is the repository's stored test weather: ERA5 hourly 2 m temperature and relative humidity at 42.88 N, 85.52 W
(West Michigan), 2023-2024, 17,544 hours (Hersbach et al., 2020; via the Open-Meteo archive). Wet-bulb temperature is
the package's Stull (2011) approximation. Dry-bulb temperature reached 20 °C for 1,896 hours a year, 21 °C for about
1,600, 27 °C for about 375 and 30 °C for 90, with a maximum of 33.9 °C. The repository holds no hotter climate's hourly weather, so the analysis is
for West Michigan only.

## Method

Variance-based indices (Sobol', 1990, 2001; Homma and Saltelli, 1996) were estimated with the radial sampling design of
Saltelli et al. (2010): two independent N x k matrices A and B of uniform draws, and k matrices AB_i equal to A with
column i taken from B, giving N(k + 2) model runs. The first-order index S1_i (the share of output variance explained
by parameter i alone) used the estimator of Saltelli et al. (2010),
V_i = (1/N) sum f(B)[f(AB_i) - f(A)]; the total index ST_i (the share explained by i including all its interactions)
used Jansen's (1999) estimator, V_Ti = (1/2N) sum [f(A) - f(AB_i)]^2. Both are
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

Sample sizes: N = 8,192 for the cooling model (155,648 runs per design, plus 1,800 Morris runs; 629,792 runs over the
four designs) and N = 32,768 for the non-cooling term (294,912 runs, plus 800 Morris runs). Seeds are fixed
(`SEED = 20261030`). The full run takes about three minutes on a laptop (198 s on a 14-core Apple machine, numpy 2.5.4).

**Convergence.** Indices were recomputed on nested subsamples of N/8, N/4 and N/2 rows (`convergence.csv`). Between
N = 4,096 and N = 8,192 the largest change in any cooling index was 0.012 (S1) and 0.019 (ST), and the largest
bootstrap half-width at N = 8,192 was 0.026; for the non-cooling term the largest changes between N = 4,096 and
N = 32,768 were 0.014 and 0.007, with half-widths of 0.011 or less. Every index lies in [0, 1] within 0.03 (the smallest
S1 is -0.0004), the sum of S1 is between 0.93 and 0.99 for every output, and ST is at least S1 within 0.004 for every
parameter. The leading three parameters by mu* match those by ST, in order, for every output but two: on the hybrid's
peak day mu* puts utilization just ahead of `hybrid_on` (mu* 180,800 and 180,300; ST 0.36 and 0.42), and for non-cooling
consumption mu* ranks `staff_gpcd` third where ST ranks `staff_used`, whose ST values are 0.099 and 0.100.

## Results

Means and standard deviations are over the pooled A and B samples (16,384 runs; 65,536 for the non-cooling term).
Indices are shown as ST [95% interval] (S1).

| Design | Output | Mean (sd), gal/day | First | Second | Third |
|---|---|---|---|---|---|
| Towers | Consumed, average | 517,700 (75,600) | utilization 0.82 [0.80, 0.85] (0.82) | er_adj 0.15 [0.15, 0.16] (0.15) | hf_econ 0.01 [0.01, 0.01] (0.01) |
| Towers | Withdrawn, average | 658,600 (106,800) | utilization 0.67 [0.65, 0.69] (0.67) | coc 0.19 [0.18, 0.20] (0.17) | er_adj 0.12 [0.12, 0.13] (0.12) |
| Towers | Withdrawn, peak day | 802,700 (129,200) | utilization 0.68 [0.66, 0.70] (0.68) | coc 0.19 [0.19, 0.20] (0.18) | er_adj 0.10 [0.10, 0.10] (0.10) |
| Hybrid | Consumed, average | 23,700 (10,800) | hybrid_on 0.85 [0.83, 0.87] (0.84) | utilization 0.10 [0.09, 0.10] (0.08) | hybrid_full 0.05 [0.05, 0.05] (0.05) |
| Hybrid | Withdrawn, average | 30,000 (13,900) | hybrid_on 0.83 [0.81, 0.85] (0.81) | utilization 0.10 [0.09, 0.10] (0.08) | hybrid_full 0.05 [0.05, 0.05] (0.05) |
| Hybrid | Withdrawn, peak day | 384,400 (85,800) | hybrid_on 0.42 [0.41, 0.44] (0.41) | utilization 0.36 [0.35, 0.37] (0.35) | coc 0.10 [0.10, 0.10] (0.09) |
| Assist | Consumed, average | 26,700 (18,600) | assist_on 0.93 [0.91, 0.96] (0.91) | utilization 0.05 [0.05, 0.06] (0.04) | assist_dt_air 0.03 [0.03, 0.03] (0.02) |
| Assist | Withdrawn, average | 33,300 (23,600) | assist_on 0.91 [0.89, 0.94] (0.87) | utilization 0.05 [0.05, 0.06] (0.04) | assist_bleed 0.04 [0.04, 0.04] (0.03) |
| Assist | Withdrawn, peak day | 341,900 (127,800) | assist_on 0.72 [0.70, 0.75] (0.69) | utilization 0.14 [0.14, 0.15] (0.12) | assist_bleed 0.10 [0.10, 0.11] (0.09) |
| Dry | Consumed = withdrawn, average and peak | 58 (34) | fill_gal_per_mw 0.57 [0.55, 0.59] (0.50) | topup 0.49 [0.47, 0.51] (0.43) | none (all others 0) |
| Non-cooling, 300 MW | Withdrawn | 6,900 (2,000) | maint_per_mw 0.62 [0.61, 0.63] (0.62) | gpcd 0.15 [0.15, 0.16] (0.14) | per_mw 0.13 [0.13, 0.13] (0.12) |
| Non-cooling, 300 MW | Consumed | 650 (260) | maint_used 0.39 [0.38, 0.39] (0.33) | maint_per_mw 0.35 [0.34, 0.35] (0.30) | used 0.10 [0.10, 0.10] (0.09) |

Total indices of the derived and assumed cooling parameters, by design and output (consumed average / withdrawn average /
withdrawn peak day):

| Parameter | Status (methods log, model 1.3) | Towers | Hybrid | Assist |
|---|---|---|---|---|
| utilization | sourced range over measured and modelled ratios that are not all the same quantity | 0.82 / 0.67 / 0.68 | 0.10 / 0.10 / 0.36 | 0.05 / 0.05 / 0.14 |
| er_adj | sourced error band, asymmetry a judgment | 0.15 / 0.12 / 0.10 | 0.01 / 0.01 / 0.05 | not used |
| hf_econ | derived | 0.007 / 0.006 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| hf_chiller | derived | 0.004 / 0.003 / 0.023 | 0.003 / 0.003 / 0.011 | 0.001 / 0.001 / 0.004 |
| wb_econ | derived | 0.001 / 0.001 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| wb_chiller | derived | 0.002 / 0.001 / 0.000 | 0.000 / 0.000 / 0.001 | 0.000 / 0.000 / 0.001 |
| hybrid_on | sourced setpoint range, narrowed | | 0.85 / 0.83 / 0.42 | |
| hybrid_full | assumption, no published value | | 0.05 / 0.05 / 0.07 | |
| assist_on | operator setting, no published typical value [A]; 20 °C from Uptime Institute (2025), 30 °C top assumed | | | 0.93 / 0.91 / 0.72 |
| assist_eff | measured (EVAPCO 2018, 72-78%) | | | 0.001 / 0.001 / 0.001 |
| assist_dt_air | makers' selection sheets [estimate] | | | 0.03 / 0.03 / 0.05 |
| assist_bleed | depends on pad type: none once-through, up to 0.5 recirculating (SCE 2015) | | | 0.00 / 0.04 / 0.10 |

Cycles of concentration (`coc`) affects only blowdown, so it has no effect on consumption and accounts for 0.19 of tower
withdrawal variance; the assist design's bleed takes its place there. Drift, tower range, loop volume and top-ups have
total indices below 0.01 for every wet design. The sums of ST exceed the sums of S1 by at most 0.14 (non-cooling
consumption; 0.12 for dry, 0.08 for assist); the model is close to additive for towers (at most 0.03) and hybrids (at
most 0.04).

## Interpretation

**Cooling towers.** Utilization explains 67-82% of the variance. It scales IT energy, so it matters in proportion to
the result; it is a property of the campus's load rather than of the cooling physics, and it drops out when a site's
expected IT load, rather than its IT capacity, is known. Where an estimate starts from announced capacity, a better
utilization range is the most valuable improvement for towers. The evaporative ratio adjustment is second for consumption
(ST 0.15): Rutberg et al.'s relation is applied here outside its fit conditions, and the asymmetric -0.10 to +0.05 range
is a judgment from the USGS error bands. A direct check of the relation against metered tower makeup and blowdown at a
data center in a cold climate would narrow it. Cycles of concentration are second for withdrawal; where an applicant
states them or water chemistry and discharge limits constrain them, they are better taken from the site than from a
range. The four derived heat-factor and economizer parameters (hf_econ, hf_chiller, wb_econ, wb_chiller) together explain
about 1% of annual tower water and about 2% of the peak day (hf_chiller, the chiller-mode heat factor). Their derived
ranges are adequate for this model; more precise values would not change the estimates materially.

**Hybrid.** The temperature at which the dry coolers switch to wet operation (`hybrid_on`) explains 83-85% of the
variance of the hybrid's annual water and 42% of its peak day. Its range (21-28 °C) is narrower than its source, a patent
that lets the operator set the switch point anywhere from 21 to 35 °C. The index would likely be larger with the
source's full range; that was not run, because a switch point above `hybrid_full` (30-33 °C) would invert the model's
ramp. Because the switch point is an operating choice rather than an uncertain physical quantity, it is better treated
as a design input, taken from the applicant's specification where one exists and shown as a scenario where it does not,
than as part of the uncertainty band. The assumed full-evaporation temperature (`hybrid_full`, no published value)
explains 5-7% and is a low priority. On the peak day the hybrid is wet for part of the day (its peak is about half the
towers'), and utilization (0.36) and cycles of concentration (0.10) matter as they do for towers.

**Dry coolers with adiabatic pre-cooling (assist).** The switch temperature explains 91-93% of the variance of annual
assist water and 72% of its peak day. With the other parameters at their middle values, annual consumption runs from
about 63,800 gal/day per 100 MW with the switch at 20 °C to 23,400 at 25 °C and 3,150 at 30 °C; dry-bulb temperature
reaches 20 °C for 1,896 hours a year and 30 °C for 90. `assist_on` is an operator setting with no published typical
value [A]: no maker publishes one, since it is a selection and control output, and the range runs from the 20 °C that
Uptime Institute (2025) reports to an assumed top of 30 °C. Like the hybrid's switch point, it is better taken from an
applicant's specification or shown as a scenario than carried as uncertainty. The other assist parameters matter much
less. Pad effectiveness, measured at 72-78% by EVAPCO (2018), has a total index of 0.001 because its measured range is
narrow (0.70 to 0.80 moves annual consumption from about 22,500 to 24,200 gal/day), and it needs no further work. The
coil air temperature rise, from makers' selection sheets [estimate], has ST 0.03-0.05 (9 to 13 K moves consumption from
about 27,300 to 20,500 gal/day). Bleed depends on pad type, none for once-through pads and up to half of evaporation
for recirculating ones; it has no effect on consumption, but it explains 0.04 of annual withdrawal and 0.10 of the peak
day, and pad type is a specification an applicant can state. Utilization is second for all three outputs (0.05-0.14).
The design's water is similar to the hybrid's (mean consumption about 26,700 against 23,700 gal/day, peak day about
342,000 against 384,000), which is expected for similar technology, and no operator has published water use for an
adiabatic dry cooler site to check it against. In the model, water starts as a step at the switch point: the evaporated
share is about 0.3 of the heat in the first degree above it, at middle values. At the corner of the ranges with the
lowest switch temperature and air rise and the highest effectiveness, the share reaches its cap of 1 for about 160
hours a year.

**Dry closed loop.** Only the loop volume per MW and the annual top-up share act (ST 0.57 and 0.49; their product
gives an interaction of about 0.06-0.07). Utilization cancels because top-ups are per MW of capacity, not per kWh. The 1%
top-up floor is an assumption; the amounts are very small (mean 58 gal/day per 100 MW).

**Non-cooling water.** Maintenance water per MW explains 62% of non-cooling withdrawal at 300 MW; for consumption, the
maintenance share used up and maintenance water per MW lead (ST 0.39 and 0.35). Both are bracketed by applicants'
projections rather than measured, so metered non-cooling use at an operating campus is the most useful single datum for
this term. Gallons per person and people per MW follow (0.15 and 0.13 of withdrawal).

**Which parameters most need better data.** In order of their effect on the published estimates: utilization (towers
and hybrid peaks; a load question, not a cooling question), the hybrid and assist switch temperatures (operating
choices, better handled as applicant inputs), the evaporative ratio adjustment (towers) and maintenance water per MW
(non-cooling). Pad type, which sets `assist_bleed`, matters for assist withdrawal and is a specification to ask for. The
derived parameters hf_econ, hf_chiller, wb_econ and wb_chiller do not need further work for this model at its present
resolution, and neither do `assist_eff`, drift, tower range or loop top-ups for the wet designs.

## Limitations

The indices are conditional on the ranges and on independent uniform distributions; a different range changes the
apportionment, which is why the hybrid switch temperature's narrowed range matters. Only one climate was analysed:
in a hotter climate more hours exceed the hybrid and assist setpoints, so the setpoints would likely explain less of the
variance and utilization (and, for towers and hybrids, the evaporative ratio) more, which has not been tested. With two years of weather, the
"1-in-10-year" peak day is the 90th percentile of two annual maxima, close to the hotter year's record day, not a
1-in-10-year statistic. Year-to-year weather variability is not treated as an uncertain input. The indices describe the
model, not the real systems: a structural error in the model (for example, applying a tower evaporation relation to
adiabatic pads in the hybrid design, or the assist design's step at its switch point) is not visible to a parameter
sensitivity analysis.

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

Sobol', I.M. (1990). On sensitivity estimation for nonlinear mathematical models. Matematicheskoe Modelirovanie, 2(1),
112-118 (in Russian). English translation: Mathematical Modeling and Computational Experiment, 1(4), 407-414 (1993).

Sobol', I.M. (2001). Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates.
Mathematics and Computers in Simulation, 55(1-3), 271-280. https://doi.org/10.1016/S0378-4754(00)00270-6

Stull, R. (2011). Wet-bulb temperature from relative humidity and air temperature. Journal of Applied Meteorology and
Climatology, 50(11), 2267-2269. https://doi.org/10.1175/JAMC-D-11-0143.1

Parameter sources (EPRI 2026, IEA 2025, LBNL 2024, Lei and Masanet, DOE FEMP, Rutberg et al. 2011, USGS SIR 2013-5188, EPA,
NIH 2023, US Patent 12,426,214 B1, EVAPCO 2018, ASHRAE 2016, Uptime Institute 2025, SCE ET13SCE1020 and the applicant projections behind the non-cooling term) are cited in
`docs/methods/methods-log.md` (Oct 30, 2026, model 1.3) and in the comments of
`packages/waterledger-models/src/waterledger_models/datacenter/physics.py`.
