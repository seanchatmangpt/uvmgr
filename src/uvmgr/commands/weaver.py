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

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from uvmgr.core.instrumentation import instrument_command
from uvmgr.core.shell import colour

from .. import main as cli_root

console = Console()
app = typer.Typer(help="OpenTelemetry Weaver semantic convention tools")
cli_root.app.add_typer(app, name="weaver")

# Paths
WEAVER_PATH = Path(__file__).parent.parent.parent.parent / "tools" / "weaver"
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"
WEAVER_URL = "https://github.com/open-telemetry/weaver/releases/latest"


@app.command("install")
@instrument_command("weaver_install")
def install(
    version: str = typer.Option("latest", "--version", "-v", help="Weaver version to install"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install or update OpenTelemetry Weaver."""
    console.print("[bold]Installing OpenTelemetry Weaver...[/bold]\n")

    # Check if already installed
    if WEAVER_PATH.exists() and not force:
        # Check version
        result = subprocess.run(
            [str(WEAVER_PATH), "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            current_version = result.stdout.strip()
            console.print(f"[green]✓ Weaver already installed: {current_version}[/green]")
            if not typer.confirm("Reinstall?"):
                raise typer.Exit()

    # Detect platform
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            artifact = "weaver-aarch64-apple-darwin"
        else:
            artifact = "weaver-x86_64-apple-darwin"
    elif system == "linux":
        if machine == "aarch64":
            artifact = "weaver-aarch64-unknown-linux-gnu"
        else:
            artifact = "weaver-x86_64-unknown-linux-gnu"
    elif system == "windows":
        artifact = "weaver-x86_64-pc-windows-msvc"
    else:
        console.print(f"[red]Unsupported platform: {system}/{machine}[/red]")
        raise typer.Exit(1)

    # Get download URL
    if version == "latest":
        api_url = "https://api.github.com/repos/open-telemetry/weaver/releases/latest"
        result = subprocess.run(
            ["curl", "-s", api_url],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            release_data = json.loads(result.stdout)
            version = release_data["tag_name"]

    download_url = f"https://github.com/open-telemetry/weaver/releases/download/{version}/{artifact}.tar.xz"

    console.print(f"Platform: {system}/{machine}")
    console.print(f"Artifact: {artifact}")
    console.print(f"Version: {version}")
    console.print(f"URL: {download_url}\n")

    # Create tools directory
    tools_dir = WEAVER_PATH.parent
    tools_dir.mkdir(exist_ok=True)

    # Download and extract
    with console.status("Downloading Weaver..."):
        subprocess.run(
            ["curl", "-L", "-o", "weaver.tar.xz", download_url],
            cwd=tools_dir,
            check=True
        )

    with console.status("Extracting..."):
        subprocess.run(
            ["tar", "-xf", "weaver.tar.xz"],
            cwd=tools_dir,
            check=True
        )
        (tools_dir / "weaver.tar.xz").unlink()

    # Make executable
    weaver_bin = tools_dir / artifact / "weaver"
    if weaver_bin.exists():
        weaver_bin.chmod(0o755)
        # Create symlink
        if WEAVER_PATH.exists():
            WEAVER_PATH.unlink()
        WEAVER_PATH.symlink_to(f"{artifact}/weaver")

    # Verify installation
    result = subprocess.run(
        [str(WEAVER_PATH), "--version"],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode == 0:
        console.print(f"\n[green]✓ Weaver {result.stdout.strip()} installed successfully![/green]")
    else:
        console.print("\n[red]✗ Installation failed[/red]")
        raise typer.Exit(1)


@app.command("check")
@instrument_command("weaver_check")
def check(
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    future: bool = typer.Option(True, "--future", help="Enable latest validation rules"),
    policy: Path | None = typer.Option(None, "--policy", "-p", help="Rego policy file"),
):
    """Validate semantic convention registry."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Checking registry: {registry}[/bold]\n")

    cmd = [str(WEAVER_PATH), "registry", "check", "-r", str(registry)]
    if future:
        cmd.append("--future")
    if policy:
        cmd.extend(["-p", str(policy)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        console.print("[green]✓ Registry validation passed![/green]")
        if result.stdout:
            console.print(result.stdout)
    else:
        console.print("[red]✗ Registry validation failed:[/red]")
        console.print(result.stderr)
        raise typer.Exit(1)


@app.command("generate")
@instrument_command("weaver_generate")
def generate(
    template: str = typer.Argument(..., help="Template type (e.g., python, markdown, go)"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    config: Path | None = typer.Option(None, "--config", "-c", help="Weaver config file"),
):
    """Generate code from semantic conventions."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Generating {template} from {registry}[/bold]\n")

    # For now, use our custom Python generator
    if template == "python":
        from weaver_forge.validate_semconv import generate_python_constants
        generate_python_constants()
        console.print("[green]✓ Python constants generated![/green]")
        return

    # For other templates, try Weaver's built-in generators
    cmd = [
        str(WEAVER_PATH), "registry", "generate",
        "-r", str(registry),
        "-t", template,
        str(output)
    ]

    if config:
        cmd.extend(["-c", str(config)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        console.print(f"[green]✓ Generated {template} in {output}[/green]")
    else:
        console.print("[red]✗ Generation failed:[/red]")
        console.print(result.stderr)
        raise typer.Exit(1)


@app.command("resolve")
@instrument_command("weaver_resolve")
def resolve(
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, yaml)"),
):
    """Resolve semantic convention references and inheritance."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Resolving registry: {registry}[/bold]\n")

    cmd = [
        str(WEAVER_PATH), "registry", "resolve",
        "-r", str(registry),
        "-f", format
    ]

    if output:
        cmd.extend(["-o", str(output)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        if output:
            console.print(f"[green]✓ Resolved registry saved to {output}[/green]")
        # Pretty print the output
        elif format == "json":
            data = json.loads(result.stdout)
            console.print(json.dumps(data, indent=2))
        else:
            console.print(result.stdout)
    else:
        console.print("[red]✗ Resolution failed:[/red]")
        console.print(result.stderr)
        raise typer.Exit(1)


@app.command("search")
@instrument_command("weaver_search")
def search(
    query: str = typer.Argument(..., help="Search query (regex supported)"),
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    type: str | None = typer.Option(None, "--type", "-t", help="Filter by type (attribute, metric, etc)"),
):
    """Search semantic conventions."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Searching for: {query}[/bold]\n")

    cmd = [
        str(WEAVER_PATH), "registry", "search",
        "-r", str(registry),
        query
    ]

    if type:
        cmd.extend(["--type", type])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        if result.stdout.strip():
            console.print(result.stdout)
        else:
            console.print("[yellow]No matches found[/yellow]")
    else:
        console.print("[red]✗ Search failed:[/red]")
        console.print(result.stderr)
        raise typer.Exit(1)


@app.command("stats")
@instrument_command("weaver_stats")
def stats(
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
):
    """Show registry statistics."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Registry Statistics: {registry}[/bold]\n")

    # Get registry stats using resolve
    cmd = [
        str(WEAVER_PATH), "registry", "resolve",
        "-r", str(registry),
        "-f", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        data = json.loads(result.stdout)

        # Count different types
        stats = {
            "groups": 0,
            "attributes": 0,
            "metrics": 0,
            "spans": 0,
            "events": 0,
        }

        if "groups" in data:
            for group in data["groups"]:
                stats["groups"] += 1
                if "attributes" in group:
                    stats["attributes"] += len(group["attributes"])
                if group.get("type") == "span":
                    stats["spans"] += 1
                elif group.get("type") == "event":
                    stats["events"] += 1

        if "metrics" in data:
            stats["metrics"] = len(data["metrics"])

        # Display stats
        table = Table(title="Registry Statistics")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")

        for type_name, count in stats.items():
            if count > 0:
                table.add_row(type_name.capitalize(), str(count))

        console.print(table)
    else:
        console.print("[red]✗ Failed to get statistics:[/red]")
        console.print(result.stderr)
        raise typer.Exit(1)


@app.command("diff")
@instrument_command("weaver_diff")
def diff(
    registry1: Path = typer.Argument(..., help="First registry to compare"),
    registry2: Path = typer.Argument(..., help="Second registry to compare"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output diff to file"),
):
    """Compare two semantic convention registries."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print("[bold]Comparing registries:[/bold]")
    console.print(f"  Registry 1: {registry1}")
    console.print(f"  Registry 2: {registry2}\n")

    # Resolve both registries
    cmd1 = [str(WEAVER_PATH), "registry", "resolve", "-r", str(registry1), "-f", "json"]
    cmd2 = [str(WEAVER_PATH), "registry", "resolve", "-r", str(registry2), "-f", "json"]

    result1 = subprocess.run(cmd1, capture_output=True, text=True, check=False)
    result2 = subprocess.run(cmd2, capture_output=True, text=True, check=False)

    if result1.returncode != 0 or result2.returncode != 0:
        console.print("[red]✗ Failed to resolve registries[/red]")
        raise typer.Exit(1)

    data1 = json.loads(result1.stdout)
    data2 = json.loads(result2.stdout)

    # Simple diff implementation
    diff_results = {
        "added": [],
        "removed": [],
        "modified": []
    }

    # Compare groups
    groups1 = {g["id"]: g for g in data1.get("groups", [])}
    groups2 = {g["id"]: g for g in data2.get("groups", [])}

    for id in set(groups1.keys()) | set(groups2.keys()):
        if id in groups1 and id not in groups2:
            diff_results["removed"].append(f"Group: {id}")
        elif id not in groups1 and id in groups2:
            diff_results["added"].append(f"Group: {id}")
        elif groups1.get(id) != groups2.get(id):
            diff_results["modified"].append(f"Group: {id}")

    # Display diff
    if any(diff_results.values()):
        if diff_results["added"]:
            console.print("[green]Added:[/green]")
            for item in diff_results["added"]:
                console.print(f"  + {item}")

        if diff_results["removed"]:
            console.print("\n[red]Removed:[/red]")
            for item in diff_results["removed"]:
                console.print(f"  - {item}")

        if diff_results["modified"]:
            console.print("\n[yellow]Modified:[/yellow]")
            for item in diff_results["modified"]:
                console.print(f"  ~ {item}")
    else:
        console.print("[green]✓ No differences found[/green]")

    # Save diff to file if requested
    if output:
        output.write_text(json.dumps(diff_results, indent=2))
        console.print(f"\n[green]✓ Diff saved to {output}[/green]")


@app.command("init")
@instrument_command("weaver_init")
def init(
    name: str = typer.Option("myproject", "--name", "-n", help="Registry name"),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Registry path"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing registry"),
):
    """Initialize a new semantic convention registry."""
    registry_path = path / "registry"

    if registry_path.exists() and not force:
        console.print(f"[red]Registry already exists at {registry_path}[/red]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit()

    console.print(f"[bold]Initializing semantic convention registry: {name}[/bold]\n")

    # Create directory structure
    registry_path.mkdir(parents=True, exist_ok=True)
    models_path = registry_path / "models"
    models_path.mkdir(exist_ok=True)

    # Create registry manifest
    manifest = {
        "name": name,
        "description": f"Semantic conventions for {name}",
        "version": "1.0.0",
        "semconv_version": "1.26.0",
        "schema_base_url": f"https://example.com/schemas/{name}",
        "models": [
            {
                "path": "models/common.yaml",
                "description": "Common attributes and conventions"
            }
        ]
    }

    manifest_path = registry_path / "registry_manifest.yaml"
    import yaml
    manifest_path.write_text(yaml.dump(manifest, default_flow_style=False))

    # Create example model
    example_model = """groups:
  - id: example
    type: attribute_group
    brief: 'Example attribute group'
    attributes:
      - id: name
        type: string
        brief: 'Example name attribute'
        note: 'This is an example attribute'
        examples: ['foo', 'bar']
        requirement_level: required
        stability: stable
        
      - id: count
        type: int
        brief: 'Example count attribute'
        note: 'Number of items'
        requirement_level: recommended
        stability: stable
"""

    model_path = models_path / "common.yaml"
    model_path.write_text(example_model)

    # Create .gitignore
    gitignore = """# Generated files
/docs/
*.pyc
__pycache__/
.DS_Store
"""
    (registry_path / ".gitignore").write_text(gitignore)

    # Display created structure
    tree = Tree(f"[bold]{registry_path}[/bold]")
    tree.add("registry_manifest.yaml")
    models_tree = tree.add("models/")
    models_tree.add("common.yaml")
    tree.add(".gitignore")

    console.print(tree)
    console.print(f"\n[green]✓ Registry '{name}' initialized successfully![/green]")
    console.print("\nNext steps:")
    console.print("  1. Edit models/common.yaml to define your conventions")
    console.print("  2. Run 'uvmgr weaver check' to validate")
    console.print("  3. Run 'uvmgr weaver generate python' to generate code")


@app.command("docs")
@instrument_command("weaver_docs")
def docs(
    registry: Path = typer.Option(REGISTRY_PATH, "--registry", "-r", help="Registry path"),
    output: Path = typer.Option(Path("docs"), "--output", "-o", help="Output directory"),
    format: str = typer.Option("markdown", "--format", "-f", help="Documentation format"),
):
    """Generate documentation from semantic conventions."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Generating {format} documentation[/bold]\n")

    # For now, manually create markdown docs
    if format == "markdown":
        output.mkdir(parents=True, exist_ok=True)

        # Resolve registry to get all data
        cmd = [
            str(WEAVER_PATH), "registry", "resolve",
            "-r", str(registry),
            "-f", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            data = json.loads(result.stdout)

            # Generate index
            index_content = "# Semantic Conventions Documentation\n\n"
            index_content += "## Attribute Groups\n\n"

            for group in data.get("groups", []):
                group_file = output / f"{group['id']}.md"
                index_content += f"- [{group['id']}]({group['id']}.md) - {group.get('brief', '')}\n"

                # Generate group documentation
                group_content = f"# {group['id']} Attributes\n\n"
                group_content += f"{group.get('brief', '')}\n\n"

                if "attributes" in group:
                    group_content += "## Attributes\n\n"
                    group_content += "| Attribute | Type | Description | Requirement Level |\n"
                    group_content += "|-----------|------|-------------|------------------|\n"

                    for attr in group["attributes"]:
                        req_level = attr.get("requirement_level", "optional")
                        group_content += f"| `{attr['id']}` | {attr.get('type', 'string')} | {attr.get('brief', '')} | {req_level} |\n"

                group_file.write_text(group_content)

            # Write index
            index_file = output / "index.md"
            index_file.write_text(index_content)

            console.print(f"[green]✓ Documentation generated in {output}[/green]")
        else:
            console.print("[red]✗ Failed to generate documentation[/red]")
            raise typer.Exit(1)
    else:
        console.print(f"[red]Format '{format}' not yet supported[/red]")
        raise typer.Exit(1)


@app.command("version")
@instrument_command("weaver_version")
def version():
    """Show Weaver version information."""
    if not WEAVER_PATH.exists():
        console.print("[red]Weaver not installed. Run: uvmgr weaver install[/red]")
        raise typer.Exit(1)

    result = subprocess.run(
        [str(WEAVER_PATH), "--version"],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode == 0:
        version_info = result.stdout.strip()

        # Create a nice panel
        panel = Panel(
            f"[green]{version_info}[/green]\n\n"
            f"Path: {WEAVER_PATH}\n"
            f"Registry: {REGISTRY_PATH}",
            title="OpenTelemetry Weaver",
            border_style="green"
        )
        console.print(panel)
    else:
        console.print("[red]✗ Failed to get version[/red]")
        raise typer.Exit(1)
