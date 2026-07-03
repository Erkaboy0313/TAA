"""Tests for apps.bot.logging_filter.PiiRedactionFilter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apps.accounts.hashing import hash_telegram_id
from apps.bot.logging_filter import PiiRedactionFilter

if TYPE_CHECKING:
    import pytest


def _make_record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="apps.bot.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_filter_hashes_telegram_id_and_drops_raw() -> None:
    record = _make_record(telegram_id=123_456_789)
    assert PiiRedactionFilter().filter(record) is True
    assert not hasattr(record, "telegram_id")
    assert record.telegram_id_hash == hash_telegram_id(123_456_789)


def test_filter_is_noop_when_telegram_id_absent() -> None:
    record = _make_record()
    assert PiiRedactionFilter().filter(record) is True
    assert not hasattr(record, "telegram_id_hash")


def test_filter_is_noop_when_telegram_id_is_none() -> None:
    record = _make_record(telegram_id=None)
    assert PiiRedactionFilter().filter(record) is True
    # None is treated as absent — the attribute stays as-is, no hash added.
    assert record.telegram_id is None
    assert not hasattr(record, "telegram_id_hash")


def test_filter_marks_invalid_when_id_is_not_a_number() -> None:
    record = _make_record(telegram_id="not-a-number")
    assert PiiRedactionFilter().filter(record) is True
    assert not hasattr(record, "telegram_id")
    assert record.telegram_id_hash == "invalid"


def test_filter_always_returns_true() -> None:
    assert PiiRedactionFilter().filter(_make_record(telegram_id=1)) is True
    assert PiiRedactionFilter().filter(_make_record()) is True


def test_filter_end_to_end_on_a_scoped_logger(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("apps.bot.tests.scoped_logging_filter")
    logger.addFilter(PiiRedactionFilter())
    try:
        with caplog.at_level(logging.INFO, logger=logger.name):
            logger.info("event", extra={"telegram_id": 500})

        matches = [r for r in caplog.records if r.name == logger.name]
        assert len(matches) == 1
        record = matches[0]
        assert not hasattr(record, "telegram_id")
        assert record.telegram_id_hash == hash_telegram_id(500)
    finally:
        logger.filters.clear()
