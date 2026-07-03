"""Per-user rate limiting for the bot.

Fixed-window counter in the Django cache (Redis on DB /1). Two buckets:
`voice` is expensive (Gemini STT + RAG), `general` covers everything else.
Windows are 60s so we can charge one atomic `aincr` per event.

Keys look like `bot:ratelimit:{kind}:{telegram_id}:{minute_bucket}` so a
cache flush cannot bleed history across users or kinds.
"""

from __future__ import annotations

import logging
import time
from typing import Literal

from django.core.cache import cache

logger = logging.getLogger(__name__)

Kind = Literal["voice", "general"]

# Limits per minute per user. Voice is Gemini-bound and expensive; general
# covers text messages, /commands, and callback queries.
LIMITS: dict[Kind, int] = {
    "voice": 10,
    "general": 30,
}

_WINDOW_SECONDS = 60


def _bucket_key(*, kind: Kind, telegram_id: int, now: float) -> str:
    minute = int(now // _WINDOW_SECONDS)
    return f"bot:ratelimit:{kind}:{telegram_id}:{minute}"


async def check_and_bump(*, kind: Kind, telegram_id: int) -> bool:
    """Return True if the caller is within their per-minute budget.

    Increments the counter atomically. Callers must invoke exactly once
    per user event — the increment is the accounting.
    """
    key = _bucket_key(kind=kind, telegram_id=telegram_id, now=time.time())
    limit = LIMITS[kind]

    # `aadd` sets the key to 1 with TTL only if it did not already exist.
    # Ignoring the return value is intentional: the subsequent `aincr` handles
    # both the fresh-window and continuing-window cases.
    await cache.aadd(key, 0, _WINDOW_SECONDS)
    count = await cache.aincr(key)

    if count > limit:
        logger.info(
            "bot.rate_limit.reject",
            extra={"kind": kind, "count": count, "limit": limit},
        )
        return False
    return True
