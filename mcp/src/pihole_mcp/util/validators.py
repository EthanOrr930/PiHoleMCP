"""Pure input-validation helpers. No I/O, no state."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_LABEL_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")
_MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}$")
_MAC_BARE_RE = re.compile(r"^[0-9A-Fa-f]{12}$")

_BLOCKED_CONFIG_PREFIXES: tuple[str, ...] = (
    "webserver.api.",
    "database.",
    "files.",
    "debug.",
)
_BLOCKED_CONFIG_EXACT: frozenset[str] = frozenset({"dns.port"})


def is_fqdn(s: str) -> bool:
    """RFC-1035 hostname check. Rejects wildcards and overlong names."""
    if not isinstance(s, str) or not s or len(s) > 253:
        return False
    if "*" in s:
        return False
    name = s[:-1] if s.endswith(".") else s
    labels = name.split(".")
    if not labels:
        return False
    return all(_LABEL_RE.match(label) for label in labels)


def is_http_url(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    try:
        parsed = urlparse(s)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def normalize_mac(s: str) -> str:
    """Return lowercase colon-separated MAC. Accepts dash- or colon-separated, or bare 12-hex."""
    if not isinstance(s, str):
        raise ValueError("MAC must be a string")
    cleaned = s.strip()
    if _MAC_RE.match(cleaned):
        return cleaned.replace("-", ":").lower()
    if _MAC_BARE_RE.match(cleaned):
        lower = cleaned.lower()
        return ":".join(lower[i : i + 2] for i in range(0, 12, 2))
    raise ValueError(f"Invalid MAC address: {s!r}")


def cap_duration(seconds: int, max_s: int = 86400) -> int:
    if not isinstance(seconds, int) or isinstance(seconds, bool):
        raise ValueError("seconds must be an int")
    if seconds < 0:
        raise ValueError("seconds must be >= 0")
    return min(seconds, max_s)


def is_safe_config_path(path: str) -> bool:
    """True if `path` is NOT in the blocked-config allowlist (we forbid edits to it)."""
    if not isinstance(path, str) or not path:
        return False
    if path in _BLOCKED_CONFIG_EXACT:
        return False
    return not any(path.startswith(prefix) for prefix in _BLOCKED_CONFIG_PREFIXES)
