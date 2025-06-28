"""
uvmgr.core.process – thin subprocess wrapper with DRY/QUIET flags.

Enhanced with comprehensive OpenTelemetry instrumentation for process execution monitoring.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path

from .instrumentation import add_span_attributes, add_span_event
from .semconv import ProcessAttributes
from .shell import colour
from .telemetry import metric_counter, metric_histogram, span

__all__ = ["run", "run_logged", "which"]

_log = logging.getLogger("uvmgr.process")


def _to_str(cmd: str | Sequence[str]) -> str:
    return cmd if isinstance(cmd, str) else " ".join(cmd)


def run(cmd: str | Sequence[str], *, capture: bool = False, cwd: Path | None = None) -> str | None:
    """Execute a command with comprehensive OTEL instrumentation."""
    cmd_str = _to_str(cmd)
    start_time = time.time()

    # Handle dry run mode
    if os.getenv("UVMGR_DRY") == "1":
        colour(f"[dry] {cmd_str}", "yellow")
        metric_counter("process.dry_runs")(1)
        return ""

    kw = dict(cwd=str(cwd) if cwd else None, text=True)
    if capture or os.getenv("UVMGR_QUIET"):
        kw |= dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    with span(
        "process.execution",
        **{
            ProcessAttributes.COMMAND: cmd_str,
            ProcessAttributes.WORKING_DIRECTORY: str(cwd) if cwd else os.getcwd(),
            "process.capture": capture,
            "process.quiet": bool(os.getenv("UVMGR_QUIET")),
        }
    ):
        add_span_event("process.starting", {
            "command": cmd_str,
            "working_directory": str(cwd) if cwd else os.getcwd(),
            "capture_output": capture,
        })

        try:
            res = subprocess.run(shlex.split(cmd_str), check=True, **kw)

            duration = time.time() - start_time

            # Record success metrics
            metric_counter("process.executions.success")(1)
            metric_histogram("process.execution.duration")(duration)

            add_span_attributes(**{
                ProcessAttributes.EXIT_CODE: res.returncode,
                ProcessAttributes.DURATION: duration,
            })

            add_span_event("process.completed", {
                "exit_code": res.returncode,
                "duration": duration,
                "output_captured": bool(res.stdout),
            })

            return res.stdout if capture else None

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time

            # Record failure metrics
            metric_counter("process.executions.failed")(1)
            metric_histogram("process.execution.duration")(duration)

            add_span_attributes(**{
                ProcessAttributes.EXIT_CODE: e.returncode,
                ProcessAttributes.DURATION: duration,
            })

            add_span_event("process.failed", {
                "exit_code": e.returncode,
                "duration": duration,
                "error": str(e),
            })

            # Re-raise the exception
            raise

        except Exception as e:
            duration = time.time() - start_time

            metric_counter("process.executions.error")(1)

            add_span_event("process.error", {
                "duration": duration,
                "error": str(e),
                "error_type": type(e).__name__,
            })

            raise


def run_logged(cmd: str | Sequence[str], **kw):
    """Execute a command with logging and telemetry."""
    cmd_str = _to_str(cmd)

    with span("process.logged_execution", command=cmd_str):
        colour(f"$ {cmd_str}", "cyan")

        add_span_event("process.logged.starting", {"command": cmd_str})
        metric_counter("process.logged_executions")(1)

        try:
            result = run(cmd, **kw)

            add_span_event("process.logged.completed", {"command": cmd_str})
            return result

        except Exception as e:
            add_span_event("process.logged.failed", {
                "command": cmd_str,
                "error": str(e),
            })
            raise


def which(binary: str) -> str | None:
    """Find executable in PATH with telemetry tracking."""
    import shutil

    with span("process.which", binary=binary):
        add_span_event("process.which.starting", {"binary": binary})

        result = shutil.which(binary)

        # Record metrics
        if result:
            metric_counter("process.which.found")(1)
            add_span_attributes(
                executable_path=result,
                binary_found=True,
            )
            add_span_event("process.which.found", {
                "binary": binary,
                "path": result,
            })
        else:
            metric_counter("process.which.not_found")(1)
            add_span_attributes(binary_found=False)
            add_span_event("process.which.not_found", {"binary": binary})

        return result
