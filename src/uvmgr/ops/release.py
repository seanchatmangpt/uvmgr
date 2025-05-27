from __future__ import annotations

from uvmgr.core.shell import timed
from uvmgr.runtime import release as _rt


@timed
def bump() -> dict:
    _rt.bump()
    return {"version": "bumped"}


@timed
def changelog() -> str:
    return _rt.changelog()
