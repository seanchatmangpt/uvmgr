"""
uvmgr.core.clipboard – thin wrapper, optional dependency.
"""

from __future__ import annotations

try:
    import pyperclip
except ImportError:
    pyperclip = None


def read_clipboard() -> str:
    return pyperclip.paste() if pyperclip else ""


def write_clipboard(text: str) -> None:
    if pyperclip:
        pyperclip.copy(text)
