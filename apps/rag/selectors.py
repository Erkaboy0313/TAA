"""Read-side vector search over ``apps.corpus`` chunks (E03-S01).

Pure read: takes a pre-computed query embedding, returns the top-K
chunks ordered by cosine distance (smaller = closer). ``select_related``
pre-loads each chunk's ``Document`` so the caller can render citation
URLs without triggering N+1 SQL when iterating.
"""

from __future__ import annotations

from pgvector.django import CosineDistance

from apps.corpus.models import Chunk

# Default retrieval budget — architecture §6 pins the pipeline at top_k=5
# for the MVP synthesis prompt, chosen to keep the context window small
# enough for reliable citation extraction.
DEFAULT_TOP_K = 5


def search_similar_chunks(
    query_embedding: list[float],
    k: int = DEFAULT_TOP_K,
) -> list[Chunk]:
    """Return the ``k`` chunks closest to ``query_embedding`` by cosine distance.

    Materialises the queryset to a list so callers do not have to worry
    about re-executing the ORDER BY on iteration; ``select_related``
    keeps ``chunk.document`` accessible without a follow-up query.
    """
    queryset = (
        Chunk.objects.annotate(distance=CosineDistance("embedding", query_embedding))
        .select_related("document")
        .order_by("distance")[:k]
    )
    return list(queryset)
