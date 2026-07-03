"""Domain exceptions for the RAG app.

Rooted at ``DomainError`` so bot-layer handlers can ``except DomainError``
at the boundary and translate any RAG failure into a user-friendly
apology (project-context R4).
"""

from apps.core.exceptions import DomainError


class RagError(DomainError):
    """Base class for expected RAG pipeline failures (retrieval, synthesis)."""


class NoChunksError(RagError):
    """Raised when the vector search returns no chunks for a query."""


class SynthesisError(RagError):
    """Raised when Gemini synthesis fails (timeout, network, empty response)."""
