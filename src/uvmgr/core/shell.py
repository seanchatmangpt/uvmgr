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

Enhanced with comprehensive OpenTelemetry instrumentation for shell operations monitoring.

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

from .instrumentation import add_span_attributes, add_span_event
from .telemetry import metric_counter, metric_histogram, span

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
    """Print *text* in *style* colour (defaults to green) with telemetry."""
    # Quick telemetry for high-frequency function
    metric_counter("shell.colour.calls")(1)
    metric_counter(f"shell.colour.style.{style}")(1)

    _console.print(text, style=style, end="\n" if nl else "")


def colour_stderr(text: str, style: str = "green", *, nl: bool = True) -> None:
    """Print *text* in *style* colour to stderr (for MCP servers)."""
    _console_stderr.print(text, style=style, end="\n" if nl else "")


def dump_json(obj: Any) -> None:
    """Pretty-print a Python object as syntax-highlighted JSON with telemetry."""
    with span("shell.dump_json", object_type=type(obj).__name__):
        start_time = time.time()

        try:
            json_str = json.dumps(obj, default=str, indent=2)
            json_size = len(json_str)

            _console.print(RichJSON(json_str))

            duration = time.time() - start_time

            # Record metrics
            metric_counter("shell.dump_json.calls")(1)
            metric_histogram("shell.dump_json.duration")(duration)
            metric_histogram("shell.dump_json.size_chars")(json_size)

            add_span_attributes(**{
                "shell.object_type": type(obj).__name__,
                "shell.json_size": json_size,
                "shell.duration": duration,
            })

        except Exception as e:
            metric_counter("shell.dump_json.failed")(1)

            add_span_event("shell.dump_json.failed", {
                "object_type": type(obj).__name__,
                "error": str(e),
            })
            raise


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
        with span(f"shell.timed.{fn.__name__}", function_name=fn.__name__):
            add_span_event("shell.timed.starting", {"function": fn.__name__})

            t0 = time.perf_counter()
            exception_occurred = False

            try:
                result = fn(*a, **kw)
                return result
            except Exception as e:
                exception_occurred = True

                add_span_event("shell.timed.exception", {
                    "function": fn.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__,
                })
                metric_counter(f"shell.timed.{fn.__name__}.failed")(1)
                raise
            finally:
                duration = time.perf_counter() - t0

                # Record metrics
                metric_counter(f"shell.timed.{fn.__name__}.calls")(1)
                metric_histogram(f"shell.timed.{fn.__name__}.duration")(duration)

                if not exception_occurred:
                    metric_counter(f"shell.timed.{fn.__name__}.completed")(1)

                add_span_attributes(**{
                    "shell.function_name": fn.__name__,
                    "shell.duration": duration,
                    "shell.exception_occurred": exception_occurred,
                })

                add_span_event("shell.timed.completed", {
                    "function": fn.__name__,
                    "duration": duration,
                    "success": not exception_occurred,
                })

                # Original display behavior
                colour(f"✔ {fn.__name__} {duration:.2f}s", "green")

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
    Enhanced with OTEL telemetry tracking.

    Example
    -------
    with progress_bar(10) as advance:
        for _ in range(10):
            work()
            advance()
    """

    class _Ctx:
        def __enter__(self):
            # Record progress bar creation
            metric_counter("shell.progress_bar.created")(1)
            metric_histogram("shell.progress_bar.total")(total)

            add_span_event("shell.progress_bar.created", {"total": total})

            self._p = Progress()
            self._p.__enter__()
            self._task = self._p.add_task("work", total=total)

            # Track advancement
            self._advances = 0
            self._start_time = time.time()

            def advance(inc=1):
                self._advances += inc
                metric_counter("shell.progress_bar.advances")(inc)

                # Record progress events periodically
                if self._advances % max(1, total // 10) == 0:
                    progress_pct = (self._advances / total) * 100 if total > 0 else 0
                    add_span_event("shell.progress_bar.progress", {
                        "advances": self._advances,
                        "total": total,
                        "progress_pct": progress_pct,
                    })

                return self._p.update(self._task, advance=inc)

            return advance

        def __exit__(self, exc_type, exc, tb):
            duration = time.time() - self._start_time

            # Record completion metrics
            metric_histogram("shell.progress_bar.duration")(duration)
            metric_counter("shell.progress_bar.completed")(1)

            completion_rate = (self._advances / total) * 100 if total > 0 else 0

            add_span_event("shell.progress_bar.completed", {
                "total": total,
                "advances": self._advances,
                "completion_rate": completion_rate,
                "duration": duration,
            })

            return self._p.__exit__(exc_type, exc, tb)

    return _Ctx()
