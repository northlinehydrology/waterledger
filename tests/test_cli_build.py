"""build-state MI and build mi run Michigan's own build; other states stay on the national tier (design 0003, decision 8)."""
from types import SimpleNamespace

import pytest

from waterledger import cli


@pytest.fixture
def calls(monkeypatch):
    ran = []
    import waterledger.states.mi.fetch as fetch
    monkeypatch.setattr(fetch, "fetch_all", lambda: ran.append("fetch"))
    mi = SimpleNamespace(main=lambda: ran.append("estimates"), build_waters=lambda: ran.append("waters"), build_power=lambda: ran.append("power"))
    monkeypatch.setattr(cli, "builder", lambda state: mi)
    import waterledger.national.build as nb
    monkeypatch.setattr(nb, "build", lambda state, out, run_checks: ran.append(("national", state)))
    return ran


@pytest.mark.parametrize("state", ["MI", "mi"])
def test_build_state_michigan_is_michigans_build(calls, state):
    cli.main(["build-state", state])
    assert calls == ["fetch", "estimates", "waters", "power"]


def test_build_mi_still_works(calls):
    cli.main(["build", "mi"])
    assert calls == ["estimates", "waters", "power"]
    calls.clear()
    cli.main(["build", "mi", "waters"])
    assert calls == ["waters"]


def test_other_states_stay_national(calls):
    cli.main(["build-state", "OH"])
    assert calls == [("national", "OH")]


def _steps(monkeypatch, ran, fails=0):
    from waterledger.states.mi import fetch
    left = [fails]

    def a():
        ran.append("a")

    def b():
        ran.append("b")
        if left[0]:
            left[0] -= 1
            raise OSError("busy")
    monkeypatch.setattr(fetch, "STEPS", [(a, ["waters/a.json"]), (b, ["waters/b_*.json"])])
    return fetch


def test_fetch_skips_what_is_cached(tmp_path, monkeypatch):
    ran = []
    fetch = _steps(monkeypatch, ran)
    (tmp_path / "waters").mkdir()
    (tmp_path / "waters" / "a.json").write_text("{}")
    fetch.fetch_all(str(tmp_path))
    assert ran == ["b"]


def test_fetch_tries_again_then_stops(tmp_path, monkeypatch):
    ran = []
    fetch = _steps(monkeypatch, ran, fails=1)
    fetch.fetch_all(str(tmp_path), tries=2, wait=0)
    assert ran == ["a", "b", "b"]
    ran.clear()
    fetch = _steps(monkeypatch, ran, fails=5)
    with pytest.raises(OSError):
        fetch.fetch_all(str(tmp_path), tries=2, wait=0)
