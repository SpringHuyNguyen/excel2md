---
name: excel2md
description: Use when the user types /excel2md --file <filepath.xlsx> (with optional [output_folder_name] [-vision-all] [-test]), or asks to convert a local Excel design document — written in Japanese, Vietnamese, English or any mix of the three — to markdown. Sub-agents read rendered sheet images to rebuild shape-based diagrams and place embedded pictures.
---

# excel2md

## Purpose

Convert an Excel design document — written in Japanese, Vietnamese, English or any mix of the three — into Markdown. The workbook is extracted into per-sheet PDFs, per-sheet text files, per-sheet PNG images, and extracted embedded images; sub-agents then combine those sources into one Markdown file per sheet.

## Trigger

`/excel2md --file <filepath.xlsx> [output_folder_name] [-vision-all] [-test]`. The workbook must be a local `.xlsx` file; `--file` is required.

`-vision-all` and `-test` are optional standalone flags at the end of the command, in any order:

- `-vision-all`: render a PNG for EVERY sheet instead of only sheets that contain drawings.
- `-test`: keep ALL intermediate folders. Without it, only the final Markdown files and the `images/` folder are kept.

## Source hierarchy — read this before anything else

The PDF branch of this pipeline is **not trustworthy for characters**. LibreOffice emits Vietnamese tone marks as separate glyphs with their own coordinates, so `Lịch sử chỉnh sửa` comes out of the PDF as `L ch sị ử ch nh sỉ ửa`; it also drops characters where a mixed Japanese/Vietnamese font falls back, and reorders text. Japanese usually survives intact — but this pipeline does not rely on "usually". The rule below applies to every language, unconditionally.

Therefore the sources have strictly separated roles:

| Source                     | Authority over                                                       | Never use for                                                       |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `normal_{IDX}_{SHEET}.txt` | Every character in the output                                        | —                                                                   |
| Rendered PNG               | Table structure, merges, diagrams, image placement, displayed values | Characters, except diagram shape labels (see Visual Source, item 1) |
| `raw md` (from PDF)        | Rough table framing only                                             | Characters                                                          |
| `strike_{IDX}_{SHEET}.txt` | Text to delete from the output                                       | —                                                                   |

**Every character in the final Markdown is copied from `normal_*.txt`, with one exception: diagram shape labels, which never reach `normal_*.txt` and may be read from the image under the rules in the Visual Source section.** For everything else, images and `raw md` decide _structure_, never _characters_.

## Workflow

0. **Preflight — check dependencies, install the Python ones if needed**:
   Set `SKILL_DIR` to the absolute path of this skill's directory first. When the skill is installed as a plugin, that is `${CLAUDE_PLUGIN_ROOT}/skills/excel2md`.

    ```bash
    python "<SKILL_DIR>\preflight.py"
    ```

    Branch on the exit code:
    - **0** — everything is present. Continue to Step 1. Say nothing about preflight in the final report.
    - **2** — Python packages are missing, and this is fixable. Tell the user which packages are missing and that you are installing them, then run the exact command preflight printed:

        ```bash
        "<PYTHON_EXE>" -m pip install -r "<SKILL_DIR>\requirements.txt"
        ```

        `<PYTHON_EXE>` is the interpreter path preflight printed on its first line — use that one, never a bare `python`, because the user may have several Pythons installed. Re-run `preflight.py` afterwards and continue only if it now exits 0.
    - **3** — LibreOffice is missing. Handle it as described under _Installing LibreOffice_ below. Never run the pipeline without it.
    - **4** — Python is too old. Show what preflight printed and STOP.

    **If the `pip install` itself fails**, do not retry it and do not continue to Step 1. Report to the user, in this order:
    1. the exact command that failed;
    2. the last ~15 lines of pip's actual output, verbatim — not a paraphrase;
    3. the interpreter path from preflight's first line, so they can see which Python was targeted;
    4. the most likely cause, chosen from what the output actually says:
        - `Permission denied` / `Could not install packages due to an OSError` → the interpreter is in a system location. Suggest re-running with `--user`, or using a virtual environment.
        - network or TLS errors, `Could not find a version` → no index access. Suggest checking the connection, a proxy, or a corporate index.
        - `externally-managed-environment` → a Linux distro Python. Suggest a virtual environment.
        - build or wheel errors on `pymupdf` → no prebuilt wheel for this platform/Python. Suggest a supported Python version.
    5. the manual fallback so they are never stuck:

        ```bash
        "<PYTHON_EXE>" -m pip install -r "<SKILL_DIR>\requirements.txt"
        ```

    Then STOP. Never guess whether the pipeline might work anyway.

    **Installing LibreOffice (exit code 3).** Unlike the Python packages, this is a system-wide install of roughly 350 MB that needs administrator rights, so ASK before running it — do not install it unprompted.

    - If preflight printed a line starting `SUGGESTED_INSTALL: `, take the rest of that line as the command. Tell the user what it will do — the package manager it uses, the ~350 MB size, and that it will prompt for administrator rights — then ask whether to run it. On a yes, run exactly that command. On a no, show the manual download link preflight printed and STOP.
    - If preflight printed no `SUGGESTED_INSTALL:` line, there is no package manager to use. Show the manual instructions preflight printed and STOP.

    After the install command finishes, re-run `preflight.py` as a NEW process. It re-detects LibreOffice at its default location, so a `PATH` that has not refreshed in the current shell does not matter. Continue only if it now exits 0.

    Then put LibreOffice on the user's `PATH`, so `soffice` works in their own terminals too:

    ```bash
    python "<SKILL_DIR>\add_to_path.py"
    ```

    This writes only to the current user's environment, never the machine's, so it needs no administrator rights. It is a convenience, not a requirement — the pipeline finds LibreOffice without it. Report the one line it prints. If it fails, say so and carry on to Step 1 anyway; a `PATH` that was not updated does not stop the conversion.

    **If the install command fails**, apply the same reporting discipline as for pip — command, verbatim output, likely cause, manual fallback, then STOP. The causes worth naming here:
    - the command hangs, or fails with an elevation or `0x800...` error → the administrator prompt could not be answered from this shell. Ask the user to run the command themselves in an elevated terminal, then re-run the skill.
    - `No package found matching input criteria` → the package manager's source index is stale. Suggest `winget source update` (or the equivalent) or the manual download.
    - preflight still exits 3 after a successful install → LibreOffice landed somewhere non-standard. Ask the user to set `EXCEL2MD_SOFFICE` to the `soffice` path.

1. **Resolve Paths & Variables**:
    - The command MUST contain `--file <path>`. If it is missing, report `provide --file <path.xlsx>` and STOP. If the path does not exist or is not an `.xlsx` file, report that and STOP.
    - Strip the standalone flags from the end of the argument list: if `-vision-all` is present set `VISION_ALL=true`, if `-test` is present set `KEEP_ALL=true`. Remove both before parsing `output_folder_name`. They are NOT part of the folder name.
    - `SKILL_DIR` is already set from Step 0.
    - Determine `OUTPUT_DIR`: the `output_folder_name` argument, as `./<output_folder_name>` in the current working directory, created if needed.

        **When `output_folder_name` is absent, ASK the user where to put the results before going any further.** Use the `AskUserQuestion` tool. A conversion writes one Markdown file per sheet plus an `images/` folder, so landing that in whatever directory the user happens to be in — often the root of a repository — leaves a mess they then have to clean up by hand. Offer:
        - a new folder named after the workbook, sanitised the same way the scripts sanitise sheet names — recommend this one;
        - the current working directory, for when they really do want the files loose where they are.

        The user can always type a different name instead. Whatever comes back becomes `output_folder_name`; create the folder if it does not exist. Do not skip this question and do not guess — the answer decides where every file in this run ends up.
    - Set `EXCEL_FILE` to the `--file` value.
    - Set `EXCEL_BASENAME` to the Excel filename without extension.

2. **Generate PDFs per Sheet**:

    ```bash
    python "<SKILL_DIR>\xlsx_to_pdf.py" "<EXCEL_FILE>" "<OUTPUT_DIR>"
    ```

    One PDF per visible sheet, named after the sanitized sheet name.

3. **Extract Text per Sheet**:

    ```bash
    python "<SKILL_DIR>\xlsx_extract_text.py" "<EXCEL_FILE>" "<OUTPUT_DIR>"
    ```

    Writes `normal_{IDX:03}_{SHEET}.txt` and `strike_{IDX:03}_{SHEET}.txt` per visible sheet. Text is read straight from the workbook, so every character is exact in every language — Vietnamese diacritics, Japanese kanji and kana alike — and formulas appear as their computed values.

4. **Extract PDF to MD**:
   For each PDF:

    ```bash
    python "<SKILL_DIR>\pdf_to_markdown.py" "<PDF_FILE>" "<OUTPUT_DIR>\raw_<SHEET_NAME>.md"
    ```

    _The SECOND argument is an output `.md` FILE path, not a directory. Prefix the filename with `raw_` so these intermediates are easy to tell apart from the final files during cleanup. Build `<SHEET_NAME>` from the PDF file's own basename rather than from the raw sheet name: `xlsx_to_pdf.py` already replaced every `\ / _ ? : " < > |`with`_`when it named the PDF, so reusing that basename keeps the two in step and never produces a path Windows rejects.*
*If the command fails for a sheet, continue without a`raw__.md` file for that sheet — dispatch its sub-agent anyway, telling it the rough table frame is unavailable so it relies on the per-sheet text file plus the rendered PNG for structure._

5. **Render Sheet Images**:

    ```bash
    python "<SKILL_DIR>\pdf_to_png.py" "<EXCEL_FILE>" "<OUTPUT_DIR>"
    ```

    Add `--all` when `VISION_ALL=true`. Renders `{IDX:03}_{SHEET}_p{N:02}.png` for every visible sheet whose drawings contain a shape or an embedded picture.

    The command ends with a line `=== SHEET MAP (JSON) ===` followed by a JSON array. **Parse that array — it is the authoritative source for each sheet's index and PNG list.** Each element is `{"index", "name", "state", "has_shape", "has_pic", "render", "pngs"}`. Sheet indexes count hidden sheets, so they may skip numbers.

6. **Extract Embedded Images**:

    ```bash
    python "<SKILL_DIR>\xlsx_extract_images.py" "<EXCEL_FILE>" "<OUTPUT_DIR>\images"
    ```

    Writes `{IDX:03}_{SHEET}_img{N:02}.{ext}`. Match a sheet's images by the `{IDX:03}` prefix of the filename, not the sheet-name portion (sanitisation can make the `{SHEET}` portion differ from the JSON sheet map's raw name). If the workbook has no embedded images the folder stays empty — delete it at Step 8 in that case.

7. **Invoke Sub-agents for Each Sheet**:
   Dispatch one sub-agent per entry in the Step 5 JSON array, using the `Task` tool with `subagent_type: general-purpose`. Issue multiple `Task` calls in a single message to run them in parallel.
   _CRITICAL: exactly one sub-agent per visible sheet. If the array has N entries, dispatch N sub-agents._

    **Subagent Configuration:**
    - **subagent_type**: `general-purpose`
    - **model**: `haiku`
    - **description**: `Markdown Generator {SHEET_INDEX}`
    - **prompt**:

        ````text
        Objective: Generate a complete, beautifully formatted Markdown document for the Excel sheet "{SHEET_NAME}" (sheet index {SHEET_INDEX}) of the workbook "{EXCEL_BASENAME}".

        --- Sources ---
        - "{normal_txt_path}": the sheet's text, read straight from Excel. This is the
          AUTHORITY on characters. Every character you output must be copied from here.
        - "{raw_md_file_path}": a rough table frame built from a PDF export. Use it only
          to learn row/column boundaries. THE TEXT IN THIS FILE IS CORRUPTED — Vietnamese
          diacritics are split into separate glyphs, characters drop out where a mixed
          Japanese/Vietnamese font falls back, and runs are reordered. This applies to
          EVERY language, Japanese included: never copy characters from it. If this path is absent, the PDF
          extraction failed for this sheet — there is no rough table frame. Rely on
          "{normal_txt_path}" plus the rendered PNG(s) for structure instead.
        - "{png_paths}": rendered images of this sheet (may be empty). Use them for
          structure, diagrams, image placement, and displayed values of formula cells.
          Never copy characters from an image.
        - "{strike_txt_path}": struck-through text. Remove every match from your output.

        Read every source with the Read tool before writing anything.

        --- Visual Source ---
        (Include this section only when {png_paths} is non-empty.)
        Read EACH image in {png_paths} with the Read tool before generating markdown.

        1. Diagram: if an image contains a diagram drawn with shapes (boxes joined by
           arrows), rebuild it as a mermaid `flowchart` or `sequenceDiagram`.
           - Node labels: shape text is NOT in "{normal_txt_path}" — that file holds
             cell values only, and drawing/shape text never reaches it. Read node
             labels from the image. If a label's text also appears as a cell value in
             "{normal_txt_path}", use that file's spelling instead of what you read
             from the image. When a label exists only in the image, transcribe it with
             particular care — Vietnamese diacritics and Japanese kanji are both easy to
             misread from a rendered image — and add a short note below
             the diagram that its labels were read from the image.
           - Edges: draw only arrows you can CLEARLY see. Keep an arrow's label when it
             has one (`A -->|label| B`).
           - Do not infer a relationship from proximity when there is no arrow.
           - If you cannot tell where an arrow goes, leave it out and note it below the
             diagram.
           - If the image has no diagram, do not emit mermaid.
        2. Table structure: when "{raw_md_file_path}" clearly contradicts the image (a
           table split in two, shifted columns, wrong merges), follow the structure you
           see in the image. Fix STRUCTURE only — characters still come from
           "{normal_txt_path}".
        3. Embedded images: {embedded_images}
           Use the rendered image to find where each embedded picture sits in the sheet,
           then insert `![short description](./images/xxx.png)` at that point in the
           markdown. Copy the file name VERBATIM from the list above — never rebuild it
           from the sheet name. Every image in the list MUST appear in the output.

        (When {png_paths} is empty, use "{normal_txt_path}" for characters and
        "{raw_md_file_path}" for structure. There is no visual source for this sheet.)

        --- Language ---
        - Content taken from the sources: keep it VERBATIM. Japanese stays Japanese,
          Vietnamese stays Vietnamese with its diacritics intact, English terms stay
          English. Do not translate and do not normalise, whichever language the
          workbook is in.
        - Headings, table column labels, and status labels that YOU generate: write them
          in English. For example `## Overview`, `| Field Name | Data Type | Description |`.
          This matches the English frontmatter schema that every file in `references/`
          already prescribes.
        - Never add diacritics to unaccented Vietnamese, and never strip diacritics.

        --- Context Detection ---
        File Type Detection from the workbook name "{EXCEL_BASENAME}":
        - Detailed Design: contains "詳細設計", "内部設計", "DD", "Detailed Design",
          "Tech Spec", "Thiết kế chi tiết", "TKCT".
        - Basic Design: contains "概要設計書", "基本設計", "BD", "Basic Design",
          "Thiết kế tổng thể", "Thiết kế sơ bộ", "TKTT".

        --- Sheet Name Normalisation ---
        Before matching the rules below, normalise "{SHEET_NAME}":
        lowercase → drop a leading sequence number ("2. ", "01_") → drop decorative
        symbols (☆ ★ ● ◆) → drop Vietnamese diacritics → collapse whitespace.
        Normalise each rule keyword the same way, then compare. This makes
        "Định nghĩa bảng", "Dinh nghia bang" and "DinhNghiaBang" all match one rule.
        The diacritic and decorative-symbol steps leave Japanese and English sheet names
        unchanged, so apply this normalisation to every workbook regardless of language.

        Common Vietnamese abbreviations to expand while matching:
        MH = màn hình, ĐN = định nghĩa, TKCT = thiết kế chi tiết, TKTT = thiết kế tổng thể.

        --- Dynamic Formatting Rules based on Sheet Name ({SHEET_NAME}) ---
        Apply the FIRST matching rule, evaluated top-to-bottom. The Default Fallback in
        Rule G applies only when nothing else matches. When a rule points to a reference
        file, you MUST read that file with the Read tool BEFORE generating output, and
        apply it exactly. This inline rule list is the authoritative source for routing;
        the "Sheet name keywords" lists inside reference files are informational only
        and do not participate in matching.

        [Rule A] General & Admin
        - Cover (表紙, Cover, Bìa, Trang bìa, Thông tin tài liệu):
          "{SKILL_DIR}/references/rule-cover.md".
        - History (変更履歴, 履歴, Change History, History, Revision History, Lịch sử,
          Lịch sử thay đổi, Lịch sử chỉnh sửa):
          "{SKILL_DIR}/references/rule-history.md".

        [Rule B] Database Tables & DDIC
        - Table Definition (テーブル定義, テーブル, Table, Table Definition, DB, Schema,
          Định nghĩa bảng, Bản định nghĩa Table, Thiết kế bảng, Cấu trúc bảng):
          "{SKILL_DIR}/references/rule-table-def.md".

        [Rule C] Flowcharts & Architecture
        - Screen Transition (画面遷移図, 画面遷移, Screen Transition, Navigation,
          Screen Flow, Sơ đồ màn hình, Sơ đồ chuyển MH, Chuyển màn hình, Luồng màn hình,
          Điều hướng): "{SKILL_DIR}/references/rule-screen-transition.md".
        - Other flows (フロー, Flowchart, Architecture, Luồng xử lý, Luồng dữ liệu,
          Luồng nghiệp vụ, Quy trình, Sơ đồ, Kiến trúc, Process Flow, Data Flow):
          - DO NOT just dump plain text.
          - Analyse the step-by-step logic and output a `mermaid` diagram
            (`flowchart TD` or `sequenceDiagram`) representing the program or data flow.
          - Follow the diagram with a structured bulleted list explaining the steps.

        [Rule D] Data Modeling & Business Logic
        - Keywords: "CDS", "CDS View", "ビュー" (View), "ビヘイビア" (Behavior/BDEF), "クラス" (Class)
        - BO Interface (BOインターフェース, BOインターフェース仕様, BO Interface,
          BO Interface Specification, Giao diện BO):
          "{SKILL_DIR}/references/rule-bo-interface.md".
        - Class (クラス, Class): "{SKILL_DIR}/references/rule-class.md".
        - Other data modeling (CDS, View, Behavior):
          - Use `###`/`####` headings to break down Methods, Actions, Validations,
            Determinations.
          - Wrap detailed logic, formulas or pseudo-code in ```abap ... ``` blocks.
          - For CDS: explicitly list Data Sources, Associations, Compositions.

        [Rule E] OData, UI, Field Specs & Metadata
        - Keywords: "サービス", "メタデータ", "UI", "Fiori", "アプリ", "Giao diện"
          (Note: Item Specification is Rule H, not here.)
        - Screen Specification (画面仕様, Screen Spec, Screen Specification, UI Spec,
          Spec màn hình, Đặc tả màn hình, Thiết kế màn hình):
          "{SKILL_DIR}/references/rule-screen-spec.md".
        - Other UI/Metadata specs:
          - Metadata: a mapping table `| Field Name | UI Annotation | Position |`.
          - UI Specs: headings per screen area (`### Filter Bar`, `### List Report Table`,
            `### Object Page`); represent layouts with bullets or blockquotes.

        [Rule F] Cross-cutting
        - Translation (翻訳, 翻訳内容, 画内内容, Translation, i18n, Localization,
          Nội dung dịch, Bản dịch, Dịch thuật, Đa ngôn ngữ — any language pair):
          "{SKILL_DIR}/references/rule-translation.md".
        - Messages-only sheet (メッセージ, Message, Thông báo, Mã lỗi): strict Markdown
          table `| Message Class | Msg No. | Msg Type (E/W/I/S) | Text |`.

        [Rule H] Item Specification
        - Item Spec (項目仕様, 項目情報, Item Spec, Item Specification, Field Spec,
          Spec item, Đặc tả trường, Danh sách trường, Chi tiết item):
          "{SKILL_DIR}/references/rule-item-spec.md".

        [Rule I] DataSpider Setting
        - DataSpider (DataSpider設定, DataSpider, DataSpider Setting,
          Cấu hình DataSpider): "{SKILL_DIR}/references/rule-dataspider.md".

        [Rule G] Requirements & Default Fallback
        - Requirements (要件定義, 要求機能, 要求仕様, 運用要件, Requirements, Yêu cầu,
          Định nghĩa yêu cầu, Đặc tả yêu cầu, Yêu cầu nghiệp vụ, Yêu cầu vận hành):
          "{SKILL_DIR}/references/rule-requirements.md".
        - Default Fallback: synthesize the text and tables cleanly into standard GitHub
          Flavored Markdown, preserving all text explanations and structured lists.

        --- Processing Constraints ---
        1. Remove every text matching "{strike_txt_path}" from the final output.
        2. If "{normal_txt_path}" is empty, emit a minimal document with just the sheet
           heading. Do not fail.
        3. Save the output using ONLY the `Write` tool, to this exact absolute path:
           "{output_md_path}"
           Do NOT use `Bash` for writing the output, and do NOT write it anywhere else —
           the path is absolute and already includes the correct folder and filename.
        ````

    _Replace `{normal_txt_path}`, `{strike_txt_path}`, `{raw_md_file_path}`, `{png_paths}`, `{embedded_images}`, `{SHEET_INDEX}`, `{SHEET_NAME}`, `{EXCEL_BASENAME}`, `{SKILL_DIR}`, `{output_md_path}` with actual absolute paths and values before invoking. Take `{SHEET_INDEX}` and `{png_paths}` from the Step 5 JSON array — do not compute indexes yourself, and substitute `{SHEET_INDEX}` already zero-padded to 3 digits (e.g. `007`). `{embedded_images}` is the list of `images/...` files whose `{IDX:03}` prefix matches this sheet's zero-padded index (not the sheet-name portion, which may be sanitised differently from the JSON sheet map's raw name); pass an empty list when there are none. `{output_md_path}` is the absolute path `<OUTPUT_DIR>\{SHEET_INDEX}_{EXCEL_BASENAME}_{SHEET_NAME}.md`, with `{SHEET_INDEX}` zero-padded to 3 digits and the sheet-name portion sanitised exactly the way the scripts sanitise it — every `\ / _ ? : " < > |`replaced by`\_`— because the JSON sheet map carries the RAW sheet name and Windows rejects those characters in a filename. Sanitise the FILENAME only: the`{SHEET_NAME}` you substitute into the prompt body stays raw, so the sub-agent still sees the sheet's real title. Resolve the path fully before dispatching, so the sub-agent never has to infer its working directory.\*

8. **Organize Files**:
   Branch on `KEEP_ALL`, using the `Bash` tool. The `images/` folder is real output, not an intermediate.

    **If `KEEP_ALL=true` (`-test` given)** — keep everything:
    - `raw_pdf/`: all intermediate `.pdf` files.
    - `raw_md/`: all `raw_*.md` files from Step 4.
    - `png/`: all `.png` files from Step 5 sitting directly in `OUTPUT_DIR` (not inside `images/` — never move or touch `images/` contents here).
    - `text/`: all `normal_*.txt` and `strike_*.txt` files.
    - `images/`: leave in place.
    - `final_md/`: the sub-agent outputs, plus a **copy** of `images/` as `final_md/images/` so the relative links resolve.

    **If `KEEP_ALL=false` (default)** — keep only the final Markdown files, flat in `OUTPUT_DIR`, plus `images/`. Do NOT create subfolders. Delete from `OUTPUT_DIR`:
    - all `.pdf` files;
    - all `raw_*.md` files from Step 4;
    - all `.png` files from Step 5 sitting directly in `OUTPUT_DIR` (not inside `images/` — never delete `images/` contents here);
    - all `normal_*.txt` and `strike_*.txt` files;
    - `images/` itself, only if it is empty.

    _The intermediates share the `.md` extension with the final files, so never blanket-delete `*.md`. The `raw_` prefix from Step 4 is what makes them safe to target._
    _NEVER delete the user's source `.xlsx` — it is their own file and normally lives outside `OUTPUT_DIR`._

9. **Report to User**:
    - Source: the local file path
    - Workbook name
    - Output directory
    - Mode: `-test` / default, and whether `-vision-all` was used
    - Total worksheets, extracted worksheets, sheets rendered as PNG
    - Successful / failed worksheets
    - Generated Markdown files
    - Embedded images extracted
