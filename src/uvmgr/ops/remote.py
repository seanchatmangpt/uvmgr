from __future__ import annotations

from uvmgr.core.shell import timed


@timed
def run(host: str, cmd: str):
    from uvmgr.runtime import remote as _rt

    _rt.run(host, cmd)
