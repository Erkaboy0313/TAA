"""Callback-query handler stub. Real inline-button handling lands in later stories."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_callback_query(update: dict[str, Any]) -> None:
    """Log receipt of a callback query. Later stories replace this stub."""
    logger.info("bot.handler.callback.stub", extra={"update_id": update.get("update_id")})
