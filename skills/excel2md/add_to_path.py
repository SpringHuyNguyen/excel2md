#!/usr/bin/env python3
"""
Put LibreOffice's program directory on the user's PATH, on Windows.

Run this after installing LibreOffice, so `soffice` works in the user's own
terminals too. excel2md itself does not need it — xlsx_to_pdf.py falls back to
the default install location — so this is a convenience, and it never touches
anything outside the current user's environment.

Elsewhere it does nothing: brew, apt, dnf, pacman and zypper all put `soffice`
on PATH themselves.

Usage:
    python add_to_path.py

Exit codes:
    0  the directory is on PATH (added just now, or already there)
    1  could not do it — the reason is printed
"""
import io
import os
import sys

# Fix Vietnamese characters on Windows console. Guarded because these modules
# import one another: wrapping an already-wrapped stdout drops the first
# wrapper, and collecting it closes the buffer both were writing to.
if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preflight import find_soffice  # noqa: E402


def already_listed(current: str, directory: str) -> bool:
    """True when `directory` is already one of the PATH entries."""
    target = os.path.normcase(os.path.normpath(directory)).rstrip("\\/")
    for entry in current.split(os.pathsep):
        entry = entry.strip().strip('"')
        if not entry:
            continue
        if os.path.normcase(os.path.normpath(entry)).rstrip("\\/") == target:
            return True
    return False


def path_after_adding(current: str, directory: str) -> str | None:
    """The new PATH value, or None when nothing needs to change."""
    if already_listed(current, directory):
        return None
    if not current:
        return directory
    return current.rstrip(os.pathsep) + os.pathsep + directory


def broadcast_environment_change() -> None:
    """Tell running programs the environment changed, so new shells pick it up."""
    import ctypes
    from ctypes import wintypes

    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002

    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPCWSTR,
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(wintypes.DWORD),
    ]
    result = wintypes.DWORD()
    send(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
         SMTO_ABORTIFHUNG, 5000, ctypes.byref(result))


def add_to_user_path(directory: str, key_name: str = "Environment") -> bool:
    """Append `directory` to the current user's PATH. True when it was added.

    Writes through the registry rather than setx, which silently truncates a
    PATH longer than 1024 characters, and preserves the value's existing type,
    so a REG_EXPAND_SZ PATH keeps working with its %VAR% entries intact.
    """
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name, 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, value_type = "", winreg.REG_EXPAND_SZ

        updated = path_after_adding(current, directory)
        if updated is None:
            return False

        winreg.SetValueEx(key, "Path", 0, value_type, updated)

    broadcast_environment_change()
    return True


def main() -> int:
    soffice = find_soffice()
    if not soffice:
        print("SKIPPED: LibreOffice was not found, so there is nothing to add to PATH.")
        return 1

    directory = os.path.dirname(os.path.abspath(soffice))

    if sys.platform != "win32":
        print(f"SKIPPED: not Windows. Your package manager already put {soffice} on PATH.")
        return 0

    try:
        added = add_to_user_path(directory)
    except OSError as exc:
        print(f"FAILED: could not update the user PATH: {exc}")
        print(f"  Add this directory yourself, under Settings > Environment Variables:")
        print(f"    {directory}")
        return 1

    if added:
        print(f"ADDED to your user PATH: {directory}")
        print("  Open a new terminal for it to take effect. Terminals already running")
        print("  keep their old PATH until they are restarted.")
    else:
        print(f"ALREADY on your user PATH: {directory}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
