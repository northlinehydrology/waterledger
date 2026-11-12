# waterledger-models

The models behind [Water Ledger](https://waterledger.org): the water large new users take, use up and send back,
starting with data centers and battery cell plants, and the power that serves them.

```bash
pip install waterledger-models          # numpy and numba
pip install "waterledger-models[all]"   # with xarray ensembles, BMI components and STAC publishing
```

- `datacenter.physics`: the cooling equations and parameter ranges, vectorized (Rutberg evaporative ratio as in USGS
  SIR 2013-5188, DOE FEMP water balance, Stull wet bulb), for each cooling plant inside the building (`PLANTS`: a shared
  facility loop, the default; a separate warm liquid loop; conventional chilled water; design 0007).
- `datacenter.kernel`: the Monte Carlo's hourly heat balance and water compiled with Numba, one pass per hour; it
  agrees with `physics` to the last bit or two and is tested against it for every design and plant.
- `datacenter.cooling`: the per-run Monte Carlo over decades of hourly weather for towers, hybrid, and closed loop with
  or without evaporative assist, for one plant (`run_location`) or each (`run_plants`); staff water at the campus's size.
- `battery`: battery cell plants (design 0009): `physics`, the plant's heat, electricity, fuel and water hour by hour per
  GWh/yr of cells for NMC or LFP cells, with returns to the sewer, the source or (with a permit of its own) a stream; `plant.run_location`, the Monte Carlo at
  one location, with the data centers' designs, full-capacity peak and water at the power plants; `bmi.BatteryCellBmi` (`[bmi]`).
- `gas`: new gas plants (design 0014): `physics`, output, fuel, heat and water hour by hour for the demand served, by
  technology (combined cycle, simple-cycle turbine, engine, fuel cell) and cooling design, where the wastewater goes;
  `plant.run_location`, the Monte Carlo on the shared runner; `bmi.GasPlantBmi` (`[bmi]`).
- `supply`: power supply scenarios (design 0014): `pv` (PVWatts, tested against pvlib) and `wind` (the IEA 3.4 MW reference
  curve) from ERA5 radiation and 100 m wind; `scenario`, resources and a residual rule as the shared runner's `extra=`, with
  sizing; `land`, solar and wind projects' land, runoff and construction water.
- `heat_rejection`: cooling towers, hybrid and dry coolers, assist's adiabatic pads, the loops' chillers, pumps and fans, their equipment ranges,
  psychrometrics and Latin hypercube sampling, shared by every water user; each user keeps its own operating settings
  (`OPERATING`: cycles of concentration, the hybrid's switch margin).
- `once_through`: once-through cooling from a Great Lake, shared by every water user: withdrawal from the heat and the rise,
  forced evaporation (Diehl et al. 2013), the lake's ranges and NOAA GLERL temperatures.
- `runs`: the Monte Carlo at one location for any water user type (design 0010): the draws, the standard loads, daily statistics,
  water at the power plants and the result names; a type supplies its designs, draws and each draw's hours. `extra=` sees every draw's
  hourly electricity.
- `daily`: daily totals and their statistics (average, 1-in-10-year peak day, months, worst year), shared by every water user.
- `grid`: water at the power plants supplying any user's hourly electricity, at grid level (design 0008): a balancing
  authority's table by month, UTC hour and the user's temperature, average and marginal, with `GridWaterBmi` (`[bmi]`);
  `RunWater`, the plant water in any user's Monte Carlo, which the data center and battery runs both call.
- `datacenter.lake`: lake-source (once-through) cooling for a campus, on `once_through`.
- `datacenter.ensemble`: vectorized ensembles as xarray, dask across locations (`[ensemble]`).
- `datacenter.bmi`: `CoolingWaterBmi` and `LakeCoolingBmi`, CSDMS BMI 2.0 with CSDMS Standard Names (`[bmi]`), on the public
  `ScalarPointBmi` base for components built on them.
  `CoolingWaterBmi` takes a withdrawal limit, dry mode and intake concentrations, and reports heat not removed, the return's
  temperature and the dissolved mass in it (design 0006); with no limit its outputs are unchanged.
- `datacenter.stac`: ensemble results as zarr with a STAC catalog (`[stac]`).
- `hydrology`: screening hydrology: SCS curve-number runoff, Theis drawdown and Glover stream depletion (on arrays).
- `runoff`: runoff, sediment, nutrients, road salt and fuel from a developed site.
- `quantile_mapping`: an ERA5 cell's hourly temperature and dew point corrected toward the stations within 100 km: shore
  stations for cells under 90% land, land stations for the rest (design 0005; land cells from model 1.9); temperature and dew
  point are each mapped on their own quantiles (from model 1.10), and the dew point never passes the temperature.
- `weather`: hourly weather from the Open-Meteo archive, its best match (ERA5, ERA5-Land and, from 2017, IFS HRES); humidity
  conversions (Bolton 1980) and a record's design dry-bulb.

`MODEL_VERSION` is Water Ledger's model version (1.15), which changes when the numbers do; the package version (semver)
changes with the code. They are independent. One model version covers every water user type; `MODELS` says which types a
version changes and which model's snapshots it reads (`snapshot_model()`): model 1.12 adds battery cell plants and reads 1.11's.
