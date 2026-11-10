"""A state answers the same from a snapshot or built live: both data classes offer the same methods."""
import pytest

from waterledger.national.data import LiveData, SnapshotData


def public(cls):
    return {k for k, v in vars(cls).items() if callable(v) and not k.startswith("_")}


def test_live_data_has_every_method_a_snapshot_has():
    assert public(SnapshotData) - public(LiveData) == set()


def test_a_package_reads_the_snapshot_for_its_own_model():
    from waterledger.national.data import snapshot_for_model
    from waterledger.national.snapshot import SNAPSHOT_ID, pointer
    from waterledger_models import snapshot_model
    import re
    old = {"state": "OH", "latest": "2026-11-01"}
    assert snapshot_for_model(old) == "2026-11-01"
    p = pointer(old, "OH", "2026-11-01.2", snapshot_model())
    assert p["latest"] == "2026-11-01" and snapshot_for_model(p) == "2026-11-01.2"
    assert pointer(p, "OH", "2026-12-01", "99.0")["by_model"][snapshot_model()] == "2026-11-01.2"
    assert re.fullmatch(SNAPSHOT_ID, "2026-11-01.2") and re.fullmatch(SNAPSHOT_ID, "2026-11-01") and not re.fullmatch(SNAPSHOT_ID, "latest.json")


def test_a_model_version_that_skips_the_snapshots_reads_the_last_rebuilt_ones(capsys, monkeypatch):
    """Model 1.12 adds battery cell plants and leaves every number the snapshots carry alone, so it reads model 1.11's snapshots and
    cell runs, without the note for another model's data; a version not in MODELS reads its own."""
    import waterledger_models as wm
    from waterledger.national import era5
    from waterledger.national.data import snapshot_for_model
    assert wm.MODEL_VERSION == "1.13" and wm.snapshot_model() == "1.11" == era5.RUN_MODEL and wm.snapshot_model("1.11") == "1.11"
    assert wm.snapshot_model("1.12") == "1.11"
    assert snapshot_for_model({"state": "OH", "latest": "a", "by_model": {"1.11": "b", "1.12": "c"}}) == "b" and capsys.readouterr().err == ""
    monkeypatch.setitem(wm.MODELS, "9.1", {"types": ("datacenter",), "snapshots": "9.1"})
    assert wm.snapshot_model("9.1") == "9.1" and wm.snapshot_model("9.2") == "9.2"


def test_each_model_version_names_its_types_and_a_rebuilt_snapshot_model():
    """MODELS: every entry names water user types the package has and the model of the snapshots it reads, which is no later than
    itself and rebuilt them (a skip never points at another skip)."""
    import waterledger_models as wm
    v = lambda s: tuple(int(x) for x in s.split("."))
    for version, m in wm.MODELS.items():
        assert m["types"] and all(hasattr(wm, t) for t in m["types"])
        assert v(m["snapshots"]) <= v(version) and wm.snapshot_model(m["snapshots"]) == m["snapshots"]


def test_an_estimate_reports_the_model_of_the_data_it_read():
    """A package reading older data says so: the numbers are that model's, as Michigan's estimate and design 0003 have it."""
    from waterledger.national import data
    from waterledger_models import snapshot_model
    assert data.LiveData("OH").model_version() == snapshot_model()
    snap = data.SnapshotData.__new__(data.SnapshotData)
    snap.manifest = {"model_version": "1.5"}
    assert snap.model_version() == "1.5"
    source = open(data.__file__.replace("data.py", "provider.py")).read()
    assert "model_version=sd.model_version()" in source


def test_reading_another_models_snapshot_is_not_silent(capsys):
    from waterledger.national.data import snapshot_for_model
    from waterledger_models import snapshot_model
    assert snapshot_for_model({"state": "OH", "latest": "a", "by_model": {snapshot_model(): "b"}}) == "b" and capsys.readouterr().err == ""
    assert snapshot_for_model({"state": "OH", "latest": "a", "current": "c", "by_model": {"0.1": "c"}}) == "c"
    assert "OH" in capsys.readouterr().err


def test_an_error_from_a_map_service_is_not_an_empty_answer(monkeypatch):
    """ArcGIS services report errors with HTTP 200 and an "error" body. Read as no features, one took 50 Michigan counties' household wells out of a build with no failure."""
    import io
    import json as js

    from waterledger_data import waters
    monkeypatch.setattr(waters.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(js.dumps({"error": {"code": 500, "message": "busy"}}).encode()))
    with pytest.raises(RuntimeError, match="busy"):
        waters._get("https://example.test/query", {"f": "json"})
