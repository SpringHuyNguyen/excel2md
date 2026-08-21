# Rule: Class Sheet (クラス / Class)

## Sheet name keywords

`クラス`, `Class`

## Note

This sheet describes one or more ABAP classes (often job template classes), each with one or more methods. A method typically calls other classes/methods (e.g. `CL_BALI_LOG`), and its parameters are grouped into Importing/Exporting/Changing/Returning blocks. The same method-block structure repeats for every method in the sheet.

## Goal

Output: metadata + one Class Information table + one section per method (Purpose, Called Method, Importing/Exporting/Changing/Returning parameter tables). Optimize for what an AI/engineer needs to understand the class's behavior and call graph — not for reproducing the Excel grid.

## Heading hierarchy

- YAML frontmatter (metadata — see section 1) at the very top of the file, before the H1
- `# Class Specification` (H1, fixed title — not the raw sheet name)
- `## Class Information` (H2)
- `## Method: <method name>` (H2) — one per method, repeated in sheet order
  - `### Purpose` (H3)
  - `### Called Method` (H3, if the method calls another class/method)
  - `### Importing` / `### Exporting` / `### Changing` / `### Returning` (H3, only the ones present)
    - `#### <parameter sub-setting title>` (H4, only if a parameter has nested detail, e.g. fixed constant values)

## 1. Metadata — YAML frontmatter (machine-readable, for downstream chunking/retrieval)

Emit metadata as YAML frontmatter, not a bullet list. This lets a chunker attach the same metadata to every chunk produced from the file (e.g. one chunk per `## Method:` section), instead of the metadata being stranded in a chunk near the top of the file.

**All 12 keys below are the standard schema shared by every sheet rule in this skill — every generated `.md` file has the SAME key set, in the SAME order, regardless of sheet type.** Keys that don't apply to this sheet (`current_version`, `file_name`) are still present, with an empty string value. This makes every file's frontmatter schema identical, so a downstream chunker/vector-DB never needs to check whether a key exists.

```yaml
---
document_type: ""
project_name: ""
business_name: ""
function_id: "39"
function_name: "AP"
created_date: 2025-04-24
last_updated_date: 2025-04-24
last_updated_by: ""
sheet_name: "☆クラス"
class_name: "ZCJ_PI920_01"
current_version: ""
file_name: ""
---
```

Field mapping (source label → YAML key):

1. Document Type (種類) → `document_type` — MUST be exactly one of two fixed values: `概要設計書` (Basic Design) or `システム要件定義書` (Detailed Design). Determine it from the workbook's Cover sheet / file name; if genuinely undeterminable, leave `""` — do NOT invent a third value.
2. Project Name (プロジェクト名) → `project_name`
3. Business Name (業務名) → `business_name`
4. Function ID (機能番号) → `function_id` (keep as a string — do NOT cast to a number, values like leading zeros or non-numeric IDs must survive)
5. Function Name (機能名称) → `function_name`
6. Created Date (作成日) → `created_date` (convert to ISO `YYYY-MM-DD`; e.g. `2025年04月24日` → `2025-04-24`)
7. Last Updated Date (最終変更日) → `last_updated_date` (same ISO conversion)
8. Last Updated By (最終変更者) → `last_updated_by`
9. `sheet_name` → the raw Excel sheet name (e.g. `☆クラス`), not translated
10. `class_name` → the class value from the sheet's Class Information block (e.g. `ZCJ_PI920_01`). If the sheet has multiple classes, use the FIRST class here (each class also repeats its own name in its `## Class Information` table body, so downstream chunking can still disambiguate).
11. `current_version` → not applicable to this sheet; always `""`.
12. `file_name` → not applicable to this sheet; always `""`.

If a field is empty in Excel, keep the YAML key with an empty string value (`""`). Do NOT omit the key and do NOT fabricate a value.

## 2. Class Information

One table per class on the sheet:

```markdown
## Class Information

| Item | Value |
|------|------|
| Class | ZCJ_PI920_01 |
| Name | APS連携_計画独立所要量送信 ジョブテンプレートクラス |
```

If the sheet lists multiple classes, repeat this table (with its own `## Class Information` heading) for each class, in sheet order.

## 3. Method sections

For every method under a class, emit one `## Method: <name>` block:

```markdown
## Method: constructor

### Purpose

アプリケーションジョブログの情報の初期化を行う。

### Called Method

| Class | Method |
|------|------|
| CL_BALI_LOG | create_with_header |
```

- `Purpose` = the method's description text (from 詳細の説明 / メソッドの説明). Keep the original Japanese text verbatim — do not translate or summarize.
- `Called Method` = only present if the method invokes another class/method. If a method calls multiple class/methods in sequence, list every call as its own row, in call order.
- If a method has no separate "called method" (e.g. it's a leaf/simple method), omit the `### Called Method` subsection entirely.

## 4. Parameter sections (Importing / Exporting / Changing / Returning)

Emit one table per parameter group that is actually present on the sheet (skip empty groups):

```markdown
### Importing

| Parameter | Type | Description |
|-----------|------|-------------|
| header | ref | ログに投入されるログヘッダーへの参照 |
```

- `Type` = the reference/type column as shown (e.g. `ref`). Keep as-is; do not infer an ABAP type that isn't stated.
- `Description` = the parameter's explanation text.

### Nested/constant detail under a parameter

When a parameter's description includes nested setup detail (e.g. "call class X's setter method with fixed values"), pull that nested detail into a `####` sub-section right after the table, as a bullet list of `key = value`:

```markdown
#### Header Setting

- object = ZRAP_COM_00
- subobject = ZRAP_IF_PI920
- external_id = ""
```

Keep the nested class/method reference itself in the parameter's `Description` cell (e.g. "クラス「CL_BALI_HEADER_SETTER」の作成メソッドをコール"); only the constant key=value pairs move to the bullet list.

## Content to keep

- Class name, Method name, Method description (Purpose)
- Called class/method (call graph)
- Importing/Exporting/Changing/Returning parameters and their descriptions
- Constant/fixed values passed into nested settings (object, subobject, external_id, etc.)
- The relationship between method and class

## Content to drop

- Merge cell artifacts, cell background color, border formatting
- Section-title-only rows that are just visual grouping: `ABAPクラス（ジョブ）`, `グローバルクラス`
- Empty cells/rows
- Row/column position from Excel (e.g. row 17, column AI)
- Font, alignment, and other pure formatting

## Constraints

- Do NOT drop or omit any method, parameter, or call — every method on the sheet gets its own `## Method:` block in sheet order.
- Do NOT invent a Type or Description that isn't stated in the sheet.
- If a metadata field is empty, keep the line with an empty value. Do NOT fabricate.
