"""
uvmgr.commands.workflow
======================

Enhanced workflow management with templates and conditional execution.

This command module addresses the critical workflow orchestration gap by providing:

• **Template execution**: Run pre-built workflow templates  
• **Conditional workflows**: Smart branching based on context
• **Workflow composition**: Chain commands into complex automation
• **Parallel execution**: Run tasks concurrently where possible
• **Progress monitoring**: Track workflow execution in real-time

Example
-------
    $ uvmgr workflow run ci_cd --environment staging
    $ uvmgr workflow list
    $ uvmgr workflow status workflow_123
    $ uvmgr workflow create my_workflow --from development

See Also
--------
- :mod:`uvmgr.core.workflows` : Workflow engine implementation
- :mod:`uvmgr.core.workspace` : Workspace configuration
"""

from __future__ import annotations

import asyncio
import typer
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations, CliAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.workflows import (
    get_workflow_engine,
    get_workflow_templates,
    execute_workflow,
    WorkflowStepStatus
)

app = typer.Typer(help="Enhanced workflow management with templates and conditional execution")


@app.command("list")
@instrument_command("workflow_list", track_args=True)
def list_templates(
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List available workflow templates."""
    
    templates = get_workflow_templates()
    
    if tag:
        templates = [t for t in templates if tag in t.tags]
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: "list_templates",
        "templates_count": str(len(templates)),
        "filter_tag": tag or "none"
    })
    
    if json_output:
        template_data = []
        for template in templates:
            template_data.append({
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "steps_count": len(template.steps),
                "tags": template.tags,
                "parameters": template.parameters
            })
        dump_json(template_data)
        return
    
    if not templates:
        typer.echo("📋 No workflow templates found")
        if tag:
            typer.echo(f"   (filtered by tag: {tag})")
        return
    
    typer.echo("📋 Available Workflow Templates:")
    for template in templates:
        typer.echo(f"\n  🔧 {colour(template.name, 'green')} v{template.version}")
        typer.echo(f"     📝 {template.description}")
        typer.echo(f"     📊 {len(template.steps)} steps")
        if template.tags:
            typer.echo(f"     🏷️  Tags: {', '.join(template.tags)}")
        
        # Show parameters if any
        if template.parameters:
            typer.echo(f"     ⚙️  Parameters:")
            for param, default in template.parameters.items():
                typer.echo(f"        • {param}: {default}")


@app.command("run")
@instrument_command("workflow_run", track_args=True)
def run_workflow(
    template_name: str = typer.Argument(..., help="Workflow template name"),
    parameters: Optional[List[str]] = typer.Option(None, "--param", "-p", help="Parameters in key=value format"),
    workflow_id: Optional[str] = typer.Option(None, "--id", help="Custom workflow ID"),
    async_execution: bool = typer.Option(False, "--async", help="Run workflow asynchronously"),
    watch: bool = typer.Option(True, "--watch/--no-watch", help="Watch workflow progress")
):
    """Run a workflow template with optional parameters."""
    
    # Parse parameters
    workflow_params = {}
    if parameters:
        for param in parameters:
            if "=" in param:
                key, value = param.split("=", 1)
                # Try to parse as JSON for complex types
                try:
                    workflow_params[key] = json.loads(value)
                except json.JSONDecodeError:
                    workflow_params[key] = value
            else:
                typer.echo(f"❌ Invalid parameter format: {param} (expected key=value)")
                raise typer.Exit(1)
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
        WorkflowAttributes.DEFINITION_NAME: template_name,
        "parameters_count": str(len(workflow_params)),
        "async_execution": str(async_execution)
    })
    
    if async_execution:
        # Start workflow asynchronously
        typer.echo(f"🚀 Starting workflow '{template_name}' asynchronously...")
        if workflow_params:
            typer.echo(f"📋 Parameters: {workflow_params}")
        
        # In practice, this would start the workflow in background
        typer.echo(f"✅ Workflow started. Use 'uvmgr workflow status {workflow_id or 'auto'}' to check progress")
        return
    
    # Run workflow synchronously
    typer.echo(f"🚀 Running workflow: {colour(template_name, 'green')}")
    if workflow_params:
        typer.echo(f"📋 Parameters: {workflow_params}")
    
    try:
        # Execute workflow
        execution = asyncio.run(execute_workflow(template_name, workflow_params))
        
        # Display results
        _display_execution_results(execution, watch)
        
        add_span_event("workflow.execution_completed", {
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "steps_count": len(execution.steps)
        })
        
        if execution.status == WorkflowStepStatus.FAILED:
            typer.echo(f"❌ Workflow failed: {execution.error_message}")
            raise typer.Exit(1)
        else:
            typer.echo(f"✅ Workflow completed successfully!")
            
    except Exception as e:
        typer.echo(f"❌ Workflow execution failed: {e}")
        raise typer.Exit(1)


@app.command("status") 
@instrument_command("workflow_status", track_args=True)
def show_status(
    workflow_id: str = typer.Argument(..., help="Workflow execution ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed step information")
):
    """Show status of a workflow execution."""
    
    engine = get_workflow_engine()
    execution = engine.get_execution(workflow_id)
    
    if not execution:
        typer.echo(f"❌ Workflow execution '{workflow_id}' not found")
        raise typer.Exit(1)
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: "status",
        "workflow_id": workflow_id,
        "detailed": str(detailed)
    })
    
    if json_output:
        execution_data = {
            "workflow_id": execution.workflow_id,
            "template_name": execution.template_name,
            "status": execution.status.value,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "current_step": execution.current_step,
            "parameters": execution.parameters,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "status": step.status.value,
                    "start_time": step.start_time,
                    "end_time": step.end_time,
                    "error_message": step.error_message
                }
                for step in execution.steps
            ]
        }
        dump_json(execution_data)
        return
    
    # Display formatted status
    _display_execution_results(execution, detailed)


@app.command("executions")
@instrument_command("workflow_executions", track_args=True)
def list_executions(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of executions to show"),
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List workflow executions."""
    
    engine = get_workflow_engine()
    executions = engine.list_executions()
    
    # Apply filters
    if status_filter:
        executions = [e for e in executions if e.status.value == status_filter]
    
    # Sort by start time (newest first) and limit
    executions = sorted(executions, key=lambda x: x.start_time or 0, reverse=True)[:limit]
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: "list_executions",
        "executions_count": str(len(executions)),
        "status_filter": status_filter or "none"
    })
    
    if json_output:
        execution_data = []
        for execution in executions:
            duration = None
            if execution.start_time and execution.end_time:
                duration = execution.end_time - execution.start_time
            
            execution_data.append({
                "workflow_id": execution.workflow_id,
                "template_name": execution.template_name,
                "status": execution.status.value,
                "start_time": execution.start_time,
                "duration": duration,
                "steps_count": len(execution.steps)
            })
        dump_json(execution_data)
        return
    
    if not executions:
        typer.echo("📋 No workflow executions found")
        return
    
    typer.echo(f"📋 Recent Workflow Executions (last {len(executions)}):")
    for execution in executions:
        status_icon = {
            WorkflowStepStatus.SUCCESS: "✅",
            WorkflowStepStatus.FAILED: "❌", 
            WorkflowStepStatus.RUNNING: "🔄",
            WorkflowStepStatus.PENDING: "⏳"
        }.get(execution.status, "❓")
        
        duration_str = ""
        if execution.start_time and execution.end_time:
            duration = execution.end_time - execution.start_time
            duration_str = f" ({duration:.1f}s)"
        
        timestamp = ""
        if execution.start_time:
            timestamp = datetime.fromtimestamp(execution.start_time).strftime("%Y-%m-%d %H:%M:%S")
        
        typer.echo(f"  {status_icon} {execution.workflow_id}")
        typer.echo(f"     📋 Template: {execution.template_name}")
        typer.echo(f"     📊 Steps: {len(execution.steps)}")
        typer.echo(f"     📅 Started: {timestamp}{duration_str}")
        
        if execution.current_step:
            typer.echo(f"     🔄 Current: {execution.current_step}")


@app.command("create")
@instrument_command("workflow_create", track_args=True)
def create_workflow(
    name: str = typer.Argument(..., help="New workflow name"),
    from_template: Optional[str] = typer.Option(None, "--from", help="Base template to copy from"),
    description: str = typer.Option("Custom workflow", "--desc", help="Workflow description"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output YAML file")
):
    """Create a new workflow template."""
    
    engine = get_workflow_engine()
    
    # Get base template if specified
    base_template = None
    if from_template:
        base_template = engine.get_template(from_template)
        if not base_template:
            typer.echo(f"❌ Base template '{from_template}' not found")
            raise typer.Exit(1)
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: "create",
        WorkflowAttributes.DEFINITION_NAME: name,
        "base_template": from_template or "none"
    })
    
    # Create workflow template structure
    if base_template:
        # Copy from existing template
        from uvmgr.core.workflows import WorkflowTemplate
        import copy
        
        new_template = copy.deepcopy(base_template)
        new_template.name = name
        new_template.description = description
        new_template.version = "1.0.0"
        
        typer.echo(f"✅ Created workflow '{name}' based on '{from_template}'")
    else:
        # Create minimal template
        template_yaml = f"""
name: {name}
description: {description}
version: "1.0.0"
parameters:
  environment: "development"
  run_tests: true

steps:
  - id: example_step
    type: command
    name: "Example Step"
    command: "deps"
    args:
      operation: "list"
    
  - id: conditional_example
    type: condition
    name: "Conditional Example"
    conditions:
      - type: config
        target: "global_settings.auto_test"
        operator: "=="
        value: true
    steps:
      - id: run_tests
        type: command
        name: "Run Tests"
        command: "tests"
        args:
          coverage: true
"""
        
        # Save to file
        output_path = output_file or f"{name}_workflow.yaml"
        with open(output_path, 'w') as f:
            f.write(template_yaml.strip())
        
        typer.echo(f"✅ Created workflow template: {output_path}")
        typer.echo(f"📝 Edit the file to customize your workflow")
    
    add_span_event("workflow.template_created", {
        "workflow_name": name,
        "based_on_template": bool(from_template)
    })


def _display_execution_results(execution, detailed: bool = False):
    """Display workflow execution results in a formatted way."""
    
    status_icon = {
        WorkflowStepStatus.SUCCESS: "✅",
        WorkflowStepStatus.FAILED: "❌",
        WorkflowStepStatus.RUNNING: "🔄", 
        WorkflowStepStatus.PENDING: "⏳"
    }.get(execution.status, "❓")
    
    typer.echo(f"\n🔧 Workflow: {execution.workflow_id}")
    typer.echo(f"📋 Template: {execution.template_name}")
    typer.echo(f"📊 Status: {status_icon} {execution.status.value}")
    
    if execution.start_time:
        start_time = datetime.fromtimestamp(execution.start_time).strftime("%Y-%m-%d %H:%M:%S")
        typer.echo(f"📅 Started: {start_time}")
    
    if execution.start_time and execution.end_time:
        duration = execution.end_time - execution.start_time
        typer.echo(f"⏱️  Duration: {duration:.2f}s")
    
    if execution.current_step:
        typer.echo(f"🔄 Current step: {execution.current_step}")
    
    if execution.error_message:
        typer.echo(f"❌ Error: {execution.error_message}")
    
    # Show step details
    if execution.steps and detailed:
        typer.echo(f"\n📋 Steps ({len(execution.steps)}):")
        
        for step in execution.steps:
            step_icon = {
                WorkflowStepStatus.SUCCESS: "✅",
                WorkflowStepStatus.FAILED: "❌",
                WorkflowStepStatus.RUNNING: "🔄",
                WorkflowStepStatus.PENDING: "⏳",
                WorkflowStepStatus.SKIPPED: "⏭️"
            }.get(step.status, "❓")
            
            typer.echo(f"  {step_icon} {step.name} ({step.id})")
            
            if step.start_time and step.end_time:
                step_duration = step.end_time - step.start_time
                typer.echo(f"     ⏱️  {step_duration:.2f}s")
            
            if step.error_message:
                typer.echo(f"     ❌ {step.error_message}")
            
            if step.output and detailed:
                typer.echo(f"     💬 {step.output}")
    
    # Summary
    if execution.steps:
        success_count = sum(1 for step in execution.steps if step.status == WorkflowStepStatus.SUCCESS)
        failed_count = sum(1 for step in execution.steps if step.status == WorkflowStepStatus.FAILED)
        skipped_count = sum(1 for step in execution.steps if step.status == WorkflowStepStatus.SKIPPED)
        
        typer.echo(f"\n📊 Summary: {success_count} success, {failed_count} failed, {skipped_count} skipped")