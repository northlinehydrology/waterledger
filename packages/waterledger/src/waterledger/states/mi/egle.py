"""Moved to waterledger_data.egle (design 0011); kept so `python -m waterledger.states.mi.egle` and old imports work through 3.x."""
import sys
import warnings

from waterledger_data.egle import COLUMNS, GOLF, reduce  # noqa: F401

warnings.warn("waterledger.states.mi.egle moved to waterledger_data.egle", DeprecationWarning, stacklevel=2)

if __name__ == "__main__":
    print(reduce(sys.argv[1], sys.argv[2]))
