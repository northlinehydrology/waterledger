# ERA5 check: NY

**FAIL** (2026-11-12; model 1.11; design 0005's leave-one-station-out check; 68 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 40 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.54 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.28 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.37 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.81 | **no** | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.81 vs 1.00 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.01 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 13.32 | **no** | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 9.06 | **no** | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 7.55 | **no** | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.52 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (36) | uncorrected | 0.55 (-0.37) | 0.37 (-0.27) | 0.49 (-0.44) | 0.25 (-0.11) |
| land cells, corrected (36) | decided | 0.54 (-0.24) | 0.37 (-0.11) | 0.52 (-0.23) | 0.34 (+0.00) |
| land cells, no station (4) | uncorrected | 0.50 (-0.59) | 0.35 (-0.34) | 0.57 (-0.64) | 0.23 (-0.22) |
| shore cells, corrected (27) | uncorrected | 1.00 (-0.88) | 0.24 (-0.09) | 0.59 (-0.22) | 0.65 (+0.61) |
| shore cells, corrected (27) | decided | 0.81 (-0.25) | 0.23 (+0.04) | 0.76 (-0.01) | 0.27 (+0.08) |
| shore cells, no shore station (1) | uncorrected | 2.25 (-2.25) | 0.06 (+0.06) | 1.21 (-1.21) | 1.18 (+1.18) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Republic Airport, NY | isd-linked | 0.50 | +0.20 | John F Kennedy International Airport 26 km, La Guardia Airport 32 km, Long Island Mac Arthur Airport 34 km, Westchester County Airport 39 km |
| Trenton A, Ontario | eccc | 0.53 | -3.08 | Point Petre (Aut) 34 km, Cobourg (Aut) 54 km, Kingston A 76 km |
| Port Weller (Aut), Ontario | eccc | 0.54 | +0.90 | Niagara Falls Intl Airport 30 km, Toronto City Centre 44 km, Burlington Piers (Aut) 45 km |
| Long Island Mac Arthur Airport, NY | isd-linked | 0.55 | +0.09 | Republic Airport 14 km, John F Kennedy International Airport 45 km, Igor I Sikorsky Memorial Airport 47 km, Westchester County Airport 52 km |
| Francis S Gabreski Ap, NY | isd-linked | 0.55 | +0.80 | Igor I Sikorsky Memorial Airport 21 km, Long Island Mac Arthur Airport 24 km, Republic Airport 46 km, Danbury Municipal Airport 58 km |
| John F Kennedy International Airport, NY | isd | 0.58 | +1.09 | La Guardia Airport 11 km, Central Park 19 km, Republic Airport 28 km, Teterboro Airport 28 km |
| Kingston A, Ontario | eccc | 0.66 | +0.77 | Watertown Intl Airport 48 km, Point Petre (Aut) 70 km, Trenton A 83 km |
| Burlington Piers (Aut), Ontario | eccc | 0.67 | -0.90 | Port Weller (Aut) 43 km, Toronto City Centre 51 km, Niagara Falls Intl Airport 68 km |
| Cobourg (Aut), Ontario | eccc | 0.68 | +2.02 | Trenton A 59 km, Point Petre (Aut) 90 km |
| La Guardia Airport, NY | isd | 0.71 | -0.90 | Central Park 4 km, Teterboro Airport 13 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Central Park, NY | isd-linked | 0.71 | +0.79 | La Guardia Airport 11 km, Teterboro Airport 13 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Teterboro Airport, NJ | isd-linked | 0.71 | -0.81 | Central Park 4 km, La Guardia Airport 11 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Erie Intl/T. Ridge Field Airport, PA | isd | 0.72 | -2.25 | no shore station within 100 km |
| Montreal/Pierre Elliott Trudeau Intl, Quebec | eccc | 0.76 | +0.03 | Mctavish 13 km, Ste-Anne-De-Bellevue 1 16 km, Montreal/St-Hubert 26 km, Ste-Clotilde 37 km |
| Westchester County Airport, NY | isd | 0.76 | +1.28 | La Guardia Airport 27 km, Teterboro Airport 30 km, Central Park 31 km, John F Kennedy International Airport 40 km |
| Point Petre (Aut), Ontario | eccc | 0.77 | +2.29 | Trenton A 26 km, Kingston A 58 km, Cobourg (Aut) 74 km, Watertown Intl Airport 98 km |
| Igor I Sikorsky Memorial Airport, CT | isd | 0.78 | +0.71 | Danbury Municipal Airport 24 km, Westchester County Airport 44 km, Long Island Mac Arthur Airport 52 km, Republic Airport 59 km |
| Watertown Intl Airport, NY | isd | 0.78 | -2.83 | Kingston A 54 km, Point Petre (Aut) 94 km |
| Ste-Anne-De-Bellevue 1, Quebec | eccc | 0.79 | +0.15 | Montreal/Pierre Elliott Trudeau Intl 20 km, Mctavish 33 km, Ste-Clotilde 44 km, Montreal/St-Hubert 45 km |
| Niagara Falls Intl Airport, NY | isd | 0.81 | -2.27 | Port Weller (Aut) 33 km, Burlington Piers (Aut) 73 km, Toronto City Centre 77 km |
| Ste-Clotilde, Quebec | eccc | 0.82 | -0.14 | Ste-Anne-De-Bellevue 1 24 km, Montreal/Pierre Elliott Trudeau Intl 24 km, Mctavish 31 km, Montreal/St-Hubert 40 km |
| Newark Liberty International Ap, NJ | isd | 0.82 | -1.55 | Teterboro Airport 20 km, Central Park 24 km, La Guardia Airport 31 km, John F Kennedy International Airport 43 km |
| Burlington International Airport, VT | isd | 0.84 | -1.88 | Ste-Clotilde 82 km |
| Danbury Municipal Airport, CT | isd-linked | 0.89 | -0.35 | Westchester County Airport 27 km, Igor I Sikorsky Memorial Airport 33 km, Republic Airport 58 km, Long Island Mac Arthur Airport 61 km |
| Toronto City Centre, Ontario | eccc | 0.90 | +0.15 | Burlington Piers (Aut) 56 km, Port Weller (Aut) 60 km, Niagara Falls Intl Airport 85 km |
| Mctavish, Quebec | eccc | 0.90 | +0.08 | Montreal/St-Hubert 7 km, Montreal/Pierre Elliott Trudeau Intl 19 km, Ste-Anne-De-Bellevue 1 34 km, Ste-Clotilde 39 km |
| Montreal/St-Hubert, Quebec | eccc | 0.90 | +0.21 | Mctavish 6 km, Montreal/Pierre Elliott Trudeau Intl 19 km, Ste-Anne-De-Bellevue 1 34 km, Ste-Clotilde 39 km |
| Theodore F Green State Airport, RI | isd | 0.90 | -3.51 | Groton-New London Airport 66 km |
| St-Anicet 1, Quebec | eccc | 0.91 | -0.53 | Massena Intl/Rchards Fd Ap 48 km, Adirondack Regional Arpt 68 km, L'Acadie 78 km |
| L'Assomption, Quebec | eccc | 0.92 | -0.16 | L'Acadie 52 km, St-Anicet 1 93 km, Frelighsburg 95 km |
| Groton-New London Airport, CT | isd-linked | 0.93 | +3.18 | Windham Airport 31 km, Hartford-Brainard Airport 60 km, Bradley International Airport 75 km, Westover Afb/Metropolitan Airport 90 km |
| Peterborough A, Ontario | eccc | 0.94 | -0.10 | no land station within 100 km |
| Ithaca Tompkins Regional Airport, NY | isd-linked | 0.94 | -0.16 | Elmira/Corning Rgnl Arpt 50 km, Greater Binghamton/E A Link Field Ap 54 km, Syracuse Hancock International Ap 75 km |
| Massena Intl/Rchards Fd Ap, NY | isd | 0.94 | +0.05 | St-Anicet 1 38 km, Adirondack Regional Arpt 80 km, Ottawa Intl A 80 km |
| Syracuse Hancock International Ap, NY | isd | 0.94 | -0.54 | Ithaca Tompkins Regional Airport 69 km, Greater Binghamton/E A Link Field Ap 88 km |
| Ottawa Intl A, Ontario | eccc | 0.94 | -0.25 | Massena Intl/Rchards Fd Ap 79 km |
| Orange Municipal Airport, MA | isd-linked | 0.95 | -0.40 | Westover Afb/Metropolitan Airport 41 km, Barnes Municipal Airport 54 km, Bradley International Airport 72 km, Harriman-And-West Airport 78 km |
| Buffalo Niagara International Airpor, NY | isd | 0.95 | +1.04 | Greater Rochester International Ap 88 km, Hamilton A 98 km |
| Adirondack Regional Arpt, NY | isd-linked | 0.96 | -1.21 | Massena Intl/Rchards Fd Ap 68 km, St-Anicet 1 69 km |
| Ne Philadelphia Airport, PA | isd-linked | 0.96 | -0.15 | South Jersey Regional Arpt 15 km, Mcguire Afb Airport 34 km, Trenton Mercer Airport 34 km |
| Mcguire Afb Airport, NJ | isd-linked | 0.96 | -0.18 | South Jersey Regional Arpt 30 km, Trenton Mercer Airport 41 km, Ne Philadelphia Airport 44 km, Essex County Airport 99 km |
| L'Acadie, Quebec | eccc | 0.97 | +0.33 | Frelighsburg 40 km, L'Assomption 64 km, St-Anicet 1 83 km, Morrisville-Stowe St Arpt 94 km |
| Essex County Airport, NJ | isd-linked | 0.97 | -0.66 | Dutchess County Airport 76 km, Trenton Mercer Airport 94 km |
| South Jersey Regional Arpt, NJ | isd-linked | 0.97 | +0.14 | Mcguire Afb Airport 13 km, Ne Philadelphia Airport 24 km, Trenton Mercer Airport 31 km |
| Westover Afb/Metropolitan Airport, MA | isd-linked | 0.97 | -0.19 | Barnes Municipal Airport 20 km, Bradley International Airport 38 km, Orange Municipal Airport 40 km, Hartford-Brainard Airport 59 km |
| Greater Rochester International Ap, NY | isd | 0.97 | -1.53 | Buffalo Niagara International Airpor 80 km |
| Albany International Airport, NY | isd | 0.98 | -0.70 | Harriman-And-West Airport 48 km |
| Hartford-Brainard Airport, CT | isd-linked | 0.98 | -0.44 | Bradley International Airport 22 km, Barnes Municipal Airport 46 km, Windham Airport 47 km, Westover Afb/Metropolitan Airport 53 km |
| Toronto Intl A, Ontario | eccc | 0.98 | -1.09 | Hamilton A 66 km |
| Wilkes-Barre/Scranton Intl Airport, PA | isd | 0.98 | -0.82 | Williamsport Regional Airport 98 km |
| Bradley International Airport, CT | isd | 0.98 | -0.88 | Barnes Municipal Airport 18 km, Westover Afb/Metropolitan Airport 28 km, Hartford-Brainard Airport 31 km, Windham Airport 55 km |
| Trenton Mercer Airport, NJ | isd-linked | 0.98 | +0.68 | Mcguire Afb Airport 29 km, Ne Philadelphia Airport 29 km, South Jersey Regional Arpt 35 km, Essex County Airport 80 km |
| Barnes Municipal Airport, MA | isd-linked | 0.98 | -1.08 | Westover Afb/Metropolitan Airport 19 km, Bradley International Airport 35 km, Orange Municipal Airport 52 km, Hartford-Brainard Airport 58 km |
| Hamilton A, Ontario | eccc | 0.98 | +0.82 | Toronto Intl A 56 km |
| Williamsport Regional Airport, PA | isd | 0.99 | -1.45 | no land station within 100 km |
| Lebanon Municipal Airport, NH | isd-linked | 0.99 | -2.12 | Hartness St (Spngfld) Arpt 50 km, Edward F Knapp State Arpt 56 km, Morrisville-Stowe St Arpt 92 km |
| Dutchess County Airport, NY | isd-linked | 0.99 | +0.10 | no land station within 100 km |
| Windham Airport, CT | isd-linked | 0.99 | +0.42 | Hartford-Brainard Airport 33 km, Bradley International Airport 41 km, Westover Afb/Metropolitan Airport 55 km, Barnes Municipal Airport 60 km |
| Morrisville-Stowe St Arpt, VT | isd-linked | 0.99 | -1.62 | Edward F Knapp State Arpt 33 km, Frelighsburg 65 km, Lebanon Municipal Airport 98 km |
| Hartness St (Spngfld) Arpt, VT | isd-linked | 0.99 | -0.55 | Lebanon Municipal Airport 45 km, Orange Municipal Airport 78 km, Harriman-And-West Airport 82 km |
| Wheeler-Sack Aaf Airport, NY | isd-linked | 0.99 | -0.90 | no land station within 100 km |
| Elmira/Corning Rgnl Arpt, NY | isd-linked | 0.99 | -1.75 | Ithaca Tompkins Regional Airport 51 km, Greater Binghamton/E A Link Field Ap 84 km |
| Edward F Knapp State Arpt, VT | isd | 0.99 | -0.16 | Morrisville-Stowe St Arpt 33 km, Lebanon Municipal Airport 71 km, Frelighsburg 91 km |
| Bradford Regional Airport, PA | isd | 0.99 | +0.43 | Du Bois-Jefferson Co Arpt 65 km |
| Greater Binghamton/E A Link Field Ap, NY | isd | 0.99 | +1.31 | Ithaca Tompkins Regional Airport 46 km, Elmira/Corning Rgnl Arpt 75 km, Syracuse Hancock International Ap 96 km |
| Harriman-And-West Airport, MA | isd-linked | 0.99 | -0.90 | Albany International Airport 45 km, Barnes Municipal Airport 79 km, Orange Municipal Airport 81 km, Westover Afb/Metropolitan Airport 85 km |
| Frelighsburg, Quebec | eccc | 1.00 | +0.51 | Morrisville-Stowe St Arpt 53 km, L'Acadie 57 km, Edward F Knapp State Arpt 90 km |
| Du Bois-Jefferson Co Arpt, PA | isd-linked | 1.00 | +0.44 | Bradford Regional Airport 68 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| New York County | La Guardia Airport (8) | 0.71 | -0 | -1 | -7 | -3 | -15 | -6 |
| Rye Brook village | Westchester County Airport (4) | 0.76 | +1 | +2 | +22 | +9 | +31 | +21 |
| Islandia village | Long Island Mac Arthur Airport (6) | 0.55 | +0 | +0 | +4 | +7 | +8 | +9 |
| North Syracuse village | Syracuse Hancock International Ap (3) | 0.84 | -2 | -4 | -31 | -10 | -54 | -32 |
| Niagara town | Niagara Falls Intl Airport (4) | 0.81 | -1 | -1 | -33 | +4 | -51 | -22 |
| Gates town | Greater Rochester International Ap (5) | 0.67 | -1 | -2 | -28 | +13 | -55 | -22 |
| Wappingers Falls village | Dutchess County Airport (4) | 0.97 | +0 | +1 | +1 | +8 | -2 | +7 |
| Maine town | Greater Binghamton/E A Link Field Ap (3) | 0.99 | +0 | +1 | +10 | -3 | +9 | -3 |
| Lansing village | Ithaca Tompkins Regional Airport (2) | 0.94 | -0 | +0 | +1 | +4 | +0 | +0 |
| Big Flats town | Elmira/Corning Rgnl Arpt (2) | 0.99 | -1 | -0 | -22 | +9 | -32 | -3 |
| Colonie town | Albany International Airport (1) | 0.98 | -1 | -2 | -13 | -9 | -18 | -10 |
| Williamsville village | Buffalo Niagara International Airpor (2) | 0.95 | -0 | +1 | -13 | -7 | -10 | -6 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
