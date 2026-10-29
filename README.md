# Water Ledger

[![tests](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/tests.yml)
[![nightly](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml/badge.svg)](https://github.com/northlinehydrology/waterledger/actions/workflows/nightly.yml)

Public estimates of what large new water users (data centers first) mean for local water and streams, as separate Python
packages in one repo. They depend in one direction, so each can be installed on its own:

| Package | Import | What it holds | Depends on |
|---|---|---|---|
| `waterledger-models` | `waterledger_models` | the models: data center cooling water (towers, hybrid, closed loop, lake-source), staff water, site runoff quality | numpy |
| `waterledger-data` | `waterledger_data` | public U.S. data for any place: Census, EPA, USGS, NOAA, EIA; fetched once and cached | pandas, matplotlib |
| `waterledger` | `waterledger` | scenarios and the state-by-state builders behind [waterledger.org](https://waterledger.org); `waterledger build mi` | both |

```python
import waterledger as wl            # everything: wl.models, wl.data, wl.scenario, wl.states
```

Installing `waterledger` brings the other two; a modeling framework that only needs the models installs `waterledger-models`.

## Development

```bash
uv sync                  # one environment with all three packages, editable
uv run pytest            # unit tests and the golden model test
uv run pytest -m live    # every public data source still answers (nightly)
```

Checks: `tests` runs on every push (lint, tests on Python 3.11 to 3.13); `nightly` builds the packages, tests the built
wheels in a clean environment and checks the data sources, and opens an issue if anything fails; `publish` releases to PyPI
from a `v*` tag by trusted publishing. A change to the cooling model's numbers fails `test_golden` until `MODEL_VERSION` is
bumped and `tests/golden.py` is rerun.

Paths (download cache, site output) come from `WATERLEDGER_CACHE` / `WATERLEDGER_SITE` or a `waterledger.toml` (see
`waterledger_data.config`).

Model version 1.2. BSD 3-Clause.
