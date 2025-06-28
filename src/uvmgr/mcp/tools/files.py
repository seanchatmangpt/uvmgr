"""
File Operations Tools - Tools for searching and creating files.

This module provides tools for searching through project files and creating
new files in the project.
"""

from fastmcp import Context

from uvmgr.core import paths
from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult

# -----------------------------------------------------------------------------
# File Operations Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def search_code(
    ctx: Context,
    pattern: str,
    file_pattern: str | None = None,
) -> str:
    """
    Search for code patterns in project files.

    Parameters
    ----------
    - ctx: MCP context
    - pattern: Text or regex pattern to search for
    - file_pattern: File pattern filter (e.g., "*.py")
    """
    try:
        await ctx.info(f"Searching for: {pattern}")

        # Use ripgrep if available, otherwise fallback to Python
        root = paths.project_root()
        matches = []
        # Simple Python-based search for now
        for py_file in root.rglob(file_pattern or "*.py"):
            if ".venv" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern.lower() in line.lower():
                        matches.append(f"{py_file}:{i}: {line.strip()}")
            except:
                continue

        return OperationResult(
            success=True,
            message=f"Found {len(matches)} matches",
            details={
                "pattern": pattern,
                "matches": matches[:20],  # Limit to first 20
            },
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Search failed", details={"error": str(e), "pattern": pattern}
        ).to_string()


@mcp.tool()
async def create_file(
    ctx: Context,
    path: str,
    content: str,
) -> str:
    """
    Create a new file in the project.

    Parameters
    ----------
    - ctx: MCP context
    - path: File path relative to project root
    - content: File content
    """
    try:
        # Validate path
        project_root = paths.project_root()
        full_path = (project_root / path).resolve()

        if not full_path.is_relative_to(project_root):
            return OperationResult(
                success=False, message="Path is outside project directory", details={"path": path}
            ).to_string()

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        full_path.write_text(content, encoding="utf-8")

        return OperationResult(
            success=True,
            message=f"Created file: {path}",
            details={"path": str(full_path), "size": len(content)},
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to create file", details={"error": str(e), "path": path}
        ).to_string()
