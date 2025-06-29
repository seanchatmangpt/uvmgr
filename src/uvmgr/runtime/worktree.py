"""
uvmgr.runtime.worktree - Git Worktree Runtime
============================================

Runtime layer for Git worktree operations with subprocess execution.

This module provides the actual implementation of Git worktree operations,
handling subprocess calls, file system operations, and environment setup.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from uvmgr.core.process import run
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import WorktreeAttributes, WorktreeOperations


class WorktreeError(Exception):
    """Error during Git worktree operations."""
    pass


def create_worktree(
    branch: str,
    path: Optional[Path] = None,
    track_remote: bool = True,
    force: bool = False,
    isolated: bool = False,
) -> Dict[str, Any]:
    """Create a new Git worktree for a branch."""
    with span("runtime.worktree.create", branch=branch):
        add_span_attributes(**{
            WorktreeAttributes.OPERATION: WorktreeOperations.CREATE,
            WorktreeAttributes.BRANCH: branch,
            WorktreeAttributes.ISOLATED: str(isolated),
            WorktreeAttributes.TRACK_REMOTE: str(track_remote),
        })
        add_span_event("worktree.create.started", {
            "branch": branch,
            "isolated": isolated,
            "force": force
        })
        
        try:
            # Determine worktree path
            if path is None:
                repo_root = _get_git_root()
                path = repo_root.parent / f"{repo_root.name}-{branch.replace('/', '-')}"
            
            path = Path(path).resolve()
            add_span_attributes(**{
                WorktreeAttributes.PATH: str(path),
            })
            
            # Check if worktree already exists
            if path.exists() and not force:
                add_span_event("worktree.create.failed", {"reason": "path_exists"})
                raise WorktreeError(f"Worktree path already exists: {path}")
            
            # Check if branch exists, create if it doesn't
            try:
                run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], 
                    capture=True, cwd=_get_git_root())
                branch_exists = True
            except subprocess.CalledProcessError:
                branch_exists = False
            
            # Create Git worktree
            git_cmd = ["git", "worktree", "add"]
            
            if force:
                git_cmd.append("--force")
            
            # Use -b only if branch doesn't exist
            if not branch_exists:
                git_cmd.extend(["-b", branch])
            
            git_cmd.extend([str(path), branch])
            
            add_span_event("git.worktree.create", {"command": " ".join(git_cmd)})
            
            output = run(git_cmd, capture=True, cwd=_get_git_root())
            
            if output is None:
                add_span_event("worktree.create.failed", {"reason": "command_failed"})
                raise WorktreeError("Failed to create worktree: Command failed")
            
            # Set up isolated environment if requested
            env_path = None
            venv_created = False
            
            if isolated:
                env_path, venv_created = _setup_isolated_environment(path)
                add_span_attributes(**{
                    WorktreeAttributes.ENVIRONMENT: str(env_path) if env_path else None,
                })
            
            # Register worktree
            from uvmgr.ops.worktree import register_worktree
            register_worktree(
                path=path,
                branch=branch,
                isolated=isolated,
                environment=str(env_path) if env_path else None,
            )
            
            add_span_event("worktree.create.completed", {
                "path": str(path),
                "venv_created": venv_created
            })
            
            return {
                "path": path,
                "branch": branch,
                "isolated": isolated,
                "env_path": env_path,
                "venv_created": venv_created,
                "track_remote": track_remote,
            }
            
        except subprocess.CalledProcessError as e:
            record_exception(e)
            add_span_event("worktree.create.failed", {"error": str(e)})
            raise WorktreeError(f"Git worktree creation failed: {e}") from e
        except Exception as e:
            record_exception(e)
            add_span_event("worktree.create.failed", {"error": str(e)})
            raise


def list_worktrees(verbose: bool = False, status: bool = False) -> List[Dict[str, Any]]:
    """List all Git worktrees."""
    with span("runtime.worktree.list"):
        try:
            # Get Git worktrees
            output = run(["git", "worktree", "list", "--porcelain"], capture=True, cwd=_get_git_root())
            
            if output is None:
                raise WorktreeError("Failed to list worktrees: No output received")
            
            # Parse Git worktree output
            worktrees = []
            current_wt = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    if current_wt:
                        worktrees.append(current_wt)
                        current_wt = {}
                elif line.startswith('worktree '):
                    current_wt['path'] = Path(line[9:])
                elif line.startswith('HEAD '):
                    current_wt['head'] = line[5:]
                elif line.startswith('branch '):
                    current_wt['branch'] = line[7:]
                elif line == 'bare':
                    current_wt['bare'] = True
                elif line == 'detached':
                    current_wt['detached'] = True
            
            if current_wt:
                worktrees.append(current_wt)
            
            # Enhance with additional information
            from uvmgr.ops.worktree import get_registered_worktrees
            registered = {wt["path"]: wt for wt in get_registered_worktrees()}
            
            for wt in worktrees:
                path_str = str(wt['path'])
                if path_str in registered:
                    reg_info = registered[path_str]
                    wt['isolated'] = reg_info.get('isolated', False)
                    wt['environment'] = reg_info.get('environment')
                    wt['created_at'] = reg_info.get('created_at')
                    wt['last_accessed'] = reg_info.get('last_accessed')
                
                # Add status information
                if status:
                    wt_status = _get_worktree_git_status(wt['path'])
                    wt['status'] = wt_status['status']
                    wt['files_changed'] = wt_status['files_changed']
                
                # Add verbose information
                if verbose:
                    wt['last_commit'] = _get_last_commit(wt['path'])
                    wt['type'] = 'isolated' if wt.get('isolated') else 'standard'
            
            return worktrees
            
        except subprocess.CalledProcessError as e:
            record_exception(e)
            raise WorktreeError(f"Failed to list worktrees: {e}") from e
        except Exception as e:
            record_exception(e)
            raise


def remove_worktree(
    path: Path,
    force: bool = False,
    cleanup_env: bool = True,
) -> Dict[str, Any]:
    """Remove a Git worktree."""
    with span("runtime.worktree.remove", path=str(path)):
        try:
            path = Path(path).resolve()
            
            if not path.exists():
                raise WorktreeError(f"Worktree path does not exist: {path}")
            
            # Check for uncommitted changes
            if not force:
                git_status = _get_worktree_git_status(path)
                if git_status['files_changed'] > 0:
                    raise WorktreeError(f"Worktree has uncommitted changes. Use --force to remove anyway.")
            
            # Get registered info before removal
            from uvmgr.ops.worktree import get_registered_worktrees
            registered = {wt["path"]: wt for wt in get_registered_worktrees()}
            worktree_info = registered.get(str(path), {})
            
            # Remove Git worktree
            git_cmd = ["git", "worktree", "remove"]
            if force:
                git_cmd.append("--force")
            git_cmd.append(str(path))
            
            add_span_event("git.worktree.remove", {"command": " ".join(git_cmd)})
            
            output = run(git_cmd, capture=True, cwd=_get_git_root())
            
            if output is None:
                raise WorktreeError("Failed to remove worktree: Command failed")
            
            # Clean up environment if exists and requested
            env_removed = False
            if cleanup_env and worktree_info.get('environment'):
                env_path = Path(worktree_info['environment'])
                if env_path.exists():
                    shutil.rmtree(env_path)
                    env_removed = True
            
            # Unregister worktree
            from uvmgr.ops.worktree import unregister_worktree
            unregister_worktree(path)
            
            warnings = []
            if not cleanup_env and worktree_info.get('environment'):
                warnings.append(f"Environment not cleaned up: {worktree_info['environment']}")
            
            return {
                "path": path,
                "env_removed": env_removed,
                "warnings": warnings,
            }
            
        except subprocess.CalledProcessError as e:
            record_exception(e)
            raise WorktreeError(f"Git worktree removal failed: {e}") from e
        except Exception as e:
            record_exception(e)
            raise


def switch_to_worktree(
    path: Path,
    activate_env: bool = True,
) -> Dict[str, Any]:
    """Switch to a different worktree."""
    with span("runtime.worktree.switch", path=str(path)):
        try:
            path = Path(path).resolve()
            
            if not path.exists():
                raise WorktreeError(f"Worktree path does not exist: {path}")
            
            if not (path / ".git").exists():
                raise WorktreeError(f"Path is not a Git worktree: {path}")
            
            # Get worktree information
            branch = _get_current_branch(path)
            
            # Update access time
            from uvmgr.ops.worktree import update_worktree_access_time
            update_worktree_access_time(path)
            
            # Get environment information
            from uvmgr.ops.worktree import get_registered_worktrees
            registered = {wt["path"]: wt for wt in get_registered_worktrees()}
            worktree_info = registered.get(str(path), {})
            
            env_activated = False
            env_path = None
            
            if activate_env and worktree_info.get('environment'):
                env_path = Path(worktree_info['environment'])
                if env_path.exists():
                    env_activated = True
            
            instructions = [
                f"cd {path}",
            ]
            
            if env_activated:
                instructions.append(f"source {env_path}/bin/activate")
            
            instructions.extend([
                "# Start your development work",
                "# Use 'uvmgr worktree status' to check worktree info",
            ])
            
            return {
                "path": path,
                "branch": branch,
                "env_activated": env_activated,
                "env_path": env_path,
                "instructions": instructions,
            }
            
        except Exception as e:
            record_exception(e)
            raise


def create_isolated_environment(
    project_path: Path,
    branch: Optional[str] = None,
    name: Optional[str] = None,
    install_uvmgr: bool = True,
    sync_deps: bool = True,
) -> Dict[str, Any]:
    """Create isolated environment for external project development."""
    with span("runtime.worktree.isolate", project_path=str(project_path)):
        try:
            project_path = Path(project_path).resolve()
            
            if not project_path.exists():
                raise WorktreeError(f"Project path does not exist: {project_path}")
            
            # Determine worktree name and path
            if name is None:
                name = f"{project_path.name}-isolated"
            
            # Create temporary directory for isolated development
            isolate_base = Path.home() / ".uvmgr" / "isolated"
            isolate_base.mkdir(parents=True, exist_ok=True)
            
            worktree_path = isolate_base / name
            
            # Remove existing isolated environment
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            
            # Copy project to isolated location
            shutil.copytree(project_path, worktree_path)
            
            # Initialize or configure Git in isolated environment
            current_branch = branch or _detect_default_branch(worktree_path)
            _setup_git_in_isolated_env(worktree_path, current_branch)
            
            # Create virtual environment
            env_path, venv_created = _setup_isolated_environment(worktree_path)
            
            # Install uvmgr in isolated environment
            uvmgr_installed = False
            if install_uvmgr and env_path:
                uvmgr_installed = _install_uvmgr_in_env(env_path)
            
            # Sync project dependencies
            deps_synced = False
            if sync_deps and env_path:
                deps_synced = _sync_project_dependencies(worktree_path, env_path)
            
            # Register isolated environment
            from uvmgr.ops.worktree import register_worktree
            register_worktree(
                path=worktree_path,
                branch=current_branch,
                isolated=True,
                environment=str(env_path) if env_path else None,
            )
            
            return {
                "worktree_path": worktree_path,
                "env_path": env_path,
                "branch": current_branch,
                "uvmgr_installed": uvmgr_installed,
                "deps_synced": deps_synced,
                "venv_created": venv_created,
            }
            
        except Exception as e:
            record_exception(e)
            raise


def cleanup_worktrees(
    dry_run: bool = False,
    force: bool = False,
    max_age_days: int = 30,
    cleanup_envs: bool = True,
) -> Dict[str, Any]:
    """Clean up unused and stale worktrees."""
    with span("runtime.worktree.cleanup"):
        try:
            from uvmgr.ops.worktree import find_stale_worktrees
            
            candidates = find_stale_worktrees(max_age_days)
            cleaned = []
            errors = []
            
            if dry_run:
                return {
                    "candidates": candidates,
                    "cleaned": [],
                    "errors": [],
                    "dry_run": True,
                }
            
            for candidate in candidates:
                try:
                    path = Path(candidate["path"])
                    
                    # Check if it's still a valid worktree
                    if _is_valid_worktree(path):
                        # Remove using Git worktree command
                        remove_result = remove_worktree(
                            path=path,
                            force=force,
                            cleanup_env=cleanup_envs,
                        )
                        cleaned.append({
                            "path": str(path),
                            "age_days": candidate.get("age_days", 0),
                            "env_removed": remove_result.get("env_removed", False),
                        })
                    else:
                        # Just remove from registry if not a valid worktree
                        from uvmgr.ops.worktree import unregister_worktree
                        unregister_worktree(path)
                        cleaned.append({
                            "path": str(path),
                            "age_days": candidate.get("age_days", 0),
                            "registry_only": True,
                        })
                        
                except Exception as e:
                    errors.append(f"Failed to clean {candidate['path']}: {e}")
            
            return {
                "candidates": candidates,
                "cleaned": cleaned,
                "errors": errors,
                "dry_run": False,
            }
            
        except Exception as e:
            record_exception(e)
            raise


def get_worktree_status(
    path: Optional[Path] = None,
    detailed: bool = False,
) -> Dict[str, Any]:
    """Get status of worktrees and isolated environments."""
    with span("runtime.worktree.status"):
        try:
            worktrees = list_worktrees(verbose=detailed, status=True)
            
            total_count = len(worktrees)
            isolated_count = sum(1 for wt in worktrees if wt.get('isolated', False))
            
            # Get current worktree
            current_worktree = "none"
            try:
                cwd = Path.cwd()
                for wt in worktrees:
                    if cwd.is_relative_to(wt['path']):
                        current_worktree = str(wt['path'])
                        break
            except Exception:
                pass
            
            result = {
                "total_count": total_count,
                "isolated_count": isolated_count,
                "current_worktree": current_worktree,
            }
            
            if detailed:
                details = []
                for wt in worktrees:
                    detail = {
                        "path": str(wt['path']),
                        "branch": wt.get('branch', 'unknown'),
                        "status": wt.get('status', 'unknown'),
                        "environment": wt.get('environment'),
                        "last_activity": wt.get('last_accessed'),
                        "isolated": wt.get('isolated', False),
                    }
                    details.append(detail)
                result["details"] = details
            
            if path:
                # Filter for specific path
                path = Path(path).resolve()
                result["details"] = [
                    d for d in result.get("details", [])
                    if Path(d["path"]).resolve() == path
                ]
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


# Helper functions

def _get_git_root() -> Path:
    """Get the root directory of the current Git repository."""
    try:
        output = run(["git", "rev-parse", "--show-toplevel"], capture=True)
        if output is not None:
            return Path(output.strip())
        else:
            raise WorktreeError("Not in a Git repository")
    except subprocess.CalledProcessError:
        raise WorktreeError("Not in a Git repository")


def _setup_isolated_environment(path: Path) -> tuple[Optional[Path], bool]:
    """Set up isolated virtual environment for a worktree."""
    try:
        env_base = Path.home() / ".uvmgr" / "envs"
        env_base.mkdir(parents=True, exist_ok=True)
        
        env_name = f"{path.name}-{path.parent.name}"
        env_path = env_base / env_name
        
        # Remove existing environment
        if env_path.exists():
            shutil.rmtree(env_path)
        
        # Create virtual environment using uv
        output = run(["uv", "venv", str(env_path)], capture=True)
        
        if output is not None:
            return env_path, True
        else:
            # Fall back to python -m venv
            output = run(["python", "-m", "venv", str(env_path)], capture=True)
            return (env_path, True) if output is not None else (None, False)
            
    except Exception:
        return None, False


def _get_worktree_git_status(path: Path) -> Dict[str, Any]:
    """Get Git status for a worktree."""
    try:
        output = run(["git", "status", "--porcelain"], capture=True, cwd=path)
        
        if output is not None:
            lines = [line for line in output.split('\n') if line.strip()]
            status = "clean" if not lines else "dirty"
            return {
                "status": status,
                "files_changed": len(lines),
            }
        else:
            return {"status": "error", "files_changed": 0}
            
    except Exception:
        return {"status": "unknown", "files_changed": 0}


def _get_last_commit(path: Path) -> str:
    """Get the last commit message for a worktree."""
    try:
        output = run(["git", "log", "-1", "--pretty=format:%h %s"], capture=True, cwd=path)
        return output.strip() if output is not None else ""
    except Exception:
        return ""


def _get_current_branch(path: Path) -> str:
    """Get the current branch for a worktree."""
    try:
        output = run(["git", "branch", "--show-current"], capture=True, cwd=path)
        return output.strip() if output is not None else "unknown"
    except Exception:
        return "unknown"


def _detect_default_branch(path: Path) -> str:
    """Detect the default branch for a project."""
    # Common default branch names
    default_branches = ["main", "master", "develop", "dev"]
    
    for branch in default_branches:
        try:
            output = run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], capture=True, cwd=path)
            if output is not None:
                return branch
        except Exception:
            continue
    
    # Fall back to current branch
    return _get_current_branch(path)


def _setup_git_in_isolated_env(path: Path, branch: str) -> None:
    """Set up Git configuration in isolated environment."""
    try:
        # Initialize Git if not already a repo
        if not (path / ".git").exists():
            run(["git", "init"], cwd=path)
        
        # Create and checkout the specified branch
        run(["git", "checkout", "-B", branch], cwd=path)
        
        # Set up basic Git config if needed
        output = run(["git", "config", "user.email"], capture=True, cwd=path)
        if output is None:
            run(["git", "config", "user.email", "uvmgr@isolated.local"], cwd=path)
            run(["git", "config", "user.name", "uvmgr-isolated"], cwd=path)
        
    except Exception as e:
        # Git setup is optional, don't fail if it doesn't work
        pass


def _install_uvmgr_in_env(env_path: Path) -> bool:
    """Install uvmgr in an isolated environment."""
    try:
        pip_path = env_path / "bin" / "pip"
        if not pip_path.exists():
            pip_path = env_path / "Scripts" / "pip.exe"  # Windows
        
        if pip_path.exists():
            # Try to install uvmgr from PyPI
            output = run([str(pip_path), "install", "uvmgr"], capture=True)
            return output is not None
        
        return False
        
    except Exception:
        return False


def _sync_project_dependencies(project_path: Path, env_path: Path) -> bool:
    """Sync project dependencies in isolated environment."""
    try:
        pip_path = env_path / "bin" / "pip"
        if not pip_path.exists():
            pip_path = env_path / "Scripts" / "pip.exe"  # Windows
        
        if not pip_path.exists():
            return False
        
        # Look for common dependency files
        dep_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
        ]
        
        for dep_file in dep_files:
            dep_path = project_path / dep_file
            if dep_path.exists():
                if dep_file == "requirements.txt":
                    output = run([str(pip_path), "install", "-r", str(dep_path)], capture=True)
                elif dep_file == "pyproject.toml":
                    output = run([str(pip_path), "install", "-e", str(project_path)], capture=True)
                elif dep_file == "setup.py":
                    output = run([str(pip_path), "install", "-e", str(project_path)], capture=True)
                else:
                    continue
                
                return output is not None
        
        return False
        
    except Exception:
        return False


def _is_valid_worktree(path: Path) -> bool:
    """Check if a path is a valid Git worktree."""
    try:
        if not path.exists():
            return False
        
        output = run(["git", "worktree", "list"], capture=True, cwd=_get_git_root())
        if output is not None:
            worktree_paths = []
            for line in output.split('\n'):
                if line.strip():
                    # Extract path from worktree list output
                    parts = line.split()
                    if parts:
                        worktree_paths.append(Path(parts[0]))
            
            return path.resolve() in [p.resolve() for p in worktree_paths]
        
        return False
        
    except Exception:
        return False