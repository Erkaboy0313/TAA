"""Domain exceptions for the corpus app.

Rooted at `DomainError` so bot-layer handlers can `except DomainError` at
the boundary and translate any corpus failure into a user-friendly
apology (project-context R4).
"""

from apps.core.exceptions import DomainError


class CorpusError(DomainError):
    """Base class for expected corpus-pipeline failures (embedding, ingest)."""


class EmbeddingError(CorpusError):
    """Raised when the embedding provider fails (Gemini error, timeout, empty text)."""


class IngestionError(CorpusError):
    """Raised when ingestion of a `Document` fails (parse error, network, seed corruption)."""
