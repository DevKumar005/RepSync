import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT_DIR / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TTL_SECONDS = 24 * 3600  # 24 hours


def get_cache_file(endpoint: str, input_key: str) -> Path:
    digest = hashlib.sha256(f"{endpoint}:{input_key}".encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{endpoint}_{digest}.json"


def read_cache(endpoint: str, input_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[dict[str, Any]]:
    path = get_cache_file(endpoint, input_key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cached_at = payload.get("cached_at", 0)
        if time.time() - cached_at > ttl_seconds:
            return None
        return payload
    except Exception:
        return None


def write_cache(endpoint: str, input_key: str, data: Any, meta: Optional[dict] = None) -> dict[str, Any]:
    path = get_cache_file(endpoint, input_key)
    payload = {
        "endpoint": endpoint,
        "input": input_key,
        "cached_at": time.time(),
        "meta": meta or {},
        "data": data,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
