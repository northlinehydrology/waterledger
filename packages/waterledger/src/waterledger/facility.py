"""Facilities: what is proposed. The types live in waterledger.facilities (design 0010); this module keeps the names it always had."""
from waterledger.facilities import COOLING, AnyFacility, BatteryCellPlant, DataCenter, Facility

__all__ = ["COOLING", "Facility", "DataCenter", "BatteryCellPlant", "AnyFacility"]
