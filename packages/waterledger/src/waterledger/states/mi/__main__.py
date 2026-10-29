"""python -m waterledger.states.mi [waters|power]: build Michigan's site data (all estimates when no part is given)."""
import sys

from waterledger.states.mi import build

{"waters": build.build_waters, "power": build.build_power}.get((sys.argv[1:] or [""])[0], build.main)()
