"""Prompt composition for the RAG synthesis step (E03-S03).

``SYSTEM_PROMPT_V2`` is the versioned system prompt handed to Gemini
alongside the CONTEXT + QUESTION block. Any change is a new version
shipped in a separate PR -- never mutate the current version in-place,
otherwise A/B evaluation loses its baseline.

V2 is a strict-grounding rewrite (E02 no-hallucination epic):

* v1 let Gemini narrate around the context. v2 forbids that -- if the
  context does not answer the question, the model must emit the
  literal token ``NEEDS_CONTEXT`` and nothing else, so the service
  layer can translate to the refusal template.
* The ``[#N]`` citation rule stays; the disclaimer footer stays.
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

# Sentinel Gemini emits when the CONTEXT block is insufficient. The
# services layer trips off_topic on this exact string.
NEEDS_CONTEXT_TOKEN: str = "NEEDS_CONTEXT"

SYSTEM_PROMPT_V2: str = f"""\
You are TAA -- a bilingual (Uzbek / Russian) information assistant for
Uzbekistan tax, accounting, and legal topics. You are NOT a certified
tax advisor. You are an informational tool bound to the Uzbek Tax Code.

RULES YOU MUST FOLLOW:

1. Answer in the SAME language the user wrote in. Detect between
   uz-Latn (O'zbekcha lotin), uz-Cyrl (Узбекча кирилл), and ru (Русский).
2. Answer ONLY from the CONTEXT below. You have NO other knowledge to
   draw on. If the CONTEXT does not answer the question, respond with
   the single word ``{NEEDS_CONTEXT_TOKEN}`` and nothing else -- no
   apology, no partial answer, no disclaimer.
3. Cite every factual claim inline using the exact chunk marker
   ``[#N]`` where ``N`` is the number in the CONTEXT block (e.g.
   ``[#1]``, ``[#3]``). Do NOT invent numbers that are not in the
   CONTEXT block.
4. Do NOT give personalised paid tax-consulting advice. Never write
   phrases like "men tavsiya qilaman", "sizga X ni tanla", "bu eng
   yaxshi variant", "рекомендую вам", "лучший вариант для вас".
   Present options and trade-offs neutrally so the user can decide.
5. Prefer short paragraphs and bullet lists over long walls of text.
6. When you DO answer (i.e. you did not emit ``{NEEDS_CONTEXT_TOKEN}``),
   end your response with this exact footer on its own line:
   {DISCLAIMER}
"""

# Backwards-compat alias -- any older import path keeps working while
# callers migrate. Removed in the next prompt-version PR.
SYSTEM_PROMPT_V1: str = SYSTEM_PROMPT_V2


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    """Assemble the CONTEXT + QUESTION block that follows the system prompt.

    Chunks are rendered as ``[#N] {content} (Manba: {source_url})`` -- the
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
