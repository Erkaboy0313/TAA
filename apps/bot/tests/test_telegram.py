"""Tests for apps.bot.telegram.get_bot()."""

from __future__ import annotations

import pytest

from django.test import override_settings

from apps.bot.exceptions import BotNotConfiguredError
from apps.bot.telegram import get_bot


@pytest.fixture(autouse=True)
def _clear_bot_cache():
    get_bot.cache_clear()
    yield
    get_bot.cache_clear()


@override_settings(TELEGRAM_BOT_TOKEN="")
def test_get_bot_raises_when_token_is_empty():
    with pytest.raises(BotNotConfiguredError):
        get_bot()


@override_settings(TELEGRAM_BOT_TOKEN="123:fake-token-for-tests")
def test_get_bot_returns_a_bot_instance_when_token_is_set():
    bot = get_bot()
    # We do not hit the network — just check the token was applied.
    assert bot.token == "123:fake-token-for-tests"


@override_settings(TELEGRAM_BOT_TOKEN="123:fake-token-for-tests")
def test_get_bot_caches_across_calls():
    assert get_bot() is get_bot()
