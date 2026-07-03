"""`/help` command handler."""

from __future__ import annotations

import logging
from typing import Any

from apps.accounts.language import detect_language
from apps.bot.telegram import get_bot
from apps.bot.templates import render_template

logger = logging.getLogger(__name__)


async def send_help(update: dict[str, Any]) -> None:
    """Reply to /help with the static help text in the caller's language."""
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text: str = message.get("text") or ""

    if chat_id is None:
        logger.warning("bot.help.no_chat_id", extra={"update_id": update.get("update_id")})
        return

    body = render_template("help", detect_language(text))

    bot = get_bot()
    await bot.send_message(chat_id=chat_id, text=body)
