# Rule: Cover Sheet (表紙 / Cover)

## Sheet name keywords
`表紙`, `Cover`, `Bìa`, `Trang bìa`, `Thông tin tài liệu`

## Goal
The Cover sheet contains a LOT of information (project info, document info, document-target info, title, table of contents 目次, approval block). When converting to Markdown, **keep ONLY the 7 core metadata fields**. Everything else is dropped.

## Fields to KEEP (exactly 7 source fields, no more no less — plus the standard schema keys below)
1. Document Type (種類)
2. Project Name (プロジェクト名)
3. Business Name (業務名)
4. Function Name (機能名称)
5. File Name (ファイル名称)
6. Created Date (作成日)
7. Last Updated Date (最終変更日)

## Information to DROP (do not output to MD)
- Table of contents (目次) — the whole 概要 / 要求機能 / 画面仕様 / ... list (it duplicates the other sheet names)
- Approval block: 会社名 (Company), サイン (Signature), 印 (Seal/Stamp), サインアップ日付 (Sign date), 日付 (Date)
- People fields: チーム名 (Team), 作成者 (Author), 確認者 (Reviewer), 最終更新者 (Last Updated User)

## Output format
- Emit metadata as **YAML frontmatter** at the very top of the file (not a bullet list) — this is the document-level metadata that a chunker can attach to every chunk from every sheet in the workbook, since the Cover sheet is the authoritative source for these values.
- The `#` heading is the document type (usually 概要設計書), with its English translation in parentheses.

**All 12 keys below are the standard schema shared by every sheet rule in this skill — every generated `.md` file has the SAME key set, in the SAME order, regardless of sheet type.** Keys that don't apply to this sheet (`function_id`, `last_updated_by`, `class_name`, `current_version`) are still present, with an empty string value. This makes every file's frontmatter schema identical, so a downstream chunker/vector-DB never needs to check whether a key exists.

### Example
```markdown
---
document_type: "概要設計書"
project_name: ""
business_name: ""
function_id: ""
function_name: ""
created_date: 2025-04-24
last_updated_date: 2025-04-24
last_updated_by: ""
sheet_name: "表紙"
class_name: ""
current_version: ""
file_name: ""
---

# 概要設計書 (Basic Design Document)
```

Field mapping (source label → YAML key):

1. Document Type (種類) → `document_type` — MUST be exactly one of two fixed values: `概要設計書` (Basic Design) or `システム要件定義書` (Detailed Design). The Cover sheet is the primary source for this value — keep it exactly as written (do not change it to a different document type); do NOT invent a third value.
2. Project Name (プロジェクト名) → `project_name`
3. Business Name (業務名) → `business_name`
4. `function_id` → not present on this sheet; always `""`.
5. Function Name (機能名称) → `function_name`
6. Created Date (作成日) → `created_date` (convert to ISO `YYYY-MM-DD`)
7. Last Updated Date (最終変更日) → `last_updated_date` (same ISO conversion)
8. `last_updated_by` → not present on this sheet; always `""`.
9. `sheet_name` → the raw Excel sheet name, not translated
10. `class_name` → not applicable to this sheet; always `""`.
11. `current_version` → not applicable to this sheet; always `""`.
12. File Name (ファイル名称) → `file_name`

## Constraints
- If a field is empty in Excel, keep the YAML key with an empty string value (`""`). Do NOT fabricate data.
- Do NOT add any field beyond the standard 12-key schema above, even if Excel has more information.
- Keep the 種類 value exactly as in the file (do not change it to a different document type).
