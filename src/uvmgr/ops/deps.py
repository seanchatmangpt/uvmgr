"""
uvmgr.ops.deps
--------------
User-facing dependency orchestration (uv add / remove / upgrade / list).
"""

from __future__ import annotations

import logging
import time

from uvmgr.core.semconv import PackageAttributes, PackageOperations
from uvmgr.core.shell import timed
from uvmgr.core.telemetry import metric_counter, metric_histogram, span
from uvmgr.runtime import uv as _rt

_log = logging.getLogger("uvmgr.ops.deps")


@timed
def add(pkgs: list[str], *, dev: bool = False) -> dict:
    start_time = time.time()

    with span("deps.add",
              **{PackageAttributes.OPERATION: PackageOperations.ADD,
                 PackageAttributes.PACKAGE_NAME: " ".join(pkgs),
                 PackageAttributes.DEV_DEPENDENCY: dev,
                 "package.count": len(pkgs)}) as current_span:

        # Record operation start
        metric_counter("deps.operations")(1)

        try:
            _rt.add(pkgs, dev=dev)

            # Record success metrics
            duration = time.time() - start_time
            metric_histogram("deps.operation.duration")(duration)

            if current_span:
                current_span.set_attribute("operation.success", True)
                current_span.set_attribute("operation.duration", duration)

        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            metric_counter("deps.errors")(1)
            metric_histogram("deps.operation.duration")(duration)
            if current_span:
                current_span.set_attribute("operation.success", False)
                current_span.set_attribute("operation.error", str(e))
            raise

    _log.debug("Added %s (dev=%s)", pkgs, dev)
    return {"added": pkgs, "dev": dev}


@timed
def remove(pkgs: list[str]) -> dict:
    with span("deps.remove", pkgs=" ".join(pkgs)):
        _rt.remove(pkgs)
    _log.debug("Removed %s", pkgs)
    return {"removed": pkgs}


@timed
def upgrade(*, all_pkgs: bool = False, pkgs: list[str] | None = None) -> dict:
    with span("deps.upgrade", all=all_pkgs, pkgs=pkgs):
        _rt.upgrade(all_pkgs=all_pkgs, pkgs=pkgs)
    _log.debug("Upgraded %s", "all packages" if all_pkgs else pkgs)
    return {"upgraded": "all" if all_pkgs else pkgs}


@timed
def list_pkgs() -> list[str]:
    """Return the current dependency list as plain strings."""
    txt = _rt.list_pkgs()
    _log.debug("Listed %d packages", len(txt.splitlines()))
    return txt.splitlines()


@timed
def lock(*, verbose: bool = False) -> dict:
    """Generate or update the lock file."""
    start_time = time.time()
    
    with span("deps.lock", verbose=verbose) as current_span:
        # Record operation start
        metric_counter("deps.operations")(1)
        
        try:
            cmd = ["uv", "lock"]
            if verbose:
                cmd.append("--verbose")
            
            from uvmgr.core.process import run_logged
            result = run_logged(cmd, capture=True)
            
            # Record success metrics
            duration = time.time() - start_time
            metric_histogram("deps.operation.duration")(duration)
            
            if current_span:
                current_span.set_attribute("operation.success", True)
                current_span.set_attribute("operation.duration", duration)
            
            _log.debug("Locked dependencies successfully")
            return {
                "status": "success",
                "duration": duration,
                "output": result if verbose else None
            }
            
        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            metric_counter("deps.errors")(1)
            metric_histogram("deps.operation.duration")(duration)
            
            if current_span:
                current_span.set_attribute("operation.success", False)
                current_span.set_attribute("operation.error", str(e))
            
            _log.error("Failed to lock dependencies: %s", e)
            raise
