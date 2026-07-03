"""Tests for ``apps.rag.selectors.search_similar_chunks`` (E03-S01).

Real Postgres + pgvector — cosine distance is a DB-side computation, so
mocking it away would defeat the point (project-context R11: never
mock the DB).
"""

from __future__ import annotations

import pytest

from apps.corpus.models import EMBEDDING_DIMENSIONS
from apps.corpus.tests.factories import ChunkFactory, DocumentFactory
from apps.rag.selectors import search_similar_chunks


def _unit_vector(seed: float) -> list[float]:
    """Return a deterministic 768-float vector clamped to a single value."""
    return [seed] * EMBEDDING_DIMENSIONS


@pytest.mark.django_db
def test_search_similar_chunks_returns_top_k_ordered_by_cosine_distance() -> None:
    document = DocumentFactory()
    near = ChunkFactory(document=document, article_ref="near", embedding=_unit_vector(0.1))
    mid = ChunkFactory(document=document, article_ref="mid", embedding=_unit_vector(0.5))
    far = ChunkFactory(document=document, article_ref="far", embedding=_unit_vector(-0.9))

    top_k = 2
    results = search_similar_chunks(_unit_vector(0.1), k=top_k)

    assert len(results) == top_k
    returned_refs = [chunk.article_ref for chunk in results]
    # ``near`` shares the query vector direction; ``far`` points the
    # opposite way and must not survive the top-2 filter.
    assert near.article_ref in returned_refs
    assert far.article_ref not in returned_refs
    assert mid.article_ref in returned_refs


@pytest.mark.django_db
def test_search_similar_chunks_returns_empty_list_when_no_chunks() -> None:
    results = search_similar_chunks(_unit_vector(0.1), k=5)
    assert results == []


@pytest.mark.django_db
def test_search_similar_chunks_preloads_document_via_select_related(
    django_assert_num_queries,
) -> None:
    ChunkFactory(embedding=_unit_vector(0.1))
    ChunkFactory(embedding=_unit_vector(0.2))

    results = search_similar_chunks(_unit_vector(0.1), k=5)
    # 1 query for the chunks — accessing ``.document`` must NOT issue
    # a follow-up query thanks to ``select_related``.
    with django_assert_num_queries(0):
        urls = [chunk.document.source_url for chunk in results]

    assert len(urls) == len(results)
