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


class EntrepreneurProfile(TimestampedModel):
    """The tadbirkor profile the onboarding wizard fills in step by step.

    All domain fields are nullable or have permissive defaults because the
    wizard persists partial state after every step — a half-onboarded user
    still has a row here. The three enum-shaped CharFields
    (`current_status`, `chosen_regime`, `onboarding_step`) intentionally
    carry no `choices=` yet; the `TextChoices` sets land in E01-S03 together
    with validation and constraints.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    profession_oked = models.CharField(max_length=10, blank=True, default="")
    # UZS. Decimal, NEVER float (R8). null while the wizard has not asked yet.
    expected_annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    employee_count = models.PositiveIntegerField(default=0)
    has_foreign_clients = models.BooleanField(default=False)
    is_it_sector = models.BooleanField(default=False)
    # choices land in S03
    current_status = models.CharField(max_length=32, blank=True, default="")
    # choices land in S03
    chosen_regime = models.CharField(max_length=32, blank=True, default="")
    # choices land in S03
    onboarding_step = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        db_table = "accounts_profile"
        verbose_name = "entrepreneur profile"
        verbose_name_plural = "entrepreneur profiles"

    def __str__(self) -> str:
        # Reuse the User's masked hash so we never leak the raw telegram id (R10).
        return f"Profile<{self.user.telegram_id_hash}>"
