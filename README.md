# excel2md

A Claude Code plugin that converts a local Excel design document into Markdown — one file per sheet.
Excel の設計書をシートごとの Markdown に変換する Claude Code プラグインです。

---

## English

### What it does

Point it at an `.xlsx` design document and it produces one Markdown file per visible sheet.

The workbook is decomposed into four sources, each with a strictly separated role:

| Source | Authority over |
| --- | --- |
| Per-sheet text, read straight from the workbook | Every character in the output |
| Rendered sheet PNG | Table structure, merges, diagrams, image placement |
| Rough table frame from a PDF export | Row/column boundaries only |
| Struck-through text | Text to delete from the output |

Characters always come from the workbook itself, never from the PDF or the image. This matters
for mixed Japanese/Vietnamese documents, where a PDF export splits Vietnamese tone marks into
separate glyphs and drops characters at font fallbacks.

Sheets are routed to a formatting rule by name — cover, change history, table definition, item
specification, screen transition, requirements and so on — so a Japanese `テーブル定義` sheet and a
Vietnamese `ĐN table` sheet reach the same rule.

Shape-based diagrams are rebuilt as Mermaid flowcharts, and embedded pictures are extracted and
linked from the Markdown.

### Requirements

| Requirement | Notes |
| --- | --- |
| Claude Code | Plugin support |
| Python 3.10+ | `list[str]` type hints are used |
| LibreOffice | Native app. Used headless to export sheets to PDF |
| Python packages | See `skills/excel2md/requirements.txt` |

`--url` / SharePoint input is **not** part of this plugin. Only local `.xlsx` files are supported.

### Install

```
/plugin marketplace add <your-org>/excel2md
/plugin install excel2md@excel2md
```

**Dependencies install themselves.** Installing a plugin never runs `pip` or a package manager,
so the skill checks what it needs before every run and offers to fill the gaps.

**LibreOffice.** If it is missing, the skill proposes the right command for your machine —
`winget` on Windows, `brew` on macOS, `apt-get` / `dnf` / `pacman` / `zypper` on Linux — and asks
before running it. This is a system-wide install of roughly 350 MB that prompts for
administrator rights, so it never happens unprompted. Decline and you get the manual download
link instead. If no package manager is available, you get the link straight away.

If the administrator prompt cannot be answered from the terminal, run the command yourself in an
elevated shell and re-run the skill:

```
winget install --id TheDocumentFoundation.LibreOffice -e --accept-package-agreements --accept-source-agreements
```

**Python packages.** These install without a confirmation step, because they go into the
interpreter you are already running rather than changing the system. The skill reports which
packages are missing and installs them with that exact interpreter — Claude Code still asks you
to approve the command. If any install fails, the skill stops and shows you the command, the
tool's real output, and the likely cause; it never runs the pipeline half-equipped.

To install them ahead of time instead:

```
pip install -r <plugin-dir>/skills/excel2md/requirements.txt
```

To check your setup at any point:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

If `soffice` is not on your `PATH`, point `EXCEL2MD_SOFFICE` at the executable:

```
# Windows
set EXCEL2MD_SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe
# macOS
export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
# Linux
export EXCEL2MD_SOFFICE=/usr/bin/soffice
```

### Usage

```
/excel2md:excel2md --file <path.xlsx> [output_folder_name] [-vision-all] [-test]
```

| Argument | Meaning |
| --- | --- |
| `--file <path.xlsx>` | Required. The local workbook to convert |
| `output_folder_name` | Optional. Output folder, relative to the current directory. Defaults to the current directory |
| `-vision-all` | Optional. Render a PNG for every sheet, not only sheets containing drawings |
| `-test` | Optional. Keep all intermediate folders (`raw_pdf/`, `raw_md/`, `png/`, `text/`) |

Example:

```
/excel2md:excel2md --file "C:\docs\design.xlsx" out
```

Output, by default:

```
out/
├── 001_design_cover.md
├── 002_design_history.md
├── ...
└── images/           ← embedded pictures, linked from the Markdown
```

Your source `.xlsx` is never modified or deleted.

### Troubleshooting

Run `python <plugin-dir>/skills/excel2md/preflight.py` first — it names what is missing and
prints the exact command to fix it.

| Symptom | Cause |
| --- | --- |
| `NOT READY: LibreOffice was not found` | Not installed, or not on `PATH`. Accept the offered install, or set `EXCEL2MD_SOFFICE` |
| Install command hangs, or fails with an elevation error | The administrator prompt could not be answered from the terminal. Run it in an elevated shell |
| `No package found matching input criteria` | Stale package index. Run `winget source update`, or download manually |
| Still `NOT READY` after a successful install | LibreOffice landed somewhere non-standard. Set `EXCEL2MD_SOFFICE` |
| `NOT READY: n Python package(s) missing` | Run the command preflight prints. It targets the right interpreter |
| pip fails with `Permission denied` | The interpreter lives in a system location. Retry with `--user`, or use a virtual environment |
| pip fails with `externally-managed-environment` | A distro-managed Python. Use a virtual environment |
| Packages installed but still `ModuleNotFoundError` | They went to a different interpreter. Compare the path preflight prints with the one you used |
| A sheet produced no PDF frame | Harmless. That sheet falls back to text plus rendered PNG for structure |
| Hidden sheets are missing | Intended. Hidden sheets are skipped |

### Development

```
cd skills/excel2md
pip install -r requirements.txt pytest
python -m pytest tests/
```

---

## 日本語

### 概要

ローカルの `.xlsx` 設計書を指定すると、表示されているシートごとに Markdown ファイルを 1 つ生成します。

ワークブックは 4 つのソースに分解され、それぞれの役割は厳密に分離されています。

| ソース | 権限を持つ範囲 |
| --- | --- |
| ワークブックから直接読んだシート別テキスト | 出力される全ての文字 |
| レンダリングされたシート PNG | 表構造、セル結合、図、画像の配置 |
| PDF エクスポートから得た大まかな表枠 | 行・列の境界のみ |
| 取り消し線付きテキスト | 出力から削除する文字列 |

文字は常にワークブック自体から取得し、PDF や画像からは決して取得しません。日本語とベトナム語が
混在する文書では、PDF エクスポートがベトナム語の声調記号を別のグリフに分割したり、フォント
フォールバック箇所で文字を落としたりするため、この区別が重要になります。

シートは名前によってフォーマット規則へ振り分けられます（表紙、変更履歴、テーブル定義、項目仕様、
画面遷移、要件定義など）。日本語の `テーブル定義` シートとベトナム語の `ĐN table` シートは
同じ規則に到達します。

図形で描かれた図は Mermaid のフローチャートとして再構築され、埋め込み画像は抽出されて
Markdown からリンクされます。

### 必要なもの

| 項目 | 備考 |
| --- | --- |
| Claude Code | プラグイン対応版 |
| Python 3.10 以上 | `list[str]` 型ヒントを使用 |
| LibreOffice | ネイティブアプリ。ヘッドレスでシートを PDF に変換 |
| Python パッケージ | `skills/excel2md/requirements.txt` を参照 |

`--url` / SharePoint 入力はこのプラグインには**含まれません**。ローカルの `.xlsx` のみ対応します。

### インストール

```
/plugin marketplace add <your-org>/excel2md
/plugin install excel2md@excel2md
```

**依存関係は自動でインストールされます。** プラグインのインストール時に `pip` やパッケージ
マネージャーが実行されることはないため、スキル側が実行のたびに必要なものを確認し、不足分の
導入を提案します。

**LibreOffice。** 見つからない場合、環境に応じたコマンドを提示します（Windows は `winget`、
macOS は `brew`、Linux は `apt-get` / `dnf` / `pacman` / `zypper`）。実行前に必ず確認を求めます。
約 350 MB のシステム全体へのインストールであり管理者権限を要求するため、無断で実行されることは
ありません。断った場合は手動ダウンロードのリンクを提示します。対応するパッケージマネージャーが
無い場合も同様にリンクを提示します。

管理者権限のプロンプトにターミナルから応答できない場合は、昇格したシェルで次を実行してから
スキルを再実行してください。

```
winget install --id TheDocumentFoundation.LibreOffice -e --accept-package-agreements --accept-source-agreements
```

**Python パッケージ。** こちらは確認なしでインストールされます。システムを変更するのではなく、
すでに動作しているインタプリタに導入されるためです。不足しているパッケージを報告し、その
インタプリタを対象にインストールします（コマンドの承認は Claude Code が求めます）。
インストールが失敗した場合は処理を中断し、実行したコマンド、ツールの実際の出力、想定される
原因を提示します。依存関係が揃わないままパイプラインを実行することはありません。

事前にインストールしておく場合:

```
pip install -r <plugin-dir>/skills/excel2md/requirements.txt
```

環境を確認する場合:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

`soffice` が `PATH` に無い場合は、`EXCEL2MD_SOFFICE` に実行ファイルのパスを指定します。

```
# Windows
set EXCEL2MD_SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe
# macOS
export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
# Linux
export EXCEL2MD_SOFFICE=/usr/bin/soffice
```

### 使い方

```
/excel2md:excel2md --file <path.xlsx> [output_folder_name] [-vision-all] [-test]
```

| 引数 | 意味 |
| --- | --- |
| `--file <path.xlsx>` | 必須。変換するローカルのワークブック |
| `output_folder_name` | 任意。カレントディレクトリからの相対出力フォルダ。省略時はカレントディレクトリ |
| `-vision-all` | 任意。図形の有無に関わらず全シートを PNG 化する |
| `-test` | 任意。中間フォルダ（`raw_pdf/`、`raw_md/`、`png/`、`text/`）を全て残す |

例:

```
/excel2md:excel2md --file "C:\docs\design.xlsx" out
```

既定の出力:

```
out/
├── 001_design_cover.md
├── 002_design_history.md
├── ...
└── images/           ← 埋め込み画像。Markdown からリンクされる
```

元の `.xlsx` は変更も削除もされません。

### トラブルシューティング

まず `python <plugin-dir>/skills/excel2md/preflight.py` を実行してください。不足しているものと、
それを解消するコマンドをそのまま出力します。

| 症状 | 原因 |
| --- | --- |
| `NOT READY: LibreOffice was not found` | 未インストール、または `PATH` に無い。提示されたインストールを承認するか `EXCEL2MD_SOFFICE` を設定 |
| インストールコマンドが停止する、権限エラーで失敗する | 管理者プロンプトにターミナルから応答できていません。昇格したシェルで実行してください |
| `No package found matching input criteria` | パッケージ索引が古い状態です。`winget source update` を実行するか手動でダウンロード |
| インストール成功後も `NOT READY` | LibreOffice が非標準の場所にあります。`EXCEL2MD_SOFFICE` を設定 |
| `NOT READY: n Python package(s) missing` | preflight が出力したコマンドを実行。正しいインタプリタが対象になります |
| pip が `Permission denied` で失敗 | インタプリタがシステム領域にあります。`--user` を付けるか仮想環境を使用 |
| pip が `externally-managed-environment` で失敗 | ディストリビューション管理下の Python です。仮想環境を使用 |
| インストール済みなのに `ModuleNotFoundError` | 別のインタプリタに入っています。preflight が出力したパスと照合してください |
| あるシートで PDF 表枠が作られない | 問題ありません。そのシートはテキストと PNG のみで構造を判断します |
| 非表示シートが出力されない | 仕様です。非表示シートはスキップされます |

### 開発

```
cd skills/excel2md
pip install -r requirements.txt pytest
python -m pytest tests/
```

---

## License

MIT. See [LICENSE](LICENSE).
