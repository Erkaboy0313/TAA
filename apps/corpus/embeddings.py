"""Embedding service for the RAG corpus.

`EmbeddingProvider` is the structural contract every concrete provider
must satisfy. Consumers depend on the Protocol, not on Gemini directly,
which keeps swap-out cheap (project-context R3 dependency inversion).

The Gemini implementation mirrors `apps/voice/gemini.py`: lazy cached
client, tenacity retry on `httpx.HTTPError`, `asyncio.wait_for` outer
timeout (project-context R9). Empty API key raises `CorpusError`.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import httpx
from google import genai
from google.genai import types as genai_types
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from django.conf import settings

from apps.corpus.exceptions import CorpusError, EmbeddingError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

# `text-embedding-004` was retired from v1beta; `gemini-embedding-001` is the
# current model. Native output is 3072-dim; we ask for 768 via `output_
# dimensionality` in the config below so `Chunk.embedding` VectorField(768)
# still fits without a migration.
_EMBED_MODEL = "gemini-embedding-001"
_EMBED_OUTPUT_DIM = 768
# Retry only on network-layer failures. A 4xx content error must NOT be
# retried blindly (project-context R9).
_RETRYABLE = retry_if_exception_type(httpx.HTTPError)


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Return the process-wide Gemini client. Cached to reuse HTTP pool."""
    if not settings.GEMINI_API_KEY:
        raise CorpusError("gemini not configured")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def _with_retry_and_timeout[T](
    op: Callable[[], Awaitable[T]],
    *,
    on_timeout: str,
) -> T:
    """Run `op` with 3x exp backoff on httpx errors, capped at settings.GEMINI_TIMEOUT_SECONDS."""

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


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Structural contract for a text-embedding engine.

    Batch API: callers pass N texts, receive N vectors of matching length
    (768-dim for Gemini `text-embedding-004`). One-at-a-time embedding is
    an anti-pattern for the ingestion pipeline (each call = one round
    trip), so the interface forces batching by design.
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one 768-float vector per input text, preserving order."""
        ...


class GeminiEmbeddingProvider:
    """Gemini implementation of the `EmbeddingProvider` Protocol.

    No constructor argument — the client is resolved lazily via
    `_client()`. Tests patch `apps.corpus.embeddings._client` (or its
    result) to avoid the network (project-context R11: mock external only).
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts as 768-float vectors."""
        client = _client()

        async def _call() -> list[list[float]]:
            response = await client.aio.models.embed_content(
                model=_EMBED_MODEL,
                contents=texts,
                config=genai_types.EmbedContentConfig(
                    output_dimensionality=_EMBED_OUTPUT_DIM,
                ),
            )
            return _extract_vectors(response)

        try:
            return await _with_retry_and_timeout(_call, on_timeout="embedding timeout")
        except TimeoutError as exc:
            raise EmbeddingError(
                f"embedding timeout after {settings.GEMINI_TIMEOUT_SECONDS}s"
            ) from exc
        except (RetryError, httpx.HTTPError) as exc:
            raise EmbeddingError("embedding failed after 3 attempts") from exc


def _extract_vectors(response: object) -> list[list[float]]:
    """Pull the ordered list of embedding vectors out of a Gemini response."""
    embeddings = getattr(response, "embeddings", None) or []
    vectors: list[list[float]] = []
    for item in embeddings:
        values = getattr(item, "values", None)
        if values is None:
            continue
        vectors.append([float(v) for v in values])
    return vectors
