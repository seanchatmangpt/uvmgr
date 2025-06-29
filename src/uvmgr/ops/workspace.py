"""
Workspace and environment management operations.

This module provides business logic for workspace management,
environment isolation, and project organization. It follows the
80/20 principle by focusing on the most essential workspace operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.core.semconv import WorktreeAttributes, WorktreeOperations
from uvmgr.runtime import workspace as workspace_runtime


def create_workspace(
    name: str,
    path: Optional[Path] = None,
    template: Optional[str] = None,
    isolated: bool = True,
    python_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new workspace environment.
    
    Parameters
    ----------
    name : str
        Name of the workspace
    path : Optional[Path]
        Path where to create the workspace
    template : Optional[str]
        Template to use for workspace initialization
    isolated : bool
        Whether to create an isolated environment
    python_version : Optional[str]
        Python version to use
        
    Returns
    -------
    Dict[str, Any]
        Workspace creation results
    """
    with span("workspace.create") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.CREATE,
            "workspace.name": name,
            "workspace.path": str(path) if path else None,
            "workspace.template": template,
            WorktreeAttributes.ISOLATED: isolated,
            "workspace.python_version": python_version,
        })
        
        # Delegate to runtime
        result = workspace_runtime.create_workspace(
            name=name,
            path=path,
            template=template,
            isolated=isolated,
            python_version=python_version
        )
        
        add_span_attributes(**{
            "workspace.success": result.get("success", False),
            "workspace.created_path": result.get("workspace_path", ""),
        })
        
        return result


def list_workspaces() -> Dict[str, Any]:
    """
    List available workspaces.
    
    Returns
    -------
    Dict[str, Any]
        List of workspaces with their details
    """
    with span("workspace.list") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.LIST,
        })
        
        # Delegate to runtime
        result = workspace_runtime.list_workspaces()
        
        workspace_count = len(result.get("workspaces", []))
        add_span_attributes(**{
            "workspace.count": workspace_count,
        })
        
        return result


def switch_workspace(name: str) -> Dict[str, Any]:
    """
    Switch to a different workspace.
    
    Parameters
    ----------
    name : str
        Name of the workspace to switch to
        
    Returns
    -------
    Dict[str, Any]
        Switch operation results
    """
    with span("workspace.switch") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.SWITCH,
            "workspace.target": name,
        })
        
        # Delegate to runtime
        result = workspace_runtime.switch_workspace(name)
        
        add_span_attributes(**{
            "workspace.switch_success": result.get("success", False),
            "workspace.current": result.get("current_workspace", ""),
        })
        
        return result


def remove_workspace(
    name: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Remove a workspace.
    
    Parameters
    ----------
    name : str
        Name of the workspace to remove
    force : bool
        Whether to force removal even if workspace has changes
        
    Returns
    -------
    Dict[str, Any]
        Removal operation results
    """
    with span("workspace.remove") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.REMOVE,
            "workspace.name": name,
            "workspace.force": force,
        })
        
        # Delegate to runtime
        result = workspace_runtime.remove_workspace(
            name=name,
            force=force
        )
        
        add_span_attributes(**{
            "workspace.removal_success": result.get("success", False),
        })
        
        return result


def get_workspace_status() -> Dict[str, Any]:
    """
    Get current workspace status and information.
    
    Returns
    -------
    Dict[str, Any]
        Current workspace status
    """
    with span("workspace.status") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.STATUS,
        })
        
        # Delegate to runtime
        result = workspace_runtime.get_workspace_status()
        
        add_span_attributes(**{
            "workspace.current": result.get("current", ""),
            "workspace.active": result.get("active", False),
            WorktreeAttributes.ISOLATED: result.get("isolated", False),
        })
        
        return result


def isolate_workspace(
    name: str,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an isolated environment for a workspace.
    
    Parameters
    ----------
    name : str
        Name of the workspace to isolate
    branch : Optional[str]
        Git branch to isolate to
        
    Returns
    -------
    Dict[str, Any]
        Isolation operation results
    """
    with span("workspace.isolate") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.ISOLATE,
            "workspace.name": name,
            WorktreeAttributes.BRANCH: branch,
        })
        
        # Delegate to runtime
        result = workspace_runtime.isolate_workspace(
            name=name,
            branch=branch
        )
        
        add_span_attributes(**{
            "workspace.isolation_success": result.get("success", False),
            "workspace.isolation_path": result.get("isolation_path", ""),
        })
        
        return result


def cleanup_workspaces(
    unused_only: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clean up unused or stale workspaces.
    
    Parameters
    ----------
    unused_only : bool
        Whether to only clean up unused workspaces
    dry_run : bool
        Whether to only show what would be cleaned up
        
    Returns
    -------
    Dict[str, Any]
        Cleanup operation results
    """
    with span("workspace.cleanup") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.CLEANUP,
            "workspace.unused_only": unused_only,
            "workspace.dry_run": dry_run,
        })
        
        # Delegate to runtime
        result = workspace_runtime.cleanup_workspaces(
            unused_only=unused_only,
            dry_run=dry_run
        )
        
        cleaned_count = len(result.get("cleaned", []))
        add_span_attributes(**{
            "workspace.cleaned_count": cleaned_count,
            "workspace.cleanup_success": result.get("success", False),
        })
        
        return result


def sync_workspace_dependencies(
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync dependencies for a workspace.
    
    Parameters
    ----------
    name : Optional[str]
        Name of workspace to sync (current if None)
        
    Returns
    -------
    Dict[str, Any]
        Sync operation results
    """
    with span("workspace.sync_deps") as current_span:
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: "sync_dependencies",
            "workspace.name": name or "current",
        })
        
        # Delegate to runtime
        result = workspace_runtime.sync_workspace_dependencies(name)
        
        add_span_attributes(**{
            "workspace.sync_success": result.get("success", False),
            "workspace.deps_synced": result.get("dependencies_synced", 0),
        })
        
        return result