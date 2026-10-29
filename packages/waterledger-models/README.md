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
- `datacenter.bmi`: `CoolingWaterBmi` and `LakeCoolingBmi`, CSDMS BMI 2.0 with CSDMS Standard Names (`[bmi]`).
- `datacenter.stac`: ensemble results as zarr with a STAC catalog (`[stac]`).
- `runoff`: runoff, sediment, nutrients, road salt and fuel from a developed site.
- `weather`: hourly ERA5 weather from the Open-Meteo archive.

`MODEL_VERSION` is Water Ledger's model version (1.2), which changes when the numbers do; the package version (semver)
changes with the code. They are independent.
