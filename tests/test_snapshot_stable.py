"""A snapshot file's checksum changes only when its data does."""
import hashlib
import json
import os
import subprocess
import sys

from waterledger.national.snapshot import _write


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
