"""Tests for the /start handler stub (E05-S05)."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock

import pytest

from apps.accounts.constants import Language
from apps.bot.templates import render_template

UPDATE_ID = 777


def _make_update(text: str, *, chat_id: int | None = 42, edited: bool = False) -> dict:
    """Build a minimal update dict shaped like Telegram's payload."""
    message: dict = {"message_id": 1, "date": 1700000000, "text": text}
    if chat_id is not None:
        message["chat"] = {"id": chat_id, "type": "private"}
    key = "edited_message" if edited else "message"
    return {"update_id": UPDATE_ID, key: message}


@pytest.fixture
def bot_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch get_bot in BOTH handler modules that consume it."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)

    def _get_bot() -> AsyncMock:
        return bot

    monkeypatch.setattr("apps.bot.handlers.start.get_bot", _get_bot)
    monkeypatch.setattr("apps.bot.handlers.commands.get_bot", _get_bot)
    return bot


@pytest.mark.asyncio
async def test_send_start_replies_with_uz_latin_body_for_latin_text(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.start import send_start

    await send_start(_make_update("/start"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("start", Language.UZ_LATIN)
    )


@pytest.mark.asyncio
async def test_send_start_replies_with_uz_cyrillic_body_for_uz_cyrillic_text(
    bot_stub: AsyncMock,
) -> None:
    from apps.bot.handlers.start import send_start

    await send_start(_make_update("/start ёрдам ўзим"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("start", Language.UZ_CYRILLIC)
    )


@pytest.mark.asyncio
async def test_send_start_replies_with_russian_body_for_russian_text(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.start import send_start

    await send_start(_make_update("/start помоги"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("start", Language.RUSSIAN)
    )


@pytest.mark.asyncio
async def test_send_start_handles_edited_message_variant(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.start import send_start

    await send_start(_make_update("/start", edited=True))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("start", Language.UZ_LATIN)
    )


@pytest.mark.asyncio
async def test_send_start_bails_when_chat_id_missing(
    bot_stub: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from apps.bot.handlers.start import send_start

    update = _make_update("/start", chat_id=None)
    with caplog.at_level(logging.WARNING, logger="apps.bot.handlers.start"):
        await send_start(update)

    bot_stub.send_message.assert_not_awaited()
    assert any(r.message == "bot.start.no_chat_id" for r in caplog.records)


@pytest.mark.asyncio
async def test_handle_command_dispatches_start_to_send_start(
    monkeypatch: pytest.MonkeyPatch,
    bot_stub: AsyncMock,
) -> None:
    from apps.bot.handlers import commands as commands_module

    send_start_stub = AsyncMock()
    monkeypatch.setattr(commands_module, "send_start", send_start_stub)

    await commands_module.handle_command(_make_update("/start"))

    send_start_stub.assert_awaited_once()
    bot_stub.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_command_logs_start_command_name(
    bot_stub: AsyncMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
) -> None:
    from apps.bot.handlers.commands import handle_command

    with caplog.at_level(logging.INFO, logger="apps.bot.handlers.commands"):
        await handle_command(_make_update("/start"))

    assert any(
        r.message == "bot.handler.command" and getattr(r, "command", None) == "start"
        for r in caplog.records
    )
