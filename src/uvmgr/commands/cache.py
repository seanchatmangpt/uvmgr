import typer

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CacheAttributes
from uvmgr.core.shell import colour
from uvmgr.ops import cache as cache_ops

from .. import main as cli_root

cache_app = typer.Typer(help="Manage uv cache")
cli_root.app.add_typer(cache_app, name="cache")


@cache_app.command("dir")
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


@cache_app.command("prune")
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
