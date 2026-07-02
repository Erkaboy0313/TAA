"""Local pytest fixtures for the accounts app."""

import pytest

from apps.accounts.tests.factories import UserFactory


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def user(db, user_factory):  # noqa: ARG001 — `db` triggers pytest-django DB setup.
    return user_factory()
