"""The 2.0 objects validate their inputs, round-trip through JSON and publish a JSON Schema."""
import pytest
from pydantic import ValidationError

from waterledger.estimate import Flow, Range, WaterUse
from waterledger.facility import DataCenter


def test_data_center_validates():
    assert DataCenter(it_mw=300, cooling="hybrid").kind == "data_center"
    for bad in ({"it_mw": -5}, {"it_mw": 300, "cooling": "hybird"}, {"it_mw": 300, "pue": 1.2}):
        with pytest.raises(ValidationError):
            DataCenter(**bad)


def test_round_trip_and_schema():
    r = Range(p10=1.0, p50=2.0, p90=3.0)
    w = WaterUse(withdrawn=Flow(avg=r, peak_day=r), withdrawn_annual_mg=r, consumed=Flow(avg=r, peak_day=r),
                 returned=Flow(avg=r, peak_day=r), to_sewer=r)
    assert WaterUse.model_validate_json(w.model_dump_json()) == w
    assert Range.from_band({"lo": 1.0, "mid": 2.0, "hi": 3.0}) == r
    assert "it_mw" in DataCenter.model_json_schema()["properties"]
