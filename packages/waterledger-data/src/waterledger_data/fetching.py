"""Saving a download to the cache: asked again while a service is busy or down, and never left half written, so a cache kept after a failed build holds only whole files."""
import http.client, json, os, time, urllib.error, urllib.request


def _usable(data, path):
    """An error page can come back as a 200: it mustn't be kept as if it were the data."""
    if not data:
        raise ValueError(f"empty answer for {path}")
    if path.endswith(".json"):
        json.loads(data)
    elif data.lstrip()[:1] == b"<":
        raise ValueError(f"a web page instead of the data for {path}")


def save(url, path, timeout=300, tries=8, wait=30, check=None):
    """Download `url` to `path`, unless it is already there. Waits between tries double up to 5 minutes, about 20 minutes in all. A 4xx other than 429 won't change, so it isn't asked again.
    `check(data)` is false for an answer that isn't the data."""
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "waterledger"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            _usable(data, path)
            if check and not check(data):
                raise ValueError(f"not the expected data for {path}")
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
            return path
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429 or attempt == tries - 1:
                raise
        except (OSError, http.client.HTTPException, ValueError):
            if attempt == tries - 1:
                raise
        time.sleep(min(wait * 2 ** attempt, 300))
