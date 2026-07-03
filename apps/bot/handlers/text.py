"""Plain-text message handler — routes user text to the RAG pipeline (E03-S10).

Handles both free-form text (``Salom qanday soliq...``) and the explicit
``/ask <query>`` command. RAG failures translate into a friendly
language-aware apology (``rag_failed`` template) so the user is never
left without feedback (project-context R4).
"""

from __future__ import annotations

import logging
from typing import Any

from apps.accounts.language import detect_language
from apps.bot.telegram import get_bot
from apps.bot.templates import render_template
from apps.rag.exceptions import RagError
from apps.rag.services import answer_question
from apps.voice.exceptions import VoiceError

logger = logging.getLogger(__name__)


def _extract_message(update: dict[str, Any]) -> dict[str, Any]:
    return update.get("message") or update.get("edited_message") or {}


def _chat_id(update: dict[str, Any]) -> int | None:
    chat = _extract_message(update).get("chat") or {}
    chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


def _text(update: dict[str, Any]) -> str:
    text = _extract_message(update).get("text")
    return text if isinstance(text, str) else ""


def _strip_ask_prefix(text: str) -> str:
    """Turn ``/ask salom`` into ``salom``; leave everything else untouched."""
    stripped = text.lstrip()
    if not stripped.startswith("/ask"):
        return text
    remainder = stripped[len("/ask") :].lstrip()
    # Drop an optional ``@bot`` suffix that Telegram appends in group chats.
    if remainder.startswith("@"):
        remainder = remainder.split(maxsplit=1)[1] if " " in remainder else ""
    return remainder


async def _send(chat_id: int, text: str) -> None:
    bot = get_bot()
    await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)


async def handle_text_message(update: dict[str, Any]) -> None:
    """Send the user's question through the RAG pipeline and reply.

    Domain errors (``RagError``, ``VoiceError`` — the latter can bubble
    through the shared embedding client) render as the ``rag_failed``
    template. Anything else propagates to the dispatcher's global error
    handler.
    """
    update_id = update.get("update_id")
    chat_id = _chat_id(update)
    raw_text = _text(update)
    question = _strip_ask_prefix(raw_text).strip()
    language = detect_language(question or raw_text)

    if chat_id is None:
        logger.warning("bot.handler.text.missing_chat_id", extra={"update_id": update_id})
        return

    if not question:
        logger.info("bot.handler.text.empty_question", extra={"update_id": update_id})
        return

    logger.info(
        "bot.handler.text.received",
        extra={"update_id": update_id, "question_len": len(question)},
    )

    try:
        answer = await answer_question(question)
    except (RagError, VoiceError):
        logger.exception("bot.handler.text.rag_failed", extra={"update_id": update_id})
        await _send(chat_id, render_template("rag_failed", language))
        return

    if answer.off_topic:
        await _send(chat_id, render_template("rag_off_topic", language))
        return

    await _send(chat_id, answer.text)
