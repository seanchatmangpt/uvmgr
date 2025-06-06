"""
Testing Tools - Tools for running tests and code quality checks.

This module provides tools for running the test suite, generating coverage
reports, and performing code linting.
"""

from pathlib import Path

from fastmcp import FastMCP, Context
from uvmgr.core import process
from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult

# -----------------------------------------------------------------------------
# Testing Tools
# -----------------------------------------------------------------------------

@mcp.tool()
async def run_tests(
    ctx: Context,
    verbose: bool = False,
) -> str:
    """
    Run project test suite with pytest.
    
    Parameters:
    - ctx: MCP context
    - verbose: If True, show detailed output
    """
    try:
        await ctx.info("Running test suite...")
        
        # Run tests using pytest
        cmd = ["pytest"]
        if verbose:
            cmd.append("-v")
        
        result = process.run(cmd, capture=True)
        
        # Parse test results
        success = "failed" not in (result or "").lower()
        
        return OperationResult(
            success=success,
            message="Tests completed" if success else "Tests failed",
            details={
                "verbose": verbose,
                "output": result if result else "No test output"
            }
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to run tests",
            details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def run_coverage(ctx: Context) -> str:
    """
    Generate test coverage report.
    
    Parameters:
    - ctx: MCP context
    """
    try:
        await ctx.info("Running coverage analysis...")
        
        # Run coverage
        process.run(["coverage", "run", "-m", "pytest"], capture=True)
        report = process.run(["coverage", "report"], capture=True)
        
        return OperationResult(
            success=True,
            message="Coverage report generated",
            details={"report": report if report else "No coverage data"}
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to run coverage",
            details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def lint_code(
    ctx: Context,
    path: str = ".",
    fix: bool = False,
) -> str:
    """
    Run linting on project code with ruff.
    
    Parameters:
    - ctx: MCP context
    - path: Path to lint (default: current directory)
    - fix: If True, automatically fix issues
    """
    try:
        await ctx.info(f"Linting code at: {path}")        
        cmd = ["ruff", "check", path]
        if fix:
            cmd.append("--fix")
        
        result = process.run(cmd, capture=True)
        success = result is not None and "error" not in result.lower()
        
        return OperationResult(
            success=success,
            message="Linting completed" if success else "Linting found issues",
            details={
                "path": path,
                "fix": fix,
                "output": result if result else "No linting issues found"
            }
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to run linting",
            details={"error": str(e), "path": path}
        ).to_string() 