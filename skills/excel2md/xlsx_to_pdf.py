"""
Convert xlsx to multiple PDFs, one per sheet, using LibreOffice + pypdf outline.

Usage:
    python xlsx_to_pdf.py input.xlsx output_dir
"""
import io
import os
import re
import shutil
import subprocess
import sys

# Fix Vietnamese characters on Windows console. Guarded because these modules
# import one another: wrapping an already-wrapped stdout drops the first
# wrapper, and collecting it closes the buffer both were writing to.
if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pypdf import PdfReader, PdfWriter

# Where LibreOffice usually lands, per platform. Only used as a last resort,
# after the EXCEL2MD_SOFFICE override and a PATH lookup.
DEFAULT_SOFFICE_PATHS = {
    "win32": [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ],
    "darwin": [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ],
}
DEFAULT_SOFFICE_PATHS_OTHER = [
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/snap/bin/libreoffice",
]

INSTALL_HINT = (
    "LibreOffice not found. Install it from https://www.libreoffice.org/download/, "
    "or point EXCEL2MD_SOFFICE at the soffice executable, e.g.\n"
    '  Windows  set EXCEL2MD_SOFFICE=C:\\Program Files\\LibreOffice\\program\\soffice.exe\n'
    "  macOS    export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice\n"
    "  Linux    export EXCEL2MD_SOFFICE=/usr/bin/soffice"
)


def find_soffice() -> str:
    """Locate the LibreOffice executable, or exit with an actionable message."""
    override = os.environ.get("EXCEL2MD_SOFFICE")
    if override:
        if os.path.isfile(override):
            return override
        print(f"ERROR: EXCEL2MD_SOFFICE points at {override}, which is not a file.")
        sys.exit(1)

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found

    candidates = DEFAULT_SOFFICE_PATHS.get(sys.platform, DEFAULT_SOFFICE_PATHS_OTHER)
    for path in candidates:
        if os.path.isfile(path):
            return path

    print(f"ERROR: {INSTALL_HINT}")
    sys.exit(1)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def xlsx_to_pdf(input_path: str, output_dir: str) -> str:
    """Convert xlsx to a single PDF using LibreOffice."""
    soffice = find_soffice()
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", input_path, "--outdir", output_dir],
        check=True,
        capture_output=True,
    )
    basename = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(output_dir, f"{basename}.pdf")


def split_pdf_by_outline(pdf_path: str, output_dir: str) -> list[str]:
    """Split PDF into multiple files based on top-level outline (bookmarks)."""
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    if not reader.outline:
        print("No outline found. Outputting single PDF.")
        return [pdf_path]

    # Collect top-level outline entries only
    outline_entries = []
    for item in reader.outline:
        if isinstance(item, list):
            continue  # skip nested
        page_num = reader.get_destination_page_number(item)
        outline_entries.append((item.title, page_num))

    print(f"Found {len(outline_entries)} outline entries:")
    for title, page in outline_entries:
        print(f"  [{page}] {title}")

    # Split pages between outline entries
    output_pdfs = []
    for i, (title, start_page) in enumerate(outline_entries):
        end_page = outline_entries[i + 1][1] if i + 1 < len(outline_entries) else total_pages

        writer = PdfWriter()
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])

        safe_name = sanitize_filename(title)
        out_path = os.path.join(output_dir, f"{safe_name}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        print(f"✓ '{title}' (pages {start_page}-{end_page - 1}) → {out_path}")
        output_pdfs.append(out_path)

    return output_pdfs


def convert(input_path: str, output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    print(f"Converting {input_path} ...")
    pdf_path = xlsx_to_pdf(input_path, output_dir)
    print(f"PDF created: {pdf_path}")
    return split_pdf_by_outline(pdf_path, output_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python xlsx_to_pdf.py <input.xlsx> <output_dir>")
        sys.exit(1)

    results = convert(sys.argv[1], sys.argv[2])
    print(f"\nDone. {len(results)} file(s) created.")
