"""
uvmgr.core.clipboard - Clipboard Operations
==========================================

Thin wrapper for clipboard operations with optional dependency support.

This module provides a simple interface for reading from and writing to the
system clipboard, with graceful handling of missing dependencies and
comprehensive OpenTelemetry instrumentation.

Key Features
-----------
• **Optional Dependency**: Graceful handling when pyperclip is not installed
• **Cross-platform**: Works on Windows, macOS, and Linux
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Error Handling**: Comprehensive error tracking and metrics
• **Content Monitoring**: Track clipboard content length and availability

Available Functions
------------------
- **read_clipboard()**: Read content from system clipboard
- **write_clipboard()**: Write text to system clipboard

Dependencies
-----------
- **pyperclip**: Optional dependency for clipboard access
  - Install with: `pip install pyperclip`
  - Functions return empty string/do nothing if not available

Examples
--------
    >>> from uvmgr.core.clipboard import read_clipboard, write_clipboard
    >>> 
    >>> # Read from clipboard
    >>> content = read_clipboard()
    >>> 
    >>> # Write to clipboard
    >>> write_clipboard("Hello, World!")

Notes
-----
If pyperclip is not installed, read_clipboard() returns an empty string
and write_clipboard() does nothing, but both operations are still tracked
in telemetry for monitoring dependency usage.

See Also
--------
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
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
