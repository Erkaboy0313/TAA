"""Django models for the accounts app."""

from __future__ import annotations

import hashlib
from functools import cached_property

from django.db import models

from apps.accounts.constants import Language
from apps.core.models import TimestampedModel


class User(TimestampedModel):
    """A Telegram user of TAA.

    The Telegram numeric id is our primary key so bot updates map directly
    to a row without extra joins. Telegram usernames can change or be
    absent, so they are stored but not relied on for lookup.
    """

    telegram_id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=64, blank=True, default="")
    language = models.CharField(
        max_length=8,
        choices=Language.choices,
        default=Language.UZ_LATIN,
    )

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return f"User<{self.telegram_id_hash}>"

    @cached_property
    def telegram_id_hash(self) -> str:
        """8-char SHA-256 prefix of the telegram id, safe to log (R10 PII)."""
        digest = hashlib.sha256(str(self.telegram_id).encode("utf-8")).hexdigest()
        return digest[:8]
