"""
uvmgr.mcp._mcp_instance – Dedicated module for the FastMCP instance.

This module creates and exports the FastMCP instance (mcp) so that other modules (like server.py and __init__.py) import it from here, breaking circular imports.
"""

from fastmcp import FastMCP

mcp = FastMCP("uvmgr-mcp", description="Python project management via Model Context Protocol", dependencies=["uv", "pytest", "build", "twine", "ruff"]) 