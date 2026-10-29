"""Where Water Ledger keeps its downloads and writes its site data, and other local paths.

Resolved once, at import, from the first of:
  1. environment variables: WATERLEDGER_CACHE, WATERLEDGER_SITE, and WATERLEDGER_<NAME> for any other setting;
  2. a waterledger.toml in the working directory or a parent, whose [paths] table names them (relative to the file):
         [paths]
         cache = "data/raw"
         site = "site"
  3. defaults: ~/.cache/waterledger for downloads and ./site for the site.
"""
import os
import tomllib


def _find(start=None):
    d = os.path.abspath(start or os.getcwd())
    while True:
        f = os.path.join(d, "waterledger.toml")
        if os.path.exists(f):
            return f
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


CONFIG_FILE = _find()
_paths = {}
if CONFIG_FILE:
    with open(CONFIG_FILE, "rb") as f:
        _paths = {k: os.path.normpath(os.path.join(os.path.dirname(CONFIG_FILE), v)) for k, v in tomllib.load(f).get("paths", {}).items()}


def setting(name, default=None):
    """A path setting: WATERLEDGER_<NAME> in the environment, else waterledger.toml's [paths], else `default`."""
    return os.environ.get("WATERLEDGER_" + name.upper()) or _paths.get(name) or default


CACHE = setting("cache", os.path.join(os.path.expanduser("~"), ".cache", "waterledger"))
SITE = setting("site", os.path.abspath("site"))
