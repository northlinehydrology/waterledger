# Switch settings implied by operators' stated time on water

Open-Meteo archive (ERA5-based) hourly 2 m dry-bulb at each point, 2015-2024 (`implied_switch.py`). A share of the year is read as a share
of hours; a number of days as days whose hottest hour is above the setting. "At least" where the operator gives an upper bound.

| Site | Operator | Stated | Implied setting, C (F) | Source |
|---|---|---|---|---|
| Northern Virginia (Ashburn) | Microsoft, direct air | 10% of the year | 26.5 (79.7) | Microsoft, June 24, 2026: about 10% of the year |
| Phoenix | Microsoft, direct air | under 40% of the year | at least 27.4 (81.3) | Microsoft, June 24, 2026: up to 40% |
| Mount Pleasant, WI | Microsoft | under 5% of the year | at least 25.2 (77.4) | Microsoft Wisconsin: less than 5% of the year |
| Metro Atlanta | Microsoft | 55 days a year | 30.5 (86.9) | Microsoft local, about Jan 2026: the hottest ~55 days |
| Sidney, OH | AWS | 3% of the year | 28.2 (82.7) | City of Sidney data center FAQ, 2026: about 3% of the year |
| Falls Township, PA | AWS | 6% of the year | 28.0 (82.4) | LevittownNow, July 28, 2026: outside air about 94% of the year |
| New Carlisle, IN | AWS | 7 days a year | 32.0 (89.6) | TheStatehouseFile (AWS statement), 2026: about 7 days a year |

Stated settings: Microsoft 85 F (29.4 C), June 24, 2026; Meta El Paso about 86 F (30 C), El Paso Water's chief executive (El Paso Matters,
Oct 24, 2025). The model samples 26.5-32.0 C (`switch_setting`), the lowest and highest of the figures above.
