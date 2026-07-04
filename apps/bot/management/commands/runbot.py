"""Local dev polling loop — no webhook / ngrok needed.

Production stays on webhook mode (architecture §5); this command is a
`make bot-polling`-friendly wrapper for smoke testing on Eric's laptop.
Delegates every incoming update to `apps.bot.dispatcher.dispatch_update`
so behaviour matches the webhook path exactly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters

if TYPE_CHECKING:
    from telegram import Update

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.bot.dispatcher import dispatch_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """`python manage.py runbot` — polls Telegram for updates."""

    help = "Run the bot in long-polling mode (dev only; production uses the webhook)."

    async def _handle(self, update: Update, _context: Any) -> None:
        await dispatch_update(update.to_dict())

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError(
                "TELEGRAM_BOT_TOKEN is empty. Fill it in .env before running the bot.",
            )

        self.stdout.write(self.style.SUCCESS("bot polling — Ctrl-C to stop"))
        app: Application = Application.builder().token(token).build()
        app.add_handler(MessageHandler(filters.ALL, self._handle))
        app.add_handler(CallbackQueryHandler(self._handle))
        # `run_polling` is blocking — that is what we want for a dev runner.
        app.run_polling(drop_pending_updates=True)
