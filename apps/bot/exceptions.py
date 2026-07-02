"""Domain exceptions for the bot app."""

from apps.core.exceptions import DomainError


class BotError(DomainError):
    """Base class for bot-layer failures."""


class BotNotConfiguredError(BotError):
    """Raised when bot credentials are missing at first use."""
