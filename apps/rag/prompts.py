"""Prompt composition for the RAG synthesis step (E03-S03).

``SYSTEM_PROMPT_V1`` is the versioned system prompt handed to Gemini
alongside the CONTEXT + QUESTION block. Any change is a new version
(``v2``) shipped in a separate PR — never mutate the current version
in-place, otherwise A/B evaluation loses its baseline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.corpus.models import Chunk

# The mandatory footer every RAG answer must end with (project-context
# R10). Kept as a module constant so the ban-list post-processor and the
# tests can reference the exact text.
DISCLAIMER: str = (
    "Bu ma'lumot vositasi. Muhim qarorlar uchun sertifikatli maslahatchi kerak bo'ladi."
)

SYSTEM_PROMPT_V1: str = f"""\
You are TAA — a bilingual (Uzbek / Russian) information assistant for
Uzbekistan tax, accounting, and legal topics. You are NOT a certified
tax advisor. You are an informational tool.

RULES YOU MUST FOLLOW:

1. Answer in the SAME language the user wrote in. Detect between
   uz-Latn (O'zbekcha lotin), uz-Cyrl (Ўзбекча кирилл), and ru (Русский).
2. Ground every factual claim in the CONTEXT block. If the context does
   not answer the question, say so plainly — do NOT invent citations.
3. Cite every claim inline using the exact chunk marker ``[#N]`` where
   ``N`` is the number in the CONTEXT block (e.g. ``[#1]``, ``[#3]``).
   Do NOT invent numbers that are not in the CONTEXT block.
4. Do NOT give personalised paid tax-consulting advice. Never write
   phrases like "men tavsiya qilaman", "sizga X ni tanla", "bu eng
   yaxshi variant", "рекомендую вам", "лучший вариант для вас".
   Instead, present options and trade-offs neutrally so the user can
   decide.
5. Prefer short paragraphs and bullet lists over long walls of text.
6. Always end your response with this exact footer on its own line:
   {DISCLAIMER}
"""


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    """Assemble the CONTEXT + QUESTION block that follows the system prompt.

    Chunks are rendered as ``[#N] {content} (Manba: {source_url})`` — the
    ``[#N]`` marker is what Gemini is instructed to cite by, and what the
    citation parser in ``services.py`` scans for.
    """
    lines: list[str] = ["CONTEXT:"]
    for index, chunk in enumerate(chunks, start=1):
        source_url = chunk.document.source_url
        content = chunk.content.strip()
        lines.append(f"[#{index}] {content} (Manba: {source_url})")
    lines.append("")
    lines.append(f"QUESTION: {question}")
    return "\n".join(lines)
