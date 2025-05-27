from __future__ import annotations

import shlex
from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span

TEMPLATE = "gh:superlinear-ai/substrate"


def scaffold(dest: Path, *, fastapi: bool = False, typer_cli: bool = True) -> None:
    """
    Run Copier to scaffold a new project into *dest* directory.

    Flags map to the Substrate template questions.
    """
    args = [
        "copier",
        "copy",
        "--overwrite",
        "--not-planned",
        "-d", f"with_fastapi_api={int(fastapi)}",
        "-d", f"with_typer_cli={int(typer_cli)}",
        TEMPLATE,
        str(dest),
    ]
    with span("project.scaffold", dest=str(dest)):
        run_logged(args)
