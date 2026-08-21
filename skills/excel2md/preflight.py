#!/usr/bin/env python3
"""
Check that everything excel2md needs is present, before the pipeline starts.

Reports what is missing and, through its exit code, whether the caller can fix
it automatically.

Usage:
    python preflight.py

Exit codes:
    0  ready — every package imports and LibreOffice was found
    2  Python packages missing — recoverable, install requirements.txt
    3  LibreOffice missing — NOT recoverable, the user must install it
    4  Python is too old
"""
import io
import os
import shutil
import sys

# Fix Vietnamese characters on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MIN_PYTHON = (3, 10)

# pip name -> import names to try, first hit wins. PyMuPDF ships as both
# `pymupdf` and the older `fitz`; probing `pymupdf` first keeps its deprecation
# warning out of the report, while `fitz` still covers older releases.
REQUIRED = {
    "openpyxl": ("openpyxl",),
    "pypdf": ("pypdf",),
    "pymupdf": ("pymupdf", "fitz"),
    "pymupdf4llm": ("pymupdf4llm",),
}

SOFFICE_CANDIDATES = {
    "win32": [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ],
    "darwin": [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ],
}
SOFFICE_CANDIDATES_OTHER = [
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/snap/bin/libreoffice",
]


def install_command() -> str | None:
    """The package-manager command that installs LibreOffice here, if there is one."""
    if sys.platform == "win32":
        if shutil.which("winget"):
            return (
                "winget install --id TheDocumentFoundation.LibreOffice -e "
                "--accept-package-agreements --accept-source-agreements"
            )
        return None

    if sys.platform == "darwin":
        if shutil.which("brew"):
            return "brew install --cask libreoffice"
        return None

    for manager, command in (
        ("apt-get", "sudo apt-get install -y libreoffice"),
        ("dnf", "sudo dnf install -y libreoffice"),
        ("pacman", "sudo pacman -S --noconfirm libreoffice-fresh"),
        ("zypper", "sudo zypper install -y libreoffice"),
    ):
        if shutil.which(manager):
            return command
    return None


def find_soffice() -> str | None:
    """Same resolution order as xlsx_to_pdf.py, but never exits."""
    override = os.environ.get("EXCEL2MD_SOFFICE")
    if override:
        return override if os.path.isfile(override) else None

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found

    for path in SOFFICE_CANDIDATES.get(sys.platform, SOFFICE_CANDIDATES_OTHER):
        if os.path.isfile(path):
            return path
    return None


def missing_packages() -> list[str]:
    missing = []
    for pip_name, import_names in REQUIRED.items():
        for import_name in import_names:
            try:
                __import__(import_name)
                break
            except ImportError:
                continue
        else:
            missing.append(pip_name)
    return missing


def main() -> int:
    # The interpreter matters more than anything else here: a user with several
    # Pythons installed will otherwise pip-install into the wrong one.
    print(f"python: {sys.version.split()[0]} at {sys.executable}")

    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(n) for n in MIN_PYTHON)
        print(f"NOT READY: Python {need}+ is required, this is {sys.version.split()[0]}.")
        print(f"  Install Python {need} or newer, then run excel2md with that interpreter.")
        return 4

    missing = missing_packages()
    soffice = find_soffice()

    for pip_name in REQUIRED:
        print(f"  {'MISSING' if pip_name in missing else 'ok     '}  {pip_name}")
    print(f"  {'ok     ' if soffice else 'MISSING'}  LibreOffice" + (f" ({soffice})" if soffice else ""))

    # LibreOffice first: no amount of pip fixes it, so say so before the caller
    # spends time installing packages it cannot use yet.
    if not soffice:
        override = os.environ.get("EXCEL2MD_SOFFICE")
        print()
        if override:
            print(f"NOT READY: EXCEL2MD_SOFFICE is set to {override}, but that is not a file.")
            print("  Correct the path, or unset the variable to fall back to auto-detection.")
        else:
            print("NOT READY: LibreOffice was not found.")
            print("  excel2md uses it headlessly to export each sheet to PDF. It is a native")
            print("  application, so it cannot be installed with pip.")
            command = install_command()
            if command:
                # Machine-readable: the caller keys on this prefix to offer the install.
                print(f"SUGGESTED_INSTALL: {command}")
                print("  A package manager is available. The command above installs LibreOffice")
                print("  (roughly 350 MB) system-wide and will ask for administrator rights.")
            else:
                print("  No supported package manager was found on this machine.")
            print("  Manual alternative: download from https://www.libreoffice.org/download/")
            print("  If `soffice` is still not on PATH afterwards, point EXCEL2MD_SOFFICE at it:")
            print(r'       Windows  set EXCEL2MD_SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe')
            print("       macOS    export EXCEL2MD_SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice")
            print("       Linux    export EXCEL2MD_SOFFICE=/usr/bin/soffice")
        return 3

    if missing:
        req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        print()
        print(f"NOT READY: {len(missing)} Python package(s) missing: {', '.join(missing)}")
        print("  Install them with:")
        print(f'    "{sys.executable}" -m pip install -r "{req}"')
        return 2

    print()
    print("READY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
