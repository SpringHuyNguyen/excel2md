# Rule: Translation Sheet (翻訳内容 / Translation)

## Sheet name keywords

`翻訳`, `翻訳内容`, `画内内容`, `Translation`, `i18n`, `Localization`, `Nội dung dịch`, `Bản dịch`, `Dịch thuật`, `Đa ngôn ngữ`
(any language pair: JA→EN, JA→ZH, ...)

## Goal

The sheet holds translated content between languages (usually JA→EN, sometimes JA→ZH). Output: metadata + all translation tables as Markdown tables. This rule applies to ALL language pairs — the target-language column is dynamic per sheet (English / Chinese / ...).

## Heading hierarchy

- YAML frontmatter (metadata — see section 1) at the very top of the file, before the H1
- Sheet name = `#` (H1)
- Each translation-table group = `##` (H2) titled by the group name

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

## 2. Translation tables — Markdown Table

- Convert ALL translation tables in the sheet to Markdown tables.
- **Do NOT hard-code the table names or the number of tables** — output as many groups as exist, each with its own H2 heading.
- Preserve column structure and content. Name the target-language column per the sheet (English / Chinese / ...).
- Keep the `Japanese (JA)` column as-is; keep `Notes (備考)` if present.

Commonly seen table groups (for reference only, NOT fixed):

- Application (アプリ名): No. | Japanese (JA) | English (EN) | Notes (備考)
- Screen (画面名): No. | Japanese (JA) | English (EN) | Notes (備考)
- Selection / Fixed Display Items (選択・固定対象項目): No. | Japanese (JA) | English (EN) | Notes (備考)
- Buttons (ボタン): No. | Japanese (JA) | English (EN) | Notes (備考)
- Messages (メッセージ): Message ID | Japanese (JA) | English (EN) | Notes (備考)

## Constraints

- Output every translation table in the sheet; do not drop any group.
- Preserve all rows and the column order as in Excel.
- If a metadata field is empty, keep the line with an empty value. Do NOT fabricate.
