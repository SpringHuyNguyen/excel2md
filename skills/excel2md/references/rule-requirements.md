# Rule: Requirements Definition Sheet (要件定義 / Requirements Definition)

## Sheet name keywords

`要件定義`, `要求機能`, `要求仕様`, `運用要件`, `Requirements`, `Yêu cầu`, `Định nghĩa yêu cầu`, `Đặc tả yêu cầu`, `Yêu cầu nghiệp vụ`, `Yêu cầu vận hành`

## Goal

This is a requirements sheet — the **Logic is the most important part and must NOT be dropped or summarized**. The MD output follows the natural flow of the content (the "Text" part); the Table / Diagram / Logic rules are applied INLINE to each element as it is encountered, NOT gathered into separate sections.

## Heading hierarchy

- YAML frontmatter (metadata — see Metadata section) at the very top of the file, before the H1
- Sheet name = `#` (H1)
- `★...` section (e.g. ★ビジネスバックグラウンド, ★業務機能的要件) = `##` (H2)
- `＜...＞` sub-heading (e.g. ＜処理フロー＞, ＜目的＞) = `###` (H3)
- Content (paragraph / bullet / numbered list / table / mermaid) sits under its heading.

## Heading translation rules

- A heading in the familiar-terms list below is translated **bilingually**: `English (日本語)`.
  - 業務背景 = Business Background, 追加開発にて実現すべき内容 = Additional Development Scope, 追加開発が必要な理由 = Reason for Additional Development, 前提 = Preconditions, 処理フロー = Processing Flow, 全体概要 = Overall Overview, 機能概要 = Function Overview, 処理概要 = Processing Overview, 目的 = Purpose, 備考 = Notes, ビジネスバックグラウンド = Business Background, 業務機能的要件 = Business Functional Requirements.
- A `＜...＞` heading NOT in the list → **keep the original Japanese** (drop the ＜＞ marks). Do NOT fabricate a translation.
- Process EVERY `＜...＞` heading — do not hard-code by name; an unknown heading still becomes an H3.

## 1. Metadata — YAML frontmatter (machine-readable, for downstream chunking/retrieval)

Emit metadata as YAML frontmatter, not a bullet list, so a chunker can attach the same metadata to every chunk produced from the file (this sheet in particular tends to be long and split across many `##`/`###` chunks).

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

## 2. Text (main content)

- Convert all descriptive content to Markdown text, preserving structure: paragraph, bullet list, numbered list, note.
- Keep ALL `＜...＞` headings as H3 (per the translation rules above).

## 3. Table (applied inline)

Any table encountered in the Text → Markdown table. Preserve the header, row/column structure, and cell content. Includes but is not limited to: Standard Function/App list, Function Summary, Authorization Matrix, Processing Summary, Parameter Mapping, processing conditions, Input/Output, logic-description tables.

## 4. Diagram (applied inline)

For the `＜処理フロー＞` (Processing Flow) section and any processing-flow figures. Do NOT store as an image. Pick the diagram source in this priority order:

1. **Preferred — the rendered PNG(s) of this sheet** given in your task prompt. Read each image with the Read tool and rebuild what you can see as Mermaid (`flowchart LR`/`TD` or `sequenceDiagram`). Node labels: shape text is NOT in the sheet's `normal_*.txt` — that file holds cell values only, and drawing/shape text never reaches it. Read node labels from the image. If a label's text also appears as a cell value in `normal_*.txt`, use that file's spelling instead of what you read from the image. When a label exists only in the image, transcribe it with particular care — Vietnamese diacritics and Japanese kanji are both easy to misread from a rendered image — and add a short note below the diagram that its labels were read from the image. Draw only arrows you can clearly see.
2. **Fallback — reconstruct from text:** If this sheet has no PNG, build the Mermaid from the box text in the intermediate markdown given in your task prompt. The PDF extraction loses connector arrows, so if relationships cannot be fully recognized, generate the best-effort Mermaid with a note for reference.

```mermaid
flowchart LR
    ManufacturingOrder --> EventClass
    EventClass --> PurchaseOrder
    PurchaseOrder --> EventLog
    EventLog --> FioriApp
```

## 5. Logic (MOST IMPORTANT — applied inline)

Keep ALL of the following in FULL, with NO dropping or summarizing: Business Logic, Processing Logic, Validation Rules, Business Rules, Conditions, Exception Handling, Authorization Logic, Notes, bullet lists, numbered lists.

## Constraints

- Do NOT summarize or drop any logic/condition/rule.
- Do NOT gather Table/Diagram/Logic into separate sections — keep them in place within the content flow.
- If a metadata field is empty, keep the line with an empty value. Do NOT fabricate.
