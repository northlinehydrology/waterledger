# Small reference tables shipped with waterledger-data

- `grid_water_2022.csv`: water used at power plants per kWh of electricity used, by balancing authority, 2022 annual
  means weighted by hourly electricity use. Derived from Siddik, M. A. B., Shehabi, A., Rao, P., & Marston, L. T. (2024),
  "Spatially and temporally detailed water and carbon footprints of U.S. electricity generation and use", Water Resources
  Research 60(12), https://doi.org/10.1029/2024WR038350; data: LBNL Water IMPACT (HydroShare
  https://www.hydroshare.org/resource/2f54448714554f83b9655da108f0fd3f/, file water_impact_consumption_2022_v1.1).
  `excl_hydro` leaves out evaporation from hydropower reservoirs (the `_zero` columns), as Water Ledger Michigan's MISO
  figure does; `incl_hydro` includes it.
