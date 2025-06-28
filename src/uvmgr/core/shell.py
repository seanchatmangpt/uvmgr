"""
uvmgr.core.shell
================

Utility helpers that wrap **Rich** so every layer of *uvmgr* can print
pretty output without repeating boiler-plate.

• `colour(text, style)`     – one-liner style wrapper
• `dump_json(obj)`          – syntax-highlighted JSON
• `markdown(md)`            – render Markdown with headings, lists, etc.
• `rich_table(headers, rows)` – quick table helper
• `progress_bar(total)`     – context-manager for a progress bar
• `timed(fn)`               – decorator that times a call and prints ✔ …s
• `install_rich()`          – enable Rich tracebacks

All functions follow the *happy-path only* rule: no error handling, no
return values unless useful.
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from typing import Any

from rich.console import Console
from rich.json import JSON as RichJSON
from rich.markdown import Markdown
from rich.progress import Progress
from rich.table import Table
from rich.traceback import install as _install_tb

__all__ = [
    "colour",
    "colour_stderr",
    "dump_json",
    "install_rich",
    "markdown",
    "progress_bar",
    "rich_table",
    "timed",
]

# One global console instance – reuse it everywhere
_console = Console(highlight=False)
# Console for stderr output (for MCP servers)
_console_stderr = Console(highlight=False, file=sys.stderr)


# --------------------------------------------------------------------------- #
# Core helpers
# --------------------------------------------------------------------------- #
def install_rich(show_locals: bool = False) -> None:
    """Activate Rich tracebacks (call once, idempotent)."""
    _install_tb(show_locals=show_locals)


def colour(text: str, style: str = "green", *, nl: bool = True) -> None:
    """Print *text* in *style* colour (defaults to green)."""
    _console.print(text, style=style, end="\n" if nl else "")


def colour_stderr(text: str, style: str = "green", *, nl: bool = True) -> None:
    """Print *text* in *style* colour to stderr (for MCP servers)."""
    _console_stderr.print(text, style=style, end="\n" if nl else "")


def dump_json(obj: Any) -> None:
    """Pretty-print a Python object as syntax-highlighted JSON."""
    _console.print(RichJSON(json.dumps(obj, default=str, indent=2)))


def markdown(md: str) -> None:
    """Render Markdown *md* via Rich (headings, lists, code blocks…)."""
    _console.print(Markdown(md))


def timed(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator: run *fn*, then print “✔ fn_name 1.23s” in green.

    Usage
    -----
    @timed
    def build():
        ...
    """

    @wraps(fn)
    def _wrap(*a, **kw):
        t0 = time.perf_counter()
        try:
            return fn(*a, **kw)
        finally:
            colour(f"✔ {fn.__name__} {(time.perf_counter() - t0):.2f}s", "green")

    return _wrap


# --------------------------------------------------------------------------- #
# Rich convenience wrappers
# --------------------------------------------------------------------------- #
def rich_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    """Quickly render a table given *headers* and an iterable of *rows*."""
    t = Table(*headers, header_style="bold magenta")
    for r in rows:
        t.add_row(*map(str, r))
    _console.print(t)


def progress_bar(total: int):
    """
    Context-manager yielding a callable *advance()* that increments the bar.

    Example
    -------
    with progress_bar(10) as advance:
        for _ in range(10):
            work()
            advance()
    """

    class _Ctx:
        def __enter__(self):
            self._p = Progress()
            self._p.__enter__()
            self._task = self._p.add_task("work", total=total)
            return lambda inc=1: self._p.update(self._task, advance=inc)

        def __exit__(self, exc_type, exc, tb):
            return self._p.__exit__(exc_type, exc, tb)

    return _Ctx()
