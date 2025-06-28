"""
Execution Tools - Tools for running Python scripts and shell commands.

This module provides tools for executing Python scripts and shell commands
in the project environment.
"""

from pathlib import Path

from fastmcp import Context

from uvmgr.core import process
from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult
from uvmgr.ops import exec as exec_ops

# -----------------------------------------------------------------------------
# Execution Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def run_script(
    ctx: Context,
    script_path: str,
    args: list[str] | None = None,
) -> str:
    """
    Execute a Python script in the project environment.

    Parameters
    ----------
    - ctx: MCP context
    - script_path: Path to the Python script
    - args: Command-line arguments for the script
    """
    try:
        await ctx.info(f"Running script: {script_path}")

        script = Path(script_path)
        if not script.exists():
            return OperationResult(
                success=False, message="Script not found", details={"path": script_path}
            ).to_string()

        exec_ops.script(path=script, argv=args or [])
        return OperationResult(
            success=True, message=f"Script executed: {script_path}", details={"args": args}
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to run script",
            details={"error": str(e), "script": script_path},
        ).to_string()


@mcp.tool()
async def run_command(
    ctx: Context,
    command: str,
) -> str:
    """
    Run a shell command in the project environment.

    Parameters
    ----------
    - ctx: MCP context
    - command: Shell command to execute
    """
    try:
        await ctx.info(f"Running command: {command}")

        result = process.run(command, capture=True)

        return OperationResult(
            success=True,
            message="Command executed",
            details={"command": command, "output": result if result else "No output"},
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Command failed", details={"error": str(e), "command": command}
        ).to_string()
