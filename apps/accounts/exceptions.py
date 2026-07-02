"""Domain exceptions for the accounts app.

Per project-context R4/R6, we ship the root class only — concrete
subclasses appear when a real caller needs to distinguish them.
"""

from apps.core.exceptions import DomainError


class AccountsError(DomainError):
    """Base class for expected accounts-domain errors (user lookup,
    profile updates, language handling).
    """
