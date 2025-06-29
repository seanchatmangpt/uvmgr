"""
Linting runtime implementation.

This module handles the actual execution of linting tools (Ruff)
at the runtime layer. It manages subprocess calls and file I/O
operations for code quality checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from uvmgr.core.instrumentation import span
from uvmgr.core.process import run_logged


def run_ruff_check(
    path: Path | None = None,
    fix: bool = False,
    show_fixes: bool = False
) -> Dict[str, Any]:
    """
    Execute Ruff linting check.
    
    Parameters
    ----------
    path : Path | None
        Path to check (None for current directory)
    fix : bool
        Whether to automatically fix violations
    show_fixes : bool
        Whether to show what would be fixed
        
    Returns
    -------
    Dict[str, Any]
        Execution results with status and output
    """
    with span("runtime.ruff.check"):
        cmd = ["ruff", "check"]
        
        if fix:
            cmd.append("--fix")
        if show_fixes:
            cmd.append("--show-fixes")
            
        if path:
            cmd.append(str(path))
        else:
            cmd.append(".")
            
        try:
            run_logged(cmd)
            return {
                "success": True,
                "exit_code": 0,
                "message": "No Ruff violations found"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "exit_code": e.returncode,
                "message": "Ruff violations found",
                "output": e.output if hasattr(e, 'output') else None
            }


def run_ruff_format(
    path: Path | None = None,
    check_only: bool = False
) -> Dict[str, Any]:
    """
    Execute Ruff formatter.
    
    Parameters
    ----------
    path : Path | None
        Path to format (None for current directory)
    check_only : bool
        Whether to only check formatting without applying
        
    Returns
    -------
    Dict[str, Any]
        Execution results with status and output
    """
    with span("runtime.ruff.format"):
        cmd = ["ruff", "format"]
        
        if check_only:
            cmd.append("--check")
            
        if path:
            cmd.append(str(path))
        else:
            cmd.append(".")
            
        try:
            run_logged(cmd)
            return {
                "success": True,
                "exit_code": 0,
                "message": "Code formatted successfully" if not check_only else "Code is properly formatted"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "exit_code": e.returncode,
                "message": "Formatting issues found" if check_only else "Formatting failed",
                "output": e.output if hasattr(e, 'output') else None
            }


def get_ruff_version() -> str:
    """
    Get the installed Ruff version.
    
    Returns
    -------
    str
        Ruff version string
    """
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def is_ruff_available() -> bool:
    """
    Check if Ruff is available in the environment.
    
    Returns
    -------
    bool
        True if Ruff is available, False otherwise
    """
    try:
        subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False