"""
Project Management Tools - Tools for creating and analyzing Python projects.

This module provides tools for creating new Python projects and analyzing
existing project structures.
"""

from pathlib import Path
from typing import Dict, Any

from fastmcp import FastMCP, Context
from uvmgr.core import paths
from uvmgr.ops import project as project_ops
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
    
    Parameters:
    - ctx: MCP context
    - name: Project name/directory
    - template: Project template to use
    - fastapi: Include FastAPI setup
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
                'dependencies = []',
                'dependencies = ["fastapi", "uvicorn"]'
            )
        
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        # Create README
        (project_path / "README.md").write_text(f"# {name}\n\nA new Python project managed by uvmgr.\n")
        
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
                "fastapi": fastapi
            }
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to create project",
            details={"error": str(e), "name": name}
        ).to_string()


@mcp.tool()
async def analyze_project(path: str = ".") -> str:
    """
    Analyze a Python project structure and configuration.
    
    Parameters:
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
            (project_path / f).exists() 
            for f in ["ruff.toml", ".ruff.toml", "pyproject.toml"]
        )
        
        return OperationResult(
            success=True,
            message="Project analysis complete",
            details=analysis
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to analyze project",
            details={"error": str(e), "path": path}
        ).to_string() 