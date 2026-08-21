import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

import pdf_to_png  # noqa: E402

SAMPLE = Path(
    r"D:\claude-code\226-vi\BD_266_製造指図 購買発注の日付を合わせる_v1.09_VN.xlsx"
)
needs_sample = pytest.mark.skipif(
    not SAMPLE.exists(), reason="sample workbook not available"
)


@needs_sample
def test_sheet_map_lists_all_sheets_in_workbook_order():
    rows = pdf_to_png.sheet_map(str(SAMPLE))

    assert len(rows) == 19
    assert rows[0]["index"] == 1
    assert rows[0]["name"] == "Cover"
    assert rows[6]["index"] == 7
    assert rows[6]["name"] == "2. ☆Sơ đồ chuyển MH"


@needs_sample
def test_sheet_map_reports_hidden_state():
    rows = pdf_to_png.sheet_map(str(SAMPLE))

    assert rows[3]["name"] == "運用要件"
    assert rows[3]["state"] == "hidden"
    assert rows[18]["state"] == "hidden"
    assert rows[1]["state"] == "visible"


@needs_sample
def test_detects_shapes():
    rows = {r["name"]: r for r in pdf_to_png.sheet_map(str(SAMPLE))}

    assert rows["Cover"]["has_shape"] is True
    assert rows["Lịch sử chỉnh sửa"]["has_shape"] is False
    assert rows["Bản định nghĩa Table"]["has_shape"] is False


@needs_sample
def test_detects_embedded_pictures():
    rows = {r["name"]: r for r in pdf_to_png.sheet_map(str(SAMPLE))}

    assert rows["Định nghĩa yêu cầu_production o"]["has_pic"] is True
    assert rows["Cover"]["has_pic"] is False
    assert rows["For Developer①"]["has_pic"] is False


def test_workbook_without_drawings(tmp_path):
    src = tmp_path / "plain.xlsx"
    wb = Workbook()
    wb.active.title = "Trống"
    wb.active["A1"] = "không có hình"
    wb.save(src)

    rows = pdf_to_png.sheet_map(str(src))

    assert len(rows) == 1
    assert rows[0]["has_shape"] is False
    assert rows[0]["has_pic"] is False


import fitz  # noqa: E402


def _make_pdf(path: Path, pages: int = 2) -> None:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)  # A4 @72dpi
        page.insert_text((72, 72), f"trang {i + 1}")
    doc.save(str(path))
    doc.close()


def test_render_pdf_pages_makes_one_png_per_page(tmp_path):
    pdf = tmp_path / "s.pdf"
    _make_pdf(pdf, pages=3)

    names = pdf_to_png.render_pdf_pages(str(pdf), str(tmp_path), "007_Sheet")

    assert names == ["007_Sheet_p01.png", "007_Sheet_p02.png", "007_Sheet_p03.png"]
    for n in names:
        assert (tmp_path / n).exists()


def test_render_clamps_long_edge_to_max(tmp_path):
    pdf = tmp_path / "big.pdf"
    doc = fitz.open()
    doc.new_page(width=595, height=3000)  # rất dài
    doc.save(str(pdf))
    doc.close()

    names = pdf_to_png.render_pdf_pages(str(pdf), str(tmp_path), "001_Big")

    pix = fitz.Pixmap(str(tmp_path / names[0]))
    assert max(pix.width, pix.height) <= pdf_to_png.MAX_EDGE


def test_a4_page_is_clamped_to_max_edge(tmp_path):
    pdf = tmp_path / "a4.pdf"
    _make_pdf(pdf, pages=1)

    names = pdf_to_png.render_pdf_pages(str(pdf), str(tmp_path), "001_A4")

    pix = fitz.Pixmap(str(tmp_path / names[0]))
    # A4 842pt @150dpi ≈ 1754px > 1600 → bị clamp về đúng 1600
    assert max(pix.width, pix.height) == pdf_to_png.MAX_EDGE


@needs_sample
def test_run_renders_only_sheets_with_drawings(tmp_path):
    # PDF giả cho 2 sheet, đặt tên đúng như xlsx_to_pdf.py sinh ra
    _make_pdf(tmp_path / "Cover.pdf", pages=1)
    _make_pdf(tmp_path / "Lịch sử chỉnh sửa.pdf", pages=1)

    rows = pdf_to_png.run(str(SAMPLE), str(tmp_path))
    by_name = {r["name"]: r for r in rows}

    assert by_name["Cover"]["render"] is True
    assert by_name["Cover"]["pngs"] == ["001_Cover_p01.png"]
    assert by_name["Lịch sử chỉnh sửa"]["render"] is False
    assert by_name["Lịch sử chỉnh sửa"]["pngs"] == []


@needs_sample
def test_run_excludes_hidden_sheets(tmp_path):
    rows = pdf_to_png.run(str(SAMPLE), str(tmp_path))

    assert len(rows) == 17
    assert all(r["state"] == "visible" for r in rows)
    assert [r["index"] for r in rows][:5] == [1, 2, 3, 5, 6]


@needs_sample
def test_run_all_flag_marks_every_visible_sheet(tmp_path):
    rows = pdf_to_png.run(str(SAMPLE), str(tmp_path), render_all=True)

    assert all(r["render"] for r in rows)


@needs_sample
def test_run_tolerates_missing_pdf(tmp_path):
    """Sheet cần render nhưng không có PDF → cảnh báo, không crash."""
    rows = pdf_to_png.run(str(SAMPLE), str(tmp_path))
    by_name = {r["name"]: r for r in rows}

    assert by_name["Cover"]["render"] is True
    assert by_name["Cover"]["pngs"] == []
