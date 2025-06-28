"""
uvmgr MCP Package - Model Context Protocol interface for uvmgr.

This package provides an MCP server that exposes uvmgr functionality to AI
assistants like Claude. It acts as a translation layer between the MCP
protocol and uvmgr's existing operations.
"""

from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.resources import (
    architect_feature,
    debug_test_failure,
    get_project_info,
    get_project_structure,
    list_dependencies,
    read_project_file,
    review_code_quality,
)
from uvmgr.mcp.server import OperationResult
from uvmgr.mcp.tools import (
    add_dependency,
    ai_explain_code,
    ai_fix_tests,
    analyze_project,
    build_package,
    bump_version,
    create_file,
    create_project,
    generate_changelog,
    lint_code,
    remove_dependency,
    run_command,
    run_coverage,
    run_script,
    run_tests,
    search_code,
    upgrade_dependencies,
)

__all__ = [
    # Server
    "mcp",
    "OperationResult",
    # Resources
    "get_project_info",
    "get_project_structure",
    "list_dependencies",
    "read_project_file",
    "debug_test_failure",
    "review_code_quality",
    "architect_feature",
    # Tools
    "create_project",
    "analyze_project",
    "add_dependency",
    "remove_dependency",
    "upgrade_dependencies",
    "run_script",
    "run_command",
    "run_tests",
    "run_coverage",
    "lint_code",
    "build_package",
    "bump_version",
    "generate_changelog",
    "search_code",
    "create_file",
    "ai_fix_tests",
    "ai_explain_code",
]
