"""
Linting operations for code quality management.

This module provides the business logic layer for linting operations,
coordinating between commands and runtime execution. It follows the
80/20 principle by focusing on the most impactful linting operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.runtime import lint as lint_runtime


def check_code(
    path: Path | None = None,
    fix: bool = False,
    show_fixes: bool = False
) -> Dict[str, Any]:
    """
    Run linting checks on code.
    
    Parameters
    ----------
    path : Path | None
        Path to check (None for current directory)
    fix : bool
        Whether to automatically fix violations
    show_fixes : bool
        Whether to show what would be fixed without applying
        
    Returns
    -------
    Dict[str, Any]
        Linting results including status and any violations found
    """
    with span("lint.check") as current_span:
        add_span_attributes(**{
            "lint.operation": "check",
            "lint.tool": "ruff",
            "lint.path": str(path) if path else ".",
            "lint.fix": fix,
            "lint.show_fixes": show_fixes,
        })
        
        # Delegate to runtime
        result = lint_runtime.run_ruff_check(
            path=path,
            fix=fix,
            show_fixes=show_fixes
        )
        
        # Add result attributes
        add_span_attributes(**{
            "lint.check.success": result["success"],
            "lint.check.exit_code": result.get("exit_code", 0),
        })
        
        return result


def format_code(
    path: Path | None = None,
    check_only: bool = False
) -> Dict[str, Any]:
    """
    Format code using Ruff formatter.
    
    Parameters
    ----------
    path : Path | None
        Path to format (None for current directory)
    check_only : bool
        Whether to only check formatting without applying changes
        
    Returns
    -------
    Dict[str, Any]
        Formatting results
    """
    with span("lint.format") as current_span:
        add_span_attributes(**{
            "lint.operation": "format",
            "lint.tool": "ruff",
            "lint.path": str(path) if path else ".",
            "lint.check_only": check_only,
        })
        
        # Delegate to runtime
        result = lint_runtime.run_ruff_format(
            path=path,
            check_only=check_only
        )
        
        # Add result attributes
        add_span_attributes(**{
            "lint.format.success": result["success"],
            "lint.format.exit_code": result.get("exit_code", 0),
        })
        
        return result


def fix_all(path: Path | None = None) -> Dict[str, Any]:
    """
    Fix all auto-fixable linting and formatting issues.
    
    This runs both formatting and linting fixes in the proper order.
    
    Parameters
    ----------
    path : Path | None
        Path to fix (None for current directory)
        
    Returns
    -------
    Dict[str, Any]
        Combined results from formatting and fixing
    """
    with span("lint.fix_all") as current_span:
        add_span_attributes(**{
            "lint.operation": "fix_all",
            "lint.tool": "ruff",
            "lint.path": str(path) if path else ".",
        })
        
        # First format the code
        format_result = lint_runtime.run_ruff_format(path=path, check_only=False)
        
        if not format_result["success"]:
            return {
                "success": False,
                "format_result": format_result,
                "message": "Formatting failed"
            }
        
        # Then fix linting issues
        fix_result = lint_runtime.run_ruff_check(path=path, fix=True, show_fixes=False)
        
        # Combine results
        result = {
            "success": format_result["success"] and fix_result["success"],
            "format_result": format_result,
            "fix_result": fix_result,
            "message": "All issues fixed successfully" if fix_result["success"] else "Some issues could not be fixed automatically"
        }
        
        add_span_attributes(**{
            "lint.fix_all.success": result["success"],
        })
        
        return result