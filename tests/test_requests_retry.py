"""A busy service or a dropped connection is asked again, and "no such record" is not."""
import http.client as hc, io, json, urllib.error

import pytest

from waterledger_data import divisions, fetching, waters


def service(monkeypatch, module, failures):
    """urlopen fails with each of `failures` in turn, then answers. Returns the list of calls made."""
    calls = []

    def urlopen(*a, **k):
        calls.append(a)
        if len(calls) <= len(failures):
            raise failures[len(calls) - 1]
        return io.BytesIO(json.dumps({"ok": 1}).encode())
    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(module.time, "sleep", lambda s: None)
    return calls


def http(code):
    return urllib.error.HTTPError("u", code, "m", {}, None)


def test_echo_asks_again_after_a_timeout(monkeypatch):
    calls = service(monkeypatch, waters, [urllib.error.URLError("handshake timed out"), TimeoutError()])
    assert waters._get("https://x", {})["ok"] == 1 and len(calls) == 3


def test_echo_gives_up_in_the_end(monkeypatch):
    service(monkeypatch, waters, [TimeoutError()] * 6)
    with pytest.raises(TimeoutError):
        waters._get("https://x", {})


def test_rainfall_rides_out_a_long_busy_spell(monkeypatch):
    calls = service(monkeypatch, divisions, [http(429)] * 8 + [urllib.error.URLError("reset")])
    assert divisions.cag_json("https://x")["ok"] == 1 and len(calls) == 10


def test_rainfall_takes_no_record_as_the_answer(monkeypatch):
    calls = service(monkeypatch, divisions, [http(404)])
    with pytest.raises(urllib.error.HTTPError):
        divisions.cag_json("https://x")
    assert len(calls) == 1


def test_a_download_waits_out_a_service_that_is_down_and_is_kept_whole(monkeypatch, tmp_path):
    path = str(tmp_path / "a" / "b.json")
    calls = service(monkeypatch, fetching, [http(503), http(429), urllib.error.URLError("reset")])
    assert fetching.save("https://x", path) == path and len(calls) == 4
    assert json.load(open(path)) == {"ok": 1} and not (tmp_path / "a" / "b.json.part").exists()
    assert fetching.save("https://x", path) == path and len(calls) == 4      # already there: not asked again


def test_a_download_that_never_comes_leaves_nothing_behind(monkeypatch, tmp_path):
    path = tmp_path / "b.json"
    service(monkeypatch, fetching, [http(503)] * 8)
    with pytest.raises(urllib.error.HTTPError):
        fetching.save("https://x", str(path))
    assert not path.exists()


def test_no_such_record_is_not_asked_again(monkeypatch, tmp_path):
    calls = service(monkeypatch, fetching, [http(404)])
    with pytest.raises(urllib.error.HTTPError):
        fetching.save("https://x", str(tmp_path / "b.json"))
    assert len(calls) == 1


def test_an_error_page_with_a_200_is_not_kept(monkeypatch, tmp_path):
    bodies = [b"<html>busy</html>", b"", b"{not json", json.dumps({"ok": 1}).encode()]
    monkeypatch.setattr(fetching.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(bodies.pop(0)))
    monkeypatch.setattr(fetching.time, "sleep", lambda s: None)
    path = tmp_path / "b.json"
    fetching.save("https://x", str(path))
    assert json.load(open(path)) == {"ok": 1} and not bodies
    text = tmp_path / "pfds.txt"
    bodies[:] = [b"Error: no data", b"quantiles = [[1]]"]
    fetching.save("https://x", str(text), check=lambda d: b"quantiles" in d)
    assert text.read_bytes() == b"quantiles = [[1]]"


def test_a_dropped_connection_is_asked_again(monkeypatch, tmp_path):
    calls = service(monkeypatch, fetching, [hc.IncompleteRead(b"")])
    fetching.save("https://x", str(tmp_path / "b.json"))
    assert len(calls) == 2

