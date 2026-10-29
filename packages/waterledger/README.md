# waterledger

Public estimates of what large new water users mean for local water and streams, state by state. The front door to the
Water Ledger packages; [waterledger.org](https://waterledger.org) is powered by them.

```bash
pip install waterledger
```

```python
import waterledger as wl

place = wl.place("Gaines charter township, MI")
est = wl.Site(place=place, facility=wl.DataCenter(it_mw=300, cooling="hybrid")).estimate()
est.water.withdrawn.avg          # Range(p10, p50, p90), million gallons a day
place.context().receiving.downstream     # the path the water takes, with impaired waters
```

Builds a state's site data: `waterledger build mi`. Michigan is available now; other states come through the national tier.
See the [repository](https://github.com/northlinehydrology/waterledger) for the models, BMI components and design notes.
