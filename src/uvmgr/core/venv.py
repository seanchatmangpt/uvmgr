"""
uvmgr.core.venv – venv inspection & smart cmd rewrite.

Enhanced with comprehensive OpenTelemetry instrumentation for virtual environment operations monitoring.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
import time
from collections.abc import Iterable

from .instrumentation import add_span_attributes, add_span_event
from .paths import bin_dir
from .telemetry import metric_counter, metric_histogram, span

__all__ = [
    "adapt_cmd",
    "is_py_file",
    "is_python_exec",
    "is_venv",
    "prepend_env_path",
]

_PY = re.compile(r"python(\d(\.\d+)?)?$")


def is_venv() -> bool:
    """Check if running in virtual environment with telemetry."""
    with span("venv.is_venv"):
        result = sys.prefix != sys.base_prefix

        metric_counter("venv.is_venv.calls")(1)
        metric_counter("venv.is_venv.in_venv" if result else "venv.is_venv.not_in_venv")(1)

        add_span_attributes(**{
            "venv.in_venv": result,
            "venv.prefix": sys.prefix,
            "venv.base_prefix": sys.base_prefix,
        })

        add_span_event("venv.is_venv.checked", {
            "in_venv": result,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
        })

        return result


def is_python_exec(tok: str) -> bool:
    """Check if token is a Python executable with telemetry."""
    result = bool(_PY.fullmatch(tok))
    metric_counter("venv.is_python_exec.calls")(1)
    metric_counter("venv.is_python_exec.matches" if result else "venv.is_python_exec.no_matches")(1)
    return result


def is_py_file(tok: str) -> bool:
    """Check if token is a Python file with telemetry."""
    result = tok.endswith(".py")
    metric_counter("venv.is_py_file.calls")(1)
    metric_counter("venv.is_py_file.matches" if result else "venv.is_py_file.no_matches")(1)
    return result


def prepend_env_path(cmd: str) -> str:
    """Prepend environment PATH with telemetry tracking."""
    with span("venv.prepend_env_path", command=cmd):
        result = f"env PATH={bin_dir()}:{os.getenv('PATH', '')} {cmd}"

        metric_counter("venv.prepend_env_path.calls")(1)

        add_span_event("venv.prepend_env_path.completed", {
            "original_cmd": cmd,
            "modified_cmd": result,
        })

        return result


def adapt_cmd(cmd: str | Iterable[str]) -> str:
    """Adapt command for virtual environment with comprehensive telemetry."""
    with span("venv.adapt_cmd", command=str(cmd)):
        start_time = time.time()
        original_cmd = str(cmd)

        if isinstance(cmd, (list, tuple)):
            cmd = " ".join(cmd)
        toks = shlex.split(cmd)
        head = toks[0]

        # Determine adaptation strategy
        adaptation_type = "none"
        if head in {"uv", "uvx", "uvmgr"}:
            result = cmd
            adaptation_type = "uvmgr_passthrough"
        elif is_python_exec(head):
            result = f"uv run -- {cmd}"
            adaptation_type = "python_exec"
        elif is_py_file(head):
            result = f"uv run -- python {cmd}"
            adaptation_type = "python_file"
        elif (bin_dir() / head).exists():
            result = prepend_env_path(cmd)
            adaptation_type = "bin_dir_exec"
        else:
            result = cmd
            adaptation_type = "no_adaptation"

        duration = time.time() - start_time

        # Record metrics
        metric_counter("venv.adapt_cmd.calls")(1)
        metric_counter(f"venv.adapt_cmd.{adaptation_type}")(1)
        metric_histogram("venv.adapt_cmd.duration")(duration)

        add_span_attributes(**{
            "venv.original_cmd": original_cmd,
            "venv.adapted_cmd": result,
            "venv.adaptation_type": adaptation_type,
            "venv.command_head": head,
            "venv.token_count": len(toks),
            "venv.duration": duration,
        })

        add_span_event("venv.adapt_cmd.completed", {
            "original": original_cmd,
            "adapted": result,
            "type": adaptation_type,
            "head": head,
            "duration": duration,
        })

        return result
