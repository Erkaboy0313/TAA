"""Read-only selectors for the accounts app.

Selectors are pure query functions — no writes, no side-effects. Bot
handlers and services call them to fetch data; they never construct
or mutate model instances.

Extra query optimisations (select_related, prefetch_related) are added
inline when a caller explicitly needs them. Do NOT eagerly join by
default — some call paths (admin, checks) only need the primary row.
"""

from __future__ import annotations

from apps.accounts.models import EntrepreneurProfile, User


def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Return the user whose Telegram id matches, or None."""
    return User.objects.filter(pk=telegram_id).first()


def get_profile(user: User) -> EntrepreneurProfile | None:
    """Return the profile attached to `user`, or None if none exists.

    Uses an explicit query so a caller passing a fresh (unsaved-profile)
    user still gets a clean `None` instead of a `RelatedObjectDoesNotExist`.
    """
    return EntrepreneurProfile.objects.filter(user=user).first()
