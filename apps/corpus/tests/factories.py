"""factory-boy factories for the corpus app."""

from __future__ import annotations

import random

import factory
from factory.django import DjangoModelFactory

from apps.corpus.models import EMBEDDING_DIMENSIONS, Chunk, Document


def _random_vector() -> list[float]:
    """A deterministic-per-call 768-float vector — sufficient for schema tests."""
    return [random.random() for _ in range(EMBEDDING_DIMENSIONS)]


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    source_url = factory.Sequence(lambda n: f"seed://test-doc/{n}")
    title = factory.Faker("sentence", nb_words=4)
    language = "uz-Latn"


class ChunkFactory(DjangoModelFactory):
    class Meta:
        model = Chunk

    document = factory.SubFactory(DocumentFactory)
    article_ref = factory.Sequence(lambda n: f"{n}")
    content = factory.Faker("paragraph")
    embedding = factory.LazyFunction(_random_vector)
