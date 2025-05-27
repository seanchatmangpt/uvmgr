import typer

from uvmgr.core.shell import colour
from uvmgr.ops import release as rel_ops

from .. import main as cli_root

rel_app = typer.Typer(help="Release helpers (Commitizen)")
cli_root.app.add_typer(rel_app, name="release")


@rel_app.command("bump")
def _bump():
    rel_ops.bump()
    colour("✔ version bumped", "green")


@rel_app.command("changelog")
def _changelog():
    print(rel_ops.changelog())
