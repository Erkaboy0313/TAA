"""AppConfig for apps.corpus."""

from django.apps import AppConfig


class CorpusConfig(AppConfig):
    """RAG corpus store: `Document` + `Chunk` with pgvector embeddings.

    Owns ingestion of Tax Code / BHMS content (architecture §3), the
    embedding service that turns chunks into 768-dim vectors (E02-S04),
    and the seed management command that hydrates a minimal corpus for
    local dev (E02-S05).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.corpus"
    label = "corpus"
