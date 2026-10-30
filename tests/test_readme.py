"""The README states the model version and the snapshot format; it is updated before every release (GOVERNANCE.md)."""
import pathlib
import re

from waterledger.national.snapshot import FORMAT
from waterledger_models import MODEL_VERSION

README = (pathlib.Path(__file__).parent.parent / "README.md").read_text()


def test_readme_states_the_current_versions():
    assert re.search(r"MODEL_VERSION`\*\* \(now ([\d.]+)\)", README).group(1) == MODEL_VERSION
    assert int(re.search(r"snapshot format version\*\* \(now (\d+),", README).group(1)) == FORMAT
