# waterledger-models

The models behind [Water Ledger](https://waterledger.org): the water large new users take, use up and send back.
Light dependencies (numpy only), so other modeling frameworks can use them directly.

- `waterledger_models.datacenter.cooling`: weather-driven cooling water, hour by hour over decades of weather, for cooling
  towers, hybrid, and closed loop with or without evaporative assist; Monte Carlo over the published parameter ranges; staff water.
- `waterledger_models.datacenter.lake`: lake-source (once-through) cooling.
- `waterledger_models.runoff`: runoff, sediment, nutrients, road salt and fuel from a developed site.

`MODEL_VERSION` is Water Ledger's model version (currently 1.2); the package version follows it.
