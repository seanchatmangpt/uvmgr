from __future__ import annotations

import logging
from pathlib import Path

from uvmgr.core.shell import timed
from uvmgr.runtime import project as _rt

_log = logging.getLogger("uvmgr.ops.project")


@timed
def new(name: str, *, fastapi: bool = False, typer_cli: bool = True) -> dict:
    dest = Path(name).resolve()
    if dest.exists():
        raise FileExistsError(dest)
    _rt.scaffold(dest, fastapi=fastapi, typer_cli=typer_cli)
    _log.info("Project scaffolded at %s", dest)
    return {"path": str(dest)}
