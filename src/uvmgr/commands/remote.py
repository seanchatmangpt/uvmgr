import typer

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import RemoteAttributes, RemoteOperations
from uvmgr.ops import remote as remote_ops

from .. import main as cli_root

remote_app = typer.Typer(help="(stub) remote runner")
cli_root.app.add_typer(remote_app, name="remote")


@remote_app.command("run")
@instrument_command("remote_run", track_args=True)
def _run(host: str, cmd: str):
    remote_ops.run(host, cmd)
