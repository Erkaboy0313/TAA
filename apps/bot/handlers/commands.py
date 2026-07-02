"""Command handler stub. Real /start, /help, ... land in E05-S04/S05 and later."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _extract_command_name(text: str) -> str:
    """Return the command word without the leading slash.

    ``/help`` -> ``"help"``, ``/start with args`` -> ``"start"``.
    Command names are considered non-PII (R10) — free-form arguments are not
    logged.
    """
    # Strip the leading '/' first, then split off the first whitespace-delimited
    # token; the '@botname' suffix Telegram appends in groups is preserved so
    # operators can see which bot handle the user targeted.
    return text[1:].split(maxsplit=1)[0]


async def handle_command(update: dict[str, Any]) -> None:
    """Log receipt of a command message; later stories replace this stub."""
    message = update.get("message") or update.get("edited_message") or {}
    text = message.get("text") or ""
    command = _extract_command_name(text) if text.startswith("/") else ""
    logger.info(
        "bot.handler.command.stub",
        extra={"update_id": update.get("update_id"), "command": command},
    )
