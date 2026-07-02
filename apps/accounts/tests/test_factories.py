"""Smoke test for UserFactory."""

import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_user_factory_creates_persisted_user(user_factory):
    user = user_factory()
    assert User.objects.filter(pk=user.pk).exists()
