"""
uvmgr.commands.agent
====================

CLI wrapper around the agent orchestration layer.
"""

from __future__ import annotations

from pathlib import Path

import typer

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.ops import agent as agent_ops

from .. import main as cli_root  # exported root Typer app

agent_app = typer.Typer(help="Execute BPMN workflows")
cli_root.app.add_typer(agent_app, name="agent")


@agent_app.command("run")
@instrument_command("agent_run_bpmn", track_args=True)
def run_bpmn(
    file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="Path to a BPMN XML file",
    ),
):
    """Run *file* until the workflow completes."""
    # Track workflow execution
    add_span_attributes(
        **{
            WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(file),
            WorkflowAttributes.DEFINITION_NAME: file.name,
            "workflow.file_size": file.stat().st_size,
        }
    )
    
    # Validate BPMN file
    try:
        content = file.read_text()
        is_valid_bpmn = "<?xml" in content and "bpmn" in content.lower()
        add_span_attributes(**{"workflow.valid_bpmn": is_valid_bpmn})
    except Exception as e:
        add_span_event("agent.validation_error", {
            "error": str(e),
            "file": str(file)
        })
    
    add_span_event("agent.workflow.started", {
        "workflow.file": str(file),
        "workflow.name": file.stem
    })
    
    agent_ops.run(file)
