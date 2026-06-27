"""Teleporter (backup/restore) MCP tools.

Exposes export_backup and import_backup. Import is the single most
destructive operation in this server, so it requires double confirmation:
both a boolean flag and a fixed confirmation phrase.
"""

from __future__ import annotations

import base64
import hashlib

from fastmcp import FastMCP

from pihole_mcp.server import get_client

REQUIRED_RESTORE_PHRASE = "RESTORE PIHOLE"


def register(mcp: FastMCP) -> None:
    """Register teleporter tools on the given FastMCP instance."""

    @mcp.tool
    async def export_backup() -> dict:
        """Export a full Pi-hole backup (Teleporter ZIP) as base64.

        Returns the ZIP bytes encoded as base64, the raw byte size, and a
        SHA-256 hex digest so the caller can verify integrity. The archive
        contains the full Pi-hole configuration and gravity database and can
        be re-imported via import_backup.
        """
        client = get_client()
        file_bytes = await client.teleporter_export()
        return _encode_backup(file_bytes)

    @mcp.tool
    async def import_backup(
        data_b64: str,
        confirm: bool = False,
        confirmation_phrase: str = "",
    ) -> dict:
        """Import (restore) a Pi-hole Teleporter backup. DESTRUCTIVE.

        This replaces the live Pi-hole configuration and gravity database
        with the contents of the provided backup. There is no undo.

        Requires DOUBLE confirmation:
          - confirm=True
          - confirmation_phrase="RESTORE PIHOLE" (exact, case-sensitive)

        Args:
            data_b64: Base64-encoded Teleporter ZIP bytes (as returned by
                export_backup).
            confirm: Must be True to proceed.
            confirmation_phrase: Must be exactly "RESTORE PIHOLE".
        """
        _require_double_confirmation(confirm, confirmation_phrase)
        file_bytes = _decode_backup(data_b64)
        client = get_client()
        result = await client.teleporter_import(file_bytes)
        return {
            "imported_bytes": len(file_bytes),
            "sha256": hashlib.sha256(file_bytes).hexdigest(),
            "result": result,
        }


def _encode_backup(file_bytes: bytes) -> dict:
    """Encode raw backup bytes for transport over MCP."""
    return {
        "data_b64": base64.b64encode(file_bytes).decode("ascii"),
        "size_bytes": len(file_bytes),
        "sha256": hashlib.sha256(file_bytes).hexdigest(),
    }


def _decode_backup(data_b64: str) -> bytes:
    """Decode a base64 backup payload, raising a friendly error if invalid."""
    if not data_b64:
        raise ValueError("data_b64 is empty; provide a base64-encoded Teleporter ZIP.")
    try:
        return base64.b64decode(data_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError(
            f"data_b64 is not valid base64: {exc}. "
            "Pass the exact string returned by export_backup."
        ) from exc


def _require_double_confirmation(confirm: bool, phrase: str) -> None:
    """Guard import_backup: both flag and exact phrase must be supplied."""
    if not confirm:
        raise ValueError(
            "Set confirm=True to proceed. import_backup will overwrite the "
            "live Pi-hole configuration and gravity database."
        )
    if phrase != REQUIRED_RESTORE_PHRASE:
        raise ValueError(
            "Refusing to restore: confirmation_phrase must be exactly "
            f'"{REQUIRED_RESTORE_PHRASE}" (case-sensitive). '
            "This is intentional friction — restoring a backup cannot be undone."
        )
