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

__version__ = "0.1.0"
