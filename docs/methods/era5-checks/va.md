# ERA5 check: VA

**PASS** (2026-11-07; model 1.9; design 0005's leave-one-station-out check; 34 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 22 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.43 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.16 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.18 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.45 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.45 vs 1.07 | yes | the reason to correct |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 3.20 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 0.98 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 4.60 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.16 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (18) | uncorrected | 0.68 (+0.21) | 0.24 (-0.10) | 0.46 (+0.13) | 0.21 (+0.22) |
| land cells, corrected (18) | decided | 0.32 (+0.10) | 0.17 (-0.02) | 0.35 (+0.08) | 0.27 (-0.03) |
| land cells, no station (4) | uncorrected | 1.20 (-1.33) | 0.58 (-0.47) | 0.97 (-1.10) | 0.27 (-0.07) |
| shore cells, corrected (12) | uncorrected | 1.07 (-1.16) | 0.41 (-0.29) | 0.44 (-0.60) | 0.24 (+0.45) |
| shore cells, corrected (12) | decided | 0.45 (+0.01) | 0.52 (+0.26) | 0.22 (+0.15) | 0.42 (-0.05) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Nwpt News/Wimburg Intl Apt, VA | isd-linked | 0.51 | -0.52 | Langley Afb Airport 22 km, Norfolk Nas 40 km, Norfolk International Airport 47 km, Oceana Nas 64 km |
| Oceana Nas, VA | isd | 0.51 | +0.18 | Norfolk International Airport 24 km, Norfolk Nas 33 km, Langley Afb Airport 49 km, Elz Cty Cg/Air Stn Rgnl Ap 57 km |
| Naval Air Station, MD | isd | 0.55 | -0.11 | Andrews Air Force Base Airport 71 km, Quantico Mcaf 76 km, Salbry-Ocn Cty Wico Rgnl Ap 87 km, Wallops Flight Facility Airport 97 km |
| Wallops Flight Facility Airport, VA | isd | 0.58 | +1.18 | Salbry-Ocn Cty Wico Rgnl Ap 38 km, Sussex County Airport 78 km, Naval Air Station 87 km |
| Elz Cty Cg/Air Stn Rgnl Ap, NC | isd-linked | 0.67 | +0.30 | Oceana Nas 66 km, Norfolk International Airport 73 km, Norfolk Nas 76 km, Langley Afb Airport 93 km |
| Norfolk Nas, VA | isd | 0.67 | -0.38 | Nwpt News/Wimburg Intl Apt 15 km, Langley Afb Airport 16 km, Norfolk International Airport 29 km, Oceana Nas 46 km |
| Langley Afb Airport, VA | isd-linked | 0.67 | +0.57 | Nwpt News/Wimburg Intl Apt 15 km, Norfolk Nas 20 km, Norfolk International Airport 29 km, Oceana Nas 46 km |
| Sussex County Airport, DE | isd-linked | 0.68 | -0.21 | Salbry-Ocn Cty Wico Rgnl Ap 51 km, Wallops Flight Facility Airport 92 km |
| Norfolk International Airport, VA | isd | 0.77 | -0.30 | Oceana Nas 21 km, Norfolk Nas 21 km, Langley Afb Airport 38 km, Nwpt News/Wimburg Intl Apt 48 km |
| Salbry-Ocn Cty Wico Rgnl Ap, MD | isd-linked | 0.82 | -0.65 | Wallops Flight Facility Airport 35 km, Sussex County Airport 50 km, Naval Air Station 80 km |
| Quantico Mcaf, VA | isd | 0.87 | +0.78 | Andrews Air Force Base Airport 48 km, Naval Air Station 76 km |
| Andrews Air Force Base Airport, MD | isd-linked | 0.89 | -0.69 | Quantico Mcaf 55 km, Naval Air Station 58 km |
| Davison Aaf Airport, VA | isd-linked | 0.94 | -0.55 | Ronald Reagan Washington Natl Ap 22 km, Washington Dulles International Ap 27 km, Baltimore-Washington Intl Airport 68 km, Etrn Wv Rgnl/Shpherd Fd Ap 96 km |
| Baltimore-Washington Intl Airport, MD | isd | 0.94 | -0.34 | Ronald Reagan Washington Natl Ap 51 km, Washington Dulles International Ap 70 km, Davison Aaf Airport 70 km, York Airport 75 km |
| Ronald Reagan Washington Natl Ap, VA | isd | 0.94 | +0.30 | Davison Aaf Airport 16 km, Washington Dulles International Ap 44 km, Baltimore-Washington Intl Airport 54 km |
| Raleigh-Durham International Ap, NC | isd | 0.95 | -0.62 | Rocky Mount-Wilson Rgn Apt 79 km, Danville Regional Airport 82 km |
| Richmond International Airport, VA | isd | 0.97 | -0.30 | no land station within 100 km |
| Raleigh County Memorial Airport, WV | isd | 0.99 | +1.18 | Mercer County Airport 53 km |
| Tri-Cities Regional Tn/Va Airport, TN | isd-linked | 0.99 | -1.50 | no land station within 100 km |
| Piedmont Triad International Airport, NC | isd | 0.99 | +0.25 | Smith Reynolds Airport 25 km, Danville Regional Airport 87 km |
| Washington Dulles International Ap, VA | isd | 0.99 | +0.14 | Davison Aaf Airport 42 km, Ronald Reagan Washington Natl Ap 44 km, Etrn Wv Rgnl/Shpherd Fd Ap 61 km, Baltimore-Washington Intl Airport 73 km |
| Danville Regional Airport, VA | isd-linked | 0.99 | +0.29 | Piedmont Triad International Airport 77 km, Raleigh-Durham International Ap 80 km, Lynchburg Rgnl/Preston Glenn Fld Ap 91 km, Smith Reynolds Airport 96 km |
| York Airport, PA | isd-linked | 0.99 | +0.71 | Hgrtwn Rgnl-R.Hnson Fld Ap 70 km, Baltimore-Washington Intl Airport 96 km |
| Rocky Mount-Wilson Rgn Apt, NC | isd-linked | 0.99 | +0.72 | Raleigh-Durham International Ap 72 km |
| Etrn Wv Rgnl/Shpherd Fd Ap, WV | isd | 1.00 | -0.01 | Hgrtwn Rgnl-R.Hnson Fld Ap 33 km, Washington Dulles International Ap 79 km |
| Smith Reynolds Airport, NC | isd-linked | 1.00 | +0.14 | Piedmont Triad International Airport 32 km, Danville Regional Airport 89 km |
| Ldon-Crbn Apt-Mgee Fld Apt, KY | isd | 1.00 | +0.10 | Julian Carroll Airport 89 km |
| Roanoke Regional/Woodrum Field Ap, VA | isd | 1.00 | -1.17 | Lynchburg Rgnl/Preston Glenn Fld Ap 71 km, Danville Regional Airport 96 km |
| Mercer County Airport, WV | isd-linked | 1.00 | -0.30 | Raleigh County Memorial Airport 60 km |
| Charlottesville Albemarle Arpt, VA | isd-linked | 1.00 | -0.90 | no land station within 100 km |
| Lynchburg Rgnl/Preston Glenn Fld Ap, VA | isd | 1.00 | +0.52 | Roanoke Regional/Woodrum Field Ap 64 km, Danville Regional Airport 76 km |
| Elkins-Rand Co-J.Rand Field Airport, WV | isd | 1.00 | -2.60 | no land station within 100 km |
| Hgrtwn Rgnl-R.Hnson Fld Ap, MD | isd-linked | 1.00 | -0.19 | Etrn Wv Rgnl/Shpherd Fd Ap 43 km, York Airport 77 km, Washington Dulles International Ap 94 km |
| Julian Carroll Airport, KY | isd-linked | 1.00 | +0.60 | Ldon-Crbn Apt-Mgee Fld Apt 86 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Virginia Beach city | Oceana Nas (4) | 0.51 | +0 | +1 | +3 | +3 | -1 | +0 |
| Norfolk city | Norfolk International Airport (5) | 0.77 | +0 | +1 | +2 | +5 | -2 | +3 |
| Newport News city | Nwpt News/Wimburg Intl Apt (7) | 0.67 | +0 | -1 | +0 | +4 | -9 | +2 |
| Chincoteague town | Wallops Flight Facility Airport (10) | 0.58 | -0 | +1 | -0 | +1 | +12 | +6 |
| Quantico town | Quantico Mcaf (2) | 0.87 | -0 | +0 | -9 | +2 | +1 | +3 |
| Henrico County | Richmond International Airport (8) | 0.97 | +0 | -0 | +0 | +2 | -5 | +2 |
| Charlottesville city | Charlottesville Albemarle Arpt (11) | 1.00 | -0 | -1 | -3 | -5 | -8 | -5 |
| Herndon town | Washington Dulles International Ap (6) | 0.99 | -0 | +1 | -4 | +4 | -5 | -0 |
| Occoquan town | Davison Aaf Airport (8) | 0.94 | -0 | +0 | +0 | +9 | -2 | +6 |
| Alexandria city | Ronald Reagan Washington Natl Ap (5) | 0.94 | -1 | -1 | -16 | -12 | -16 | -12 |
| Lynchburg city | Lynchburg Rgnl/Preston Glenn Fld Ap (9) | 0.99 | +0 | +1 | +5 | +10 | +8 | +8 |
| Danville city | Danville Regional Airport (7) | 1.00 | +0 | +1 | +9 | +11 | +8 | +13 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
