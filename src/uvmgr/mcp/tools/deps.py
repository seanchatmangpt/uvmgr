"""
Dependency Management Tools - Tools for managing Python package dependencies.

This module provides tools for adding, removing, and upgrading project dependencies.
"""

from fastmcp import Context

from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult
from uvmgr.ops import deps as deps_ops

# -----------------------------------------------------------------------------
# Dependency Management Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def add_dependency(
    ctx: Context,
    packages: list[str],
    dev: bool = False,
) -> str:
    """
    Add packages to the project.

    Parameters
    ----------
    - ctx: MCP context
    - packages: List of package names to install
    - dev: If True, add as development dependencies
    """
    try:
        await ctx.info(f"Adding {len(packages)} package(s)...")

        result = deps_ops.add(packages, dev=dev)

        return OperationResult(
            success=True,
            message=f"Added {len(packages)} package(s)",
            details={"packages": packages, "dev": dev, "action": "add"},
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to add packages",
            details={"error": str(e), "packages": packages},
        ).to_string()


@mcp.tool()
async def remove_dependency(packages: list[str]) -> str:
    """
    Remove packages from the project.

    Parameters
    ----------
    - packages: List of package names to remove
    """
    try:
        result = deps_ops.remove(packages)

        return OperationResult(
            success=True,
            message=f"Removed {len(packages)} package(s)",
            details={"packages": packages, "action": "remove"},
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to remove packages",
            details={"error": str(e), "packages": packages},
        ).to_string()


@mcp.tool()
async def upgrade_dependencies(all: bool = False, packages: list[str] | None = None) -> str:
    """
    Upgrade project dependencies.

    Parameters
    ----------
    - all: If True, upgrade all dependencies
    - packages: Specific packages to upgrade (if not upgrading all)
    """
    try:
        result = deps_ops.upgrade(all_pkgs=all, pkgs=packages)

        target = "all dependencies" if all else f"{len(packages or [])} package(s)"
        return OperationResult(
            success=True, message=f"Upgraded {target}", details={"all": all, "packages": packages}
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to upgrade dependencies", details={"error": str(e)}
        ).to_string()
