# 0018: Solar and wind on a study's own forcing (AORC)

Status: **decided Nov 16, 2026 (Andrew; decisions 1-6 below); built on branch `supply-on-aorc` (checks A1-A5 done, Nov 16); not released.**
Branch `supply-on-aorc`. Builds on 0014 (power supply scenarios). 0015-0017 are taken on other branches, so this is 0018.
Fuel cells as data centers use them, added to this work the same day, are in the companion note 0019.

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

**First agreed: DIRINT; chosen after check A2: Erbs** (decision 1). DIRINT (Perez et al. 1992, ASHRAE Transactions 98(1):354-369), as pvlib implements it
(`pvlib.irradiance.dirint`), **with DISC (Maxwell 1987, SERI/TR-215-3087) and Erbs (Erbs et al. 1982, Solar Energy
28:293-302) run beside it in the check**, and the one used chosen by check A2.

- **Practice it is held to** (Andrew asked that it go against no norm): PVsyst, the usual tool for bankable estimates,
  splits with Erbs by default (as reported in pvlib's and Sandia's comparisons); NREL's NSRDB took cloudy-sky beam from
  DISC through PSM v3 and from FARMS-DNI from v4 (2023), its 2024 validation finding DISC better in scattered cloud and
  FARMS-DNI in overcast. Both of the industry's choices are in check A2, scored on the same footing; if DIRINT does not
  clearly beat them on AORC, DISC is used, as NREL's national dataset did [A: "clearly" is a smaller plane-of-array
  error over all three stations].

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

**Agreed (Andrew, Nov 16): an exponent for each month and hour of the day, set at the place from ERA5's own 10 m and
100 m wind.** The hours stay AORC's; ERA5 sets a parameter, as it already sets the resource factors.

`speed_hub = |(u10, v10)| x resource x (110 / 10)^(alpha[month, hour] x shear_scale)`

- `alpha[month, hour]` = ln(mean |U100| / mean |U10|) / ln 10 over the hours of that calendar month and local solar
  hour in ERA5 at the place's cell, 1995-2024 (the calculator's 30 years) [A: the ratio of means, so calm hours don't
  blow it up]. A 12 x 24 table, worked once per place by `wind.shear_table` from the two ERA5 series; the study passes
  the table, so the ERA5 fetch stays outside the coupled run.
- The table's exponent is taken on to 110 m [A: ERA5 gives nothing above 100 m; at 0.24 the last 10 m adds 2% to the
  speed].
- `shear_scale` 0.85-1.15, sampled [A], for ERA5's own shear error; check A4 narrows or widens it.

The reasons for an hourly exponent, and the sources, as first proposed:

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
- **The tower literature is the check on the table**, not its source: the two NREL papers' tables are read, and the
  table's day and night values at their towers' cells compared.
- **The level comes from the resource factor; the shape from the exponents.** As on ERA5, a factor on the speed is set
  where the AORC chain meets EIA's fleet (check A3), at central exponents. Check A4 tests the day-night shape against
  EIA-930's hourly wind in MISO.
- **Not proposed, unless check A4 fails:** a stability class each hour from AORC's own fields (Turner's method from the
  sun's elevation, the wind and cloud read from downward longwave; Irwin's exponents), or an exponent falling with the
  night's wind speed (ERA5 at the Clam cell: 0.32 under 3 m/s, 0.24 at 5-8 m/s). Each adds parameters with weaker sources.
- **The first proposal, not taken:** a sampled day and a night exponent (0.12-0.20 and 0.22-0.40) from the tower
  literature. The table is place-specific and carries the season; it brings ERA5's surface layer into a study on AORC,
  and ERA5's 10 m wind is not AORC's, which check A5 shows.
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
  Gives the AORC ranges. The shear table at each plant comes from ERA5's 10 m and 100 m wind at its cell (the 100 m
  already cached by `wind_check.py` for 2024; 1995-2024 for the table). Agreed: all of EIA's 2024 plants. Cost: AORC's zarr chunks are 144 hours x 128 x 256 points, about 1.3-2.2 MB of shortwave and
  0.7-0.8 MB of each wind component a chunk. The 953 PV and 1,076 wind plants fall in 249 spatial chunks, about 45 GB of
  reads for the year; the interior and Great Lakes states alone (274 PV, 740 wind plants, 138 chunks) about 24 GB.
  Fetched once into the power work cache, apart from everything else.
- **A4, the day-night shape.** EIA-930's hourly wind generation for MISO in 2024, normalized by its mean, against the
  modeled MISO fleet (A3's MISO plants, summed): mean diurnal shape by season, and hourly correlation, for the ERA5 path
  and the AORC path. 0014's check 5 named this check and it was not built, so it serves both paths.
- **A5, AORC against ERA5** at the Clam River's points and A3's plant points: radiation, PV output and wind output by
  month and hour, and the AORC-to-ERA5 ratio of 10 m wind by year over 2000-2022 at the Clam River (the study's drift
  after 2014, against a reference that isn't AORC).

## Found in checks A3 and A4 (Nov 16)

**A3, PV** (`docs/methods/power_supply/aorc_check.py`, `aorc_pv_check.csv`, `aorc_pv_check_monthly.csv`): EIA's 2024 tracking fleet, the
same 944 plants (56 GW AC) and screens as `pv_check.py`, against `pv.hourly_from_ghi` on AORC at each plant's 1 km point (Erbs, shift 0, the
plant's own ILR, central parameters, resource 1.0), with each plant's 2024 curtailment added back as `pv_check.py` does since Nov 17
(`curtailment.py`: a scenario's dispatch counts curtailment itself). The chain gives 27.6% where the fleet would have delivered 24.8% (24.1%
delivered): the factor that matches is 0.89 overall (ERA5's 0.86), 0.82 in the Great Lakes states (ERA5's 0.81) and 0.90 in Michigan (0.89),
none of which curtail. Across the 15 states with ten or more plants it is 0.73-1.03 (median 0.88; ERA5's 0.75-0.94), New York to Nevada:
AORC runs closer to the fleet in the Southwest (Colorado 0.99, Nevada 1.03, against ERA5's 0.87 and 0.94) and alike elsewhere, so its spread
is wider, as check A2's scatter said it would be. So `pv.RANGES_AORC` is `pv.RANGES` with resource 0.73-1.03 (on delivered output, Nov 16,
it was 0.87 overall and 0.73-1.02; `aorc_pv_check_delivered.csv`). By month the Great Lakes' January is 0.52 (snow on the panels, which the
factor holds, as on ERA5). The wind half of A3 was not run (decision 6).

**A4, the hours** (`wind_shape_check.py`, `wind_shape_check.csv`): EIA-930's MISO wind, 2024, against the ERA5 path at the 250 MISO
plants of the check (31 GW), each at its own hub and summed by nameplate. Hourly correlation 0.949. The night (00-05 CST) over the day
(10-15) is 1.10-1.29 by season against the fleet's 1.01-1.24, so the path runs 4-9% too strong at night against midday; the largest
gap in any hour of the seasonal mean is 5-16%. The fixed alpha 0.15 from 100 m to the hub carries little of the day's cycle, so the
cycle is ERA5's own at 100 m. Accepted as it is; `wind.RANGES`' alpha (0.10-0.20) stays.

## Found in check A5 (Nov 16): AORC's 10 m wind breaks in 2018

AORC's 10 m wind steps down against ERA5's between 2017 and 2018 (`docs/methods/power_supply/aorc_drift.py`, `aorc_drift.csv`,
`aorc_wind_break.csv`). At the Clam River the ratio of mean speeds is 1.31-1.45 in every year 2000-2017 and 0.67-0.82 in 2018-2022, so
the AORC path's wind capacity factor there falls from 0.44-0.51 to 0.14-0.23 while the ERA5 path's stays at 0.25-0.30. Over 2015-2020 the
same step shows at Bondville (1.07-1.10 to 0.76-0.97), Penn State (1.66-1.68 to 0.70-0.86), Sioux Falls (1.13-1.15 to 0.90-1.00) and central
Iowa (1.12-1.14 to 0.71-0.76), not on the Texas plains (0.98-1.04 throughout), and it recovers partly by 2020 at some. AORC's shortwave shows
no step (0.98-1.06 against ERA5 every year at the Clam River). AORC v1.1 keeps NLDAS-2's wind through the record (methods, sec. 4.2), and
NLDAS-2's is NARR's diagnostic 10 m wind; no documented change was found. The Clam River study saw its forcing's wind fall against the
Cadillac airport's "after 2014" (STUDY.md, 3.1); this is likely the same step. **Confirmed by a measured wind (the Clam River session,
Nov 16; the study's AUDIT.md, "The forcing's wind steps down on January 1, 2018"):** the study's forcing, basin mean, over the Cadillac
airport anemometer (ISD 72638414817, daily means) is 1.47-1.58 every water year 2005-2017 and 0.90-1.16 in 2018-2022; by month 1.48-1.99
through December 2017, 1.09 in January 2018 and 0.89-1.06 after, while the airport's own wind holds at 3.0-3.3 m/s. A step on New Year's
Day is a seam in the dataset, not the weather.

So no one resource factor serves AORC's wind over a record that crosses 2018, and the step differs by place, so neither does one factor a
period. Check A3's factor (2024) holds for 2018 on. Decision 6 asks what the study's wind runs on.

## 4. API

New entry points beside the old ones, named by what they take, not by the forcing. The ERA5 functions keep their
signatures and their numbers.

```python
pv.decompose(g, ghi, method="dirint", dew_point=None)            # beam horizontal, W/m2, on a geometry()
pv.geometry(times_utc, lat, lon, mount, tilt, shift_s=-1800)       # new keyword; -1800 (ERA5's preceding hour) the default
pv.output_from_ghi(g, ghi, temp_air, wind_10m, p, dew_point=None)  # decompose, then the same chain as output()
pv.hourly_from_ghi(times_utc, lat, lon, ghi, temp_air, wind_10m, p, mount="tracking", tilt=None, shift_s=..., dew_point=None)
pv.RANGES_AORC                                                   # RANGES with AORC's resource factor

wind.shear_table(times_utc, lon, u10, v10, u100, v100)            # 12 x 24 exponents from ERA5 at the place
wind.hourly_from_10m(times_utc, lon, u10, v10, table, p)           # the table, 10 m to HUB_M
```

(`wind.RANGES_AORC` was proposed and not set: decision 6.)

- `pv.output` becomes the ERA5 wrapper of a shared core that takes the 10 m wind: it multiplies by (10/100)^(1/7)
  exactly as now and calls the core, so the operations, and the numbers, are the same.
- **Identity test:** the ERA5 `pv.hourly`, `pv.output`, `wind.hourly` and a `scenario.Supply` run on fixed inputs equal
  values saved from main (f370fcc) to the bit; `tests/test_supply.py`'s pvlib tests unchanged.
- `scenario.Supply` and `size` take either ERA5's tuple, as before, or `scenario.ForcingWeather(utc, ghi, wind_10m, u100, v100)`
  (decision 4): PV by `pv.output_from_ghi` on the forcing with `pv.RANGES_AORC` sampled, wind by `wind.hourly` on ERA5's 100 m wind
  (decision 6), the runner's temperature for both. So a study on AORC gets the grid, grid-plus-gas and islanded cases, their sizing,
  unserved hours and water, from the same tested runner; `tests/test_scenarios.py` holds its capacity factors to the functions' own.
- The `RANGES_AORC` factors hold for AORC as published. A forcing corrected to stations, or another forcing, needs its own
  check A3; the docstrings say so.

## 5. Parameters on the AORC path

| Parameter | Range | Set from |
|---|---|---|
| PV `losses`, `gamma`, `ilr`, `albedo` | as `pv.RANGES` | the same sources (Dobos 2014; [A] as there) |
| PV `resource` | 0.73-1.03 (check A3) | AORC's PV chain against EIA's 2024 tracking fleet, the spread over states with ten or more plants, as on ERA5 |
| PV split | none sampled [A] | its bias is inside the resource factor; check A2 reports its share |
| PV time shift | fixed | check A1 |
| Wind shear table | set, per place | ERA5's 10 m and 100 m wind at the place's cell, 1995-2024 (Clam cell: 0.15-0.18 midday, 0.27-0.31 night) |
| Wind `shear_scale` | not set (decision 6) | a study on AORC runs wind on ERA5 |
| Wind `losses`, `resource`, `LOW_WIND_MS` | not set (decision 6) | the ERA5 path's (`wind.RANGES`, `wind.LOW_WIND_MS`) |

Sampled by the same Latin hypercube as the ERA5 ranges, central values last.

## 6. Version

No existing number changes, so `MODEL_VERSION` stays; the new functions and ranges are public API in the release that
carries them, a minor package release: **3.24.0 if done by then, else 3.25.0** (decision 5); 3.24.0 does not wait. Nothing touches the 3.24.0 branches' files (checked Nov 16: no other branch changes `supply/`).

## Order of work, each step its own commit

1. The split (`decompose`, Erbs, DISC, DIRINT) and the `shift_s` keyword, held to pvlib; the shared PV core; the identity
   test.
2. Checks A1 and A2 (AORC's time stamp; SURFRAD); the split chosen.
3. `wind.hourly_from_10m`, `pv.hourly_from_ghi`; balance and Betz tests.
4. Check A3 (AORC against EIA's fleet; the fetch), A4 (EIA-930 MISO), A5 (AORC against ERA5); the AORC ranges set.
5. README, the supply docstrings, the methods log, CHANGELOG; a release on Andrew's word.

## Decisions (Andrew, Nov 16, 2026)

1. **The split: DIRINT**, with DISC and Erbs beside it and the one used chosen by check A2 on AORC at SURFRAD stations.
   Agreed, "unless there are industry or academic norms for this that we would be going against or not using properly":
   PVsyst's Erbs and the NSRDB's DISC are in the check (section 1).
   **Check A2 (Nov 16) and the choice: Erbs.** On AORC's global at Bondville, Penn State and Sioux Falls (2024), Erbs had the
   smallest hourly PV scatter (41.1-44.3% against DIRINT's 41.4-45.0% and DISC's 42.1-45.5%), the smallest daily scatter and the
   smallest annual bias (+3.0 to +7.1%) at all three; on measured radiation DIRINT was best (annual PV bias -0.3 to -0.8%). The
   rule as written would have fallen to DISC, last on AORC. Andrew: "yes, let's do the industry norm": Erbs, PVsyst's default,
   is `pv.AORC_SPLIT`; DIRINT and DISC stay as options. Also from A2: AORC's own global scatters more than ERA5's against the
   stations (daily 26-31% against 20-22%, correlation 0.89-0.90 against 0.94-0.95; annual biases alike), so PV on AORC is
   rougher hour by hour and day by day than the calculator's.
2. **The shear: a month-by-hour table from ERA5's 10 m and 100 m wind at the place.** Andrew chose it over the sampled
   day and night exponents.
3. **Check A3: all of EIA's 2024 plants** (about 45 GB of AORC reads), with SURFRAD (three stations, one year) and
   EIA-930 (MISO, 2024). Agreed, downloads included.
4. **`scenario.Supply` and `size` take a study's forcing** (Andrew, Nov 16: "lets do b"), narrowly: a `ForcingWeather` in place of
   ERA5's tuple runs PV on the forcing and wind on ERA5 (decision 6); the ERA5 tuple's numbers are unchanged. The alternative, the study
   writing its own sizing and dispatch around the `hourly_from_` functions, would have kept two copies of that logic, one untested.
5. **The release:** 3.25.0 after 3.24.0, or in 3.24.0 if done by then; "fine to split".
6. **Wind on ERA5's 100 m wind, the calculator's path, as a stated exception to the one-forcing rule** (Andrew, Nov 16: "run wind
   on ERA5 100 m and state the exception"). AORC's 10 m wind is not one series over 2000-2022 (above), and no factor fixes a step that
   differs by place; ERA5's 100 m path is homogeneous and checked against EIA's fleet (0014, check 5). A study on AORC runs PV on its own
   forcing (`pv.hourly_from_ghi`) and wind on ERA5 at the place's cell (`waterledger_data.era5.fetch_supply`, `era5.supply`,
   `wind.hourly`), aligned on UTC hours, and says so. `wind.hourly_from_10m` and `shear_table` stay for a forcing whose 10 m wind is
   homogeneous, with no ranges set for AORC; check A3 runs for PV only, and A4 checks the ERA5 path's hours.

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
- NREL (2024). Integrating FARMS-DNI into the NSRDB (NREL/TP, fy24osti/87671); NSRDB release notes, v4.0.0 (May 2023).
- Sengupta, M., et al. (2018). The National Solar Radiation Data Base (NSRDB). Renewable and Sustainable Energy Reviews
  89:51-60.
- Schwartz, M., and Elliott, D. (2006). Wind Shear Characteristics at Central Plains Tall Towers. NREL/CP-500-40019.
- Xia, Y., et al. (2012). Continental-scale water and energy flux analysis and validation for the North American Land Data
  Assimilation System project phase 2 (NLDAS-2). J. Geophys. Res. 117:D03109.
