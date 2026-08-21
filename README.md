# excel2md

Turn an Excel design document into Markdown — one file per sheet.
Chuyển tài liệu thiết kế Excel thành Markdown — mỗi sheet một file.

---

## English

### What it does

Give it an `.xlsx` design document and you get back one Markdown file per visible sheet.

The hard part of this job is not reading Excel — it is not corrupting the text on the way out.
So the workbook is pulled apart into four sources, and each one is trusted for exactly one thing:

| Source | What it decides |
| --- | --- |
| Sheet text, read straight from the workbook | Every character in the output |
| A rendered image of the sheet | Table structure, merged cells, diagrams, where pictures sit |
| A rough table frame from a PDF export | Row and column boundaries, nothing else |
| Struck-through text | What to delete |

Characters always come from the workbook itself — never from the PDF, never from the image. That
rule exists because a PDF export mangles Vietnamese: it splits tone marks into separate glyphs, so
`Lịch sử chỉnh sửa` comes back as `L ch sị ử ch nh sỉ ửa`. Japanese usually survives, but "usually"
is not good enough, so the rule holds for every language.

Sheets are matched to a formatting rule by name, after stripping accents, numbering and decorative
symbols. A Japanese `テーブル定義` sheet, a Vietnamese `ĐN table` sheet and an English
`Table Definition` sheet all land on the same rule.

Diagrams drawn with shapes come back as Mermaid flowcharts. Embedded pictures are pulled out and
linked from the Markdown.

### What you need

| | |
| --- | --- |
| Claude Code | With plugin support |
| Python 3.10+ | |
| LibreOffice | Used headlessly to turn sheets into PDFs. The skill offers to install it |
| Four Python packages | Listed in `skills/excel2md/requirements.txt`. The skill installs them |

Only local `.xlsx` files. There is no SharePoint or URL input.

### Install

```
/plugin marketplace add <your-org>/excel2md
/plugin install excel2md@excel2md
```

That is the whole install. The dependencies sort themselves out on first use.

Installing a plugin never runs `pip` or a package manager, so the skill checks what it needs
before every run and fills in what is missing.

**LibreOffice.** If it is not there, the skill picks the right command for your machine — `winget`
on Windows, `brew` on macOS, `apt-get` / `dnf` / `pacman` / `zypper` on Linux — and asks you first.
It is a 350 MB system-wide install that wants administrator rights, so it never happens behind your
back. Say no and you get the download link instead.

Once it is installed on Windows, the skill adds LibreOffice to your user `PATH` so `soffice` works
in your own terminals too. Your existing terminals keep their old `PATH` until you open a new one.

**Python packages.** These go in without asking, because they land in the interpreter you are
already running rather than changing anything system-wide. Claude Code still shows you the command
before it runs.

If anything fails, the skill stops and shows you what it ran, what came back, and what to try. It
never starts a conversion half-equipped.

Want to do it yourself instead:

```
pip install -r <plugin-dir>/skills/excel2md/requirements.txt
```

Want to check your setup at any point:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

If LibreOffice ends up somewhere unusual, point the skill straight at it:

```
# Windows
set EXCEL2MD_SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe
# macOS
export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
# Linux
export EXCEL2MD_SOFFICE=/usr/bin/soffice
```

### Using it

```
/excel2md:excel2md --file <path.xlsx> [output_folder] [-vision-all] [-test]
```

| | |
| --- | --- |
| `--file <path.xlsx>` | Required. The workbook to convert |
| `output_folder` | Where to put the results, relative to where you are. Defaults to the current folder |
| `-vision-all` | Render an image of every sheet, not just the ones with drawings |
| `-test` | Keep the intermediate files instead of cleaning them up |

For example:

```
/excel2md:excel2md --file "C:\docs\design.xlsx" out
```

leaves you with:

```
out/
├── 001_design_cover.md
├── 002_design_history.md
├── ...
└── images/           ← pictures from the workbook, linked from the Markdown
```

Your `.xlsx` is never touched.

### When something goes wrong

Start here — it tells you what is missing and the exact command that fixes it:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

| What you see | What it means |
| --- | --- |
| `NOT READY: LibreOffice was not found` | Not installed, or the skill cannot see it. Accept the install it offers, or set `EXCEL2MD_SOFFICE` |
| The install hangs, or complains about permissions | The administrator prompt could not be answered from the terminal. Run the command yourself in an elevated shell |
| `No package found matching input criteria` | Your package index is stale. Try `winget source update`, or download LibreOffice manually |
| Still `NOT READY` after a clean install | LibreOffice landed somewhere unusual. Set `EXCEL2MD_SOFFICE` |
| `NOT READY: n Python package(s) missing` | Run the command preflight prints — it targets the right interpreter |
| pip says `Permission denied` | Your Python lives in a system folder. Add `--user`, or use a virtual environment |
| pip says `externally-managed-environment` | A Linux distro Python. Use a virtual environment |
| Installed fine, still `ModuleNotFoundError` | The packages went to a different Python. Compare the path preflight prints against the one you used |
| A sheet has no PDF frame | Nothing to worry about. That sheet uses its text and rendered image instead |
| A sheet is missing entirely | Hidden sheets are skipped on purpose |

---

## Tiếng Việt

### Nó làm gì

Đưa vào một file thiết kế `.xlsx`, bạn nhận lại mỗi sheet hiển thị một file Markdown.

Phần khó không nằm ở việc đọc Excel, mà ở việc không làm hỏng chữ trên đường ra. Vì vậy workbook
được tách thành bốn nguồn, mỗi nguồn chỉ được tin đúng một việc:

| Nguồn | Quyết định điều gì |
| --- | --- |
| Text đọc thẳng từ workbook | Mọi ký tự trong kết quả |
| Ảnh render của sheet | Cấu trúc bảng, ô gộp, sơ đồ, vị trí hình |
| Khung bảng thô từ bản PDF | Ranh giới hàng và cột, chỉ vậy thôi |
| Chữ gạch ngang | Phần cần xoá |

Ký tự luôn lấy từ chính workbook, không bao giờ từ PDF hay từ ảnh. Quy tắc này có vì bản PDF phá
tiếng Việt: nó tách dấu thanh thành glyph riêng, nên `Lịch sử chỉnh sửa` quay ra thành
`L ch sị ử ch nh sỉ ửa`. Tiếng Nhật thường không sao, nhưng "thường" thì chưa đủ, nên quy tắc áp
dụng cho mọi ngôn ngữ.

Sheet được ghép vào quy tắc định dạng theo tên, sau khi bỏ dấu, bỏ số thứ tự và ký hiệu trang trí.
Sheet `テーブル定義` tiếng Nhật, `ĐN table` tiếng Việt và `Table Definition` tiếng Anh đều rơi vào
cùng một quy tắc.

Sơ đồ vẽ bằng shape được dựng lại thành Mermaid flowchart. Hình nhúng được trích ra và link từ
Markdown.

### Cần những gì

| | |
| --- | --- |
| Claude Code | Bản có hỗ trợ plugin |
| Python 3.10 trở lên | |
| LibreOffice | Chạy ngầm để chuyển sheet thành PDF. Skill sẽ hỏi để cài giúp |
| Bốn package Python | Ghi trong `skills/excel2md/requirements.txt`. Skill tự cài |

Chỉ nhận file `.xlsx` trên máy. Không có đầu vào SharePoint hay URL.

### Cài đặt

```
/plugin marketplace add <your-org>/excel2md
/plugin install excel2md@excel2md
```

Cài đặt chỉ có vậy. Phần phụ thuộc tự lo lấy trong lần dùng đầu tiên.

Việc cài plugin không bao giờ chạy `pip` hay package manager, nên skill tự kiểm tra trước mỗi lần
chạy và bù vào những gì còn thiếu.

**LibreOffice.** Nếu chưa có, skill chọn đúng lệnh cho máy bạn — `winget` trên Windows, `brew` trên
macOS, `apt-get` / `dnf` / `pacman` / `zypper` trên Linux — và hỏi bạn trước. Đây là bản cài 350 MB
cho toàn máy và cần quyền admin, nên nó không bao giờ tự chạy sau lưng bạn. Từ chối thì bạn nhận
link tải về.

Trên Windows, sau khi cài xong skill thêm LibreOffice vào `PATH` của người dùng để bạn gõ `soffice`
được trong terminal của mình. Các terminal đang mở vẫn giữ `PATH` cũ cho tới khi bạn mở cái mới.

**Package Python.** Phần này cài không hỏi, vì chúng vào đúng interpreter bạn đang chạy chứ không
đụng gì tới hệ thống. Claude Code vẫn cho bạn xem lệnh trước khi chạy.

Nếu có gì đó hỏng, skill dừng lại và cho bạn xem nó đã chạy lệnh gì, kết quả trả về ra sao, và nên
thử gì tiếp. Nó không bao giờ bắt đầu convert khi còn thiếu đồ.

Muốn tự làm thay vì để skill lo:

```
pip install -r <plugin-dir>/skills/excel2md/requirements.txt
```

Muốn kiểm tra môi trường bất cứ lúc nào:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

Nếu LibreOffice nằm ở chỗ lạ, trỏ thẳng skill vào đó:

```
# Windows
set EXCEL2MD_SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe
# macOS
export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
# Linux
export EXCEL2MD_SOFFICE=/usr/bin/soffice
```

### Cách dùng

```
/excel2md:excel2md --file <path.xlsx> [output_folder] [-vision-all] [-test]
```

| | |
| --- | --- |
| `--file <path.xlsx>` | Bắt buộc. File workbook cần chuyển |
| `output_folder` | Nơi để kết quả, tính từ chỗ bạn đang đứng. Bỏ trống thì dùng thư mục hiện tại |
| `-vision-all` | Render ảnh cho mọi sheet, không chỉ sheet có hình vẽ |
| `-test` | Giữ lại file trung gian thay vì dọn đi |

Ví dụ:

```
/excel2md:excel2md --file "C:\docs\design.xlsx" out
```

cho ra:

```
out/
├── 001_design_cover.md
├── 002_design_history.md
├── ...
└── images/           ← hình lấy từ workbook, được link trong Markdown
```

File `.xlsx` của bạn không bị đụng tới.

### Khi có trục trặc

Bắt đầu từ đây — nó nói cho bạn biết thiếu gì và lệnh nào sửa được:

```
python <plugin-dir>/skills/excel2md/preflight.py
```

| Bạn thấy gì | Nghĩa là gì |
| --- | --- |
| `NOT READY: LibreOffice was not found` | Chưa cài, hoặc skill không thấy. Đồng ý cho nó cài, hoặc đặt `EXCEL2MD_SOFFICE` |
| Lệnh cài treo, hoặc báo lỗi quyền | Cửa sổ xin quyền admin không trả lời được từ terminal. Tự chạy lệnh đó trong shell đã nâng quyền |
| `No package found matching input criteria` | Danh mục package đã cũ. Thử `winget source update`, hoặc tải LibreOffice thủ công |
| Cài xong vẫn `NOT READY` | LibreOffice nằm ở chỗ lạ. Đặt `EXCEL2MD_SOFFICE` |
| `NOT READY: n Python package(s) missing` | Chạy lệnh preflight in ra — nó nhắm đúng interpreter |
| pip báo `Permission denied` | Python của bạn nằm trong thư mục hệ thống. Thêm `--user`, hoặc dùng virtual environment |
| pip báo `externally-managed-environment` | Python do distro Linux quản lý. Dùng virtual environment |
| Cài xong vẫn `ModuleNotFoundError` | Package vào nhầm Python khác. So đường dẫn preflight in ra với cái bạn đã dùng |
| Một sheet không có khung PDF | Không sao. Sheet đó dùng text và ảnh render thay thế |
| Thiếu hẳn một sheet | Sheet ẩn bị bỏ qua, đúng như thiết kế |

---

## License

MIT. Xem [LICENSE](LICENSE).
