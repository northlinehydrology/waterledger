# ERA5 check: MI

**PASS** (2026-11-16; model 1.16; design 0005's leave-one-station-out check; 36 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 18 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.27 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.03 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.10 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.48 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.48 vs 1.55 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.17 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 0.21 | yes | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.04 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 3.82 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.27 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 0.18 | yes | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 2.24 | yes | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (15) | uncorrected | 0.35 (-0.34) | 0.09 (-0.11) | 0.27 (-0.29) | 0.15 (+0.04) |
| land cells, corrected (15) | decided | 0.14 (+0.03) | 0.08 (-0.08) | 0.25 (+0.13) | 0.21 (-0.01) |
| land cells, no station (3) | uncorrected | 0.60 (-0.33) | 0.35 (-0.25) | 0.33 (-0.34) | 0.41 (+0.12) |
| shore cells, corrected (11) | uncorrected | 1.55 (-1.37) | 0.21 (-0.16) | 0.66 (-0.73) | 0.40 (+0.42) |
| shore cells, corrected (11) | decided | 0.48 (-0.09) | 0.22 (-0.01) | 0.71 (+0.14) | 0.41 (-0.01) |
| shore cells, no shore station (7) | uncorrected | 1.95 (-1.66) | 0.36 (-0.22) | 1.41 (-1.04) | 0.63 (+0.31) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Gore Bay Climate, Ontario | eccc | 0.50 | -2.40 | no shore station within 100 km |
| Selfridge Air National Guard Base, MI | isd-linked | 0.62 | +0.29 | Detroit City Airport 24 km, Windsor A 30 km, Detroit Metro Wayne County Airport 56 km |
| Sw Michigan Regional Arpt, MI | isd-linked | 0.65 | -0.48 | Tulip City Airport 89 km |
| Houghton County Memo Arpt, MI | isd | 0.69 | -0.30 | no shore station within 100 km |
| Alpena County Regional Airport, MI | isd | 0.69 | -2.25 | no shore station within 100 km |
| Cherry Capital Airport, MI | isd | 0.70 | -0.67 | Roscommon County Airport 79 km |
| Sault Ste. Marie Airport, Ontario | eccc | 0.71 | +0.32 | Sault Ste Marie Muni/Sasn Field Ap 11 km |
| Muskegon County Airport, MI | isd | 0.72 | +0.95 | Tulip City Airport 57 km |
| Thunder Bay, Ontario | eccc | 0.74 | -2.45 | no shore station within 100 km |
| Windsor A, Ontario | eccc | 0.78 | +0.58 | Detroit City Airport 18 km, Detroit Metro Wayne County Airport 27 km, Selfridge Air National Guard Base 42 km |
| Goderich, Ontario | eccc | 0.80 | -0.70 | no shore station within 100 km |
| Tulip City Airport, MI | isd-linked | 0.81 | -0.97 | Muskegon County Airport 51 km, Sw Michigan Regional Arpt 77 km |
| Chicago Midway Intl Arpt, IL | isd | 0.82 | -1.60 | no shore station within 100 km |
| Sault Ste Marie Muni/Sasn Field Ap, MI | isd | 0.85 | -0.71 | Sault Ste. Marie Airport 21 km |
| Pellston Regional Arpt Of Emmet County Arpt, MI | isd | 0.87 | -1.95 | no shore station within 100 km |
| Detroit City Airport, MI | isd | 0.88 | -0.21 | Selfridge Air National Guard Base 19 km, Windsor A 25 km, Detroit Metro Wayne County Airport 40 km |
| Detroit Metro Wayne County Airport, MI | isd | 0.88 | -0.10 | Windsor A 24 km, Detroit City Airport 26 km, Selfridge Air National Guard Base 53 km |
| Roscommon County Airport, MI | isd | 0.89 | -0.02 | Cherry Capital Airport 85 km |
| Rhinelander-Oneida Co Arpt, WI | isd-linked | 0.90 | -1.30 | no land station within 100 km |
| Mbs International Airport, MI | isd | 0.92 | +0.67 | Bishop International Airport 63 km, Capital City Airport 94 km |
| Toledo Express Airport, OH | isd | 0.95 | +0.12 | Metcalf Field Airport 24 km, Findlay Airport 54 km, Defiance Memorial Airport 60 km, Willow Run Airport 84 km |
| Austin Straubel International Ap, WI | isd | 0.95 | +0.60 | no land station within 100 km |
| Oakland Co. Intnl Airport, MI | isd-linked | 0.96 | +0.28 | Bishop International Airport 32 km, Willow Run Airport 57 km, Capital City Airport 90 km, Jakson Co-Rynolds Fld Arpt 95 km |
| Metcalf Field Airport, OH | isd-linked | 0.96 | +0.08 | Toledo Express Airport 27 km, Findlay Airport 56 km, Defiance Memorial Airport 80 km, Willow Run Airport 82 km |
| Klmazo/Btl Creek Intl Arpt, MI | isd-linked | 0.97 | -0.28 | W K Kellogg Airport 22 km, Gerald R Ford International Airport 70 km, Jakson Co-Rynolds Fld Arpt 86 km, South Bend Regional Airport 90 km |
| Ford Airport, MI | isd-linked | 0.98 | -0.30 | no land station within 100 km |
| W K Kellogg Airport, MI | isd-linked | 0.98 | -0.06 | Klmazo/Btl Creek Intl Arpt 24 km, Jakson Co-Rynolds Fld Arpt 65 km, Gerald R Ford International Airport 74 km, Capital City Airport 79 km |
| Gerald R Ford International Airport, MI | isd | 0.98 | +0.37 | Capital City Airport 77 km, W K Kellogg Airport 79 km, Klmazo/Btl Creek Intl Arpt 86 km |
| Bishop International Airport, MI | isd | 0.99 | -0.13 | Oakland Co. Intnl Airport 47 km, Mbs International Airport 64 km, Capital City Airport 74 km, Willow Run Airport 87 km |
| Jakson Co-Rynolds Fld Arpt, MI | isd | 0.99 | +0.26 | Capital City Airport 59 km, W K Kellogg Airport 61 km, Willow Run Airport 80 km, Klmazo/Btl Creek Intl Arpt 86 km |
| South Bend Regional Airport, IN | isd | 0.99 | +0.14 | Klmazo/Btl Creek Intl Arpt 79 km |
| Willow Run Airport, MI | isd-linked | 0.99 | -0.81 | Oakland Co. Intnl Airport 46 km, Metcalf Field Airport 76 km, Toledo Express Airport 78 km, Jakson Co-Rynolds Fld Arpt 79 km |
| Capital City Airport, MI | isd | 0.99 | +0.11 | Jakson Co-Rynolds Fld Arpt 54 km, Bishop International Airport 66 km, W K Kellogg Airport 78 km, Gerald R Ford International Airport 85 km |
| Fort Wayne International Airport, IN | isd | 1.00 | -0.31 | Defiance Memorial Airport 78 km |
| Findlay Airport, OH | isd | 1.00 | -0.14 | Toledo Express Airport 65 km, Metcalf Field Airport 67 km, Defiance Memorial Airport 68 km |
| Defiance Memorial Airport, OH | isd-linked | 1.00 | +0.07 | Fort Wayne International Airport 67 km, Toledo Express Airport 69 km, Findlay Airport 74 km, Metcalf Field Airport 92 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Romulus city | Detroit Metro Wayne County Airport (3) | 0.88 | -0 | +1 | -7 | +5 | -7 | +8 |
| Hamtramck city | Detroit City Airport (4) | 0.88 | -1 | -1 | -29 | -8 | -34 | -16 |
| Harrison charter township | Selfridge Air National Guard Base (2) | 0.62 | +1 | +2 | +16 | +4 | +26 | +5 |
| Holland city | Tulip City Airport (1) | 0.81 | -0 | +0 | -32 | +10 | -37 | -7 |
| Benton charter township | Sw Michigan Regional Arpt (2) | 0.65 | -0 | +1 | -0 | +4 | -1 | -2 |
| Norton Shores city | Muskegon County Airport (0) | 0.72 | +0 | +2 | +64 | +11 | +66 | +17 |
| Van Buren charter township | Willow Run Airport (4) | 0.99 | -0 | +0 | -23 | +8 | -28 | -1 |
| Lansing city | Capital City Airport (1) | 0.99 | +0 | +1 | +1 | +3 | +5 | +9 |
| Blackman charter township | Jakson Co-Rynolds Fld Arpt (4) | 0.99 | +0 | +1 | +17 | +12 | +20 | +18 |
| Springfield city | W K Kellogg Airport (2) | 0.98 | -0 | +1 | +12 | +10 | +12 | +13 |
| Cascade charter township | Gerald R Ford International Airport (3) | 0.98 | +0 | +1 | +7 | +8 | +14 | +3 |
| Portage city | Klmazo/Btl Creek Intl Arpt (5) | 0.97 | -0 | +0 | -14 | +5 | -16 | +1 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| Romulus city | -0.11 | +2.53 | -0.09 | +2.55 |
| Hamtramck city | -0.51 | -5.04 | -0.48 | -5.97 |
| Harrison charter township | +0.21 | +2.50 | +0.26 | +1.80 |
| Holland city | -0.39 | +5.03 | -0.32 | -2.05 |
| Benton charter township | -0.00 | +2.02 | -0.01 | -0.68 |
| Norton Shores city | +0.46 | +5.37 | +0.32 | +4.17 |
| Van Buren charter township | -0.44 | +3.77 | -0.51 | -0.18 |
| Lansing city | +0.02 | +1.52 | +0.05 | +2.43 |
| Blackman charter township | +0.20 | +5.53 | +0.17 | +4.40 |
| Springfield city | +0.15 | +4.77 | +0.12 | +3.52 |
| Cascade charter township | +0.09 | +3.87 | +0.14 | +0.78 |
| Portage city | -0.22 | +2.56 | -0.19 | +0.20 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
