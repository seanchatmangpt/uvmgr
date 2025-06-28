"""
Execute BPMN workflows with SpiffWorkflow.

Provides comprehensive OTEL instrumentation for workflow execution,
including task-level tracing, performance metrics, and semantic conventions.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from SpiffWorkflow.bpmn.parser import BpmnParser
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.task import Task

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import metric_counter, metric_histogram, span


def _load(path: Path) -> BpmnWorkflow:
    """Load BPMN workflow from file with instrumentation."""
    with span("workflow.load", definition_path=str(path)):
        add_span_event("workflow.parsing.started", {"file_path": str(path)})
        
        parser = BpmnParser()
        parser.add_bpmn_file(str(path))
        
        # Get the workflow specification name from the file
        # Try to get the first available process spec
        process_parsers = parser.process_parsers
        if process_parsers:
            process_id = list(process_parsers.keys())[0]
            wf_spec = parser.get_spec(process_id)
        else:
            # Fallback to empty string for legacy compatibility
            wf_spec = parser.get_spec("")
        workflow = BpmnWorkflow(wf_spec)
        
        # Add workflow metadata to current span
        add_span_attributes(
            workflow_engine="SpiffWorkflow",
            workflow_definition_name=wf_spec.name or path.stem,
            workflow_instance_id=str(id(workflow)),
        )
        
        add_span_event("workflow.parsing.completed", {
            "workflow_name": wf_spec.name or path.stem,
            "task_count": len(list(wf_spec.task_specs)),
        })
        
        metric_counter("workflow.instances.created")(1)
        
        return workflow


def _step(wf: BpmnWorkflow) -> None:
    """Execute one step of workflow with detailed instrumentation."""
    with span("workflow.step"):
        step_start = time.time()
        tasks_processed = 0
        
        # Process user tasks
        user_tasks = wf.get_ready_user_tasks()
        if user_tasks:
            add_span_event("workflow.user_tasks.found", {"count": len(user_tasks)})
            
        for task in user_tasks:
            _process_task(wf, task, "user")
            tasks_processed += 1

        # Process service tasks
        service_tasks = wf.get_ready_service_tasks()
        if service_tasks:
            add_span_event("workflow.service_tasks.found", {"count": len(service_tasks)})
            
        for task in service_tasks:
            _process_task(wf, task, "service")
            tasks_processed += 1
        
        step_duration = time.time() - step_start
        
        add_span_attributes(
            tasks_processed=tasks_processed,
            step_duration_ms=int(step_duration * 1000),
        )
        
        # Record step metrics
        metric_histogram("workflow.step.duration")(step_duration)
        metric_counter("workflow.tasks.processed")(tasks_processed)


def _process_task(wf: BpmnWorkflow, task: Task, task_type: str) -> None:
    """Process a single workflow task with instrumentation."""
    task_name = getattr(task.task_spec, 'name', str(task))
    
    with span(
        f"workflow.task.{task_type}",
        task_name=task_name,
        task_type=task_type,
        task_id=str(task.id),
    ):
        task_start = time.time()
        
        add_span_event("task.started", {
            "task_name": task_name,
            "task_type": task_type,
            "task_state": str(task.state),
        })
        
        try:
            if task_type == "user":
                colour(f"⏸  waiting for user task: {task_name}", "yellow")
                input("Press <Enter> when done …")
            else:
                colour(f"↻  auto-completing service task: {task_name}", "cyan")
            
            # Complete the task
            wf.complete_task_from_id(task.id)
            
            task_duration = time.time() - task_start
            
            add_span_event("task.completed", {
                "task_name": task_name,
                "duration_ms": int(task_duration * 1000),
            })
            
            # Record task metrics
            metric_histogram(f"workflow.task.{task_type}.duration")(task_duration)
            metric_counter(f"workflow.task.{task_type}.completed")(1)
            
        except Exception as e:
            add_span_event("task.failed", {
                "task_name": task_name,
                "error": str(e),
            })
            metric_counter(f"workflow.task.{task_type}.failed")(1)
            raise


def run_bpmn(path: Path) -> Dict[str, Any]:
    """Execute a BPMN workflow with comprehensive instrumentation.
    
    Args:
        path: Path to the BPMN file
        
    Returns:
        Dict containing workflow execution statistics
    """
    execution_start = time.time()
    
    with span(
        "workflow.execute",
        **{
            WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
            WorkflowAttributes.TYPE: "bpmn",
            WorkflowAttributes.DEFINITION_PATH: str(path),
            WorkflowAttributes.DEFINITION_NAME: path.stem,
            WorkflowAttributes.ENGINE: "SpiffWorkflow",
        }
    ):
        add_span_event("workflow.execution.started", {"file_path": str(path)})
        
        # Load workflow
        wf = _load(path)
        
        steps = 0
        total_tasks = 0
        
        try:
            # Execute workflow steps
            while not wf.is_completed():
                step_start_tasks = len(list(wf.get_ready_tasks()))
                _step(wf)
                step_end_tasks = len(list(wf.get_completed_tasks()))
                
                steps += 1
                total_tasks += (step_end_tasks - step_start_tasks + step_start_tasks)
                
                # Add progress update
                add_span_event("workflow.step.completed", {
                    "step_number": steps,
                    "completed_tasks": step_end_tasks,
                })
            
            execution_duration = time.time() - execution_start
            
            # Final workflow state
            final_tasks = list(wf.get_tasks())
            completed_tasks = list(wf.get_completed_tasks())
            failed_tasks = [t for t in final_tasks if hasattr(t, 'state') and 'CANCELLED' in str(t.state)]
            
            stats = {
                "status": "completed",
                "duration_seconds": execution_duration,
                "steps_executed": steps,
                "total_tasks": len(final_tasks),
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "workflow_name": path.stem,
            }
            
            add_span_attributes(**{
                f"workflow.{k}": v for k, v in stats.items()
                if isinstance(v, (str, int, float, bool))
            })
            
            add_span_event("workflow.execution.completed", stats)
            
            # Record final metrics
            metric_histogram("workflow.execution.duration")(execution_duration)
            metric_counter("workflow.executions.completed")(1)
            
            colour("✔ BPMN workflow completed", "green")
            colour(f"  Duration: {execution_duration:.2f}s, Steps: {steps}, Tasks: {len(completed_tasks)}", "blue")
            
            return stats
            
        except Exception as e:
            execution_duration = time.time() - execution_start
            
            error_stats = {
                "status": "failed",
                "duration_seconds": execution_duration,
                "steps_executed": steps,
                "error": str(e),
                "workflow_name": path.stem,
            }
            
            add_span_event("workflow.execution.failed", error_stats)
            metric_counter("workflow.executions.failed")(1)
            
            colour(f"✗ BPMN workflow failed: {e}", "red")
            raise


def get_workflow_stats(wf: BpmnWorkflow) -> Dict[str, Any]:
    """Get comprehensive statistics about a workflow instance."""
    all_tasks = list(wf.get_tasks())
    
    stats = {
        "total_tasks": len(all_tasks),
        "completed_tasks": len(list(wf.get_completed_tasks())),
        "ready_tasks": len(list(wf.get_ready_tasks())),
        "waiting_tasks": len(list(wf.get_waiting_tasks())),
        "cancelled_tasks": len([t for t in all_tasks if hasattr(t, 'state') and 'CANCELLED' in str(t.state)]),
        "is_completed": wf.is_completed(),
        "workflow_name": getattr(wf.spec, 'name', 'unknown'),
    }
    
    return stats


def validate_bpmn_file(path: Path) -> bool:
    """Validate a BPMN file can be loaded successfully."""
    with span("workflow.validate", definition_path=str(path)):
        try:
            parser = BpmnParser()
            parser.add_bpmn_file(str(path))
            
            # Try to get the first available process spec
            process_parsers = parser.process_parsers
            if process_parsers:
                process_id = list(process_parsers.keys())[0]
                spec = parser.get_spec(process_id)
            else:
                # Fallback to empty string for legacy compatibility
                spec = parser.get_spec("")
            
            add_span_event("workflow.validation.success", {
                "workflow_name": spec.name or path.stem,
                "task_specs": len(list(spec.task_specs)),
            })
            
            metric_counter("workflow.validations.passed")(1)
            return True
            
        except Exception as e:
            add_span_event("workflow.validation.failed", {
                "error": str(e),
                "file_path": str(path),
            })
            
            metric_counter("workflow.validations.failed")(1)
            return False
