"""
ingestion.py
------------
Responsible for turning a raw PDF file into clean, page-tagged text.

Why page-tagging matters:
    We keep the page number attached to every character of text we pull out.
    Later, when we chunk the text, each chunk inherits the page number(s) it
    came from. That page number is what lets us cite sources like
    "(Source: paper.pdf, page 4)" in the final answer.
"""

from dataclasses import dataclass
from typing import List

try:
    import pymupdf as fitz  # modern PyMuPDF package
except ImportError:  # pragma: no cover
    import fitz  # legacy fallback


@dataclass
class PageText:
    page_number: int  # 1-indexed, human-friendly
    text: str


class PDFIngestor:
    """Extracts text from a PDF, page by page."""

    def __init__(self, min_chars_per_page: int = 20):
        # Pages with fewer than this many characters are treated as
        # near-empty (e.g. a title page, a figure-only page) and skipped.
        self.min_chars_per_page = min_chars_per_page

    def extract(self, pdf_path: str) -> List[PageText]:
        pages: List[PageText] = []
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                raw_text = page.get_text("text")
                cleaned = self._clean(raw_text)
                if len(cleaned) >= self.min_chars_per_page:
                    pages.append(PageText(page_number=i + 1, text=cleaned))
        return pages

    @staticmethod
    def _clean(text: str) -> str:
        # Collapse excessive whitespace/newlines that PDFs commonly produce
        # (e.g. from column layouts, hyphenation, headers/footers).
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]  # drop empty lines
        return "\n".join(lines)
