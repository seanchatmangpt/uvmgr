from __future__ import annotations

from typing import List

from uvmgr.core.shell import timed
from uvmgr.runtime import poetask as _rt


@timed
def lint() -> None:
    _rt.exec_task("lint")


@timed
def test(extra: list[str] | None = None) -> None:
    _rt.exec_task("test", *(extra or []))


@timed
def serve(dev: bool = False, host: str = "0.0.0.0", port: str = "8000") -> None:
    args = ["--dev"] if dev else []
    args += ["--host", host, "--port", port]
    _rt.exec_task("api", *args)
