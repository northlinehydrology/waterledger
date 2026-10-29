# waterledger

Public estimates of what large new water users mean for local water and streams, state by state. The front door to the
Water Ledger packages; [waterledger.org](https://waterledger.org) is powered by them.

```bash
pip install waterledger
```

```python
import waterledger as wl

place = wl.place("Columbus city, OH")            # Michigan, Ohio, Virginia and Texas; or wl.place(lat=..., lon=...)
est = wl.Site(place=place, facility=wl.DataCenter(it_mw=300, cooling="hybrid")).estimate()
est.water.withdrawn.avg          # Range(p10, p50, p90), million gallons a day
place.context().receiving.downstream     # the path the water takes, with impaired waters
```

Each state's data comes from a checked, dated snapshot at [data.waterledger.org](https://data.waterledger.org), cached on
first use; without one, the package can build the state from the public sources (`WATERLEDGER_FALLBACK=build`).

Commands: `waterledger build-state ST` (build any state from the public sources), `waterledger snapshot ST --out DIR`,
`waterledger check-snapshot ST --dir DIR`, and `waterledger build mi` (Water Ledger Michigan's site data).

Methods for each state: [waterledger.org/methods](https://waterledger.org/methods/). See the
[repository](https://github.com/northlinehydrology/waterledger) for the models, BMI components and design notes.
