"""
Build Tools - Tools for building packages and managing versions.

This module provides tools for building Python packages, managing versions,
and generating changelogs.
"""

from fastmcp import FastMCP, Context
from uvmgr.ops import build as build_ops
from uvmgr.ops import release as release_ops
from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult

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
    
    Parameters:
    - ctx: MCP context
    - upload: If True, upload to PyPI after building
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
            details={
                "built": result.get("built", "dist/"),
                "uploaded": upload
            }
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to build package",
            details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def bump_version(ctx: Context) -> str:
    """
    Bump project version using commitizen.
    
    Parameters:
    - ctx: MCP context
    """
    try:
        await ctx.info("Bumping version...")
        
        result = release_ops.bump()
        
        return OperationResult(
            success=True,
            message="Version bumped",
            details=result
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to bump version",
            details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def generate_changelog() -> str:
    """Generate changelog from commit history."""
    try:
        changelog = release_ops.changelog()
        
        return OperationResult(
            success=True,
            message="Changelog generated",
            details={"changelog": changelog}
        ).to_string()
        
    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to generate changelog",
            details={"error": str(e)}
        ).to_string() 