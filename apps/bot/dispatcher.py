"""Bot update dispatcher — stub. Replaced with real routing in E05-S03."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def dispatch_update(update: dict[str, Any]) -> None:
    """Accept a parsed Telegram Update and route it to the right handler.

    Stub — E05-S03 implements real routing. For now we just log the update
    id and message type so integration tests can see traffic and the
    webhook has something concrete to hand off to.
    """
    update_id = update.get("update_id")
    kinds = [k for k in ("message", "edited_message", "callback_query") if k in update]
    logger.info("bot.dispatch.stub", extra={"update_id": update_id, "kinds": kinds})
