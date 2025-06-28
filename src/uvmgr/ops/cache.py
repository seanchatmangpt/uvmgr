"""
uvmgr.ops.cache
---------------
User-facing wrapper around `uv cache` commands.
"""

from __future__ import annotations

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.runtime.uv import call as uv_call


@timed
def dir() -> str:
    with span("cache.dir"):
        return uv_call("cache dir", capture=True) or ""


@timed
def prune() -> None:
    with span("cache.prune"):
        uv_call("cache prune")
