"""Source-specific corpus scrapers.

Every module here owns one corpus source (lex.uz, soliq.uz, ...). The
package is the ONLY place ``beautifulsoup4`` / ``lxml`` are imported —
R6 forbids adding HTML-parsing helpers anywhere else in the codebase.
"""
