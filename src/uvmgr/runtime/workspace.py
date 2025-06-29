"""
Workspace and environment management runtime implementation.

This module handles the actual execution of workspace management operations
at the runtime layer. It manages file system operations, environment creation,
and process execution for workspace isolation.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import span
from uvmgr.core.config import get_config


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
    with span("runtime.workspace.create"):
        try:
            # Determine workspace path
            if path is None:
                config = get_config()
                workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
                workspace_path = workspaces_dir / name
            else:
                workspace_path = path / name
                
            # Create workspace directory
            workspace_path.mkdir(parents=True, exist_ok=False)
            
            result = {
                "success": True,
                "workspace_path": str(workspace_path),
                "name": name,
                "isolated": isolated
            }
            
            # Initialize with template if provided
            if template:
                template_result = _apply_template(workspace_path, template)
                result["template_applied"] = template_result
                
            # Create isolated environment if requested
            if isolated:
                env_result = _create_isolated_environment(workspace_path, python_version)
                result["environment"] = env_result
                
            # Create workspace metadata
            metadata = {
                "name": name,
                "created_at": _get_timestamp(),
                "isolated": isolated,
                "python_version": python_version,
                "template": template
            }
            _save_workspace_metadata(workspace_path, metadata)
            
            return result
            
        except FileExistsError:
            return {
                "success": False,
                "error": f"Workspace '{name}' already exists"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def list_workspaces() -> Dict[str, Any]:
    """
    List available workspaces.
    
    Returns
    -------
    Dict[str, Any]
        List of workspaces with their details
    """
    with span("runtime.workspace.list"):
        try:
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            
            if not workspaces_dir.exists():
                return {"workspaces": []}
                
            workspaces = []
            for workspace_dir in workspaces_dir.iterdir():
                if workspace_dir.is_dir():
                    metadata = _load_workspace_metadata(workspace_dir)
                    workspace_info = {
                        "name": workspace_dir.name,
                        "path": str(workspace_dir),
                        "metadata": metadata
                    }
                    workspaces.append(workspace_info)
                    
            return {"workspaces": workspaces}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workspaces": []
            }


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
    with span("runtime.workspace.switch"):
        try:
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            workspace_path = workspaces_dir / name
            
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace '{name}' does not exist"
                }
                
            # Update current workspace in config
            _set_current_workspace(name)
            
            # Activate workspace environment if it exists
            env_path = workspace_path / ".venv"
            if env_path.exists():
                _activate_environment(env_path)
                
            return {
                "success": True,
                "current_workspace": name,
                "workspace_path": str(workspace_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


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
    with span("runtime.workspace.remove"):
        try:
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            workspace_path = workspaces_dir / name
            
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace '{name}' does not exist"
                }
                
            # Check for uncommitted changes if not forced
            if not force and _has_uncommitted_changes(workspace_path):
                return {
                    "success": False,
                    "error": "Workspace has uncommitted changes. Use --force to remove anyway."
                }
                
            # Remove workspace directory
            shutil.rmtree(workspace_path)
            
            # Update current workspace if this was the active one
            current = _get_current_workspace()
            if current == name:
                _set_current_workspace(None)
                
            return {
                "success": True,
                "removed": name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def get_workspace_status() -> Dict[str, Any]:
    """
    Get current workspace status and information.
    
    Returns
    -------
    Dict[str, Any]
        Current workspace status
    """
    with span("runtime.workspace.status"):
        try:
            current = _get_current_workspace()
            
            if not current:
                return {
                    "current": None,
                    "active": False
                }
                
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            workspace_path = workspaces_dir / current
            
            metadata = _load_workspace_metadata(workspace_path)
            
            # Check if environment is active
            env_active = _is_environment_active(workspace_path)
            
            return {
                "current": current,
                "active": True,
                "path": str(workspace_path),
                "metadata": metadata,
                "environment_active": env_active,
                "isolated": metadata.get("isolated", False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


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
    with span("runtime.workspace.isolate"):
        try:
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            workspace_path = workspaces_dir / name
            
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace '{name}' does not exist"
                }
                
            # Create git worktree if branch specified
            isolation_path = workspace_path
            if branch:
                worktree_path = workspace_path / f"worktree-{branch}"
                result = _create_git_worktree(workspace_path, worktree_path, branch)
                if not result["success"]:
                    return result
                isolation_path = worktree_path
                
            # Ensure isolated environment exists
            env_result = _create_isolated_environment(isolation_path)
            
            return {
                "success": True,
                "isolation_path": str(isolation_path),
                "environment": env_result,
                "branch": branch
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


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
    with span("runtime.workspace.cleanup"):
        try:
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            
            if not workspaces_dir.exists():
                return {"cleaned": [], "success": True}
                
            cleaned = []
            current = _get_current_workspace()
            
            for workspace_dir in workspaces_dir.iterdir():
                if not workspace_dir.is_dir():
                    continue
                    
                workspace_name = workspace_dir.name
                
                # Skip current workspace
                if workspace_name == current:
                    continue
                    
                should_clean = False
                
                if unused_only:
                    # Check if workspace is unused (no recent activity)
                    if _is_workspace_unused(workspace_dir):
                        should_clean = True
                else:
                    # Clean all non-current workspaces
                    should_clean = True
                    
                if should_clean:
                    if not dry_run:
                        shutil.rmtree(workspace_dir)
                    cleaned.append(workspace_name)
                    
            return {
                "success": True,
                "cleaned": cleaned,
                "dry_run": dry_run
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cleaned": []
            }


def sync_workspace_dependencies(name: Optional[str] = None) -> Dict[str, Any]:
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
    with span("runtime.workspace.sync_deps"):
        try:
            if name is None:
                name = _get_current_workspace()
                
            if not name:
                return {
                    "success": False,
                    "error": "No current workspace"
                }
                
            config = get_config()
            workspaces_dir = Path(config.get("workspaces_dir", Path.home() / ".uvmgr_workspaces"))
            workspace_path = workspaces_dir / name
            
            # Run uv sync in the workspace
            cmd = ["uv", "sync"]
            result = subprocess.run(
                cmd,
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "dependencies_synced": _count_dependencies(workspace_path),
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Helper functions

def _apply_template(workspace_path: Path, template: str) -> Dict[str, Any]:
    """Apply a template to the workspace."""
    # This is a placeholder for template application
    # In a real implementation, this would copy template files
    return {"success": True, "template": template}


def _create_isolated_environment(
    workspace_path: Path,
    python_version: Optional[str] = None
) -> Dict[str, Any]:
    """Create an isolated Python environment."""
    try:
        env_path = workspace_path / ".venv"
        
        cmd = ["python", "-m", "venv", str(env_path)]
        if python_version:
            cmd = [f"python{python_version}", "-m", "venv", str(env_path)]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "environment_path": str(env_path),
            "python_version": python_version
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _save_workspace_metadata(workspace_path: Path, metadata: Dict[str, Any]) -> None:
    """Save workspace metadata to file."""
    import json
    
    metadata_file = workspace_path / ".uvmgr_workspace.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)


def _load_workspace_metadata(workspace_path: Path) -> Dict[str, Any]:
    """Load workspace metadata from file."""
    import json
    
    metadata_file = workspace_path / ".uvmgr_workspace.json"
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()


def _set_current_workspace(name: Optional[str]) -> None:
    """Set the current workspace in configuration."""
    # This would update the configuration file
    # For now, we'll use an environment variable
    if name:
        os.environ["UVMGR_CURRENT_WORKSPACE"] = name
    else:
        os.environ.pop("UVMGR_CURRENT_WORKSPACE", None)


def _get_current_workspace() -> Optional[str]:
    """Get the current workspace from configuration."""
    return os.environ.get("UVMGR_CURRENT_WORKSPACE")


def _has_uncommitted_changes(workspace_path: Path) -> bool:
    """Check if workspace has uncommitted git changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except:
        return False


def _is_environment_active(workspace_path: Path) -> bool:
    """Check if the workspace environment is currently active."""
    env_path = workspace_path / ".venv"
    virtual_env = os.environ.get("VIRTUAL_ENV")
    return virtual_env and Path(virtual_env) == env_path


def _activate_environment(env_path: Path) -> None:
    """Activate the workspace environment."""
    # Update environment variables to activate the environment
    os.environ["VIRTUAL_ENV"] = str(env_path)
    os.environ["PATH"] = f"{env_path / 'bin'}:{os.environ['PATH']}"


def _create_git_worktree(
    workspace_path: Path,
    worktree_path: Path,
    branch: str
) -> Dict[str, Any]:
    """Create a git worktree for branch isolation."""
    try:
        cmd = ["git", "worktree", "add", str(worktree_path), branch]
        result = subprocess.run(
            cmd,
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "worktree_path": str(worktree_path),
            "branch": branch,
            "output": result.stdout
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _is_workspace_unused(workspace_path: Path) -> bool:
    """Check if workspace is unused (simple heuristic)."""
    import time
    
    # Check if workspace was modified in the last 30 days
    cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30 days ago
    
    try:
        stat = workspace_path.stat()
        return stat.st_mtime < cutoff_time
    except:
        return True


def _count_dependencies(workspace_path: Path) -> int:
    """Count dependencies in workspace."""
    try:
        pyproject_file = workspace_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
                
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
                
            deps = len(data.get("project", {}).get("dependencies", []))
            
            # Add dev dependencies
            for group in data.get("dependency-groups", {}).values():
                if isinstance(group, list):
                    deps += len(group)
                    
            return deps
    except:
        pass
    return 0