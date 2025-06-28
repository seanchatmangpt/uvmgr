"""
uvmgr.runtime.mcp
=================

Runtime operations for MCP functionality.

This module handles the actual execution and side effects for MCP operations,
such as running servers, installing FastMCP, and managing MCP processes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from uvmgr.core.process import run_logged
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def ensure_fastmcp_installed() -> bool:
    """
    Check if FastMCP is installed, return True if available.

    Returns
    -------
    bool
        True if FastMCP is installed, False otherwise
    """
    with span("mcp.check_installed"):
        try:
            import fastmcp

            return True
        except ImportError:
            return False


def install_fastmcp() -> None:
    """
    Install FastMCP using uv pip install.

    Raises
    ------
    subprocess.CalledProcessError
        If installation fails
    """
    with span("mcp.install_fastmcp"):
        colour("Installing FastMCP...", "yellow")
        run_logged(["uv", "pip", "install", "fastmcp"])
        colour("✅ FastMCP installed successfully", "green")


def run_mcp_server(
    server_path: Path,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    auth_token: str | None = None,
) -> None:
    """
    Run an MCP server with specified transport.

    Parameters
    ----------
    server_path : Path
        Path to the MCP server Python file
    transport : str
        Transport type (stdio, sse, http)
    host : str
        Host address for network transports
    port : int
        Port number for network transports
    auth_token : str, optional
        Authentication token if required

    Raises
    ------
    subprocess.CalledProcessError
        If server fails to start
    """
    with span("mcp.run_server", transport=transport):
        cmd = ["python", str(server_path)]

        # Add transport-specific environment variables
        env = {}
        if transport == "sse":
            env["MCP_TRANSPORT"] = "sse"
            env["MCP_HOST"] = host
            env["MCP_PORT"] = str(port)
        elif transport == "http":
            env["MCP_TRANSPORT"] = "streamable-http"
            env["MCP_HOST"] = host
            env["MCP_PORT"] = str(port)

        if auth_token:
            env["MCP_AUTH_TOKEN"] = auth_token

        # Run the server
        if env:
            import os

            full_env = os.environ.copy()
            full_env.update(env)
            subprocess.run(cmd, env=full_env, check=True)
        else:
            subprocess.run(cmd, check=True)


def test_mcp_server(server_path: Path) -> dict[str, Any]:
    """
    Test an MCP server by running it and checking basic functionality.

    Parameters
    ----------
    server_path : Path
        Path to the MCP server to test

    Returns
    -------
    dict
        Test results including success status and any errors
    """
    with span("mcp.test_server", path=str(server_path)):
        try:
            # Try to import and validate the server
            import importlib.util

            spec = importlib.util.spec_from_file_location("test_server", server_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check for mcp object
                if hasattr(module, "mcp"):
                    return {
                        "success": True,
                        "message": "Server imports successfully",
                        "has_mcp": True,
                    }
                return {
                    "success": False,
                    "message": "No 'mcp' object found in server",
                    "has_mcp": False,
                }
            return {"success": False, "message": "Failed to load server module", "has_mcp": False}

        except Exception as e:
            return {"success": False, "message": f"Error testing server: {e}", "has_mcp": False}


def generate_server_template(name: str, include_examples: bool = True) -> str:
    """
    Generate a basic MCP server template.

    Parameters
    ----------
    name : str
        Name for the server
    include_examples : bool
        Whether to include example tools/resources

    Returns
    -------
    str
        Python code for a basic MCP server
    """
    with span("mcp.generate_template", name=name, include_examples=include_examples):
        template = f'''#!/usr/bin/env python
"""
{name} MCP Server

A FastMCP server for {name} functionality.
"""

from fastmcp import FastMCP, Context

mcp = FastMCP("{name}")
'''

    if include_examples:
        template += '''

# Example tool
@mcp.tool()
async def hello(name: str, ctx: Context) -> str:
    """
    Say hello to someone.

    Parameters:
    - name: The person's name
    - ctx: MCP context
    """
    await ctx.info(f"Saying hello to {name}")
    return f"Hello, {name}!"
'''
        template += '''

# Example resource
@mcp.resource("info://version")
async def get_version() -> str:
    """Get server version."""
    return "1.0.0"


# Example prompt
@mcp.prompt("greeting")
async def greeting_prompt(name: str) -> str:
    """Generate a greeting prompt."""
    return f"Please write a friendly greeting for {name}"
'''

    template += """

if __name__ == "__main__":
    mcp.run()
"""

    return template
