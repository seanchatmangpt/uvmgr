"""
Container management commands for uvmgr.

This module provides Docker and Podman integration commands, addressing the critical
container support gap. Implements the 80/20 principle: 10% effort for 40% value.

Commands:
- build : Build container images
- run : Run containers
- compose : Docker Compose / Podman Pod management
- exec : Execute commands in containers
- logs : View container logs
- dev : Development container management

Example:
    $ uvmgr container build --tag myapp:latest
    $ uvmgr container run myapp:latest --port 8080:80
    $ uvmgr container compose up
    $ uvmgr container dev create --language python
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List, Dict
import json
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.containers import (
    get_container_manager,
    ContainerConfig,
    ComposeConfig,
    ContainerRuntime,
    create_dev_container_config
)
from uvmgr.core.shell import dump_json

app = typer.Typer(help="🐳 Container management (Docker/Podman)")
console = Console()


@app.command("build")
@instrument_command("container_build", track_args=True)
def build_container(
    dockerfile: str = typer.Option("Dockerfile", "--file", "-f", help="Dockerfile path"),
    tag: str = typer.Option(None, "--tag", "-t", help="Image tag (name:version)"),
    build_arg: List[str] = typer.Option([], "--build-arg", help="Build arguments (KEY=VALUE)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Build without cache"),
    platform: Optional[str] = typer.Option(None, "--platform", help="Target platform"),
):
    """🏗️ Build a container image."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    # Parse tag to get image name
    if not tag:
        # Try to infer from project
        project_name = Path.cwd().name
        tag = f"{project_name}:latest"
    
    image, version = tag.split(":") if ":" in tag else (tag, "latest")
    
    # Parse build args
    build_args_dict = {}
    for arg in build_arg:
        if "=" in arg:
            key, value = arg.split("=", 1)
            build_args_dict[key] = value
    
    config = ContainerConfig(
        name=image,
        image=image,
        tag=version,
        dockerfile=dockerfile,
        build_args=build_args_dict
    )
    
    console.print(Panel(
        f"🏗️  [bold]Building Container Image[/bold]\n"
        f"Runtime: {manager.runtime.value}\n"
        f"Image: {tag}\n"
        f"Dockerfile: {dockerfile}",
        title="Container Build"
    ))
    
    add_span_attributes(**{
        "container.runtime": manager.runtime.value,
        "container.image": image,
        "container.tag": version
    })
    
    import asyncio
    result = asyncio.run(manager.build(config, no_cache=no_cache))
    
    if result.success:
        console.print(f"[green]✅ Successfully built {tag}[/green]")
        add_span_event("container.build.success", {"image": tag})
    else:
        console.print(f"[red]❌ Build failed: {result.error}[/red]")
        add_span_event("container.build.failed", {"error": result.error})
        raise typer.Exit(1)


@app.command("run")
@instrument_command("container_run", track_args=True)
def run_container(
    image: str = typer.Argument(..., help="Image to run (name:tag)"),
    name: Optional[str] = typer.Option(None, "--name", help="Container name"),
    port: List[str] = typer.Option([], "--port", "-p", help="Port mapping (HOST:CONTAINER)"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variables (KEY=VALUE)"),
    volume: List[str] = typer.Option([], "--volume", "-v", help="Volume mount (HOST:CONTAINER)"),
    detach: bool = typer.Option(True, "--detach/--no-detach", "-d/-D", help="Run in background"),
    rm: bool = typer.Option(False, "--rm", help="Remove container after exit"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Override container command"),
):
    """🚀 Run a container."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    # Parse image tag
    if ":" not in image:
        image = f"{image}:latest"
    image_name, tag = image.split(":", 1)
    
    # Parse ports
    ports_dict = {}
    for p in port:
        if ":" in p:
            host, container = p.split(":", 1)
            ports_dict[host] = container
    
    # Parse environment variables
    env_dict = {}
    for e in env:
        if "=" in e:
            key, value = e.split("=", 1)
            env_dict[key] = value
    
    # Parse volumes
    volumes_dict = {}
    for v in volume:
        if ":" in v:
            host, container = v.split(":", 1)
            volumes_dict[host] = container
    
    config = ContainerConfig(
        name=name or f"{image_name}-{tag}",
        image=image_name,
        tag=tag,
        ports=ports_dict,
        env_vars=env_dict,
        volumes=volumes_dict,
        command=command.split() if command else None
    )
    
    console.print(Panel(
        f"🚀 [bold]Running Container[/bold]\n"
        f"Runtime: {manager.runtime.value}\n"
        f"Image: {image}\n"
        f"Name: {config.name}\n"
        f"Detached: {'Yes' if detach else 'No'}",
        title="Container Run"
    ))
    
    import asyncio
    result = asyncio.run(manager.run(config, detach=detach, rm=rm))
    
    if result.success:
        if detach and result.container_id:
            console.print(f"[green]✅ Container started: {result.container_id[:12]}[/green]")
            console.print(f"   Name: {config.name}")
            console.print(f"   View logs: uvmgr container logs {config.name}")
        else:
            console.print(f"[green]✅ Container finished successfully[/green]")
    else:
        console.print(f"[red]❌ Failed to run container: {result.error}[/red]")
        raise typer.Exit(1)


# Compose sub-commands
compose_app = typer.Typer(help="Docker Compose / Podman Pod management")
app.add_typer(compose_app, name="compose")


@compose_app.command("up")
@instrument_command("container_compose_up", track_args=True)
def compose_up(
    file: str = typer.Option("docker-compose.yml", "--file", "-f", help="Compose file"),
    detach: bool = typer.Option(True, "--detach/--no-detach", "-d/-D", help="Run in background"),
    build: bool = typer.Option(False, "--build", help="Build images before starting"),
    service: List[str] = typer.Argument(None, help="Specific services to start"),
):
    """Start services defined in compose file."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🚀 [bold]Starting Compose Services[/bold]\n"
        f"Runtime: {manager.runtime.value}\n"
        f"File: {file}\n"
        f"Build: {'Yes' if build else 'No'}\n"
        f"Services: {', '.join(service) if service else 'All'}",
        title="Compose Up"
    ))
    
    import asyncio
    result = asyncio.run(manager.compose_up(file, detach=detach, build=build, services=service))
    
    if result.success:
        console.print(f"[green]✅ Services started successfully[/green]")
        if detach:
            console.print(f"   View logs: uvmgr container compose logs")
    else:
        console.print(f"[red]❌ Failed to start services: {result.error}[/red]")
        raise typer.Exit(1)


@compose_app.command("down")
@instrument_command("container_compose_down", track_args=True)
def compose_down(
    file: str = typer.Option("docker-compose.yml", "--file", "-f", help="Compose file"),
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove volumes"),
):
    """Stop and remove services."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🛑 [bold]Stopping Compose Services[/bold]\n"
        f"Runtime: {manager.runtime.value}\n"
        f"File: {file}\n"
        f"Remove Volumes: {'Yes' if volumes else 'No'}",
        title="Compose Down"
    ))
    
    import asyncio
    result = asyncio.run(manager.compose_down(file, volumes=volumes))
    
    if result.success:
        console.print(f"[green]✅ Services stopped and removed[/green]")
    else:
        console.print(f"[red]❌ Failed to stop services: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("exec")
@instrument_command("container_exec", track_args=True)
def exec_in_container(
    container: str = typer.Argument(..., help="Container name or ID"),
    command: List[str] = typer.Argument(..., help="Command to execute"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="User to run as"),
):
    """Execute command in running container."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    console.print(f"🔧 Executing in {container}: {' '.join(command)}")
    
    import asyncio
    result = asyncio.run(manager.exec(container, command, interactive=interactive, user=user))
    
    if result.success:
        if result.output:
            console.print(result.output)
    else:
        console.print(f"[red]❌ Execution failed: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("logs")
@instrument_command("container_logs", track_args=True) 
def view_logs(
    container: str = typer.Argument(..., help="Container name or ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: Optional[int] = typer.Option(None, "--tail", "-n", help="Number of lines to show"),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Show timestamps"),
):
    """View container logs."""
    
    manager = get_container_manager()
    
    if not manager.is_available():
        console.print("[red]❌ No container runtime found. Install Docker or Podman.[/red]")
        raise typer.Exit(1)
    
    import asyncio
    result = asyncio.run(manager.logs(container, follow=follow, tail=tail, timestamps=timestamps))
    
    if result.success:
        console.print(result.output)
    else:
        console.print(f"[red]❌ Failed to get logs: {result.error}[/red]")
        raise typer.Exit(1)


# Development container sub-commands
dev_app = typer.Typer(help="Development container management")
app.add_typer(dev_app, name="dev")


@dev_app.command("create")
@instrument_command("container_dev_create", track_args=True)
def create_dev_container(
    name: Optional[str] = typer.Option(None, "--name", help="Project name"),
    language: str = typer.Option("python", "--language", "-l", help="Programming language"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Language version"),
    build_only: bool = typer.Option(False, "--build-only", help="Only generate Dockerfile"),
):
    """Create a development container for the project."""
    
    project_name = name or Path.cwd().name
    
    # Default versions
    default_versions = {
        "python": "3.12",
        "node": "20",
        "go": "1.21",
        "rust": "latest",
        "java": "17"
    }
    
    version = version or default_versions.get(language, "latest")
    
    config = create_dev_container_config(project_name, language, version)
    
    # Generate Dockerfile
    dockerfile_content = _generate_dev_dockerfile(language, version)
    dockerfile_path = Path.cwd() / "Dockerfile.dev"
    
    console.print(Panel(
        f"🏗️  [bold]Creating Development Container[/bold]\n"
        f"Project: {project_name}\n"
        f"Language: {language} {version}\n"
        f"Dockerfile: {dockerfile_path}",
        title="Dev Container"
    ))
    
    # Write Dockerfile
    dockerfile_path.write_text(dockerfile_content)
    console.print(f"✅ Created {dockerfile_path}")
    
    if not build_only:
        manager = get_container_manager()
        
        if not manager.is_available():
            console.print("[yellow]⚠️  No container runtime found. Dockerfile created but not built.[/yellow]")
            return
        
        # Update config to use the generated dockerfile
        config.dockerfile = "Dockerfile.dev"
        
        # Build the container
        import asyncio
        result = asyncio.run(manager.build(config))
        
        if result.success:
            console.print(f"[green]✅ Built development container: {config.image}:{config.tag}[/green]")
            console.print(f"\nTo run: uvmgr container run {config.image}:{config.tag} --name {project_name}-dev")
        else:
            console.print(f"[red]❌ Build failed: {result.error}[/red]")


@app.command("status")
@instrument_command("container_status", track_args=True)
def container_status(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show container runtime status and info."""
    
    manager = get_container_manager()
    
    status_data = {
        "runtime": manager.runtime.value,
        "available": manager.is_available(),
        "project_root": str(manager.project_root)
    }
    
    if json_output:
        dump_json(status_data)
        return
    
    # Create status table
    table = Table(title="Container Runtime Status", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Runtime", manager.runtime.value)
    table.add_row("Available", "✅ Yes" if manager.is_available() else "❌ No")
    table.add_row("Project Root", str(manager.project_root))
    
    if manager.is_available():
        table.add_row("Status", "🟢 Ready")
    else:
        table.add_row("Status", "🔴 Not Available")
    
    console.print(table)
    
    if not manager.is_available():
        console.print("\n[yellow]💡 Install Docker or Podman to use container features[/yellow]")
        console.print("   Docker: https://docs.docker.com/get-docker/")
        console.print("   Podman: https://podman.io/getting-started/installation")


def _generate_dev_dockerfile(language: str, version: str) -> str:
    """Generate a development Dockerfile for the specified language."""
    
    templates = {
        "python": f"""FROM python:{version}-slim

WORKDIR /workspace

# Install development tools
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY . .

# Install dependencies if they exist
RUN if [ -f "pyproject.toml" ]; then uv pip install -e .; fi
RUN if [ -f "requirements.txt" ]; then uv pip install -r requirements.txt; fi

CMD ["/bin/bash"]
""",
        
        "node": f"""FROM node:{version}-alpine

WORKDIR /workspace

# Install development tools
RUN apk add --no-cache git curl bash

# Copy project files
COPY . .

# Install dependencies if they exist
RUN if [ -f "package.json" ]; then npm install; fi

CMD ["/bin/bash"]
""",
        
        "go": f"""FROM golang:{version}-alpine

WORKDIR /workspace

# Install development tools
RUN apk add --no-cache git curl bash build-base

# Copy project files
COPY . .

# Download dependencies if go.mod exists
RUN if [ -f "go.mod" ]; then go mod download; fi

CMD ["/bin/bash"]
""",
        
        "rust": f"""FROM rust:{version}

WORKDIR /workspace

# Install development tools
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Build if Cargo.toml exists
RUN if [ -f "Cargo.toml" ]; then cargo build; fi

CMD ["/bin/bash"]
""",
        
        "java": f"""FROM openjdk:{version}-slim

WORKDIR /workspace

# Install development tools
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    maven \\
    gradle \\
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

CMD ["/bin/bash"]
"""
    }
    
    return templates.get(language, templates["python"])