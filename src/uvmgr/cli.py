"""
uvmgr.cli
=========

Root Typer application.

• Sets up logging once (plain `logging` + optional OpenTelemetry)
• Adds a global `--json / -j` flag
• Dynamically mounts every sub-command package found in **uvmgr.commands**
"""

from __future__ import annotations

import importlib
import os
import sys

import typer

from uvmgr.cli_utils import handle_cli_exception
from uvmgr.logging_config import setup_logging
from uvmgr.core.instrumentation import instrument_command

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

# ──────────────────────────────────────────────────────────────────────────────
#  Logging bootstrap (idempotent)
# ──────────────────────────────────────────────────────────────────────────────
setup_logging()

# ──────────────────────────────────────────────────────────────────────────────
#  Root Typer application
# ──────────────────────────────────────────────────────────────────────────────
app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="**uvmgr** – unified Python workflow engine (powered by *uv*).",
    context_settings={"allow_extra_args": True},
)


# Record JSON preference in ctx.meta so sub-commands can honour it -------------
def _json_cb(ctx: typer.Context, value: bool):
    if value:
        ctx.meta["json"] = True


@app.callback()
@instrument_command("uvmgr_main", track_args=True)
def _root(
    ctx: typer.Context,
    json_: bool = typer.Option(
        False,
        "--json",
        "-j",
        callback=_json_cb,
        is_eager=True,
        help="Print machine-readable JSON and exit",
    ),
):
    """Callback only sets the JSON flag – no other side-effects."""


# ──────────────────────────────────────────────────────────────────────────────
#  Mount every sub-command defined in *uvmgr.commands*
# ──────────────────────────────────────────────────────────────────────────────
commands_pkg = importlib.import_module("uvmgr.commands")

for verb in commands_pkg.__all__:
    mod = importlib.import_module(f"uvmgr.commands.{verb}")

    # Expect exactly one typer.Typer object in the module's globals ------------
    sub_app = next(
        (obj for obj in mod.__dict__.values() if isinstance(obj, typer.Typer)),
        None,
    )
    if sub_app is None:  # Fail fast during development
        raise ImportError(f"`{verb}` has no Typer sub-app")

    # Mount under the same name (convert _ to - for nicer CLI UX) --------------
    app.add_typer(sub_app, name=verb.replace("_", "-"))


if __name__ == "__main__":
    import sys

    debug = "--debug" in sys.argv
    try:
        # ... main CLI logic ...
        pass
    except Exception as e:
        handle_cli_exception(e, debug=debug)
