import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ReleaseAttributes, ReleaseOperations
from uvmgr.core.shell import colour
from uvmgr.ops import release as rel_ops

from .. import main as cli_root

rel_app = typer.Typer(help="Release helpers (Commitizen)")
cli_root.app.add_typer(rel_app, name="release")


@rel_app.command("bump")
@instrument_command("release_bump", track_args=True)
def _bump():
    rel_ops.bump()
    colour("✔ version bumped", "green")


@rel_app.command("changelog")
@instrument_command("release_changelog", track_args=True)
def _changelog():
    print(rel_ops.changelog())
