import pathlib

import typer

from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import build as build_ops

from .. import main as cli_root

build_app = typer.Typer(help="Build wheel + sdist")
cli_root.app.add_typer(build_app, name="build")


@build_app.command()
def dist(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    upload: bool = typer.Option(False, "--upload", help="Twine upload after build"),
):
    payload = build_ops.dist(outdir)
    if upload:
        build_ops.upload(outdir or pathlib.Path("dist"))
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour("✔ build completed", "green")
