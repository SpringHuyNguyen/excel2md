#!/usr/bin/env python3
"""
Convert PDF (houganshi / Excel export with diagrams) to Markdown.

Uses pymupdf4llm for extraction (tables as GFM, multi-line cells joined with
<br>, text as paragraphs/headings), then strips repeated page header/footer
noise (company banner, page numbers, workbook filename) that Excel-exported
PDFs repeat on every page.

Header/footer removal only affects STANDALONE lines (outside tables); noise that
pymupdf4llm folded into a table cell is left untouched to avoid breaking tables.

Usage:
    python pdf_to_markdown.py input.pdf
    python pdf_to_markdown.py input.pdf output.md

Dependencies:
    pip install pymupdf4llm
"""

import io
import re
import sys
from pathlib import Path

# Fix Vietnamese characters on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pymupdf4llm


# ── Config ────────────────────────────────────────────────────────────────────

# Short lines only: long lines are real content, never headers/footers.
HEADER_MAX_LEN = 80


def repeat_threshold(n_pages: int) -> int:
    """
    Min pages a standalone short line must repeat on to count as a running
    header/footer. Scales with document length so short sheets (where a footer
    may only stand alone on 2 of 3 pages) still get cleaned, while single-page
    sheets never trigger frequency-based removal.
    """
    if n_pages <= 1:
        return n_pages + 1   # unreachable threshold: no frequency removal
    if n_pages <= 3:
        return 2
    return 3


# ── Header / footer detection ─────────────────────────────────────────────────

# Page numbers like "6/30", "18 / 30".
RE_PAGE_NUM = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")

# A standalone line that is just a workbook filename (running header). The header
# shows the WORKBOOK name, which differs from the per-sheet PDF filename, so we
# match any short standalone line ending in .xlsx rather than a specific stem.
RE_XLSX_LINE = re.compile(r"\.xlsx\s*$", re.IGNORECASE)


def is_table_line(line: str) -> bool:
    """A GFM table row / separator (starts with a pipe)."""
    return line.lstrip().startswith("|")


def is_standalone(line: str) -> bool:
    """Candidate header/footer line: short, non-empty, not a table row."""
    s = line.strip()
    return bool(s) and len(s) <= HEADER_MAX_LEN and not is_table_line(line)


def collect_repeated_lines(pages: list[str]) -> set[str]:
    """
    Return the set of standalone short lines that appear on enough distinct pages
    (see repeat_threshold) — these are running headers/footers (company banners,
    etc.). Counting per-page (not per-occurrence) avoids nuking a line that
    legitimately repeats many times inside one page.
    """
    threshold = repeat_threshold(len(pages))
    page_count: dict[str, int] = {}
    for page in pages:
        seen_here = {
            ln.strip()
            for ln in page.splitlines()
            if is_standalone(ln)
        }
        for s in seen_here:
            page_count[s] = page_count.get(s, 0) + 1
    return {s for s, c in page_count.items() if c >= threshold}


def strip_headers_footers(pages: list[str]) -> str:
    """
    Drop standalone header/footer lines from each page, then join.
    Removed when a line is:
      - a page number (N/M),
      - a standalone line that is just a workbook filename (ends in .xlsx), or
      - a short standalone line repeated across enough pages (see repeat_threshold).
    """
    repeated = collect_repeated_lines(pages)

    def is_noise(line: str) -> bool:
        s = line.strip()
        if not s:
            return False
        if RE_PAGE_NUM.match(s):
            return True
        if not is_standalone(line):
            return False
        if RE_XLSX_LINE.search(s):
            return True
        if s in repeated:
            return True
        return False

    cleaned_pages = []
    for page in pages:
        kept = [ln for ln in page.splitlines() if not is_noise(ln)]
        cleaned_pages.append("\n".join(kept))

    return "\n\n".join(cleaned_pages)


# ── Main conversion ───────────────────────────────────────────────────────────

def convert(pdf_path: Path, md_path: Path) -> None:
    # page_chunks=True → one dict per page, so we can detect per-page repeats.
    # use_ocr=False: these PDFs are LibreOffice exports of Excel sheets, so all
    # text is real (extractable) text, never scanned images. OCR is pure overhead
    # here, and on some sheets RapidOCR crashes with TypeError when a page region
    # yields no text lines (pymupdf4llm/ocr/rapidocr_api.py iterates a None result).
    chunks = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True, use_ocr=False)
    pages = [c["text"] for c in chunks]

    md = strip_headers_footers(pages)

    # Collapse the runs of blank lines left behind by removed noise.
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"

    md_path.write_text(md, encoding="utf-8")
    print(f"Saved: {md_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_markdown.py input.pdf [output.md]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: file not found - {pdf_path}")
        sys.exit(1)

    md_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else pdf_path.with_suffix(".md")
    convert(pdf_path, md_path)


if __name__ == "__main__":
    main()
