"""Local pytest fixtures for the accounts app."""

import pytest

from apps.accounts.tests.factories import ProfileFactory, UserFactory


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def user(db, user_factory):  # noqa: ARG001 — `db` triggers pytest-django DB setup.
    return user_factory()


@pytest.fixture
def profile_factory():
    return ProfileFactory


@pytest.fixture
def profile(db, profile_factory):  # noqa: ARG001 — `db` triggers pytest-django DB setup.
    return profile_factory()
