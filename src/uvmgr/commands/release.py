"""
uvmgr.commands.release - Release Management
=========================================

Release helpers using Commitizen for version management.

This module provides CLI commands for managing project releases using
Commitizen, including version bumping and changelog generation.

Key Features
-----------
• **Version Bumping**: Automatic version increment using Commitizen
• **Changelog Generation**: Generate changelog from commit history
• **Commitizen Integration**: Standardized commit message processing
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **bump**: Bump version using Commitizen
- **changelog**: Generate changelog from commit history

Examples
--------
    >>> # Bump version
    >>> uvmgr release bump
    >>> 
    >>> # Generate changelog
    >>> uvmgr release changelog

See Also
--------
- :mod:`uvmgr.ops.release` : Release operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

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
