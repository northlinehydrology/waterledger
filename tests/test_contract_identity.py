"""Design 0010's identity test: whole estimates in every published state, as they were before the facility contract (tests/data/
estimates_before_contract.json.gz, written by tests/contract_reference.py from 3.21.0), are unchanged to the last bit. Every value the record holds must
match; names added since (the contract's optional fields: WaterUse.to_source, Electricity.fuel_mw, Estimate.extras) are allowed. A refusal must
still be refused with the same message. Nightly, with the states' snapshots (pytest -m live)."""
import gzip
import json
import os

import pytest

from contract_reference import PLACES, cases

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(HERE, "data", "estimates_before_contract.json.gz")
ADDED = {"to_source": None, "fuel_mw": None, "extras": {}}       # the contract's additions, at their values for a data center

pytestmark = pytest.mark.live


def held(want, got, path=""):
    """Every value in `want` is in `got`, equal to the bit; `got` may add the contract's names at their data center values."""
    if isinstance(want, dict):
        assert isinstance(got, dict), path
        for k in want:
            assert k in got, f"{path}/{k} missing"
            held(want[k], got[k], f"{path}/{k}")
        for k in set(got) - set(want):
            assert k in ADDED and got[k] == ADDED[k], f"{path}/{k} added: {got[k]!r}"
    elif isinstance(want, list):
        assert isinstance(got, list) and len(got) == len(want), path
        for i, (a, b) in enumerate(zip(want, got)):
            held(a, b, f"{path}[{i}]")
    else:
        assert got == want, f"{path}: {got!r} != {want!r}"


def _record():
    if not os.path.exists(RECORD):
        return {}
    with gzip.open(RECORD, "rt") as f:
        return json.load(f)


@pytest.mark.parametrize("state", sorted(PLACES))
def test_estimates_match_the_record(state):
    R = {k: v for k, v in _record().items() if k.split("|")[0].endswith(f", {state}")}
    assert R, f"no record for {state}"
    C = cases()
    for key, want in R.items():
        if key.endswith("|local"):
            continue                                # the model run at the place: test_local_estimates_match_the_record
        try:
            got = {"ok": C[key]()}
        except Exception as e:                      # noqa: BLE001
            got = {"error": f"{type(e).__name__}: {e}"}
        held(want, json.loads(json.dumps(got)), key)


def test_local_estimates_match_the_record():
    R = {k: v for k, v in _record().items() if k.endswith("|local")}
    C = cases()
    for key, want in R.items():
        held(want, json.loads(json.dumps({"ok": C[key]()})), key)
