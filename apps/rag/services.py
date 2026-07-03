"""RAG synthesis service (E03-S04 + E03-S05).

``answer_question`` is the async entrypoint used by the bot handlers.
It embeds the query, retrieves top-K chunks, prompts Gemini, extracts
citations from ``[#N]`` markers, and applies a MVP ban-list warning
(project-context R10; full rewriting lands in E03-S07).

Every real Gemini call is wrapped in the same retry + timeout envelope
as ``apps/voice/gemini.py`` (project-context R9).
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING

import httpx
from asgiref.sync import sync_to_async
from google import genai
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from django.conf import settings

from apps.corpus.embeddings import GeminiEmbeddingProvider
from apps.rag.exceptions import RagError, SynthesisError
from apps.rag.prompts import DISCLAIMER, SYSTEM_PROMPT_V1, build_prompt
from apps.rag.selectors import DEFAULT_TOP_K, search_similar_chunks

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from apps.corpus.models import Chunk

logger = logging.getLogger(__name__)

_SYNTHESIS_MODEL = "gemini-2.0-flash"
_RETRYABLE = retry_if_exception_type(httpx.HTTPError)
_CITATION_PATTERN = re.compile(r"\[#(\d+)\]")

# MVP ban-list — a full rewriting post-processor is E03-S07. For now we
# only log a warning so operators notice regressions in the prompt
# adherence without blocking user replies (spec says pass-through).
_BAN_PHRASES: tuple[str, ...] = (
    "men tavsiya qilaman",
    "sizga X ni tanla",
    "bu eng yaxshi",
    "рекомендую вам",
    "лучший вариант для вас",
    "выберите X",
)

_FALLBACK_NO_CONTEXT: str = "Ma'lumotim yo'q."


@dataclass
class RagAnswer:
    """Structured result returned by ``answer_question``.

    ``citations`` and ``chunk_ids`` are kept as parallel ordered lists so
    the bot layer can render the answer without touching the ORM again.
    """

    text: str
    citations: list[str] = field(default_factory=list)
    chunk_ids: list[int] = field(default_factory=list)


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Return the process-wide Gemini client. Cached to reuse HTTP pool."""
    if not settings.GEMINI_API_KEY:
        raise RagError("gemini not configured")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def _with_retry_and_timeout[T](
    op: Callable[[], Awaitable[T]],
    *,
    on_timeout: str,
) -> T:
    """Run ``op`` with 3x exp backoff on httpx errors, capped at settings.GEMINI_TIMEOUT_SECONDS."""

    async def _retrying() -> T:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
            retry=_RETRYABLE,
            reraise=True,
        ):
            with attempt:
                return await op()
        raise RuntimeError("unreachable")  # pragma: no cover

    try:
        return await asyncio.wait_for(_retrying(), timeout=settings.GEMINI_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        raise TimeoutError(on_timeout) from exc


async def _synthesize(prompt: str) -> str:
    """Call Gemini synthesis with retry + timeout; return the raw text."""
    client = _client()

    async def _call() -> str:
        response = await client.aio.models.generate_content(
            model=_SYNTHESIS_MODEL,
            contents=[SYSTEM_PROMPT_V1, prompt],
        )
        return (response.text or "").strip()

    try:
        return await _with_retry_and_timeout(_call, on_timeout="synthesis timeout")
    except TimeoutError as exc:
        raise SynthesisError(f"synthesis timeout after {settings.GEMINI_TIMEOUT_SECONDS}s") from exc
    except (RetryError, httpx.HTTPError) as exc:
        raise SynthesisError("synthesis failed after 3 attempts") from exc


def _extract_citations(text: str, chunks: list[Chunk]) -> tuple[list[str], list[int]]:
    """Return ordered, de-duplicated ``(source_urls, chunk_ids)`` cited by ``text``.

    Any ``[#N]`` marker outside the range of the retrieved chunk list is
    silently skipped — Gemini occasionally invents markers, and we would
    rather drop the phantom citation than raise on it.
    """
    citations: list[str] = []
    chunk_ids: list[int] = []
    seen_urls: set[str] = set()

    for match in _CITATION_PATTERN.finditer(text):
        index = int(match.group(1)) - 1
        if index < 0 or index >= len(chunks):
            continue
        chunk = chunks[index]
        url = chunk.document.source_url
        if url in seen_urls:
            continue
        seen_urls.add(url)
        citations.append(url)
        chunk_ids.append(chunk.pk)

    return citations, chunk_ids


def _check_ban_list(text: str) -> None:
    """Log a warning if any banned phrase is present. Pass-through by design (E03-S07)."""
    lowered = text.lower()
    hits = [phrase for phrase in _BAN_PHRASES if phrase in lowered]
    if hits:
        logger.warning("rag.ban_list.hit", extra={"phrases": hits, "count": len(hits)})


def _append_disclaimer(text: str) -> str:
    """Ensure the answer ends with the mandatory disclaimer (R10)."""
    if DISCLAIMER in text:
        return text
    stripped = text.rstrip()
    return f"{stripped}\n\n{DISCLAIMER}"


async def answer_question(question: str) -> RagAnswer:
    """Embed → retrieve → synthesise → parse citations → append disclaimer."""
    embedding_provider = GeminiEmbeddingProvider()
    vectors = await embedding_provider.embed([question])
    if not vectors:
        raise SynthesisError("embedding returned no vectors")
    query_vector = vectors[0]

    chunks = await sync_to_async(search_similar_chunks, thread_sensitive=True)(
        query_vector, DEFAULT_TOP_K
    )

    if not chunks:
        return RagAnswer(text=_append_disclaimer(_FALLBACK_NO_CONTEXT))

    prompt = build_prompt(question, chunks)
    raw_answer = await _synthesize(prompt)
    _check_ban_list(raw_answer)
    citations, chunk_ids = _extract_citations(raw_answer, chunks)
    final_text = _append_disclaimer(raw_answer)
    return RagAnswer(text=final_text, citations=citations, chunk_ids=chunk_ids)
