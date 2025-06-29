"""
Dependency management runtime implementation.

This module handles the actual execution of dependency management operations
using the uv package manager. It manages subprocess calls for adding, removing,
upgrading, and listing dependencies.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import span
from uvmgr.core.process import run_logged


def add_packages(
    packages: List[str],
    dev: bool = False,
    extras: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add packages to the project dependencies using uv.
    
    Parameters
    ----------
    packages : List[str]
        List of package specifications to add
    dev : bool
        Whether to add as development dependencies
    extras : Optional[List[str]]
        Optional extras to install
        
    Returns
    -------
    Dict[str, Any]
        Operation results including success status and output
    """
    with span("runtime.deps.add"):
        cmd = ["uv", "add"]
        
        if dev:
            cmd.extend(["--dev"])
            
        cmd.extend(packages)
        
        if extras:
            for extra in extras:
                cmd.extend(["--extra", extra])
                
        try:
            result = run_logged(cmd)
            return {
                "success": True,
                "packages": packages,
                "dev": dev,
                "message": f"Successfully added {', '.join(packages)}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "packages": packages,
                "error": str(e),
                "output": e.output if hasattr(e, 'output') else None
            }


def remove_packages(packages: List[str]) -> Dict[str, Any]:
    """
    Remove packages from the project dependencies using uv.
    
    Parameters
    ----------
    packages : List[str]
        List of package names to remove
        
    Returns
    -------
    Dict[str, Any]
        Operation results
    """
    with span("runtime.deps.remove"):
        cmd = ["uv", "remove"]
        cmd.extend(packages)
        
        try:
            result = run_logged(cmd)
            return {
                "success": True,
                "packages": packages,
                "message": f"Successfully removed {', '.join(packages)}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "packages": packages,
                "error": str(e),
                "output": e.output if hasattr(e, 'output') else None
            }


def upgrade_packages(
    all_packages: bool = False,
    packages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Upgrade packages to their latest versions using uv.
    
    Parameters
    ----------
    all_packages : bool
        Whether to upgrade all packages
    packages : Optional[List[str]]
        Specific packages to upgrade
        
    Returns
    -------
    Dict[str, Any]
        Operation results
    """
    with span("runtime.deps.upgrade"):
        # uv doesn't have a direct upgrade command, so we use sync with --upgrade
        cmd = ["uv", "sync"]
        
        if all_packages:
            cmd.append("--upgrade")
        elif packages:
            # For specific packages, we need to re-add them to get latest versions
            # This is a workaround until uv has proper upgrade support
            results = []
            for pkg in packages:
                try:
                    # Remove and re-add to get latest version
                    remove_result = remove_packages([pkg])
                    if remove_result["success"]:
                        add_result = add_packages([pkg])
                        results.append({
                            "package": pkg,
                            "success": add_result["success"]
                        })
                    else:
                        results.append({
                            "package": pkg,
                            "success": False,
                            "error": "Failed to remove package"
                        })
                except Exception as e:
                    results.append({
                        "package": pkg,
                        "success": False,
                        "error": str(e)
                    })
                    
            success = all(r["success"] for r in results)
            return {
                "success": success,
                "packages": packages,
                "results": results,
                "message": "Upgrade completed" if success else "Some upgrades failed"
            }
        else:
            # Just sync without upgrade
            pass
            
        try:
            result = run_logged(cmd)
            return {
                "success": True,
                "all_packages": all_packages,
                "message": "Successfully upgraded dependencies"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "output": e.output if hasattr(e, 'output') else None
            }


def list_packages() -> List[str]:
    """
    List installed packages in the current project.
    
    Returns
    -------
    List[str]
        List of installed package specifications
    """
    with span("runtime.deps.list"):
        try:
            # Use uv pip list in the project environment
            result = subprocess.run(
                ["uv", "pip", "list", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            packages = json.loads(result.stdout)
            # Format as name==version
            return [f"{pkg['name']}=={pkg['version']}" for pkg in packages]
            
        except subprocess.CalledProcessError:
            # Fallback to reading from pyproject.toml if pip list fails
            return _list_from_pyproject()
        except json.JSONDecodeError:
            return _list_from_pyproject()


def _list_from_pyproject() -> List[str]:
    """
    Fallback method to list dependencies from pyproject.toml.
    
    Returns
    -------
    List[str]
        List of dependency specifications from pyproject.toml
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
        
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return []
        
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            
        deps = []
        
        # Get main dependencies
        if "project" in data and "dependencies" in data["project"]:
            deps.extend(data["project"]["dependencies"])
            
        # Get dev dependencies from dependency-groups
        if "dependency-groups" in data:
            for group_name, group_deps in data["dependency-groups"].items():
                if isinstance(group_deps, list):
                    deps.extend(f"{dep} (group: {group_name})" for dep in group_deps)
                    
        return deps
        
    except Exception:
        return []


def lock_dependencies(verbose: bool = False) -> Dict[str, Any]:
    """
    Generate or update the lock file.
    
    Parameters
    ----------
    verbose : bool
        Whether to show verbose output
        
    Returns
    -------
    Dict[str, Any]
        Lock operation results
    """
    with span("runtime.deps.lock"):
        cmd = ["uv", "lock"]
        
        if verbose:
            cmd.append("--verbose")
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "success": True,
                "message": "Dependencies locked successfully",
                "output": result.stdout if verbose else None
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "output": e.stderr if e.stderr else e.stdout
            }


def sync_dependencies(frozen: bool = False) -> Dict[str, Any]:
    """
    Sync dependencies from lock file.
    
    Parameters
    ----------
    frozen : bool
        Whether to use frozen (exact) versions
        
    Returns
    -------
    Dict[str, Any]
        Sync operation results
    """
    with span("runtime.deps.sync"):
        cmd = ["uv", "sync"]
        
        if frozen:
            cmd.append("--frozen")
            
        try:
            result = run_logged(cmd)
            return {
                "success": True,
                "message": "Dependencies synced successfully"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "output": e.output if hasattr(e, 'output') else None
            }