# ERA5 check: TX

**PASS** (2026-11-07; model 1.9; design 0005's leave-one-station-out check; 67 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 63 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.45 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.02 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.17 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | - | not judged | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | - | not judged | the reason to correct |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 4.98 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 1.63 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 4.03 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.28 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (53) | uncorrected | 0.40 (-0.34) | 0.18 (-0.05) | 0.34 (-0.13) | 0.22 (+0.04) |
| land cells, corrected (53) | decided | 0.45 (+0.03) | 0.17 (+0.01) | 0.30 (+0.10) | 0.28 (-0.06) |
| land cells, no station (10) | uncorrected | 0.45 (-0.25) | 0.18 (-0.10) | 0.20 (-0.21) | 0.16 (+0.08) |
| shore cells, corrected (1) | uncorrected | 0.25 (-0.25) | 0.13 (-0.13) | 0.72 (-0.72) | 0.04 (+0.04) |
| shore cells, corrected (1) | decided | 0.23 (+0.23) | 0.25 (+0.25) | 0.12 (-0.12) | 0.25 (+0.25) |
| shore cells, no shore station (3) | uncorrected | 0.30 (-0.43) | 0.39 (-0.40) | 0.45 (-0.44) | 0.34 (-0.29) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Scholes Intl At Glston Apt, TX | isd-linked | 0.67 | +0.30 | no shore station within 100 km |
| Aransas County Airport, TX | isd-linked | 0.77 | +0.23 | Corpus Christi Nas 69 km, Palacios Municipal Airport 90 km |
| Palacios Municipal Airport, TX | isd | 0.77 | -0.10 | no shore station within 100 km |
| Southeast Texas Regional Airport, TX | isd | 0.89 | -1.50 | no shore station within 100 km |
| Dallas/Ft Worth International Ap, TX | isd | 0.92 | +0.30 | Denton Municipal Airport 30 km, Fort Worth Alliance Arpt 30 km, Dallas Executive Airport 38 km, Ft Worth Meacham Intl Arpt 39 km |
| Kingsville Nas, TX | isd | 0.92 | -0.49 | Alice International Arpt 38 km, Corpus Christi International Airport 38 km |
| Shreveport Regional Airport, LA | isd | 0.94 | -0.55 | Shreveport Downtown Arpt 4 km, Barksdale Air Force Base 8 km, East Texas Regional Arpt 91 km |
| Shreveport Downtown Arpt, LA | isd-linked | 0.94 | +0.20 | Barksdale Air Force Base 8 km, Shreveport Regional Airport 9 km, East Texas Regional Arpt 91 km |
| Barksdale Air Force Base, LA | isd-linked | 0.94 | +0.53 | Shreveport Downtown Arpt 4 km, Shreveport Regional Airport 9 km, East Texas Regional Arpt 91 km |
| Texarkana Regional Airport-Webb Field, AR | isd | 0.96 | +0.15 | no land station within 100 km |
| Tyler Pounds Regional Arpt, TX | isd-linked | 0.96 | -0.25 | East Texas Regional Arpt 76 km |
| Corpus Christi International Airport, TX | isd | 0.96 | +1.99 | Kingsville Nas 40 km, Alice International Arpt 52 km |
| Corpus Christi Nas, TX | isd | 0.96 | +1.75 | Corpus Christi International Airport 3 km, Kingsville Nas 40 km, Alice International Arpt 52 km |
| Robert Gray Aff Airport, TX | isd-linked | 0.96 | -0.10 | Burnet Municipal Cradock Field Airport 54 km, Austin-Camp Mabry 76 km, Waco Regional Airport 85 km, Austin-Bergstrom Intl Airport 91 km |
| Dallas Executive Airport, TX | isd-linked | 0.97 | +0.11 | Dallas/Ft Worth International Ap 30 km, Mckinney Municipal Arpt 50 km, Ft Worth Meacham Intl Arpt 58 km, Fort Worth Alliance Arpt 60 km |
| Lake Charles Regional Airport, LA | isd | 0.97 | +0.40 | no land station within 100 km |
| Burnet Municipal Cradock Field Airport, TX | isd-linked | 0.97 | +0.15 | Robert Gray Aff Airport 53 km, Austin-Camp Mabry 67 km, Austin-Bergstrom Intl Airport 83 km |
| Del Rio International Airport, TX | isd | 0.97 | -0.29 | Laughlin Afb Airport 26 km |
| East Texas Regional Arpt, TX | isd | 0.98 | -0.11 | Tyler Pounds Regional Arpt 63 km, Shreveport Regional Airport 87 km, Shreveport Downtown Arpt 94 km |
| Sheppard Afb/Wichita Falls Muni Ap, TX | isd | 0.98 | +0.56 | Frederick Municipal Airpt 60 km, Lawton-Fort Sill Rgnl Arpt 62 km |
| Waco Regional Airport, TX | isd | 0.98 | +0.45 | Robert Gray Aff Airport 73 km |
| Fort Worth Naval Air Station Jrb/Carswell Field, TX | isd | 0.98 | -0.52 | Ft Worth Meacham Intl Arpt 15 km, Fort Worth Alliance Arpt 32 km, Dallas/Ft Worth International Ap 48 km, Mineral Wells Airport 52 km |
| Fort Worth Alliance Arpt, TX | isd-linked | 0.98 | -0.37 | Ft Worth Meacham Intl Arpt 22 km, Denton Municipal Airport 24 km, Dallas/Ft Worth International Ap 24 km, Fort Worth Naval Air Station Jrb/Carswell Field 32 km |
| Ft Worth Meacham Intl Arpt, TX | isd-linked | 0.98 | +0.29 | Fort Worth Naval Air Station Jrb/Carswell Field 19 km, Dallas/Ft Worth International Ap 27 km, Fort Worth Alliance Arpt 28 km, Dallas Executive Airport 37 km |
| G Bush Intercontinental Ap/Houston Ap, TX | isd | 0.98 | +0.03 | Hooks Memorial Airpt 30 km, William P. Hobby Airport 40 km |
| Altus Afb Airport, OK | isd-linked | 0.99 | -0.34 | Hobart Municipal Airport 32 km, Frederick Municipal Airpt 50 km, Clinton-Sherman Airport 68 km, Lawton-Fort Sill Rgnl Arpt 79 km |
| Brownsville/S Padre Island Intl Ap, TX | isd | 0.99 | +1.21 | Valley International Arpt 30 km, Mc Allen Miller Intl Arpt 77 km |
| William P. Hobby Airport, TX | isd-linked | 0.99 | +0.79 | G Bush Intercontinental Ap/Houston Ap 28 km, Hooks Memorial Airpt 46 km |
| Mckinney Municipal Arpt, TX | isd-linked | 0.99 | +0.95 | Dallas/Ft Worth International Ap 62 km, Denton Municipal Airport 65 km, Dallas Executive Airport 72 km, Fort Worth Alliance Arpt 82 km |
| San Angelo Regional/Maths Field Ap, TX | isd | 0.99 | -1.25 | no land station within 100 km |
| Denton Municipal Airport, TX | isd-linked | 0.99 | +0.17 | Fort Worth Alliance Arpt 29 km, Dallas/Ft Worth International Ap 45 km, Ft Worth Meacham Intl Arpt 48 km, Fort Worth Naval Air Station Jrb/Carswell Field 57 km |
| Stinson Minicipal Airport, TX | isd-linked | 0.99 | -0.26 | Lackland Air Force Base (Kelly Field Annex) 17 km, San Antonio International Airport 33 km, Randolph Afb Airport 39 km, Hondo Municipal Airport 66 km |
| Valley International Arpt, TX | isd-linked | 0.99 | +0.12 | Brownsville/S Padre Island Intl Ap 50 km, Mc Allen Miller Intl Arpt 50 km |
| Victoria Regional Airport, TX | isd | 0.99 | +0.05 | no land station within 100 km |
| San Antonio International Airport, TX | isd | 0.99 | +0.35 | Lackland Air Force Base (Kelly Field Annex) 15 km, Stinson Minicipal Airport 18 km, Randolph Afb Airport 23 km, Hondo Municipal Airport 67 km |
| Lackland Air Force Base (Kelly Field Annex), TX | isd-linked | 0.99 | -0.75 | San Antonio International Airport 5 km, Stinson Minicipal Airport 18 km, Randolph Afb Airport 23 km, Hondo Municipal Airport 67 km |
| Tucumcari Municipal Arpt, NM | isd-linked | 0.99 | -0.65 | Cannon Afb Airport 98 km |
| Lawton-Fort Sill Rgnl Arpt, OK | isd-linked | 0.99 | +0.53 | Frederick Municipal Airpt 48 km, Sheppard Afb/Wichita Falls Muni Ap 58 km, Altus Afb Airport 72 km, Hobart Municipal Airport 74 km |
| Alice International Arpt, TX | isd-linked | 1.00 | -1.30 | Kingsville Nas 33 km, Corpus Christi International Airport 48 km |
| Austin-Bergstrom Intl Airport, TX | isd-linked | 1.00 | +0.53 | Austin-Camp Mabry 8 km, Burnet Municipal Cradock Field Airport 72 km, Robert Gray Aff Airport 91 km, Randolph Afb Airport 94 km |
| Austin-Camp Mabry, TX | isd-linked | 1.00 | -1.01 | Austin-Bergstrom Intl Airport 10 km, Burnet Municipal Cradock Field Airport 72 km, Robert Gray Aff Airport 91 km, Randolph Afb Airport 94 km |
| Mc Allen Miller Intl Arpt, TX | isd | 1.00 | -1.96 | Valley International Arpt 59 km, Brownsville/S Padre Island Intl Ap 91 km |
| Clinton-Sherman Airport, OK | isd-linked | 1.00 | +0.64 | Hobart Municipal Airport 34 km, Altus Afb Airport 67 km |
| Laughlin Afb Airport, TX | isd-linked | 1.00 | -0.22 | Del Rio International Airport 22 km |
| Mineral Wells Airport, TX | isd | 1.00 | -0.67 | Fort Worth Naval Air Station Jrb/Carswell Field 52 km, Ft Worth Meacham Intl Arpt 60 km, Fort Worth Alliance Arpt 69 km, Denton Municipal Airport 90 km |
| Cavern City Air Trml Arpt, NM | isd | 1.00 | +0.25 | no land station within 100 km |
| Amarillo Rick Husband Intl Airport, TX | isd | 1.00 | -0.40 | no land station within 100 km |
| Frederick Municipal Airpt, OK | isd-linked | 1.00 | -0.19 | Altus Afb Airport 51 km, Sheppard Afb/Wichita Falls Muni Ap 56 km, Lawton-Fort Sill Rgnl Arpt 64 km, Hobart Municipal Airport 82 km |
| Hooks Memorial Airpt, TX | isd-linked | 1.00 | -0.45 | G Bush Intercontinental Ap/Houston Ap 14 km, William P. Hobby Airport 45 km |
| Childress Municipal Arpt, TX | isd-linked | 1.00 | +0.26 | Altus Afb Airport 92 km |
| Easterwood Field Airport, TX | isd-linked | 1.00 | -1.19 | Hooks Memorial Airpt 82 km |
| Angelina County Airport, TX | isd | 1.00 | +0.55 | no land station within 100 km |
| Abilene Regional Airport, TX | isd | 1.00 | +0.37 | Dyess Air Force Base 12 km |
| Dyess Air Force Base, TX | isd-linked | 1.00 | -0.42 | Abilene Regional Airport 12 km |
| Hobart Municipal Airport, OK | isd | 1.00 | -0.22 | Clinton-Sherman Airport 44 km, Altus Afb Airport 46 km, Frederick Municipal Airpt 72 km, Lawton-Fort Sill Rgnl Arpt 72 km |
| Lubbock International Airport, TX | isd | 1.00 | -0.75 | no land station within 100 km |
| Hondo Municipal Airport, TX | isd | 1.00 | +0.02 | Lackland Air Force Base (Kelly Field Annex) 66 km, Stinson Minicipal Airport 76 km, San Antonio International Airport 81 km, Cotulla-La Salle Co Arpt 88 km |
| Winkler County Airport, TX | isd | 1.00 | -1.71 | Fort Stockton-Pecos Co Apt 98 km |
| Randolph Afb Airport, TX | isd-linked | 1.00 | +0.20 | San Antonio International Airport 23 km, Stinson Minicipal Airport 28 km, Lackland Air Force Base (Kelly Field Annex) 35 km, Hondo Municipal Airport 91 km |
| Midland International Airport, TX | isd | 1.00 | +1.85 | Winkler County Airport 93 km |
| Municipal Airport, TX | isd-linked | 1.00 | +0.37 | Clayton Municipal Airpark Airport 77 km |
| El Paso International Airport, TX | isd | 1.00 | -0.50 | no land station within 100 km |
| Clayton Municipal Airpark Airport, NM | isd | 1.00 | -0.53 | Municipal Airport 82 km |
| Cannon Afb Airport, NM | isd-linked | 1.00 | +0.82 | Tucumcari Municipal Arpt 82 km |
| Fort Stockton-Pecos Co Apt, TX | isd-linked | 1.00 | +1.89 | Winkler County Airport 89 km |
| Cotulla-La Salle Co Arpt, TX | isd | 1.00 | -1.43 | Hondo Municipal Airport 96 km |
| Kimble County Airport, TX | isd | 1.00 | -1.05 | no land station within 100 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Nederland city | Southeast Texas Regional Airport (3) | 0.89 | +0 | +0 | +9 | +11 | -7 | +2 |
| Galveston County | Scholes Intl At Glston Apt (4) | 0.67 | -1 | -1 | -16 | -13 | -14 | -11 |
| Corpus Christi city | Corpus Christi Nas (14) | 0.74 | -1 | -1 | +0 | +3 | -1 | +4 |
| Fulton town | Aransas County Airport (2) | 0.77 | +0 | +1 | -4 | +6 | -7 | +7 |
| Palacios city | Palacios Municipal Airport (3) | 0.77 | -0 | -1 | -4 | -9 | -4 | -7 |
| Tye city | Dyess Air Force Base (3) | 1.00 | -0 | -0 | -5 | -1 | -8 | -3 |
| Tomball city | Hooks Memorial Airpt (7) | 1.00 | +0 | -1 | +5 | +3 | +0 | +4 |
| Humble city | G Bush Intercontinental Ap/Houston Ap (9) | 0.98 | +0 | -0 | -1 | -1 | -3 | +1 |
| South Houston city | William P. Hobby Airport (5) | 0.99 | -0 | +1 | -6 | -0 | -1 | -0 |
| Burke city | Angelina County Airport (1) | 1.00 | +0 | +1 | +4 | +5 | +9 | +9 |
| Chandler city | Tyler Pounds Regional Arpt (9) | 0.96 | -1 | -0 | -7 | +1 | -10 | -5 |
| Lakeport city | East Texas Regional Arpt (2) | 0.98 | +0 | +1 | +7 | +6 | +7 | +7 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
