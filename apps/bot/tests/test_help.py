"""Tests for the /help handler (E05-S04)."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock

import pytest

from apps.accounts.constants import Language
from apps.bot.templates import render_template

UPDATE_ID = 555


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

    monkeypatch.setattr("apps.bot.handlers.help.get_bot", _get_bot)
    monkeypatch.setattr("apps.bot.handlers.commands.get_bot", _get_bot)
    return bot


@pytest.mark.asyncio
async def test_send_help_replies_with_uz_latin_body_for_latin_text(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.help import send_help

    await send_help(_make_update("/help"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("help", Language.UZ_LATIN)
    )


@pytest.mark.asyncio
async def test_send_help_replies_with_uz_cyrillic_body_for_uz_cyrillic_text(
    bot_stub: AsyncMock,
) -> None:
    from apps.bot.handlers.help import send_help

    await send_help(_make_update("/help ёрдам ўзим"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("help", Language.UZ_CYRILLIC)
    )


@pytest.mark.asyncio
async def test_send_help_replies_with_russian_body_for_russian_text(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.help import send_help

    await send_help(_make_update("/help помоги мне"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("help", Language.RUSSIAN)
    )


@pytest.mark.asyncio
async def test_send_help_handles_edited_message_variant(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.help import send_help

    await send_help(_make_update("/help", edited=True))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("help", Language.UZ_LATIN)
    )


@pytest.mark.asyncio
async def test_send_help_bails_when_chat_id_missing(
    bot_stub: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from apps.bot.handlers.help import send_help

    update = _make_update("/help", chat_id=None)
    with caplog.at_level(logging.WARNING, logger="apps.bot.handlers.help"):
        await send_help(update)

    bot_stub.send_message.assert_not_awaited()
    assert any(r.message == "bot.help.no_chat_id" for r in caplog.records)


@pytest.mark.asyncio
async def test_handle_command_dispatches_help_to_send_help(
    monkeypatch: pytest.MonkeyPatch,
    bot_stub: AsyncMock,  # noqa: ARG001
) -> None:
    from apps.bot.handlers import commands as commands_module

    send_help_stub = AsyncMock()
    monkeypatch.setattr(commands_module, "send_help", send_help_stub)

    await commands_module.handle_command(_make_update("/help"))

    send_help_stub.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_command_replies_unknown_for_gibberish(bot_stub: AsyncMock) -> None:
    from apps.bot.handlers.commands import handle_command

    await handle_command(_make_update("/gibberish"))

    bot_stub.send_message.assert_awaited_once_with(
        chat_id=42, text=render_template("unknown_command", Language.UZ_LATIN)
    )


def test_extract_command_name_strips_botname_suffix() -> None:
    from apps.bot.handlers.commands import _extract_command_name

    assert _extract_command_name("/help@TaaBot with args") == "help"
    assert _extract_command_name("/help") == "help"
    assert _extract_command_name("/START") == "start"
