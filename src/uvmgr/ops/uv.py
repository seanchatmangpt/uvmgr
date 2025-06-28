"""
uvmgr.ops.uv
============
Thin orchestration wrapper around *runtime.uv*.

• Never spawns processes directly – delegates to `uvmgr.runtime.uv.call`
• Returns JSON-safe data so the CLI layer can decide how to display it
"""

from __future__ import annotations

from collections.abc import Sequence

from uvmgr.core.shell import timed
from uvmgr.runtime import uv as _rt


@timed
def call(args: str | Sequence[str], *, capture: bool = False) -> str | None:
    """
    Invoke the ``uv`` CLI inside the project's virtual-env.

    Parameters
    ----------
    args
        Either a single string (e.g. ``"pip list"``) or a list of tokens
        (e.g. ``["pip", "install", "-e", "."]``).
    capture
        When *True* the subprocess output is returned; otherwise it streams
        to the terminal.

    Returns
    -------
    str | None
        Captured stdout if *capture* is True, else **None**.
    """
    return _rt.call(args, capture=capture)
