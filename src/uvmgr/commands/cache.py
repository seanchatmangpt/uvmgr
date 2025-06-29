"""
uvmgr.commands.cache - Cache Management
=====================================

Manage uv cache operations and maintenance.

This module provides CLI commands for managing the uv package cache,
including viewing cache location and pruning unused cache entries.
All operations are instrumented with OpenTelemetry for monitoring
cache usage and performance.

Key Features
-----------
• **Cache Location**: View uv cache directory location
• **Cache Pruning**: Remove unused cache entries
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Performance Monitoring**: Track cache operations and usage

Available Commands
-----------------
- **dir**: Display uv cache directory location
- **prune**: Remove unused cache entries to free space

Examples
--------
    >>> # View cache directory
    >>> uvmgr cache dir
    >>> 
    >>> # Prune unused cache entries
    >>> uvmgr cache prune

See Also
--------
- :mod:`uvmgr.ops.cache` : Cache operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CacheAttributes
from uvmgr.core.shell import colour
from uvmgr.ops import cache as cache_ops

app = typer.Typer(help="Manage uv cache")


@app.command("dir")
@instrument_command("cache_dir", track_args=True)
def _dir():
    # Track cache dir operation
    add_span_attributes(
        **{
            CacheAttributes.OPERATION: "dir",
        }
    )
    add_span_event("cache.dir.started")

    cache_dir = cache_ops.dir()
    add_span_attributes(**{"cache.directory": cache_dir})
    add_span_event("cache.dir.completed", {"directory": cache_dir})
    colour(cache_dir, "cyan")


@app.command("prune")
@instrument_command("cache_prune", track_args=True)
def _prune():
    # Track cache prune operation
    add_span_attributes(
        **{
            CacheAttributes.OPERATION: "prune",
        }
    )
    add_span_event("cache.prune.started")

    cache_ops.prune()
    add_span_event("cache.prune.completed", {"success": True})
    colour("✔ cache pruned", "green")
