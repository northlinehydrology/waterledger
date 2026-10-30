# Power-plant water per kWh, by state (2024)

Builds `packages/waterledger-data/src/waterledger_data/tables/state_power_water_2024.csv`, the water consumed and
withdrawn at power plants per kWh of electricity used in each state, from plant-reported data. Method and decisions:
[../methods-log.md](../methods-log.md) (Oct 30, 2026, model 1.3).

Inputs, in a work folder (`$WL_POWER_WORK`, default `./work`, not committed):

| File | Source |
|---|---|
| `eia_cooling_detail_2024.xlsx` (or `$WL_EIA_COOLING_DETAIL`) | EIA, Thermoelectric cooling water data, 2024 detail file (EIA-923 Schedule 8D with EIA-860 cooling types): https://www.eia.gov/electricity/data/water/ |
| `dl/api/state_gen_2024.json`, `facility_gen_2024.json`, `generators_2024_12.json` | EIA API v2 (`fetch_eia.py`; public data, DEMO_KEY) |
| `dl/eia860/x/2___Plant_Y2024.xlsx` | EIA-860 2024, plant file (balancing authority of each plant): https://www.eia.gov/electricity/data/eia860/ |
| `dl/sep/sep_<ST>.xlsx` | EIA State Electricity Profiles, Table 10, supply and disposition: https://www.eia.gov/electricity/state/xls/SEP%20Tables%20for%20<ST>.xlsx |

Order: `fetch_eia.py`, `states.py` (state totals, plant flags, Macknick-filled adjusted case, bottom-up), `ba_compare.py`
(the same by balancing authority), `imports.py` (net imports, blend with the main balancing authority, ranges).
`verify_table.py` checks `grid_water_2022.csv` against the Siddik et al. dataset.

Rules, the same for every state:
- Plant water is summed over unique (plant, cooling system, month) rows; cooled generation over unique (plant,
  generator, month), falling back to the plant's 2024 net generation.
- A plant is flagged when its reported consumption exceeds its withdrawal or 1,500 gal/MWh, when a once-through or
  pond plant reports zero consumption, or when a tower or pond plant reports more than 25,000 gal/MWh withdrawn
  (circulation through a cooling reservoir reported as withdrawal). Flagged values are replaced by Macknick et al.
  (2012) medians for the plant's technology and cooling (Table 2 consumption, Table 3 withdrawal).
- State intensity = plant totals / the state's 2024 net generation, all sources (EIA).
- Central value = (1 - s) x state + s x main balancing authority (plant-based, same method), s = net interstate imports
  / in-state consumption (EIA Table 10; 0 for net exporters).
- Range = min and max over: state as reported (only where no plant is flagged), state adjusted, Macknick bottom-up,
  the blend, and the Siddik et al. (2024) balancing-authority value for 2022 (excluding hydropower).

`flagged_plants_2024.csv` lists every flagged plant with its reported and adjusted values.
