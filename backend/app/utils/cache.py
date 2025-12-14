import os
import json
import time
from pathlib import Path
from typing import Any, Dict

CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # seconds
MEM_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_path(key: str) -> Path:
    safe = key.replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
    return CACHE_DIR / f"{safe}.json"


def get_cache(key: str, ttl: int = DEFAULT_TTL) -> Any | None:
    # In-memory first
    mem = MEM_CACHE.get(key)
    if mem:
        if time.time() - mem.get("_ts", 0) <= ttl:
            return mem.get("payload")
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        ts = data.get("_ts", 0)
        if time.time() - ts > ttl:
            return None
        payload = data.get("payload")
        MEM_CACHE[key] = {"_ts": ts, "payload": payload}
        return payload
    except Exception:
        return None


def set_cache(key: str, payload: Any) -> None:
    now = time.time()
    MEM_CACHE[key] = {"_ts": now, "payload": payload}
    p = _cache_path(key)
    p.write_text(json.dumps({"_ts": now, "payload": payload}, ensure_ascii=False))
