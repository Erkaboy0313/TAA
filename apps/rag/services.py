"""RAG synthesis service (E03-S04 + E03-S05 + E02 no-hallucination).

``answer_question`` is the async entrypoint used by the bot handlers.
It embeds the query, retrieves top-K chunks, checks the closest chunk
against ``settings.RAG_MAX_DISTANCE`` -- if that best-chunk distance
is too high the question is off-topic and Gemini is NEVER called.

When we do call Gemini, the strict-grounding prompt forces the model
to emit ``NEEDS_CONTEXT`` if the CONTEXT does not answer the question;
we translate that sentinel into the same off-topic refusal path.

Every Gemini call is wrapped in the same retry + timeout envelope as
``apps/voice/gemini.py`` (project-context R9).
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
from apps.rag.prompts import DISCLAIMER, NEEDS_CONTEXT_TOKEN, SYSTEM_PROMPT_V2, build_prompt
from apps.rag.selectors import search_similar_chunks

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from apps.corpus.models import Chunk

logger = logging.getLogger(__name__)

_SYNTHESIS_MODEL = "gemini-2.0-flash"
_RETRYABLE = retry_if_exception_type(httpx.HTTPError)
_CITATION_PATTERN = re.compile(r"\[#(\d+)\]")

# MVP ban-list -- a full rewriting post-processor is E03-S07. For now we
# only log a warning so operators notice regressions in prompt
# adherence without blocking user replies (spec says pass-through).
_BAN_PHRASES: tuple[str, ...] = (
    "men tavsiya qilaman",
    "sizga X ni tanla",
    "bu eng yaxshi",
    "рекомендую вам",
    "лучший вариант для вас",
    "выберите X",
)


@dataclass
class RagAnswer:
    """Structured result returned by ``answer_question``.

    ``off_topic`` is set when either (a) the best-chunk distance
    exceeded ``settings.RAG_MAX_DISTANCE`` and Gemini was never called,
    or (b) Gemini itself replied ``NEEDS_CONTEXT``. The bot handler
    renders the ``rag_off_topic`` template in that case instead of
    ``text`` (which is left as an empty string).
    """

    text: str
    citations: list[str] = field(default_factory=list)
    chunk_ids: list[int] = field(default_factory=list)
    off_topic: bool = False


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
            contents=[SYSTEM_PROMPT_V2, prompt],
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
    silently skipped -- Gemini occasionally invents markers, and we would
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


def _off_topic_answer() -> RagAnswer:
    """The bot layer renders ``rag_off_topic`` when this is returned."""
    return RagAnswer(text="", off_topic=True)


def _best_distance(chunks: list[Chunk]) -> float | None:
    """Smallest cosine distance across the top-K, or ``None`` if unset.

    ``search_similar_chunks`` annotates each chunk with ``distance``,
    but tests using fake chunks may omit the attribute -- treat that
    as ``None`` and skip the threshold guard.
    """
    distances = [getattr(c, "distance", None) for c in chunks]
    real = [d for d in distances if d is not None]
    return min(real) if real else None


async def answer_question(question: str) -> RagAnswer:
    """Embed -> retrieve -> distance guard -> synthesise -> parse citations.

    The pipeline short-circuits before Gemini in two places:

    * empty retrieval -> off-topic;
    * best-chunk cosine distance > ``settings.RAG_MAX_DISTANCE`` ->
      off-topic (this is the *hard* no-hallucination gate).
    """
    embedding_provider = GeminiEmbeddingProvider()
    vectors = await embedding_provider.embed([question])
    if not vectors:
        raise SynthesisError("embedding returned no vectors")
    query_vector = vectors[0]

    chunks = await sync_to_async(search_similar_chunks, thread_sensitive=True)(
        query_vector, settings.RAG_TOP_K
    )

    if not chunks:
        logger.info("rag.off_topic", extra={"reason": "no_chunks"})
        return _off_topic_answer()

    best = _best_distance(chunks)
    if best is not None and best > settings.RAG_MAX_DISTANCE:
        logger.info(
            "rag.off_topic",
            extra={"reason": "distance_threshold", "best_distance": best},
        )
        return _off_topic_answer()

    prompt = build_prompt(question, chunks)
    raw_answer = await _synthesize(prompt)
    if raw_answer.strip() == NEEDS_CONTEXT_TOKEN:
        logger.info("rag.off_topic", extra={"reason": "needs_context_token"})
        return _off_topic_answer()

    _check_ban_list(raw_answer)
    citations, chunk_ids = _extract_citations(raw_answer, chunks)
    final_text = _append_disclaimer(raw_answer)
    return RagAnswer(text=final_text, citations=citations, chunk_ids=chunk_ids)
