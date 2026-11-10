"""Census names to a place's base name and kind, with no network."""
import pytest

from waterledger_data.census import _base_kind


@pytest.mark.parametrize("name, basename, base, kind", [
    ("Lebanon city", "Lebanon", "Lebanon", "city"),
    ("Gaines charter township", "Gaines", "Gaines", "charter township"),
    ("Indianapolis city (balance)", "Indianapolis city (balance)", "Indianapolis", "city"),
    ("Louisville/Jefferson County metro government (balance)", "Louisville/Jefferson County metro government (balance)",
     "Louisville/Jefferson County metro government", "consolidated government"),
])
def test_base_and_kind(name, basename, base, kind):
    assert _base_kind({"NAME": name, "BASENAME": basename}) == (base, kind)
