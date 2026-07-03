"""Tests for apps.bot.rate_limit."""

from __future__ import annotations

import pytest

from django.core.cache import cache

from apps.bot.rate_limit import LIMITS, _bucket_key, check_and_bump


@pytest.fixture(autouse=True)
async def _clear_cache():
    await cache.aclear()
    yield
    await cache.aclear()


@pytest.mark.asyncio
async def test_first_request_is_allowed() -> None:
    assert await check_and_bump(kind="general", telegram_id=100) is True


@pytest.mark.asyncio
async def test_within_budget_is_allowed() -> None:
    limit = LIMITS["general"]
    for _ in range(limit):
        assert await check_and_bump(kind="general", telegram_id=200) is True


@pytest.mark.asyncio
async def test_over_budget_is_rejected() -> None:
    limit = LIMITS["general"]
    for _ in range(limit):
        await check_and_bump(kind="general", telegram_id=300)
    assert await check_and_bump(kind="general", telegram_id=300) is False


@pytest.mark.asyncio
async def test_voice_has_stricter_budget_than_general() -> None:
    assert LIMITS["voice"] < LIMITS["general"]
    for _ in range(LIMITS["voice"]):
        await check_and_bump(kind="voice", telegram_id=400)
    assert await check_and_bump(kind="voice", telegram_id=400) is False


@pytest.mark.asyncio
async def test_voice_and_general_buckets_do_not_share() -> None:
    for _ in range(LIMITS["voice"]):
        await check_and_bump(kind="voice", telegram_id=500)
    # Voice bucket is now full but general should be fresh.
    assert await check_and_bump(kind="general", telegram_id=500) is True


@pytest.mark.asyncio
async def test_users_do_not_share_buckets() -> None:
    for _ in range(LIMITS["general"]):
        await check_and_bump(kind="general", telegram_id=600)
    # User 600 is at the cap; a different user should still be fresh.
    assert await check_and_bump(kind="general", telegram_id=700) is True


def test_bucket_key_partitions_by_kind_user_and_minute() -> None:
    keys = {
        _bucket_key(kind="general", telegram_id=1, now=0.0),
        _bucket_key(kind="voice", telegram_id=1, now=0.0),
        _bucket_key(kind="general", telegram_id=2, now=0.0),
        _bucket_key(kind="general", telegram_id=1, now=60.0),
    }
    # All four combinations produce distinct keys — no bucket sharing.
    assert len(keys) == len(
        [
            ("general", 1, 0.0),
            ("voice", 1, 0.0),
            ("general", 2, 0.0),
            ("general", 1, 60.0),
        ]
    )
