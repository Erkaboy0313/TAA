"""Unit tests for ``apps.corpus.scrapers.lex_uz`` (E02 real ingest).

Every test operates on a hand-crafted HTML fixture embedded below --
no real network calls, no cached lex.uz snapshot required to run.
The fixture mirrors the observed lex.uz structure (verified against
the live page 2026-07): ``TEXT_HEADER_DEFAULT`` for section / chapter,
``CLAUSE_DEFAULT`` for the ``N-modda. Title`` line, ``ACT_TEXT`` for
body paragraphs, plus a ``COMMENT lx_no_select`` block that must be
dropped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx

if TYPE_CHECKING:
    from pathlib import Path

from apps.corpus.scrapers.lex_uz import (
    ParsedArticle,
    chunk_article,
    fetch_tax_code_html,
    parse_tax_code,
)

_FIXTURE_HTML = """
<html><body>
<div class="TEXT_HEADER_DEFAULT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="h1" id="h1">I BOʻLIM. UMUMIY QOIDALAR</div>
</div>
<div class="TEXT_HEADER_DEFAULT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="h2" id="h2">1-bob. Asosiy qoidalar</div>
</div>

<div class="CLAUSE_DEFAULT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="a1t" id="a1t">1-modda. Kirish moddasi</div>
</div>
<div class="ACT_TEXT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="a1b" id="a1b">Ushbu Kodeks soliqlarni tartibga soladi.</div>
</div>

<div class="COMMENT lx_no_select">
  <div name="cmt" id="cmt">Oldingi tahrirga qarang.</div>
</div>

<div class="CLAUSE_DEFAULT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="a2t" id="a2t">2-modda. Uzun modda</div>
</div>
<div class="ACT_TEXT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="a2b1" id="a2b1">Birinchi band matni ancha uzun.</div>
</div>
<div class="ACT_TEXT lx_elem">
  <div class="lx_elem2"><div class="lx_elem3">chrome</div></div>
  <div name="a2b2" id="a2b2">Ikkinchi band matni ham juda uzun.</div>
</div>

<div class="CHANGES_ORIGINS lx_no_select">
  <div name="chg" id="chg">Qonun tahririda.</div>
</div>
</body></html>
"""


def _articles() -> list[ParsedArticle]:
    return parse_tax_code(_FIXTURE_HTML)


def test_parse_tax_code_finds_all_articles() -> None:
    articles = _articles()

    assert [a.article_ref for a in articles] == ["1", "2"]
    assert articles[0].title == "1-modda. Kirish moddasi"
    assert articles[1].title == "2-modda. Uzun modda"


def test_parse_tax_code_propagates_section_and_chapter_state() -> None:
    articles = _articles()

    for article in articles:
        assert article.section.startswith("I BO")
        assert article.chapter == "1-bob. Asosiy qoidalar"


def test_parse_tax_code_skips_comment_and_changes_blocks() -> None:
    articles = _articles()

    combined = "\n".join(a.content for a in articles)
    assert "Oldingi tahrirga qarang" not in combined
    assert "Qonun tahririda" not in combined


def test_chunk_article_short_article_returns_single_prefixed_chunk() -> None:
    article = _articles()[0]

    chunks = chunk_article(article, max_chars=1500)

    assert len(chunks) == 1
    assert chunks[0].startswith("[Modda 1] ")
    assert "Kirish moddasi" in chunks[0]


def test_chunk_article_long_article_splits_on_paragraph_boundary() -> None:
    # A fabricated multi-paragraph article whose combined length
    # exceeds the chunk budget so we exercise the paragraph splitter.
    long_para = "Sentence. " * 40  # ~400 chars per paragraph
    article = ParsedArticle(
        section="X",
        chapter="Y",
        article_ref="42",
        title="42-modda. Uzun modda",
        content="",
        paragraphs=[long_para, long_para, long_para, long_para, long_para],
    )

    chunks = chunk_article(article, max_chars=600)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.startswith("[Modda 42] ")


async def test_fetch_tax_code_html_uses_cache_when_file_exists(tmp_path: Path) -> None:
    cache = tmp_path / "cached.html"
    cache.write_text("<html>cached</html>", encoding="utf-8")

    # If we DID touch the network, httpx.Client would blow up here.
    def _boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network was called despite cache hit")

    with patch.object(httpx, "Client", side_effect=_boom):
        html = await fetch_tax_code_html(cache)

    assert html == "<html>cached</html>"
