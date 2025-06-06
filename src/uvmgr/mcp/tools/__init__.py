"""
MCP Tools Package - Collection of tools for the MCP server.

This package contains various tools organized by functionality:
- project: Project creation and analysis
- deps: Dependency management
- exec: Script and command execution
- test: Testing and code quality
- build: Package building and versioning
- files: File operations
- ai: AI-assisted development
"""

from uvmgr.mcp.tools.project import create_project, analyze_project
from uvmgr.mcp.tools.deps import add_dependency, remove_dependency, upgrade_dependencies
from uvmgr.mcp.tools.exec import run_script, run_command
from uvmgr.mcp.tools.test import run_tests, run_coverage, lint_code
from uvmgr.mcp.tools.build import build_package, bump_version, generate_changelog
from uvmgr.mcp.tools.files import search_code, create_file
from uvmgr.mcp.tools.ai import ai_fix_tests, ai_explain_code

__all__ = [
    # Project tools
    'create_project',
    'analyze_project',
    
    # Dependency tools
    'add_dependency',
    'remove_dependency',
    'upgrade_dependencies',
    
    # Execution tools
    'run_script',
    'run_command',
    
    # Testing tools
    'run_tests',
    'run_coverage',
    'lint_code',
    
    # Build tools
    'build_package',
    'bump_version',
    'generate_changelog',
    
    # File tools
    'search_code',
    'create_file',
    
    # AI tools
    'ai_fix_tests',
    'ai_explain_code',
] 