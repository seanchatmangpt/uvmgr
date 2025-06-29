"""
Workflow management operations for uvmgr.

This module provides business logic for workflow orchestration, template management,
and conditional execution. It follows the 80/20 principle by focusing on the most
essential workflow operations that provide maximum value.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
from uvmgr.runtime import workflow as workflow_runtime


def create_workflow(
    name: str,
    template: str,
    path: Optional[Path] = None,
    variables: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new workflow from a template.
    
    Parameters
    ----------
    name : str
        Name of the workflow
    template : str
        Template to use for workflow creation
    path : Optional[Path]
        Path where to create the workflow
    variables : Optional[Dict[str, Any]]
        Template variables to substitute
        
    Returns
    -------
    Dict[str, Any]
        Workflow creation results
    """
    with span("workflow.create") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
            "workflow.name": name,
            "workflow.template": template,
            WorkflowAttributes.DEFINITION_PATH: str(path) if path else None,
        })
        
        # Delegate to runtime
        result = workflow_runtime.create_workflow_from_template(
            name=name,
            template=template,
            path=path,
            variables=variables or {}
        )
        
        add_span_attributes(**{
            "workflow.creation_success": result.get("success", False),
            "workflow.created_path": result.get("workflow_path", ""),
        })
        
        return result


def execute_workflow(
    workflow_path: Path,
    inputs: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute a workflow definition.
    
    Parameters
    ----------
    workflow_path : Path
        Path to the workflow definition file
    inputs : Optional[Dict[str, Any]]
        Input parameters for the workflow
    dry_run : bool
        Whether to perform a dry run without executing
        
    Returns
    -------
    Dict[str, Any]
        Workflow execution results
    """
    with span("workflow.execute") as current_span:
        start_time = time.time()
        
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
            WorkflowAttributes.DEFINITION_PATH: str(workflow_path),
            WorkflowAttributes.ENGINE: "uvmgr",
            "workflow.dry_run": dry_run,
        })
        
        # Delegate to runtime
        result = workflow_runtime.execute_workflow_file(
            workflow_path=workflow_path,
            inputs=inputs or {},
            dry_run=dry_run
        )
        
        execution_time = time.time() - start_time
        add_span_attributes(**{
            "workflow.execution_success": result.get("success", False),
            "workflow.execution_time": execution_time,
            "workflow.steps_executed": result.get("steps_executed", 0),
            "workflow.steps_failed": result.get("steps_failed", 0),
        })
        
        return result


def validate_workflow(workflow_path: Path) -> Dict[str, Any]:
    """
    Validate a workflow definition.
    
    Parameters
    ----------
    workflow_path : Path
        Path to the workflow definition file
        
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    with span("workflow.validate") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: WorkflowOperations.VALIDATE,
            WorkflowAttributes.DEFINITION_PATH: str(workflow_path),
        })
        
        # Delegate to runtime
        result = workflow_runtime.validate_workflow_definition(workflow_path)
        
        add_span_attributes(**{
            "workflow.validation_success": result.get("valid", False),
            "workflow.validation_errors": len(result.get("errors", [])),
            "workflow.validation_warnings": len(result.get("warnings", [])),
        })
        
        return result


def list_workflows(
    path: Optional[Path] = None,
    include_templates: bool = True
) -> Dict[str, Any]:
    """
    List available workflows and templates.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to search for workflows
    include_templates : bool
        Whether to include available templates
        
    Returns
    -------
    Dict[str, Any]
        List of workflows and templates
    """
    with span("workflow.list") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: "list",
            "workflow.search_path": str(path) if path else ".",
            "workflow.include_templates": include_templates,
        })
        
        # Delegate to runtime
        result = workflow_runtime.discover_workflows(
            search_path=path,
            include_templates=include_templates
        )
        
        add_span_attributes(**{
            "workflow.workflows_found": len(result.get("workflows", [])),
            "workflow.templates_found": len(result.get("templates", [])),
        })
        
        return result


def generate_workflow_template(
    template_type: str,
    output_path: Path,
    customizations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a workflow template.
    
    Parameters
    ----------
    template_type : str
        Type of template to generate (ci, build, test, etc.)
    output_path : Path
        Where to save the generated template
    customizations : Optional[Dict[str, Any]]
        Template customizations
        
    Returns
    -------
    Dict[str, Any]
        Template generation results
    """
    with span("workflow.generate_template") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: "generate_template",
            "workflow.template_type": template_type,
            "workflow.output_path": str(output_path),
        })
        
        # Delegate to runtime
        result = workflow_runtime.generate_template(
            template_type=template_type,
            output_path=output_path,
            customizations=customizations or {}
        )
        
        add_span_attributes(**{
            "workflow.generation_success": result.get("success", False),
            "workflow.template_path": result.get("template_path", ""),
        })
        
        return result


def schedule_workflow(
    workflow_path: Path,
    schedule: str,
    inputs: Optional[Dict[str, Any]] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    """
    Schedule a workflow for recurring execution.
    
    Parameters
    ----------
    workflow_path : Path
        Path to the workflow definition file
    schedule : str
        Cron-style schedule expression
    inputs : Optional[Dict[str, Any]]
        Default input parameters
    enabled : bool
        Whether the scheduled workflow is enabled
        
    Returns
    -------
    Dict[str, Any]
        Scheduling results
    """
    with span("workflow.schedule") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: "schedule",
            WorkflowAttributes.DEFINITION_PATH: str(workflow_path),
            "workflow.schedule": schedule,
            "workflow.enabled": enabled,
        })
        
        # Delegate to runtime
        result = workflow_runtime.schedule_workflow(
            workflow_path=workflow_path,
            schedule=schedule,
            inputs=inputs or {},
            enabled=enabled
        )
        
        add_span_attributes(**{
            "workflow.scheduling_success": result.get("success", False),
            "workflow.schedule_id": result.get("schedule_id", ""),
        })
        
        return result


def get_workflow_status(
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the status of workflow executions.
    
    Parameters
    ----------
    workflow_id : Optional[str]
        Specific workflow ID to check
    execution_id : Optional[str]
        Specific execution ID to check
        
    Returns
    -------
    Dict[str, Any]
        Workflow status information
    """
    with span("workflow.status") as current_span:
        add_span_attributes(**{
            WorkflowAttributes.OPERATION: "status",
            "workflow.workflow_id": workflow_id,
            "workflow.execution_id": execution_id,
        })
        
        # Delegate to runtime
        result = workflow_runtime.get_execution_status(
            workflow_id=workflow_id,
            execution_id=execution_id
        )
        
        add_span_attributes(**{
            "workflow.status_success": result.get("success", False),
            "workflow.active_executions": result.get("active_executions", 0),
        })
        
        return result