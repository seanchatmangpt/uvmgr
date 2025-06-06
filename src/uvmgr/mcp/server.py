"""
uvmgr MCP Server - Model Context Protocol interface for uvmgr.

This module provides the main MCP server setup that exposes uvmgr functionality
to AI assistants like Claude. It acts as a translation layer between the MCP
protocol and uvmgr's existing operations.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from fastmcp import FastMCP, Context
except ImportError:
    raise ImportError(
        "FastMCP is required for MCP server functionality. "
        "Install with: pip install 'uvmgr[mcp]' or 'pip install fastmcp'"
    )

from uvmgr.core import paths
from uvmgr.mcp._mcp_instance import mcp

# Import all tools and resources
from uvmgr.mcp.resources import (
    get_project_info,
    get_project_structure,
    list_dependencies,
    read_project_file,
    debug_test_prompt,
    review_code_prompt,
    architect_feature_prompt,
)

from uvmgr.mcp.tools.project import (
    create_project,
    analyze_project,
)

from uvmgr.mcp.tools.deps import (
    add_dependency,
    remove_dependency,
    upgrade_dependencies,
)

from uvmgr.mcp.tools.exec import (
    run_script,
    run_command,
)

from uvmgr.mcp.tools.test import (
    run_tests,
    run_coverage,
    lint_code,
)

from uvmgr.mcp.tools.build import (
    build_package,
    bump_version,
    generate_changelog,
)

from uvmgr.mcp.tools.files import (
    search_code,
    create_file,
)

from uvmgr.mcp.tools.ai import (
    ai_fix_tests,
    ai_explain_code,
)

# -----------------------------------------------------------------------------
# Helper Classes
# -----------------------------------------------------------------------------

@dataclass
class OperationResult:
    """Standardized result format for MCP operations."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    
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