"""
Execute BPMN workflows with SpiffWorkflow.
"""

from __future__ import annotations

from pathlib import Path

from SpiffWorkflow.bpmn.parser import BpmnParser
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow

from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def _load(path: Path) -> BpmnWorkflow:
    parser = BpmnParser()
    parser.add_bpmn_xml_file(str(path))
    wf_spec = parser.get_spec("")
    return BpmnWorkflow(wf_spec)


def _step(wf: BpmnWorkflow) -> None:
    # User tasks
    for task in wf.get_ready_user_tasks():
        colour(f"⏸  waiting for user task: {task}", "yellow")
        input("Press <Enter> when done …")
        wf.complete_task_from_id(task.id)

    # Service tasks
    for task in wf.get_ready_service_tasks():
        colour(f"↻  auto-completing service task: {task}", "cyan")
        wf.complete_task_from_id(task.id)


def run_bpmn(path: Path) -> None:
    with span("agent.run_bpmn", path=str(path)):
        wf = _load(path)
        while not wf.is_completed():
            _step(wf)
        colour("✔ BPMN workflow completed", "green")
