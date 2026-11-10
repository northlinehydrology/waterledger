# waterledger-models

The models behind [Water Ledger](https://waterledger.org): the water large new users take, use up and send back,
starting with data centers.

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
- `grid`: water at the power plants supplying any user's hourly electricity, at grid level (design 0008): a balancing
  authority's table by month, UTC hour and the user's temperature, average and marginal, with `GridWaterBmi` (`[bmi]`).
- `datacenter.lake`: lake-source (once-through) cooling with forced lake evaporation (USGS heat-balance method).
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

`MODEL_VERSION` is Water Ledger's model version (1.12), which changes when the numbers do; the package version (semver)
changes with the code. They are independent. One model version covers every water user type; `MODELS` says which types a
version changes and which model's snapshots it reads (`snapshot_model()`): model 1.12 adds battery cell plants and reads 1.11's.
