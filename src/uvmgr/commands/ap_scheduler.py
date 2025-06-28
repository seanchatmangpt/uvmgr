import typer

from uvmgr.core.instrumentation import instrument_subcommand
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import aps as ops_aps

from .. import main as cli_root

app_aps = typer.Typer(help="Minimal APScheduler wrapper")
cli_root.app.add_typer(app_aps, name="ap-scheduler")


@app_aps.command("add")
@instrument_subcommand("ap-scheduler")
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


@app_aps.command("remove")
@instrument_subcommand("ap-scheduler")
def remove(job_id: str):
    ops_aps.remove(job_id)
    colour(f"❎ removed {job_id}", "yellow")


@app_aps.command("list")
@instrument_subcommand("ap-scheduler")
def list_(json_: bool = typer.Option(False, "--json")):
    jobs = ops_aps.list_jobs()
    dump_json(jobs) if json_ else [colour(j, "cyan") for j in jobs]


@app_aps.command("run")
@instrument_subcommand("ap-scheduler")
def run():
    ops_aps.run()
