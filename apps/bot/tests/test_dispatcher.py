"""Tests for ``apps.bot.dispatcher.dispatch_update`` (E05-S03).

The router itself owns no business logic — it just picks one of four
handler stubs based on the update shape. So the tests here verify:

- routing table (voice beats /-command beats plain text beats callback)
- edge cases (empty text, None text, empty update)
- log payloads (update_id + command name, never raw user text — R10)
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

UNHANDLED_UPDATE_ID = 42
COMMAND_LOG_UPDATE_ID = 99


@pytest.fixture(autouse=True)
def _allow_all_rate_limits(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Bypass the rate limiter in every dispatcher test.

    E05-S07 wired ``check_and_bump`` into the router; these tests concern
    the routing table itself, not throttling. Rate-limit behavior is
    covered separately in ``test_rate_limit.py`` and the reject-path
    tests below.
    """
    stub = AsyncMock(return_value=True)
    monkeypatch.setattr("apps.bot.dispatcher.check_and_bump", stub)
    return stub


@pytest.fixture
def stubs(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    """Patch the four handler symbols the router imports.

    The router does ``from apps.bot.handlers.voice import handle_voice_message``
    at module import time — so the *binding* we must patch is
    ``apps.bot.dispatcher.handle_voice_message``, not the original module
    attribute. Patching the origin would leave the router's local reference
    pointing at the real function.
    """
    voice = AsyncMock()
    command = AsyncMock()
    text = AsyncMock()
    callback = AsyncMock()
    monkeypatch.setattr("apps.bot.dispatcher.handle_voice_message", voice)
    monkeypatch.setattr("apps.bot.dispatcher.handle_command", command)
    monkeypatch.setattr("apps.bot.dispatcher.handle_text_message", text)
    monkeypatch.setattr("apps.bot.dispatcher.handle_callback_query", callback)
    return {"voice": voice, "command": command, "text": text, "callback": callback}


def _assert_only(stubs: dict[str, AsyncMock], expected: str, update: dict[str, Any]) -> None:
    """Assert exactly one stub was awaited once with ``update`` and the others were not."""
    stubs[expected].assert_awaited_once_with(update)
    for name, stub in stubs.items():
        if name != expected:
            stub.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_routes_to_voice_when_message_has_voice(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {
        "update_id": 1,
        "message": {"message_id": 10, "voice": {"file_id": "AwA", "duration": 3}},
    }
    await dispatch_update(update)
    _assert_only(stubs, "voice", update)


@pytest.mark.asyncio
@pytest.mark.parametrize("cmd_text", ["/start", "/help", "/start with args", "/help@taa_bot"])
async def test_dispatch_routes_to_command_when_text_starts_with_slash(
    stubs: dict[str, AsyncMock], cmd_text: str
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": 2, "message": {"text": cmd_text}}
    await dispatch_update(update)
    _assert_only(stubs, "command", update)


@pytest.mark.asyncio
async def test_dispatch_routes_to_text_when_message_is_plain_text(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": 3, "message": {"text": "Salom, qanday soliq beraman?"}}
    await dispatch_update(update)
    _assert_only(stubs, "text", update)


@pytest.mark.asyncio
async def test_dispatch_routes_to_callback_when_update_has_callback_query(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {
        "update_id": 4,
        "callback_query": {"id": "cbq-1", "data": "regime:yatt_4"},
    }
    await dispatch_update(update)
    _assert_only(stubs, "callback", update)


@pytest.mark.asyncio
async def test_dispatch_routes_edited_message_text_to_text_handler(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {
        "update_id": 5,
        "edited_message": {"text": "tuzatilgan savol"},
    }
    await dispatch_update(update)
    _assert_only(stubs, "text", update)


@pytest.mark.asyncio
async def test_dispatch_routes_edited_message_command_to_command_handler(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": 6, "edited_message": {"text": "/help"}}
    await dispatch_update(update)
    _assert_only(stubs, "command", update)


@pytest.mark.asyncio
async def test_dispatch_routes_edited_message_voice_to_voice_handler(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {
        "update_id": 7,
        "edited_message": {"voice": {"file_id": "AwB", "duration": 2}},
    }
    await dispatch_update(update)
    _assert_only(stubs, "voice", update)


@pytest.mark.asyncio
async def test_dispatch_voice_wins_over_text_caption(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    # Telegram sends both ``voice`` and a ``text`` caption on the same message.
    # We route to voice — the transcript is the authoritative signal.
    update = {
        "update_id": 8,
        "message": {
            "voice": {"file_id": "AwC", "duration": 1},
            "text": "/start",
        },
    }
    await dispatch_update(update)
    _assert_only(stubs, "voice", update)


@pytest.mark.asyncio
async def test_dispatch_logs_unhandled_when_update_is_empty(
    stubs: dict[str, AsyncMock],
    caplog: pytest.LogCaptureFixture,
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": UNHANDLED_UPDATE_ID}
    with caplog.at_level(logging.INFO, logger="apps.bot.dispatcher"):
        await dispatch_update(update)

    for stub in stubs.values():
        stub.assert_not_awaited()
    assert any(
        r.message == "bot.dispatch.unhandled_update_kind"
        and getattr(r, "update_id", None) == UNHANDLED_UPDATE_ID
        for r in caplog.records
    )


@pytest.mark.asyncio
async def test_dispatch_logs_unhandled_when_message_text_is_empty_string(
    stubs: dict[str, AsyncMock],
    caplog: pytest.LogCaptureFixture,
) -> None:
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": 43, "message": {"text": ""}}
    with caplog.at_level(logging.INFO, logger="apps.bot.dispatcher"):
        await dispatch_update(update)

    for stub in stubs.values():
        stub.assert_not_awaited()
    assert any(r.message == "bot.dispatch.unhandled_update_kind" for r in caplog.records)


@pytest.mark.asyncio
async def test_dispatch_logs_unhandled_when_message_text_is_none(
    stubs: dict[str, AsyncMock],
) -> None:
    from apps.bot.dispatcher import dispatch_update

    # ``text: None`` must NOT crash (guards the isinstance check in the router).
    update = {"update_id": 44, "message": {"text": None}}
    await dispatch_update(update)
    for stub in stubs.values():
        stub.assert_not_awaited()


@pytest.mark.asyncio
async def test_command_handler_logs_command_name_in_extras(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Uses the REAL command handler (no stub monkeypatch) to prove the
    # command-name extraction in the log payload. `send_help` is stubbed
    # because dispatching to a real handler is out of scope for this test.
    from apps.bot.handlers.commands import handle_command

    monkeypatch.setattr("apps.bot.handlers.commands.send_help", AsyncMock())

    update = {
        "update_id": COMMAND_LOG_UPDATE_ID,
        "message": {"text": "/help with something extra"},
    }
    with caplog.at_level(logging.INFO, logger="apps.bot.handlers.commands"):
        await handle_command(update)

    matches = [r for r in caplog.records if r.message == "bot.handler.command"]
    assert len(matches) == 1
    assert matches[0].command == "help"
    assert matches[0].update_id == COMMAND_LOG_UPDATE_ID


@pytest.mark.asyncio
async def test_dispatch_rejects_when_rate_limit_says_no(
    stubs: dict[str, AsyncMock],
    monkeypatch: pytest.MonkeyPatch,
    _allow_all_rate_limits: AsyncMock,
) -> None:
    """When ``check_and_bump`` returns False, no handler is called and the
    user gets a friendly reject message via ``get_bot().send_message``."""
    from apps.bot.dispatcher import dispatch_update

    _allow_all_rate_limits.return_value = False
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    monkeypatch.setattr("apps.bot.dispatcher.get_bot", lambda: bot)

    telegram_id = 12345
    update = {
        "update_id": 900,
        "message": {
            "text": "Salom",
            "from": {"id": telegram_id, "is_bot": False},
            "chat": {"id": telegram_id, "type": "private"},
        },
    }
    await dispatch_update(update)

    for stub in stubs.values():
        stub.assert_not_awaited()
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == telegram_id


@pytest.mark.asyncio
async def test_dispatch_skips_rate_limit_when_from_id_missing(
    stubs: dict[str, AsyncMock],
    _allow_all_rate_limits: AsyncMock,
) -> None:
    """Updates without a ``from.id`` (rare, but possible for anonymous
    channel posts) bypass the rate limiter entirely — otherwise all such
    updates would share a single bucket keyed on None."""
    from apps.bot.dispatcher import dispatch_update

    update = {"update_id": 901, "message": {"text": "hi"}}
    await dispatch_update(update)
    stubs["text"].assert_awaited_once()
    _allow_all_rate_limits.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_logs_exception_and_apologises_when_handler_fails(
    stubs: dict[str, AsyncMock],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A crashing handler must NOT bubble up — the dispatcher logs the
    exception with a full traceback and sends a friendly apology so the
    webhook still returns 200 to Telegram."""
    from apps.bot.dispatcher import dispatch_update

    chat_id = 7
    stubs["text"].side_effect = RuntimeError("boom")
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    monkeypatch.setattr("apps.bot.dispatcher.get_bot", lambda: bot)

    update = {
        "update_id": 902,
        "message": {"text": "hi", "chat": {"id": chat_id, "type": "private"}},
    }
    with caplog.at_level(logging.ERROR, logger="apps.bot.dispatcher"):
        await dispatch_update(update)

    stubs["text"].assert_awaited_once()
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == chat_id
    assert any(r.message == "bot.dispatch.handler_failed" for r in caplog.records)


@pytest.mark.asyncio
async def test_dispatch_swallows_secondary_failure_in_apology(
    stubs: dict[str, AsyncMock],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If even the apology send fails, log and move on — do not re-raise."""
    from apps.bot.dispatcher import dispatch_update

    stubs["text"].side_effect = RuntimeError("boom")
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=RuntimeError("telegram down"))
    monkeypatch.setattr("apps.bot.dispatcher.get_bot", lambda: bot)

    update = {
        "update_id": 903,
        "message": {"text": "hi", "chat": {"id": 7, "type": "private"}},
    }
    with caplog.at_level(logging.ERROR, logger="apps.bot.dispatcher"):
        await dispatch_update(update)

    # Both the original handler failure and the apology failure got logged.
    handler_failed = [r for r in caplog.records if r.message == "bot.dispatch.handler_failed"]
    apology_failed = [r for r in caplog.records if r.message == "bot.dispatch.apology_send_failed"]
    assert len(handler_failed) == 1
    assert len(apology_failed) == 1
