"""
uvmgr MCP Server - Model Context Protocol interface for uvmgr.

This module provides the main MCP server setup that exposes uvmgr functionality
to AI assistants like Claude. It acts as a translation layer between the MCP
protocol and uvmgr's existing operations.
"""

from dataclasses import dataclass
from typing import Any

try:
    from fastmcp import Context, FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required for MCP server functionality. "
        "Install with: pip install 'uvmgr[mcp]' or 'pip install fastmcp'"
    )

from uvmgr.mcp._mcp_instance import mcp

# Note: Tool and resource imports are handled by the individual modules
# They register themselves with the mcp instance when imported

# -----------------------------------------------------------------------------
# Helper Classes
# -----------------------------------------------------------------------------


@dataclass
class OperationResult:
    """Standardized result format for MCP operations."""

    success: bool
    message: str
    details: dict[str, Any] | None = None

    def to_string(self) -> str:
        """Format result for LLM consumption."""
        result = f"{'✅' if self.success else '❌'} {self.message}"
        if self.details:
            result += "\n" + "\n".join(f"  {k}: {v}" for k, v in self.details.items())
        return result


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # This allows testing the server directly
    mcp.run()
