"""
uvmgr.commands.remote - Remote Execution
=====================================

Remote runner for executing commands on remote hosts.

This module provides CLI commands for executing commands on remote hosts,
enabling distributed development and deployment workflows.

Key Features
-----------
• **Remote Execution**: Execute commands on remote hosts
• **Host Management**: Support for multiple remote hosts
• **Command Execution**: Run arbitrary commands remotely
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **run**: Execute command on remote host

Examples
--------
    >>> # Execute command on remote host
    >>> uvmgr remote run hostname "python --version"

See Also
--------
- :mod:`uvmgr.ops.remote` : Remote operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import RemoteAttributes, RemoteOperations
from uvmgr.ops import remote as remote_ops

# Standard uvmgr command pattern
app = typer.Typer(help="Remote execution and management for distributed development")


@app.command("run")
@instrument_command("remote_run", track_args=True)
def _run(host: str, cmd: str):
    remote_ops.run(host, cmd)
