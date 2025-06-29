"""
uvmgr.commands.guides - Agent Guide Catalog CLI
=============================================

Commands for managing agent guides catalog, fetching, caching, and versioning.

This module provides comprehensive CLI commands for the agent-guides ecosystem,
enabling discovery, download, caching, and version management of agent guides.
Core to the agent-guides value proposition in the WeaverShip roadmap.

Key Features
-----------
• **Guide Discovery**: Search and browse available guides
• **Guide Fetching**: Download guides from remote repositories
• **Guide Caching**: Local cache management with TTL
• **Version Management**: Pin and update guide versions
• **Guide Validation**: Validate guide structure and compatibility

Available Commands
-----------------
- **catalog**: Browse available guides catalog
- **fetch**: Download a guide from repository
- **list**: List locally cached guides
- **update**: Update guides to latest versions
- **validate**: Validate guide structure
- **pin**: Pin guide to specific version
- **cache**: Manage guide cache

Examples
--------
    >>> # Browse guide catalog
    >>> uvmgr guides catalog
    >>> 
    >>> # Fetch a specific guide
    >>> uvmgr guides fetch claude-commands
    >>> 
    >>> # Update all guides
    >>> uvmgr guides update --all
    >>> 
    >>> # Validate local guides
    >>> uvmgr guides validate

See Also
--------
- :mod:`uvmgr.ops.guides` : Guide operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import GuideAttributes, GuideOperations
from uvmgr.cli_utils import maybe_json

console = Console()
app = typer.Typer(help="Agent guide catalog management and versioning")


@app.command("catalog")
@instrument_command("guides_catalog", track_args=True)
def browse_catalog(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search guides by name or tag"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    sort_by: str = typer.Option("popularity", "--sort", help="Sort by: popularity, updated, name"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of guides to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Browse available agent guides catalog."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.CATALOG,
        "guides.search": search or "",
        "guides.category": category or "all",
        "guides.sort_by": sort_by,
        "guides.limit": limit,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        catalog = guides_ops.get_guide_catalog(
            search=search,
            category=category,
            sort_by=sort_by,
            limit=limit,
        )
        
        add_span_event("guides.catalog.fetched", {
            "total_guides": len(catalog.get("guides", [])),
            "categories": len(catalog.get("categories", [])),
        })
        
        if json_output:
            maybe_json(ctx, catalog, exit_code=0)
            return
        
        # Display catalog
        guides = catalog.get("guides", [])
        if not guides:
            console.print("[yellow]No guides found matching criteria[/yellow]")
            return
        
        table = Table(title="📚 Agent Guides Catalog")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Version", style="green")
        table.add_column("Downloads", style="blue", justify="right")
        table.add_column("Updated", style="dim")
        table.add_column("Description", style="white")
        
        for guide in guides:
            table.add_row(
                guide["name"],
                guide.get("category", "general"),
                guide.get("version", "latest"),
                str(guide.get("downloads", 0)),
                guide.get("updated", "unknown"),
                guide.get("description", "")[:50] + "..."
            )
        
        console.print(table)
        
        # Show categories
        if catalog.get("categories"):
            console.print("\n[bold]Available Categories:[/bold]")
            for cat in catalog["categories"]:
                console.print(f"  • {cat['name']} ({cat['count']} guides)")
        
    except Exception as e:
        add_span_event("guides.catalog.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to browse catalog: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("fetch")
@instrument_command("guides_fetch", track_args=True)
def fetch_guide(
    ctx: typer.Context,
    guide_name: str = typer.Argument(..., help="Name of the guide to fetch"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version to fetch"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if cached"),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Verify guide integrity"),
):
    """Fetch a guide from the repository."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.FETCH,
        GuideAttributes.NAME: guide_name,
        GuideAttributes.VERSION: version or "latest",
        "guides.force": force,
        "guides.verify": verify,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Fetching guide '{guide_name}'...", total=None)
            
            result = guides_ops.fetch_guide(
                name=guide_name,
                version=version,
                force=force,
                verify=verify,
            )
            
            progress.update(task, description="Guide fetched successfully")
        
        add_span_event("guides.fetched", {
            "name": guide_name,
            "version": result.get("version"),
            "size": result.get("size", 0),
            "cached": result.get("from_cache", False),
        })
        
        console.print(f"[green]✅ Successfully fetched guide: {guide_name}[/green]")
        console.print(f"[blue]📍 Location: {result['path']}[/blue]")
        console.print(f"[cyan]📌 Version: {result['version']}[/cyan]")
        
        if result.get("from_cache"):
            console.print("[yellow]📦 Loaded from cache[/yellow]")
        
        if result.get("dependencies"):
            console.print("\n[bold]Dependencies:[/bold]")
            for dep in result["dependencies"]:
                console.print(f"  • {dep['name']} ({dep['version']})")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("guides.fetch.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to fetch guide: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("list")
@instrument_command("guides_list", track_args=True)
def list_guides(
    ctx: typer.Context,
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    outdated: bool = typer.Option(False, "--outdated", help="Show only outdated guides"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """List locally cached guides."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.LIST,
        "guides.category": category or "all",
        "guides.outdated": outdated,
        "guides.verbose": verbose,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        guides = guides_ops.list_cached_guides(
            category=category,
            outdated_only=outdated,
            verbose=verbose,
        )
        
        add_span_attributes(**{"guides.count": len(guides)})
        
        if not guides:
            console.print("[yellow]No cached guides found[/yellow]")
            maybe_json(ctx, {"guides": []}, exit_code=0)
            return
        
        if ctx.meta.get("json"):
            maybe_json(ctx, {"guides": guides}, exit_code=0)
            return
        
        # Display guides
        table = Table(title="📚 Cached Agent Guides")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Size", style="blue", justify="right")
        table.add_column("Cached", style="dim")
        
        if verbose:
            table.add_column("Path", style="dim")
            table.add_column("Status", style="white")
        
        for guide in guides:
            row = [
                guide["name"],
                guide["version"],
                guide.get("category", "general"),
                guide.get("size_human", "unknown"),
                guide.get("cached_date", "unknown"),
            ]
            
            if verbose:
                row.extend([
                    str(guide.get("path", "")),
                    "🔄 Update available" if guide.get("outdated") else "✅ Up to date",
                ])
            
            table.add_row(*row)
        
        console.print(table)
        
        # Summary
        total_size = sum(g.get("size", 0) for g in guides)
        outdated_count = sum(1 for g in guides if g.get("outdated", False))
        
        console.print(f"\n[dim]Total: {len(guides)} guides, {total_size / 1024 / 1024:.1f} MB[/dim]")
        if outdated_count > 0:
            console.print(f"[yellow]🔄 {outdated_count} guides have updates available[/yellow]")
        
    except Exception as e:
        add_span_event("guides.list.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to list guides: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("update")
@instrument_command("guides_update", track_args=True)
def update_guides(
    ctx: typer.Context,
    guide_name: Optional[str] = typer.Argument(None, help="Specific guide to update"),
    all_guides: bool = typer.Option(False, "--all", "-a", help="Update all cached guides"),
    check_only: bool = typer.Option(False, "--check", help="Check for updates without applying"),
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if current"),
):
    """Update guides to latest versions."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.UPDATE,
        GuideAttributes.NAME: guide_name or "all",
        "guides.all": all_guides,
        "guides.check_only": check_only,
        "guides.force": force,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        if not guide_name and not all_guides:
            console.print("[red]Error: Specify a guide name or use --all[/red]")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking for updates...", total=None)
            
            result = guides_ops.update_guides(
                name=guide_name,
                update_all=all_guides,
                check_only=check_only,
                force=force,
            )
            
            progress.update(task, description="Update check complete")
        
        add_span_event("guides.update.completed", {
            "checked": len(result.get("checked", [])),
            "updated": len(result.get("updated", [])),
            "failed": len(result.get("failed", [])),
        })
        
        # Display results
        if check_only:
            updates = result.get("available_updates", [])
            if not updates:
                console.print("[green]✅ All guides are up to date![/green]")
            else:
                console.print(f"[yellow]🔄 {len(updates)} updates available:[/yellow]")
                for update in updates:
                    console.print(f"  • {update['name']}: {update['current']} → {update['latest']}")
        else:
            updated = result.get("updated", [])
            failed = result.get("failed", [])
            
            if updated:
                console.print(f"[green]✅ Updated {len(updated)} guides:[/green]")
                for guide in updated:
                    console.print(f"  • {guide['name']} → {guide['version']}")
            
            if failed:
                console.print(f"\n[red]❌ Failed to update {len(failed)} guides:[/red]")
                for fail in failed:
                    console.print(f"  • {fail['name']}: {fail['error']}")
            
            if not updated and not failed:
                console.print("[green]✅ All guides are already up to date![/green]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("guides.update.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to update guides: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("guides_validate", track_args=True)
def validate_guides(
    ctx: typer.Context,
    guide_name: Optional[str] = typer.Argument(None, help="Specific guide to validate"),
    all_guides: bool = typer.Option(False, "--all", "-a", help="Validate all cached guides"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation mode"),
):
    """Validate guide structure and compatibility."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.VALIDATE,
        GuideAttributes.NAME: guide_name or "all",
        "guides.all": all_guides,
        "guides.strict": strict,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        if not guide_name and not all_guides:
            console.print("[red]Error: Specify a guide name or use --all[/red]")
            raise typer.Exit(1)
        
        result = guides_ops.validate_guides(
            name=guide_name,
            validate_all=all_guides,
            strict=strict,
        )
        
        add_span_event("guides.validation.completed", {
            "validated": len(result.get("validated", [])),
            "passed": len(result.get("passed", [])),
            "failed": len(result.get("failed", [])),
        })
        
        # Display results
        passed = result.get("passed", [])
        failed = result.get("failed", [])
        
        if passed:
            console.print(f"[green]✅ {len(passed)} guides passed validation:[/green]")
            for guide in passed:
                console.print(f"  • {guide['name']} ({guide['version']})")
        
        if failed:
            console.print(f"\n[red]❌ {len(failed)} guides failed validation:[/red]")
            for fail in failed:
                console.print(f"  • {fail['name']}: {fail['reason']}")
                if fail.get("errors"):
                    for error in fail["errors"][:3]:
                        console.print(f"    - {error}")
        
        # Summary
        total = len(passed) + len(failed)
        if total > 0:
            success_rate = (len(passed) / total) * 100
            console.print(f"\n[bold]Validation Summary:[/bold]")
            console.print(f"  Success rate: {success_rate:.1f}%")
            console.print(f"  Mode: {'Strict' if strict else 'Standard'}")
        
        maybe_json(ctx, result, exit_code=0)
        
        if failed and strict:
            raise typer.Exit(1)
        
    except Exception as e:
        add_span_event("guides.validate.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to validate guides: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("pin")
@instrument_command("guides_pin", track_args=True)
def pin_guide_version(
    ctx: typer.Context,
    guide_name: str = typer.Argument(..., help="Guide to pin"),
    version: str = typer.Argument(..., help="Version to pin to"),
    project_only: bool = typer.Option(False, "--project", "-p", help="Pin only for current project"),
):
    """Pin a guide to a specific version."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: GuideOperations.PIN,
        GuideAttributes.NAME: guide_name,
        GuideAttributes.VERSION: version,
        "guides.project_only": project_only,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        result = guides_ops.pin_guide_version(
            name=guide_name,
            version=version,
            project_only=project_only,
        )
        
        add_span_event("guides.pinned", {
            "name": guide_name,
            "version": version,
            "scope": "project" if project_only else "global",
        })
        
        console.print(f"[green]✅ Pinned {guide_name} to version {version}[/green]")
        
        if project_only:
            console.print(f"[blue]📍 Pinned in project: {result.get('project_path')}[/blue]")
        else:
            console.print("[cyan]📌 Pinned globally[/cyan]")
        
        if result.get("warning"):
            console.print(f"[yellow]⚠️  {result['warning']}[/yellow]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("guides.pin.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to pin guide: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("cache")
@instrument_command("guides_cache", track_args=True)
def manage_cache(
    ctx: typer.Context,
    action: str = typer.Argument("status", help="Action: status, clean, configure"),
    max_age_days: Optional[int] = typer.Option(None, "--max-age", help="Maximum cache age in days"),
    max_size_mb: Optional[int] = typer.Option(None, "--max-size", help="Maximum cache size in MB"),
    clear_all: bool = typer.Option(False, "--clear-all", help="Clear entire cache"),
):
    """Manage guide cache settings and cleanup."""
    add_span_attributes(**{
        GuideAttributes.OPERATION: "cache_" + action,
        "guides.cache.action": action,
        "guides.cache.max_age_days": max_age_days or 0,
        "guides.cache.max_size_mb": max_size_mb or 0,
    })
    
    try:
        from uvmgr.ops import guides as guides_ops
        
        if action == "status":
            result = guides_ops.get_cache_status()
            
            console.print(Panel.fit(
                f"[bold]Guide Cache Status[/bold]\n\n"
                f"Location: {result['path']}\n"
                f"Size: {result['size_human']}\n"
                f"Guides: {result['guide_count']}\n"
                f"Oldest: {result.get('oldest_date', 'N/A')}\n"
                f"Max Age: {result.get('max_age_days', 'unlimited')} days\n"
                f"Max Size: {result.get('max_size_mb', 'unlimited')} MB",
                title="📦 Cache Information",
                border_style="cyan"
            ))
            
        elif action == "clean":
            result = guides_ops.clean_cache(
                max_age_days=max_age_days,
                max_size_mb=max_size_mb,
                clear_all=clear_all,
            )
            
            console.print(f"[green]✅ Cache cleaned successfully[/green]")
            console.print(f"  Removed: {result['removed_count']} guides")
            console.print(f"  Freed: {result['freed_size_human']}")
            
        elif action == "configure":
            result = guides_ops.configure_cache(
                max_age_days=max_age_days,
                max_size_mb=max_size_mb,
            )
            
            console.print("[green]✅ Cache configuration updated[/green]")
            if max_age_days:
                console.print(f"  Max age: {max_age_days} days")
            if max_size_mb:
                console.print(f"  Max size: {max_size_mb} MB")
        
        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: status, clean, configure")
            raise typer.Exit(1)
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("guides.cache.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to manage cache: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)