"""
uvmgr.commands.deps
-------------------
Dependency management commands for uvmgr.

This module provides CLI commands for managing Python project dependencies using
the uv package manager. It includes commands for adding, removing, upgrading,
and listing dependencies with full OpenTelemetry instrumentation.

Commands
--------
- add : Add packages to the project
- remove : Remove packages from the project  
- upgrade : Upgrade packages to latest versions
- list : List installed packages

All commands automatically instrument with telemetry and provide both human-readable
and JSON output formats.

Example
-------
    $ uvmgr deps add requests pandas
    $ uvmgr deps add pytest --dev
    $ uvmgr deps remove numpy
    $ uvmgr deps upgrade --all
    $ uvmgr deps list

See Also
--------
- :mod:`uvmgr.ops.deps` : Core dependency operations
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import PackageAttributes, PackageOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import deps as deps_ops

app = typer.Typer(help="Dependency management (uv add/remove/upgrade)")


# --------------------------------------------------------------------------- #
# Shared util
# --------------------------------------------------------------------------- #
def _maybe_json(ctx: typer.Context, payload):
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit()


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
@app.command("add")
@instrument_command("deps_add", track_args=True)
def add(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(..., help="Packages e.g. fastapi requests"),
    dev: bool = typer.Option(False, "--dev", "-D", help="Add to dev group"),
):
    """
    Add packages to the project dependencies.
    
    This command adds one or more packages to the project's dependencies using
    the uv package manager. It automatically updates the pyproject.toml file
    and installs the packages in the project's virtual environment.
    
    Parameters
    ----------
    ctx : typer.Context
        Typer context for command execution.
    pkgs : list[str]
        List of package names to add. Can include version specifiers
        (e.g., "requests>=2.25.0", "pandas~=1.5.0").
    dev : bool, optional
        If True, add packages to the development dependencies group.
        Default is False (runtime dependencies).
    
    Notes
    -----
    The command automatically:
    - Resolves package dependencies
    - Updates pyproject.toml with new dependencies
    - Installs packages in the project's virtual environment
    - Records telemetry for the operation
    
    Example
    -------
    >>> # Add runtime dependencies
    >>> uvmgr deps add requests pandas
    >>> 
    >>> # Add development dependencies
    >>> uvmgr deps add pytest black --dev
    >>> 
    >>> # Add with version constraints
    >>> uvmgr deps add "fastapi>=0.100.0" "uvicorn[standard]"
    """
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.ADD,
            "package.count": len(pkgs),
            "package.names": ",".join(pkgs),
            PackageAttributes.DEV_DEPENDENCY: dev,
        }
    )

    res = deps_ops.add(pkgs, dev=dev)
    _maybe_json(ctx, res)
    colour(f"✔ added {' '.join(pkgs)}", "green")


@app.command("remove")
@instrument_command("deps_remove", track_args=True)
def remove(
    ctx: typer.Context,
    pkgs: list[str] = typer.Argument(...),
):
    """
    Remove packages from the project dependencies.
    
    This command removes one or more packages from the project's dependencies
    using the uv package manager. It automatically updates the pyproject.toml
    file and removes the packages from the project's virtual environment.
    
    Parameters
    ----------
    ctx : typer.Context
        Typer context for command execution.
    pkgs : list[str]
        List of package names to remove. Only the package names are required;
        version specifiers are ignored during removal.
    
    Notes
    -----
    The command automatically:
    - Removes packages from pyproject.toml
    - Uninstalls packages from the virtual environment
    - Updates the lock file if necessary
    - Records telemetry for the operation
    
    Example
    -------
    >>> # Remove single package
    >>> uvmgr deps remove requests
    >>> 
    >>> # Remove multiple packages
    >>> uvmgr deps remove pandas numpy matplotlib
    >>> 
    >>> # Remove from both runtime and dev dependencies
    >>> uvmgr deps remove pytest black
    """
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.REMOVE,
            "package.count": len(pkgs),
            "package.names": ",".join(pkgs),
        }
    )

    res = deps_ops.remove(pkgs)
    _maybe_json(ctx, res)
    colour(f"✔ removed {' '.join(pkgs)}", "green")


@app.command("upgrade")
@instrument_command("deps_upgrade", track_args=True)
def upgrade(
    ctx: typer.Context,
    all_: bool = typer.Option(False, "--all", help="Upgrade everything"),
    pkgs: list[str] = typer.Argument(None, help="Specific packages"),
):
    """
    Upgrade packages to their latest versions.
    
    This command upgrades packages to their latest versions within the constraints
    specified in pyproject.toml. It can upgrade all packages or specific packages
    as requested.
    
    Parameters
    ----------
    ctx : typer.Context
        Typer context for command execution.
    all_ : bool, optional
        If True, upgrade all packages to their latest versions within the
        constraints specified in pyproject.toml. Default is False.
    pkgs : list[str], optional
        List of specific package names to upgrade. If not provided and all_
        is False, no packages will be upgraded.
    
    Notes
    -----
    The command automatically:
    - Respects version constraints in pyproject.toml
    - Updates the lock file with new versions
    - Installs upgraded packages in the virtual environment
    - Records telemetry for the operation
    
    When using --all, all packages (both runtime and development) are upgraded
    to their latest versions within the specified constraints.
    
    Example
    -------
    >>> # Upgrade all packages
    >>> uvmgr deps upgrade --all
    >>> 
    >>> # Upgrade specific packages
    >>> uvmgr deps upgrade requests pandas
    >>> 
    >>> # Upgrade single package
    >>> uvmgr deps upgrade fastapi
    """
    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.UPDATE,
            "package.update.all": all_,
            "package.count": len(pkgs) if pkgs else 0,
        }
    )
    if pkgs:
        add_span_attributes(**{"package.names": ",".join(pkgs)})

    res = deps_ops.upgrade(all_pkgs=all_, pkgs=pkgs or None)
    _maybe_json(ctx, res)
    colour("✔ dependencies upgraded", "green")


@app.command("list")
@instrument_command("deps_list")
def _list(ctx: typer.Context):
    """
    List installed packages in the project.
    
    This command displays all packages currently installed in the project's
    virtual environment, including both runtime and development dependencies.
    
    Parameters
    ----------
    ctx : typer.Context
        Typer context for command execution.
    
    Notes
    -----
    The command shows:
    - All installed packages with their versions
    - Both runtime and development dependencies
    - Packages installed in the current virtual environment
    
    Output can be formatted as JSON using the --json flag.
    
    Example
    -------
    >>> # List all packages
    >>> uvmgr deps list
    >>> 
    >>> # List with JSON output
    >>> uvmgr --json deps list
    """
    pkgs = deps_ops.list_pkgs()

    # Add package operation attributes to span
    add_span_attributes(
        **{
            PackageAttributes.OPERATION: PackageOperations.LIST,
            "package.count": len(pkgs),
        }
    )

    _maybe_json(ctx, pkgs)
    for p in pkgs:
        colour(p, "cyan")


@app.command("lock")
@instrument_command("deps_lock", track_args=True)
def lock_dependencies(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Generate or update the lock file.
    
    This command generates or updates the uv.lock file with resolved
    dependency versions. It ensures all dependencies are properly locked
    to specific versions for reproducible builds.
    
    Parameters
    ----------
    ctx : typer.Context
        Typer context for command execution.
    verbose : bool, optional
        If True, show detailed output during lock generation.
        Default is False.
    
    Notes
    -----
    The command automatically:
    - Resolves all dependencies to specific versions
    - Creates or updates uv.lock file
    - Validates dependency compatibility
    - Records telemetry for the operation
    
    Example
    -------
    >>> # Generate lock file
    >>> uvmgr deps lock
    >>> 
    >>> # Generate with verbose output
    >>> uvmgr deps lock --verbose
    """
    add_span_event("deps.lock.started", {"verbose": verbose})
    
    try:
        result = deps_ops.lock(verbose=verbose)
        
        add_span_attributes(**{
            PackageAttributes.OPERATION: "lock",
            "lock.success": True,
        })
        
        add_span_event("deps.lock.completed", {"success": True})
        
        if verbose and result.get("output"):
            typer.echo(result["output"])
        
        typer.echo("✅ Dependencies locked successfully")
        _maybe_json(ctx, result)
        
    except Exception as e:
        add_span_event("deps.lock.failed", {"error": str(e)})
        typer.echo(f"❌ Failed to lock dependencies: {e}", err=True)
        raise typer.Exit(1)
