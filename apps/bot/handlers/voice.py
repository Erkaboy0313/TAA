"""Voice-message handler — download → Gemini STT → RAG answer.

Wire-up for E04-S06 + E03-S11. Rules enforced here (project-context R9):

- audio bytes stay in local scope; never written to disk, never logged
- no user text logged (privacy — R10)
- Gemini timeout inherited from the provider; Telegram download bounded
  by ``_DOWNLOAD_TIMEOUT_SECONDS``

Flow: transcript replaces the old echo. We call :func:`answer_question`
with the transcript, then send a combined message that shows the user
what we heard AND the RAG answer via the ``voice_answer`` template. A
``VoiceError`` (STT) falls back to ``voice_failed``; a ``RagError``
(retrieval / synthesis) falls back to ``rag_failed``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from apps.accounts.constants import Language
from apps.bot.telegram import get_bot
from apps.bot.templates import render_template
from apps.rag.exceptions import RagError
from apps.rag.services import answer_question
from apps.voice.exceptions import VoiceError
from apps.voice.gemini import GeminiVoiceProvider

logger = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT_SECONDS = 10.0

# Real per-user language plumbing lands with the accounts integration
# story; for MVP smoke testing we hardcode Uzbek-Latin — the same
# default the language detector falls back to.
_DEFAULT_LANGUAGE: str = Language.UZ_LATIN


def _extract_message(update: dict[str, Any]) -> dict[str, Any]:
    return update.get("message") or update.get("edited_message") or {}


def _file_id(update: dict[str, Any]) -> str | None:
    voice = _extract_message(update).get("voice") or {}
    file_id = voice.get("file_id")
    return file_id if isinstance(file_id, str) and file_id else None


def _chat_id(update: dict[str, Any]) -> int | None:
    chat = _extract_message(update).get("chat") or {}
    chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


async def _download_audio(file_id: str) -> bytes:
    """Fetch the voice payload from Telegram's file server, in-memory only."""
    bot = get_bot()
    tg_file = await bot.get_file(file_id)
    payload = await asyncio.wait_for(
        tg_file.download_as_bytearray(),
        timeout=_DOWNLOAD_TIMEOUT_SECONDS,
    )
    return bytes(payload)


async def _send(chat_id: int, template_name: str, language: str, **context: str) -> None:
    body = render_template(template_name, language, **context)
    bot = get_bot()
    await bot.send_message(chat_id=chat_id, text=body, disable_web_page_preview=True)


async def handle_voice_message(update: dict[str, Any]) -> None:
    """Transcribe the incoming voice message and reply with the RAG answer.

    A :class:`VoiceError` (STT failure) translates into ``voice_failed``.
    A :class:`RagError` (retrieval / synthesis) translates into
    ``rag_failed``. Anything else propagates to the dispatcher's global
    error path.
    """
    update_id = update.get("update_id")
    file_id = _file_id(update)
    chat_id = _chat_id(update)
    language = _DEFAULT_LANGUAGE

    if file_id is None:
        logger.warning("bot.handler.voice.missing_file_id", extra={"update_id": update_id})
        return

    if chat_id is None:
        logger.warning("bot.handler.voice.missing_chat_id", extra={"update_id": update_id})
        return

    try:
        audio_bytes = await _download_audio(file_id)
        transcript = await GeminiVoiceProvider().transcribe(audio_bytes, language)
    except VoiceError:
        logger.exception("bot.handler.voice.transcription_failed", extra={"update_id": update_id})
        await _send(chat_id, "voice_failed", language)
        return

    logger.info(
        "bot.handler.voice.transcribed",
        extra={"update_id": update_id, "transcript_len": len(transcript)},
    )

    try:
        answer = await answer_question(transcript)
    except (RagError, VoiceError):
        logger.exception("bot.handler.voice.rag_failed", extra={"update_id": update_id})
        await _send(chat_id, "rag_failed", language)
        return

    await _send(
        chat_id,
        "voice_answer",
        language,
        transcript=transcript,
        answer=answer.text,
    )
