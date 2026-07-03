"""Local pytest fixtures for the corpus app."""

import pytest

from apps.corpus.tests.factories import ChunkFactory, DocumentFactory


@pytest.fixture
def document_factory():
    return DocumentFactory


@pytest.fixture
def document(db, document_factory):  # noqa: ARG001 — `db` triggers pytest-django DB setup.
    return document_factory()


@pytest.fixture
def chunk_factory():
    return ChunkFactory


@pytest.fixture
def chunk(db, chunk_factory):  # noqa: ARG001 — `db` triggers pytest-django DB setup.
    return chunk_factory()
