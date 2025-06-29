"""
uvmgr.commands.mcp - MCP (Model Context Protocol) Commands
=========================================================

FastMCP server with DSPy integration for AI-powered analysis of GitHub Actions
workflows and validation systems.

This module provides comprehensive MCP functionality including:

• **FastMCP Server**: Full Model Context Protocol implementation
• **DSPy Integration**: 10 specialized AI models with 4 strategies
• **GitHub Actions**: Complete API coverage with AI analysis
• **Validation System**: Multi-level validation with ML detection
• **Rich CLI**: Beautiful terminal output with progress tracking

Key Features
-----------
• **AI-Powered Analysis**: DSPy models for validation, optimization, diagnosis
• **Comprehensive Validation**: Strict, moderate, lenient validation levels
• **Workflow Optimization**: Intelligent suggestions for GitHub Actions
• **Real-Time Dashboard**: Live validation metrics and monitoring
• **Performance Analysis**: Detailed performance insights and bottlenecks

Usage
-----
    $ uvmgr mcp server                    # Start MCP server
    $ uvmgr mcp status --owner org --repo repo  # Get status with AI analysis
    $ uvmgr mcp dashboard --owner org --repo repo  # Get validation dashboard
    $ uvmgr mcp optimize --owner org --repo repo  # Optimize workflows

Example
-------
    >>> from uvmgr.commands import mcp
    >>> # MCP commands are available via CLI

See Also
--------
- :mod:`uvmgr.mcp.server` : FastMCP server implementation
- :mod:`uvmgr.mcp.client` : MCP client with DSPy integration
- :mod:`uvmgr.mcp.models` : Advanced DSPy models
- :mod:`uvmgr.mcp.config` : Configuration management
"""

from uvmgr.mcp.commands import mcp_group

# Export the MCP command group for CLI mounting as 'app'
app = mcp_group
__all__ = ["app", "mcp_group"] 