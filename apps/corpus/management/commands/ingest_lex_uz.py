"""Management command that ingests the full Uzbek Tax Code from lex.uz.

Flow:

1. Load the source HTML (``--source-html PATH`` or cached fetch).
2. Parse into ``ParsedArticle`` objects using
   :func:`apps.corpus.scrapers.lex_uz.parse_tax_code`.
3. Group articles by section, one ``Document`` per section.
4. For each article: split into chunks, batch-embed via
   ``GeminiEmbeddingProvider``, upsert into ``Chunk``.

Idempotency: every chunk is fingerprinted by SHA-256 of its content
prefixed with ``article_ref``. On re-run we reuse existing chunks whose
fingerprint has not changed, and only re-embed the ones whose content
moved. That means running the command twice in a row is a cheap no-op.

Unlike ``seed_corpus``, this command REFUSES to run without a real
``GEMINI_API_KEY`` -- zero-vectors would pollute the retriever with
483 useless rows.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from apps.corpus.embeddings import GeminiEmbeddingProvider
from apps.corpus.exceptions import CorpusError, IngestionError
from apps.corpus.models import Chunk, Document
from apps.corpus.scrapers.lex_uz import (
    TAX_CODE_URL,
    ParsedArticle,
    chunk_article,
    fetch_tax_code_html,
    parse_tax_code,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = logging.getLogger(__name__)

# Default cache path -- gitignored via the ``data/`` rule. Overridable
# with ``--source-html`` for local dev / offline testing.
_DEFAULT_CACHE_PATH: Path = Path("data/cache/lex_uz_tax_code.html")

# Batch size for the Gemini embed call. Gemini's public docs cap the
# per-request batch at 100 texts; we stay conservatively below.
_EMBED_BATCH_SIZE: int = 100

# Progress log cadence -- one line per N articles keeps the ingest log
# scannable without spamming.
_PROGRESS_EVERY_N_ARTICLES: int = 10

# ~4 chars per token on average for Latin script -- close enough to
# estimate Gemini usage without pulling in a tokeniser.
_CHARS_PER_TOKEN: int = 4


def _batched(iterable: Iterable[str], size: int) -> Iterable[list[str]]:
    """Yield ``iterable`` in lists of ``size`` (last batch may be shorter)."""
    iterator = iter(iterable)
    while batch := list(islice(iterator, size)):
        yield batch


def _chunk_fingerprint(article_ref: str, content: str) -> str:
    """Stable content-hash used to skip re-embedding unchanged chunks."""
    payload = f"{article_ref}\n{content}".encode()
    return hashlib.sha256(payload).hexdigest()


class Command(BaseCommand):
    """``python manage.py ingest_lex_uz`` -- full Tax Code ingest."""

    help = "Fetch, parse, and ingest the Uzbek Tax Code from lex.uz."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--source-html",
            type=Path,
            default=None,
            help="Path to a local HTML file to use instead of fetching lex.uz.",
        )
        parser.add_argument(
            "--force-refresh",
            action="store_true",
            help="Delete the cached HTML before fetching.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and print stats only. Does not touch the DB.",
        )
        parser.add_argument(
            "--cache-path",
            type=Path,
            default=_DEFAULT_CACHE_PATH,
            help="Override the cache location for the fetched HTML.",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002 -- Django BaseCommand signature
        source_html: Path | None = options.get("source_html")
        cache_path: Path = options.get("cache_path") or _DEFAULT_CACHE_PATH
        force_refresh: bool = bool(options.get("force_refresh"))
        dry_run: bool = bool(options.get("dry_run"))

        if not dry_run and not settings.GEMINI_API_KEY:
            raise CommandError(
                "GEMINI_API_KEY is empty -- refusing to ingest. "
                "This command needs real embeddings; use --dry-run to parse only.",
            )

        if force_refresh and cache_path.exists() and source_html is None:
            self.stdout.write(self.style.WARNING(f"deleting cache at {cache_path}"))
            cache_path.unlink()

        html = self._load_html(source_html, cache_path)
        articles = parse_tax_code(html)
        self._print_stats(articles)

        if dry_run:
            self.stdout.write(self.style.SUCCESS("dry-run: DB not touched"))
            return

        provider = GeminiEmbeddingProvider()
        stats = asyncio.run(self._ingest(articles, provider))
        self.stdout.write(
            self.style.SUCCESS(
                f"ingested: documents={stats['documents']}, "
                f"chunks_created={stats['created']}, chunks_reused={stats['reused']}",
            ),
        )

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def _load_html(self, source_html: Path | None, cache_path: Path) -> str:
        if source_html is not None:
            if not source_html.exists():
                raise CommandError(f"--source-html {source_html} does not exist")
            self.stdout.write(f"loading HTML from {source_html}")
            return source_html.read_text(encoding="utf-8")

        self.stdout.write(f"loading HTML (cache={cache_path})")
        try:
            return asyncio.run(fetch_tax_code_html(cache_path))
        except Exception as exc:  # pragma: no cover -- httpx / IO
            raise CommandError(f"fetch failed: {exc}") from exc

    def _print_stats(self, articles: list[ParsedArticle]) -> None:
        sections = sorted({a.section for a in articles if a.section})
        chapters = sorted({a.chapter for a in articles if a.chapter})
        total_chars = sum(len(a.content) for a in articles)
        self.stdout.write(
            f"parsed: sections={len(sections)}, chapters={len(chapters)}, "
            f"articles={len(articles)}, total_chars={total_chars}, "
            f"est_tokens={total_chars // _CHARS_PER_TOKEN}",
        )

    async def _ingest(
        self,
        articles: list[ParsedArticle],
        provider: GeminiEmbeddingProvider,
    ) -> dict[str, int]:
        by_section: dict[str, list[ParsedArticle]] = {}
        for article in articles:
            by_section.setdefault(article.section or "UMUMIY QISM", []).append(article)

        stats: dict[str, int] = {"documents": 0, "created": 0, "reused": 0}
        for section_index, (section_title, section_articles) in enumerate(
            by_section.items(),
            start=1,
        ):
            source_url = f"{TAX_CODE_URL}#section-{section_index}"
            document = await self._upsert_document(source_url, section_title)
            counts = await self._ingest_section(document, section_articles, provider)
            stats["documents"] += 1
            stats["created"] += counts["created"]
            stats["reused"] += counts["reused"]

        return stats

    async def _upsert_document(self, source_url: str, title: str) -> Document:
        def _sync() -> Document:
            document, _ = Document.objects.update_or_create(
                source_url=source_url,
                defaults={"title": title, "language": "uz-Latn"},
            )
            return document

        return await sync_to_async(_sync, thread_sensitive=True)()

    async def _ingest_section(
        self,
        document: Document,
        articles: list[ParsedArticle],
        provider: GeminiEmbeddingProvider,
    ) -> dict[str, int]:
        # Build the flat list of (article_ref, chunk_text, fingerprint).
        rows: list[tuple[str, str, str]] = []
        for article in articles:
            for text in chunk_article(article):
                rows.append(
                    (article.article_ref, text, _chunk_fingerprint(article.article_ref, text)),
                )

        existing = await self._load_existing_fingerprints(document)
        pending: list[tuple[str, str, str]] = []
        reused = 0
        for ref, text, fp in rows:
            if existing.get(ref) == fp:
                reused += 1
                continue
            pending.append((ref, text, fp))

        created = 0
        if pending:
            texts = [text for _, text, _ in pending]
            vectors: list[list[float]] = []
            for batch in _batched(texts, _EMBED_BATCH_SIZE):
                batch_vectors = await provider.embed(batch)
                if len(batch_vectors) != len(batch):
                    raise IngestionError(
                        f"embedding batch mismatch: sent {len(batch)}, got {len(batch_vectors)}",
                    )
                vectors.extend(batch_vectors)

            created = await self._persist_chunks(document, pending, vectors)

        logger.info(
            "corpus.ingest_lex_uz.section_done",
            extra={
                "document": document.pk,
                "created": created,
                "reused": reused,
            },
        )
        if (created + reused) and (created + reused) % _PROGRESS_EVERY_N_ARTICLES == 0:
            self.stdout.write(
                f"  progress: doc={document.title[:40]} created={created} reused={reused}",
            )
        return {"created": created, "reused": reused}

    async def _load_existing_fingerprints(self, document: Document) -> dict[str, str]:
        def _sync() -> dict[str, str]:
            out: dict[str, str] = {}
            for chunk in Chunk.objects.filter(document=document).only("article_ref", "content"):
                out[chunk.article_ref] = _chunk_fingerprint(chunk.article_ref, chunk.content)
            return out

        return await sync_to_async(_sync, thread_sensitive=True)()

    async def _persist_chunks(
        self,
        document: Document,
        rows: list[tuple[str, str, str]],
        vectors: list[list[float]],
    ) -> int:
        def _sync() -> int:
            with db_transaction.atomic():
                refs = {ref for ref, _, _ in rows}
                Chunk.objects.filter(document=document, article_ref__in=refs).delete()
                Chunk.objects.bulk_create(
                    [
                        Chunk(
                            document=document,
                            article_ref=ref,
                            content=text,
                            embedding=vector,
                        )
                        for (ref, text, _fp), vector in zip(rows, vectors, strict=True)
                    ],
                    batch_size=200,
                )
            return len(rows)

        try:
            return await sync_to_async(_sync, thread_sensitive=True)()
        except CorpusError:
            raise
        except Exception as exc:  # pragma: no cover -- DB errors bubble up here
            raise IngestionError(f"persist failed for {document.pk}: {exc}") from exc
