"""
uvmgr.commands.project - Project Creation and Management
======================================================

Project scaffolding with Substrate-inspired features and comprehensive templates.

This module provides CLI commands for creating new Python projects with
various templates and configurations, including Substrate-inspired features
for modern Python development workflows.

Key Features
-----------
• **Multiple Templates**: Basic, Substrate, FastAPI, CLI templates
• **Substrate Features**: Modern development workflow integration
• **DevOps Integration**: GitHub Actions, DevContainers, pre-commit hooks
• **Code Quality**: Conventional commits and semantic versioning
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **new**: Create a new project with customizable features
- **substrate**: Create a Substrate-inspired project with all features

Template Options
---------------
- **basic**: Simple Python project structure
- **substrate**: Full-featured modern Python project
- **fastapi**: FastAPI web application template
- **cli**: Command-line application template

Substrate Features
-----------------
- **DevContainers**: Containerized development environment
- **GitHub Actions**: Automated CI/CD pipelines
- **Pre-commit Hooks**: Code quality enforcement
- **Conventional Commits**: Standardized commit messages
- **Semantic Versioning**: Automated version management

Examples
--------
    >>> # Create basic project
    >>> uvmgr project new my-app
    >>> 
    >>> # Create Substrate project
    >>> uvmgr project substrate my-app --fastapi
    >>> 
    >>> # Create with specific features
    >>> uvmgr project new my-app --template fastapi --github-actions

See Also
--------
- :mod:`uvmgr.ops.project` : Project operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ProjectAttributes, ProjectOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import project as project_ops

app = typer.Typer(help="Project scaffolding with Substrate-inspired features")


@app.command("substrate")
@instrument_command("project_substrate", track_args=True)
def substrate_project(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Directory / project name"),
    fastapi: bool = typer.Option(False, "--fastapi", help="Include FastAPI API skeleton"),
    typer_cli: bool = typer.Option(True, "--typer/--no-typer", help="Include Typer CLI skeleton"),
):
    """Create a new project with full Substrate-inspired features."""
    # Forward to main command with substrate template
    return new(
        ctx=ctx,
        name=name,
        template="substrate",
        substrate=True,
        fastapi=fastapi,
        typer_cli=typer_cli,
        dev_containers=True,
        github_actions=True,
        pre_commit=True,
        conventional_commits=True,
        semantic_versioning=True,
    )


@app.command()
@instrument_command("project_new", track_args=True)
def new(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Directory / project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template: basic, substrate, fastapi, cli"),
    substrate: bool = typer.Option(False, "--substrate", help="Generate Substrate-inspired project"),
    fastapi: bool = typer.Option(False, "--fastapi", help="Include FastAPI API skeleton"),
    typer_cli: bool = typer.Option(True, "--typer/--no-typer", help="Include Typer CLI skeleton"),
    dev_containers: bool = typer.Option(False, "--dev-containers", help="Include DevContainer configuration"),
    github_actions: bool = typer.Option(False, "--github-actions", help="Include GitHub Actions CI/CD"),
    pre_commit: bool = typer.Option(False, "--pre-commit", help="Include pre-commit hooks"),
    conventional_commits: bool = typer.Option(False, "--conventional-commits", help="Enable conventional commits"),
    semantic_versioning: bool = typer.Option(False, "--semantic-versioning", help="Enable semantic versioning"),
):
    # Auto-enable substrate features if substrate template selected
    if template == "substrate" or substrate:
        substrate = True
        dev_containers = True
        github_actions = True
        pre_commit = True
        conventional_commits = True
        semantic_versioning = True

    # Track project creation
    add_span_attributes(**{
        ProjectAttributes.OPERATION: ProjectOperations.CREATE,
        ProjectAttributes.NAME: name,
        ProjectAttributes.LANGUAGE: "python",
        "project.template": template,
        "project.substrate": substrate,
        "project.fastapi": fastapi,
        "project.typer_cli": typer_cli,
        "project.dev_containers": dev_containers,
        "project.github_actions": github_actions,
        "project.pre_commit": pre_commit,
        "project.conventional_commits": conventional_commits,
        "project.semantic_versioning": semantic_versioning,
    })
    add_span_event("project.new.started", {
        "name": name,
        "template": template,
        "substrate": substrate,
        "features": {
            "fastapi": fastapi,
            "typer_cli": typer_cli,
            "dev_containers": dev_containers,
            "github_actions": github_actions,
            "pre_commit": pre_commit,
            "conventional_commits": conventional_commits,
            "semantic_versioning": semantic_versioning,
        }
    })

    payload = project_ops.new(
        name, 
        template=template,
        substrate=substrate,
        fastapi=fastapi, 
        typer_cli=typer_cli,
        dev_containers=dev_containers,
        github_actions=github_actions,
        pre_commit=pre_commit,
        conventional_commits=conventional_commits,
        semantic_versioning=semantic_versioning,
    )

    # Track successful creation
    add_span_attributes(**{
        "project.path": payload.get("path"),
        "project.created": True,
    })
    add_span_event("project.new.completed", {
        "path": payload.get("path"),
        "success": True
    })
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ created project in {payload['path']}", "green")


@app.command("status")
@instrument_command("project_status", track_args=True)
def status(ctx: typer.Context):
    """Show current project status and uvmgr configuration."""
    import os
    from pathlib import Path
    
    # Get basic project info
    cwd = Path.cwd()
    project_info = {
        "path": str(cwd),
        "name": cwd.name,
        "uvmgr_version": "0.0.0",  # This would be dynamic in a real implementation
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "has_pyproject": (cwd / "pyproject.toml").exists(),
        "has_venv": (cwd / ".venv").exists(),
        "has_tests": (cwd / "tests").exists(),
        "has_src": (cwd / "src").exists(),
    }
    
    # Track status check
    add_span_attributes(**{
        ProjectAttributes.OPERATION: "status",
        ProjectAttributes.NAME: project_info["name"],
        "project.path": project_info["path"],
    })
    add_span_event("project.status.checked", project_info)
    
    if ctx.meta.get("json"):
        dump_json(project_info)
    else:
        colour(f"📁 Project: {project_info['name']}", "blue")
        colour(f"📍 Path: {project_info['path']}", "cyan")
        colour(f"🐍 Python: {project_info['python_version']}", "green")
        colour(f"📦 pyproject.toml: {'✓' if project_info['has_pyproject'] else '✗'}", 
               "green" if project_info['has_pyproject'] else "red")
        colour(f"🔧 Virtual env: {'✓' if project_info['has_venv'] else '✗'}", 
               "green" if project_info['has_venv'] else "yellow")
        colour(f"🧪 Tests dir: {'✓' if project_info['has_tests'] else '✗'}", 
               "green" if project_info['has_tests'] else "yellow")
        colour(f"📂 Source dir: {'✓' if project_info['has_src'] else '✗'}", 
               "green" if project_info['has_src'] else "yellow")
