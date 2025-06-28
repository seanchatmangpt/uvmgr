"""
Typer sub-app: uvmgr history …

Commands for managing command history and analytics.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uvmgr.core.history import (
    clear_history,
    get_command_history,
    get_command_stats,
    log_command,
)
from uvmgr.core.instrumentation import instrument_command

console = Console()
app = typer.Typer(help="Command history management and analytics")


@app.command("show")
@instrument_command("history_show")
def show(
    command: str = typer.Option(None, "--command", "-c", help="Filter by specific command"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of entries to show"),
    successful_only: bool = typer.Option(False, "--successful-only", "-s", help="Show only successful commands"),
):
    """Show command history with optional filtering."""
    console.print(Panel.fit(
        "[bold]Command History[/bold]\n\n"
        f"Showing {'successful ' if successful_only else ''}commands"
        f"{f' for {command}' if command else ''} (limit: {limit})",
        border_style="cyan"
    ))

    try:
        history = get_command_history(
            command=command, 
            limit=limit, 
            successful_only=successful_only
        )

        if not history:
            console.print("[yellow]No command history found.[/yellow]")
            return

        # Create table
        table = Table(show_header=True)
        table.add_column("Time", style="dim")
        table.add_column("Command", style="cyan")
        table.add_column("Args", style="blue", max_width=40)
        table.add_column("Exit Code", justify="center")
        table.add_column("Duration", justify="right", style="green")
        table.add_column("Working Dir", style="dim", max_width=30)

        for entry in history:
            timestamp = entry.get("ts", "").split("T")[1][:8] if "T" in entry.get("ts", "") else entry.get("ts", "")[:8]
            command_name = entry.get("command", "unknown")
            args = " ".join(entry.get("args", []))[:40]
            exit_code = entry.get("exit_code", 0)
            duration = entry.get("duration")
            working_dir = entry.get("working_dir", "")

            # Color code exit codes
            if exit_code == 0:
                exit_code_str = "[green]✓ 0[/green]"
            else:
                exit_code_str = f"[red]✗ {exit_code}[/red]"

            # Format duration
            if duration:
                if duration < 1:
                    duration_str = f"{duration*1000:.0f}ms"
                else:
                    duration_str = f"{duration:.2f}s"
            else:
                duration_str = "-"

            table.add_row(
                timestamp,
                command_name,
                args if args else "",
                exit_code_str,
                duration_str,
                working_dir.split("/")[-1] if working_dir else ""
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error retrieving command history: {e}[/red]")
        raise typer.Exit(1)


@app.command("stats")
@instrument_command("history_stats")
def stats():
    """Show command usage statistics and analytics."""
    console.print(Panel.fit(
        "[bold]Command Usage Statistics[/bold]\n\n"
        "Analytics for command execution patterns",
        border_style="cyan"
    ))

    try:
        stats_data = get_command_stats()

        # Overall stats panel
        overall_panel = Panel(
            f"[bold]Total Commands:[/bold] {stats_data['total_commands']}\n"
            f"[bold]Unique Commands:[/bold] {stats_data['unique_commands']}\n"
            f"[bold]Success Rate:[/bold] [{'green' if stats_data['success_rate'] >= 90 else 'yellow' if stats_data['success_rate'] >= 70 else 'red'}]{stats_data['success_rate']:.1f}%[/]\n"
            f"[bold]Failed Commands:[/bold] {stats_data['failed_commands']}\n"
            f"[bold]Average Duration:[/bold] {stats_data['avg_duration']:.3f}s",
            title="Overall Statistics",
            border_style="green"
        )
        console.print(overall_panel)

        # Recent activity
        if stats_data['recent_activity']:
            recent_panel = Panel(
                f"[bold]Last 24 Hours:[/bold] {stats_data['recent_activity']['last_24h']} commands\n"
                f"[bold]24h Success Rate:[/bold] {stats_data['recent_activity']['success_rate_24h']:.1f}%",
                title="Recent Activity",
                border_style="blue"
            )
            console.print(recent_panel)

        # Most used commands
        if stats_data['most_used']:
            table = Table(title="Most Used Commands", show_header=True)
            table.add_column("Command", style="cyan")
            table.add_column("Count", justify="right", style="bold")
            table.add_column("Percentage", justify="right", style="dim")

            for command, count in stats_data['most_used']:
                percentage = (count / stats_data['total_commands']) * 100
                table.add_row(
                    command,
                    str(count),
                    f"{percentage:.1f}%"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error retrieving command statistics: {e}[/red]")
        raise typer.Exit(1)


@app.command("clear")
@instrument_command("history_clear")
def clear_cmd(
    commands: bool = typer.Option(True, "--commands/--no-commands", help="Clear command history"),
    files: bool = typer.Option(False, "--files/--no-files", help="Clear file history"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt"),
):
    """Clear command and/or file history."""
    if not commands and not files:
        console.print("[yellow]No history selected for clearing. Use --commands or --files.[/yellow]")
        return

    # Confirmation prompt
    if not confirm:
        items_to_clear = []
        if commands:
            items_to_clear.append("command history")
        if files:
            items_to_clear.append("file history")
        
        items_str = " and ".join(items_to_clear)
        
        confirmed = typer.confirm(f"Are you sure you want to clear {items_str}?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return

    try:
        clear_history(command_history=commands, file_history=files)
        
        cleared_items = []
        if commands:
            cleared_items.append("command history")
        if files:
            cleared_items.append("file history")
            
        items_str = " and ".join(cleared_items)
        console.print(f"[green]✓ Successfully cleared {items_str}[/green]")

    except Exception as e:
        console.print(f"[red]Error clearing history: {e}[/red]")
        raise typer.Exit(1)


@app.command("log")
@instrument_command("history_log")
def log_cmd(
    command: str = typer.Argument(..., help="Command name to log"),
    exit_code: int = typer.Option(0, "--exit-code", "-e", help="Exit code"),
    duration: float = typer.Option(None, "--duration", "-d", help="Command duration in seconds"),
    error: str = typer.Option(None, "--error", help="Error message if command failed"),
):
    """Manually log a command execution."""
    try:
        log_command(
            command=command,
            exit_code=exit_code,
            duration=duration,
            error=error
        )
        
        console.print(f"[green]✓ Logged command: {command}[/green]")

    except Exception as e:
        console.print(f"[red]Error logging command: {e}[/red]")
        raise typer.Exit(1)


@app.command("export")
@instrument_command("history_export")
def export(
    output: str = typer.Option("command_history.json", "--output", "-o", help="Output file path"),
    command: str = typer.Option(None, "--command", "-c", help="Filter by specific command"),
    limit: int = typer.Option(None, "--limit", "-l", help="Limit number of entries"),
):
    """Export command history to JSON file."""
    import json
    from pathlib import Path

    try:
        history = get_command_history(command=command, limit=limit)
        
        if not history:
            console.print("[yellow]No command history to export.[/yellow]")
            return

        output_path = Path(output)
        output_path.write_text(json.dumps(history, indent=2))
        
        console.print(f"[green]✓ Exported {len(history)} entries to {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error exporting command history: {e}[/red]")
        raise typer.Exit(1)