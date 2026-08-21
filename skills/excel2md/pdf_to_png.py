"""
Render mỗi sheet Excel có drawing thành PNG để sub-agent đọc bằng vision,
và xuất bản đồ sheet → index → danh sách PNG.

Sheet được render khi drawing của nó chứa shape (<xdr:sp>) hoặc ảnh nhúng
(<xdr:pic>). Ảnh nhúng cũng cần render vì sub-agent phải nhìn layout mới
biết chèn ảnh vào đúng vị trí trong markdown.

Usage:
    python pdf_to_png.py input.xlsx output_dir [--all]

Dependencies:
    pip install pymupdf openpyxl
"""

import io
import json
import os
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
DRAWING_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing"
)

DPI = 150
MAX_EDGE = 1600


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def parse_rels(z: zipfile.ZipFile, rels_path: str) -> dict:
    """Parse a .rels file → {rId: (type, target)}."""
    try:
        data = z.read(rels_path)
    except KeyError:
        return {}
    root = ET.fromstring(data)
    return {
        rel.get("Id"): (rel.get("Type"), rel.get("Target"))
        for rel in root.findall(f"{RELS_NS}Relationship")
    }


def rels_path_for(file_path: str) -> str:
    d = posixpath.dirname(file_path)
    b = posixpath.basename(file_path)
    return f"{d}/_rels/{b}.rels"


def sheet_map(xlsx_path: str) -> list:
    """
    Every sheet in workbook order, hidden included.

    Returns [{"index": int, "name": str, "state": str,
              "has_shape": bool, "has_pic": bool}, ...]
    """
    ns_s = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    ns_r = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

    rows = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        root = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = [
            (s.get("name"), s.get(f"{ns_r}id"), s.get("state") or "visible")
            for s in root.findall(f".//{ns_s}sheet")
        ]
        wb_rels = parse_rels(z, "xl/_rels/workbook.xml.rels")

        for idx, (name, r_id, state) in enumerate(sheets, start=1):
            has_shape = has_pic = False
            entry = wb_rels.get(r_id)
            if entry is not None:
                sheet_path = posixpath.normpath(posixpath.join("xl", entry[1]))
                sheet_rels = parse_rels(z, rels_path_for(sheet_path))
                for _, (rtype, target) in sheet_rels.items():
                    if rtype != DRAWING_REL_TYPE:
                        continue
                    drawing_path = posixpath.normpath(
                        posixpath.join(posixpath.dirname(sheet_path), target)
                    )
                    try:
                        xml = z.read(drawing_path).decode("utf-8", "replace")
                    except KeyError:
                        continue
                    if "<xdr:sp" in xml:
                        has_shape = True
                    if "<xdr:pic" in xml:
                        has_pic = True

            rows.append(
                {
                    "index": idx,
                    "name": name,
                    "state": state,
                    "has_shape": has_shape,
                    "has_pic": has_pic,
                }
            )
    return rows


def render_pdf_pages(pdf_path: str, out_dir: str, prefix: str) -> list:
    """Render every page of pdf_path to PNG. Returns PNG basenames."""
    import fitz

    os.makedirs(out_dir, exist_ok=True)
    names = []
    doc = fitz.open(pdf_path)
    try:
        for page_no, page in enumerate(doc, start=1):
            zoom = DPI / 72.0
            longest = max(page.rect.width, page.rect.height) * zoom
            if longest > MAX_EDGE:
                zoom *= MAX_EDGE / longest
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            name = f"{prefix}_p{page_no:02}.png"
            pix.save(os.path.join(out_dir, name))
            names.append(name)
    finally:
        doc.close()
    return names


def run(xlsx_path: str, output_dir: str, render_all: bool = False) -> list:
    """
    Render PNGs for visible sheets that need them.

    Returns the visible-sheet rows with "render" and "pngs" added.
    """
    rows = [r for r in sheet_map(xlsx_path) if r["state"] == "visible"]

    for row in rows:
        row["render"] = render_all or row["has_shape"] or row["has_pic"]
        row["pngs"] = []

        if not row["render"]:
            continue

        # xlsx_to_pdf.py names each PDF after the sanitized sheet name.
        safe = sanitize_filename(row["name"])
        pdf_path = os.path.join(output_dir, f"{safe}.pdf")
        if not os.path.exists(pdf_path):
            print(f"! '{row['name']}': PDF not found ({safe}.pdf) — skipped")
            continue

        prefix = f"{row['index']:03}_{safe}"
        row["pngs"] = render_pdf_pages(pdf_path, output_dir, prefix)
        print(f"✓ '{row['name']}': {len(row['pngs'])} page(s) rendered")

    return rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    args = [a for a in sys.argv[1:] if a != "--all"]
    if len(args) < 2:
        print("Usage: python pdf_to_png.py <input.xlsx> <output_dir> [--all]")
        sys.exit(1)

    result = run(args[0], args[1], render_all="--all" in sys.argv[1:])

    print("\n=== SHEET MAP (JSON) ===")
    print(json.dumps(result, ensure_ascii=False))
