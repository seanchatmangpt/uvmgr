import logging
import sys
import traceback
from typing import Any

import typer

from uvmgr.core.shell import dump_json


def handle_cli_exception(e, debug=False, exit_code=1):
    logger = logging.getLogger("uvmgr.cli")
    logger.error(f"An error occurred: {e}")
    if debug:
        traceback.print_exc()
    sys.exit(exit_code)


def maybe_json(ctx: typer.Context, payload: Any, exit_code: int = 0) -> None:
    """
    Utility: in sub-commands call **maybe_json(ctx, data, exit_code)**; if the user
    passed --json we dump the object and exit early.
    """
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit(exit_code)
