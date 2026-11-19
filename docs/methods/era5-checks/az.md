# ERA5 check: AZ

**FAIL** (2026-11-18; model 1.17; design 0005's leave-one-station-out check; 17 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 17 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.82 | **no** | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.57 | **no** | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.41 | **no** | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | - | not judged | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | - | not judged | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.05 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 1.52 | **no** | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.37 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 5.03 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 1.39 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 2.89 | **no** | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 8.56 | **no** | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (10) | uncorrected | 0.72 (-0.45) | 0.27 (-0.03) | 0.53 (-0.39) | 0.59 (-0.36) |
| land cells, corrected (10) | decided | 0.69 (-0.51) | 0.28 (-0.16) | 0.75 (-0.43) | 0.99 (-0.09) |
| land cells, no station (7) | uncorrected | 1.45 (-0.65) | 0.45 (-0.32) | 0.98 (-0.31) | 0.57 (-0.14) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Page Municipal Airport, AZ | isd-linked | 0.94 | -0.85 | no land station within 100 km |
| Needles Airport, CA | isd | 0.99 | -2.48 | Kingman Airport 76 km |
| Blythe Airport, CA | isd | 1.00 | -1.91 | Yuma Mcas 95 km |
| Imperial County Airport, CA | isd-linked | 1.00 | +0.07 | Yuma Mcas 83 km |
| Yuma Mcas, AZ | isd-linked | 1.00 | +1.25 | Blythe Airport 99 km |
| Phoenix Sky Harbor Intl Airport, AZ | isd | 1.00 | -0.74 | Phoenix Deer Valley Arpt 22 km, Luke Afb Airport 34 km |
| Ernest A. Love Field Arpt, AZ | isd | 1.00 | +0.75 | no land station within 100 km |
| Safford Regional Airport, AZ | isd-linked | 1.00 | -3.15 | no land station within 100 km |
| Luke Afb Airport, AZ | isd-linked | 1.00 | -0.43 | Phoenix Sky Harbor Intl Airport 24 km, Phoenix Deer Valley Arpt 27 km |
| Winslow-Lindbergh Regional Airport, AZ | isd | 1.00 | -0.75 | no land station within 100 km |
| Cedar City Regional Arpt, UT | isd | 1.00 | -2.30 | no land station within 100 km |
| Tucson International Airport, AZ | isd | 1.00 | -0.64 | Davis-Monthan Afb Airport 14 km |
| Gallup Municipal Airport, NM | isd | 1.00 | -1.45 | no land station within 100 km |
| Phoenix Deer Valley Arpt, AZ | isd-linked | 1.00 | -0.57 | Phoenix Sky Harbor Intl Airport 36 km, Luke Afb Airport 41 km |
| Kingman Airport, AZ | isd-linked | 1.00 | +0.82 | Needles Airport 78 km |
| Grand Canyon Natl Park Apt, AZ | isd-linked | 1.00 | +3.20 | no land station within 100 km |
| Davis-Monthan Afb Airport, AZ | isd-linked | 1.00 | -0.47 | Tucson International Airport 14 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| South Tucson city | Tucson International Airport (7) | 1.00 | -1 | -1 | -9 | -6 | -11 | -9 |
| Tucson city | Davis-Monthan Afb Airport (2) | 1.00 | -2 | -3 | -27 | -13 | -32 | -19 |
| Safford city | Safford Regional Airport (6) | 1.00 | -2 | -4 | -31 | -9 | -37 | -19 |
| Guadalupe town | Phoenix Sky Harbor Intl Airport (8) | 1.00 | -1 | -1 | -14 | -6 | -14 | -5 |
| Phoenix city | Phoenix Deer Valley Arpt (13) | 1.00 | +1 | +1 | +15 | +2 | +15 | +2 |
| Litchfield Park city | Luke Afb Airport (5) | 1.00 | +1 | +0 | +4 | +2 | +4 | -0 |
| Kingman city | Kingman Airport (8) | 1.00 | +1 | +2 | +19 | +12 | +23 | +13 |
| Page city | Page Municipal Airport (6) | 0.94 | -1 | -2 | -7 | -6 | -10 | -14 |
| Prescott city | Ernest A. Love Field Arpt (7) | 1.00 | +2 | +4 | +38 | +18 | +44 | +20 |
| Winslow city | Winslow-Lindbergh Regional Airport (1) | 1.00 | +1 | +0 | -2 | +10 | +2 | +4 |
| Tusayan town | Grand Canyon Natl Park Apt (3) | 1.00 | +3 | +5 | +85 | +13 | +134 | +29 |
| Somerton city | Yuma Mcas (9) | 1.00 | -1 | -1 | -11 | -5 | -12 | -1 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| South Tucson city | -1.06 | -3.88 | -2.04 | -7.15 |
| Tucson city | -2.95 | -8.25 | -5.95 | -16.05 |
| Safford city | -2.96 | -5.48 | -6.11 | -15.22 |
| Guadalupe town | -2.38 | -4.92 | -4.24 | -4.61 |
| Phoenix city | +2.25 | +1.42 | +3.79 | +1.37 |
| Litchfield Park city | +0.70 | +1.39 | +1.25 | -0.09 |
| Kingman city | +1.59 | +7.55 | +3.19 | +9.97 |
| Page city | -0.45 | -3.40 | -1.12 | -10.36 |
| Prescott city | +1.33 | +9.22 | +2.20 | +10.46 |
| Winslow city | -0.09 | +5.14 | +0.13 | +2.27 |
| Tusayan town | +1.45 | +5.97 | +2.58 | +11.63 |
| Somerton city | -1.82 | -3.39 | -3.50 | -0.52 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
