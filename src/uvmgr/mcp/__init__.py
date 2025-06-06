"""
uvmgr MCP Package - Model Context Protocol interface for uvmgr.

This package provides an MCP server that exposes uvmgr functionality to AI
assistants like Claude. It acts as a translation layer between the MCP
protocol and uvmgr's existing operations.
"""

from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult
from uvmgr.mcp.resources import (
    get_project_info,
    get_project_structure,
    list_dependencies,
    read_project_file,
    debug_test_prompt,
    review_code_prompt,
    architect_feature_prompt,
)
from uvmgr.mcp.tools import (
    create_project,
    analyze_project,
    add_dependency,
    remove_dependency,
    upgrade_dependencies,
    run_script,
    run_command,
    run_tests,
    run_coverage,
    lint_code,
    build_package,
    bump_version,
    generate_changelog,
    search_code,
    create_file,
    ai_fix_tests,
    ai_explain_code,
)

__all__ = [
    # Server
    'mcp',
    'OperationResult',
    
    # Resources
    'get_project_info',
    'get_project_structure',
    'list_dependencies',
    'read_project_file',
    'debug_test_prompt',
    'review_code_prompt',
    'architect_feature_prompt',
    
    # Tools
    'create_project',
    'analyze_project',
    'add_dependency',
    'remove_dependency',
    'upgrade_dependencies',
    'run_script',
    'run_command',
    'run_tests',
    'run_coverage',
    'lint_code',
    'build_package',
    'bump_version',
    'generate_changelog',
    'search_code',
    'create_file',
    'ai_fix_tests',
    'ai_explain_code',
] 