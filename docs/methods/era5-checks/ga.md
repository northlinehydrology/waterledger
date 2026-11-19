# ERA5 check: GA

**PASS** (2026-11-18; model 1.17; design 0005's leave-one-station-out check; 37 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 33 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.25 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.10 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.32 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.43 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.43 vs 1.55 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.04 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 0.18 | yes | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.06 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 3.95 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.47 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 0.14 | yes | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 4.47 | yes | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (30) | uncorrected | 0.43 (-0.26) | 0.18 (-0.04) | 0.26 (-0.16) | 0.27 (+0.07) |
| land cells, corrected (30) | decided | 0.24 (-0.05) | 0.29 (-0.09) | 0.15 (+0.08) | 0.36 (+0.05) |
| land cells, no station (3) | uncorrected | 0.50 (-0.53) | 0.34 (-0.27) | 0.30 (-0.33) | 0.16 (-0.12) |
| shore cells, corrected (3) | uncorrected | 1.55 (-1.35) | 0.67 (-0.52) | 0.66 (-0.59) | 0.23 (+0.09) |
| shore cells, corrected (3) | decided | 0.43 (-0.12) | 0.27 (-0.01) | 0.24 (+0.20) | 0.50 (+0.31) |
| shore cells, no shore station (1) | uncorrected | 0.80 (-0.80) | 0.49 (-0.49) | 0.77 (-0.77) | 0.03 (-0.03) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Mayport Naf, FL | isd | 0.63 | +0.43 | Craig Municipal Airport 18 km, Malcolm Mc Kinnon Airport 73 km |
| Craig Municipal Airport, FL | isd-linked | 0.69 | -0.77 | Mayport Naf 18 km |
| Malcolm Mc Kinnon Airport, GA | isd | 0.77 | -0.01 | Mayport Naf 95 km |
| Beaufort Mcas, SC | isd | 0.84 | -0.80 | no shore station within 100 km |
| Hunter Army Airfield, GA | isd-linked | 0.94 | -0.01 | Savannah/Hilton Head Intl Airport 15 km |
| Anderson Regional Airport, SC | isd-linked | 0.94 | -0.18 | Greenville Downtown Arpt 53 km, Greenville-Spartanburg Intl Airport 67 km, Athens/Ben Epps Airport 81 km |
| Jacksonville Nas, FL | isd | 0.94 | -0.79 | Jacksonville International Airport 28 km |
| Jacksonville International Airport, FL | isd | 0.94 | +0.55 | Jacksonville Nas 31 km |
| Mc Ghee Tyson Airport, TN | isd | 0.96 | -0.50 | no land station within 100 km |
| Lee Gilmer Memorial Arpt, GA | isd-linked | 0.97 | +1.04 | Athens/Ben Epps Airport 51 km, Dekalb-Peachtree Airport 65 km, Dobbins Air Reserve Base Airport 80 km, Fulton Co-Brown Fld Arpt 89 km |
| Tallahassee Regional Airport, FL | isd | 0.98 | +0.31 | Valdosta Regional Airport 98 km |
| Lovell Field Airport, TN | isd | 0.98 | -0.13 | Richard B Russell Airport 73 km |
| Dekalb-Peachtree Airport, GA | isd-linked | 0.98 | -0.39 | Dobbins Air Reserve Base Airport 26 km, Fulton Co-Brown Fld Arpt 35 km, Hartsfield-Jackson Atlanta Intl Ap 45 km, Lee Gilmer Memorial Arpt 49 km |
| Savannah/Hilton Head Intl Airport, GA | isd | 0.98 | +0.15 | Hunter Army Airfield 28 km |
| Daniel Field Airport, GA | isd-linked | 0.99 | -0.35 | Augusta Regional At Bush Field Ap 15 km |
| Dobbins Air Reserve Base Airport, GA | isd-linked | 0.99 | +0.23 | Dekalb-Peachtree Airport 23 km, Fulton Co-Brown Fld Arpt 25 km, Hartsfield-Jackson Atlanta Intl Ap 42 km, Lee Gilmer Memorial Arpt 69 km |
| Richard B Russell Airport, GA | isd-linked | 0.99 | -1.09 | Dobbins Air Reserve Base Airport 77 km, Fulton Co-Brown Fld Arpt 85 km, Lovell Field Airport 87 km, Anniston Metropolitan Arpt 92 km |
| Valdosta Regional Airport, GA | isd-linked | 0.99 | -0.15 | Moody Afb Airport 25 km |
| Lawson Aaf Airport, GA | isd-linked | 0.99 | -0.39 | Columbus Metro Airport 30 km |
| Pchtre Cty-Falcon Fld Arpt, GA | isd-linked | 0.99 | +0.07 | Hartsfield-Jackson Atlanta Intl Ap 43 km, Fulton Co-Brown Fld Arpt 59 km, Dekalb-Peachtree Airport 72 km, Dobbins Air Reserve Base Airport 74 km |
| Columbus Metro Airport, GA | isd | 0.99 | -0.16 | Lawson Aaf Airport 18 km |
| Middle Georgia Regional Airport, GA | isd | 0.99 | -0.40 | Robins Afb Airport 19 km |
| Anniston Metropolitan Arpt, AL | isd | 0.99 | -1.10 | no land station within 100 km |
| Augusta Regional At Bush Field Ap, GA | isd | 0.99 | +0.14 | Daniel Field Airport 24 km |
| Greenville-Spartanburg Intl Airport, SC | isd | 0.99 | -0.21 | Greenville Downtown Arpt 19 km, Asheville Regional Airport 55 km, Anderson Regional Airport 70 km |
| Moody Afb Airport, GA | isd-linked | 0.99 | +0.63 | Valdosta Regional Airport 25 km, Bacon County Airport 93 km |
| Robins Afb Airport, GA | isd-linked | 1.00 | -0.24 | Middle Georgia Regional Airport 16 km |
| Sw Georgia Regional Arpt, GA | isd-linked | 1.00 | +0.00 | no land station within 100 km |
| Cairns Army Airfield (Fort Rucker), AL | isd-linked | 1.00 | +0.64 | Dothan Regional Airport 30 km, Troy Municipal Airport 72 km |
| Asheville Regional Airport, NC | isd | 1.00 | +0.25 | Greenville-Spartanburg Intl Airport 71 km, Greenville Downtown Arpt 74 km |
| Greenville Downtown Arpt, SC | isd-linked | 1.00 | +0.22 | Greenville-Spartanburg Intl Airport 18 km, Anderson Regional Airport 50 km, Asheville Regional Airport 80 km |
| Hartsfield-Jackson Atlanta Intl Ap, GA | isd | 1.00 | -0.29 | Fulton Co-Brown Fld Arpt 4 km, Dobbins Air Reserve Base Airport 19 km, Dekalb-Peachtree Airport 24 km, Pchtre Cty-Falcon Fld Arpt 44 km |
| Fulton Co-Brown Fld Arpt, GA | isd-linked | 1.00 | -0.07 | Hartsfield-Jackson Atlanta Intl Ap 14 km, Dobbins Air Reserve Base Airport 19 km, Dekalb-Peachtree Airport 24 km, Pchtre Cty-Falcon Fld Arpt 44 km |
| Athens/Ben Epps Airport, GA | isd | 1.00 | -0.27 | Lee Gilmer Memorial Arpt 61 km, Anderson Regional Airport 74 km, Dekalb-Peachtree Airport 98 km |
| Dothan Regional Airport, AL | isd-linked | 1.00 | -0.48 | Cairns Army Airfield (Fort Rucker) 21 km, Troy Municipal Airport 83 km |
| Troy Municipal Airport, AL | isd-linked | 1.00 | -0.18 | Cairns Army Airfield (Fort Rucker) 60 km, Dothan Regional Airport 71 km |
| Bacon County Airport, GA | isd-linked | 1.00 | -0.09 | Moody Afb Airport 89 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Brunswick city | Malcolm Mc Kinnon Airport (8) | 0.77 | +1 | +1 | +12 | +20 | +17 | +25 |
| Garden City city | Savannah/Hilton Head Intl Airport (5) | 0.94 | +0 | +1 | -5 | +5 | -3 | +3 |
| Dougherty County | Sw Georgia Regional Arpt (1) | 1.00 | -0 | -0 | -2 | +10 | +0 | +16 |
| Dasher town | Valdosta Regional Airport (6) | 0.99 | -0 | -0 | -1 | +2 | -1 | +2 |
| Centerville city | Middle Georgia Regional Airport (6) | 0.99 | +0 | +0 | -5 | +9 | -8 | +0 |
| Warner Robins city | Robins Afb Airport (6) | 1.00 | -1 | -2 | -4 | -10 | -2 | -12 |
| Augusta-Richmond County consolidated government (balance) | Augusta Regional At Bush Field Ap (10) | 0.99 | +1 | +0 | +9 | -0 | +15 | +4 |
| Gainesville city | Lee Gilmer Memorial Arpt (2) | 0.97 | +0 | +1 | +17 | +1 | +32 | +10 |
| College Park city | Hartsfield-Jackson Atlanta Intl Ap (2) | 1.00 | -1 | -1 | +3 | -5 | -2 | -12 |
| Chamblee city | Dekalb-Peachtree Airport (0) | 0.98 | +0 | -0 | -1 | +8 | -4 | -7 |
| Peachtree City city | Pchtre Cty-Falcon Fld Arpt (4) | 1.00 | +1 | +2 | +4 | +26 | +11 | +25 |
| Chattahoochee County | Lawson Aaf Airport (19) | 0.99 | +0 | +0 | +0 | +20 | +2 | +16 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| Brunswick city | +0.45 | +9.20 | +0.56 | +8.18 |
| Garden City city | -0.23 | +2.29 | -0.14 | +1.08 |
| Dougherty County | -0.15 | +4.72 | +0.02 | +6.55 |
| Dasher town | -0.08 | +1.06 | -0.04 | +0.60 |
| Centerville city | -0.23 | +4.22 | -0.43 | +0.04 |
| Warner Robins city | -0.21 | -5.19 | -0.09 | -5.79 |
| Augusta-Richmond County consolidated government (balance) | +0.44 | -0.04 | +0.86 | +1.73 |
| Gainesville city | +0.52 | +0.53 | +0.88 | +3.66 |
| College Park city | +0.11 | -2.63 | -0.06 | -5.28 |
| Chamblee city | -0.03 | +3.69 | -0.14 | -3.00 |
| Peachtree City city | +0.13 | +11.75 | +0.41 | +9.11 |
| Chattahoochee County | +0.01 | +8.92 | +0.14 | +6.00 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
