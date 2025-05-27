import typer

from uvmgr.core.shell import colour
from uvmgr.ops import cache as cache_ops

from .. import main as cli_root

cache_app = typer.Typer(help="Manage uv cache")
cli_root.app.add_typer(cache_app, name="cache")


@cache_app.command("dir")
def _dir():
    colour(cache_ops.dir(), "cyan")


@cache_app.command("prune")
def _prune():
    cache_ops.prune()
    colour("✔ cache pruned", "green")
