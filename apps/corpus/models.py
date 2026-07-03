"""Django models for the RAG corpus.

`Document` is a top-level source (a Tax Code article page, a soliq.uz
clarification, a hand-written seed entry). `Chunk` is one embed-able
slice of that document. Chunks carry a 768-dim vector embedding produced
by Gemini `text-embedding-004` and are indexed with pgvector HNSW for
cosine similarity search (architecture §4).
"""

from __future__ import annotations

from pgvector.django import HnswIndex, VectorField

from django.db import models

from apps.core.models import TimestampedModel

# Gemini `text-embedding-004` output dimensionality. Kept as a module-level
# constant so a future embedding-model swap only touches one place (R5).
EMBEDDING_DIMENSIONS = 768


class Document(TimestampedModel):
    """A source document in the RAG corpus.

    `source_url` is the natural key: lex.uz URL for scraped articles, or a
    `seed://...` slug for the hand-written local-dev fixture. Unique so
    idempotent seed / ingest runs collapse to `get_or_create`.
    """

    source_url = models.URLField(unique=True)
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=8, default="uz-Latn")

    class Meta:
        db_table = "corpus_document"
        verbose_name = "document"
        verbose_name_plural = "documents"

    def __str__(self) -> str:
        return f"Document<{self.source_url}>"


class Chunk(TimestampedModel):
    """A retrievable slice of a `Document` with its embedding vector.

    `article_ref` is a short human-readable pointer (e.g. `"1.4"` or
    `"3"`) preserved verbatim from the source so citations rendered to
    the user match what they would find on lex.uz / soliq.uz.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    article_ref = models.CharField(max_length=32, blank=True, default="")
    content = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)

    class Meta:
        db_table = "corpus_chunk"
        verbose_name = "chunk"
        verbose_name_plural = "chunks"
        indexes = [
            HnswIndex(
                name="chunk_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self) -> str:
        ref = self.article_ref or "-"
        return f"Chunk<{self.document_id}:{ref}>"
