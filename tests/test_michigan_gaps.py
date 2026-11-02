"""Michigan's gaps against the other states: paths past the state line, assessed flags, USGS county use."""
from waterledger_data import receiving as rc

H = {"a": {"n": "A", "t": "b", "a": 1}, "b": {"n": "B", "t": None, "a": 0, "i": [["ecoli", 0, []]]}, "c": {"n": "C", "t": None, "a": 0}, "home": {"n": "Back in the state", "t": "c", "a": 1}, "idle": {"n": "Nothing drains here", "t": None, "a": 0}}


def _trace(code):
    return {"b": [{"code": "b", "name": "B", "listings": [], "assessed": False}, {"code": "x", "name": "X in Ohio", "listings": [["nutrients", 1, []]], "assessed": True},
                  {"code": "y", "name": "Y in Ohio", "listings": [], "assessed": False}, {"code": "home", "name": "Back", "listings": [], "assessed": True}],
            "c": [{"code": "c", "name": "C", "listings": [], "assessed": False}]}[code]


def test_a_path_goes_past_the_line_and_rejoins_its_own_links():
    out = rc.past_the_line(H, ["a", "c"], trace=_trace)
    path, h = [], "a"
    while h:
        path.append(h)
        h = out[h]["t"]
    assert path == ["a", "b", "x", "y", "home", "c"]
    assert out["x"] == {"n": "X in Ohio", "t": "y", "a": 1, "o": 1, "i": [["nutrients", 1, []]]} and out["y"] == {"n": "Y in Ohio", "t": "home", "a": 0, "o": 1}
    assert "o" not in out["home"] and out["home"]["n"] == "Back in the state"          # the state's own record stands


def test_only_paths_from_places_are_traced_and_the_table_is_not_changed():
    seen = []
    rc.past_the_line(H, ["c"], trace=lambda code: seen.append(code) or _trace(code))
    assert seen == ["c"] and H["b"]["t"] is None


def test_usgs_failure_leaves_michigan_answering(monkeypatch):
    from waterledger.national import provider as np
    from waterledger.states.mi import provider as mp

    def boom(*a):
        raise RuntimeError("no snapshot")
    monkeypatch.setattr(np, "county_water_use", boom)
    assert mp._usgs_water_use("26081") is None
    monkeypatch.setattr(np, "county_water_use", lambda st, f: ("egle", "usgs" if st == "MI" and f == "26081" else None))
    assert mp._usgs_water_use("26081") == "usgs"


def test_every_parameter_has_its_sources_and_none_is_stale():
    from waterledger.states.mi.build import PARAM_SOURCES, SOURCES, WATER_SOURCES
    from waterledger_models import runoff
    from waterledger_models.datacenter import physics
    assert set(PARAM_SOURCES) == set(physics.PARAMETERS) | set(physics.STAFF_PARAMETERS)
    assert {s for ids in PARAM_SOURCES.values() for s in ids} <= set(SOURCES)
    assert PARAM_SOURCES["coc"] == ["lei2021", "han2026", "femp_bmp10"] and "lower" in SOURCES["femp_bmp10"][0]
    assert not any("Vantage" in c for c, _ in SOURCES.values())
    cited = lambda x: ({s for v in x.values() for s in cited(v)} | set(x.get("sources", []))) if isinstance(x, dict) else set()
    assert cited(runoff.PARAMS) <= WATER_SOURCES <= set(SOURCES)
