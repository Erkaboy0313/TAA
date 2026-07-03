"""Tests for the ``ingest_lex_uz`` management command (E02 real ingest).

The scraper is mocked at the command boundary so we never hit lex.uz.
Gemini's ``embed`` is patched via ``GeminiEmbeddingProvider.embed``
per project-context R11 (mock external, real Postgres).
"""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError

from apps.corpus.models import EMBEDDING_DIMENSIONS, Chunk, Document
from apps.corpus.scrapers.lex_uz import ParsedArticle


def _articles() -> list[ParsedArticle]:
    """Two-article fixture across a single section."""
    return [
        ParsedArticle(
            section="I BOLIM. UMUMIY QOIDALAR",
            chapter="1-bob. Asosiy qoidalar",
            article_ref="1",
            title="1-modda. Kirish",
            content="1-modda. Kirish\n\nUshbu Kodeks tartibga soladi.",
            paragraphs=["Ushbu Kodeks tartibga soladi."],
        ),
        ParsedArticle(
            section="I BOLIM. UMUMIY QOIDALAR",
            chapter="1-bob. Asosiy qoidalar",
            article_ref="2",
            title="2-modda. Qonunchilik",
            content="2-modda. Qonunchilik\n\nSoliq qonunchiligi Kodeksdan iborat.",
            paragraphs=["Soliq qonunchiligi Kodeksdan iborat."],
        ),
    ]


_EXPECTED_INGEST_CHUNKS: int = 2

# Module-wide: use pytest-django's `transaction=True` mode so the outer test
# transaction is a real one that gets flushed between tests. asyncio.run inside
# the ingest command opens a fresh event loop whose ORM connection lives
# outside a savepoint; the flush path is the only pytest-django mechanism that
# reliably scrubs those leaks.
pytestmark = pytest.mark.django_db(transaction=True)


def _vector(seed: float) -> list[float]:
    return [seed] * EMBEDDING_DIMENSIONS


@pytest.fixture
def patched_scraper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Replace the scraper entry points with fixture-backed stubs."""
    html_path = tmp_path / "src.html"
    html_path.write_text("<html>stub</html>", encoding="utf-8")

    async def _fake_fetch(_cache_path: Path) -> str:
        return html_path.read_text(encoding="utf-8")

    def _fake_parse(_html: str) -> list[ParsedArticle]:
        return _articles()

    monkeypatch.setattr(
        "apps.corpus.management.commands.ingest_lex_uz.fetch_tax_code_html",
        _fake_fetch,
    )
    monkeypatch.setattr(
        "apps.corpus.management.commands.ingest_lex_uz.parse_tax_code",
        _fake_parse,
    )
    return html_path


@pytest.fixture
def gemini_embed_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    stub = AsyncMock(side_effect=lambda texts: [_vector(0.1 + i * 0.01) for i in range(len(texts))])
    monkeypatch.setattr(
        "apps.corpus.management.commands.ingest_lex_uz.GeminiEmbeddingProvider.embed",
        stub,
    )
    return stub


def test_dry_run_prints_stats_without_touching_db(
    patched_scraper: Path,  # noqa: ARG001 -- installs the scraper stub
    settings,
) -> None:
    settings.GEMINI_API_KEY = ""  # dry-run must NOT require a key.
    stdout = StringIO()

    call_command("ingest_lex_uz", "--dry-run", "--source-html", str(patched_scraper), stdout=stdout)

    output = stdout.getvalue()
    assert "articles=2" in output
    assert "dry-run" in output
    assert Document.objects.count() == 0
    assert Chunk.objects.count() == 0


def test_ingest_lex_uz_persists_documents_and_chunks(
    patched_scraper: Path,
    gemini_embed_stub: AsyncMock,  # noqa: ARG001 -- installs the embed stub
    settings,
) -> None:
    settings.GEMINI_API_KEY = "test-key"
    call_command(
        "ingest_lex_uz",
        "--source-html",
        str(patched_scraper),
        stdout=StringIO(),
    )

    # One section -> one Document; two articles -> two Chunks.
    assert Document.objects.count() == 1
    assert Chunk.objects.count() == _EXPECTED_INGEST_CHUNKS
    refs = sorted(Chunk.objects.values_list("article_ref", flat=True))
    assert refs == ["1", "2"]


def test_ingest_lex_uz_is_idempotent(
    patched_scraper: Path,
    gemini_embed_stub: AsyncMock,
    settings,
) -> None:
    settings.GEMINI_API_KEY = "test-key"
    call_command(
        "ingest_lex_uz",
        "--source-html",
        str(patched_scraper),
        stdout=StringIO(),
    )
    first_call_count = gemini_embed_stub.await_count

    call_command(
        "ingest_lex_uz",
        "--source-html",
        str(patched_scraper),
        stdout=StringIO(),
    )

    # Same content -> no re-embed on the second run.
    assert gemini_embed_stub.await_count == first_call_count
    assert Document.objects.count() == 1
    assert Chunk.objects.count() == _EXPECTED_INGEST_CHUNKS


def test_ingest_lex_uz_refuses_when_gemini_key_missing(
    patched_scraper: Path,
    settings,
) -> None:
    settings.GEMINI_API_KEY = ""

    with pytest.raises(CommandError, match="GEMINI_API_KEY"):
        call_command(
            "ingest_lex_uz",
            "--source-html",
            str(patched_scraper),
            stdout=StringIO(),
        )

    assert Document.objects.count() == 0
    assert Chunk.objects.count() == 0
