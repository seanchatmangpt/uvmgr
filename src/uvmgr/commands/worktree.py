"""
uvmgr.commands.worktree - Git Worktree Isolation
==============================================

Commands for Git worktree management and project isolation.

This module provides comprehensive CLI commands for managing Git worktrees,
enabling isolated development environments for multiple projects and branches.
Essential for external project integration and multi-project workflows.

Key Features
-----------
• **Worktree Creation**: Create isolated Git worktrees for branches
• **Project Isolation**: Isolate projects with separate dependencies
• **External Integration**: Support for external project workflows
• **Auto-cleanup**: Automatic cleanup of unused worktrees
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **create**: Create a new Git worktree
- **list**: List all Git worktrees
- **remove**: Remove a Git worktree
- **switch**: Switch between worktrees
- **isolate**: Create isolated environment for external projects
- **cleanup**: Clean up unused worktrees

Examples
--------
    >>> # Create worktree for feature branch
    >>> uvmgr worktree create feature/new-ui
    >>> 
    >>> # Create isolated environment for external project
    >>> uvmgr worktree isolate /path/to/external/project
    >>> 
    >>> # List all worktrees
    >>> uvmgr worktree list
    >>> 
    >>> # Clean up unused worktrees
    >>> uvmgr worktree cleanup

See Also
--------
- :mod:`uvmgr.ops.worktree` : Worktree operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import WorktreeAttributes, WorktreeOperations
from uvmgr.cli_utils import maybe_json

console = Console()
app = typer.Typer(help="Git worktree isolation and management for multi-project development")


@app.command("create")
@instrument_command("worktree_create", track_args=True)
def create_worktree(
    ctx: typer.Context,
    branch: str = typer.Argument(..., help="Branch name for the worktree"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Custom path for worktree"),
    track_remote: bool = typer.Option(True, "--track-remote/--no-track", help="Track remote branch"),
    force: bool = typer.Option(False, "--force", "-f", help="Force creation even if branch exists"),
    isolated: bool = typer.Option(False, "--isolated", "-i", help="Create isolated environment"),
):
    """Create a new Git worktree for a branch."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.CREATE,
        WorktreeAttributes.BRANCH: branch,
        "worktree.isolated": isolated,
        "worktree.track_remote": track_remote,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.create_worktree(
            branch=branch,
            path=path,
            track_remote=track_remote,
            force=force,
            isolated=isolated,
        )
        
        add_span_event("worktree.created", {
            "branch": branch,
            "path": str(result["path"]),
            "isolated": isolated,
        })
        
        console.print(f"[green]✅ Created worktree for branch '{branch}'[/green]")
        console.print(f"[blue]📁 Path: {result['path']}[/blue]")
        
        if isolated:
            console.print("[yellow]🔒 Isolated environment created[/yellow]")
            console.print("   • Separate virtual environment")
            console.print("   • Independent dependencies")
            console.print("   • Clean workspace")
        
        if result.get("venv_created"):
            console.print(f"[cyan]🐍 Virtual environment: {result['venv_path']}[/cyan]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.create_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to create worktree: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("list")
@instrument_command("worktree_list", track_args=True)
def list_worktrees(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    status: bool = typer.Option(False, "--status", "-s", help="Show Git status for each worktree"),
):
    """List all Git worktrees."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.LIST,
        "worktree.verbose": verbose,
        "worktree.show_status": status,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        worktrees = worktree_ops.list_worktrees(verbose=verbose, status=status)
        
        add_span_attributes(**{"worktree.count": len(worktrees)})
        
        if not worktrees:
            console.print("[yellow]No worktrees found[/yellow]")
            maybe_json(ctx, {"worktrees": []}, exit_code=0)
            return
        
        if ctx.meta.get("json"):
            maybe_json(ctx, {"worktrees": worktrees}, exit_code=0)
            return
        
        # Display as table
        table = Table(title="Git Worktrees")
        table.add_column("Branch", style="cyan")
        table.add_column("Path", style="blue")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")
        
        if verbose:
            table.add_column("Last Commit", style="dim")
            table.add_column("Environment", style="magenta")
        
        for wt in worktrees:
            row = [
                wt["branch"],
                str(wt["path"]),
                wt.get("type", "standard"),
                wt.get("status", "unknown"),
            ]
            
            if verbose:
                row.extend([
                    wt.get("last_commit", "")[:40],
                    wt.get("environment", "none"),
                ])
            
            table.add_row(*row)
        
        console.print(table)
        
        # Show summary
        isolated_count = sum(1 for wt in worktrees if wt.get("isolated", False))
        console.print(f"\n[dim]Total: {len(worktrees)} worktrees ({isolated_count} isolated)[/dim]")
        
    except Exception as e:
        add_span_event("worktree.list_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to list worktrees: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("remove")
@instrument_command("worktree_remove", track_args=True)
def remove_worktree(
    ctx: typer.Context,
    path: Path = typer.Argument(..., help="Path to worktree to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal even with uncommitted changes"),
    cleanup_env: bool = typer.Option(True, "--cleanup-env/--keep-env", help="Remove associated virtual environment"),
):
    """Remove a Git worktree."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.REMOVE,
        WorktreeAttributes.PATH: str(path),
        "worktree.force": force,
        "worktree.cleanup_env": cleanup_env,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.remove_worktree(
            path=path,
            force=force,
            cleanup_env=cleanup_env,
        )
        
        add_span_event("worktree.removed", {
            "path": str(path),
            "force": force,
            "env_removed": result.get("env_removed", False),
        })
        
        console.print(f"[green]✅ Removed worktree: {path}[/green]")
        
        if result.get("env_removed"):
            console.print("[cyan]🗑️  Removed associated virtual environment[/cyan]")
        
        if result.get("warnings"):
            for warning in result["warnings"]:
                console.print(f"[yellow]⚠️  {warning}[/yellow]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.remove_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to remove worktree: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("switch")
@instrument_command("worktree_switch", track_args=True)
def switch_worktree(
    ctx: typer.Context,
    path: Path = typer.Argument(..., help="Path to worktree to switch to"),
    activate_env: bool = typer.Option(True, "--activate-env/--no-activate", help="Activate associated environment"),
):
    """Switch to a different worktree."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.SWITCH,
        WorktreeAttributes.PATH: str(path),
        "worktree.activate_env": activate_env,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.switch_to_worktree(
            path=path,
            activate_env=activate_env,
        )
        
        add_span_event("worktree.switched", {
            "path": str(path),
            "branch": result.get("branch"),
            "env_activated": result.get("env_activated", False),
        })
        
        console.print(f"[green]✅ Switched to worktree: {path}[/green]")
        console.print(f"[blue]🌿 Branch: {result.get('branch', 'unknown')}[/blue]")
        
        if result.get("env_activated"):
            console.print(f"[cyan]🐍 Environment activated: {result['env_path']}[/cyan]")
        
        if result.get("instructions"):
            console.print("\n[bold]Next steps:[/bold]")
            for instruction in result["instructions"]:
                console.print(f"  • {instruction}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.switch_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to switch worktree: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("isolate")
@instrument_command("worktree_isolate", track_args=True)
def isolate_project(
    ctx: typer.Context,
    project_path: Path = typer.Argument(..., help="Path to external project to isolate"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to work on"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Custom name for isolated environment"),
    install_uvmgr: bool = typer.Option(True, "--install-uvmgr/--no-uvmgr", help="Auto-install uvmgr in isolated env"),
    sync_deps: bool = typer.Option(True, "--sync-deps/--no-sync", help="Sync project dependencies"),
):
    """Create isolated environment for external project development."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.ISOLATE,
        WorktreeAttributes.PROJECT_PATH: str(project_path),
        WorktreeAttributes.BRANCH: branch or "main",
        "worktree.install_uvmgr": install_uvmgr,
        "worktree.sync_deps": sync_deps,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.create_isolated_environment(
            project_path=project_path,
            branch=branch,
            name=name,
            install_uvmgr=install_uvmgr,
            sync_deps=sync_deps,
        )
        
        add_span_event("worktree.isolated", {
            "project_path": str(project_path),
            "worktree_path": str(result["worktree_path"]),
            "env_path": str(result.get("env_path", "")),
            "uvmgr_installed": result.get("uvmgr_installed", False),
        })
        
        console.print(Panel.fit(
            f"[green]✅ Created isolated environment for external project[/green]\n\n"
            f"[bold]Project:[/bold] {project_path.name}\n"
            f"[bold]Worktree:[/bold] {result['worktree_path']}\n"
            f"[bold]Environment:[/bold] {result.get('env_path', 'none')}\n"
            f"[bold]Branch:[/bold] {result.get('branch', 'main')}",
            title="🔒 Project Isolation Complete",
            border_style="green"
        ))
        
        if result.get("uvmgr_installed"):
            console.print("[cyan]🛠️  uvmgr installed in isolated environment[/cyan]")
        
        if result.get("deps_synced"):
            console.print("[blue]📦 Project dependencies synchronized[/blue]")
        
        # Show usage instructions
        console.print("\n[bold yellow]Usage Instructions:[/bold yellow]")
        console.print(f"  cd {result['worktree_path']}")
        if result.get("env_path"):
            console.print(f"  source {result['env_path']}/bin/activate")
        console.print("  # Start development work")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.isolate_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to create isolated environment: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("cleanup")
@instrument_command("worktree_cleanup", track_args=True)
def cleanup_worktrees(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be cleaned up"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cleanup without confirmation"),
    max_age_days: int = typer.Option(30, "--max-age", help="Maximum age in days for unused worktrees"),
    cleanup_envs: bool = typer.Option(True, "--cleanup-envs/--keep-envs", help="Clean up associated environments"),
):
    """Clean up unused and stale worktrees."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: WorktreeOperations.CLEANUP,
        "worktree.dry_run": dry_run,
        "worktree.force": force,
        "worktree.max_age_days": max_age_days,
        "worktree.cleanup_envs": cleanup_envs,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.cleanup_worktrees(
            dry_run=dry_run,
            force=force,
            max_age_days=max_age_days,
            cleanup_envs=cleanup_envs,
        )
        
        add_span_event("worktree.cleanup_completed", {
            "candidates_found": len(result.get("candidates", [])),
            "cleaned_up": len(result.get("cleaned", [])),
            "dry_run": dry_run,
        })
        
        candidates = result.get("candidates", [])
        cleaned = result.get("cleaned", [])
        
        if not candidates:
            console.print("[green]✅ No worktrees need cleanup[/green]")
            maybe_json(ctx, result, exit_code=0)
            return
        
        if dry_run:
            console.print(f"[yellow]🔍 Found {len(candidates)} worktrees that could be cleaned up:[/yellow]")
            for candidate in candidates:
                console.print(f"  • {candidate['path']} (age: {candidate['age_days']} days)")
            console.print("\n[blue]💡 Use --force to perform actual cleanup[/blue]")
        else:
            console.print(f"[green]✅ Cleaned up {len(cleaned)} worktrees[/green]")
            for cleaned_wt in cleaned:
                console.print(f"  🗑️  {cleaned_wt['path']}")
        
        if result.get("errors"):
            console.print("\n[red]Errors during cleanup:[/red]")
            for error in result["errors"]:
                console.print(f"  ❌ {error}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.cleanup_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to cleanup worktrees: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("status")
@instrument_command("worktree_status", track_args=True)
def status(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Specific worktree path to check"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed status information"),
):
    """Show status of worktrees and isolated environments."""
    add_span_attributes(**{
        WorktreeAttributes.OPERATION: "status",
        "worktree.path": str(path) if path else "all",
        "worktree.detailed": detailed,
    })
    
    try:
        from uvmgr.ops import worktree as worktree_ops
        
        result = worktree_ops.get_worktree_status(path=path, detailed=detailed)
        
        add_span_attributes(**{
            "worktree.total_count": result.get("total_count", 0),
            "worktree.isolated_count": result.get("isolated_count", 0),
        })
        
        # Summary panel
        summary = (
            f"Total Worktrees: {result.get('total_count', 0)}\n"
            f"Isolated Environments: {result.get('isolated_count', 0)}\n"
            f"Active Worktree: {result.get('current_worktree', 'none')}"
        )
        
        console.print(Panel(summary, title="🌿 Worktree Status", border_style="cyan"))
        
        # Detailed information
        if detailed and result.get("details"):
            for detail in result["details"]:
                console.print(f"\n[cyan]📁 {detail['path']}[/cyan]")
                console.print(f"   Branch: {detail.get('branch', 'unknown')}")
                console.print(f"   Status: {detail.get('status', 'unknown')}")
                if detail.get("environment"):
                    console.print(f"   Environment: {detail['environment']}")
                if detail.get("last_activity"):
                    console.print(f"   Last Activity: {detail['last_activity']}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("worktree.status_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to get worktree status: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)