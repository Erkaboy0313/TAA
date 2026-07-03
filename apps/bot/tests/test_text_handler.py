"""Tests for ``apps.bot.handlers.text.handle_text_message`` (E03-S10).

Every test mocks the RAG service and the Telegram bot so no network or
Postgres call leaves the process (project-context R11).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from apps.accounts.constants import Language
from apps.bot.handlers.text import handle_text_message
from apps.bot.templates import TEMPLATES
from apps.rag.exceptions import RagError
from apps.rag.services import RagAnswer

_CHAT_ID = 424242
_UPDATE_ID = 5001


def _text_update(
    text: str,
    *,
    chat_id: int | None = _CHAT_ID,
) -> dict[str, Any]:
    """Build a minimal Telegram-shaped update carrying a plain-text message."""
    message: dict[str, Any] = {"message_id": 11, "text": text}
    if chat_id is not None:
        message["chat"] = {"id": chat_id, "type": "private"}
    return {"update_id": _UPDATE_ID, "message": message}


@pytest.fixture
def bot_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch ``get_bot`` to return an AsyncMock with a working ``send_message``."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    monkeypatch.setattr("apps.bot.handlers.text.get_bot", lambda: bot)
    return bot


@pytest.mark.asyncio
async def test_handle_text_message_calls_rag_and_sends_answer(
    bot_stub: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = RagAnswer(text="Aylanma soliq 4% [#1].\n\nDisclaimer.", citations=["https://lex.uz/a"])
    rag_stub = AsyncMock(return_value=answer)
    monkeypatch.setattr("apps.bot.handlers.text.answer_question", rag_stub)

    await handle_text_message(_text_update("QQS chegarasi qancha?"))

    rag_stub.assert_awaited_once_with("QQS chegarasi qancha?")
    bot_stub.send_message.assert_awaited_once()
    kwargs = bot_stub.send_message.await_args.kwargs
    assert kwargs["chat_id"] == _CHAT_ID
    assert kwargs["text"] == answer.text
    assert kwargs["disable_web_page_preview"] is True


@pytest.mark.asyncio
async def test_handle_text_message_sends_rag_failed_template_when_rag_raises(
    bot_stub: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rag_stub = AsyncMock(side_effect=RagError("boom"))
    monkeypatch.setattr("apps.bot.handlers.text.answer_question", rag_stub)

    await handle_text_message(_text_update("qanday qilib soliq tolayman"))

    bot_stub.send_message.assert_awaited_once()
    kwargs = bot_stub.send_message.await_args.kwargs
    assert kwargs["chat_id"] == _CHAT_ID
    assert kwargs["text"] == TEMPLATES["rag_failed"][Language.UZ_LATIN]
