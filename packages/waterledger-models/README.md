# waterledger-models

The models behind [Water Ledger](https://waterledger.org): the water large new users take, use up and send back,
starting with data centers.

```bash
pip install waterledger-models          # numpy only
pip install "waterledger-models[all]"   # with xarray ensembles, BMI components and STAC publishing
```

- `datacenter.physics`: the cooling equations and parameter ranges, vectorized (Rutberg evaporative ratio as in USGS
  SIR 2013-5188, DOE FEMP water balance, Stull wet bulb).
- `datacenter.cooling`: the per-run Monte Carlo over decades of hourly weather for towers, hybrid, and closed loop with
  or without evaporative assist; staff water at the campus's size.
- `datacenter.lake`: lake-source (once-through) cooling with forced lake evaporation (USGS heat-balance method).
- `datacenter.ensemble`: vectorized ensembles as xarray, dask across locations (`[ensemble]`).
- `datacenter.bmi`: `CoolingWaterBmi` and `LakeCoolingBmi`, CSDMS BMI 2.0 with CSDMS Standard Names (`[bmi]`), on the public
  `ScalarPointBmi` base for components built on them.
  `CoolingWaterBmi` takes a withdrawal limit, dry mode and intake concentrations, and reports heat not removed, the return's
  temperature and the dissolved mass in it (design 0006); with no limit its outputs are unchanged.
- `datacenter.stac`: ensemble results as zarr with a STAC catalog (`[stac]`).
- `hydrology`: screening hydrology: SCS curve-number runoff, Theis drawdown and Glover stream depletion (on arrays).
- `runoff`: runoff, sediment, nutrients, road salt and fuel from a developed site.
- `quantile_mapping`: an ERA5 cell's hourly temperature and dew point corrected toward the shore stations within 100 km,
  for cells under 90% land (design 0005); the dew point never passes the temperature.
- `weather`: hourly weather from the Open-Meteo archive, its best match (ERA5, ERA5-Land and, from 2017, IFS HRES); humidity
  conversions (Bolton 1980) and a record's design dry-bulb.

`MODEL_VERSION` is Water Ledger's model version (1.8), which changes when the numbers do; the package version (semver)
changes with the code. They are independent.
