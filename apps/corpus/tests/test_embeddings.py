"""Tests for `apps.corpus.embeddings` — Gemini batch embed with retry.

Every test patches `apps.corpus.embeddings._client` so no real network
call leaves the process (project-context R11). Vectors carry no PII,
but embeddings can leak the source text via similarity, so nothing is
logged with content.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from apps.corpus.embeddings import GeminiEmbeddingProvider, _client
from apps.corpus.exceptions import CorpusError, EmbeddingError

_MAX_ATTEMPTS = 3
_EMBEDDING_DIM = 768


def _fake_client(*, embed: AsyncMock) -> SimpleNamespace:
    """Build a stand-in for `google.genai.Client` with the shape the code uses."""
    return SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(embed_content=embed)))


def _embed_response(vectors: list[list[float]]) -> SimpleNamespace:
    embeddings = [SimpleNamespace(values=v) for v in vectors]
    return SimpleNamespace(embeddings=embeddings)


@pytest.fixture(autouse=True)
def _reset_client_cache() -> None:
    """Clear the lru_cache between tests so patched settings take effect."""
    _client.cache_clear()
    yield
    _client.cache_clear()


async def test_embed_returns_vectors_from_gemini_response() -> None:
    vectors_in = [[0.1] * _EMBEDDING_DIM, [0.2] * _EMBEDDING_DIM]
    embed = AsyncMock(return_value=_embed_response(vectors_in))
    with patch("apps.corpus.embeddings._client", return_value=_fake_client(embed=embed)):
        provider = GeminiEmbeddingProvider()
        result = await provider.embed(["one", "two"])

    assert len(result) == len(vectors_in)
    assert len(result[0]) == _EMBEDDING_DIM
    assert result[0][0] == pytest.approx(0.1)
    assert result[1][0] == pytest.approx(0.2)
    assert embed.await_count == 1


async def test_embed_raises_corpus_error_when_api_key_missing(settings) -> None:
    settings.GEMINI_API_KEY = ""
    provider = GeminiEmbeddingProvider()
    with pytest.raises(CorpusError, match="gemini not configured"):
        await provider.embed(["hello"])


async def test_embed_gives_up_after_three_attempts_and_raises_embedding_error() -> None:
    embed = AsyncMock(side_effect=httpx.ConnectError("boom"))
    with (
        patch("apps.corpus.embeddings._client", return_value=_fake_client(embed=embed)),
        pytest.raises(EmbeddingError, match="3 attempts"),
    ):
        provider = GeminiEmbeddingProvider()
        await provider.embed(["persistent failure"])
    assert embed.await_count == _MAX_ATTEMPTS
