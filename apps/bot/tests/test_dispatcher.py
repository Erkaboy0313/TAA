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
) -> None:
    # Uses the REAL command handler (no stub monkeypatch) to prove the
    # command-name extraction in the log payload.
    from apps.bot.handlers.commands import handle_command

    update = {
        "update_id": COMMAND_LOG_UPDATE_ID,
        "message": {"text": "/help with something extra"},
    }
    with caplog.at_level(logging.INFO, logger="apps.bot.handlers.commands"):
        await handle_command(update)

    matches = [r for r in caplog.records if r.message == "bot.handler.command.stub"]
    assert len(matches) == 1
    assert matches[0].command == "help"
    assert matches[0].update_id == COMMAND_LOG_UPDATE_ID
