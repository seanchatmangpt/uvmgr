"""
MCP Resources - Read-only project information and prompts.

This module provides resource handlers for the MCP server that expose
read-only project information and LLM interaction templates.
"""

import json
from pathlib import Path
from typing import Dict, Any

from fastmcp import FastMCP, Context
from uvmgr.core import paths
from uvmgr.ops import deps as deps_ops

# Get the MCP instance from _mcp_instance
from uvmgr.mcp._mcp_instance import mcp

# -----------------------------------------------------------------------------
# Resources - Read-only project information
# -----------------------------------------------------------------------------

@mcp.resource("project://info")
async def get_project_info() -> str:
    """Get current project metadata from pyproject.toml."""
    try:
        pyproject_path = paths.project_root() / "pyproject.toml"
        if not pyproject_path.exists():
            return "No pyproject.toml found in current directory"
        
        import tomllib
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        
        project = data.get('project', {})
        info = {
            "name": project.get('name', 'Unknown'),
            "version": project.get('version', 'Unknown'),
            "description": project.get('description', ''),
            "python_requires": project.get('requires-python', ''),
            "dependencies": len(project.get('dependencies', [])),
            "root_directory": str(paths.project_root()),
            "venv_path": str(paths.venv_path())
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error reading project info: {e}"


@mcp.resource("project://structure")
async def get_project_structure() -> str:
    """Get project directory structure."""
    try:
        root = paths.project_root()
        structure = []
        
        for path in sorted(root.rglob("*")):
            if any(part.startswith('.') for part in path.parts):
                continue  # Skip hidden files
            if any(part in ['__pycache__', 'node_modules', '.venv'] for part in path.parts):
                continue  # Skip common ignored directories
            
            rel_path = path.relative_to(root)
            indent = "  " * (len(rel_path.parts) - 1)
            name = path.name
            if path.is_dir():
                name += "/"
            structure.append(f"{indent}{name}")
        
        return "\n".join(structure[:100])  # Limit to first 100 entries
    except Exception as e:
        return f"Error getting project structure: {e}"


@mcp.resource("project://dependencies")
async def list_dependencies() -> str:
    """List all project dependencies."""
    try:
        deps = deps_ops.list_pkgs()
        return "\n".join(deps) if deps else "No dependencies installed"
    except Exception as e:
        return f"Error listing dependencies: {e}"


@mcp.resource("project://files/{path:path}")
async def read_project_file(path: str) -> str:
    """Read a file from the project."""
    try:
        # Validate path is within project
        project_root = paths.project_root()
        full_path = (project_root / path).resolve()
        
        if not full_path.is_relative_to(project_root):
            return "Error: Path is outside project directory"
        
        if not full_path.exists():
            return f"Error: File not found: {path}"
        
        if full_path.is_dir():
            return f"Error: Path is a directory: {path}"
        
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file: {e}"


# -----------------------------------------------------------------------------
# Prompts - LLM interaction templates
# -----------------------------------------------------------------------------

@mcp.prompt("debug://test_failure")
async def debug_test_prompt(test_output: str) -> str:
    """Help debug failing tests."""
    return f"""
The following tests are failing in a Python project using uvmgr. 
Please analyze the error and suggest fixes:

{test_output}

Provide:
1. Root cause analysis of the failure
2. Suggested code changes to fix the issue
3. Additional tests that might help prevent similar issues
4. Any dependency or configuration issues that might be involved
"""


@mcp.prompt("review://code_quality")
async def review_code_prompt(file_path: str, code: str) -> str:
    """Review code for quality and best practices."""
    return f"""
Please review the following Python code from {file_path} for:
- Code quality and readability
- Python best practices
- Potential bugs or issues
- Performance considerations
- Security concerns

Code:
```python
{code}
```

Provide specific, actionable feedback with examples where appropriate.
"""


@mcp.prompt("architect://feature")
async def architect_feature_prompt(feature_request: str, existing_structure: str) -> str:
    """Help architect a new feature."""
    return f"""
As a Python architect, help implement this feature request in a uvmgr-managed project:

Feature Request:
{feature_request}

Current Project Structure:
{existing_structure}

Please provide:
1. Recommended file structure and module organization
2. Key classes/functions to implement
3. Integration points with existing code
4. Testing strategy
5. Any new dependencies needed
""" 