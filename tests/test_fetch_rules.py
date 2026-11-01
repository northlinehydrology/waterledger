"""A download is whole or it fails. Map services report errors with HTTP 200 and an "error" body, and mark a cut-off answer with exceededTransferLimit; neither may read as all there is."""
import glob, io, json, os

import pytest

import waterledger_data
from waterledger_data import places, receiving, waters, wastewater


def _serve(monkeypatch, answer):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(json.dumps(answer).encode()))
    monkeypatch.setattr(places.time, "sleep", lambda s: None)


@pytest.mark.parametrize("get", [waters._get, places._get])
def test_an_error_body_raises(monkeypatch, get):
    _serve(monkeypatch, {"error": {"code": 500, "message": "busy"}})
    with pytest.raises(RuntimeError, match="busy"):
        get("https://x.test/query", {"f": "json"})


@pytest.mark.parametrize("get", [waters._get, places._get])
def test_a_cut_off_answer_to_a_single_query_raises(monkeypatch, get):
    _serve(monkeypatch, {"features": [{"attributes": {}}], "exceededTransferLimit": True})
    with pytest.raises(RuntimeError, match="cut off"):
        get("https://x.test/query", {"f": "json"})


@pytest.mark.parametrize("get", [waters._get, places._get])
def test_a_cut_off_page_with_nothing_on_it_raises(monkeypatch, get):
    _serve(monkeypatch, {"features": [], "exceededTransferLimit": True})
    with pytest.raises(RuntimeError, match="cut off"):
        get("https://x.test/query", {"f": "json", "resultOffset": 0})


def _capped(total, cap):
    """A service with `total` records that returns at most `cap` at a time and flags the cut-off, whatever size was asked for."""
    def get(url, params, *a, **k):
        off, want = params.get("resultOffset", 0), params.get("resultRecordCount", cap)
        n = min(want, cap, total - off)
        rows = [{"attributes": {"i": off + j, "huc12": str(off + j), "Name": "n", "Type": "t", "Customers": 1, "Counties_1": ""}} for j in range(max(n, 0))]
        return {"features": rows, "exceededTransferLimit": off + n < total}
    return get


def test_paged_downloads_go_past_a_service_limit_smaller_than_the_page(monkeypatch):
    monkeypatch.setattr(waters, "_get", _capped(2500, 1000))
    assert len(waters._paged("https://x.test/query", "1=1")) == 2500
    monkeypatch.setattr(receiving, "_get", _capped(2500, 1000))
    assert len(receiving._paged("https://x.test/query", "1=1", "*", "OBJECTID")) == 2500


def test_every_paged_download_honors_the_cut_off_flag():
    root = os.path.dirname(waterledger_data.__file__)
    for path in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
        text = open(path).read()
        if "resultOffset" in text:
            assert text.count("exceededTransferLimit") >= text.count("resultOffset"), path


def test_a_short_echo_download_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(wastewater, "RAW", str(tmp_path))
    answers = iter([{"Results": {"QueryID": "1", "QueryRows": "3"}}, {"Results": {"Facilities": [{"a": 1}]}}, {"Results": {"Facilities": []}}])
    monkeypatch.setattr(wastewater, "_get", lambda *a, **k: next(answers))
    with pytest.raises(RuntimeError, match="1 of 3"):
        wastewater._echo("OH")


def test_michigans_echo_download_reads_every_page(monkeypatch):
    pages = {1: [{"a": 1}, {"a": 2}], 2: [{"a": 3}]}

    def get(url, params, *a, **k):
        return {"Results": {"QueryID": "1", "QueryRows": "3"}} if "get_facilities" in url else {"Results": {"Facilities": pages.get(params["pageno"], [])}}
    monkeypatch.setattr(waters, "_get", get)
    assert len(waters.echo_rows("MI")) == 3
