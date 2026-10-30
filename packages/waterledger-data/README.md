# waterledger-data

Public U.S. water data for any place, fetched once and cached, as used by [Water Ledger](https://waterledger.org).

```bash
pip install waterledger-data
```

| Module | What it fetches |
|---|---|
| `census` | places in any state: incorporated places, county subdivisions that are governments, counties (Census TIGERweb) |
| `supply` | community water system service areas, with SDWIS population and connections (EPA) |
| `wastewater` | sewer plants: CWNS 2022 design flows matched to ECHO recent flows and receiving waters, active permits only (EPA) |
| `receiving` | each place's HUC-12 watersheds, impairments and TMDLs by watershed (USGS WBD, EPA ATTAINS) |
| `trace` | the watershed tracer: follows a HUC-12 upstream or downstream across state lines with the impaired waters on the way (also the `waterledger-trace` command) |
| `divisions` | NOAA climate divisions, one long-record ISD station for each, county rainfall and Atlas 14 design storms |
| `climate` | hourly ERA5 (Open-Meteo) and NOAA ISD weather, Atlas 14 depths |
| `energy` | electric utility territories (HIFLD), EIA-861 sales and peaks, power-plant water per kWh by grid region (Siddik et al. 2024) |
| `power` | EIA-861 retail sales and residential use for any state (`state_retail_mwh`, `residential`); Michigan's MPSC territories |
| `places`, `waters` | Michigan's own layers (cities and townships, EGLE water use and wells) |

Downloads are cached under `WATERLEDGER_CACHE` (default `~/.cache/waterledger`) or the `cache` path in a
`waterledger.toml`. A build that stops part way resumes from the cache.
