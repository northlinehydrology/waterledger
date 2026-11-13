"""Facility types (design 0010): what is proposed. Each type is a Facility subclass in its own module, registered by its `kind`; Site.facility
accepts any registered type (AnyFacility). A facility given without `kind` is read as a data center, as before the contract.

    base            the contract: Facility, register, REGISTRY
    data_center     DataCenter
    battery_cell    BatteryCellPlant (design 0009)
"""
from typing import Annotated, Union

from pydantic import Discriminator, Tag

from waterledger.facilities.base import REGISTRY, Facility, register
from waterledger.facilities.battery_cell import BatteryCellPlant
from waterledger.facilities.data_center import COOLING, DataCenter


def _kind(v):
    return v.get("kind", "data_center") if isinstance(v, dict) else getattr(v, "kind", None)


def any_facility():
    """The pydantic type for any registered facility, discriminated on `kind`."""
    return Annotated[Union[tuple(Annotated[cls, Tag(kind)] for kind, cls in REGISTRY.items())], Discriminator(_kind)]


AnyFacility = any_facility()

__all__ = ["REGISTRY", "Facility", "register", "DataCenter", "BatteryCellPlant", "COOLING", "AnyFacility", "any_facility"]
