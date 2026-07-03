"""Command handler entrypoint — routes /commands to their handlers."""

from __future__ import annotations

import logging
from typing import Any

from apps.accounts.language import detect_language
from apps.bot.handlers.help import send_help
from apps.bot.handlers.start import send_start
from apps.bot.telegram import get_bot
from apps.bot.templates import render_template

logger = logging.getLogger(__name__)


def _extract_command_name(text: str) -> str:
    """Return the bare command name (`/help extra` → `help`)."""
    first = text.split(maxsplit=1)[0]
    return first.lstrip("/").split("@", 1)[0].lower()


async def _send_unknown_command(update: dict[str, Any]) -> None:
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text: str = message.get("text") or ""
    if chat_id is None:
        return
    body = render_template("unknown_command", detect_language(text))
    bot = get_bot()
    await bot.send_message(chat_id=chat_id, text=body)


async def handle_command(update: dict[str, Any]) -> None:
    """Dispatch to the specific command handler based on the command name."""
    message = update.get("message") or update.get("edited_message") or {}
    text: str = message.get("text") or ""
    command = _extract_command_name(text) if text.startswith("/") else ""
    logger.info(
        "bot.handler.command",
        extra={"update_id": update.get("update_id"), "command": command},
    )
    if command == "help":
        await send_help(update)
        return
    if command == "start":
        await send_start(update)
        return
    await _send_unknown_command(update)
