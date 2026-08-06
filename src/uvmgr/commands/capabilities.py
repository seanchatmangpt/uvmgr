"""Inspect and verify uvmgr capability standing."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from uvmgr.core.capabilities import capabilities_as_dict, inspect_capabilities
from uvmgr.core.instrumentation import instrument_command

app = typer.Typer(help="Inspect admitted, excluded, and incomplete command capabilities.")
console = Console()


@app.command("list")
@instrument_command("capabilities_list", track_args=True)
def list_capabilities(
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Emit machine-readable capability records."),
    ] = False,
) -> None:
    """List every physical or admitted command capability."""
    records = inspect_capabilities()
    if json_output:
        typer.echo(json.dumps(capabilities_as_dict(records), sort_keys=True))
        return

    table = Table(title="uvmgr capability standing")
    table.add_column("Capability")
    table.add_column("Standing")
    table.add_column("Enabled")
    table.add_column("C/O/R")
    table.add_column("Detail")
    for record in records:
        closure = (
            f"{int(record.command_module)}/"
            f"{int(record.operations_module)}/"
            f"{int(record.runtime_module)}"
        )
        table.add_row(
            record.name,
            record.standing,
            "yes" if record.enabled else "no",
            closure,
            record.detail,
        )
    console.print(table)


@app.command("verify")
@instrument_command("capabilities_verify", track_args=True)
def verify_capabilities(
    strict: Annotated[
        bool,
        typer.Option(
            "--strict/--no-strict",
            help="Fail when an enabled capability is not ALIVE.",
        ),
    ] = False,
) -> None:
    """Verify enabled commands and expose incomplete layer closure."""
    records = inspect_capabilities()
    broken = [
        record
        for record in records
        if record.enabled
        and (
            record.standing in {"BUILD_BROKEN", "UNSUPPORTED"}
            or (strict and record.standing != "ALIVE")
        )
    ]
    typer.echo(
        json.dumps(
            {
                "enabled": sum(record.enabled for record in records),
                "records": capabilities_as_dict(records),
                "verified": not broken,
            },
            sort_keys=True,
        )
    )
    if broken:
        raise typer.Exit(1)
