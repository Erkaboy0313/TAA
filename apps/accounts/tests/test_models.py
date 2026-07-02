"""Tests for apps.accounts.models.User."""

import pytest

from apps.accounts.constants import Language
from apps.accounts.models import User

TELEGRAM_ID_HASH_LENGTH = 8


@pytest.mark.django_db
def test_user_saves_with_telegram_id_as_primary_key(user_factory):
    user = user_factory(telegram_id=123456789)
    assert User.objects.get(pk=123456789) == user


@pytest.mark.django_db
def test_user_defaults_to_uz_latin_language(user_factory):
    user = user_factory()
    assert user.language == Language.UZ_LATIN


@pytest.mark.django_db
def test_user_accepts_supported_languages(user_factory):
    for value in (Language.UZ_LATIN, Language.UZ_CYRILLIC, Language.RUSSIAN):
        u = user_factory(language=value)
        assert u.language == value


@pytest.mark.django_db
def test_user_str_masks_telegram_id(user_factory):
    user = user_factory(telegram_id=987654321)
    rendered = str(user)
    assert "987654321" not in rendered
    assert rendered.startswith("User<") and rendered.endswith(">")


@pytest.mark.django_db
def test_user_stamps_created_and_updated_on_save(user_factory):
    user = user_factory()
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.created_at <= user.updated_at


def test_telegram_id_hash_is_stable_and_short():
    # Pure function — no DB. Exercise hash directly via a bound object.
    u = User(telegram_id=42)
    h = u.telegram_id_hash
    assert len(h) == TELEGRAM_ID_HASH_LENGTH
    assert h == User(telegram_id=42).telegram_id_hash


def test_telegram_id_hash_differs_across_ids():
    assert User(telegram_id=1).telegram_id_hash != User(telegram_id=2).telegram_id_hash
