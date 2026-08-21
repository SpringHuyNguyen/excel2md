"""
Extract embedded images from an Excel workbook, mapped to their source sheets.

Uses zipfile + XML relationships for reliable sheet-to-image mapping.
Output: {SHEET_INDEX:03}_{SANITIZED_SHEET_NAME}_img{N:02}.{ext}

Usage:
    python xlsx_extract_images.py input.xlsx output_dir
"""

import io
import os
import posixpath
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
DRAWING_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing"
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"


def sanitize_filename(name: str) -> str:
    """ASCII-only, space-free name so markdown links need no URL-encoding."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.replace("đ", "d").replace("Đ", "D")
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return re.sub(r"\s+", "_", name).strip("_")


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


def resolve_zip_path(base_dir: str, relative: str) -> str:
    """Resolve a relative path within zip (always posix)."""
    return posixpath.normpath(posixpath.join(base_dir, relative))


def rels_path_for(file_path: str) -> str:
    """Get the .rels path for a given zip entry."""
    d = posixpath.dirname(file_path)
    b = posixpath.basename(file_path)
    return f"{d}/_rels/{b}.rels"


def get_sheet_order(z: zipfile.ZipFile) -> list:
    """Return ordered list of (sheet_name, rId, state) from workbook.xml."""
    root = ET.fromstring(z.read("xl/workbook.xml"))
    ns_s = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ns_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    return [
        (sheet.get("name"), sheet.get(f"{{{ns_r}}}id"), sheet.get("state") or "visible")
        for sheet in root.findall(f".//{{{ns_s}}}sheet")
    ]


def extract_images(xlsx_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    total = 0

    with zipfile.ZipFile(xlsx_path, "r") as z:
        sheets = get_sheet_order(z)
        wb_rels = parse_rels(z, "xl/_rels/workbook.xml.rels")

        for sheet_idx, (sheet_name, r_id, state) in enumerate(sheets, start=1):
            # Skip hidden / veryHidden sheets — the customer hid them on purpose.
            if state != "visible":
                print(f"  '{sheet_name}': skipped (hidden)")
                continue
            entry = wb_rels.get(r_id)
            if entry is None:
                continue
            _, sheet_target = entry

            # Resolve sheet path relative to xl/
            sheet_path = resolve_zip_path("xl", sheet_target)
            sheet_rels = parse_rels(z, rels_path_for(sheet_path))

            # Find drawings referenced by this sheet
            drawing_targets = [
                target
                for _, (rtype, target) in sheet_rels.items()
                if rtype == DRAWING_REL_TYPE
            ]

            safe_name = sanitize_filename(sheet_name)
            prefix = f"{sheet_idx:03}_{safe_name}"
            img_counter = 0

            for dt in drawing_targets:
                drawing_path = resolve_zip_path(
                    posixpath.dirname(sheet_path), dt
                )
                drawing_rels = parse_rels(z, rels_path_for(drawing_path))

                for _, (rtype, img_target) in drawing_rels.items():
                    if rtype != IMAGE_REL_TYPE:
                        continue

                    img_zip_path = resolve_zip_path(
                        posixpath.dirname(drawing_path), img_target
                    )
                    ext = posixpath.splitext(img_zip_path)[1].lstrip(".")

                    img_counter += 1
                    filename = f"{prefix}_img{img_counter:02}.{ext}"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, "wb") as f:
                        f.write(z.read(img_zip_path))

                    print(f"  '{sheet_name}' image {img_counter} -> {filename}")
                    total += 1

    if total == 0:
        print("No images found in workbook.")
    else:
        print(f"\n-> {total} image(s) extracted to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python xlsx_extract_images.py <input.xlsx> <output_dir>")
        sys.exit(1)

    extract_images(sys.argv[1], sys.argv[2])
