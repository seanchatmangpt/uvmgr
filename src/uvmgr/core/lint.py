"""
uvmgr.core.lint - Code Quality and Linting Utilities
==================================================

Local quality gate helpers with comprehensive telemetry instrumentation.

This module provides utilities for enforcing code quality standards using
Ruff linting and mapping exceptions to appropriate exit codes for
consistent error handling across the application.

Key Features
-----------
• **Ruff Integration**: Enforce code quality using Ruff linter
• **Exception Mapping**: Consistent exit code mapping for different exception types
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Performance Monitoring**: Duration tracking for linting operations
• **Quality Gates**: Automated code quality enforcement

Available Functions
------------------
- **enforce_ruff()**: Run Ruff linting with quality gate enforcement
- **map_exception()**: Map exceptions to standardized exit codes

Exception Mapping
----------------
- **FileNotFoundError**: Exit code 3
- **KeyError**: Exit code 4
- **ValueError**: Exit code 5
- **Other exceptions**: Exit code 1 (default)

Examples
--------
    >>> from uvmgr.core.lint import enforce_ruff, map_exception
    >>> 
    >>> # Enforce code quality
    >>> try:
    >>>     enforce_ruff("src/")
    >>> except SystemExit:
    >>>     print("Linting failed")
    >>> 
    >>> # Map exception to exit code
    >>> try:
    >>>     # ... some operation
    >>>     pass
    >>> except Exception as e:
    >>>     exit_code = map_exception(e)
    >>>     sys.exit(exit_code)

See Also
--------
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Mapping

from .instrumentation import add_span_attributes, add_span_event
from .telemetry import metric_counter, metric_histogram, span

__all__ = ["enforce_ruff", "map_exception"]

_EXIT: Mapping[type[BaseException], int] = {
    FileNotFoundError: 3,
    KeyError: 4,
    ValueError: 5,
}


def enforce_ruff(path: str | None = ".") -> None:
    """Enforce Ruff linting with comprehensive telemetry."""
    with span("lint.enforce_ruff", path=str(path)):
        start_time = time.time()
        path_str = str(path)

        add_span_event("lint.ruff.starting", {
            "path": path_str,
            "command": ["ruff", "check", "--quiet", path_str]
        })

        # Run ruff check
        result = subprocess.run(["ruff", "check", "--quiet", path_str], check=False)
        returncode = result.returncode
        duration = time.time() - start_time

        # Record metrics
        metric_counter("lint.enforce_ruff.calls")(1)
        metric_histogram("lint.enforce_ruff.duration")(duration)

        if returncode == 0:
            metric_counter("lint.enforce_ruff.passed")(1)
            add_span_event("lint.ruff.passed", {
                "path": path_str,
                "duration": duration,
                "returncode": returncode
            })
        else:
            metric_counter("lint.enforce_ruff.failed")(1)
            add_span_event("lint.ruff.violations_found", {
                "path": path_str,
                "duration": duration,
                "returncode": returncode
            })

        add_span_attributes(**{
            "lint.path": path_str,
            "lint.returncode": returncode,
            "lint.duration": duration,
            "lint.passed": returncode == 0,
        })

        if returncode:
            add_span_event("lint.ruff.exit", {
                "path": path_str,
                "returncode": returncode,
                "message": "❌ Ruff violations."
            })
            sys.exit("❌ Ruff violations.")


def map_exception(exc: BaseException) -> int:
    """Map exception to exit code with telemetry."""
    with span("lint.map_exception", exception_type=type(exc).__name__):
        exc_type = type(exc)
        exc_name = exc_type.__name__

        for et, code in _EXIT.items():
            if isinstance(exc, et):
                metric_counter("lint.map_exception.mapped")(1)
                metric_counter(f"lint.map_exception.{et.__name__}")(1)

                add_span_attributes(**{
                    "lint.exception_type": exc_name,
                    "lint.mapped_type": et.__name__,
                    "lint.exit_code": code,
                })

                add_span_event("lint.exception.mapped", {
                    "exception_type": exc_name,
                    "mapped_to": et.__name__,
                    "exit_code": code,
                    "exception_message": str(exc),
                })

                return code

        # Default case
        metric_counter("lint.map_exception.default")(1)
        metric_counter(f"lint.map_exception.unmapped_{exc_name}")(1)

        add_span_attributes(**{
            "lint.exception_type": exc_name,
            "lint.mapped_type": "default",
            "lint.exit_code": 1,
        })

        add_span_event("lint.exception.unmapped", {
            "exception_type": exc_name,
            "exit_code": 1,
            "exception_message": str(exc),
        })

        return 1
