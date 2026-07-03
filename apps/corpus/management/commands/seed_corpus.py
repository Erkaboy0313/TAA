"""Management command that seeds a minimal RAG corpus (E02-S05).

Reads `apps.corpus.fixtures.SEED_ENTRIES`, upserts one `Document` per
entry via `get_or_create(source_url=...)`, wipes existing chunks for the
document, then creates a single fresh `Chunk` with a Gemini-computed
embedding.

Idempotent: running twice does not duplicate documents. When
`GEMINI_API_KEY` is empty the command logs a warning and stores a
zero-vector placeholder so the schema is exercised in local dev without
a key (the "smoke seed" path).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from apps.corpus.embeddings import GeminiEmbeddingProvider
from apps.corpus.exceptions import CorpusError
from apps.corpus.fixtures import SEED_ENTRIES
from apps.corpus.models import EMBEDDING_DIMENSIONS, Chunk, Document

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """`python manage.py seed_corpus [--dry-run]` — hydrate the RAG corpus."""

    help = "Seed the RAG corpus from apps.corpus.fixtures.SEED_ENTRIES."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the entries that would be seeded without touching the DB.",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002 — Django BaseCommand signature
        if options.get("dry_run"):
            self._print_dry_run()
            return

        embeddings = self._compute_embeddings([entry["content"] for entry in SEED_ENTRIES])
        count = self._persist(embeddings)
        self.stdout.write(self.style.SUCCESS(f"seeded {count} documents"))

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _print_dry_run(self) -> None:
        for entry in SEED_ENTRIES:
            self.stdout.write(f"{entry['source_url']} — {entry['title']}")
        self.stdout.write(f"total: {len(SEED_ENTRIES)} entries (dry-run, DB not touched)")

    def _compute_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for `texts`, or zero-vectors when Gemini is unconfigured."""
        try:
            provider = GeminiEmbeddingProvider()
            return asyncio.run(provider.embed(texts))
        except CorpusError as exc:
            logger.warning("seed_corpus falling back to zero vectors: %s", exc)
            self.stdout.write(
                self.style.WARNING("GEMINI_API_KEY not set — storing zero vectors (smoke seed).")
            )
            zero = [0.0] * EMBEDDING_DIMENSIONS
            return [list(zero) for _ in texts]

    @db_transaction.atomic
    def _persist(self, embeddings: list[list[float]]) -> int:
        for entry, vector in zip(SEED_ENTRIES, embeddings, strict=True):
            document, _ = Document.objects.get_or_create(
                source_url=entry["source_url"],
                defaults={
                    "title": entry["title"],
                    "language": entry["language"],
                },
            )
            document.chunks.all().delete()
            Chunk.objects.create(
                document=document,
                article_ref=entry["article_ref"],
                content=entry["content"],
                embedding=vector,
            )
        return len(SEED_ENTRIES)
