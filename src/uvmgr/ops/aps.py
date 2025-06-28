"""
uvmgr.ops.aps
============

Operations for APScheduler integration.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from uvmgr.core.shell import timed

# Global scheduler instance (lazy-loaded)
_scheduler: BackgroundScheduler | None = None


@timed
def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    if not _scheduler.running:
        _scheduler.start()
    return _scheduler


@timed
def add_cron(job_id: str, cron: str, cmd: str) -> None:
    """Add a cron job to the scheduler."""
    get_scheduler().add_job(
        _run_cmd,
        CronTrigger.from_crontab(cron),
        id=job_id,
        args=[cmd],
        replace_existing=True,
    )


@timed
def add_interval(job_id: str, seconds: int, cmd: str) -> None:
    """Add an interval job to the scheduler."""
    get_scheduler().add_job(
        _run_cmd,
        IntervalTrigger(seconds=seconds),
        id=job_id,
        args=[cmd],
        replace_existing=True,
    )


@timed
def remove(job_id: str) -> None:
    """Remove a job from the scheduler."""
    if _scheduler is not None:
        _scheduler.remove_job(job_id)


@timed
def list_jobs() -> list[str]:
    """List all scheduled jobs."""
    if _scheduler is None:
        return []
    return [f"{j.id}: {j.trigger}" for j in _scheduler.get_jobs()]


def _run_cmd(cmd: str) -> None:
    """Execute a command string."""
    import subprocess

    subprocess.run(cmd, shell=True, check=True)


@timed
def run() -> None:
    """Run the scheduler (blocking)."""
    scheduler = get_scheduler()
    scheduler.print_jobs()
    try:
        while True:
            import time

            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        global _scheduler
        _scheduler = None
