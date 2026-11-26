"""A BMI component's state as one string, after the CSDMS proposal for get_state/set_state (bmi PR #112): "all information that
forms the state of the model ... as a single string", its format the modeller's, JSON suggested. Design 0024.

The string is JSON. Floats are written as their exact hexadecimal form (float.hex), so a state loads to the bit, infinity and NaN
included, and the JSON stays standard. A state carries a fingerprint of the component's settings (everything initialize set that
stepping does not change), so it loads only into a component initialized the same way: same class, same configuration, same forcing.
"""
import base64
import hashlib
import json

import numpy as np

FORMAT = "waterledger-models BMI state"
VERSION = 1


def pack(x):
    """A state value as JSON, exactly: floats as hex, arrays as their bytes, containers recursively. Raises TypeError for anything else."""
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return {"float": float(x).hex()}
    if isinstance(x, np.ndarray):
        a = np.ascontiguousarray(x)
        return {"ndarray": base64.b64encode(a.tobytes()).decode("ascii"), "dtype": a.dtype.str, "shape": list(a.shape)}
    if isinstance(x, (list, tuple)):
        return {"tuple" if isinstance(x, tuple) else "list": [pack(v) for v in x]}
    if isinstance(x, dict):
        if not all(isinstance(k, str) for k in x):
            raise TypeError("a state dict needs string keys")
        return {"dict": {k: pack(v) for k, v in x.items()}}
    raise TypeError(f"can't put a {type(x).__name__} in a state")


def unpack(x):
    """The inverse of pack."""
    if x is None or isinstance(x, (bool, int, str)):
        return x
    if "float" in x:
        return float.fromhex(x["float"])
    if "ndarray" in x:
        return np.frombuffer(base64.b64decode(x["ndarray"]), dtype=np.dtype(x["dtype"])).reshape(x["shape"]).copy()
    if "list" in x:
        return [unpack(v) for v in x["list"]]
    if "tuple" in x:
        return tuple(unpack(v) for v in x["tuple"])
    if "dict" in x:
        return {k: unpack(v) for k, v in x["dict"].items()}
    raise ValueError(f"not a packed state value: {x!r}")


def _canon(x, seen):
    """A settings value as plain JSON for a fingerprint: equal settings give equal results, arrays by their bytes."""
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, (int, np.integer)) and not isinstance(x, np.bool_):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, (float, np.floating)):
        return float(x).hex()
    if isinstance(x, (np.datetime64, np.timedelta64)):
        return str(x)
    if isinstance(x, np.ndarray):
        a = np.ascontiguousarray(x)
        if a.dtype == object:
            return ["object array", [_canon(v, seen) for v in a.ravel()], list(a.shape)]
        return ["ndarray", a.dtype.str, list(a.shape), hashlib.sha256(a.tobytes()).hexdigest()]
    if isinstance(x, (list, tuple)):
        return [_canon(v, seen) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((_canon(v, seen) for v in x), key=repr)
    if isinstance(x, dict):
        return sorted(([repr(k), _canon(v, seen)] for k, v in x.items()), key=lambda kv: kv[0])
    if id(x) in seen:
        return ["cycle", type(x).__qualname__]
    if hasattr(x, "__dict__"):
        return [type(x).__module__ + "." + type(x).__qualname__, _canon(vars(x), seen | {id(x)})]
    return [type(x).__qualname__, repr(x)]


def fingerprint(settings):
    """sha256 of a component's settings (a dict of attribute name -> value)."""
    text = json.dumps(_canon(settings, frozenset()), separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
