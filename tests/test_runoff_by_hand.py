"""Runoff worked by hand, with the numbers written out here, not read from the code's constants, so a wrong constant in the code fails.
A 200-acre site, half of it roofs and paving afterward, in 36 inches of rain a year."""
import pytest

from waterledger_models import hydrology, runoff

R_IMP = 36 * 0.9 * 0.95     # 30.78 in a year off roofs and paving
R_TURF = 36 * 0.9 * 0.20    # 6.48 in off turf
R_WOODS = 36 * 0.9 * 0.03   # 0.972 in off woods


def test_runoff_depths_by_cover():
    assert R_IMP == pytest.approx(30.78) and R_TURF == pytest.approx(6.48) and R_WOODS == pytest.approx(0.972)
    assert runoff.runoff_in(36, 0.5) == pytest.approx(0.5 * 30.78 + 0.5 * 6.48)      # 18.63
    assert runoff.runoff_in(36, 0.02, "farm") == pytest.approx(0.02 * 30.78 + 0.98 * 6.48)     # farmland as turf [A]: 6.966
    assert runoff.runoff_in(36, 0.01, "woods") == pytest.approx(0.01 * 30.78 + 0.99 * 0.972)   # 1.27008
    assert runoff.runoff_in(36, 0.60, "built") == pytest.approx(0.60 * 30.78 + 0.40 * 6.48)    # 21.06


def test_runoff_volume_before_and_after():
    L = runoff.loads(200, 36)["runoff_gal"]
    assert L["after"][1] == pytest.approx(200 * 18.63 * 27154)                   # 101,175,804 gallons
    assert L["now"][1] == pytest.approx(200 * 6.966 * 27154)                     # 37,830,953 gallons
    assert L["after"][1] / L["now"][1] == pytest.approx(18.63 / 6.966)           # 2.67 times, not 7
    w = runoff.loads(200, 36, before="woods")["runoff_gal"]
    assert w["now"][1] == pytest.approx(200 * 1.27008 * 27154)                   # woods shed far less than fields


def test_water_closes_runoff_stays_a_part_of_the_rain():
    for cover in ("turf", "farm", "woods", "built"):
        for imp in (0.0, 0.5, 1.0):
            assert 0 < runoff.runoff_in(36, imp, cover) < 36


def test_row_crops_shed_more_than_lawn_in_a_storm():
    assert hydrology.CN_PRE_PERV == 78 and hydrology.CN_POST_PERV == 65
    s = 1000 / 78 - 10                                                           # 2.8205 in; TR-55
    assert hydrology.scs_runoff_in(5, 78) == pytest.approx((5 - 0.2 * s) ** 2 / (5 + 0.8 * s))
    assert hydrology.scs_runoff_in(5, 78) > hydrology.scs_runoff_in(5, 65)
