"""AppConfig for apps.rag."""

from django.apps import AppConfig


class RagConfig(AppConfig):
    """RAG Q&A pipeline (architecture §6).

    Owns the pgvector similarity selector (E03-S01), the versioned
    system prompt (E03-S03), and the Gemini synthesis service with
    citation extraction (E03-S04, E03-S05). No models of its own — it
    consumes ``apps.corpus`` chunks.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rag"
    label = "rag"
