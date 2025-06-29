"""
Workflow management runtime implementation.

This module handles the actual execution of workflow orchestration operations
at the runtime layer. It manages file I/O, template processing, and workflow
execution using various engines.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import span


def create_workflow_from_template(
    name: str,
    template: str,
    path: Optional[Path] = None,
    variables: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a workflow from a template.
    
    Parameters
    ----------
    name : str
        Name of the workflow
    template : str
        Template to use
    path : Optional[Path]
        Where to create the workflow
    variables : Optional[Dict[str, Any]]
        Template variables
        
    Returns
    -------
    Dict[str, Any]
        Creation results
    """
    with span("runtime.workflow.create_from_template"):
        try:
            # Determine output path
            if path is None:
                output_path = Path.cwd() / f"{name}.workflow.yaml"
            else:
                output_path = path / f"{name}.workflow.yaml"
                
            # Get template content
            template_content = _get_template_content(template)
            if not template_content:
                return {
                    "success": False,
                    "error": f"Template '{template}' not found"
                }
                
            # Substitute variables
            workflow_content = _substitute_template_variables(
                template_content, 
                variables or {}
            )
            
            # Write workflow file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(workflow_content)
                
            return {
                "success": True,
                "workflow_path": str(output_path),
                "template_used": template
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def execute_workflow_file(
    workflow_path: Path,
    inputs: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute a workflow definition file.
    
    Parameters
    ----------
    workflow_path : Path
        Path to workflow definition
    inputs : Optional[Dict[str, Any]]
        Input parameters
    dry_run : bool
        Whether to perform dry run
        
    Returns
    -------
    Dict[str, Any]
        Execution results
    """
    with span("runtime.workflow.execute_file"):
        try:
            if not workflow_path.exists():
                return {
                    "success": False,
                    "error": f"Workflow file not found: {workflow_path}"
                }
                
            # Load workflow definition
            workflow_def = _load_workflow_definition(workflow_path)
            if not workflow_def:
                return {
                    "success": False,
                    "error": "Failed to load workflow definition"
                }
                
            # Execute workflow steps
            if dry_run:
                return _dry_run_workflow(workflow_def, inputs or {})
            else:
                return _execute_workflow_steps(workflow_def, inputs or {})
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def validate_workflow_definition(workflow_path: Path) -> Dict[str, Any]:
    """
    Validate a workflow definition file.
    
    Parameters
    ----------
    workflow_path : Path
        Path to workflow definition
        
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    with span("runtime.workflow.validate"):
        try:
            if not workflow_path.exists():
                return {
                    "valid": False,
                    "errors": [f"Workflow file not found: {workflow_path}"]
                }
                
            # Load and validate syntax
            workflow_def = _load_workflow_definition(workflow_path)
            if not workflow_def:
                return {
                    "valid": False,
                    "errors": ["Invalid YAML/JSON syntax"]
                }
                
            # Validate structure
            errors = []
            warnings = []
            
            # Check required fields
            if "name" not in workflow_def:
                errors.append("Missing required field: name")
            if "steps" not in workflow_def:
                errors.append("Missing required field: steps")
            elif not isinstance(workflow_def["steps"], list):
                errors.append("Field 'steps' must be a list")
                
            # Validate steps
            for i, step in enumerate(workflow_def.get("steps", [])):
                if not isinstance(step, dict):
                    errors.append(f"Step {i} must be an object")
                    continue
                    
                if "name" not in step:
                    warnings.append(f"Step {i} missing name field")
                if "action" not in step:
                    errors.append(f"Step {i} missing required field: action")
                    
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)]
            }


def discover_workflows(
    search_path: Optional[Path] = None,
    include_templates: bool = True
) -> Dict[str, Any]:
    """
    Discover workflow files and templates.
    
    Parameters
    ----------
    search_path : Optional[Path]
        Path to search in
    include_templates : bool
        Whether to include templates
        
    Returns
    -------
    Dict[str, Any]
        Discovery results
    """
    with span("runtime.workflow.discover"):
        try:
            search_dir = search_path or Path.cwd()
            
            workflows = []
            templates = []
            
            # Find workflow files
            for pattern in ["*.workflow.yaml", "*.workflow.yml", "*.workflow.json"]:
                for workflow_file in search_dir.rglob(pattern):
                    workflows.append({
                        "name": workflow_file.stem.replace(".workflow", ""),
                        "path": str(workflow_file),
                        "type": workflow_file.suffix[1:]  # Remove dot
                    })
                    
            # Find template files if requested
            if include_templates:
                template_dirs = [
                    search_dir / ".uvmgr" / "templates" / "workflows",
                    Path.home() / ".uvmgr" / "templates" / "workflows"
                ]
                
                for template_dir in template_dirs:
                    if template_dir.exists():
                        for template_file in template_dir.rglob("*.template.*"):
                            templates.append({
                                "name": template_file.stem.replace(".template", ""),
                                "path": str(template_file),
                                "type": "template"
                            })
                            
            return {
                "success": True,
                "workflows": workflows,
                "templates": templates
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflows": [],
                "templates": []
            }


def generate_template(
    template_type: str,
    output_path: Path,
    customizations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a workflow template.
    
    Parameters
    ----------
    template_type : str
        Type of template to generate
    output_path : Path
        Where to save the template
    customizations : Optional[Dict[str, Any]]
        Template customizations
        
    Returns
    -------
    Dict[str, Any]
        Generation results
    """
    with span("runtime.workflow.generate_template"):
        try:
            # Get base template
            base_template = _get_base_template(template_type)
            if not base_template:
                return {
                    "success": False,
                    "error": f"Unknown template type: {template_type}"
                }
                
            # Apply customizations
            customized_template = _apply_template_customizations(
                base_template, 
                customizations or {}
            )
            
            # Write template file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                yaml.dump(customized_template, f, default_flow_style=False)
                
            return {
                "success": True,
                "template_path": str(output_path),
                "template_type": template_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


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
        Path to workflow file
    schedule : str
        Cron-style schedule
    inputs : Optional[Dict[str, Any]]
        Default inputs
    enabled : bool
        Whether enabled
        
    Returns
    -------
    Dict[str, Any]
        Scheduling results
    """
    with span("runtime.workflow.schedule"):
        try:
            import uuid
            
            schedule_id = str(uuid.uuid4())
            
            # Create schedule entry
            schedule_entry = {
                "id": schedule_id,
                "workflow_path": str(workflow_path),
                "schedule": schedule,
                "inputs": inputs or {},
                "enabled": enabled,
                "created_at": _get_timestamp()
            }
            
            # Save to schedule file
            schedule_file = Path.home() / ".uvmgr" / "schedules.json"
            schedule_file.parent.mkdir(parents=True, exist_ok=True)
            
            schedules = []
            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedules = json.load(f)
                    
            schedules.append(schedule_entry)
            
            with open(schedule_file, 'w') as f:
                json.dump(schedules, f, indent=2)
                
            return {
                "success": True,
                "schedule_id": schedule_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def get_execution_status(
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get workflow execution status.
    
    Parameters
    ----------
    workflow_id : Optional[str]
        Workflow ID to check
    execution_id : Optional[str]
        Execution ID to check
        
    Returns
    -------
    Dict[str, Any]
        Status results
    """
    with span("runtime.workflow.get_status"):
        try:
            # This is a simplified implementation
            # In a real system, this would query a workflow engine
            
            return {
                "success": True,
                "active_executions": 0,
                "recent_executions": [],
                "status": "No active executions"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Helper functions

def _get_template_content(template: str) -> Optional[str]:
    """Get template content by name."""
    # Built-in templates
    templates = {
        "ci": """
name: CI Workflow
description: Continuous Integration workflow
steps:
  - name: Install dependencies
    action: run
    command: uvmgr deps sync
  - name: Run lints
    action: run
    command: uvmgr lint check
  - name: Run tests
    action: run
    command: uvmgr tests run
""",
        "build": """
name: Build Workflow
description: Build and package workflow
steps:
  - name: Build package
    action: run
    command: uvmgr build
  - name: Test package
    action: run
    command: uvmgr tests run
""",
        "release": """
name: Release Workflow
description: Version bump and release workflow
steps:
  - name: Bump version
    action: run
    command: uvmgr release version {{ version_type }}
  - name: Build package
    action: run
    command: uvmgr build
  - name: Upload to PyPI
    action: run
    command: uvmgr build upload
"""
    }
    
    return templates.get(template)


def _substitute_template_variables(content: str, variables: Dict[str, Any]) -> str:
    """Substitute template variables."""
    result = content
    for key, value in variables.items():
        result = result.replace(f"{{{{ {key} }}}}", str(value))
    return result


def _load_workflow_definition(workflow_path: Path) -> Optional[Dict[str, Any]]:
    """Load workflow definition from file."""
    try:
        with open(workflow_path) as f:
            if workflow_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                return yaml.safe_load(f)
    except Exception:
        return None


def _dry_run_workflow(workflow_def: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Perform dry run of workflow."""
    steps = workflow_def.get("steps", [])
    
    return {
        "success": True,
        "dry_run": True,
        "steps_would_execute": len(steps),
        "steps_failed": 0,
        "steps": [{"name": step.get("name", f"Step {i}"), "action": step.get("action")} 
                 for i, step in enumerate(steps)]
    }


def _execute_workflow_steps(workflow_def: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute workflow steps."""
    steps = workflow_def.get("steps", [])
    executed = 0
    failed = 0
    
    for step in steps:
        try:
            action = step.get("action")
            if action == "run":
                command = step.get("command", "")
                # Substitute inputs in command
                for key, value in inputs.items():
                    command = command.replace(f"{{{{ {key} }}}}", str(value))
                    
                # Execute command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    failed += 1
                else:
                    executed += 1
            else:
                executed += 1
                
        except Exception:
            failed += 1
            
    return {
        "success": failed == 0,
        "steps_executed": executed,
        "steps_failed": failed,
        "total_steps": len(steps)
    }


def _get_base_template(template_type: str) -> Optional[Dict[str, Any]]:
    """Get base template structure."""
    templates = {
        "ci": {
            "name": "CI Template",
            "description": "Continuous Integration template",
            "steps": [
                {"name": "Setup", "action": "run", "command": "uvmgr deps sync"},
                {"name": "Lint", "action": "run", "command": "uvmgr lint check"},
                {"name": "Test", "action": "run", "command": "uvmgr tests run"}
            ]
        },
        "build": {
            "name": "Build Template", 
            "description": "Build and package template",
            "steps": [
                {"name": "Build", "action": "run", "command": "uvmgr build"}
            ]
        }
    }
    
    return templates.get(template_type)


def _apply_template_customizations(template: Dict[str, Any], customizations: Dict[str, Any]) -> Dict[str, Any]:
    """Apply customizations to template."""
    result = template.copy()
    
    # Apply name customization
    if "name" in customizations:
        result["name"] = customizations["name"]
        
    # Apply description customization
    if "description" in customizations:
        result["description"] = customizations["description"]
        
    # Apply additional steps
    if "additional_steps" in customizations:
        result["steps"].extend(customizations["additional_steps"])
        
    return result


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()