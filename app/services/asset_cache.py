import threading
from typing import Any


_cache: dict[str, dict] = {}
_lock = threading.RLock()
_counters: dict[str, int] = {}


def store(organization_id: int, assets: list[dict], relationships: list[dict]):
    key = str(organization_id)
    with _lock:
        # Assign unique IDs to new assets
        for asset in assets:
            _counters[key] = _counters.get(key, 0) + 1
            asset["id"] = _counters[key]

        # Merge with existing entries instead of overwriting
        existing = _cache.get(key)
        if existing:
            existing["assets"].extend(assets)
            existing["relationships"].extend(relationships)
        else:
            _cache[key] = {"assets": list(assets), "relationships": list(relationships)}


def get_assets(organization_id: int) -> list[dict]:
    with _lock:
        entry = _cache.get(str(organization_id))
        return list(entry["assets"]) if entry else []


def get_relationships(organization_id: int) -> list[dict]:
    with _lock:
        entry = _cache.get(str(organization_id))
        return list(entry["relationships"]) if entry else []


def clear(organization_id: int):
    key = str(organization_id)
    with _lock:
        _cache.pop(key, None)
        _counters.pop(key, None)
