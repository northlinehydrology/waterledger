"""Time per cell on model 1.7: run_location (400 draws, every design) on 30 hourly years, alone and with k cells at once.
Usage: WEATHER=path.json python timing.py 6 12"""
import os, sys, time
from concurrent.futures import ProcessPoolExecutor
from waterledger_models import MODEL_VERSION
from waterledger_models.datacenter import cooling as cw
from waterledger_models.weather import from_open_meteo_json

F = os.environ.get("WEATHER", ".cache/42.88_-85.52.json")    # any 30-year Open-Meteo JSON; this one is West Michigan, from dc-cooling-water

def one(_=None):
    w = from_open_meteo_json(F)
    times = [str(t)[:16] for t in w.time.values]
    a = time.perf_counter()
    cw.run_location(times, w.air_temperature.values, w.relative_humidity.values)
    return time.perf_counter() - a

if __name__ == "__main__":
    print("model", MODEL_VERSION, "hours", len(from_open_meteo_json(F).time), flush=True)
    print("alone", round(one(), 1), "s", flush=True)
    for k in (int(a) for a in sys.argv[1:]):
        a = time.perf_counter()
        with ProcessPoolExecutor(k) as pool:
            each = list(pool.map(one, range(k)))
        wall = time.perf_counter() - a
        print(f"{k} at once: wall {wall:.0f} s, each {min(each):.0f}-{max(each):.0f} s, {wall / k:.1f} s per cell", flush=True)
