# Rule: Change History Sheet (変更履歴 / Change History)

## Sheet name keywords
`変更履歴`, `履歴`, `Change History`, `History`, `Revision History`, `Lịch sử`, `Lịch sử thay đổi`, `Lịch sử chỉnh sửa`

## Goal
The sheet holds header metadata plus a change-history table. When converting to Markdown: keep concise metadata (4 fields) plus the history table with columns trimmed and duplicate rows merged.

## Information to KEEP

### Metadata (YAML frontmatter, machine-readable)
1. Document Type (種類) — this sheet has NO dedicated 種類 cell; infer it from the overall document context (e.g. 概要設計書, taken from the file name / Cover sheet).
2. Function ID (機能番号)
3. Function Name (機能名称)
4. Current Version (Ver) — NOT from a dedicated cell; take the largest/latest Version appearing in the history table.

### History table (exactly 4 columns, in order)
| Change Date (変更日) | Version (Ver) | Change Type (種別) | Change Details (変更内容) |

## Information to DROP
- The **Changed By (変更者)** column — no need to track who edited.
- Header fields not in the 4 metadata above: Project Name (プロジェクト名), Business Name (業務名), Created Date (作成日), Last Updated Date (最終変更日), Last Updated By (最終変更者).

## Output format

Emit metadata as **YAML frontmatter** at the very top of the file (not a bullet list), so a chunker can attach this metadata to every chunk from the file.

**All 12 keys below are the standard schema shared by every sheet rule in this skill — every generated `.md` file has the SAME key set, in the SAME order, regardless of sheet type.** This sheet only has real values for 4 of them (`document_type`, `function_id`, `function_name`, `current_version`, plus `sheet_name`); the rest are still present, with an empty string value. This makes every file's frontmatter schema identical, so a downstream chunker/vector-DB never needs to check whether a key exists.

### Example
```markdown
---
document_type: "概要設計書"
project_name: ""
business_name: ""
function_id: ""
function_name: ""
created_date: ""
last_updated_date: ""
last_updated_by: ""
sheet_name: "変更履歴"
class_name: ""
current_version: ""
file_name: ""
---

# 変更履歴 (Change History)

| Change Date (変更日) | Version (Ver) | Change Type (種別) | Change Details (変更内容) |
|---|---|---|---|
| <date> | <ver> | <type> | <details> |
```

Field mapping (source label → YAML key):

1. Document Type (種類) → `document_type` (inferred, per above) — MUST be exactly one of two fixed values: `概要設計書` (Basic Design) or `システム要件定義書` (Detailed Design). Do NOT invent a third value.
2. `project_name` → not present on this sheet; always `""`.
3. `business_name` → not present on this sheet; always `""`.
4. Function ID (機能番号) → `function_id` (keep as a string)
5. Function Name (機能名称) → `function_name`
6. `created_date` → not present on this sheet (dropped per above); always `""`.
7. `last_updated_date` → not present on this sheet (dropped per above); always `""`.
8. `last_updated_by` → not present on this sheet (dropped per above); always `""`.
9. `sheet_name` → the raw Excel sheet name, not translated
10. `class_name` → not applicable to this sheet; always `""`.
11. Current Version (Ver) → `current_version` (latest version in the table)
12. `file_name` → not applicable to this sheet; always `""`.

## Constraints
- STRICTLY consolidate/merge duplicate history rows (by date + version + details) to avoid duplicates in the log.
- Order the table chronologically / by version as in Excel; do not reorder on your own.
- If a metadata field is empty, keep the YAML key with an empty string value (`""`). Do NOT fabricate.
- Do NOT add fields beyond the standard 12-key schema above (the history table columns are separate — see above).
