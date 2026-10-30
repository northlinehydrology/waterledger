"""build-state MI and build mi run Michigan's own build; other states stay on the national tier (design 0003, decision 8)."""
from types import SimpleNamespace

import pytest

from waterledger import cli


@pytest.fixture
def calls(monkeypatch):
    ran = []
    mi = SimpleNamespace(main=lambda: ran.append("estimates"), build_waters=lambda: ran.append("waters"), build_power=lambda: ran.append("power"))
    monkeypatch.setattr(cli, "builder", lambda state: mi)
    import waterledger.national.build as nb
    monkeypatch.setattr(nb, "build", lambda state, out, run_checks: ran.append(("national", state)))
    return ran


@pytest.mark.parametrize("state", ["MI", "mi"])
def test_build_state_michigan_is_michigans_build(calls, state):
    cli.main(["build-state", state])
    assert calls == ["estimates", "waters", "power"]


def test_build_mi_still_works(calls):
    cli.main(["build", "mi"])
    assert calls == ["estimates", "waters", "power"]
    calls.clear()
    cli.main(["build", "mi", "waters"])
    assert calls == ["waters"]


def test_other_states_stay_national(calls):
    cli.main(["build-state", "OH"])
    assert calls == [("national", "OH")]
