"""Smoke tests for apps.core.exceptions."""

from apps.core.exceptions import DomainError


def test_domain_error_is_an_exception() -> None:
    assert issubclass(DomainError, Exception)


def test_domain_error_can_be_raised_and_caught() -> None:
    try:
        raise DomainError("test message")
    except DomainError as exc:
        assert str(exc) == "test message"
