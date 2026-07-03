"""lex.uz Uzbek Tax Code scraper.

Fetches, caches, and parses the Latin-script Tax Code page
(``https://lex.uz/uz/docs/-4674902``) into a normalised list of
articles. Every article carries its section (``bolim``), chapter
(``bob``), the ``N-modda`` reference number, its title, and the full
body text.

Structure notes (verified against the live page, 2026-07):

* Top-level content elements share the ``lx_elem`` class. The kind of
  block is encoded by an additional class:

    - ``TEXT_HEADER_DEFAULT`` -- a section (``I BOLIM. ...``), chapter
      (``N-bob. ...``) or top-level rubric (``UMUMIY QISM``).
    - ``CLAUSE_DEFAULT`` -- either the article title line
      (``N-modda. Title``) OR a numbered clause line inside an article.
    - ``ACT_TEXT`` -- a body paragraph inside the currently open article.
    - ``BY_DEFAULT`` -- an inline note; treated as body text.

* The real text of a block lives in an inner ``<div name="..." id="...">``
  child. The outer ``lx_elem`` also contains a "Hujjatga taklif yuborish
  / Audioni tinglash / ..." action bar (inside ``lx_elem3``) which is
  chrome and must be dropped.

* Metadata blocks that must never enter the corpus:

    - ``COMMENT lx_no_select`` -- "Oldingi tahrirga qarang" hyperlinks.
    - ``CHANGES_ORIGINS lx_no_select`` -- revision provenance footnotes.
    - ``INDEXES_ON_REF`` -- cross-reference indexes.
    - ``FOOTNOTE`` -- legislative footnotes.

The parser therefore filters by class list, extracts each block's inner
data ``<div>``, and walks the document in source order so section /
chapter state is preserved as it enters each article.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Canonical URL for the current Latin-script Tax Code page.
TAX_CODE_URL: str = "https://lex.uz/uz/docs/-4674902"

# Stable UA so lex.uz operators can trace research traffic.
_USER_AGENT: str = "TAA-bot/1.0 (research)"
_REQUEST_TIMEOUT_SECONDS: float = 30.0

# lex.uz uses a modifier-letter apostrophe (U+02BB) in Uzbek-Latin
# words; normalise every apostrophe variant to empty for pattern
# matching. Preserved verbatim in the emitted text.
_APOSTROPHE_RE = re.compile("[" + "ʻ" + "‘" + "’" + "ʼ" + "`" + "´" + "'" + "]")

# Header / article recognisers. Anchored to line start so a stray
# "3-modda" occurrence inside prose does NOT open a new article.
_SECTION_RE = re.compile(
    r"^(?:[IVXLC]+\s*BOLIM\.|UMUMIY\s+QISM|MAXSUS\s+QISM)",
    re.IGNORECASE,
)
_CHAPTER_RE = re.compile(r"^\d+-BOB\.", re.IGNORECASE)
_ARTICLE_RE = re.compile(
    r"^(?P<ref>\d+(?:-\d+)?)-MODDA\.\s*(?P<title>.+)$",
    re.IGNORECASE,
)

# Class buckets we walk. Every relevant top-level block carries
# ``lx_elem`` + one of these; ``lx_elem2`` / ``lx_elem3`` share the
# prefix but only wrap the action-bar chrome.
_RELEVANT_CLASSES: frozenset[str] = frozenset(
    {"TEXT_HEADER_DEFAULT", "CLAUSE_DEFAULT", "ACT_TEXT", "BY_DEFAULT"},
)

# Class names we must never enter (metadata / navigation / chrome).
_SKIP_CLASSES: frozenset[str] = frozenset(
    {
        "COMMENT",
        "CHANGES_ORIGINS",
        "INDEXES_ON_REF",
        "FOOTNOTE",
        "lx_no_select",
    },
)


@dataclass
class ParsedArticle:
    """A single Tax Code article, fully normalised for embedding.

    ``section`` and ``chapter`` are kept verbatim (with the original
    Uzbek-Latin apostrophes) so downstream citations render exactly
    what a reader would find on lex.uz. ``paragraphs`` is preserved as
    a list so the chunker can split on paragraph boundaries.
    """

    section: str
    chapter: str
    article_ref: str
    title: str
    content: str
    paragraphs: list[str] = field(default_factory=list)


async def fetch_tax_code_html(cache_path: Path) -> str:
    """Return the raw HTML for the Tax Code page, using ``cache_path`` as a cache.

    If ``cache_path`` exists, its contents are returned unchanged -- this
    makes re-runs of the ingest command free-of-network and lets Eric
    ship the cached HTML around. Otherwise we make one GET request with
    a 30s timeout, store the body under ``cache_path`` (creating parent
    directories if needed) and return it.
    """
    if cache_path.exists():
        logger.info(
            "scrapers.lex_uz.cache_hit",
            extra={"path": str(cache_path), "size": cache_path.stat().st_size},
        )
        return cache_path.read_text(encoding="utf-8")

    logger.info("scrapers.lex_uz.fetch", extra={"url": TAX_CODE_URL})

    def _sync_get() -> str:
        with httpx.Client(
            headers={"User-Agent": _USER_AGENT},
            timeout=_REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            response = client.get(TAX_CODE_URL)
            response.raise_for_status()
            return response.text

    html = await asyncio.to_thread(_sync_get)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")
    logger.info(
        "scrapers.lex_uz.fetch_saved",
        extra={"path": str(cache_path), "size": len(html)},
    )
    return html


def parse_tax_code(html: str) -> list[ParsedArticle]:
    """Parse the lex.uz Tax Code HTML into a list of ``ParsedArticle``.

    Walks the document in source order, tracking section / chapter
    state, and accumulates every ``ACT_TEXT`` / ``BY_DEFAULT`` /
    non-title ``CLAUSE_DEFAULT`` block into the currently open article.
    Blocks encountered before the first article are silently dropped
    (they are the document's title-page rubric).
    """
    soup = BeautifulSoup(html, "lxml")

    section: str = ""
    chapter: str = ""
    current: ParsedArticle | None = None
    articles: list[ParsedArticle] = []
    skipped = 0

    for elem in _iter_content_blocks(soup):
        text = _extract_text(elem)
        if not text:
            continue

        classes = elem.get("class") or []
        normalised = _normalise_for_match(text)

        if "TEXT_HEADER_DEFAULT" in classes:
            if _SECTION_RE.match(normalised):
                section = text
            elif _CHAPTER_RE.match(normalised):
                chapter = text
            else:
                logger.debug(
                    "scrapers.lex_uz.unknown_header",
                    extra={"snippet": text[:80]},
                )
            continue

        match = _ARTICLE_RE.match(normalised)
        if "CLAUSE_DEFAULT" in classes and match:
            if current is not None:
                articles.append(_finalise(current))
            current = ParsedArticle(
                section=section,
                chapter=chapter,
                article_ref=match.group("ref"),
                title=text,
                content="",
            )
            continue

        if current is None:
            # Body text before we have opened any article -- the doc's
            # preamble (promulgation table, etc). Skip cleanly and
            # count so operators can audit the delta.
            skipped += 1
            continue

        current.paragraphs.append(text)

    if current is not None:
        articles.append(_finalise(current))

    logger.info(
        "scrapers.lex_uz.parse_summary",
        extra={"articles": len(articles), "skipped_preamble_blocks": skipped},
    )
    return articles


def chunk_article(article: ParsedArticle, max_chars: int = 1500) -> list[str]:
    """Split an article into embed-able chunks.

    A short article (below ``max_chars``) becomes a single chunk. A
    longer one is split on paragraph boundaries -- never mid-sentence
    -- and every emitted chunk is prefixed with ``[Modda {ref}] `` so
    the marker survives even if the retriever surfaces only the tail
    chunk of a long article.
    """
    prefix = f"[Modda {article.article_ref}] "
    body = _compose_body(article)

    if len(body) + len(prefix) <= max_chars:
        return [f"{prefix}{body}"]

    chunks: list[str] = []
    buffer: list[str] = [article.title] if article.title else []
    length = sum(len(p) for p in buffer) + len(prefix)

    for para in article.paragraphs:
        para_len = len(para) + 2  # +2 for the newline joiner
        if buffer and length + para_len > max_chars:
            chunks.append(f"{prefix}{_join_paragraphs(buffer)}")
            buffer = []
            length = len(prefix)
        buffer.append(para)
        length += para_len

    if buffer:
        chunks.append(f"{prefix}{_join_paragraphs(buffer)}")

    return chunks


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _iter_content_blocks(soup: BeautifulSoup) -> list[Tag]:
    """Return the ordered list of top-level content blocks."""
    blocks: list[Tag] = []
    for tag in soup.find_all("div"):
        if not isinstance(tag, Tag):
            continue
        classes = tag.get("class") or []
        if "lx_elem" not in classes:
            continue
        if not _RELEVANT_CLASSES.intersection(classes):
            continue
        if _SKIP_CLASSES.intersection(classes):
            continue
        blocks.append(tag)
    return blocks


def _extract_text(elem: Tag) -> str:
    """Pull the article text out of a block, dropping action-bar chrome."""
    inner = elem.find("div", attrs={"name": True})
    if isinstance(inner, Tag):
        text = inner.get_text(" ", strip=True)
    else:
        text = elem.get_text(" ", strip=True)
    return _collapse_whitespace(text)


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalise_for_match(text: str) -> str:
    """Uppercase + apostrophe-stripped form used by header / article regex."""
    return _APOSTROPHE_RE.sub("", text).upper()


def _finalise(article: ParsedArticle) -> ParsedArticle:
    """Freeze ``paragraphs`` into ``content`` (string used by chunker + tests)."""
    article.content = _compose_body(article)
    return article


def _compose_body(article: ParsedArticle) -> str:
    """Return title + paragraphs joined by blank lines."""
    parts: list[str] = []
    if article.title:
        parts.append(article.title)
    parts.extend(article.paragraphs)
    return _join_paragraphs(parts)


def _join_paragraphs(paragraphs: list[str]) -> str:
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())
