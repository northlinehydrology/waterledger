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
    from waterledger_models import MODEL_VERSION
    import re
    old = {"state": "OH", "latest": "2026-11-01"}
    assert snapshot_for_model(old) == "2026-11-01"
    p = pointer(old, "OH", "2026-11-01.2", MODEL_VERSION)
    assert p["latest"] == "2026-11-01" and snapshot_for_model(p) == "2026-11-01.2"
    assert pointer(p, "OH", "2026-12-01", "99.0")["by_model"][MODEL_VERSION] == "2026-11-01.2"
    assert re.fullmatch(SNAPSHOT_ID, "2026-11-01.2") and re.fullmatch(SNAPSHOT_ID, "2026-11-01") and not re.fullmatch(SNAPSHOT_ID, "latest.json")


def test_an_estimate_reports_the_model_of_the_data_it_read():
    """A package reading older data says so: the numbers are that model's, as Michigan's estimate and design 0003 have it."""
    from waterledger.national import data
    from waterledger_models import MODEL_VERSION
    assert data.LiveData("OH").model_version() == MODEL_VERSION
    snap = data.SnapshotData.__new__(data.SnapshotData)
    snap.manifest = {"model_version": "1.5"}
    assert snap.model_version() == "1.5"
    source = open(data.__file__.replace("data.py", "provider.py")).read()
    assert "model_version=sd.model_version()" in source


def test_reading_another_models_snapshot_is_not_silent(capsys):
    from waterledger.national.data import snapshot_for_model
    from waterledger_models import MODEL_VERSION
    assert snapshot_for_model({"state": "OH", "latest": "a", "by_model": {MODEL_VERSION: "b"}}) == "b" and capsys.readouterr().err == ""
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
