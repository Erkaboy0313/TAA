"""Tests for apps.accounts.models.EntrepreneurProfile."""

from decimal import Decimal

import pytest

from apps.accounts.models import EntrepreneurProfile


@pytest.mark.django_db
def test_profile_persists_with_defaults_when_created_from_factory(profile_factory):
    profile = profile_factory()
    assert profile.pk is not None
    assert EntrepreneurProfile.objects.filter(pk=profile.pk).exists()


@pytest.mark.django_db
def test_profile_field_defaults_when_freshly_created(profile_factory):
    profile = profile_factory()
    assert profile.profession_oked == ""
    assert profile.expected_annual_revenue is None
    assert profile.employee_count == 0
    assert profile.has_foreign_clients is False
    assert profile.is_it_sector is False
    assert profile.current_status == ""
    assert profile.chosen_regime == ""
    assert profile.onboarding_step == ""


@pytest.mark.django_db
def test_expected_annual_revenue_round_trips_as_decimal_when_set(profile_factory):
    revenue = Decimal("50000000.00")
    profile = profile_factory(expected_annual_revenue=revenue)
    profile.refresh_from_db()
    assert profile.expected_annual_revenue == revenue
    # R8: money is Decimal, never float — assert the concrete type survives the round trip.
    assert isinstance(profile.expected_annual_revenue, Decimal)


@pytest.mark.django_db
def test_expected_annual_revenue_round_trips_as_none_when_unset(profile_factory):
    profile = profile_factory(expected_annual_revenue=None)
    profile.refresh_from_db()
    assert profile.expected_annual_revenue is None


@pytest.mark.django_db
def test_profile_str_masks_raw_telegram_id(profile_factory, user_factory):
    user = user_factory(telegram_id=987654321)
    profile = profile_factory(user=user)
    rendered = str(profile)
    assert "987654321" not in rendered
    assert user.telegram_id_hash in rendered
    assert rendered.startswith("Profile<") and rendered.endswith(">")


@pytest.mark.django_db
def test_profile_is_deleted_when_user_is_deleted(profile_factory):
    profile = profile_factory()
    profile_pk = profile.pk
    profile.user.delete()
    assert not EntrepreneurProfile.objects.filter(pk=profile_pk).exists()


@pytest.mark.django_db
def test_user_profile_reverse_accessor_returns_profile(profile_factory):
    profile = profile_factory()
    profile.user.refresh_from_db()
    assert profile.user.profile == profile
