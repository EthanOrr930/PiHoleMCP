"""Exception hierarchy for the Pi-hole client."""

from __future__ import annotations


class PiHoleError(Exception):
    """Base for every Pi-hole client error."""

    def __init__(self, message: str = "", *, status: int | None = None, payload: object | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


class AuthError(PiHoleError):
    """401 / invalid SID / bad app password."""


class DestructiveActionsDisabled(PiHoleError):
    """Server rejected an action because webserver.api.allow_destructive=false."""


class NotFound(PiHoleError):
    """404 — resource (domain, group, list, client, lease, etc.) does not exist."""


class PiHoleRateLimited(PiHoleError):
    """429 from Pi-hole (other than seat exhaustion)."""


class PiHoleSeatExhausted(PiHoleError):
    """429 with body {error:{key:'no_free_seats'}} — too many concurrent sessions."""


class InvalidRegex(PiHoleError):
    """Rejected regex pattern (typically 400 on domain rule create/update)."""


class PiHoleServerError(PiHoleError):
    """5xx from Pi-hole."""


class PiHoleTimeout(PiHoleError):
    """Network / read timeout talking to Pi-hole."""
