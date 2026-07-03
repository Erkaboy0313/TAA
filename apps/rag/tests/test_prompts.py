"""Tests for ``apps.rag.prompts`` — SYSTEM_PROMPT_V1 + build_prompt (E03-S03)."""

from __future__ import annotations

from types import SimpleNamespace

from apps.rag.prompts import DISCLAIMER, SYSTEM_PROMPT_V1, build_prompt


def _fake_chunk(*, content: str, source_url: str) -> object:
    """Duck-type stand-in for `Chunk` — build_prompt only touches two attrs."""
    document = SimpleNamespace(source_url=source_url)
    return SimpleNamespace(content=content, document=document)


def test_build_prompt_includes_context_block_with_chunk_markers() -> None:
    chunks = [
        _fake_chunk(content="Modda 461: QQS", source_url="https://lex.uz/a"),
        _fake_chunk(content="Modda 462: aylanma soliq", source_url="https://lex.uz/b"),
    ]
    question = "QQS chegarasi qancha?"

    rendered = build_prompt(question, chunks)

    assert "CONTEXT:" in rendered
    assert "[#1] Modda 461: QQS (Manba: https://lex.uz/a)" in rendered
    assert "[#2] Modda 462: aylanma soliq (Manba: https://lex.uz/b)" in rendered
    assert f"QUESTION: {question}" in rendered


def test_system_prompt_v1_contains_disclaimer_and_ban_language() -> None:
    assert DISCLAIMER in SYSTEM_PROMPT_V1
    # Sanity check that the ban-list guidance is spelled out — otherwise
    # Gemini has no signal that these phrases are off-limits.
    assert "men tavsiya qilaman" in SYSTEM_PROMPT_V1
    assert "[#N]" in SYSTEM_PROMPT_V1
