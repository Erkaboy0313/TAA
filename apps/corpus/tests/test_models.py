"""Tests for apps.corpus.models — Document + Chunk."""

from __future__ import annotations

import pytest

from django.db import IntegrityError

from apps.corpus.models import EMBEDDING_DIMENSIONS, Chunk, Document

_FIXED_VECTOR = [float(i % 7) / 7.0 for i in range(EMBEDDING_DIMENSIONS)]


@pytest.mark.django_db
def test_document_source_url_is_unique_when_duplicated(document_factory):
    document_factory(source_url="seed://collision/one")

    with pytest.raises(IntegrityError):
        document_factory(source_url="seed://collision/one")


@pytest.mark.django_db
def test_chunk_cascades_when_parent_document_deleted(chunk_factory):
    chunk = chunk_factory()
    document = chunk.document

    document.delete()

    assert not Chunk.objects.filter(pk=chunk.pk).exists()
    assert not Document.objects.filter(pk=document.pk).exists()


@pytest.mark.django_db
def test_chunk_embedding_roundtrips_a_768_vector_when_saved(document_factory):
    document = document_factory()
    chunk = Chunk.objects.create(
        document=document,
        article_ref="1.4",
        content="Roundtrip probe",
        embedding=_FIXED_VECTOR,
    )

    chunk.refresh_from_db()

    assert len(chunk.embedding) == EMBEDDING_DIMENSIONS
    for stored, expected in zip(chunk.embedding, _FIXED_VECTOR, strict=True):
        assert stored == pytest.approx(expected)
