"""Tests for apps.accounts.hashing.hash_telegram_id."""

from __future__ import annotations

import string

import pytest

from apps.accounts.hashing import TELEGRAM_ID_HASH_LENGTH, hash_telegram_id


def test_hash_returns_eight_char_string() -> None:
    result = hash_telegram_id(42)
    assert isinstance(result, str)
    assert len(result) == TELEGRAM_ID_HASH_LENGTH


def test_hash_is_deterministic() -> None:
    assert hash_telegram_id(123456789) == hash_telegram_id(123456789)


def test_hash_differs_across_ids() -> None:
    assert hash_telegram_id(1) != hash_telegram_id(2)


def test_hash_is_all_hex_chars() -> None:
    result = hash_telegram_id(999)
    assert set(result) <= set(string.hexdigits.lower())


@pytest.mark.parametrize(
    "telegram_id",
    [1, 42, 1_000_000, 9_999_999_999, 12_345_678_901],
)
def test_hash_handles_range_of_ids(telegram_id: int) -> None:
    result = hash_telegram_id(telegram_id)
    assert len(result) == TELEGRAM_ID_HASH_LENGTH
