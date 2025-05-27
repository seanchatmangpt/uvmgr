"""
uvmgr.commands.agent
====================

CLI wrapper around the agent orchestration layer.
"""

from __future__ import annotations

from pathlib import Path

import typer

from .. import main as cli_root          # exported root Typer app
from uvmgr.ops import agent as agent_ops

agent_app = typer.Typer(help="Execute BPMN workflows")
cli_root.app.add_typer(agent_app, name="agent")


@agent_app.command("run")
def run_bpmn(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    )
):
    """Run *file* until the workflow completes."""
    agent_ops.run(file)
