"""
uvmgr.core.clipboard – thin wrapper, optional dependency.

Enhanced with OpenTelemetry instrumentation for clipboard operations monitoring.
"""

from __future__ import annotations

try:
    import pyperclip
except ImportError:
    pyperclip = None

from .instrumentation import add_span_event
from .telemetry import metric_counter, span


def read_clipboard() -> str:
    """Read clipboard content with telemetry tracking."""
    with span("clipboard.read", has_pyperclip=pyperclip is not None):
        metric_counter("clipboard.read.calls")(1)

        if pyperclip:
            result = pyperclip.paste()
            metric_counter("clipboard.read.success")(1)

            add_span_event("clipboard.read.success", {
                "content_length": len(result),
                "has_content": bool(result),
            })
            return result
        metric_counter("clipboard.read.unavailable")(1)
        add_span_event("clipboard.read.unavailable", {"reason": "pyperclip not installed"})
        return ""


def write_clipboard(text: str) -> None:
    """Write text to clipboard with telemetry tracking."""
    with span("clipboard.write", text_length=len(text), has_pyperclip=pyperclip is not None):
        metric_counter("clipboard.write.calls")(1)

        if pyperclip:
            pyperclip.copy(text)
            metric_counter("clipboard.write.success")(1)

            add_span_event("clipboard.write.success", {
                "text_length": len(text),
                "has_content": bool(text),
            })
        else:
            metric_counter("clipboard.write.unavailable")(1)
            add_span_event("clipboard.write.unavailable", {"reason": "pyperclip not installed"})
