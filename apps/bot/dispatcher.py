"""Bot update dispatcher — routes a parsed Telegram Update to a handler."""

from __future__ import annotations

import logging
from typing import Any

from apps.bot.handlers.callback import handle_callback_query
from apps.bot.handlers.commands import handle_command
from apps.bot.handlers.text import handle_text_message
from apps.bot.handlers.voice import handle_voice_message

logger = logging.getLogger(__name__)


async def dispatch_update(update: dict[str, Any]) -> None:
    """Route the update to the appropriate handler.

    Order matters: voice beats text-with-`/` beats plain text beats
    callback_query. Anything else is logged as unhandled so operators
    notice new update kinds we do not yet cover.
    """
    message = update.get("message") or update.get("edited_message") or {}
    text: str | None = message.get("text")

    if message.get("voice"):
        await handle_voice_message(update)
        return

    if isinstance(text, str) and text.startswith("/"):
        await handle_command(update)
        return

    if isinstance(text, str) and text:
        await handle_text_message(update)
        return

    if "callback_query" in update:
        await handle_callback_query(update)
        return

    logger.info(
        "bot.dispatch.unhandled_update_kind",
        extra={"update_id": update.get("update_id")},
    )
