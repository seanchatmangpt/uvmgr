"""
uvmgr.runtime.uv
================
Thin, opinionated wrapper around the **uv** command-line tool.

Responsibilities
----------------
* Build the final shell command (`["uv", …]`) with global flags.
* Delegate execution to `core.process.run_logged`, which:
  – prints colourised `$ cmd`,
  – respects UVMGR_DRY / UVMGR_QUIET,
  – records an OpenTelemetry span.
* Offer convenience helpers (`add()`, `remove()`, …) used by `ops.deps`.
No business logic lives here – that belongs in the *ops* layer.
"""

from __future__ import annotations

import logging
import shlex
import time
from pathlib import Path

from uvmgr.core.config import env_or
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.metrics import OperationResult, package_metrics
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import PackageAttributes
from uvmgr.core.telemetry import span

_log = logging.getLogger("uvmgr.runtime.uv")


# --------------------------------------------------------------------------- #
# Low-level executor
# --------------------------------------------------------------------------- #
def _extra_flags() -> list[str]:
    """
    Compose global flags that should apply to **every** uv invocation
    (read from env vars so CI can tweak behaviour).
    """
    flags: list[str] = []
    if env_or("UV_OFFLINE") == "1":
        flags.append("--offline")
    if url := env_or("UV_EXTRA_INDEX"):
        flags += ["--extra-index-url", url]
    return flags


def call(sub_cmd: str | list[str], *, capture: bool = False, cwd: Path | None = None) -> str | None:
    """
    Execute `uv <sub_cmd>` and return stdout if *capture* is True.

    Args:
        sub_cmd: Command as string (for backward compat) or list (preferred for safety).
                 Lists are passed directly to subprocess without parsing.
        capture: If True, return stdout; otherwise return None.
        cwd: Working directory for the command.

    Examples
    --------
    >>> call("pip list", capture=True)  # OK - simple read-only command
    $ uv pip list

    >>> call(["add", "fastapi", "ruff"])  # Preferred - safe from injection
    $ uv add fastapi ruff
    """
    # Convert to list if string (for backward compatibility with read-only commands)
    if isinstance(sub_cmd, str):
        # Only allow string for safe, read-only commands with no user input
        # New code should use list-based calls
        cmd = ["uv"] + shlex.split(sub_cmd) + _extra_flags()
    else:
        # List-based call - SAFE, no shell parsing
        cmd = ["uv"] + sub_cmd + _extra_flags()

    _log.debug("uv call: %s", cmd)
    with span("uv.call", cmd=" ".join(cmd)):
        return run_logged(cmd, capture=capture, cwd=cwd)


# --------------------------------------------------------------------------- #
# High-level helpers – used by ops.deps
# --------------------------------------------------------------------------- #
def add(pkgs: list[str], *, dev: bool = False) -> None:
    start_time = time.time()

    with span("uv.add", pkgs=" ".join(pkgs), dev=dev):
        add_span_attributes(**{
            PackageAttributes.OPERATION: "add",
            PackageAttributes.DEV_DEPENDENCY: dev,
            "package.count": len(pkgs),
        })
        add_span_event("uv.add.started", {"packages": pkgs, "dev": dev})

        try:
            # Build command as list - SAFE from injection
            cmd = ["add"]
            if dev:
                cmd.append("--dev")
            cmd.extend(pkgs)
            call(cmd)

            # Record successful metrics for each package
            duration = time.time() - start_time
            for pkg in pkgs:
                result = OperationResult(success=True, duration=duration)
                package_metrics.record_add(pkg, None, dev, result)

            add_span_event("uv.add.completed", {"packages": pkgs, "success": True})

        except Exception as e:
            # Record failed metrics for each package
            duration = time.time() - start_time
            for pkg in pkgs:
                result = OperationResult(success=False, duration=duration, error=e)
                package_metrics.record_add(pkg, None, dev, result)

            add_span_event("uv.add.failed", {"error": str(e), "packages": pkgs})
            raise


def remove(pkgs: list[str]) -> None:
    start_time = time.time()

    with span("uv.remove", pkgs=" ".join(pkgs)):
        add_span_attributes(**{
            PackageAttributes.OPERATION: "remove",
            "package.count": len(pkgs),
        })
        add_span_event("uv.remove.started", {"packages": pkgs})

        try:
            # Build command as list - SAFE from injection
            cmd = ["remove"] + pkgs
            call(cmd)

            # Record successful metrics for each package
            duration = time.time() - start_time
            for pkg in pkgs:
                result = OperationResult(success=True, duration=duration)
                package_metrics.record_remove(pkg, result)

            add_span_event("uv.remove.completed", {"packages": pkgs, "success": True})

        except Exception as e:
            # Record failed metrics for each package
            duration = time.time() - start_time
            for pkg in pkgs:
                result = OperationResult(success=False, duration=duration, error=e)
                package_metrics.record_remove(pkg, result)

            add_span_event("uv.remove.failed", {"error": str(e), "packages": pkgs})
            raise


def upgrade(*, all_pkgs: bool = False, pkgs: list[str] | None = None) -> None:
    with span("uv.upgrade", all=all_pkgs, pkgs=pkgs or []):
        if all_pkgs:
            call(["upgrade", "--all"])
        elif pkgs:
            # Build command as list - SAFE from injection
            cmd = ["upgrade"] + pkgs
            call(cmd)


def list_pkgs() -> str:
    """
    Return `uv pip list` output (one package per line) as **plain text**.
    The ops layer will turn it into a Python list.
    """
    with span("uv.pip_list"):
        return call("pip list", capture=True) or ""
