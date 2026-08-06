"""Inspect and structurally verify uvmgr capability standing."""

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
    table.add_column("O/A/E")
    table.add_column("C/O/R")
    table.add_column("Detail")
    for record in records:
        lifecycle = (
            f"{int(record.observed)}/"
            f"{int(record.admitted)}/"
            f"{int(record.executed)}"
        )
        closure = (
            f"{int(record.command_module)}/"
            f"{int(record.operations_module)}/"
            f"{int(record.runtime_module)}"
        )
        table.add_row(
            record.name,
            record.standing,
            lifecycle,
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
            help="Require admitted commands to import and have C/O/R closure.",
        ),
    ] = False,
) -> None:
    """Verify imports and structural closure without claiming execution."""
    records = inspect_capabilities()
    broken = [
        record
        for record in records
        if record.admitted
        and (
            record.standing in {"BUILD_BROKEN", "UNSUPPORTED"}
            or (
                strict
                and not (
                    record.imported
                    and record.typer_app
                    and record.operations_module
                    and record.runtime_module
                )
            )
        )
    ]
    typer.echo(
        json.dumps(
            {
                "admitted": sum(record.admitted for record in records),
                "executed": sum(record.executed for record in records),
                "records": capabilities_as_dict(records),
                "structurally_verified": not broken,
            },
            sort_keys=True,
        )
    )
    if broken:
        raise typer.Exit(1)
