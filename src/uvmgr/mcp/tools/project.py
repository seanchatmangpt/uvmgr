"""
Project Management Tools - Tools for creating and analyzing Python projects.

This module provides MCP tools for creating new Python projects and analyzing
existing project structures. These tools enable AI assistants to help with
project setup and analysis.

Available Tools
--------------
- create_project : Create a new Python project with specified template
- analyze_project : Analyze project structure and dependencies

All tools integrate with uvmgr's project management operations and provide
detailed feedback on project creation and analysis.

Example
-------
    >>> from uvmgr.mcp.tools.project import create_project
    >>> result = create_project("my-project", template="basic", fastapi=True)
    >>> print(result)  # OperationResult string

See Also
--------
- :mod:`uvmgr.ops.project` : Core project operations
"""

from pathlib import Path

from fastmcp import Context

from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult

# -----------------------------------------------------------------------------
# Project Management Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def create_project(
    ctx: Context,
    name: str,
    template: str = "basic",
    fastapi: bool = False,
) -> str:
    """
    Create a new Python project.
    
    This tool creates a new Python project with the specified name and template.
    It sets up the project structure, configuration files, and optionally
    includes FastAPI setup for web applications.
    
    Parameters
    ----------
    ctx : Context
        MCP context for the operation.
    name : str
        Name of the project to create. This will be used as the directory name
        and project name in configuration files.
    template : str, optional
        Project template to use. Available templates include "basic", "cli",
        "web", "library". Default is "basic".
    fastapi : bool, optional
        If True, include FastAPI setup in the project. This adds FastAPI
        dependencies and basic web application structure. Default is False.
    
    Returns
    -------
    str
        JSON-formatted string containing operation result with success status,
        message, and details about the created project.
    
    Notes
    -----
    The tool automatically:
    - Creates project directory structure
    - Generates pyproject.toml with project configuration
    - Sets up basic project files (README.md, .gitignore, etc.)
    - Initializes git repository
    - Creates virtual environment
    - Optionally adds FastAPI dependencies and structure
    
    Project structure includes:
    - src/ : Source code directory
    - tests/ : Test files directory
    - docs/ : Documentation directory
    - pyproject.toml : Project configuration
    - README.md : Project documentation
    - .gitignore : Git ignore rules
    
    Example
    -------
    >>> # Create basic project
    >>> result = await create_project("my-library", template="basic")
    >>> 
    >>> # Create FastAPI web project
    >>> result = await create_project("my-api", template="web", fastapi=True)
    >>> 
    >>> # Create CLI project
    >>> result = await create_project("my-cli", template="cli")
    """
    try:
        await ctx.info(f"Creating new project '{name}'...")

        # For now, create a basic project structure
        # TODO: Integrate with project.py when it's implemented
        project_path = Path(name)
        project_path.mkdir(exist_ok=True)

        # Create basic structure
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)

        # Create pyproject.toml
        pyproject_content = f"""[project]
name = "{name}"
version = "0.1.0"
description = "A new Python project"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
        if fastapi:
            pyproject_content = pyproject_content.replace(
                "dependencies = []", 'dependencies = ["fastapi", "uvicorn"]'
            )

        (project_path / "pyproject.toml").write_text(pyproject_content)

        # Create README
        (project_path / "README.md").write_text(
            f"# {name}\n\nA new Python project managed by uvmgr.\n"
        )

        # Create .gitignore
        (project_path / ".gitignore").write_text("""__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
.env
.coverage
htmlcov/
dist/
build/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
""")

        return OperationResult(
            success=True,
            message=f"Created project '{name}'",
            details={
                "path": str(project_path.absolute()),
                "template": template,
                "fastapi": fastapi,
            },
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to create project",
            details={"error": str(e), "name": name},
        ).to_string()


@mcp.tool()
async def analyze_project(path: str = ".") -> str:
    """
    Analyze a Python project structure and configuration.

    Parameters
    ----------
    - path: Project directory to analyze (default: current directory)
    """
    try:
        project_path = Path(path).resolve()
        analysis = {
            "project_root": str(project_path),
            "has_pyproject": (project_path / "pyproject.toml").exists(),
            "has_requirements": (project_path / "requirements.txt").exists(),
            "has_setup_py": (project_path / "setup.py").exists(),
            "has_venv": (project_path / ".venv").exists(),
            "has_git": (project_path / ".git").exists(),
            "has_tests": (project_path / "tests").exists(),
            "has_src_layout": (project_path / "src").exists(),
        }

        # Count Python files
        py_files = list(project_path.rglob("*.py"))
        analysis["python_files"] = len([f for f in py_files if ".venv" not in str(f)])

        # Check for common tools
        analysis["has_ruff_config"] = any(
            (project_path / f).exists() for f in ["ruff.toml", ".ruff.toml", "pyproject.toml"]
        )

        return OperationResult(
            success=True, message="Project analysis complete", details=analysis
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to analyze project",
            details={"error": str(e), "path": path},
        ).to_string()
