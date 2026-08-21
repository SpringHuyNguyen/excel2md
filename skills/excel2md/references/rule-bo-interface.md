# Rule: BO Interface Specification Sheet (BOインターフェース仕様 / BO Interface Specification)

## Sheet name keywords

`BOインターフェース`, `BOインターフェース仕様`, `BO Interface`, `BO Interface Specification`, `Giao diện BO`

## Note

This sheet is NOT present in every Basic Design. It only appears when the function uses a Business Object (BO) Interface (e.g. RAP BO, EML, BO Operation...).

## Goal

Output: metadata + BO Interface specification tables (keep original columns) + accompanying text/logic (if any).

## Heading hierarchy

- YAML frontmatter (metadata — see section 1) at the very top of the file, before the H1
- Sheet name = `#` (H1)
- `BOインターフェース仕様` (BO Interface Specification) section = `##` (H2)

## 1. Metadata — YAML frontmatter (machine-readable, for downstream chunking/retrieval)

Emit metadata as YAML frontmatter, not a bullet list, so a chunker can attach the same metadata to every chunk produced from the file.

**All 12 keys below are the standard schema shared by every sheet rule in this skill — every generated `.md` file has the SAME key set, in the SAME order, regardless of sheet type.** Keys that don't apply to this sheet (`class_name`, `current_version`, `file_name`) are still present, with an empty string value. This makes every file's frontmatter schema identical, so a downstream chunker/vector-DB never needs to check whether a key exists.

```yaml
---
document_type: ""
project_name: ""
business_name: ""
function_id: ""
function_name: ""
created_date: 2025-04-24
last_updated_date: 2025-04-24
last_updated_by: ""
sheet_name: ""
class_name: ""
current_version: ""
file_name: ""
---
```

Field mapping (source label → YAML key):

1. Document Type (種類) → `document_type` — MUST be exactly one of two fixed values: `概要設計書` (Basic Design) or `システム要件定義書` (Detailed Design). Determine it from the workbook's Cover sheet / file name; if genuinely undeterminable, leave `""` — do NOT invent a third value.
2. Project Name (プロジェクト名) → `project_name`
3. Business Name (業務名) → `business_name`
4. Function ID (機能番号) → `function_id` (keep as a string)
5. Function Name (機能名称) → `function_name`
6. Created Date (作成日) → `created_date` (convert to ISO `YYYY-MM-DD`)
7. Last Updated Date (最終変更日) → `last_updated_date` (same ISO conversion)
8. Last Updated By (最終変更者) → `last_updated_by`
9. `sheet_name` → the raw Excel sheet name, not translated
10. `class_name` → not applicable to this sheet; always `""`.
11. `current_version` → not applicable to this sheet; always `""`.
12. `file_name` → not applicable to this sheet; always `""`.

If a field is empty in Excel, keep the YAML key with an empty string value (`""`). Do NOT omit the key and do NOT fabricate a value.

## 2. Tables — Markdown Table with DYNAMIC columns

- This sheet usually consists only of tables. Convert every table to a Markdown table.
- **Keep the ENTIRE original header/columns as in Excel** — do NOT hard-code column names.
- Preserve column order and all rows.

## 3. Accompanying Text / Logic (if any)

- If, besides the tables, there is a BO Operation description, rules, or code → **keep it in full** as Markdown text.
- EML / ABAP code → wrap in a ```` ```abap ... ``` ```` code block.
- Do NOT drop or summarize logic.

## Constraints

- Do NOT drop or rename any column; output the exact header present.
- Do NOT omit any row or any text/logic.
- If a metadata field is empty, keep the line with an empty value. Do NOT fabricate.
