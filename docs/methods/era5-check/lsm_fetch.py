"""ERA5's land-sea mask (one 0.25-degree global field, about 0.8 MB compressed) from Google's public ARCO-ERA5 copy, saved as DIR/lsm/lsm.npz
with its latitude (90 to -90) and longitude (0 to 359.75). Usage: python lsm_fetch.py DIR"""
import os, sys, urllib.request
import numcodecs, numpy as np

B = "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
out = os.path.join(sys.argv[1], "lsm")
os.makedirs(out, exist_ok=True)
get = lambda path, shape: np.frombuffer(numcodecs.Blosc().decode(urllib.request.urlopen(f"{B}/{path}").read()), dtype="<f4").reshape(shape)
np.savez(os.path.join(out, "lsm.npz"), lsm=get("land_sea_mask/876576.0.0", (721, 1440)), lat=get("latitude/0", (721,)), lon=get("longitude/0", (1440,)))
