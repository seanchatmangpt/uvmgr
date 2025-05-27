"""
uvmgr.ops.deps
--------------
User-facing dependency orchestration (uv add / remove / upgrade / list).
"""

from __future__ import annotations

import logging
from typing import List

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.runtime import uv as _rt

_log = logging.getLogger("uvmgr.ops.deps")


@timed
def add(pkgs: List[str], *, dev: bool = False) -> dict:
    with span("deps.add", pkgs=" ".join(pkgs), dev=dev):
        _rt.add(pkgs, dev=dev)
    _log.debug("Added %s (dev=%s)", pkgs, dev)
    return {"added": pkgs, "dev": dev}


@timed
def remove(pkgs: List[str]) -> dict:
    with span("deps.remove", pkgs=" ".join(pkgs)):
        _rt.remove(pkgs)
    _log.debug("Removed %s", pkgs)
    return {"removed": pkgs}


@timed
def upgrade(*, all_pkgs: bool = False, pkgs: List[str] | None = None) -> dict:
    with span("deps.upgrade", all=all_pkgs, pkgs=pkgs):
        _rt.upgrade(all_pkgs=all_pkgs, pkgs=pkgs)
    _log.debug("Upgraded %s", "all packages" if all_pkgs else pkgs)
    return {"upgraded": "all" if all_pkgs else pkgs}


def list_pkgs() -> list[str]:
    """Return the current dependency list as plain strings."""
    txt = _rt.list_pkgs()
    _log.debug("Listed %d packages", len(txt.splitlines()))
    return txt.splitlines()
