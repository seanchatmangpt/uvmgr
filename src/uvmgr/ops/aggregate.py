"""
uvmgr.ops.aggregate - Command Aggregation Operations
==================================================

Operations layer for command aggregation with 8020 implementation.

This module provides the business logic for aggregating multiple uvmgr commands
using SpiffWorkflow orchestration and Weaver semantic convention validation.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file
from uvmgr.ops.weaver import check_registry, generate_code


@dataclass
class CommandNode:
    """Represents a command in the aggregation workflow."""
    name: str
    dependencies: Set[str] = field(default_factory=set)
    execution_time: float = 0.0
    success_rate: float = 1.0
    critical: bool = False
    parallel_safe: bool = True
    weaver_validation: bool = False


@dataclass
class AggregationResult:
    """Result of command aggregation execution."""
    workflow_name: str
    commands_executed: List[str]
    commands_successful: List[str]
    commands_failed: List[str]
    total_duration: float
    parallel_execution: bool
    weaver_validation_passed: bool
    spiff_workflow_used: bool
    metrics: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


# 8020 Command Analysis - 20% of commands that provide 80% of value
CRITICAL_COMMANDS = {
    "deps": {"critical": True, "dependencies": [], "parallel_safe": True},
    "test": {"critical": True, "dependencies": ["deps"], "parallel_safe": True},
    "build": {"critical": True, "dependencies": ["deps", "test"], "parallel_safe": False},
    "lint": {"critical": False, "dependencies": ["deps"], "parallel_safe": True},
    "release": {"critical": False, "dependencies": ["build"], "parallel_safe": False},
    "otel": {"critical": False, "dependencies": [], "parallel_safe": True},
    "weaver": {"critical": False, "dependencies": [], "parallel_safe": True},
    "forge": {"critical": False, "dependencies": ["weaver"], "parallel_safe": True},
}

# Mode-specific command sets
MODE_COMMANDS = {
    "development": ["deps", "lint", "test", "build"],
    "ci_cd": ["deps", "test", "build", "release"],
    "deployment": ["deps", "test", "build", "release"],
    "validation": ["otel", "weaver", "forge"],
    "custom": [],
}


def analyze_command_dependencies(commands: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze command dependencies and execution patterns.
    
    Args:
        commands: Optional list of commands to analyze (default: all)
        
    Returns:
        Dictionary with dependency analysis
    """
    with span("aggregate.analyze_dependencies"):
        add_span_attributes(**{
            "aggregate.commands_count": len(commands) if commands else len(CRITICAL_COMMANDS),
            "aggregate.analysis_type": "dependency",
        })
        
        # Use provided commands or all critical commands
        target_commands = commands or list(CRITICAL_COMMANDS.keys())
        
        dependencies = {}
        metrics = {}
        
        for cmd in target_commands:
            if cmd in CRITICAL_COMMANDS:
                cmd_info = CRITICAL_COMMANDS[cmd]
                dependencies[cmd] = list(cmd_info["dependencies"])
                metrics[cmd] = {
                    "critical": cmd_info["critical"],
                    "parallel_safe": cmd_info["parallel_safe"],
                    "execution_time": cmd_info.get("execution_time", 5.0),
                    "success_rate": cmd_info.get("success_rate", 0.95),
                }
            else:
                # Unknown command - assume safe defaults
                dependencies[cmd] = []
                metrics[cmd] = {
                    "critical": False,
                    "parallel_safe": True,
                    "execution_time": 10.0,
                    "success_rate": 0.90,
                }
        
        result = {
            "commands": target_commands,
            "dependencies": dependencies,
            "metrics": metrics,
            "critical_path": _calculate_critical_path(dependencies),
            "parallel_groups": _calculate_parallel_groups(dependencies),
        }
        
        add_span_event("aggregate.dependencies.analyzed", {
            "commands_analyzed": len(target_commands),
            "dependencies_found": sum(len(deps) for deps in dependencies.values()),
            "critical_path_length": len(result["critical_path"]),
        })
        
        return result


def create_8020_workflow(
    mode: str,
    parallel: bool = True,
    validate_weaver: bool = True,
    dependencies: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Create 8020-optimized BPMN workflow for command aggregation.
    
    Args:
        mode: Aggregation mode (development, ci_cd, deployment, validation)
        parallel: Enable parallel execution
        validate_weaver: Include Weaver validation
        dependencies: Command dependency analysis
        
    Returns:
        Path to created BPMN workflow file
    """
    with span("aggregate.create_8020_workflow", mode=mode, parallel=parallel):
        add_span_attributes(**{
            "aggregate.mode": mode,
            "aggregate.parallel": parallel,
            "aggregate.validate_weaver": validate_weaver,
        })
        
        # Get commands for mode
        commands = MODE_COMMANDS.get(mode, [])
        if not commands:
            # Fallback to development mode
            commands = MODE_COMMANDS["development"]
        
        # Use provided dependencies or analyze
        if dependencies is None:
            dependencies = analyze_command_dependencies(commands)
        
        # Create workflow directory
        workflow_dir = Path.cwd() / ".uvmgr_temp" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate workflow file
        workflow_path = workflow_dir / f"8020_{mode}_workflow.bpmn"
        
        # Generate BPMN content
        bpmn_content = _generate_8020_bpmn_workflow(
            commands=commands,
            dependencies=dependencies,
            parallel=parallel,
            validate_weaver=validate_weaver,
            mode=mode
        )
        
        # Write workflow file
        workflow_path.write_text(bpmn_content)
        
        add_span_event("aggregate.8020_workflow.created", {
            "workflow_path": str(workflow_path),
            "commands_count": len(commands),
            "mode": mode,
            "parallel": parallel,
        })
        
        metric_counter("aggregate.workflows.created")(1)
        
        return workflow_path


def execute_aggregation_workflow(
    workflow_path: Path,
    parallel: bool = True,
    validate_weaver: bool = True,
    timeout: int = 300
) -> AggregationResult:
    """
    Execute command aggregation workflow using SpiffWorkflow.
    
    Args:
        workflow_path: Path to BPMN workflow file
        parallel: Enable parallel execution
        validate_weaver: Include Weaver validation
        timeout: Execution timeout in seconds
        
    Returns:
        AggregationResult with execution details
    """
    start_time = time.time()
    
    with span("aggregate.execute_workflow", 
              workflow=str(workflow_path), 
              parallel=parallel):
        
        add_span_attributes(**{
            "aggregate.workflow_file": str(workflow_path),
            "aggregate.parallel": parallel,
            "aggregate.validate_weaver": validate_weaver,
            "aggregate.timeout": timeout,
        })
        
        commands_executed = []
        commands_successful = []
        commands_failed = []
        errors = []
        metrics = {}
        
        try:
            # Validate workflow file
            if not workflow_path.exists():
                raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
            # Validate BPMN structure
            bpmn_valid = validate_bpmn_file(workflow_path)
            if not bpmn_valid:
                raise ValueError("Invalid BPMN workflow file")
            
            # Weaver validation (if enabled)
            weaver_validation_passed = True
            if validate_weaver:
                try:
                    weaver_result = check_registry()
                    weaver_validation_passed = weaver_result.get("valid", False)
                    if not weaver_validation_passed:
                        errors.append("Weaver semantic convention validation failed")
                except Exception as e:
                    weaver_validation_passed = False
                    errors.append(f"Weaver validation error: {e}")
            
            # Execute workflow
            workflow_stats = run_bpmn(workflow_path)
            
            # Parse results
            if workflow_stats["status"] == "completed":
                # Extract executed commands from workflow data
                workflow_data = workflow_stats.get("data", {})
                commands_executed = workflow_data.get("commands_executed", [])
                commands_successful = workflow_data.get("commands_successful", [])
                commands_failed = workflow_data.get("commands_failed", [])
                
                # Calculate metrics
                metrics = {
                    "workflow_duration": workflow_stats.get("duration_seconds", 0),
                    "steps_executed": workflow_stats.get("steps_executed", 0),
                    "total_tasks": workflow_stats.get("total_tasks", 0),
                    "completed_tasks": workflow_stats.get("completed_tasks", 0),
                    "failed_tasks": workflow_stats.get("failed_tasks", 0),
                    "parallel_execution": parallel,
                    "weaver_validation": weaver_validation_passed,
                }
            else:
                commands_failed = ["workflow_execution"]
                errors.append(f"Workflow execution failed: {workflow_stats.get('error', 'Unknown error')}")
            
        except Exception as e:
            record_exception(e)
            commands_failed = ["workflow_execution"]
            errors.append(f"Workflow execution error: {e}")
        
        total_duration = time.time() - start_time
        
        # Create result
        result = AggregationResult(
            workflow_name=workflow_path.stem,
            commands_executed=commands_executed,
            commands_successful=commands_successful,
            commands_failed=commands_failed,
            total_duration=total_duration,
            parallel_execution=parallel,
            weaver_validation_passed=weaver_validation_passed,
            spiff_workflow_used=True,
            metrics=metrics,
            errors=errors,
        )
        
        # Record metrics
        metric_counter("aggregate.workflows.executed")(1)
        metric_histogram("aggregate.workflow.duration")(total_duration)
        
        add_span_event("aggregate.workflow.completed", {
            "commands_executed": len(commands_executed),
            "commands_successful": len(commands_successful),
            "commands_failed": len(commands_failed),
            "total_duration": total_duration,
            "weaver_validation": weaver_validation_passed,
        })
        
        return result


def validate_aggregation_workflow(
    workflow_path: Path,
    weaver_only: bool = False,
    spiff_only: bool = False
) -> Dict[str, Any]:
    """
    Validate aggregation workflow using Weaver semantic conventions.
    
    Args:
        workflow_path: Path to BPMN workflow file
        weaver_only: Only validate Weaver conventions
        spiff_only: Only validate SpiffWorkflow structure
        
    Returns:
        Validation result dictionary
    """
    with span("aggregate.validate_workflow", workflow=str(workflow_path)):
        add_span_attributes(**{
            "aggregate.workflow_file": str(workflow_path),
            "aggregate.weaver_only": weaver_only,
            "aggregate.spiff_only": spiff_only,
        })
        
        results = {}
        
        # SpiffWorkflow validation
        if not weaver_only:
            try:
                spiff_valid = validate_bpmn_file(workflow_path)
                results["spiff"] = {
                    "valid": spiff_valid,
                    "message": "BPMN workflow structure is valid" if spiff_valid else "Invalid BPMN structure",
                    "errors": [] if spiff_valid else ["Invalid BPMN workflow file"],
                }
            except Exception as e:
                results["spiff"] = {
                    "valid": False,
                    "message": f"SpiffWorkflow validation error: {e}",
                    "errors": [str(e)],
                }
        
        # Weaver validation
        if not spiff_only:
            try:
                weaver_result = check_registry()
                results["weaver"] = {
                    "valid": weaver_result.get("valid", False),
                    "message": weaver_result.get("message", "Weaver validation completed"),
                    "errors": weaver_result.get("errors", []),
                }
            except Exception as e:
                results["weaver"] = {
                    "valid": False,
                    "message": f"Weaver validation error: {e}",
                    "errors": [str(e)],
                }
        
        # Overall validation result
        all_valid = all(result.get("valid", False) for result in results.values())
        
        add_span_event("aggregate.validation.completed", {
            "weaver_valid": results.get("weaver", {}).get("valid", False),
            "spiff_valid": results.get("spiff", {}).get("valid", False),
            "overall_valid": all_valid,
        })
        
        return {
            "valid": all_valid,
            "results": results,
            "message": "All validations passed" if all_valid else "Some validations failed",
        }


def generate_bpmn_workflow(
    commands: List[str],
    parallel: bool = True,
    include_weaver: bool = True
) -> str:
    """
    Generate BPMN workflow content for command aggregation.
    
    Args:
        commands: List of commands to include
        parallel: Enable parallel execution
        include_weaver: Include Weaver validation
        
    Returns:
        BPMN XML content as string
    """
    with span("aggregate.generate_bpmn", commands_count=len(commands)):
        add_span_attributes(**{
            "aggregate.commands": ",".join(commands),
            "aggregate.parallel": parallel,
            "aggregate.include_weaver": include_weaver,
        })
        
        # Generate task XML
        tasks_xml = ""
        flows_xml = ""
        
        for i, cmd in enumerate(commands):
            task_id = f"Task_{cmd}"
            flow_id = f"Flow_{i}"
            
            # Task definition
            tasks_xml += f'''
    <bpmn:task id="{task_id}" name="Execute {cmd}">
      <bpmn:incoming>{flow_id}</bpmn:incoming>
      <bpmn:outgoing>Flow_{i + 1}</bpmn:outgoing>
      <bpmn:script>
        print(f"Executing {{cmd}}...")
        import subprocess
        import sys
        
        # Execute uvmgr command
        result = subprocess.run([
            sys.executable, "-m", "uvmgr.commands.{cmd}"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        # Store result
        task.workflow.data["{cmd}_result"] = {{
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode
        }}
        
        # Track execution
        if "commands_executed" not in task.workflow.data:
            task.workflow.data["commands_executed"] = []
        task.workflow.data["commands_executed"].append("{cmd}")
        
        if result.returncode == 0:
            if "commands_successful" not in task.workflow.data:
                task.workflow.data["commands_successful"] = []
            task.workflow.data["commands_successful"].append("{cmd}")
        else:
            if "commands_failed" not in task.workflow.data:
                task.workflow.data["commands_failed"] = []
            task.workflow.data["commands_failed"].append("{cmd}")
        
        print(f"{{cmd}} completed with return code: {{result.returncode}}")
      </bpmn:script>
    </bpmn:task>'''
            
            # Flow definition
            flows_xml += f'''
    <bpmn:sequenceFlow id="{flow_id}" sourceRef="{"start" if i == 0 else f"Task_{commands[i-1]}"}" targetRef="{task_id}" />'''
        
        # Add Weaver validation task if requested
        if include_weaver:
            weaver_task_id = "Task_weaver_validation"
            tasks_xml += f'''
    <bpmn:task id="{weaver_task_id}" name="Weaver Semantic Convention Validation">
      <bpmn:incoming>Flow_weaver</bpmn:incoming>
      <bpmn:outgoing>Flow_end</bpmn:outgoing>
      <bpmn:script>
        print("Validating Weaver semantic conventions...")
        import subprocess
        import sys
        
        # Run Weaver validation
        result = subprocess.run([
            sys.executable, "-m", "uvmgr.commands.weaver", "check"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        task.workflow.data["weaver_validation"] = {{
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }}
        
        print(f"Weaver validation completed: {{'SUCCESS' if result.returncode == 0 else 'FAILED'}}")
      </bpmn:script>
    </bpmn:task>'''
            
            flows_xml += f'''
    <bpmn:sequenceFlow id="Flow_weaver" sourceRef="Task_{commands[-1]}" targetRef="{weaver_task_id}" />
    <bpmn:sequenceFlow id="Flow_end" sourceRef="{weaver_task_id}" targetRef="end" />'''
        else:
            flows_xml += f'''
    <bpmn:sequenceFlow id="Flow_end" sourceRef="Task_{commands[-1]}" targetRef="end" />'''
        
        # Generate complete BPMN
        bpmn_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="CommandAggregation" name="Command Aggregation Workflow" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start Aggregation">
      <bpmn:outgoing>Flow_0</bpmn:outgoing>
    </bpmn:startEvent>
    
{tasks_xml}
    
    <bpmn:endEvent id="end" name="Aggregation Complete">
      <bpmn:incoming>{"Flow_end" if include_weaver else "Flow_end"}</bpmn:incoming>
    </bpmn:endEvent>
    
{flows_xml}
    
  </bpmn:process>
</bpmn:definitions>'''
        
        add_span_event("aggregate.bpmn.generated", {
            "commands_count": len(commands),
            "include_weaver": include_weaver,
            "bpmn_size": len(bpmn_content),
        })
        
        return bpmn_content


def get_aggregation_metrics(workflow_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get aggregation workflow metrics and status.
    
    Args:
        workflow_file: Optional specific workflow file
        
    Returns:
        Metrics dictionary
    """
    with span("aggregate.get_metrics"):
        add_span_attributes(**{
            "aggregate.workflow_file": str(workflow_file) if workflow_file else "all",
        })
        
        # Get metrics from all sources
        metrics_result = collect_metrics(
            project_path=project_path,
            sources=sources,
            time_range=time_range,
            detailed=detailed
        )
        
        return NotImplemented


def _calculate_critical_path(dependencies: Dict[str, List[str]]) -> List[str]:
    """Calculate critical path through command dependencies."""
    # Simple topological sort for critical path
    visited = set()
    path = []
    
    def visit(cmd: str):
        if cmd in visited:
            return
        visited.add(cmd)
        
        # Visit dependencies first
        for dep in dependencies.get(cmd, []):
            visit(dep)
        
        path.append(cmd)
    
    # Visit all commands
    for cmd in dependencies.keys():
        visit(cmd)
    
    return path


def _calculate_parallel_groups(dependencies: Dict[str, List[str]]) -> List[List[str]]:
    """Calculate groups of commands that can run in parallel."""
    # Simple grouping based on no dependencies between commands
    groups = []
    remaining = set(dependencies.keys())
    
    while remaining:
        # Find commands with no dependencies on remaining commands
        current_group = []
        for cmd in list(remaining):
            cmd_deps = set(dependencies.get(cmd, []))
            if not cmd_deps.intersection(remaining):
                current_group.append(cmd)
        
        if not current_group:
            # Circular dependency or no progress
            break
        
        groups.append(current_group)
        remaining -= set(current_group)
    
    return groups


def _generate_8020_bpmn_workflow(
    commands: List[str],
    dependencies: Dict[str, Any],
    parallel: bool,
    validate_weaver: bool,
    mode: str
) -> str:
    """Generate 8020-optimized BPMN workflow content."""
    # This would generate a more sophisticated BPMN with parallel execution
    # and dependency management based on the 8020 principle
    
    # For now, use the basic generation
    return generate_bpmn_workflow(
        commands=commands,
        parallel=parallel,
        include_weaver=validate_weaver
    ) 