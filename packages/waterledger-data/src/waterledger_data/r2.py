"""The private raw store on Cloudflare R2 (bucket waterledger-raw), an optional step: off unless it is set up.

    store = r2.from_env()       # None when off
    store.put(key, path)        # skipped when R2 already has the file with the same sha256; a failure warns and returns False
    store.get(key, path)        # True if R2 had it (checked against its sha256), False if not

How it is turned on (the first that applies):
- S3 API: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY in the environment (the names the build-state workflow uses),
  ideally a token limited to this bucket. Needs boto3 (waterledger-data[r2]).
- wrangler: WATERLEDGER_R2=wrangler, using the wrangler login already on the machine (`npx wrangler r2 object put|get ... --remote`).
- A folder, for tests and dry runs: WATERLEDGER_R2=dir:/some/path.
WATERLEDGER_R2=off turns it off whatever else is set; WATERLEDGER_R2_BUCKET names another bucket.

Each object has a sidecar <key>.sha256 holding its checksum, written after the object itself, so a file is skipped only when R2 holds that
exact file, and a half-finished upload is never mistaken for a whole one. Nothing here holds or asks for credentials.
"""
import hashlib, os, shutil, subprocess, sys, tempfile

BUCKET = "waterledger-raw"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _warn(msg):
    print(f"Water Ledger R2: {msg}", file=sys.stderr)


class Store:
    """put/get/exists over a backend's three primitives: _put_file, _get_file (False if missing) and their names."""
    name = "store"

    def checksum(self, key):
        """The sha256 R2 holds for `key`, or None if it has none."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sha")
            return open(p).read().strip() if self._get_file(key + ".sha256", p) else None

    def put(self, key, path):
        """Upload `path` to `key` unless R2 already has it with the same checksum. True when R2 holds it after; a failure warns, keeps the
        local file and returns False, so a run never stops for it."""
        try:
            sha = sha256(path)
            if self.checksum(key) == sha:
                return True
            self._put_file(key, path)
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "sha")
                open(p, "w").write(sha)
                self._put_file(key + ".sha256", p)
            return True
        except Exception as e:                       # noqa: BLE001  any failure: warn and go on
            _warn(f"could not upload {key} ({type(e).__name__}: {str(e)[:200]}); the local file is kept")
            return False

    def get(self, key, path):
        """Download `key` to `path` if R2 has it and it matches its checksum. False when R2 has no such key; a failure warns and returns False."""
        try:
            sha = self.checksum(key)
            if sha is None:
                return False
            if os.path.exists(path) and sha256(path) == sha:
                return True
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            part = path + ".r2part"
            if not self._get_file(key, part):
                return False
            if sha256(part) != sha:
                os.remove(part)
                raise ValueError("checksum does not match")
            os.replace(part, path)
            return True
        except Exception as e:                       # noqa: BLE001
            _warn(f"could not download {key} ({type(e).__name__}: {str(e)[:200]})")
            return False


class FolderStore(Store):
    """A local folder standing in for the bucket (WATERLEDGER_R2=dir:PATH)."""
    name = "folder"

    def __init__(self, root):
        self.root = root

    def _put_file(self, key, path):
        dst = os.path.join(self.root, key)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(path, dst + ".tmp")
        os.replace(dst + ".tmp", dst)

    def _get_file(self, key, path):
        src = os.path.join(self.root, key)
        if not os.path.exists(src):
            return False
        shutil.copyfile(src, path)
        return True


class WranglerStore(Store):
    """Through the wrangler login on this machine. wrangler has no head or list for R2 objects, so a missing key is told by its error
    ("The specified key does not exist.", wrangler 4). Each call starts wrangler, about 2-3 s."""
    name = "wrangler"
    MISSING = ("does not exist", "not found", "nosuchkey", "404")

    def __init__(self, bucket, run=subprocess.run, command=("npx", "--yes", "wrangler")):
        self.bucket, self._run, self.command = bucket, run, list(command)

    def _call(self, *args):
        return self._run([*self.command, "r2", "object", *args, "--remote"], capture_output=True, text=True, timeout=600)

    def _put_file(self, key, path):
        r = self._call("put", f"{self.bucket}/{key}", "--file", path)
        if r.returncode:
            raise RuntimeError((r.stderr or r.stdout).strip()[-300:])

    def _get_file(self, key, path):
        r = self._call("get", f"{self.bucket}/{key}", "--file", path)
        if r.returncode == 0 and os.path.exists(path):
            return True
        if os.path.exists(path):                      # wrangler leaves an empty file behind when the key is missing
            os.remove(path)
        msg = (r.stderr + r.stdout).lower()
        if any(m in msg for m in self.MISSING):
            return False
        raise RuntimeError((r.stderr or r.stdout).strip()[-300:])


class S3Store(Store):
    """Through R2's S3 API with credentials from the environment (boto3)."""
    name = "s3"

    def __init__(self, bucket, account, key_id, secret, client=None):
        if client is None:
            import boto3
            client = boto3.client("s3", endpoint_url=f"https://{account}.r2.cloudflarestorage.com", aws_access_key_id=key_id,
                                  aws_secret_access_key=secret, region_name="auto")
        self.bucket, self.client = bucket, client

    def _put_file(self, key, path):
        self.client.upload_file(path, self.bucket, key)

    def _get_file(self, key, path):
        try:
            self.client.download_file(self.bucket, key, path)
            return True
        except Exception as e:                       # botocore's ClientError, without importing botocore here
            if "404" in str(e) or "NoSuchKey" in str(e) or "Not Found" in str(e):
                return False
            raise


def from_env(env=None):
    """The store the environment sets up, or None when R2 is off."""
    env = os.environ if env is None else env
    mode = env.get("WATERLEDGER_R2", "").strip()
    bucket = env.get("WATERLEDGER_R2_BUCKET") or BUCKET
    if mode == "off":
        return None
    if mode.startswith("dir:"):
        return FolderStore(mode[4:])
    if mode == "wrangler":
        return WranglerStore(bucket)
    if all(env.get(k) for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")):
        return S3Store(bucket, env["R2_ACCOUNT_ID"], env["R2_ACCESS_KEY_ID"], env["R2_SECRET_ACCESS_KEY"])
    if mode:
        raise ValueError(f"WATERLEDGER_R2={mode!r}: use wrangler, dir:PATH or off, or set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY")
    return None
