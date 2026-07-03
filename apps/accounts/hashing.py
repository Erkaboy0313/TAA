"""Shared PII-safe hashing helpers.

Used by `User.telegram_id_hash` and by the bot logging filter so both
paths agree on the same 8-char SHA-256 prefix convention — enough to
disambiguate log lines without ever leaking the underlying id (R10).
"""

from __future__ import annotations

import hashlib

TELEGRAM_ID_HASH_LENGTH = 8


def hash_telegram_id(telegram_id: int) -> str:
    """Return an 8-char SHA-256 prefix of `str(telegram_id)`."""
    digest = hashlib.sha256(str(telegram_id).encode("utf-8")).hexdigest()
    return digest[:TELEGRAM_ID_HASH_LENGTH]
