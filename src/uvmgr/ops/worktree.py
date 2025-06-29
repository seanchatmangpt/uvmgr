"""
uvmgr.ops.worktree - Git Worktree Operations
==========================================

Business logic for Git worktree management and project isolation.

This module provides the core operations for Git worktree management,
enabling isolated development environments for multiple projects and branches.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.instrumentation import add_span_attributes, add_span_event


@timed
def create_worktree(
    branch: str,
    path: Optional[Path] = None,
    track_remote: bool = True,
    force: bool = False,
    isolated: bool = False,
) -> Dict[str, Any]:
    """Create a new Git worktree for a branch."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.create", branch=branch, isolated=isolated):
        add_span_attributes(**{
            "worktree.branch": branch,
            "worktree.isolated": isolated,
            "worktree.track_remote": track_remote,
            "worktree.force": force,
        })
        
        try:
            result = _rt.create_worktree(
                branch=branch,
                path=path,
                track_remote=track_remote,
                force=force,
                isolated=isolated,
            )
            
            add_span_event("worktree.created", {
                "path": str(result["path"]),
                "branch": branch,
                "isolated": isolated,
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def list_worktrees(verbose: bool = False, status: bool = False) -> List[Dict[str, Any]]:
    """List all Git worktrees."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.list"):
        add_span_attributes(**{
            "worktree.verbose": verbose,
            "worktree.show_status": status,
        })
        
        try:
            worktrees = _rt.list_worktrees(verbose=verbose, status=status)
            
            add_span_attributes(**{"worktree.count": len(worktrees)})
            
            return worktrees
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def remove_worktree(
    path: Path,
    force: bool = False,
    cleanup_env: bool = True,
) -> Dict[str, Any]:
    """Remove a Git worktree."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.remove", path=str(path)):
        add_span_attributes(**{
            "worktree.path": str(path),
            "worktree.force": force,
            "worktree.cleanup_env": cleanup_env,
        })
        
        try:
            result = _rt.remove_worktree(
                path=path,
                force=force,
                cleanup_env=cleanup_env,
            )
            
            add_span_event("worktree.removed", {
                "path": str(path),
                "env_removed": result.get("env_removed", False),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def switch_to_worktree(
    path: Path,
    activate_env: bool = True,
) -> Dict[str, Any]:
    """Switch to a different worktree."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.switch", path=str(path)):
        add_span_attributes(**{
            "worktree.path": str(path),
            "worktree.activate_env": activate_env,
        })
        
        try:
            result = _rt.switch_to_worktree(
                path=path,
                activate_env=activate_env,
            )
            
            add_span_event("worktree.switched", {
                "path": str(path),
                "branch": result.get("branch"),
                "env_activated": result.get("env_activated", False),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def create_isolated_environment(
    project_path: Path,
    branch: Optional[str] = None,
    name: Optional[str] = None,
    install_uvmgr: bool = True,
    sync_deps: bool = True,
) -> Dict[str, Any]:
    """Create isolated environment for external project development."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.isolate", project_path=str(project_path)):
        add_span_attributes(**{
            "worktree.project_path": str(project_path),
            "worktree.branch": branch or "main",
            "worktree.install_uvmgr": install_uvmgr,
            "worktree.sync_deps": sync_deps,
        })
        
        try:
            result = _rt.create_isolated_environment(
                project_path=project_path,
                branch=branch,
                name=name,
                install_uvmgr=install_uvmgr,
                sync_deps=sync_deps,
            )
            
            add_span_event("worktree.isolated", {
                "project_path": str(project_path),
                "worktree_path": str(result["worktree_path"]),
                "uvmgr_installed": result.get("uvmgr_installed", False),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def cleanup_worktrees(
    dry_run: bool = False,
    force: bool = False,
    max_age_days: int = 30,
    cleanup_envs: bool = True,
) -> Dict[str, Any]:
    """Clean up unused and stale worktrees."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.cleanup"):
        add_span_attributes(**{
            "worktree.dry_run": dry_run,
            "worktree.force": force,
            "worktree.max_age_days": max_age_days,
            "worktree.cleanup_envs": cleanup_envs,
        })
        
        try:
            result = _rt.cleanup_worktrees(
                dry_run=dry_run,
                force=force,
                max_age_days=max_age_days,
                cleanup_envs=cleanup_envs,
            )
            
            add_span_event("worktree.cleanup_completed", {
                "candidates_found": len(result.get("candidates", [])),
                "cleaned_up": len(result.get("cleaned", [])),
                "dry_run": dry_run,
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def get_worktree_status(
    path: Optional[Path] = None,
    detailed: bool = False,
) -> Dict[str, Any]:
    """Get status of worktrees and isolated environments."""
    from uvmgr.runtime import worktree as _rt
    
    with span("worktree.status"):
        add_span_attributes(**{
            "worktree.path": str(path) if path else "all",
            "worktree.detailed": detailed,
        })
        
        try:
            result = _rt.get_worktree_status(path=path, detailed=detailed)
            
            add_span_attributes(**{
                "worktree.total_count": result.get("total_count", 0),
                "worktree.isolated_count": result.get("isolated_count", 0),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


# Helper functions for worktree management

def _get_worktree_config_path() -> Path:
    """Get path to worktree configuration file."""
    config_dir = Path.home() / ".uvmgr" / "worktrees"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def _save_worktree_config(config: Dict[str, Any]) -> None:
    """Save worktree configuration."""
    config_path = _get_worktree_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)


def _load_worktree_config() -> Dict[str, Any]:
    """Load worktree configuration."""
    config_path = _get_worktree_config_path()
    if not config_path.exists():
        return {"worktrees": [], "isolated_envs": []}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def register_worktree(
    path: Path,
    branch: str,
    isolated: bool = False,
    environment: Optional[str] = None,
) -> None:
    """Register a worktree in configuration."""
    config = _load_worktree_config()
    
    worktree_info = {
        "path": str(path),
        "branch": branch,
        "isolated": isolated,
        "environment": environment,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
    }
    
    # Remove existing entry for same path
    config["worktrees"] = [
        wt for wt in config["worktrees"] 
        if wt["path"] != str(path)
    ]
    
    config["worktrees"].append(worktree_info)
    _save_worktree_config(config)


def unregister_worktree(path: Path) -> None:
    """Unregister a worktree from configuration."""
    config = _load_worktree_config()
    
    config["worktrees"] = [
        wt for wt in config["worktrees"] 
        if wt["path"] != str(path)
    ]
    
    _save_worktree_config(config)


def get_registered_worktrees() -> List[Dict[str, Any]]:
    """Get list of registered worktrees."""
    config = _load_worktree_config()
    return config.get("worktrees", [])


def update_worktree_access_time(path: Path) -> None:
    """Update last access time for a worktree."""
    config = _load_worktree_config()
    
    for wt in config["worktrees"]:
        if wt["path"] == str(path):
            wt["last_accessed"] = datetime.now().isoformat()
            break
    
    _save_worktree_config(config)


def find_stale_worktrees(max_age_days: int = 30) -> List[Dict[str, Any]]:
    """Find worktrees that haven't been accessed recently."""
    config = _load_worktree_config()
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    stale_worktrees = []
    for wt in config["worktrees"]:
        try:
            last_accessed = datetime.fromisoformat(wt["last_accessed"])
            if last_accessed < cutoff_date:
                # Check if path still exists
                path = Path(wt["path"])
                if path.exists():
                    age_days = (datetime.now() - last_accessed).days
                    wt["age_days"] = age_days
                    stale_worktrees.append(wt)
                else:
                    # Path doesn't exist, remove from config
                    unregister_worktree(path)
        except (KeyError, ValueError):
            # Invalid date format, consider it stale
            stale_worktrees.append(wt)
    
    return stale_worktrees