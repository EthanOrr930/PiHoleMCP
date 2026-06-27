"""Pi-hole v6 REST API client + supporting types."""

from .client import PiHoleClient
from .errors import (
    AuthError,
    DestructiveActionsDisabled,
    InvalidRegex,
    NotFound,
    PiHoleError,
    PiHoleRateLimited,
    PiHoleSeatExhausted,
    PiHoleServerError,
    PiHoleTimeout,
)

__all__ = [
    "PiHoleClient",
    "PiHoleError",
    "AuthError",
    "DestructiveActionsDisabled",
    "NotFound",
    "PiHoleRateLimited",
    "PiHoleSeatExhausted",
    "InvalidRegex",
    "PiHoleServerError",
    "PiHoleTimeout",
]
