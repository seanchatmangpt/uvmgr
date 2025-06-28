"""
uvmgr.commands.index - Package Index Management
=============================================

Manage extra package indexes for uv package management.

This module provides CLI commands for managing additional package indexes
beyond the default PyPI, allowing access to private repositories and
alternative package sources.

Key Features
-----------
• **Index Management**: Add and list package indexes
• **Multiple Sources**: Support for private and alternative repositories
• **uv Integration**: Seamless integration with uv package manager
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **add**: Add a new package index URL
- **list**: List all configured package indexes

Examples
--------
    >>> # Add a private package index
    >>> uvmgr index add https://pypi.company.com/simple/
    >>> 
    >>> # List all indexes
    >>> uvmgr index list

See Also
--------
- :mod:`uvmgr.ops.indexes` : Index operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import IndexAttributes, IndexOperations
from uvmgr.core.shell import colour
from uvmgr.ops import indexes as idx_ops

from .. import main as cli_root

idx_app = typer.Typer(help="Extra package indexes")
cli_root.app.add_typer(idx_app, name="index")


@idx_app.command("add")
@instrument_command("index_add", track_args=True)
def _add(url: str):
    idx_ops.add(url)
    colour(f"✔ added {url}", "green")


@idx_app.command("list")
@instrument_command("index_list", track_args=True)
def _list():
    for line in idx_ops.list_indexes():
        colour(line, "cyan")
