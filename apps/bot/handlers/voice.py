"""Voice-message handler stub. Real STT + RAG flow lands in later stories."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_voice_message(update: dict[str, Any]) -> None:
    """Log receipt of a voice message. E04-S06 replaces this stub."""
    logger.info("bot.handler.voice.stub", extra={"update_id": update.get("update_id")})
