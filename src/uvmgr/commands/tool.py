"""
uvmgr.commands.tool_enhanced
============================

Enhanced tool management with uvx integration and value-add features.

This module extends the basic tool functionality with:
• uvx isolated tool environments
• Smart tool recommendations
• Tool health checking
• Profile management
• OTEL instrumentation throughout

Legacy venv commands are preserved for backwards compatibility.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ToolAttributes, ToolOperations
from uvmgr.core.shell import colour
from uvmgr.ops import tools as tools_ops
from uvmgr.ops import uvx as uvx_ops

app = typer.Typer(help="Advanced tool management (venv + uvx)")
console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Legacy Commands (Backwards Compatible)
# ──────────────────────────────────────────────────────────────────────────────

@app.command("run")
@instrument_command("tool_run", track_args=True)
def run(
    pkg_and_args: list[str] = typer.Argument(
        ...,
        metavar="COMMAND [ARGS]...",
        help="Tool name followed by its arguments (e.g.  black --check src/)",
    ),
    isolated: bool = typer.Option(
        False,
        "--isolated",
        "-i", 
        help="Run with uvx in isolated environment"
    ),
):
    """Execute a tool (project venv or uvx isolated)."""
    if not pkg_and_args:
        typer.echo("No command supplied", err=True)
        raise typer.Exit(1)

    command, *args = pkg_and_args
    
    add_span_attributes(**{
        ToolAttributes.TOOL_NAME: command,
        ToolAttributes.ISOLATED: isolated,
        ToolAttributes.OPERATION: ToolOperations.RUN
    })

    if isolated:
        success = uvx_ops.run_tool(command, args, isolated=True)
    else:
        success = tools_ops.run(command, args)
    
    if not success:
        raise typer.Exit(1)


@app.command("install")
@instrument_command("tool_install", track_args=True) 
def install(
    pkgs: list[str] = typer.Argument(
        ...,
        metavar="PACKAGE...",
        help="One or more PyPI package names to install",
    ),
    isolated: bool = typer.Option(
        False,
        "--isolated", 
        "-i",
        help="Install with uvx in isolated environment"
    ),
    python: Optional[str] = typer.Option(
        None,
        "--python",
        "-p",
        help="Python version for uvx installation"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f", 
        help="Force reinstall if exists (uvx only)"
    ),
):
    """Install tools (project venv or uvx isolated)."""
    add_span_attributes(**{
        ToolAttributes.OPERATION: ToolOperations.INSTALL,
        ToolAttributes.ISOLATED: isolated,
        ToolAttributes.PACKAGE_COUNT: len(pkgs)
    })
    
    if isolated:
        failed = []
        for pkg in pkgs:
            if not uvx_ops.install_tool(pkg, python=python, force=force):
                failed.append(pkg)
        
        if failed:
            colour(f"❌ Failed to install: {', '.join(failed)}", "red")
            raise typer.Exit(1)
        else:
            colour(f"✅ Successfully installed {len(pkgs)} tools with uvx", "green")
    else:
        tools_ops.install(pkgs)


@app.command("dir")
@instrument_command("tool_dir", track_args=True)
def dir_() -> None:
    """Print the venv's bin directory that hosts console-scripts."""
    add_span_attributes(**{ToolAttributes.OPERATION: ToolOperations.DIRECTORY})
    colour(tools_ops.tool_dir(), "cyan")


# ──────────────────────────────────────────────────────────────────────────────
# uvx Commands (New Functionality)
# ──────────────────────────────────────────────────────────────────────────────

@app.command("uvx-install")
@instrument_command("uvx_install", track_args=True)
def uvx_install(
    package: str = typer.Argument(..., help="Package to install with uvx"),
    python: Optional[str] = typer.Option(
        None,
        "--python", 
        "-p",
        help="Python version to use"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinstall if exists"
    ),
):
    """Install a tool with uvx in an isolated environment."""
    success = uvx_ops.install_tool(package, python=python, force=force)
    if not success:
        raise typer.Exit(1)


@app.command("uvx-run")
@instrument_command("uvx_run", track_args=True)
def uvx_run(
    tool_and_args: list[str] = typer.Argument(
        ...,
        metavar="TOOL [ARGS]...",
        help="Tool and arguments to run with uvx"
    ),
):
    """Run a tool with uvx (auto-installs if needed)."""
    if not tool_and_args:
        typer.echo("No tool specified", err=True)
        raise typer.Exit(1)
    
    tool, *args = tool_and_args
    success = uvx_ops.run_tool(tool, args, isolated=True)
    if not success:
        raise typer.Exit(1)


@app.command("uvx-list")
@instrument_command("uvx_list", track_args=True)
def uvx_list():
    """List all uvx-installed tools."""
    tools = uvx_ops.list_tools()
    
    if not tools:
        console.print("No uvx tools installed", style="yellow")
        return
    
    table = Table(title="uvx Installed Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Python", style="blue")
    table.add_column("Apps", style="magenta")
    
    for tool in tools:
        apps_str = ", ".join(tool.apps) if tool.apps else "none"
        table.add_row(tool.name, tool.version, tool.python_version, apps_str)
    
    console.print(table)


@app.command("uvx-uninstall")
@instrument_command("uvx_uninstall", track_args=True) 
def uvx_uninstall(
    package: str = typer.Argument(..., help="Package to uninstall"),
):
    """Uninstall a uvx tool."""
    success = uvx_ops.uninstall_tool(package)
    if not success:
        raise typer.Exit(1)


@app.command("uvx-upgrade")
@instrument_command("uvx_upgrade", track_args=True)
def uvx_upgrade(
    package: str = typer.Argument(..., help="Package to upgrade"),
):
    """Upgrade a uvx tool to the latest version."""
    success = uvx_ops.upgrade_tool(package)
    if not success:
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Value-Add Commands
# ──────────────────────────────────────────────────────────────────────────────

@app.command("recommend")
@instrument_command("tool_recommend", track_args=True)
def recommend(
    category: Optional[str] = typer.Argument(
        None, 
        help="Category: linting, formatting, testing, development, documentation"
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a", 
        help="Show all recommendations, not just top picks"
    ),
):
    """Get smart tool recommendations."""
    recommendations = uvx_ops.get_recommendations(category)
    
    if not recommendations:
        console.print("No recommendations found", style="yellow")
        return
    
    add_span_attributes(**{
        ToolAttributes.OPERATION: ToolOperations.RECOMMEND,
        ToolAttributes.CATEGORY: category or "all",
        ToolAttributes.RECOMMENDATION_COUNT: len(recommendations)
    })
    
    table = Table(title=f"Tool Recommendations - {category or 'All Categories'}")
    table.add_column("Tool", style="cyan")
    table.add_column("Category", style="blue") 
    table.add_column("Description", style="white")
    table.add_column("Use Case", style="green")
    table.add_column("Priority", style="magenta")
    
    display_recommendations = recommendations if show_all else recommendations[:5]
    
    for rec in display_recommendations:
        table.add_row(
            rec.name,
            rec.category,
            rec.description,
            rec.use_case,
            str(rec.priority)
        )
    
    console.print(table)
    
    if not show_all and len(recommendations) > 5:
        console.print(f"... and {len(recommendations) - 5} more. Use --all to see them.", style="dim")


@app.command("health")
@instrument_command("tool_health", track_args=True)
def health():
    """Check tool environment health."""
    health_info = uvx_ops.health_check()
    
    add_span_attributes(**{
        ToolAttributes.OPERATION: ToolOperations.HEALTH_CHECK,
        ToolAttributes.HEALTH_STATUS: "healthy" if not health_info["issues"] else "issues"
    })
    
    console.print("🔍 Tool Environment Health Check", style="bold")
    console.print()
    
    # uvx Status
    if health_info["uvx_available"]:
        console.print("✅ uvx is available", style="green")
        if "uvx_version" in health_info:
            console.print(f"   Version: {health_info['uvx_version']}", style="dim")
    else:
        console.print("❌ uvx is not available", style="red")
    
    # Tool Count
    tool_count = health_info["tool_count"]
    console.print(f"📦 {tool_count} tools installed with uvx", style="blue")
    
    # Issues
    if health_info["issues"]:
        console.print("⚠️  Issues found:", style="yellow")
        for issue in health_info["issues"]:
            console.print(f"   • {issue}", style="yellow")
    
    # Recommendations
    if health_info["recommendations"]:
        console.print("💡 Recommendations:", style="cyan")
        for rec in health_info["recommendations"]:
            console.print(f"   • {rec}", style="cyan")
    
    if not health_info["issues"]:
        console.print("✅ All systems healthy!", style="green bold")


@app.command("sync")
@instrument_command("tool_sync", track_args=True)
def sync(
    profile: str = typer.Option(
        "default",
        "--profile",
        "-p",
        help="Tool profile to sync (default, linting, dev, etc.)"
    ),
    install: bool = typer.Option(
        False,
        "--install",
        "-i",
        help="Install missing tools"
    ),
):
    """Sync tool environment with recommended profile."""
    add_span_attributes(**{
        ToolAttributes.OPERATION: ToolOperations.SYNC,
        ToolAttributes.PROFILE: profile
    })
    
    # Tool profiles
    profiles = {
        "default": ["ruff", "black", "pytest"],
        "linting": ["ruff", "mypy", "bandit"], 
        "formatting": ["black", "isort"],
        "testing": ["pytest", "coverage", "tox"],
        "dev": ["httpie", "ipython", "ruff", "black", "pytest"],
        "docs": ["mkdocs", "sphinx"]
    }
    
    if profile not in profiles:
        console.print(f"❌ Unknown profile: {profile}", style="red")
        console.print(f"Available profiles: {', '.join(profiles.keys())}", style="dim")
        raise typer.Exit(1)
    
    required_tools = profiles[profile]
    installed_tools = {tool.name for tool in uvx_ops.list_tools()}
    missing_tools = [tool for tool in required_tools if tool not in installed_tools]
    
    console.print(f"🔄 Syncing profile: {profile}", style="bold")
    console.print(f"Required tools: {', '.join(required_tools)}")
    
    if missing_tools:
        console.print(f"Missing tools: {', '.join(missing_tools)}", style="yellow")
        
        if install:
            console.print("Installing missing tools...", style="blue")
            for tool in missing_tools:
                console.print(f"Installing {tool}...")
                uvx_ops.install_tool(tool)
        else:
            console.print("Use --install to install missing tools", style="dim")
    else:
        console.print("✅ All tools are installed!", style="green")