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
from pathlib import Path

from uvmgr.core.config import env_or
from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span
from uvmgr.core.metrics import package_metrics, OperationResult
from uvmgr.core.semconv import PackageAttributes
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
import time

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


def call(sub_cmd: str, *, capture: bool = False, cwd: Path | None = None) -> str | None:
    """
    Execute `uv <sub_cmd>` and return stdout if *capture* is True.

    Examples
    --------
    >>> call("add fastapi ruff")  # doctest: +ELLIPSIS
    $ uv add fastapi ruff
    """
    cmd = ["uv"] + shlex.split(sub_cmd) + _extra_flags()
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
            flags = "--dev" if dev else ""
            call(f"add {flags} {' '.join(pkgs)}")
            
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
            call(f"remove {' '.join(pkgs)}")
            
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
            call("upgrade --all")
        elif pkgs:
            call(f"upgrade {' '.join(pkgs)}")


def list_pkgs() -> str:
    """
    Return `uv list` output (one package per line) as **plain text**.
    The ops layer will turn it into a Python list.
    """
    with span("uv.list"):
        return call("list", capture=True) or ""
