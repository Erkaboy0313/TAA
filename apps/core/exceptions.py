"""Base exceptions for TAA domain errors.

Per project-context R4, every app defines its own `exceptions.py` with a
hierarchy rooted at `DomainError`. Consumers can `except DomainError` at
the boundary (bot handlers, views) to distinguish expected domain
failures from unexpected bugs.
"""


class DomainError(Exception):
    """Base class for all expected domain-level errors raised by TAA services.

    Do NOT catch bare `Exception` at handler boundaries — catch `DomainError`
    for cases the app knows how to explain to the user, and let everything
    else propagate to Django's error handling.
    """
