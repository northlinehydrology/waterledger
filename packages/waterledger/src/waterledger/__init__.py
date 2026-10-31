"""Water Ledger: public estimates of what large new water users mean for local water and streams.

    import waterledger as wl
    wl.models.datacenter.cooling     the models (package waterledger-models)
    wl.data.places                   public data for any place (package waterledger-data)
    wl.scenario                      a proposal at a place, as waterledger.org shows it
    wl.states.mi                     the builder for a state's site data (waterledger build mi)
"""
import waterledger_data as data
import waterledger_models as models
from waterledger import scenario, states
from waterledger.estimate import Estimate, Flow, Range, WaterUse
from waterledger.facility import DataCenter, Facility
from waterledger.place import Place, place
from waterledger.site import Site
from waterledger.context import Context

Estimate.model_rebuild()

__all__ = ["data", "models", "scenario", "states", "place", "Place", "Facility", "DataCenter", "Range", "Flow", "WaterUse", "Site", "Estimate", "Context"]
__version__ = "3.5.0"
