"""Bot update dispatcher — routes a parsed Telegram Update to a handler."""

from __future__ import annotations

import logging
from typing import Any

from apps.accounts.language import detect_language
from apps.bot.handlers.callback import handle_callback_query
from apps.bot.handlers.commands import handle_command
from apps.bot.handlers.text import handle_text_message
from apps.bot.handlers.voice import handle_voice_message
from apps.bot.rate_limit import Kind, check_and_bump
from apps.bot.telegram import get_bot
from apps.bot.templates import render_template

logger = logging.getLogger(__name__)


def _telegram_id(update: dict[str, Any]) -> int | None:
    message = update.get("message") or update.get("edited_message") or {}
    sender = message.get("from") or {}
    telegram_id = sender.get("id")
    if telegram_id is None:
        callback = update.get("callback_query") or {}
        sender = callback.get("from") or {}
        telegram_id = sender.get("id")
    return telegram_id if isinstance(telegram_id, int) else None


def _chat_id(update: dict[str, Any]) -> int | None:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        callback = update.get("callback_query") or {}
        callback_message = callback.get("message") or {}
        chat = callback_message.get("chat") or {}
        chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


async def _reject_with_message(update: dict[str, Any]) -> None:
    chat_id = _chat_id(update)
    if chat_id is None:
        return
    message = update.get("message") or update.get("edited_message") or {}
    text: str = message.get("text") or ""
    body = render_template("rate_limit", detect_language(text))
    bot = get_bot()
    await bot.send_message(chat_id=chat_id, text=body)


def _classify(update: dict[str, Any]) -> Kind | None:
    """Return the rate-limit kind for this update or None when nothing to route."""
    message = update.get("message") or update.get("edited_message") or {}
    if message.get("voice"):
        return "voice"
    text = message.get("text")
    if isinstance(text, str) and text:
        return "general"
    if "callback_query" in update:
        return "general"
    return None


async def dispatch_update(update: dict[str, Any]) -> None:
    """Route the update to the appropriate handler.

    Order matters: voice beats text beats callback_query. Anything else is
    logged as unhandled so operators notice new update kinds we do not
    yet cover.

    Rate limits: voice (Gemini-bound) has a tighter budget than general
    updates. When over budget, we send a friendly bilingual message and
    skip the handler entirely.
    """
    kind = _classify(update)
    if kind is None:
        logger.info(
            "bot.dispatch.unhandled_update_kind",
            extra={"update_id": update.get("update_id")},
        )
        return

    telegram_id = _telegram_id(update)
    if telegram_id is not None:
        allowed = await check_and_bump(kind=kind, telegram_id=telegram_id)
        if not allowed:
            await _reject_with_message(update)
            return

    if kind == "voice":
        await handle_voice_message(update)
        return

    message = update.get("message") or update.get("edited_message") or {}
    text = message.get("text")

    if isinstance(text, str) and text.startswith("/"):
        await handle_command(update)
        return

    if isinstance(text, str) and text:
        await handle_text_message(update)
        return

    if "callback_query" in update:
        await handle_callback_query(update)
