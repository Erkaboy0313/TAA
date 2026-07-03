"""Bot-side logging filter that hashes any `telegram_id` extras leaked
into log records (R10 §PII).

Handlers today deliberately log `update_id` only — never `telegram_id`
— but if a future handler slips, this filter downgrades the leak to an
8-char hash and drops the raw value before the formatter runs.
"""

from __future__ import annotations

import logging

from apps.accounts.hashing import hash_telegram_id


class PiiRedactionFilter(logging.Filter):
    """Redact well-known PII attributes from log records in place."""

    def filter(self, record: logging.LogRecord) -> bool:
        raw = getattr(record, "telegram_id", None)
        if raw is not None:
            try:
                record.telegram_id_hash = hash_telegram_id(int(raw))
            except (TypeError, ValueError):
                record.telegram_id_hash = "invalid"
            delattr(record, "telegram_id")
        return True
