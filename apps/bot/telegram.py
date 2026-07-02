"""Lazy-initialised Telegram Bot singleton.

Webhook mode does not need a running `Application` polling loop — a
plain `telegram.Bot` handles both receiving updates (via the webhook
view in E05-S02) and sending replies. The instance is cached per
process so we do not pay the SSL/session setup cost on every request.
"""

from __future__ import annotations

from functools import lru_cache

from telegram import Bot

from django.conf import settings

from apps.bot.exceptions import BotNotConfiguredError


@lru_cache(maxsize=1)
def get_bot() -> Bot:
    """Return the process-wide Telegram Bot instance.

    Raises `BotNotConfiguredError` if `TELEGRAM_BOT_TOKEN` is unset.
    Use `get_bot.cache_clear()` in tests when you need a fresh instance.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise BotNotConfiguredError(
            "TELEGRAM_BOT_TOKEN is empty; set it in .env before using the bot."
        )
    return Bot(token=token)
