"""
uvmgr.ops.uvx
=============

Operations layer for uvx (uv's pipx equivalent) tool management.

This module provides business logic for managing Python tools through uvx,
offering isolated environments, global tool installation, and advanced
tool management capabilities.

Value-add features:
• Smart tool recommendations
• Tool profiles and collections  
• Integration with uvmgr workflows
• Version management and upgrades
• Environment health checking
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import ToolAttributes, ToolOperations, UvxAttributes
from uvmgr.core.shell import colour
from uvmgr.runtime.uv import run_uv_command


@dataclass
class ToolInfo:
    """Information about an installed tool."""
    name: str
    version: str
    python_version: str
    apps: List[str]
    isolated: bool = True
    install_date: Optional[str] = None


@dataclass
class ToolRecommendation:
    """Smart tool recommendation."""
    name: str
    description: str
    category: str
    use_case: str
    priority: int = 1


# Tool recommendations database
TOOL_RECOMMENDATIONS = {
    "linting": [
        ToolRecommendation("ruff", "Fast Python linter", "linting", "Code quality", 1),
        ToolRecommendation("mypy", "Static type checker", "linting", "Type safety", 2),
        ToolRecommendation("bandit", "Security linter", "linting", "Security", 3),
    ],
    "formatting": [
        ToolRecommendation("black", "Code formatter", "formatting", "Style consistency", 1),
        ToolRecommendation("isort", "Import sorter", "formatting", "Import organization", 2),
    ],
    "testing": [
        ToolRecommendation("pytest", "Testing framework", "testing", "Unit tests", 1),
        ToolRecommendation("coverage", "Coverage analysis", "testing", "Test coverage", 2),
        ToolRecommendation("tox", "Test automation", "testing", "Multi-env testing", 3),
    ],
    "development": [
        ToolRecommendation("httpie", "HTTP client", "development", "API testing", 1),
        ToolRecommendation("ipython", "Enhanced REPL", "development", "Interactive development", 2),
        ToolRecommendation("cookiecutter", "Project templates", "development", "Project scaffolding", 3),
    ],
    "documentation": [
        ToolRecommendation("mkdocs", "Documentation generator", "documentation", "Static sites", 1),
        ToolRecommendation("sphinx", "Documentation builder", "documentation", "API docs", 2),
    ]
}


def install_tool(package: str, python: Optional[str] = None, force: bool = False) -> bool:
    """
    Install a tool using uvx in an isolated environment.
    
    Args:
        package: Package name to install (e.g., 'black', 'ruff==0.1.0')
        python: Specific Python version to use
        force: Force reinstall if already exists
        
    Returns:
        True if installation succeeded
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.INSTALL,
        UvxAttributes.PACKAGE: package,
        ToolAttributes.ISOLATED: True
    })
    
    cmd = ["uvx", "install"]
    
    if python:
        cmd.extend(["--python", python])
        add_span_attributes(**{UvxAttributes.PYTHON_VERSION: python})
    
    if force:
        cmd.append("--force")
        add_span_attributes(**{UvxAttributes.FORCE: True})
    
    cmd.append(package)
    
    add_span_event("uvx_install_start", {"package": package})
    
    try:
        result = run_uv_command(cmd)
        if result.returncode == 0:
            add_span_event("uvx_install_success", {"package": package})
            colour(f"✅ Installed {package} with uvx", "green")
            return True
        else:
            add_span_event("uvx_install_failed", {
                "package": package, 
                "error": result.stderr
            })
            colour(f"❌ Failed to install {package}: {result.stderr}", "red")
            return False
    except Exception as e:
        add_span_event("uvx_install_error", {"package": package, "error": str(e)})
        colour(f"❌ Error installing {package}: {e}", "red")
        return False


def run_tool(tool: str, args: List[str], isolated: bool = True) -> bool:
    """
    Run a tool with uvx or from project venv.
    
    Args:
        tool: Tool name to run
        args: Arguments to pass to the tool
        isolated: Whether to use uvx (isolated) or project venv
        
    Returns:
        True if command succeeded
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.RUN,
        UvxAttributes.TOOL: tool,
        ToolAttributes.ISOLATED: isolated
    })
    
    if isolated:
        cmd = ["uvx", "run", tool] + args
        add_span_event("uvx_run_isolated", {"tool": tool, "args": args})
    else:
        # Fall back to project venv (existing behavior)
        from uvmgr.ops.tools import run as tools_run
        add_span_event("uvx_run_venv", {"tool": tool, "args": args})
        return tools_run(tool, args)
    
    try:
        result = run_uv_command(cmd)
        success = result.returncode == 0
        
        if success:
            add_span_event("uvx_run_success", {"tool": tool})
        else:
            add_span_event("uvx_run_failed", {
                "tool": tool,
                "error": result.stderr
            })
            
        return success
    except Exception as e:
        add_span_event("uvx_run_error", {"tool": tool, "error": str(e)})
        return False


def list_tools() -> List[ToolInfo]:
    """
    List all installed uvx tools.
    
    Returns:
        List of ToolInfo objects for installed tools
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.LIST
    })
    
    try:
        result = run_uv_command(["uvx", "list", "--format", "json"])
        if result.returncode != 0:
            add_span_event("uvx_list_failed", {"error": result.stderr})
            return []
        
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        tools = []
        
        for tool_name, tool_data in data.items():
            apps = tool_data.get("apps", [])
            version = tool_data.get("version", "unknown")
            python_version = tool_data.get("python_version", "unknown")
            
            tools.append(ToolInfo(
                name=tool_name,
                version=version,
                python_version=python_version,
                apps=apps,
                isolated=True
            ))
        
        add_span_attributes(**{UvxAttributes.TOOL_COUNT: len(tools)})
        add_span_event("uvx_list_success", {"tool_count": len(tools)})
        
        return tools
        
    except Exception as e:
        add_span_event("uvx_list_error", {"error": str(e)})
        return []


def uninstall_tool(package: str) -> bool:
    """
    Uninstall a tool using uvx.
    
    Args:
        package: Package name to uninstall
        
    Returns:
        True if uninstallation succeeded
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.UNINSTALL,
        UvxAttributes.PACKAGE: package
    })
    
    add_span_event("uvx_uninstall_start", {"package": package})
    
    try:
        result = run_uv_command(["uvx", "uninstall", package])
        if result.returncode == 0:
            add_span_event("uvx_uninstall_success", {"package": package})
            colour(f"✅ Uninstalled {package}", "green")
            return True
        else:
            add_span_event("uvx_uninstall_failed", {
                "package": package,
                "error": result.stderr
            })
            colour(f"❌ Failed to uninstall {package}: {result.stderr}", "red")
            return False
    except Exception as e:
        add_span_event("uvx_uninstall_error", {"package": package, "error": str(e)})
        colour(f"❌ Error uninstalling {package}: {e}", "red")
        return False


def upgrade_tool(package: str) -> bool:
    """
    Upgrade a tool to the latest version.
    
    Args:
        package: Package name to upgrade
        
    Returns:
        True if upgrade succeeded
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.UPGRADE,
        UvxAttributes.PACKAGE: package
    })
    
    # uvx doesn't have direct upgrade, so we reinstall with --force
    return install_tool(package, force=True)


def get_recommendations(category: Optional[str] = None) -> List[ToolRecommendation]:
    """
    Get smart tool recommendations.
    
    Args:
        category: Optional category filter (linting, formatting, testing, etc.)
        
    Returns:
        List of recommended tools
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.RECOMMEND,
        UvxAttributes.CATEGORY: category or "all"
    })
    
    if category and category in TOOL_RECOMMENDATIONS:
        recommendations = TOOL_RECOMMENDATIONS[category]
    else:
        # Return top recommendation from each category
        recommendations = []
        for cat_tools in TOOL_RECOMMENDATIONS.values():
            if cat_tools:
                recommendations.append(cat_tools[0])  # Top priority tool
    
    add_span_attributes(**{UvxAttributes.RECOMMENDATION_COUNT: len(recommendations)})
    add_span_event("uvx_recommendations", {
        "category": category or "all",
        "count": len(recommendations)
    })
    
    return sorted(recommendations, key=lambda x: x.priority)


def health_check() -> Dict[str, Any]:
    """
    Check the health of uvx and installed tools.
    
    Returns:
        Health status information
    """
    add_span_attributes(**{
        UvxAttributes.OPERATION: UvxOperations.HEALTH_CHECK
    })
    
    health = {
        "uvx_available": False,
        "tool_count": 0,
        "issues": [],
        "recommendations": []
    }
    
    # Check if uvx is available
    try:
        result = run_uv_command(["uvx", "--version"])
        if result.returncode == 0:
            health["uvx_available"] = True
            health["uvx_version"] = result.stdout.strip()
        else:
            health["issues"].append("uvx not available")
    except Exception:
        health["issues"].append("uvx command failed")
    
    # Check installed tools
    if health["uvx_available"]:
        tools = list_tools()
        health["tool_count"] = len(tools)
        health["tools"] = [{"name": t.name, "version": t.version} for t in tools]
        
        # Check for common issues
        if len(tools) == 0:
            health["recommendations"].append("Consider installing common tools like ruff, black")
    
    add_span_attributes(**{
        UvxAttributes.HEALTH_STATUS: "healthy" if not health["issues"] else "issues",
        UvxAttributes.TOOL_COUNT: health["tool_count"]
    })
    
    add_span_event("uvx_health_check", {
        "available": health["uvx_available"],
        "tool_count": health["tool_count"],
        "issues": len(health["issues"])
    })
    
    return health


# Create operation class for easy access
class UvxOperations:
    """uvx operation types for semantic conventions."""
    INSTALL = "install"
    RUN = "run" 
    LIST = "list"
    UNINSTALL = "uninstall"
    UPGRADE = "upgrade"
    RECOMMEND = "recommend"
    HEALTH_CHECK = "health_check"