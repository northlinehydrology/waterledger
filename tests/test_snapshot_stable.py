"""A snapshot file's checksum changes only when its data does."""
import hashlib
import json
import os
import subprocess
import sys

from waterledger.national.snapshot import _write
from waterledger_data import energy


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def test_key_order_does_not_change_a_file(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    _write(a, {"reaches": {"041": {"n": "x", "i": []}, "040": {"i": [], "n": "y"}}, "by_place": {}})
    _write(b, {"by_place": {}, "reaches": {"040": {"n": "y", "i": []}, "041": {"i": [], "n": "x"}}})
    assert _sha(a) == _sha(b)


def test_a_change_in_the_data_changes_the_file(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    _write(a, {"k": 1.0})
    _write(b, {"k": 1.5})
    assert _sha(a) != _sha(b)


def test_a_dict_built_from_a_set_is_the_same_under_any_hash_seed(tmp_path):
    """The cause in Virginia's receiving.json: a dict keyed through a set of strings comes out in an order that differs between Python runs."""
    code = ("import sys; from waterledger.national.snapshot import _write\n"
            "used = {f'0407{i:08d}' for i in range(200)}\n"
            "_write(sys.argv[1], {c: {'n': c} for c in used})\n")
    shas = []
    for seed in ("1", "2"):
        path = tmp_path / f"{seed}.json"
        subprocess.run([sys.executable, "-c", code, str(path)], env={**os.environ, "PYTHONHASHSEED": seed}, check=True)
        shas.append(_sha(path))
        assert len(json.load(open(path))) == 200
    assert shas[0] == shas[1]


def test_tied_utilities_come_out_in_one_order():
    us = [{"eia_id": 20, "name": "B", "share": 1.0}, {"eia_id": 10, "name": "A", "share": 1.0}, {"eia_id": None, "name": "C", "share": 1.0}, {"eia_id": 30, "name": "D", "share": 0.4}]
    want = ["A", "B", "C", "D"]
    assert [u["name"] for u in energy.in_order(us)] == want and [u["name"] for u in energy.in_order(us[::-1])] == want


def test_a_snapshot_writer_uses_sorted_keys_for_every_state(tmp_path):
    from waterledger.states.mi import snapshot as mi
    assert mi._write is _write
