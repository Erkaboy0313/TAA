"""Language detection for TAA input text.

Rules the bot needs to pick a user's language on first contact and to
keep RAG answers in the same language as the query. Three-way choice
between the two Uzbek scripts and Russian — see the module tests for
the exact decision tree.
"""

from __future__ import annotations

from apps.accounts.constants import Language

# Letters unique to Uzbek Cyrillic (absent from Russian).
_UZ_CYRILLIC_MARKERS = frozenset("ўғҳқЎҒҲҚ")

# Letters common in Russian and absent from modern Uzbek Cyrillic.
_RUSSIAN_MARKERS = frozenset("ыэъЫЭЪ")

_CYRILLIC_MIN = "Ѐ"
_CYRILLIC_MAX = "ӿ"


def _is_cyrillic(ch: str) -> bool:
    return _CYRILLIC_MIN <= ch <= _CYRILLIC_MAX


def detect_language(text: str) -> str:
    """Best-guess Language for `text`. Whitespace-only inputs return the
    product default (UZ_LATIN).
    """
    if not text or not text.strip():
        return Language.UZ_LATIN

    has_cyrillic = any(_is_cyrillic(ch) for ch in text)
    if not has_cyrillic:
        return Language.UZ_LATIN

    if any(ch in _UZ_CYRILLIC_MARKERS for ch in text):
        return Language.UZ_CYRILLIC
    if any(ch in _RUSSIAN_MARKERS for ch in text):
        return Language.RUSSIAN

    # Ambiguous Cyrillic without unique markers — bias toward Russian.
    return Language.RUSSIAN
