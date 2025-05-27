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
from typing import List

from uvmgr.core.config import env_or
from uvmgr.core.process import run_logged
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span

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
    flags = "--dev" if dev else ""
    call(f"add {flags} {' '.join(pkgs)}")


def remove(pkgs: list[str]) -> None:
    call(f"remove {' '.join(pkgs)}")


def upgrade(*, all_pkgs: bool = False, pkgs: list[str] | None = None) -> None:
    if all_pkgs:
        call("upgrade --all")
    elif pkgs:
        call(f"upgrade {' '.join(pkgs)}")


def list_pkgs() -> str:
    """
    Return `uv list` output (one package per line) as **plain text**.
    The ops layer will turn it into a Python list.
    """
    return call("list", capture=True) or ""
