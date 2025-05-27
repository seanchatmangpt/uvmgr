from __future__ import annotations

def run(host: str, cmd: str):
    from uvmgr.runtime import remote as _rt
    _rt.run(host, cmd)
