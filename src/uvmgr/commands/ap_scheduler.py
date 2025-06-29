"""
uvmgr.commands.ap_scheduler - Advanced Process Scheduler
=====================================================

Minimal APScheduler wrapper for task scheduling and automation.

This module provides CLI commands for scheduling and managing recurring
tasks using APScheduler, supporting both cron expressions and interval-based
scheduling.

Key Features
-----------
• **Task Scheduling**: Schedule recurring tasks with cron or interval
• **Job Management**: Add, remove, and list scheduled jobs
• **Cron Support**: Full crontab expression support
• **Interval Scheduling**: Time-based interval scheduling
• **Job Persistence**: Persistent job storage and management
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **add**: Add a new scheduled job
- **remove**: Remove a scheduled job
- **list**: List all scheduled jobs
- **run**: Start the scheduler daemon

Scheduling Types
---------------
- **Cron Jobs**: Use crontab expressions for complex scheduling
- **Interval Jobs**: Run jobs at fixed time intervals

Examples
--------
    >>> # Add cron job
    >>> uvmgr ap-scheduler add backup "0 2 * * *" "backup.sh"
    >>> 
    >>> # Add interval job
    >>> uvmgr ap-scheduler add cleanup --every 3600 "cleanup.sh"
    >>> 
    >>> # List jobs
    >>> uvmgr ap-scheduler list
    >>> 
    >>> # Remove job
    >>> uvmgr ap-scheduler remove backup
    >>> 
    >>> # Start scheduler
    >>> uvmgr ap-scheduler run

Cron Expression Format
---------------------
Standard crontab format: minute hour day month weekday
- `* * * * *` - Every minute
- `0 2 * * *` - Daily at 2 AM
- `0 9 * * 1` - Weekly on Monday at 9 AM

See Also
--------
- :mod:`uvmgr.ops.aps` : APScheduler operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import aps as ops_aps

app = typer.Typer(help="Minimal APScheduler wrapper")


@app.command("add")
@instrument_command("scheduler_add", track_args=True)
def add(
    job_id: str,
    cron: str = typer.Option(None, "--cron", help="crontab expression"),
    every: int = typer.Option(None, "--every", help="seconds"),
    cmd: str = typer.Argument(..., help="Command string to run"),
):
    if cron:
        ops_aps.add_cron(job_id, cron, cmd)
    elif every:
        ops_aps.add_interval(job_id, every, cmd)
    else:
        raise typer.BadParameter("Either --cron or --every required")


@app.command("remove")
@instrument_command("scheduler_remove", track_args=True)
def remove(job_id: str):
    ops_aps.remove(job_id)
    colour(f"❎ removed {job_id}", "yellow")


@app.command("list")
@instrument_command("scheduler_list", track_args=True)
def list_(json_: bool = typer.Option(False, "--json")):
    jobs = ops_aps.list_jobs()
    dump_json(jobs) if json_ else [colour(j, "cyan") for j in jobs]


@app.command("run")
@instrument_command("scheduler_run", track_args=True)
def run():
    ops_aps.run()
