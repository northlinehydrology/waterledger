"""Where a state's data comes from (design 0003): the hosted snapshot, the cached copy offline, and the fallback when neither
is there. A fake server stands in for data.waterledger.org."""
import hashlib, json, os, urllib.error

import pytest

from waterledger.national import data


def _serve(monkeypatch, files):
    """files: {path under the URL: bytes}; anything else is a 404. Returns the list of paths requested."""
    asked = []

    def get(url, timeout=30):
        path = url.split("://", 1)[1].split("/", 1)[1]
        asked.append(path)
        if path not in files:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return files[path]
    monkeypatch.setattr(data, "_get", get)
    return asked


def _snapshot(state, date, contents):
    """The files a snapshot publishes: latest.json, the manifest and each file."""
    out = {f"{state}/latest.json": json.dumps({"latest": date}).encode()}
    man = {"state": state, "date": date, "files": {}}
    for name, body in contents.items():
        out[f"{state}/{date}/{name}"] = body
        man["files"][name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    out[f"{state}/{date}/manifest.json"] = json.dumps(man).encode()
    return out


@pytest.fixture
def cache(tmp_path, monkeypatch):
    import waterledger_data.config as cfg
    monkeypatch.setattr(cfg, "CACHE", str(tmp_path))
    for v in ("WATERLEDGER_DATA_URL", "WATERLEDGER_DATA_DATE", "WATERLEDGER_DATA", "WATERLEDGER_FALLBACK"):
        monkeypatch.delenv(v, raising=False)
    data.state_data.cache_clear()
    yield tmp_path
    data.state_data.cache_clear()


def test_fetch_checks_and_caches(cache, monkeypatch):
    _serve(monkeypatch, _snapshot("OH", "2026-10-29", {"places.json": b'{"places": []}', "michigan/power.json": b"{}"}))
    folder = data.fetch_snapshot("OH")
    assert open(os.path.join(folder, "places.json"), "rb").read() == b'{"places": []}'
    assert os.path.exists(os.path.join(folder, "michigan", "power.json"))          # subfolders are created


def test_bad_checksum_is_refused(cache, monkeypatch):
    files = _snapshot("OH", "2026-10-29", {"places.json": b"good"})
    files["OH/2026-10-29/places.json"] = b"tampered"
    _serve(monkeypatch, files)
    with pytest.raises(data.DataUnavailable, match="checksum"):
        data.fetch_snapshot("OH")


def test_same_date_republish_is_picked_up(cache, monkeypatch):
    _serve(monkeypatch, _snapshot("OH", "2026-10-29", {"places.json": b"first"}))
    data.fetch_snapshot("OH")
    _serve(monkeypatch, _snapshot("OH", "2026-10-29", {"places.json": b"second"}))
    folder = data.fetch_snapshot("OH")
    assert open(os.path.join(folder, "places.json"), "rb").read() == b"second"


def test_cached_files_are_not_downloaded_again(cache, monkeypatch):
    files = _snapshot("OH", "2026-10-29", {"places.json": b"x"})
    _serve(monkeypatch, files)
    data.fetch_snapshot("OH")
    asked = _serve(monkeypatch, files)
    data.fetch_snapshot("OH")
    assert "OH/2026-10-29/places.json" not in asked


def test_offline_uses_the_newest_cached_snapshot(cache, monkeypatch, capsys):
    _serve(monkeypatch, _snapshot("OH", "2026-10-29", {"manifest_only.json": b"{}"}))
    data.fetch_snapshot("OH")
    _serve(monkeypatch, {})                                                     # offline
    sd = data.state_data("OH")
    assert isinstance(sd, data.SnapshotData) and sd.date == "2026-10-29"
    assert "using the cached OH snapshot" in capsys.readouterr().err


def test_no_snapshot_no_cache_fails_with_how_to_build(cache, monkeypatch):
    _serve(monkeypatch, {})
    with pytest.raises(data.DataUnavailable, match="WATERLEDGER_FALLBACK=build"):
        data.state_data("OH", fallback="fail")


def test_ask_declined_fails(cache, monkeypatch):
    _serve(monkeypatch, {})
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    with pytest.raises(data.DataUnavailable):
        data.state_data("OH", fallback="ask")


def test_ask_accepted_builds(cache, monkeypatch):
    _serve(monkeypatch, {})
    built = []
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr("waterledger.national.build.build", lambda state: built.append(state))
    sd = data.state_data("OH", fallback="ask")
    assert built == ["OH"] and isinstance(sd, data.LiveData)


def test_live_skips_snapshots(cache, monkeypatch):
    asked = _serve(monkeypatch, {})
    assert isinstance(data.state_data("OH", source="live"), data.LiveData) and asked == []
