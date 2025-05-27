from __future__ import annotations

from pathlib import Path
from typing import List

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.runtime.uv import call as uv_call


@timed
def run(pkg_and_args: list[str]) -> None:
    with span("tool.run", args=" ".join(pkg_and_args)):
        uv_call(f"tool run {' '.join(pkg_and_args)}")


@timed
def install(pkgs: list[str]) -> None:
    with span("tool.install", pkgs=" ".join(pkgs)):
        uv_call(f"tool install {' '.join(pkgs)}")


def tool_dir() -> str:
    return uv_call("tool dir", capture=True) or ""
