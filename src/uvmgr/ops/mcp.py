"""
uvmgr.ops.mcp
=============

MCP-specific orchestration operations.

This module provides orchestration functions specific to MCP server functionality,
such as server validation, tool extraction, and MCP-specific operations that
don't fit into other ops modules.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span


@timed
def validate_mcp_server(server_path: Path) -> dict[str, Any]:
    """
    Validate an MCP server file for correctness.

    Parameters
    ----------
    server_path : Path
        Path to the MCP server Python file

    Returns
    -------
    dict
        Validation results including tools, resources, prompts found
    """
    with span("mcp.validate_server", path=str(server_path)):
        if not server_path.exists():
            return {"valid": False, "error": "File not found"}

        try:
            content = server_path.read_text()
            tree = ast.parse(content)

            # Look for FastMCP import and decorators
            has_fastmcp_import = False
            tools = []
            resources = []
            prompts = []
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.ImportFrom) and node.module == "fastmcp":
                    has_fastmcp_import = True

                # Check for decorated functions
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        decorator_name = (
                            ast.unparse(decorator) if hasattr(ast, "unparse") else str(decorator)
                        )
                        if "mcp.tool" in decorator_name:
                            tools.append(node.name)
                        elif "mcp.resource" in decorator_name:
                            resources.append(node.name)
                        elif "mcp.prompt" in decorator_name:
                            prompts.append(node.name)

            return {
                "valid": has_fastmcp_import,
                "tools": tools,
                "resources": resources,
                "prompts": prompts,
                "has_fastmcp": has_fastmcp_import,
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}


@timed
def list_mcp_servers(root_path: Path = Path(".")) -> list[dict[str, Any]]:
    """
    Find all MCP servers in a project.

    Parameters
    ----------
    root_path : Path
        Root directory to search

    Returns
    -------
    list
        List of MCP server info dictionaries
    """
    with span("mcp.list_servers", root=str(root_path)):
        servers = []
        for py_file in root_path.rglob("*.py"):
            if any(part.startswith(".") for part in py_file.parts):
                continue
            if any(part in ["__pycache__", ".venv", "venv"] for part in py_file.parts):
                continue

            try:
                content = py_file.read_text()
                if "from fastmcp import" in content or "import fastmcp" in content:
                    info = validate_mcp_server(py_file)
                    if info["valid"]:
                        servers.append(
                            {
                                "path": str(py_file),
                                "tools": info["tools"],
                                "resources": info["resources"],
                                "prompts": info["prompts"],
                            }
                        )
            except:
                continue

        return servers


@timed
def generate_mcp_client_code(server_name: str, transport: str = "stdio") -> str:
    """
    Generate example client code for connecting to an MCP server.

    Parameters
    ----------
    server_name : str
        Name of the server to connect to
    transport : str
        Transport type (stdio, sse, http)

    Returns
    -------
    str
        Python code for connecting to the server
    """
    with span("mcp.generate_client", server=server_name, transport=transport):
        if transport == "stdio":
            template = f"""
from fastmcp import Client
import asyncio

async def main():
    # Connect to {server_name} via stdio
    async with Client("{server_name}.py") as client:        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {{tools}}")

        # Example: Call a tool
        # result = await client.call_tool("tool_name", {{"param": "value"}})
        # print(f"Result: {{result.text}}")

if __name__ == "__main__":
    asyncio.run(main())
"""
        elif transport == "sse":
            template = f"""
from fastmcp import Client
import asyncio

async def main():
    # Connect to {server_name} via SSE
    async with Client("http://localhost:8000/sse") as client:
        tools = await client.list_tools()
        print(f"Available tools: {{tools}}")

if __name__ == "__main__":
    asyncio.run(main())
"""
        else:  # http
            template = f"""
from fastmcp import Client
import asyncio

async def main():
    # Connect to {server_name} via HTTP
    async with Client("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()
        print(f"Available tools: {{tools}}")

if __name__ == "__main__":
    asyncio.run(main())
"""

        return template.strip()
