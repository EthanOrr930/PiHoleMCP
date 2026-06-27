"""Tiny synchronous TTL cache for read-only descriptor calls."""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Dict with per-entry expiry. Not thread-safe; intended for asyncio single-thread use."""

    def __init__(self, default_ttl: float = 60.0) -> None:
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl_s = self._default_ttl if ttl is None else ttl
        self._store[key] = (time.monotonic() + ttl_s, value)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        for k in [k for k in self._store if k.startswith(prefix)]:
            self._store.pop(k, None)

    def clear(self) -> None:
        self._store.clear()
