"""Plain-text message handler stub. Real routing lands in E03 (RAG) and E08 (wizard)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_text_message(update: dict[str, Any]) -> None:
    """Log receipt of a plain-text message. Real RAG/wizard routing lands later."""
    logger.info("bot.handler.text.stub", extra={"update_id": update.get("update_id")})
