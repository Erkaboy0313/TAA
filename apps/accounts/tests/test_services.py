"""Tests for apps.accounts.services.

Integration tests hitting the real Postgres — project-context R11 forbids
mocking the DB or ORM. The only monkeypatch is on
`EntrepreneurProfile.objects.create` to force an ORM-level error inside
the transaction so we can observe atomic rollback.
"""

from decimal import Decimal

import pytest

from django.db import IntegrityError

from apps.accounts.constants import Language, OnboardingStep, Regime
from apps.accounts.exceptions import UserAlreadyExistsError
from apps.accounts.models import EntrepreneurProfile, User
from apps.accounts.services import create_user_from_telegram, update_profile

TELEGRAM_ID_NEW = 500_001
TELEGRAM_ID_PROFILE_CHECK = 500_002
TELEGRAM_ID_DEFAULT_USERNAME = 500_003
TELEGRAM_ID_DEFAULT_LANGUAGE = 500_004
TELEGRAM_ID_RUSSIAN_LANGUAGE = 500_005
TELEGRAM_ID_DUPLICATE = 500_006
TELEGRAM_ID_ROLLBACK = 500_007

EMPLOYEE_COUNT_UPDATE = 7
EMPLOYEE_COUNT_CREATE = 2
REVENUE_TEST = Decimal("50000000.00")


# ---------------------------------------------------------------------------
# create_user_from_telegram
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_user_from_telegram_persists_user_row_when_id_new():
    user = create_user_from_telegram(telegram_id=TELEGRAM_ID_NEW)

    assert user.pk == TELEGRAM_ID_NEW
    assert User.objects.filter(pk=TELEGRAM_ID_NEW).exists()


@pytest.mark.django_db
def test_create_user_from_telegram_creates_empty_profile_when_user_new():
    user = create_user_from_telegram(telegram_id=TELEGRAM_ID_PROFILE_CHECK)

    assert hasattr(user, "profile")
    assert user.profile.onboarding_step == OnboardingStep.NOT_STARTED
    assert user.profile.employee_count == 0
    assert user.profile.expected_annual_revenue is None


@pytest.mark.django_db
def test_create_user_from_telegram_defaults_username_to_empty_when_omitted():
    user = create_user_from_telegram(telegram_id=TELEGRAM_ID_DEFAULT_USERNAME)

    assert user.username == ""


@pytest.mark.django_db
def test_create_user_from_telegram_defaults_language_to_uz_latin_when_omitted():
    user = create_user_from_telegram(telegram_id=TELEGRAM_ID_DEFAULT_LANGUAGE)

    assert user.language == Language.UZ_LATIN


@pytest.mark.django_db
def test_create_user_from_telegram_persists_non_default_language_when_supplied():
    user = create_user_from_telegram(
        telegram_id=TELEGRAM_ID_RUSSIAN_LANGUAGE,
        language=Language.RUSSIAN,
    )

    assert user.language == Language.RUSSIAN
    assert User.objects.get(pk=TELEGRAM_ID_RUSSIAN_LANGUAGE).language == Language.RUSSIAN


@pytest.mark.django_db
def test_create_user_from_telegram_raises_user_already_exists_when_id_taken(user_factory):
    user_factory(telegram_id=TELEGRAM_ID_DUPLICATE)

    with pytest.raises(UserAlreadyExistsError):
        create_user_from_telegram(telegram_id=TELEGRAM_ID_DUPLICATE)


@pytest.mark.django_db(transaction=True)
def test_create_user_from_telegram_rolls_back_user_when_profile_create_fails(monkeypatch):
    """If profile creation inside the atomic block raises, the user row
    must not survive. Force an IntegrityError on the profile create step
    and check that no user row remains.
    """
    original_create = EntrepreneurProfile.objects.create

    def boom(*_args, **_kwargs):
        raise IntegrityError("simulated profile integrity failure")

    monkeypatch.setattr(EntrepreneurProfile.objects, "create", boom)

    with pytest.raises(IntegrityError):
        create_user_from_telegram(telegram_id=TELEGRAM_ID_ROLLBACK)

    monkeypatch.setattr(EntrepreneurProfile.objects, "create", original_create)
    assert not User.objects.filter(pk=TELEGRAM_ID_ROLLBACK).exists()


# ---------------------------------------------------------------------------
# update_profile
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_profile_writes_only_supplied_field_when_profile_exists(profile_factory):
    profile = profile_factory(employee_count=0)

    result = update_profile(user=profile.user, employee_count=EMPLOYEE_COUNT_UPDATE)

    assert result.employee_count == EMPLOYEE_COUNT_UPDATE
    result.refresh_from_db()
    assert result.employee_count == EMPLOYEE_COUNT_UPDATE


@pytest.mark.django_db
def test_update_profile_returns_fresh_instance_when_updated(profile_factory):
    profile = profile_factory(has_foreign_clients=False)

    result = update_profile(user=profile.user, has_foreign_clients=True)

    assert result.pk == profile.pk
    assert result.has_foreign_clients is True


@pytest.mark.django_db
def test_update_profile_bumps_updated_at_when_field_written(profile_factory):
    profile = profile_factory()
    before = profile.updated_at

    result = update_profile(user=profile.user, employee_count=EMPLOYEE_COUNT_UPDATE)

    assert result.updated_at > before


@pytest.mark.django_db
def test_update_profile_creates_profile_when_user_has_none(user_factory):
    user = user_factory()
    assert not EntrepreneurProfile.objects.filter(user=user).exists()

    result = update_profile(user=user, employee_count=EMPLOYEE_COUNT_CREATE)

    assert result.pk is not None
    assert EntrepreneurProfile.objects.filter(user=user).count() == 1
    assert result.employee_count == EMPLOYEE_COUNT_CREATE


@pytest.mark.django_db
def test_update_profile_raises_type_error_when_field_unknown(profile_factory):
    profile = profile_factory()

    with pytest.raises(TypeError):
        update_profile(user=profile.user, totally_made_up_field="oops")


@pytest.mark.django_db
def test_update_profile_persists_chosen_regime_when_supplied(profile_factory):
    profile = profile_factory(chosen_regime="")

    result = update_profile(user=profile.user, chosen_regime=Regime.YTT_4)

    assert result.chosen_regime == Regime.YTT_4
    result.refresh_from_db()
    assert result.chosen_regime == Regime.YTT_4


@pytest.mark.django_db
def test_update_profile_round_trips_decimal_revenue_when_supplied(profile_factory):
    profile = profile_factory()

    result = update_profile(user=profile.user, expected_annual_revenue=REVENUE_TEST)

    result.refresh_from_db()
    assert result.expected_annual_revenue == REVENUE_TEST
    assert isinstance(result.expected_annual_revenue, Decimal)
