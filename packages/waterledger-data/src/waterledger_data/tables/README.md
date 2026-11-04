# Small reference tables shipped with waterledger-data

- `grid_water_2022.csv`: water used at power plants per kWh of electricity used, by balancing authority, 2022 annual
  means weighted by hourly electricity use. Derived from Siddik, M. A. B., Shehabi, A., Rao, P., & Marston, L. T. (2024),
  "Spatially and temporally detailed water and carbon footprints of U.S. electricity generation and use", Water Resources
  Research 60(12), https://doi.org/10.1029/2024WR038350; data: LBNL Water IMPACT (HydroShare
  https://www.hydroshare.org/resource/2f54448714554f83b9655da108f0fd3f/, file water_impact_consumption_2022_v1.1).
  `excl_hydro` leaves out evaporation from hydropower reservoirs (the `_zero` columns), as Water Ledger Michigan's MISO
  figure does; `incl_hydro` includes it.
- `state_power_water_2024.csv`: water at power plants per kWh used in each state, consumed and withdrawn, with withdrawn split into fresh and saline; built by `docs/methods/power_water/`.
- `state_fuel_water_2024.csv`: each state's coal and nuclear plants as power options: Macknick et al. (2012) factors for how they are cooled, weighted by 2024 generation (EIA), with the plants' screened reports as a check; built by `docs/methods/power_water/fuels.py`.
- `era5_conus.npz`: ERA5's land-sea mask (`lsm`, the invariant field `land_sea_mask`) and surface elevation (`orog_m`, `geopotential_at_surface` / 9.80665) on the 0.25-degree grid over 24-50 N, 125-66 W (`ci0`, `cj0`: the first row's and column's latitude and longitude x 4), for `era5.cell`'s land rule and quantile mapping's lapse to the cell's elevation. Read from Google's ARCO-ERA5 copy (gs://gcp-public-data-arco-era5) on Nov 3, 2026; Hersbach et al. (2023), C3S Climate Data Store, doi:10.24381/cds.adbb2d47, CC-BY 4.0.
