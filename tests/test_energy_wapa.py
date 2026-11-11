"""WAPA's control area by state: the territory layer labels it the Desert Southwest's (WALC) everywhere."""
from waterledger_data import energy as en


def test_wapa_in_the_upper_great_plains_is_spp_and_elsewhere_unchanged():
    def rows():
        return {"1": [{"name": "WAPA-- WESTERN AREA POWER ADMINISTRATION", "balancing_authority": "WALC"},
                      {"name": "Northern States Power Co - Minnesota", "balancing_authority": "MISO"}]}
    mn = en._wapa("MN", rows())["1"]
    assert [u["balancing_authority"] for u in mn] == ["SWPP", "MISO"]
    assert en._wapa("AZ", rows())["1"][0]["balancing_authority"] == "WALC"
