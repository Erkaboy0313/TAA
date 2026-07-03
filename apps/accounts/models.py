"""Django models for the accounts app."""

from __future__ import annotations

from functools import cached_property

from django.db import models

from apps.accounts.constants import CurrentStatus, Language, OnboardingStep, Regime
from apps.accounts.hashing import hash_telegram_id
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
        return hash_telegram_id(self.telegram_id)


class EntrepreneurProfile(TimestampedModel):
    """The tadbirkor profile the onboarding wizard fills in step by step.

    All domain fields are nullable or have permissive defaults because the
    wizard persists partial state after every step — a half-onboarded user
    still has a row here. `chosen_regime` and `current_status` stay blank
    until the wizard fills them; `onboarding_step` defaults to
    `OnboardingStep.NOT_STARTED` so new rows land in a well-known state.
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
    current_status = models.CharField(
        max_length=32,
        choices=CurrentStatus.choices,
        blank=True,
        default="",
    )
    chosen_regime = models.CharField(
        max_length=32,
        choices=Regime.choices,
        blank=True,
        default="",
    )
    onboarding_step = models.CharField(
        max_length=32,
        choices=OnboardingStep.choices,
        default=OnboardingStep.NOT_STARTED,
    )

    class Meta:
        db_table = "accounts_profile"
        verbose_name = "entrepreneur profile"
        verbose_name_plural = "entrepreneur profiles"

    def __str__(self) -> str:
        # Reuse the User's masked hash so we never leak the raw telegram id (R10).
        return f"Profile<{self.user.telegram_id_hash}>"
