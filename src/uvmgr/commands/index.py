import typer

from uvmgr.core.shell import colour
from uvmgr.ops import indexes as idx_ops

from .. import main as cli_root

idx_app = typer.Typer(help="Extra package indexes")
cli_root.app.add_typer(idx_app, name="index")


@idx_app.command("add")
def _add(url: str):
    idx_ops.add(url)
    colour(f"✔ added {url}", "green")


@idx_app.command("list")
def _list():
    for line in idx_ops.list_indexes():
        colour(line, "cyan")
