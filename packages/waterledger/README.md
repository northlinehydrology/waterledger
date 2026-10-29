# waterledger

Public estimates of what large new water users mean for local water and streams, state by state; the builder behind
[waterledger.org](https://waterledger.org).

```python
import waterledger as wl
p = wl.scenario.place(wl.scenario.find("gaines charter township"))
wl.scenario.estimate(p, mw=300, cool="hybrid", dest="sewer")["wAvg"]     # million gallons a day: lo, mid, hi
```

```bash
waterledger build mi            # writes <site>/mi/data/*.json
```
