"""Which watersheds count for a place (waterledger_data.receiving.keeps)."""
import pandas as pd

from waterledger_data.receiving import keeps


def test_sliver_of_a_small_place_is_dropped():
    assert not keeps(0.005, 0.02)          # a boundary sliver: little of the place, little of the watershed


def test_a_watershed_over_one_percent_of_the_place_counts():
    assert keeps(0.01, 0.01)


def test_a_watershed_inside_a_very_large_county_counts():
    assert keeps(80 / 29000, 1.0)          # an 80 km2 HUC12 wholly inside Apache County, AZ (about 29,000 km2)
    assert keeps(0.003, 0.5)


def test_vectorized_over_overlaps():
    assert list(keeps(pd.Series([0.005, 0.02, 0.003]), pd.Series([0.1, 0.0, 0.9]))) == [False, True, True]
