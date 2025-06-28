"""
uvmgr.ops.deps
--------------
User-facing dependency orchestration (uv add / remove / upgrade / list).
"""

from __future__ import annotations

import logging
import time

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.core.semconv import PackageAttributes, PackageOperations
from uvmgr.runtime import uv as _rt

_log = logging.getLogger("uvmgr.ops.deps")


@timed
def add(pkgs: list[str], *, dev: bool = False) -> dict:
    start_time = time.time()
    
    with span("deps.add", 
              **{PackageAttributes.OPERATION: PackageOperations.ADD,
                 PackageAttributes.NAME: " ".join(pkgs),
                 PackageAttributes.DEV_DEPENDENCY: dev,
                 "package.count": len(pkgs)}) as current_span:
        
        # Record operation start
        metric_counter("deps.operations")(1, {
            "operation": "add",
            "dev": str(dev),
            "package_count": len(pkgs)
        })
        
        try:
            _rt.add(pkgs, dev=dev)
            
            # Record success metrics
            duration = time.time() - start_time
            metric_histogram("deps.operation.duration")(duration, {
                "operation": "add",
                "success": "true"
            })
            
            current_span.set_attribute("operation.success", True)
            current_span.set_attribute("operation.duration", duration)
            
        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            metric_counter("deps.errors")(1, {"operation": "add"})
            metric_histogram("deps.operation.duration")(duration, {
                "operation": "add", 
                "success": "false"
            })
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
