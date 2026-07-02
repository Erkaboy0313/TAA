"""Tests for apps.accounts.selectors."""

import pytest

from apps.accounts.models import EntrepreneurProfile, User
from apps.accounts.selectors import get_profile, get_user_by_telegram_id


@pytest.mark.django_db
def test_get_user_by_telegram_id_returns_user_when_id_exists(user_factory):
    user = user_factory(telegram_id=100_500)
    assert get_user_by_telegram_id(100_500) == user


@pytest.mark.django_db
def test_get_user_by_telegram_id_returns_none_when_id_missing():
    assert get_user_by_telegram_id(999_999_999) is None


@pytest.mark.django_db
def test_get_user_by_telegram_id_returns_none_when_id_is_zero():
    assert get_user_by_telegram_id(0) is None


@pytest.mark.django_db
def test_get_user_by_telegram_id_returns_correct_type(user_factory):
    user_factory(telegram_id=100_501)
    result = get_user_by_telegram_id(100_501)
    assert isinstance(result, User)


@pytest.mark.django_db
def test_get_user_by_telegram_id_is_pure(user_factory):
    user_factory(telegram_id=200_000)
    before = User.objects.count()
    get_user_by_telegram_id(200_000)
    get_user_by_telegram_id(200_000)
    assert User.objects.count() == before


@pytest.mark.django_db
def test_get_profile_returns_profile_when_exists(profile_factory):
    profile = profile_factory()
    assert get_profile(profile.user) == profile


@pytest.mark.django_db
def test_get_profile_returns_none_when_no_profile(user_factory):
    user = user_factory()
    assert get_profile(user) is None


@pytest.mark.django_db
def test_get_profile_returns_none_for_fresh_user_without_related_error(user_factory):
    """A user without a saved profile must yield None, not RelatedObjectDoesNotExist.

    The naive `user.profile` reverse accessor raises when the OneToOne row
    is missing; the selector avoids that trap by issuing a filter query.
    """
    user = user_factory()
    assert get_profile(user) is None


@pytest.mark.django_db
def test_get_profile_returns_correct_type(profile_factory):
    profile = profile_factory()
    result = get_profile(profile.user)
    assert isinstance(result, EntrepreneurProfile)


@pytest.mark.django_db
def test_get_profile_is_pure(profile_factory):
    profile = profile_factory()
    before = EntrepreneurProfile.objects.count()
    get_profile(profile.user)
    get_profile(profile.user)
    assert EntrepreneurProfile.objects.count() == before
