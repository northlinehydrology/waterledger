# ERA5 check: MN

**PASS** (2026-11-16; model 1.16; design 0005's leave-one-station-out check; 31 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 28 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.40 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.29 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.22 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | - | not judged | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | - | not judged | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.06 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 0.10 | yes | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.01 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 3.94 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.25 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 0.12 | yes | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 3.06 | yes | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (18) | uncorrected | 0.63 (-0.49) | 0.15 (-0.12) | 0.28 (-0.25) | 0.21 (+0.07) |
| land cells, corrected (18) | decided | 0.32 (-0.14) | 0.23 (-0.01) | 0.30 (+0.02) | 0.32 (+0.09) |
| land cells, no station (10) | uncorrected | 0.68 (-0.56) | 0.20 (-0.26) | 0.48 (-0.39) | 0.14 (+0.05) |
| shore cells, no shore station (3) | uncorrected | 1.50 (-1.40) | 0.51 (-0.24) | 0.87 (-0.73) | 0.70 (+0.65) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Duluth International Airport, MN | isd | 0.81 | -1.00 | no shore station within 100 km |
| Atikokan (Aut), Ontario | eccc | 0.84 | -1.50 | no shore station within 100 km |
| Brainerd Lakes Rgnl Arpt, MN | isd-linked | 0.84 | -1.70 | no shore station within 100 km |
| Sprague, Manitoba | eccc | 0.91 | +0.36 | Baudette International Apt 72 km |
| Sawyer County Airport, WI | isd-linked | 0.92 | -0.85 | no land station within 100 km |
| St Paul Dwtwn Holman Fd Ap, MN | isd-linked | 0.93 | -0.17 | Minneapolis-St Paul International Ap 22 km, Crystal Airport 28 km, Flying Cloud Airport 42 km |
| Chandler Field Airport, MN | isd | 0.93 | +0.81 | Appleton Municipal Airport 70 km |
| Falls International Airport, MN | isd | 0.94 | +0.28 | Baudette International Apt 86 km |
| Pk Rpds Muni-Konshok Fd Ap, MN | isd | 0.94 | -1.05 | no land station within 100 km |
| Watertown Municipal Arpt, SD | isd | 0.94 | -0.75 | no land station within 100 km |
| Minneapolis-St Paul International Ap, MN | isd | 0.94 | -0.45 | Crystal Airport 10 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km, St Cloud Regional Airport 87 km |
| Crystal Airport, MN | isd-linked | 0.94 | -0.26 | Minneapolis-St Paul International Ap 13 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km, St Cloud Regional Airport 87 km |
| St Cloud Regional Airport, MN | isd | 0.95 | +0.03 | Crystal Airport 70 km, Flying Cloud Airport 85 km, Minneapolis-St Paul International Ap 91 km, St Paul Dwtwn Holman Fd Ap 97 km |
| Flying Cloud Airport, MN | isd-linked | 0.96 | -0.27 | Minneapolis-St Paul International Ap 26 km, Crystal Airport 37 km, St Paul Dwtwn Holman Fd Ap 40 km, St Cloud Regional Airport 98 km |
| Appleton Municipal Airport, MN | isd-linked | 0.96 | -0.16 | Chandler Field Airport 83 km, Watertown Municipal Arpt 98 km |
| La Crosse Municipal Airport, WI | isd | 0.96 | -1.28 | Chippewa Valley Rgnl Arpt 98 km, Rochester International Airport 100 km |
| Baudette International Apt, MN | isd | 0.97 | -0.52 | Falls International Airport 84 km, Sprague 86 km |
| Spencer Municipal Airport, IA | isd-linked | 0.97 | -1.47 | Estherville Muni Airport 44 km |
| Chisholm-Hibbing Airport, MN | isd | 0.97 | -0.00 | no land station within 100 km |
| Mason City Municipal Arpt, IA | isd | 0.98 | -0.95 | Rochester International Airport 95 km |
| Chippewa Valley Rgnl Arpt, WI | isd | 0.99 | +0.39 | La Crosse Municipal Airport 99 km |
| Estherville Muni Airport, IA | isd-linked | 0.99 | +1.29 | Spencer Municipal Airport 52 km |
| Tri-County Regional Arpt, WI | isd-linked | 0.99 | -0.65 | no land station within 100 km |
| Hector International Airport, ND | isd | 1.00 | -0.40 | no land station within 100 km |
| Redwood Falls Muni Airport, MN | isd-linked | 1.00 | -0.20 | no land station within 100 km |
| Grand Forks Afb Airport, ND | isd-linked | 1.00 | -0.90 | no land station within 100 km |
| Rochester International Airport, MN | isd | 1.00 | -0.10 | no land station within 100 km |
| Carman U Of M Cs, Manitoba | eccc | 1.00 | -0.20 | Gretna (Aut) 61 km, Emerson Auto 78 km |
| Joe Foss Field Airport, SD | isd | 1.00 | -0.70 | no land station within 100 km |
| Gretna (Aut), Manitoba | eccc | 1.00 | +0.07 | Emerson Auto 19 km, Carman U Of M Cs 68 km |
| Emerson Auto, Manitoba | eccc | 1.00 | +0.01 | Gretna (Aut) 23 km, Carman U Of M Cs 79 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Hermantown city | Duluth International Airport (7) | 0.81 | +1 | +1 | -46 | -16 | -46 | -30 |
| High Forest township | Rochester International Airport (4) | 1.00 | +0 | +1 | +7 | +14 | +10 | +10 |
| Appleton city | Appleton Municipal Airport (3) | 0.96 | +0 | -0 | +2 | +14 | +7 | +10 |
| Haven township | St Cloud Regional Airport (3) | 0.95 | +1 | +1 | +15 | +10 | +12 | +1 |
| Oak Lawn township | Brainerd Lakes Rgnl Arpt (3) | 0.95 | +0 | +0 | +4 | +2 | +6 | -1 |
| Redwood Falls city | Redwood Falls Muni Airport (2) | 1.00 | +0 | +0 | -6 | +12 | -8 | +6 |
| Alexandria city | Chandler Field Airport (2) | 0.92 | +0 | +0 | +31 | +6 | +31 | +24 |
| Brooklyn Center city | Crystal Airport (3) | 0.94 | +0 | +0 | -5 | +2 | -10 | -10 |
| Eden Prairie city | Flying Cloud Airport (2) | 0.96 | -0 | +1 | -7 | +6 | -9 | -2 |
| Richfield city | Minneapolis-St Paul International Ap (4) | 0.96 | -0 | -0 | -5 | -1 | -14 | -8 |
| West St. Paul city | St Paul Dwtwn Holman Fd Ap (4) | 0.93 | -0 | +0 | +7 | +9 | +6 | +5 |
| Park Rapids city | Pk Rpds Muni-Konshok Fd Ap (2) | 0.94 | -0 | -1 | -29 | -6 | -33 | -12 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| Hermantown city | -0.19 | -6.99 | -0.12 | -7.15 |
| High Forest township | +0.07 | +6.33 | +0.06 | +2.80 |
| Appleton city | +0.03 | +6.57 | +0.09 | +3.41 |
| Haven township | +0.19 | +4.92 | +0.12 | +0.23 |
| Oak Lawn township | +0.04 | +0.73 | +0.05 | -0.26 |
| Redwood Falls city | -0.10 | +6.18 | -0.11 | +2.30 |
| Alexandria city | +0.31 | +2.74 | +0.21 | +7.46 |
| Brooklyn Center city | -0.08 | +0.87 | -0.14 | -4.00 |
| Eden Prairie city | -0.12 | +3.03 | -0.12 | -0.59 |
| Richfield city | -0.08 | -0.80 | -0.19 | -3.32 |
| West St. Paul city | +0.10 | +4.85 | +0.08 | +1.77 |
| Park Rapids city | -0.24 | -2.61 | -0.20 | -3.56 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
