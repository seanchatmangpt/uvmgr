#!/usr/bin/env python3
"""
uvmgr.commands.autogit
=====================

Intelligent Git automation with AI-powered commit messages and workflow optimization.

This module provides automated Git operations including:
• **Smart Status**: Enhanced git status with AI insights
• **Auto Commit**: AI-generated commit messages following conventional commits
• **Smart Sync**: Intelligent push/pull with conflict resolution
• **Workflow Integration**: Seamless integration with uvmgr workflows

Features
--------
• AI-powered commit message generation
• Conventional commit format compliance
• Conflict detection and resolution suggestions
• OpenTelemetry instrumentation for all operations
• Batch operations for multiple files
• Safe operations with rollback capabilities

Examples
--------
    >>> # Enhanced git status
    >>> uvmgr autogit status
    >>> 
    >>> # Auto-commit with AI message
    >>> uvmgr autogit commit
    >>> 
    >>> # Smart sync with remote
    >>> uvmgr autogit sync
    >>> 
    >>> # Batch commit multiple changes
    >>> uvmgr autogit commit --batch
"""

from __future__ import annotations

import asyncio
import subprocess
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import GitAttributes, GitOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.ai import get_ai_client

app = typer.Typer(help="🤖 Intelligent Git automation with AI-powered workflows")


@app.command()
@instrument_command("autogit_status", track_args=True)
def status(
    ctx: typer.Context,
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed file analysis"),
    ai_insights: bool = typer.Option(True, "--ai-insights/--no-ai-insights", help="Include AI-powered insights"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format")
) -> None:
    """
    Enhanced git status with AI insights and detailed analysis.
    
    Provides intelligent analysis of repository state including:
    - Standard git status information
    - AI-powered change analysis and suggestions
    - Conventional commit recommendations
    - Conflict detection and resolution hints
    """
    from uvmgr.ops.autogit import analyze_git_status
    
    add_span_attributes(
        operation=GitOperations.STATUS,
        detailed=detailed,
        ai_insights=ai_insights
    )
    
    try:
        # Get current directory as project path
        project_path = Path.cwd()
        
        # Verify this is a git repository
        if not (project_path / ".git").exists():
            typer.echo(f"{colour.red('Error:')} Not a git repository", err=True)
            raise typer.Exit(1)
        
        add_span_event("autogit.status.started", {"project_path": str(project_path)})
        
        # Analyze git status with AI insights
        result = analyze_git_status(
            project_path=project_path,
            detailed=detailed,
            ai_insights=ai_insights
        )
        
        if not result["success"]:
            typer.echo(f"{colour.red('Error:')} {result['error']}", err=True)
            raise typer.Exit(1)
        
        # Output results
        if json_output:
            dump_json(result)
        else:
            _display_status_result(result, detailed, ai_insights)
        
        add_span_event("autogit.status.completed", {
            "files_changed": result.get("files_changed", 0),
            "untracked_files": result.get("untracked_files", 0),
            "branch": result.get("branch", "unknown")
        })
        
    except subprocess.CalledProcessError as e:
        add_span_event("autogit.status.git_error", {"error": str(e)})
        typer.echo(f"{colour.red('Git Error:')} {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        add_span_event("autogit.status.error", {"error": str(e)})
        typer.echo(f"{colour.red('Error:')} {e}", err=True)
        raise typer.Exit(1)


@app.command()
@instrument_command("autogit_commit", track_args=True)
def commit(
    ctx: typer.Context,
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom commit message"),
    ai_generate: bool = typer.Option(True, "--ai-generate/--no-ai-generate", help="Generate AI commit message"),
    conventional: bool = typer.Option(True, "--conventional/--no-conventional", help="Use conventional commit format"),
    batch: bool = typer.Option(False, "--batch", help="Commit all changes in batch"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview commit without executing"),
    add_all: bool = typer.Option(False, "--add-all", "-a", help="Add all changed files before committing")
) -> None:
    """
    AI-powered commit with intelligent message generation.
    
    Features:
    - AI-generated commit messages following conventional commits
    - Automatic change analysis and categorization
    - Smart file staging recommendations
    - Preview mode for safe operations
    """
    from uvmgr.ops.autogit import generate_commit
    
    add_span_attributes(
        operation=GitOperations.COMMIT,
        ai_generate=ai_generate,
        conventional=conventional,
        batch=batch,
        dry_run=dry_run
    )
    
    try:
        project_path = Path.cwd()
        
        if not (project_path / ".git").exists():
            typer.echo(f"{colour.red('Error:')} Not a git repository", err=True)
            raise typer.Exit(1)
        
        add_span_event("autogit.commit.started", {"project_path": str(project_path)})
        
        # Generate and execute commit
        result = generate_commit(
            project_path=project_path,
            message=message,
            ai_generate=ai_generate,
            conventional=conventional,
            batch=batch,
            dry_run=dry_run,
            add_all=add_all
        )
        
        if not result["success"]:
            typer.echo(f"{colour.red('Error:')} {result['error']}", err=True)
            raise typer.Exit(1)
        
        # Display results
        if dry_run:
            _display_commit_preview(result)
        else:
            _display_commit_result(result)
        
        add_span_event("autogit.commit.completed", {
            "commit_hash": result.get("commit_hash", ""),
            "files_committed": result.get("files_committed", 0),
            "message_generated": ai_generate and not message
        })
        
    except Exception as e:
        add_span_event("autogit.commit.error", {"error": str(e)})
        typer.echo(f"{colour.red('Error:')} {e}", err=True)
        raise typer.Exit(1)


@app.command()
@instrument_command("autogit_sync", track_args=True)
def sync(
    ctx: typer.Context,
    remote: str = typer.Option("origin", "--remote", "-r", help="Remote repository name"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch name (default: current)"),
    pull_first: bool = typer.Option(True, "--pull-first/--no-pull-first", help="Pull before pushing"),
    force: bool = typer.Option(False, "--force", help="Force push (dangerous)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview sync without executing"),
    conflict_strategy: str = typer.Option("merge", "--conflict-strategy", help="Conflict resolution: merge, rebase, abort")
) -> None:
    """
    Intelligent sync with remote repository.
    
    Features:
    - Smart pull/push with conflict detection
    - Automatic conflict resolution suggestions
    - Safe operation modes with rollback
    - Multi-remote synchronization support
    """
    from uvmgr.ops.autogit import sync_repository
    
    add_span_attributes(
        operation=GitOperations.SYNC,
        remote=remote,
        pull_first=pull_first,
        force=force,
        dry_run=dry_run
    )
    
    try:
        project_path = Path.cwd()
        
        if not (project_path / ".git").exists():
            typer.echo(f"{colour.red('Error:')} Not a git repository", err=True)
            raise typer.Exit(1)
        
        add_span_event("autogit.sync.started", {
            "project_path": str(project_path),
            "remote": remote,
            "branch": branch or "current"
        })
        
        # Perform repository sync
        result = sync_repository(
            project_path=project_path,
            remote=remote,
            branch=branch,
            pull_first=pull_first,
            force=force,
            dry_run=dry_run,
            conflict_strategy=conflict_strategy
        )
        
        if not result["success"]:
            typer.echo(f"{colour.red('Error:')} {result['error']}", err=True)
            if "conflicts" in result:
                _display_conflict_resolution(result["conflicts"])
            raise typer.Exit(1)
        
        # Display results
        if dry_run:
            _display_sync_preview(result)
        else:
            _display_sync_result(result)
        
        add_span_event("autogit.sync.completed", {
            "operations_performed": result.get("operations", []),
            "conflicts_resolved": result.get("conflicts_resolved", 0),
            "commits_pulled": result.get("commits_pulled", 0),
            "commits_pushed": result.get("commits_pushed", 0)
        })
        
    except Exception as e:
        add_span_event("autogit.sync.error", {"error": str(e)})
        typer.echo(f"{colour.red('Error:')} {e}", err=True)
        raise typer.Exit(1)


def _display_status_result(result: Dict[str, Any], detailed: bool, ai_insights: bool) -> None:
    """Display git status results in a user-friendly format."""
    typer.echo(f"\n🔍 {colour.bold('Git Repository Status')}")
    typer.echo(f"📁 Branch: {colour.green(result.get('branch', 'unknown'))}")
    
    if result.get("behind_remote"):
        typer.echo(f"⬇️  Behind remote by {result['behind_remote']} commits")
    if result.get("ahead_remote"):
        typer.echo(f"⬆️  Ahead of remote by {result['ahead_remote']} commits")
    
    # Modified files
    if modified := result.get("modified_files", []):
        typer.echo(f"\n📝 {colour.yellow('Modified files')} ({len(modified)}):")
        for file in modified:
            typer.echo(f"  • {file}")
    
    # Untracked files
    if untracked := result.get("untracked_files", []):
        typer.echo(f"\n➕ {colour.blue('Untracked files')} ({len(untracked)}):")
        for file in untracked:
            typer.echo(f"  • {file}")
    
    # Staged files
    if staged := result.get("staged_files", []):
        typer.echo(f"\n✅ {colour.green('Staged files')} ({len(staged)}):")
        for file in staged:
            typer.echo(f"  • {file}")
    
    # AI insights
    if ai_insights and "ai_insights" in result:
        insights = result["ai_insights"]
        typer.echo(f"\n🤖 {colour.bold('AI Insights')}:")
        if insights.get("commit_suggestion"):
            typer.echo(f"💡 Suggested commit: {colour.cyan(insights['commit_suggestion'])}")
        if insights.get("recommendations"):
            typer.echo("📋 Recommendations:")
            for rec in insights["recommendations"]:
                typer.echo(f"  • {rec}")


def _display_commit_preview(result: Dict[str, Any]) -> None:
    """Display commit preview for dry-run mode."""
    typer.echo(f"\n🔍 {colour.bold('Commit Preview')} (dry-run)")
    typer.echo(f"📝 Message: {colour.cyan(result.get('message', ''))}")
    
    if files := result.get("files_to_commit", []):
        typer.echo(f"📁 Files to commit ({len(files)}):")
        for file in files:
            typer.echo(f"  • {file}")
    
    typer.echo(f"\n💡 Run without --dry-run to execute this commit")


def _display_commit_result(result: Dict[str, Any]) -> None:
    """Display commit results."""
    typer.echo(f"\n✅ {colour.bold('Commit Successful')}")
    typer.echo(f"🔗 Hash: {colour.green(result.get('commit_hash', ''))}")
    typer.echo(f"📝 Message: {colour.cyan(result.get('message', ''))}")
    
    if files := result.get("files_committed", []):
        typer.echo(f"📁 Files committed: {len(files)}")


def _display_sync_preview(result: Dict[str, Any]) -> None:
    """Display sync preview for dry-run mode."""
    typer.echo(f"\n🔍 {colour.bold('Sync Preview')} (dry-run)")
    
    operations = result.get("planned_operations", [])
    for op in operations:
        typer.echo(f"  • {op}")
    
    typer.echo(f"\n💡 Run without --dry-run to execute these operations")


def _display_sync_result(result: Dict[str, Any]) -> None:
    """Display sync results."""
    typer.echo(f"\n✅ {colour.bold('Sync Successful')}")
    
    operations = result.get("operations_performed", [])
    for op in operations:
        typer.echo(f"  ✓ {op}")
    
    if pulled := result.get("commits_pulled", 0):
        typer.echo(f"⬇️  Pulled {pulled} commits")
    
    if pushed := result.get("commits_pushed", 0):
        typer.echo(f"⬆️  Pushed {pushed} commits")


def _display_conflict_resolution(conflicts: List[Dict[str, Any]]) -> None:
    """Display conflict resolution suggestions."""
    typer.echo(f"\n⚠️  {colour.yellow('Conflicts Detected')}")
    
    for conflict in conflicts:
        typer.echo(f"📁 {conflict.get('file', 'unknown')}")
        typer.echo(f"   Resolution: {conflict.get('suggestion', 'Manual resolution required')}")