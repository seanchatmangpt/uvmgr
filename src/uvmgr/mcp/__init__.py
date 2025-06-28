"""
uvmgr MCP Package - Model Context Protocol interface for uvmgr.

This package provides an MCP (Model Context Protocol) server that exposes uvmgr
functionality to AI assistants like Claude. It acts as a translation layer
between the MCP protocol and uvmgr's existing operations, enabling AI assistants
to interact with Python projects through a standardized interface.

Package Features
---------------
• **MCP Server**: Full MCP protocol implementation with multiple transport methods
• **Tools**: Commands that AI assistants can execute on your behalf
• **Resources**: Read-only access to project files and information
• **Prompts**: Pre-defined prompts for common development tasks
• **Multiple Transports**: stdio, SSE, and HTTP protocol support
• **Authentication**: Secure authentication for production deployments

Available Components
-------------------
Server
- mcp : Main MCP server instance
- OperationResult : Standardized operation result format

Resources
- get_project_info : Get project metadata and configuration
- get_project_structure : Get project file and directory structure
- list_dependencies : List project dependencies
- read_project_file : Read contents of project files
- debug_test_failure : Analyze and debug test failures
- review_code_quality : Review code quality and suggest improvements
- architect_feature : Help architect new features

Tools
- create_project : Create new Python projects
- analyze_project : Analyze project structure and dependencies
- add_dependency : Add packages to project
- remove_dependency : Remove packages from project
- upgrade_dependencies : Upgrade project dependencies
- run_script : Execute Python scripts
- run_command : Execute shell commands
- run_tests : Run test suite
- run_coverage : Generate coverage reports
- lint_code : Run code linting and formatting
- build_package : Build distribution packages
- bump_version : Bump project version
- generate_changelog : Generate changelog
- search_code : Search code for patterns
- create_file : Create new files
- ai_fix_tests : Use AI to fix failing tests
- ai_explain_code : Use AI to explain code

Example
-------
    >>> from uvmgr.mcp import mcp
    >>> # Start MCP server
    >>> mcp.run(transport="stdio")
    
    >>> # Use tools programmatically
    >>> from uvmgr.mcp import create_project, add_dependency
    >>> result = create_project("my-project", template="basic")

See Also
--------
- :mod:`uvmgr.mcp.server` : MCP server implementation
- :mod:`uvmgr.mcp.tools` : MCP tools implementation
- :mod:`uvmgr.mcp.resources` : MCP resources implementation
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
