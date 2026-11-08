"""EIA-930 headers to fuel classes (design 0007, part 1): both the pre-July-2024 headers and the split ones after,
EIA's typos included. No download."""
import pytest

from waterledger_data import grid930 as g


@pytest.mark.parametrize("header, cls", [
    ("Net Generation (MW) from Coal (Adjusted)", "coal"),
    ("Net Generation (MW) from Natural Gas (Adjusted)", "gas"),
    ("Net Generation (MW) from All Petroleum Products (Adjusted)", "oil"),
    ("Net Generation (MW) from Hydropower and Pumped Storage (Adjusted)", "hydro"),
    ("Net Generation (MW) from Hydropower Excluding Pumped Storage (Adjusted)", "hydro"),
    ("Net Generation (MW) from Pumped Storage  (Adjusted)", "hydro"),
    ("Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted)", "solar"),
    ("Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)", "solar"),
    ("Net Generation (MW) from Wind with Integrated Battery Storage (Adjusted)", "wind"),
    ("Net Generation (MW) from Battery Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Other Energy Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Unknown Energy Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Geothermal (Adjusted)", "geothermal"),
    ("Net Generation (MW) from Other Fuel Sources (Adjusted)", "other"),
    ("Net Generation (MW) from Unknown Fuel Sources (Adjusted)", "unknown"),
])
def test_fuel_class(header, cls):
    assert g.fuel_class(header) == cls


@pytest.mark.parametrize("header", ["Net Generation (MW) from Coal", "Net Generation (MW) from Coal (Imputed)",
                                    "Demand (MW) (Adjusted)", "Net Generation (MW) (Adjusted)"])
def test_not_a_fuel_column(header):
    assert g.fuel_class(header) is None


def test_unknown_fuel_word_is_an_error():
    with pytest.raises(ValueError):
        g.fuel_class("Net Generation (MW) from Tidal (Adjusted)")


def test_every_class_listed():
    assert {c for _, c in g._WORDS} == set(g.FUELS)
