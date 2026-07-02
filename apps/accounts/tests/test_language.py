"""Tests for apps.accounts.language.detect_language."""

from __future__ import annotations

import pytest

from apps.accounts.constants import Language
from apps.accounts.language import detect_language


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", Language.UZ_LATIN),
        ("   \n\t", Language.UZ_LATIN),
        ("hello world", Language.UZ_LATIN),
        ("Bugun 15k taxi qildim, oʻyladi", Language.UZ_LATIN),
        ("Salom, mening oʻzim yaxshi", Language.UZ_LATIN),
        ("Салом, менинг ўзим яхши", Language.UZ_CYRILLIC),
        ("Тошкент ғоят катта", Language.UZ_CYRILLIC),
        ("Ҳурмат", Language.UZ_CYRILLIC),
        ("Қандай", Language.UZ_CYRILLIC),
        ("Как ты", Language.RUSSIAN),
        ("Это тест", Language.RUSSIAN),
        ("объект", Language.RUSSIAN),
        ("Привет", Language.RUSSIAN),
        ("Menda ҳисоб бор", Language.UZ_CYRILLIC),
        ("hello Привет", Language.RUSSIAN),
        ("12345", Language.UZ_LATIN),
        ("🎉🚀", Language.UZ_LATIN),
        ("ЎЗБЕКИСТОН", Language.UZ_CYRILLIC),
    ],
)
def test_detect_language_returns_expected_when_text_given(text: str, expected: str) -> None:
    assert detect_language(text) == expected


def test_detect_language_returns_str_matching_enum_value_when_called() -> None:
    result = detect_language("Salom dunyo")
    assert isinstance(result, str)
    assert result == Language.UZ_LATIN.value


def test_detect_language_is_deterministic_when_called_repeatedly() -> None:
    text = "Салом, менинг ўзим яхши"
    first = detect_language(text)
    second = detect_language(text)
    third = detect_language(text)
    assert first == second == third
