"""
uvmgr.commands.weaver - OpenTelemetry Weaver Tools
================================================

OpenTelemetry Weaver command suite for semantic convention management.

This module provides comprehensive CLI commands for managing OpenTelemetry
semantic conventions using the Weaver tool. Includes installation, validation,
code generation, and registry management capabilities.

Key Features
-----------
• **Weaver Installation**: Install and manage OpenTelemetry Weaver
• **Registry Validation**: Validate semantic convention registries
• **Code Generation**: Generate code from semantic conventions
• **Registry Management**: Search, resolve, and manage registries
• **Documentation**: Generate documentation from conventions
• **Version Control**: Compare and diff registry versions

Available Commands
-----------------
- **install**: Install or update OpenTelemetry Weaver
- **check**: Validate semantic convention registry
- **generate**: Generate code from semantic conventions
- **resolve**: Resolve and export registry data
- **search**: Search for semantic conventions
- **stats**: Show registry statistics
- **diff**: Compare two registries
- **init**: Initialize a new registry
- **docs**: Generate documentation
- **version**: Show Weaver version

Registry Management
------------------
- **Validation**: Check registry compliance and consistency
- **Search**: Find specific attributes, metrics, or spans
- **Resolution**: Resolve dependencies and references
- **Statistics**: Analyze registry size and complexity
- **Comparison**: Diff between registry versions

Code Generation
--------------
- **Python**: Generate Python constants and types
- **Markdown**: Generate documentation
- **Go**: Generate Go code (planned)
- **Custom Templates**: Support for custom generation templates

Examples
--------
    >>> # Install Weaver
    >>> uvmgr weaver install
    >>> 
    >>> # Validate registry
    >>> uvmgr weaver check --registry ./registry
    >>> 
    >>> # Generate Python constants
    >>> uvmgr weaver generate python --output src/
    >>> 
    >>> # Search for attributes
    >>> uvmgr weaver search "http.request"
    >>> 
    >>> # Generate documentation
    >>> uvmgr weaver docs --output docs/

See Also
--------
- :mod:`uvmgr.core.semconv` : Semantic conventions
- :mod:`uvmgr.commands.otel` : OpenTelemetry validation
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from uvmgr.cli_utils import handle_cli_exception, maybe_json
from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.ops.weaver import (
    check_registry,
    diff_registries,
    generate_code,
    generate_docs,
    get_registry_stats,
    init_registry,
    install_weaver,
    resolve_registry,
    search_registry,
)

console = Console()
app = typer.Typer(help="OpenTelemetry Weaver semantic convention tools")

# Paths
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"


@app.command("install")
@instrument_command("weaver_install", track_args=True)
def install(
    ctx: typer.Context,
    version: str = typer.Option("latest", "--version", "-v", help="Weaver version to install"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install or update OpenTelemetry Weaver."""
    add_span_attributes(**{
        "weaver.operation": "install",
        "weaver.version": version,
        "weaver.force": force,
    })
    add_span_event("weaver.install.started", {"version": version})
    
    console.print("[bold]Installing OpenTelemetry Weaver...[/bold]\n")
    
    try:
        result = install_weaver(version=version, force=force)
        
        if result["status"] == "already_installed":
            console.print(f"[green]✓ {result['message']}[/green]")
            if not typer.confirm("Reinstall?"):
                raise typer.Exit()
            # Force reinstall
            result = install_weaver(version=version, force=True)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("check")
@instrument_command("weaver_check", track_args=True)
def check(
    ctx: typer.Context,
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    future: bool = typer.Option(True, "--future", help="Enable latest validation rules"),
    policy: Path | None = typer.Option(None, "--policy", "-p", help="Rego policy file"),
):
    """Validate semantic convention registry."""
    add_span_attributes(**{
        "weaver.operation": "check",
        "weaver.registry_path": str(registry),
        "weaver.future": future,
        "weaver.policy": str(policy) if policy else None,
    })
    add_span_event("weaver.check.started", {"registry": str(registry)})
    
    console.print(f"[bold]Checking registry: {registry}[/bold]\n")
    
    try:
        result = check_registry(registry=registry, future=future, policy=policy)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("output"):
            console.print(result["output"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("generate")
@instrument_command("weaver_generate", track_args=True)
def generate(
    ctx: typer.Context,
    template: str = typer.Argument(..., help="Template type (e.g., python, markdown, go)"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    config: Path | None = typer.Option(None, "--config", "-c", help="Weaver config file"),
):
    """Generate code from semantic conventions."""
    add_span_attributes(**{
        "weaver.operation": "generate",
        "weaver.template": template,
        "weaver.output_path": str(output),
        "weaver.registry_path": str(registry),
        "weaver.config": str(config) if config else None,
    })
    add_span_event("weaver.generate.started", {
        "template": template,
        "registry": str(registry)
    })
    
    console.print(f"[bold]Generating {template} from {registry}[/bold]\n")
    
    try:
        result = generate_code(
            template=template,
            output=output,
            registry=registry,
            config=config
        )
        
        console.print(f"[green]✓ {result['message']}[/green]")
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("resolve")
@instrument_command("weaver_resolve", track_args=True)
def resolve(
    ctx: typer.Context,
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, yaml)"),
):
    """Resolve semantic convention references and inheritance."""
    add_span_attributes(**{
        "weaver.operation": "resolve",
        "weaver.registry_path": str(registry),
        "weaver.format": format,
        "weaver.output": str(output) if output else None,
    })
    add_span_event("weaver.resolve.started", {"registry": str(registry)})
    
    console.print(f"[bold]Resolving registry: {registry}[/bold]\n")
    
    try:
        result = resolve_registry(registry=registry, output=output, format=format)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("output"):
            console.print(result["output"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("search")
@instrument_command("weaver_search", track_args=True)
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query (regex supported)"),
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    type: str | None = typer.Option(None, "--type", "-t", help="Filter by type (attribute, metric, etc)"),
):
    """Search for semantic conventions in registry."""
    add_span_attributes(**{
        "weaver.operation": "search",
        "weaver.query": query,
        "weaver.registry_path": str(registry),
        "weaver.search_type": type,
    })
    add_span_event("weaver.search.started", {"query": query})
    
    console.print(f"[bold]Searching for '{query}' in {registry}[/bold]\n")
    
    try:
        result = search_registry(query=query, registry=registry, type=type)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("results"):
            console.print(result["results"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("stats")
@instrument_command("weaver_stats", track_args=True)
def stats(
    ctx: typer.Context,
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
):
    """Show registry statistics."""
    add_span_attributes(**{
        "weaver.operation": "stats",
        "weaver.registry_path": str(registry),
    })
    add_span_event("weaver.stats.started", {"registry": str(registry)})
    
    console.print(f"[bold]Registry statistics: {registry}[/bold]\n")
    
    try:
        result = get_registry_stats(registry=registry)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("stats"):
            console.print(result["stats"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("diff")
@instrument_command("weaver_diff", track_args=True)
def diff(
    ctx: typer.Context,
    registry1: Path = typer.Argument(..., help="First registry to compare"),
    registry2: Path = typer.Argument(..., help="Second registry to compare"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output diff to file"),
):
    """Compare two registries and show differences."""
    add_span_attributes(**{
        "weaver.operation": "diff",
        "weaver.registry1": str(registry1),
        "weaver.registry2": str(registry2),
        "weaver.output": str(output) if output else None,
    })
    add_span_event("weaver.diff.started", {
        "registry1": str(registry1),
        "registry2": str(registry2)
    })
    
    console.print(f"[bold]Comparing registries:[/bold]")
    console.print(f"  {registry1}")
    console.print(f"  {registry2}\n")
    
    try:
        result = diff_registries(registry1=registry1, registry2=registry2, output=output)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("diff"):
            console.print(result["diff"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("init")
@instrument_command("weaver_init", track_args=True)
def init(
    ctx: typer.Context,
    name: str = typer.Option("myproject", "--name", "-n", help="Registry name"),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Registry path"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing registry"),
):
    """Initialize a new semantic convention registry."""
    add_span_attributes(**{
        "weaver.operation": "init",
        "weaver.name": name,
        "weaver.path": str(path),
        "weaver.force": force,
    })
    add_span_event("weaver.init.started", {"name": name, "path": str(path)})
    
    console.print(f"[bold]Initializing registry '{name}' at {path}[/bold]\n")
    
    try:
        result = init_registry(name=name, path=path, force=force)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("output"):
            console.print(result["output"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("docs")
@instrument_command("weaver_docs", track_args=True)
def docs(
    ctx: typer.Context,
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    output: Path = typer.Option(Path("docs"), "--output", "-o", help="Output directory"),
    format: str = typer.Option("markdown", "--format", "-f", help="Documentation format"),
):
    """Generate documentation from semantic conventions."""
    add_span_attributes(**{
        "weaver.operation": "docs",
        "weaver.registry_path": str(registry),
        "weaver.output_path": str(output),
        "weaver.format": format,
    })
    add_span_event("weaver.docs.started", {
        "registry": str(registry),
        "format": format
    })
    
    console.print(f"[bold]Generating {format} documentation from {registry}[/bold]\n")
    
    try:
        result = generate_docs(registry=registry, output=output, format=format)
        
        console.print(f"[green]✓ {result['message']}[/green]")
        if result.get("output"):
            console.print(result["output"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)


@app.command("version")
@instrument_command("weaver_version")
def version(ctx: typer.Context):
    """Show Weaver version."""
    add_span_attributes(**{
        "weaver.operation": "version",
    })
    add_span_event("weaver.version.started")
    
    try:
        from uvmgr.ops.weaver import get_weaver_version
        
        version = get_weaver_version()
        if version:
            console.print(f"[green]Weaver version: {version}[/green]")
            maybe_json(ctx, {"version": version}, exit_code=0)
        else:
            console.print("[red]Weaver not installed[/red]")
            maybe_json(ctx, {"error": "Weaver not installed"}, exit_code=1)
            
    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        handle_cli_exception(e, exit_code=1)
