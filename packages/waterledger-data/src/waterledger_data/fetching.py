"""Saving a download to the cache: asked again while a service is busy or down, and never left half written, so a cache kept after a failed build holds only whole files."""
import os, time, urllib.error, urllib.request


def save(url, path, timeout=300, tries=8, wait=30):
    """Download `url` to `path`, unless it is already there. Waits between tries double up to 5 minutes, about 20 minutes in all. A 4xx other than 429 won't change, so it isn't asked again."""
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "waterledger"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
            return path
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429 or attempt == tries - 1:
                raise
        except OSError:
            if attempt == tries - 1:
                raise
        time.sleep(min(wait * 2 ** attempt, 300))
