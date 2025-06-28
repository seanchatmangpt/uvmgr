"""
Build Tools - Tools for building packages and managing versions.

This module provides MCP tools for building Python packages, managing versions,
and generating changelogs. These tools enable AI assistants to help with
package distribution and release management.

Available Tools
--------------
- build_package : Build Python package (wheel and sdist)
- bump_version : Bump project version using Commitizen
- generate_changelog : Generate changelog from commit history

All tools integrate with uvmgr's build and release operations and provide
detailed feedback on success or failure.

Example
-------
    >>> from uvmgr.mcp.tools.build import build_package
    >>> result = build_package(upload=False)
    >>> print(result)  # OperationResult string

See Also
--------
- :mod:`uvmgr.ops.build` : Core build operations
- :mod:`uvmgr.ops.release` : Core release operations
"""

from fastmcp import Context

from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult
from uvmgr.ops import build as build_ops
from uvmgr.ops import release as release_ops

# -----------------------------------------------------------------------------
# Build Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def build_package(
    ctx: Context,
    upload: bool = False,
) -> str:
    """
    Build Python package (wheel and sdist).
    
    This tool builds distribution packages for the current Python project,
    creating both wheel (.whl) and source distribution (.tar.gz) files.
    Optionally uploads the packages to PyPI after building.
    
    Parameters
    ----------
    ctx : Context
        MCP context for the operation.
    upload : bool, optional
        If True, upload the built packages to PyPI after building.
        Requires proper PyPI credentials to be configured.
        Default is False.
    
    Returns
    -------
    str
        JSON-formatted string containing operation result with success status,
        message, and details about the build process.
    
    Notes
    -----
    The tool automatically:
    - Builds both wheel and source distribution packages
    - Places built packages in the dist/ directory
    - Validates package structure and metadata
    - Optionally uploads to PyPI if upload=True
    - Provides detailed feedback on the build process
    
    Requirements:
    - Project must have a valid pyproject.toml file
    - All dependencies must be installed
    - For upload: PyPI credentials must be configured
    
    Example
    -------
    >>> # Build packages without uploading
    >>> result = await build_package(upload=False)
    >>> 
    >>> # Build and upload to PyPI
    >>> result = await build_package(upload=True)
    """
    try:
        await ctx.info("Building package...")

        result = build_ops.dist()
        if upload:
            await ctx.info("Uploading to PyPI...")
            upload_result = build_ops.upload()

        return OperationResult(
            success=True,
            message="Package built" + (" and uploaded" if upload else ""),
            details={"built": result.get("built", "dist/"), "uploaded": upload},
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to build package", details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def bump_version(ctx: Context) -> str:
    """
    Bump project version using commitizen.

    Parameters
    ----------
    - ctx: MCP context
    """
    try:
        await ctx.info("Bumping version...")

        result = release_ops.bump()

        return OperationResult(success=True, message="Version bumped", details=result).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to bump version", details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def generate_changelog() -> str:
    """Generate changelog from commit history."""
    try:
        changelog = release_ops.changelog()

        return OperationResult(
            success=True, message="Changelog generated", details={"changelog": changelog}
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to generate changelog", details={"error": str(e)}
        ).to_string()
