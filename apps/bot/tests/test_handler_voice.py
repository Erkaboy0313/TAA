"""Tests for ``apps.bot.handlers.voice.handle_voice_message`` (E04-S06 + E03-S11).

Coverage focus:

- happy path: file download → Gemini transcribe → RAG answer → combined
  ``voice_answer`` reply carrying both transcript AND answer
- transcription failure surfaces the ``voice_failed`` copy
- RAG failure surfaces the ``rag_failed`` copy
- missing ``file_id`` / ``chat_id`` early-exit with a warning
- audio bytes never appear in log records (R9 hard rule)

Every test mocks the external boundaries (Telegram bot + Gemini
provider + RAG service). No real network, no real audio files — just
distinctive byte patterns that let us assert they are NOT logged.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.accounts.constants import Language
from apps.bot.handlers.voice import handle_voice_message
from apps.bot.templates import TEMPLATES
from apps.rag.exceptions import RagError
from apps.rag.services import RagAnswer
from apps.voice.exceptions import TranscriptionError

# A byte pattern distinctive enough to spot in any log record if it
# somehow leaked. Used by the R9 spot-check.
_FAKE_AUDIO = b"\xde\xad\xbe\xefTAA-SECRET-AUDIO-PATTERN\x00\x01"
_TRANSCRIPT = "Salom qanday soliq to'layman"
_ANSWER_TEXT = "Aylanma soliq 4% [#1]. Disclaimer."
_FILE_ID = "AwADAgAD-fake-file-id"
_CHAT_ID = 424242
_UPDATE_ID = 1001


def _voice_update(
    *,
    file_id: str | None = _FILE_ID,
    chat_id: int | None = _CHAT_ID,
) -> dict[str, Any]:
    """Build a minimal Telegram-shaped update carrying a voice message."""
    voice: dict[str, Any] = {"duration": 3}
    if file_id is not None:
        voice["file_id"] = file_id
    message: dict[str, Any] = {"message_id": 7, "voice": voice}
    if chat_id is not None:
        message["chat"] = {"id": chat_id, "type": "private"}
    return {"update_id": _UPDATE_ID, "message": message}


@pytest.fixture
def bot_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch ``get_bot`` to return an AsyncMock with a working ``get_file``."""
    tg_file = MagicMock()
    tg_file.download_as_bytearray = AsyncMock(return_value=bytearray(_FAKE_AUDIO))
    bot = AsyncMock()
    bot.get_file = AsyncMock(return_value=tg_file)
    bot.send_message = AsyncMock(return_value=None)
    monkeypatch.setattr("apps.bot.handlers.voice.get_bot", lambda: bot)
    return bot


@pytest.fixture
def transcribe_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch ``GeminiVoiceProvider.transcribe`` to a controllable AsyncMock."""
    stub = AsyncMock(return_value=_TRANSCRIPT)
    monkeypatch.setattr(
        "apps.bot.handlers.voice.GeminiVoiceProvider.transcribe",
        stub,
    )
    return stub


@pytest.fixture
def rag_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch ``answer_question`` (RAG service) to a controllable AsyncMock."""
    stub = AsyncMock(return_value=RagAnswer(text=_ANSWER_TEXT, citations=["https://lex.uz/a"]))
    monkeypatch.setattr("apps.bot.handlers.voice.answer_question", stub)
    return stub


@pytest.mark.asyncio
async def test_handle_voice_downloads_transcribes_and_replies_with_rag_answer(
    bot_stub: AsyncMock,
    transcribe_stub: AsyncMock,
    rag_stub: AsyncMock,
) -> None:
    await handle_voice_message(_voice_update())

    bot_stub.get_file.assert_awaited_once_with(_FILE_ID)
    transcribe_stub.assert_awaited_once_with(_FAKE_AUDIO, Language.UZ_LATIN)
    rag_stub.assert_awaited_once_with(_TRANSCRIPT)
    bot_stub.send_message.assert_awaited_once()
    kwargs = bot_stub.send_message.await_args.kwargs
    assert kwargs["chat_id"] == _CHAT_ID
    # The combined ``voice_answer`` reply must show both the transcript
    # AND the RAG answer text.
    assert _TRANSCRIPT in kwargs["text"]
    assert _ANSWER_TEXT in kwargs["text"]


@pytest.mark.asyncio
async def test_handle_voice_sends_rag_failed_copy_when_rag_raises(
    bot_stub: AsyncMock,
    transcribe_stub: AsyncMock,  # noqa: ARG001 — installs the transcribe stub
    rag_stub: AsyncMock,
) -> None:
    rag_stub.side_effect = RagError("gemini synthesis exploded")

    await handle_voice_message(_voice_update())

    bot_stub.send_message.assert_awaited_once()
    kwargs = bot_stub.send_message.await_args.kwargs
    assert kwargs["chat_id"] == _CHAT_ID
    assert kwargs["text"] == TEMPLATES["rag_failed"][Language.UZ_LATIN]


@pytest.mark.asyncio
async def test_handle_voice_sends_voice_failed_copy_when_transcription_raises(
    bot_stub: AsyncMock,
    transcribe_stub: AsyncMock,
    rag_stub: AsyncMock,
) -> None:
    transcribe_stub.side_effect = TranscriptionError("gemini exploded")

    await handle_voice_message(_voice_update())

    rag_stub.assert_not_awaited()
    bot_stub.send_message.assert_awaited_once()
    kwargs = bot_stub.send_message.await_args.kwargs
    assert kwargs["chat_id"] == _CHAT_ID
    assert kwargs["text"] == TEMPLATES["voice_failed"][Language.UZ_LATIN]


@pytest.mark.asyncio
async def test_handle_voice_warns_and_no_send_when_file_id_missing(
    bot_stub: AsyncMock,
    transcribe_stub: AsyncMock,
    rag_stub: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    update = _voice_update(file_id=None)
    with caplog.at_level(logging.WARNING, logger="apps.bot.handlers.voice"):
        await handle_voice_message(update)

    bot_stub.get_file.assert_not_awaited()
    transcribe_stub.assert_not_awaited()
    rag_stub.assert_not_awaited()
    bot_stub.send_message.assert_not_awaited()
    assert any(r.message == "bot.handler.voice.missing_file_id" for r in caplog.records)


@pytest.mark.asyncio
async def test_handle_voice_warns_and_no_send_when_chat_id_missing(
    bot_stub: AsyncMock,
    transcribe_stub: AsyncMock,
    rag_stub: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    update = _voice_update(chat_id=None)
    with caplog.at_level(logging.WARNING, logger="apps.bot.handlers.voice"):
        await handle_voice_message(update)

    bot_stub.get_file.assert_not_awaited()
    transcribe_stub.assert_not_awaited()
    rag_stub.assert_not_awaited()
    bot_stub.send_message.assert_not_awaited()
    assert any(r.message == "bot.handler.voice.missing_chat_id" for r in caplog.records)


@pytest.mark.asyncio
async def test_handle_voice_never_logs_raw_audio_bytes(
    bot_stub: AsyncMock,  # noqa: ARG001 — installs the download stub
    transcribe_stub: AsyncMock,  # noqa: ARG001 — installs the transcribe stub
    rag_stub: AsyncMock,  # noqa: ARG001 — installs the RAG stub
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R9 spot-check: distinctive audio marker must not appear anywhere in
    the captured log stream (message body, args, or extras).
    """
    marker = "TAA-SECRET-AUDIO-PATTERN"

    with caplog.at_level(logging.DEBUG, logger="apps.bot.handlers.voice"):
        await handle_voice_message(_voice_update())

    for record in caplog.records:
        rendered = record.getMessage()
        assert marker not in rendered
        for value in record.__dict__.values():
            assert marker not in repr(value)
