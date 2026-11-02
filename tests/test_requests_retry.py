"""A busy service or a dropped connection is asked again, and "no such record" is not."""
import io, json, urllib.error

import pytest

from waterledger_data import divisions, waters


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
