"""
uvmgr.runtime.tools
------------------
Runtime layer for tool management operations.

This module provides the runtime implementation for tool management operations,
including tool installation, execution, and management through various backends
like uv, uvx, and direct execution.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import ToolAttributes, ToolOperations
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def install_tool(package: str, dev: bool = False, isolated: bool = False) -> Dict[str, Any]:
    """
    Install a tool using appropriate backend.
    
    Args:
        package: Package name to install
        dev: Install as development dependency
        isolated: Use isolated environment (uvx)
        
    Returns:
        Dictionary with installation results
    """
    with span("tool.install", package=package):
        add_span_attributes(**{
            ToolAttributes.OPERATION: ToolOperations.INSTALL,
            ToolAttributes.TOOL_NAME: package,
            ToolAttributes.ISOLATED: isolated,
        })
        add_span_event("tool.install.started", {
            "package": package, 
            "isolated": isolated,
            "dev": dev
        })
        
        result = {"success": False, "package": package, "backend": "", "error": None}
        
        try:
            if isolated:
                # Use uvx for isolated installation
                cmd = ["uvx", "install", package]
                result["backend"] = "uvx"
                add_span_event("tool.install.using_uvx", {"package": package})
            else:
                # Use uv for project installation
                cmd = ["uv", "add", package]
                if dev:
                    cmd.append("--dev")
                result["backend"] = "uv"
                add_span_event("tool.install.using_uv", {"package": package, "dev": dev})
            
            process_result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            result["success"] = True
            add_span_attributes(**{"tool.install.success": True})
            add_span_event("tool.install.completed", {"success": True})
            colour(f"✅ Installed {package} using {result['backend']}", "green")
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            add_span_event("tool.install.failed", {
                "error": result["error"],
                "exit_code": e.returncode
            })
            colour(f"❌ Failed to install {package}: {result['error']}", "red")
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.install.error", {"error": result["error"]})
            colour(f"❌ Error installing {package}: {result['error']}", "red")
        
        return result


def run_tool(tool: str, args: List[str], isolated: bool = False) -> Dict[str, Any]:
    """
    Run a tool with specified arguments.
    
    Args:
        tool: Tool name to run
        args: Arguments to pass to the tool
        isolated: Use isolated environment (uvx)
        
    Returns:
        Dictionary with execution results
    """
    with span("tool.run", tool=tool):
        add_span_attributes(**{
            ToolAttributes.OPERATION: ToolOperations.RUN,
            ToolAttributes.TOOL_NAME: tool,
            ToolAttributes.ISOLATED: isolated,
        })
        add_span_event("tool.run.started", {
            "tool": tool, 
            "args": args,
            "isolated": isolated
        })
        
        result = {"success": False, "tool": tool, "backend": "", "output": "", "error": None}
        
        try:
            if isolated:
                # Use uvx run for isolated execution
                cmd = ["uvx", "run", tool] + args
                result["backend"] = "uvx"
                add_span_event("tool.run.using_uvx", {"tool": tool})
            else:
                # Direct execution or uv run
                if Path(tool).exists():
                    # Direct execution of file path
                    cmd = [sys.executable, tool] + args
                    result["backend"] = "python"
                else:
                    # Try uv run first, fall back to direct
                    try:
                        cmd = ["uv", "run", tool] + args
                        result["backend"] = "uv"
                        add_span_event("tool.run.using_uv", {"tool": tool})
                    except:
                        cmd = [tool] + args
                        result["backend"] = "direct"
                        add_span_event("tool.run.using_direct", {"tool": tool})
            
            process_result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            result["success"] = True
            result["output"] = process_result.stdout
            add_span_attributes(**{"tool.run.success": True})
            add_span_event("tool.run.completed", {"success": True})
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            result["output"] = e.stdout or ""
            add_span_event("tool.run.failed", {
                "error": result["error"],
                "exit_code": e.returncode
            })
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.run.error", {"error": result["error"]})
        
        return result


def list_tools(isolated: bool = False) -> Dict[str, Any]:
    """
    List available tools.
    
    Args:
        isolated: List isolated tools (uvx) or project tools
        
    Returns:
        Dictionary with tool list
    """
    with span("tool.list"):
        add_span_attributes(**{
            ToolAttributes.OPERATION: ToolOperations.LIST,
            ToolAttributes.ISOLATED: isolated,
        })
        add_span_event("tool.list.started", {"isolated": isolated})
        
        result = {"tools": [], "backend": "", "error": None}
        
        try:
            if isolated:
                # List uvx tools
                process_result = subprocess.run(
                    ["uvx", "list"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                result["backend"] = "uvx"
                # Parse uvx list output (tool lines typically start with package name)
                for line in process_result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith(" "):
                        # Extract tool name (first word)
                        tool_name = line.split()[0] if line.split() else line
                        result["tools"].append({"name": tool_name, "isolated": True})
                        
            else:
                # List project dependencies
                try:
                    process_result = subprocess.run(
                        ["uv", "pip", "list"], 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    result["backend"] = "uv"
                    # Parse pip list output
                    lines = process_result.stdout.splitlines()
                    for line in lines[2:]:  # Skip header lines
                        parts = line.split()
                        if len(parts) >= 2:
                            result["tools"].append({
                                "name": parts[0], 
                                "version": parts[1],
                                "isolated": False
                            })
                except subprocess.CalledProcessError:
                    # Fallback to basic uv list
                    result["tools"] = []
                    result["backend"] = "uv (no pip list)"
            
            add_span_attributes(**{
                ToolAttributes.PACKAGE_COUNT: len(result["tools"]),
            })
            add_span_event("tool.list.completed", {"count": len(result["tools"])})
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            add_span_event("tool.list.failed", {"error": result["error"]})
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.list.error", {"error": result["error"]})
        
        return result


def uninstall_tool(package: str, isolated: bool = False) -> Dict[str, Any]:
    """
    Uninstall a tool.
    
    Args:
        package: Package name to uninstall
        isolated: Uninstall from isolated environment (uvx)
        
    Returns:
        Dictionary with uninstallation results
    """
    with span("tool.uninstall", package=package):
        add_span_attributes(**{
            ToolAttributes.OPERATION: ToolOperations.UNINSTALL,
            ToolAttributes.TOOL_NAME: package,
            ToolAttributes.ISOLATED: isolated,
        })
        add_span_event("tool.uninstall.started", {
            "package": package,
            "isolated": isolated
        })
        
        result = {"success": False, "package": package, "backend": "", "error": None}
        
        try:
            if isolated:
                # Use uvx for isolated uninstallation
                cmd = ["uvx", "uninstall", package]
                result["backend"] = "uvx"
                add_span_event("tool.uninstall.using_uvx", {"package": package})
            else:
                # Use uv for project uninstallation
                cmd = ["uv", "remove", package]
                result["backend"] = "uv"
                add_span_event("tool.uninstall.using_uv", {"package": package})
            
            process_result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            result["success"] = True
            add_span_attributes(**{"tool.uninstall.success": True})
            add_span_event("tool.uninstall.completed", {"success": True})
            colour(f"✅ Uninstalled {package} using {result['backend']}", "green")
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            add_span_event("tool.uninstall.failed", {
                "error": result["error"],
                "exit_code": e.returncode
            })
            colour(f"❌ Failed to uninstall {package}: {result['error']}", "red")
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.uninstall.error", {"error": result["error"]})
            colour(f"❌ Error uninstalling {package}: {result['error']}", "red")
        
        return result


def get_tool_info(tool: str, isolated: bool = False) -> Dict[str, Any]:
    """
    Get information about a specific tool.
    
    Args:
        tool: Tool name to get info for
        isolated: Check isolated environment (uvx)
        
    Returns:
        Dictionary with tool information
    """
    with span("tool.info", tool=tool):
        add_span_attributes(**{
            ToolAttributes.OPERATION: "info",
            ToolAttributes.TOOL_NAME: tool,
            ToolAttributes.ISOLATED: isolated,
        })
        add_span_event("tool.info.started", {"tool": tool, "isolated": isolated})
        
        result = {"tool": tool, "found": False, "info": {}, "error": None}
        
        try:
            # Get list of tools and find the specific one
            tools_result = list_tools(isolated=isolated)
            
            if tools_result.get("error"):
                result["error"] = tools_result["error"]
                return result
            
            # Find the tool in the list
            for tool_info in tools_result.get("tools", []):
                if tool_info.get("name") == tool:
                    result["found"] = True
                    result["info"] = tool_info
                    break
            
            if result["found"]:
                add_span_event("tool.info.found", {"tool": tool})
            else:
                add_span_event("tool.info.not_found", {"tool": tool})
            
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.info.error", {"error": result["error"]})
        
        return result


def sync_tools() -> Dict[str, Any]:
    """
    Sync tool environments and dependencies.
    
    Returns:
        Dictionary with sync results
    """
    with span("tool.sync"):
        add_span_attributes(**{
            ToolAttributes.OPERATION: ToolOperations.SYNC,
        })
        add_span_event("tool.sync.started", {})
        
        result = {"success": False, "actions": [], "error": None}
        
        try:
            # Sync uv project
            process_result = subprocess.run(
                ["uv", "sync"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            result["actions"].append("uv_sync")
            result["success"] = True
            
            add_span_event("tool.sync.completed", {"success": True})
            colour("✅ Tool environments synced", "green")
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            add_span_event("tool.sync.failed", {"error": result["error"]})
            colour(f"❌ Failed to sync tools: {result['error']}", "red")
        except Exception as e:
            result["error"] = str(e)
            add_span_event("tool.sync.error", {"error": result["error"]})
            colour(f"❌ Error syncing tools: {result['error']}", "red")
        
        return result