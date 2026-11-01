"""The workflow's upload step, run with a stand-in for aws: only a real not-found counts as absent, so a failed read can't overwrite a snapshot or move older packages onto a new model."""
import os, re, stat, subprocess

import pytest

WORKFLOW = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows", "build-state.yml")
AWS = """#!/bin/bash
echo "$*" >> "$LOG"
if [[ "$*" == *head-object* ]]; then
  case "$*" in *latest.json*) r=$LATEST;; *) r=$MANIFEST;; esac
  case "$r" in ok) echo '{}'; exit 0;; 404) echo "An error occurred (404) when calling the HeadObject operation: Not Found" >&2; exit 254;; *) echo "An error occurred (500) when calling the HeadObject operation: Internal Error" >&2; exit 254;; esac
fi
if [[ "$*" == *"latest.json old-latest.json"* ]]; then
  [ "$LATEST_CP" = fail ] && { echo "fatal error: 500" >&2; exit 1; }
  echo '{"latest": "old"}' > old-latest.json
fi
exit 0
"""
UV = """#!/bin/bash
echo "uv $*" >> "$LOG"
echo '{}'
"""


def _step():
    text = open(WORKFLOW).read()
    head = text.index("- name: Upload to R2")
    block = text[text.index("run: |", head):].split("\n")[1:]
    return "\n".join(line[10:] for line in block if line.startswith(" " * 10) or not line.strip())


def _run(tmp_path, **env):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    for name, body in (("aws", AWS), ("uv", UV)):
        (bin_ / name).write_text(body)
        (bin_ / name).chmod((bin_ / name).stat().st_mode | stat.S_IEXEC)
    (tmp_path / "snapshot" / "OH" / "2026-11-01.2").mkdir(parents=True)
    log = tmp_path / "log"
    log.write_text("")
    r = subprocess.run(["bash", "-e", "-c", _step()], cwd=tmp_path, capture_output=True, text=True,
                       env={**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "LOG": str(log), "ST": "OH", "R2": "https://r2",
                            "MANIFEST": "404", "LATEST": "ok", "LATEST_CP": "ok", **env})
    return r.returncode, log.read_text()


def test_new_snapshot_uploads_and_keeps_the_old_pointer(tmp_path):
    code, log = _run(tmp_path)
    assert code == 0 and "s3://waterledger-data/OH/2026-11-01.2" in log and "--from old-latest.json" in log and "old-latest.json" in log


def test_a_published_snapshot_is_refused(tmp_path):
    code, log = _run(tmp_path, MANIFEST="ok")
    assert code != 0 and "cp --recursive" not in log


def test_a_failed_check_is_not_taken_for_absent(tmp_path):
    code, log = _run(tmp_path, MANIFEST="500")
    assert code != 0 and "cp --recursive" not in log
