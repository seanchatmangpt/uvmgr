#!/usr/bin/env python3
"""
Demo script showcasing uvmgr's PyInstaller integration.

This demonstrates the end-to-end workflow of uvmgr packaging itself
as a standalone executable (eating its own dog food).
"""

import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_command(cmd: str, description: str):
    """Run a command and display the output."""
    console.print(f"\n[bold blue]Running:[/bold blue] {cmd}")
    console.print(f"[dim]{description}[/dim]\n")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            console.print("[green]✓[/green] Command succeeded")
            if result.stdout:
                console.print(Panel(result.stdout.strip(), title="Output", border_style="green"))
        else:
            console.print("[red]✗[/red] Command failed")
            if result.stderr:
                console.print(Panel(result.stderr.strip(), title="Error", border_style="red"))
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return False


def main():
    """Run the PyInstaller e2e demo."""
    console.print(Panel.fit(
        "[bold]uvmgr PyInstaller E2E Demo[/bold]\n\n"
        "This demo shows how uvmgr can package itself as a standalone executable.",
        border_style="cyan"
    ))

    # Step 1: Show current uvmgr version
    console.print("\n[bold cyan]Step 1:[/bold cyan] Check uvmgr version")
    run_command("uvmgr --version", "Display current uvmgr version")

    # Step 2: Generate a spec file
    console.print("\n[bold cyan]Step 2:[/bold cyan] Generate PyInstaller spec file")
    if run_command("uvmgr build spec --name uvmgr-demo", "Generate a customizable spec file"):
        console.print("[dim]Spec file created: uvmgr-demo.spec[/dim]")

    # Step 3: Build uvmgr as an executable
    console.print("\n[bold cyan]Step 3:[/bold cyan] Build uvmgr executable")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Building executable...", total=None)

        success = run_command(
            "uvmgr build dogfood --test --version --platform",
            "Build uvmgr as a standalone executable with testing"
        )

        progress.update(task, completed=True)

    if success:
        # Step 4: List the built executable
        console.print("\n[bold cyan]Step 4:[/bold cyan] Verify built executable")
        run_command("ls -la dist/", "List contents of dist directory")

        # Find the executable
        dist_path = Path("dist")
        if dist_path.exists():
            executables = list(dist_path.glob("uvmgr-*"))
            if executables:
                exe_path = executables[0]
                console.print(f"\n[green]Found executable:[/green] {exe_path}")

                # Step 5: Test the standalone executable
                console.print("\n[bold cyan]Step 5:[/bold cyan] Test standalone executable")
                run_command(f"{exe_path} --help", "Test the built executable")

                # Show file size
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                console.print(f"\n[dim]Executable size: {size_mb:.2f} MB[/dim]")

    # Step 6: Build with custom options
    console.print("\n[bold cyan]Step 6:[/bold cyan] Build with custom options")
    run_command(
        "uvmgr build exe --name custom-uvmgr --onedir",
        "Build as a directory bundle with custom name"
    )

    console.print(Panel.fit(
        "[bold green]Demo Complete![/bold green]\n\n"
        "uvmgr successfully demonstrated its ability to package itself\n"
        "as a standalone executable using PyInstaller.",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
