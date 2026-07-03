"""Tests for the `seed_corpus` management command (E02-S05).

Every test patches `apps.corpus.embeddings._client` (or the provider
directly) so no real Gemini call leaves the process (project-context
R11). The DB is real — R11 forbids mocking Postgres.
"""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from django.core.management import call_command

from apps.corpus.embeddings import _client
from apps.corpus.fixtures import SEED_ENTRIES
from apps.corpus.models import EMBEDDING_DIMENSIONS, Chunk, Document

_EXPECTED_SEED_COUNT = len(SEED_ENTRIES)


def _fake_client(*, embed: AsyncMock) -> SimpleNamespace:
    return SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(embed_content=embed)))


def _embed_response_for(count: int) -> SimpleNamespace:
    vectors = [[0.01 * (i + 1)] * EMBEDDING_DIMENSIONS for i in range(count)]
    embeddings = [SimpleNamespace(values=v) for v in vectors]
    return SimpleNamespace(embeddings=embeddings)


@pytest.fixture(autouse=True)
def _reset_client_cache() -> None:
    _client.cache_clear()
    yield
    _client.cache_clear()


@pytest.mark.django_db
def test_dry_run_lists_entries_without_touching_the_database() -> None:
    stdout = StringIO()
    call_command("seed_corpus", "--dry-run", stdout=stdout)

    output = stdout.getvalue()
    for entry in SEED_ENTRIES:
        assert entry["source_url"] in output
        assert entry["title"] in output
    assert Document.objects.count() == 0
    assert Chunk.objects.count() == 0


@pytest.mark.django_db
def test_seed_corpus_creates_documents_and_chunks_when_gemini_returns_vectors() -> None:
    embed = AsyncMock(return_value=_embed_response_for(_EXPECTED_SEED_COUNT))
    with patch("apps.corpus.embeddings._client", return_value=_fake_client(embed=embed)):
        call_command("seed_corpus", stdout=StringIO())

    assert Document.objects.count() == _EXPECTED_SEED_COUNT
    assert Chunk.objects.count() == _EXPECTED_SEED_COUNT
    for entry in SEED_ENTRIES:
        document = Document.objects.get(source_url=entry["source_url"])
        assert document.title == entry["title"]
        assert document.chunks.count() == 1
        chunk = document.chunks.first()
        assert chunk.article_ref == entry["article_ref"]
        assert len(chunk.embedding) == EMBEDDING_DIMENSIONS


@pytest.mark.django_db
def test_seed_corpus_is_idempotent_when_run_twice() -> None:
    embed = AsyncMock(return_value=_embed_response_for(_EXPECTED_SEED_COUNT))
    with patch("apps.corpus.embeddings._client", return_value=_fake_client(embed=embed)):
        call_command("seed_corpus", stdout=StringIO())
        call_command("seed_corpus", stdout=StringIO())

    assert Document.objects.count() == _EXPECTED_SEED_COUNT
    assert Chunk.objects.count() == _EXPECTED_SEED_COUNT


@pytest.mark.django_db
def test_seed_corpus_stores_zero_vectors_when_gemini_key_is_missing(settings) -> None:
    settings.GEMINI_API_KEY = ""

    call_command("seed_corpus", stdout=StringIO())

    assert Document.objects.count() == _EXPECTED_SEED_COUNT
    for chunk in Chunk.objects.all():
        assert len(chunk.embedding) == EMBEDDING_DIMENSIONS
        assert all(value == 0.0 for value in chunk.embedding)
