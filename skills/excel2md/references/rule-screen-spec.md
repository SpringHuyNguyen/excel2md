# Rule: Screen Specification Sheet (画面仕様 / Screen Specification)

## Sheet name keywords

`画面仕様`, `Screen Spec`, `Screen Specification`, `UI Spec`, `Spec màn hình`, `Đặc tả màn hình`, `Thiết kế màn hình`, `Giao diện`

## Goal

Screen specification sheet. Output: metadata + layout description as text (NO OCR of images) + field/button tables.

## Heading hierarchy

- YAML frontmatter (metadata — see section 1) at the very top of the file, before the H1
- Sheet name = `#` (H1)
- Layout section `☆画面レイアウト` = `##` (H2)
- `画面定義` (Screen Definition) section = `##` (H2)
- Each screen table = `###` (H3) with a title based on the screen name

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

## 2. Screen Layout (☆画面レイアウト) — Text

- Keep ONLY the textual description below the figure (if any): screen components (App, Screen, List, Button...), layout notes, UI-related descriptions.
- **Do NOT OCR, do NOT turn a screenshot into text.**

## 3. Screen Definition (画面定義) — Text

Keep as text:

- App Name (アプリ名)
- Screen Name (画面名)

## 4. List Screen tables (一覧画面) — Markdown Table with FIXED columns

For the list screen (一覧画面), output the 3 tables with exactly the columns and order below. Leave a column empty if it has no data. If Excel has an extra column beyond the list → **add that column** (do not drop data).

### 4.1 Selection Fields (一覧画面「選択項目」 / search conditions)

| Field Name (項目名) | Specification No. (項目仕様No.) | Required (必須) | Search Help (検索ヘルプ) | Existence Check (存在チェック) | Notes (備考) |

### 4.2 Output Fields (一覧画面「出力項目」 / display columns)

| Field Name (項目名) | Specification No. (項目仕様No.) | Notes (備考) |

### 4.3 Buttons (一覧画面・ボタン)

| Button (ボタン) | Action (動作内容) | Notes (備考) |

## 5. Screens OTHER than List Screen (Detail / Object page / Create...)

- Do NOT apply the fixed-column template from section 4.
- Convert to a Markdown table **keeping the original columns as in Excel**.
- Set the H3 heading based on the original screen/table name.

## Constraints

- Do NOT OCR layout images.
- Keep all rows of every table.
- If a metadata field is empty, keep the line with an empty value. Do NOT fabricate.
