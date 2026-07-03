"""Tests for ``apps.rag.services.answer_question`` (E03-S04 + E03-S05).

Every test mocks the external boundaries — Gemini embed, Gemini
synthesis, and the pgvector selector — so no real network or DB call
leaves the process (project-context R11).
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from apps.rag.exceptions import SynthesisError
from apps.rag.prompts import DISCLAIMER
from apps.rag.services import _client, answer_question


def _fake_chunk(*, pk: int, content: str, source_url: str) -> object:
    """Duck-type stand-in that the services code can consume."""
    document = SimpleNamespace(source_url=source_url)
    return SimpleNamespace(pk=pk, content=content, document=document)


def _fake_gemini_client(*, generate: AsyncMock) -> SimpleNamespace:
    """Return a SimpleNamespace shaped like `google.genai.Client`."""
    return SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))


async def _instant_timeout(awaitable: object, *_args: object, **_kwargs: object) -> object:
    """Close the wrapped coroutine, then raise TimeoutError.

    Mirrors the helper in apps/voice/tests/test_gemini.py so we can
    force a timeout without waiting the full 30 s budget.
    """
    if hasattr(awaitable, "close"):
        awaitable.close()
    raise TimeoutError


@pytest.fixture(autouse=True)
def _reset_client_cache() -> None:
    """Clear the lru_cache between tests so patched settings take effect."""
    _client.cache_clear()
    yield
    _client.cache_clear()


@pytest.fixture
def embed_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Force ``GeminiEmbeddingProvider.embed`` to return a canned vector."""
    stub = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        "apps.rag.services.GeminiEmbeddingProvider.embed",
        stub,
    )
    return stub


@pytest.fixture
def search_stub(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Force the selector to return a controllable list of duck-typed chunks."""
    chunks: list[object] = [
        _fake_chunk(pk=101, content="Modda 461", source_url="https://lex.uz/a"),
        _fake_chunk(pk=202, content="Modda 462", source_url="https://lex.uz/b"),
    ]

    def _fake_search(_vector: list[float], _k: int) -> list[object]:
        return chunks

    monkeypatch.setattr("apps.rag.services.search_similar_chunks", _fake_search)
    return chunks


async def test_answer_question_returns_rag_answer_with_citations_on_happy_path(
    embed_stub: AsyncMock,  # noqa: ARG001 — installs the embed stub
    search_stub: list[object],  # noqa: ARG001 — installs the selector stub
) -> None:
    raw = "QQS chegarasi bir milliard so'm [#1]. Aylanma soliq stavkasi [#2]."
    generate = AsyncMock(return_value=SimpleNamespace(text=raw, candidates=[]))
    with patch("apps.rag.services._client", return_value=_fake_gemini_client(generate=generate)):
        answer = await answer_question("QQS chegarasi qancha?")

    assert raw in answer.text
    assert answer.text.endswith(DISCLAIMER)
    assert answer.citations == ["https://lex.uz/a", "https://lex.uz/b"]
    assert answer.chunk_ids == [101, 202]
    assert generate.await_count == 1


async def test_answer_question_returns_fallback_when_no_chunks_found(
    embed_stub: AsyncMock,  # noqa: ARG001 — installs the embed stub
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("apps.rag.services.search_similar_chunks", lambda _v, _k: [])
    generate = AsyncMock()
    with patch("apps.rag.services._client", return_value=_fake_gemini_client(generate=generate)):
        answer = await answer_question("noma'lum savol")

    assert "Ma'lumotim yo'q" in answer.text
    assert answer.text.endswith(DISCLAIMER)
    assert answer.citations == []
    assert answer.chunk_ids == []
    # Synthesis must NOT be called when there is nothing to ground on.
    generate.assert_not_awaited()


async def test_answer_question_logs_warning_when_banned_phrase_present(
    embed_stub: AsyncMock,  # noqa: ARG001 — installs the embed stub
    search_stub: list[object],  # noqa: ARG001 — installs the selector stub
    caplog: pytest.LogCaptureFixture,
) -> None:
    raw = "Men tavsiya qilaman: YTT 4% [#1]. Chegara 1 mlrd."
    generate = AsyncMock(return_value=SimpleNamespace(text=raw, candidates=[]))
    with (
        patch("apps.rag.services._client", return_value=_fake_gemini_client(generate=generate)),
        caplog.at_level(logging.WARNING, logger="apps.rag.services"),
    ):
        answer = await answer_question("qaysi rejim yaxshi?")

    assert raw in answer.text  # ban list is pass-through in MVP (E03-S07 rewrites)
    assert any(r.message == "rag.ban_list.hit" for r in caplog.records)


async def test_answer_question_wraps_synthesis_timeout_as_synthesis_error(
    embed_stub: AsyncMock,  # noqa: ARG001 — installs the embed stub
    search_stub: list[object],  # noqa: ARG001 — installs the selector stub
) -> None:
    generate = AsyncMock(return_value=SimpleNamespace(text="unused", candidates=[]))
    with (
        patch("apps.rag.services._client", return_value=_fake_gemini_client(generate=generate)),
        patch("apps.rag.services.asyncio.wait_for", side_effect=_instant_timeout),
        pytest.raises(SynthesisError, match="timeout"),
    ):
        await answer_question("timeout question")
