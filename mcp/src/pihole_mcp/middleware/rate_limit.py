"""Per-tool token-bucket rate limiter (in-memory)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from ..pihole.errors import PiHoleError


class RateLimited(PiHoleError):
    """Raised when a per-tool quota is exhausted."""


@dataclass
class _Bucket:
    capacity: float
    refill_per_sec: float
    tokens: float
    updated_at: float

    def consume(self, now: float, cost: float = 1.0) -> bool:
        elapsed = max(0.0, now - self.updated_at)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.updated_at = now
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True


_DEFAULT_RATE_PER_MIN = 60
_SENSITIVE_LIMITS: dict[str, tuple[float, float]] = {
    "flush_dns_logs": (1.0, 1.0 / 3600.0),
    "restart_dns": (1.0, 1.0 / 30.0),
    "run_gravity_update": (1.0, 1.0 / 30.0),
    "flush_arp_cache": (1.0, 1.0 / 300.0),
    "import_backup": (1.0, 1.0 / 600.0),
}


class RateLimiter:
    """Per-tool token bucket. Raises RateLimited if quota exhausted."""

    def __init__(self, default_per_min: int = _DEFAULT_RATE_PER_MIN) -> None:
        self._default_per_min = default_per_min
        self._buckets: dict[str, _Bucket] = {}

    def check(self, tool_name: str, now: float | None = None) -> None:
        ts = now if now is not None else time.monotonic()
        bucket = self._buckets.get(tool_name) or self._make_bucket(tool_name, ts)
        self._buckets[tool_name] = bucket
        if not bucket.consume(ts):
            raise RateLimited(f"Rate limit exhausted for tool {tool_name!r}; try again shortly.")

    def _make_bucket(self, tool_name: str, ts: float) -> _Bucket:
        if tool_name in _SENSITIVE_LIMITS:
            cap, refill = _SENSITIVE_LIMITS[tool_name]
        else:
            cap = float(self._default_per_min)
            refill = cap / 60.0
        return _Bucket(capacity=cap, refill_per_sec=refill, tokens=cap, updated_at=ts)
