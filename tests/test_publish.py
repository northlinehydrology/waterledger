"""waterledger publish with a folder for the bucket and no network: it sends a checked snapshot whole, manifest and latest.json last,
and refuses an unchecked snapshot or a date already published."""
import json, os

import pytest

from waterledger.national import publish as P
from waterledger_data import r2


def _snapshot(root, checks=True):
    d = root / "WI" / "2026-11-06"
    (d / "cells").mkdir(parents=True)
    (d / "places.json").write_text("[]")
    (d / "cells" / "42.50_-88.00.json").write_text("{}")
    (d / "manifest.json").write_text(json.dumps({"model_version": "1.8", "checks": {"coverage": {}} if checks else None}))
    return root


class Recording(r2.FolderStore):
    def __init__(self, root):
        super().__init__(root)
        self.sent = []

    def _put_file(self, key, path, content_type=None, cache_control=None):
        self.sent.append((key, content_type, cache_control))
        super()._put_file(key, path)


def _web(published=()):
    old = json.dumps({"state": "WI", "latest": "2026-10-01", "current": "2026-10-01", "by_model": {"1.7": "2026-10-01"}}).encode()
    return lambda url: (200, b"{}") if any(p in url for p in published) else (200, old) if url.endswith("latest.json") else (404, None)


def test_sends_the_snapshot_whole_with_the_manifest_and_latest_last(tmp_path):
    root, bucket = _snapshot(tmp_path / "snap"), tmp_path / "bucket"
    build = tmp_path / "WI_build.json"
    build.write_text("{}")
    store = Recording(str(bucket))
    url = P.publish("wi", str(root), build=str(build), store=store, get=_web(), say=lambda m: None)
    assert url == "https://data.waterledger.org/WI/2026-11-06/manifest.json"
    keys = [k for k, _, _ in store.sent]
    assert keys[-2:] == ["WI/2026-11-06/manifest.json", "WI/latest.json"]
    assert set(keys[:-2]) == {"WI/2026-11-06/places.json", "WI/2026-11-06/cells/42.50_-88.00.json", "WI/2026-11-06/build.json"}
    assert all(t == "application/json" for _, t, _ in store.sent) and store.sent[-1][2] == "max-age=300"
    latest = json.load(open(bucket / "WI" / "latest.json"))
    assert latest == {"state": "WI", "latest": "2026-10-01", "current": "2026-11-06", "by_model": {"1.7": "2026-10-01", "1.8": "2026-11-06"}}
    assert not any(k.endswith(".sha256") for k in keys)


def test_refuses_a_date_already_published(tmp_path):
    store = Recording(str(tmp_path / "bucket"))
    with pytest.raises(SystemExit, match="already published"):
        P.publish("WI", str(_snapshot(tmp_path / "snap")), store=store, get=_web(["2026-11-06/manifest.json"]))
    assert store.sent == []


def test_refuses_a_snapshot_not_checked(tmp_path):
    with pytest.raises(SystemExit, match="check-snapshot"):
        P.publish("WI", str(_snapshot(tmp_path / "snap", checks=False)), store=Recording(str(tmp_path / "b")), get=_web())


def test_a_failed_file_stops_it_before_the_manifest(tmp_path):
    class Failing(Recording):
        def _put_file(self, key, path, content_type=None, cache_control=None):
            if key.endswith("places.json"):
                raise RuntimeError("upload failed")
            super()._put_file(key, path, content_type, cache_control)
    store = Failing(str(tmp_path / "bucket"))
    store.publish = lambda *a, **k: r2.Store.publish(store, *a, **{**k, "tries": 1})
    with pytest.raises(RuntimeError):
        P.publish("WI", str(_snapshot(tmp_path / "snap")), store=store, get=_web(), say=lambda m: None)
    assert not os.path.exists(tmp_path / "bucket" / "WI" / "2026-11-06" / "manifest.json")
    assert not os.path.exists(tmp_path / "bucket" / "WI" / "latest.json")


def test_from_env_names_the_bucket():
    store = r2.from_env({"WATERLEDGER_R2": "wrangler"}, bucket="waterledger-data")
    assert store.bucket == "waterledger-data"
    assert r2.from_env({"WATERLEDGER_R2": "wrangler"}).bucket == "waterledger-raw"
