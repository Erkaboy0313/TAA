"""Tests for apps.bot.templates.render_template."""

from __future__ import annotations

import pytest

from apps.accounts.constants import Language
from apps.bot.templates import TEMPLATES, render_template


@pytest.mark.parametrize("name", ["help", "start", "unknown_command", "rate_limit"])
def test_render_returns_uz_latin_body_when_language_matches(name: str) -> None:
    result = render_template(name, Language.UZ_LATIN)
    assert result == TEMPLATES[name][Language.UZ_LATIN]


@pytest.mark.parametrize("name", ["help", "start", "unknown_command", "rate_limit"])
def test_render_returns_uz_cyrillic_body_when_language_matches(name: str) -> None:
    assert render_template(name, Language.UZ_CYRILLIC) == TEMPLATES[name][Language.UZ_CYRILLIC]


@pytest.mark.parametrize("name", ["help", "start", "unknown_command", "rate_limit"])
def test_render_returns_russian_body_when_language_matches(name: str) -> None:
    assert render_template(name, Language.RUSSIAN) == TEMPLATES[name][Language.RUSSIAN]


def test_render_falls_back_to_uz_latin_for_unknown_language() -> None:
    result = render_template("help", "fr")
    assert result == TEMPLATES["help"][Language.UZ_LATIN]


def test_render_raises_key_error_for_unknown_template() -> None:
    with pytest.raises(KeyError):
        render_template("nonexistent-template", Language.UZ_LATIN)


def test_render_leaves_literal_braces_untouched_when_no_context() -> None:
    # A copy that legitimately contains a `{` would trip str.format if we
    # unconditionally formatted. The API returns the raw string when no
    # kwargs are supplied to avoid this trap.
    tricky = "Salom {noname}"
    TEMPLATES["_test_tricky"] = {Language.UZ_LATIN: tricky}
    try:
        assert render_template("_test_tricky", Language.UZ_LATIN) == tricky
    finally:
        del TEMPLATES["_test_tricky"]


def test_render_interpolates_when_context_supplied() -> None:
    TEMPLATES["_test_greeting"] = {Language.UZ_LATIN: "Salom {name}"}
    try:
        assert render_template("_test_greeting", Language.UZ_LATIN, name="Aziza") == "Salom Aziza"
    finally:
        del TEMPLATES["_test_greeting"]
