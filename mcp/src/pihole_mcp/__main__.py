"""CLI entry point — `pihole-mcp` script delegates here."""

from __future__ import annotations

from .config import get_settings
from .server import run


def main() -> None:
    settings = get_settings()
    run(settings)


if __name__ == "__main__":
    main()
