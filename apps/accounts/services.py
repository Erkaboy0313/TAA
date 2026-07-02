"""Write operations for the accounts app.

Services own multi-step writes and enforce atomicity (project-context R4).
Bot handlers, views, and higher-level services call in; selectors do not.
Every public entry is keyword-only and returns the fresh model instance.
"""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction as db_transaction

from apps.accounts.constants import Language
from apps.accounts.exceptions import UserAlreadyExistsError
from apps.accounts.models import EntrepreneurProfile, User


@db_transaction.atomic
def create_user_from_telegram(
    *,
    telegram_id: int,
    username: str = "",
    language: str = Language.UZ_LATIN,
) -> User:
    """Atomically create a User and its empty EntrepreneurProfile.

    Raises `UserAlreadyExistsError` if a row with the given `telegram_id`
    already exists — callers should decide whether to fall back to a
    lookup or surface the collision.
    """
    try:
        user = User.objects.create(
            telegram_id=telegram_id,
            username=username,
            language=language,
        )
    except IntegrityError as exc:
        raise UserAlreadyExistsError("user with telegram_id already exists") from exc

    EntrepreneurProfile.objects.create(user=user)
    return user


@db_transaction.atomic
def update_profile(*, user: User, **fields: Any) -> EntrepreneurProfile:
    """Update the given user's profile with the supplied fields.

    If no profile exists yet — the wizard skipped early — the profile is
    created with the given fields plus defaults. Only fields present in
    the kwargs are written; the rest are untouched.

    Unknown field names raise `TypeError` early so typos do not silently
    lose data.
    """
    valid_fields = {f.name for f in EntrepreneurProfile._meta.get_fields()}
    unknown = set(fields) - valid_fields
    if unknown:
        raise TypeError(f"unknown profile fields: {sorted(unknown)}")

    profile, _created = EntrepreneurProfile.objects.get_or_create(user=user)
    if fields:
        for name, value in fields.items():
            setattr(profile, name, value)
        profile.save(update_fields=[*fields.keys(), "updated_at"])
    return profile
