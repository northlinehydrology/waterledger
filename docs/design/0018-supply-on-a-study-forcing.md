# 0018: Solar and wind on a study's own forcing (AORC)

Status: **proposed Nov 16, 2026, for Andrew; nothing built.** Branch `supply-on-aorc`. Builds on 0014 (power supply
scenarios). 0015-0017 are taken on other branches, so this is 0018.

## Why

Andrew's rule (Nov 14-15): in a coupled study every model runs on the study's one weather forcing; Water Ledger's ERA5
weather is for the calculator only. The Clam River study runs SWAT+, MODFLOW 6 and Basin Ledger on the NWM v3
retrospective forcing (AORC), and wants solar and wind beside its grid, grid-plus-gas and islanded-on-gas cases. The supply
models take what ERA5 gives and AORC does not:

| | ERA5 path today | AORC gives |
|---|---|---|
| PV radiation | global and direct horizontal, preceding-hour means (`pv.output`) | downward shortwave only (global horizontal) |
| PV cell temperature wind | 100 m, taken to 10 m by a 1/7 power law [A] | 10 m, U and V |
| Wind | 100 m U and V, taken to the 110 m hub by alpha 0.10-0.20 (`wind.hourly`) | 10 m, U and V |

So AORC needs a split of global horizontal radiation into beam and diffuse, and a way from 10 m to the hub. This note
proposes both, the checks, the API and the parameters. The ERA5 path does not change by a bit.

## What AORC's radiation and wind are

From the AORC v1.1 methods (NWS OWP, Oct 2021, section 4.2): the downward shortwave and the 10 m wind components are
NLDAS-2's 1-hour, 12 km fields, bilinearly interpolated to the 1 km grid, over the whole record. Temperature, humidity,
pressure and longwave were replaced by URMA from 2016; shortwave and wind were not. NLDAS-2's shortwave is NARR's (32 km,
3-hourly), bias-corrected against GOES-based surface radiation (Pinker et al. 2003; 1996-2000) and spread to hours; its
wind is NARR's 10 m wind (Xia et al. 2012; Cosgrove et al. 2003). Four consequences:

1. **The hourly variability of AORC's shortwave is mostly synthetic below three hours.** A split model that reads
   hour-to-hour changes (DIRINT's stability index) sees a smoothed series. The split has to be checked on AORC's own
   radiation, not only on measured radiation.
2. **Its time stamp is not ERA5's.** On a July day at the Clam River (2024, 44.3 N, 85.4 W) morning and evening hours
   mirror each other about solar noon only if each value is centred on its time stamp, not a mean over the preceding hour
   as ERA5's is (one day only; preliminary). Taking ERA5's convention would put the sun 30 minutes off. The time shift
   is to be fitted over a year (check A1), not assumed.
3. **AORC's 10 m wind is a model diagnostic** (NARR's surface layer at 32 km), not a measured 10 m wind. The study finds
   it 30-50% above Cadillac airport's anemometer and drifting lower after 2014 (STUDY.md, section 3.1; weather_correction.py).
   Its shear to the hub is as much NARR's as the atmosphere's, so the level has to come from a check against output, not
   from a tower's exponent alone.
4. **The ERA5 resource factors do not carry over.** `pv.RANGES["resource"]` (0.76-0.92) and `wind.RANGES["resource"]`
   (0.93-1.05) hold ERA5's own bias against EIA's fleet (0014, check 5). AORC's shortwave runs 10-16% above the
   Gaylord pyranometer at the Clam River (the study's weather_correction.py), and its wind 30-50% above the airport's. The
   AORC path needs its own factors from the same EIA check on AORC.

## 1. Splitting global horizontal radiation

**Proposed: DIRINT** (Perez et al. 1992, ASHRAE Transactions 98(1):354-369), as pvlib implements it
(`pvlib.irradiance.dirint`), **with DISC (Maxwell 1987, SERI/TR-215-3087) and Erbs (Erbs et al. 1982, Solar Energy
28:293-302) run beside it in the check**, and the one used chosen by check A2.

- DIRINT is DISC (clearness index and air mass to beam normal) with a correction from Perez's 6 x 6 x 7 x 5 coefficient
  table by the hour's clearness, the zenith, the dew point (AORC has specific humidity and pressure) and the change in
  clearness to the hours before and after. Ineichen (2008, Solar Energy 82:501-512) found it the best of three against
  ground stations, at about 2% bias and 28% scatter in beam normal on 10-minute data (as reported; the hourly figures to be
  read from the paper). Erbs gives diffuse fraction from clearness alone and is usually the worst of the classic models in
  comparisons (Gueymard and Ruiz-Arias 2016, Solar Energy 128:1-30, UNVERIFIED in this session).
- Newer models (Engerer2, BRL, Yang4) beat DIRINT on 1-minute measured data, but they lean harder on short-term
  variability that AORC does not have, and pvlib does not carry all of them as a test reference. Not proposed [A].
- **Why the check decides, not the papers:** published errors are for measured radiation. On AORC's smoothed hours the
  stability index may hurt more than help; if DISC does as well on AORC at the stations, it is simpler and is used.
- **What matters is the tracker's plane of array, not beam normal.** On a single-axis tracker much of a misplaced beam
  comes back as sky diffuse through Hay and Davies, so the PV error is smaller than the beam error. The check scores
  annual and hourly plane-of-array irradiance and PV output.
- **Energy balance:** beam horizontal + diffuse horizontal = global horizontal every hour, exactly (beam is clipped to
  [0, global], and beam normal to below the extraterrestrial); a test holds it.
- Numpy only, as `pv.py` is. The DIRINT coefficient table comes from pvlib (BSD-3-Clause, cited as the turbine curve's
  source is), and tests hold the split to `pvlib.irradiance.dirint` / `disc` / `erbs` hour by hour.

## 2. From 10 m to the hub

**Proposed: a day and a night power-law exponent, each sampled, 10 m straight to the 110 m hub.**

`speed_hub = |(u10, v10)| x resource x (110 / 10)^alpha`, with `alpha = alpha_day` while the sun is up at the hour and
`alpha_night` otherwise [A: the switch at the horizon].

- **One exponent can't carry the hours.** The shear from 10 m changes with stability every day. ERA5's own 10 m and 100 m
  wind at the Clam River cell (44.25_-85.25, 2019-2021, computed for this note) give a 10-100 m exponent of 0.15-0.18 at
  midday and 0.27-0.31 at night in every season, 0.24 on the means. Over 10 m to 110 m that is a factor of 1.4-1.5 on the
  speed by day and about 2.0 by night, and through the power curve, which is steep below rated, a large share of the
  energy. One exponent would put the wrong hours under the load, which is what hourly matching and the islanded case read.
- **The literature supports more than 1/7 and a strong day-night swing over the Midwest's open land.** Schwartz and
  Elliott (2006, NREL/CP-500-40019): 13 tall towers in the central plains, top anemometers near 100-110 m, a diurnal
  shear pattern alike across the region and annual shear varying more between towers than between regions. NREL's Indiana
  and Iowa towers (2008, NREL/PO-500-43150): average exponents from 1/7 to 0.25 or more. Night values in those studies
  and the per-class exponents of Irwin (1979, Atmospheric Environment 13:191-194; rural D 0.15, E 0.35, F 0.55) bracket
  ERA5's.
- **Proposed ranges** [A]: `alpha_day` 0.12-0.20, `alpha_night` 0.22-0.40, around ERA5's 0.16 and 0.29 at the Clam
  cell and inside the tower literature. The tables from the two NREL papers are to be read before the ranges are fixed.
- **The level comes from the resource factor; the shape from the exponents.** As on ERA5, a factor on the speed is set
  where the AORC chain meets EIA's fleet (check A3), at central exponents. Check A4 tests the day-night shape against
  EIA-930's hourly wind in MISO.
- **Not proposed, unless check A4 fails:** a stability class each hour from AORC's own fields (Turner's method from the
  sun's elevation, the wind and cloud read from downward longwave; Irwin's exponents), or an exponent falling with the
  night's wind speed (ERA5 at the Clam cell: 0.32 under 3 m/s, 0.24 at 5-8 m/s). Each adds parameters with weaker sources.
- **Alternative for Andrew (decision 2):** set the exponents by month and hour at the place from ERA5's own 10 m and
  100 m wind (a 12 x 24 table). The hours stay AORC's; ERA5 only sets a parameter, as it already sets the resource
  factors. It is place-specific and captures the season, but brings ERA5's surface layer into a study on AORC, and
  ERA5's 10 m wind is not AORC's.
- **Energy balance:** no turbine hour may exceed the Betz limit at the hour's air density (16/27 x 1/2 rho A v^3, rho
  from AORC's temperature and pressure); a test holds the power curve and losses under it. No density correction of the
  curve [A], as on the ERA5 path, so the two stay comparable.

## 3. Checks

Each a script in `docs/methods/power_supply/`, aggregates only (0014's scope rule), results in the methods log. Nothing
tuned except the resource factors, which are what the checks are for.

- **A1, AORC's time stamp.** Over 2024 at the Clam River point and the check's plant points: the shift (in 15-minute
  steps) that best centres clear-ish days' radiation on the computed solar noon. The AORC entry takes that shift.
- **A2, the split at measuring stations.** SURFRAD stations in or near the Midwest (Bondville IL, Penn State PA, Sioux
  Falls SD; NOAA GML; one year, hourly means of the measured global, beam and diffuse). Two ways: Erbs, DISC and DIRINT on
  the station's measured global (the split's own error), and on AORC's global at the station (the whole AORC path).
  Scored on beam normal and on the tracker's plane of array and PV output, annual and hourly bias and scatter. Picks the
  split.
- **A3, AORC against EIA's fleet** (0014 check 5, the same plants, year and screens as `pv_check.py` and `wind_check.py`,
  2024): the AORC chain at each plant's 1 km point, state ratios and the resource factor that matches each state.
  Gives the AORC ranges. Cost: AORC's zarr chunks are 144 hours x 128 x 256 points, about 1.3-2.2 MB of shortwave and
  0.7-0.8 MB of each wind component a chunk. The 953 PV and 1,076 wind plants fall in 249 spatial chunks, about 45 GB of
  reads for the year; the interior and Great Lakes states alone (274 PV, 740 wind plants, 138 chunks) about 24 GB.
  Fetched once into the power work cache, apart from everything else.
- **A4, the day-night shape.** EIA-930's hourly wind generation for MISO in 2024, normalized by its mean, against the
  modeled MISO fleet (A3's MISO plants, summed): mean diurnal shape by season, and hourly correlation, for the ERA5 path
  and the AORC path. 0014's check 5 named this check and it was not built, so it serves both paths.
- **A5, AORC against ERA5** at the Clam River's points and A3's plant points: radiation, PV output and wind output by
  month and hour, and the AORC-to-ERA5 ratio of 10 m wind by year over 2000-2022 at the Clam River (the study's drift
  after 2014, against a reference that isn't AORC).

## 4. API

New entry points beside the old ones, named by what they take, not by the forcing. The ERA5 functions keep their
signatures and their numbers.

```python
pv.decompose(g, ghi, method="dirint", dew_point=None)            # beam horizontal, W/m2, on a geometry()
pv.geometry(times_utc, lat, lon, mount, tilt, shift_s=-1800)       # new keyword; -1800 (ERA5's preceding hour) the default
pv.output_from_ghi(g, ghi, temp_air, wind_10m, p, dew_point=None)  # decompose, then the same chain as output()
pv.hourly_from_ghi(times_utc, lat, lon, ghi, temp_air, wind_10m, p, mount="tracking", tilt=None, shift_s=..., dew_point=None)
pv.RANGES_AORC                                                   # RANGES with AORC's resource factor

wind.hourly_from_10m(times_utc, lat, lon, u10, v10, p)            # day and night exponents, 10 m to HUB_M
wind.RANGES_AORC                                                 # alpha_day, alpha_night, losses, resource
```

- `pv.output` becomes the ERA5 wrapper of a shared core that takes the 10 m wind: it multiplies by (10/100)^(1/7)
  exactly as now and calls the core, so the operations, and the numbers, are the same.
- **Identity test:** the ERA5 `pv.hourly`, `pv.output`, `wind.hourly` and a `scenario.Supply` run on fixed inputs equal
  values saved from main (f370fcc) to the bit; `tests/test_supply.py`'s pvlib tests unchanged.
- `scenario.Supply` and `size` stay on ERA5 (decision 4 asks whether to widen them). The Clam River study composes its
  plants itself (Basin Ledger), so it would call the two `hourly_from_` functions on its catchments' hourly forcing.
- The `RANGES_AORC` factors hold for AORC as published. A forcing corrected to stations, or another forcing, needs its own
  check A3; the docstrings say so.

## 5. Parameters on the AORC path

| Parameter | Range | Set from |
|---|---|---|
| PV `losses`, `gamma`, `ilr`, `albedo` | as `pv.RANGES` | the same sources (Dobos 2014; [A] as there) |
| PV `resource` | from check A3 | AORC's PV chain against EIA's 2024 tracking fleet, the spread over states with ten or more plants, as on ERA5 |
| PV split | none sampled [A] | its bias is inside the resource factor; check A2 reports its share |
| PV time shift | fixed | check A1 |
| Wind `alpha_day` | 0.12-0.20 [A] | the tall-tower literature; ERA5 at the Clam cell 0.15-0.18 |
| Wind `alpha_night` | 0.22-0.40 [A] | the same; ERA5 0.27-0.31; Irwin's E class 0.35 |
| Wind `losses` | 0.10-0.20 | as `wind.RANGES` |
| Wind `resource` | from check A3 | AORC's wind chain against EIA's 2024 fleet at 110 m, as on ERA5 |
| `LOW_WIND_MS` flag | from check A3 | the AORC 10 m mean speed under which the chain runs far low, if there is one |

Sampled by the same Latin hypercube as the ERA5 ranges, central values last.

## 6. Version

No existing number changes, so `MODEL_VERSION` stays; the new functions and ranges are public API in the release that
carries them, a minor package release. Proposed: **waterledger-models 3.25.0, after 3.24.0**, which goes out tomorrow
without waiting for this. Nothing touches the 3.24.0 branches' files (checked Nov 16: no other branch changes `supply/`).

## Order of work, each step its own commit

1. The split (`decompose`, Erbs, DISC, DIRINT) and the `shift_s` keyword, held to pvlib; the shared PV core; the identity
   test.
2. Checks A1 and A2 (AORC's time stamp; SURFRAD); the split chosen.
3. `wind.hourly_from_10m`, `pv.hourly_from_ghi`; balance and Betz tests.
4. Check A3 (AORC against EIA's fleet; the fetch), A4 (EIA-930 MISO), A5 (AORC against ERA5); the AORC ranges set.
5. README, the supply docstrings, the methods log, CHANGELOG; a release on Andrew's word.

## Decisions for Andrew

1. **The split:** DIRINT, with DISC and Erbs beside it and the one used chosen by check A2 on AORC at SURFRAD stations.
2. **The shear:** a sampled day and night exponent, 10 m to the hub (proposed); or a month-by-hour table set from ERA5's
   own 10 m and 100 m wind at the place.
3. **Check A3's reach:** all of EIA's 2024 plants, comparable with the ERA5 tables (about 45 GB of AORC reads), or the
   interior and Great Lakes states only (about 24 GB). Plus SURFRAD (three stations, one year, a few hundred MB) and
   EIA-930 (MISO, 2024).
4. **`scenario.Supply` and `size`:** stay on ERA5 (proposed; the study composes its own), or take the AORC weather too.
5. **The release:** 3.25.0 after 3.24.0 (proposed).

## References

- Cosgrove, B. A., et al. (2003). Real-time and retrospective forcing in the North American Land Data Assimilation System
  (NLDAS) project. J. Geophys. Res. 108(D22):8842.
- Erbs, D. G., Klein, S. A., and Duffie, J. A. (1982). Estimation of the diffuse radiation fraction for hourly, daily and
  monthly-average global radiation. Solar Energy 28(4):293-302.
- Fall, G., et al. (2023). The Office of Water Prediction's Analysis of Record for Calibration, version 1.1: Dataset
  description and precipitation evaluation. JAWRA, doi:10.1111/1752-1688.13143.
- Gueymard, C. A., and Ruiz-Arias, J. A. (2016). Extensive worldwide validation and climate sensitivity analysis of direct
  irradiance predictions from 1-min global irradiance. Solar Energy 128:1-30.
- Ineichen, P. (2008). Comparison and validation of three global-to-beam irradiance models against ground measurements.
  Solar Energy 82(6):501-512.
- Irwin, J. S. (1979). A theoretical variation of the wind profile power-law exponent as a function of surface roughness
  and stability. Atmospheric Environment 13:191-194.
- Maxwell, E. L. (1987). A quasi-physical model for converting hourly global horizontal to direct normal insolation.
  SERI/TR-215-3087.
- NREL (2008). Wind Shear and Resources at Elevated Heights: Indiana and Iowa Case Studies. NREL/PO-500-43150.
- NWS Office of Water Prediction (2021). AORC v1.1 methods.
- Perez, R., Ineichen, P., Maxwell, E., Seals, R., and Zelenka, A. (1992). Dynamic global-to-direct irradiance conversion
  models. ASHRAE Transactions 98(1):354-369.
- Pinker, R. T., et al. (2003). Surface radiation budgets in support of the GEWEX Continental-Scale International Project
  (GCIP) and the GEWEX Americas Prediction Project (GAPP). J. Geophys. Res. 108(D22):8844.
- Schwartz, M., and Elliott, D. (2006). Wind Shear Characteristics at Central Plains Tall Towers. NREL/CP-500-40019.
- Xia, Y., et al. (2012). Continental-scale water and energy flux analysis and validation for the North American Land Data
  Assimilation System project phase 2 (NLDAS-2). J. Geophys. Res. 117:D03109.
