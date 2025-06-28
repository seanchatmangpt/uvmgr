"""
Universal Tool Integration Framework
===================================

This module addresses the critical gap in uvmgr's tool integration by providing a unified framework
for integrating with external development tools and services.

Key features:
1. **Tool Adapters**: Standardized interfaces for common dev tools
2. **Command Translation**: Unified commands that delegate to appropriate tools
3. **Context-Aware Routing**: Intelligent tool selection based on project context
4. **Configuration Management**: Unified configuration for all integrated tools
5. **Health Monitoring**: Status checks and health monitoring for integrated tools

The 80/20 approach: 20% of integration features that provide 80% of tool integration value.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from enum import Enum
import time
import logging

from uvmgr.core.semconv import ToolAttributes, ToolOperations, CliAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.workspace import get_workspace_config, get_workspace_manager

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of development tools."""
    PACKAGE_MANAGER = "package_manager"
    BUILD_SYSTEM = "build_system" 
    CONTAINER = "container"
    VERSION_CONTROL = "version_control"
    DATABASE = "database"
    WEB_FRAMEWORK = "web_framework"
    TESTING = "testing"
    LINTING = "linting"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    CLOUD = "cloud"
    AI_ML = "ai_ml"


class ToolStatus(Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    VERSION_INCOMPATIBLE = "version_incompatible"
    CONFIG_ERROR = "config_error"
    NETWORK_ERROR = "network_error"


@dataclass
class ToolInfo:
    """Information about a development tool."""
    
    name: str
    category: ToolCategory
    version: Optional[str] = None
    status: ToolStatus = ToolStatus.NOT_FOUND
    command: Optional[str] = None
    install_instructions: Optional[str] = None
    config_path: Optional[Path] = None
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ToolCommand:
    """Represents a command that can be executed by a tool."""
    
    tool_name: str
    operation: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    working_directory: Optional[Path] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[int] = None


@dataclass
class ToolResult:
    """Result of executing a tool command."""
    
    success: bool
    return_code: int
    stdout: str
    stderr: str
    duration: float
    command: str
    tool_name: str
    error_message: Optional[str] = None


class ToolAdapter(ABC):
    """Abstract base class for tool adapters."""
    
    def __init__(self, tool_info: ToolInfo):
        self.tool_info = tool_info
        self._health_cache: Optional[Tuple[bool, float]] = None
        self._health_cache_timeout = 60.0  # Cache health check for 60 seconds
    
    @abstractmethod
    async def check_available(self) -> bool:
        """Check if the tool is available and properly configured."""
        pass
    
    @abstractmethod
    async def get_version(self) -> Optional[str]:
        """Get the tool version."""
        pass
    
    @abstractmethod
    async def execute_command(self, command: ToolCommand) -> ToolResult:
        """Execute a command using this tool."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this tool provides."""
        pass
    
    async def health_check(self, force: bool = False) -> bool:
        """Perform health check with caching."""
        
        current_time = time.time()
        
        # Check cache
        if not force and self._health_cache:
            is_healthy, cache_time = self._health_cache
            if current_time - cache_time < self._health_cache_timeout:
                return is_healthy
        
        # Perform actual health check
        is_healthy = await self.check_available()
        self._health_cache = (is_healthy, current_time)
        
        return is_healthy
    
    def update_status(self, status: ToolStatus, version: Optional[str] = None):
        """Update tool status and version."""
        self.tool_info.status = status
        if version:
            self.tool_info.version = version


class DockerAdapter(ToolAdapter):
    """Docker container management adapter."""
    
    def __init__(self):
        super().__init__(ToolInfo(
            name="docker",
            category=ToolCategory.CONTAINER,
            command="docker",
            capabilities=["container_management", "image_building", "compose"]
        ))
    
    async def check_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = await self._run_command(["docker", "--version"])
            return result.return_code == 0
        except Exception:
            return False
    
    async def get_version(self) -> Optional[str]:
        """Get Docker version."""
        try:
            result = await self._run_command(["docker", "--version"])
            if result.return_code == 0:
                # Parse version from output like "Docker version 20.10.21, build baeda1f"
                version_line = result.stdout.strip()
                if "version" in version_line:
                    parts = version_line.split()
                    for i, part in enumerate(parts):
                        if part == "version" and i + 1 < len(parts):
                            return parts[i + 1].rstrip(',')
        except Exception:
            pass
        return None
    
    async def execute_command(self, command: ToolCommand) -> ToolResult:
        """Execute Docker command."""
        
        cmd_args = ["docker", command.operation] + command.args
        
        # Add common Docker options
        if command.working_directory:
            # For docker run commands, add volume mount
            if command.operation == "run" and "--volume" not in command.args:
                cmd_args.extend(["--volume", f"{command.working_directory}:/workspace"])
                cmd_args.extend(["--workdir", "/workspace"])
        
        return await self._run_command(cmd_args, 
                                     cwd=command.working_directory,
                                     env=command.environment_vars,
                                     timeout=command.timeout)
    
    def get_capabilities(self) -> List[str]:
        """Get Docker capabilities."""
        return [
            "build_images",
            "run_containers", 
            "manage_volumes",
            "docker_compose",
            "container_logs",
            "container_exec"
        ]
    
    async def _run_command(self, cmd: List[str], **kwargs) -> ToolResult:
        """Run a Docker command."""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            return ToolResult(
                success=process.returncode == 0,
                return_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                duration=duration,
                command=' '.join(cmd),
                tool_name="docker"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=' '.join(cmd),
                tool_name="docker",
                error_message=str(e)
            )


class GitAdapter(ToolAdapter):
    """Git version control adapter."""
    
    def __init__(self):
        super().__init__(ToolInfo(
            name="git",
            category=ToolCategory.VERSION_CONTROL,
            command="git",
            capabilities=["version_control", "branching", "remote_repos"]
        ))
    
    async def check_available(self) -> bool:
        """Check if Git is available."""
        try:
            result = await self._run_command(["git", "--version"])
            return result.return_code == 0
        except Exception:
            return False
    
    async def get_version(self) -> Optional[str]:
        """Get Git version."""
        try:
            result = await self._run_command(["git", "--version"])
            if result.return_code == 0:
                # Parse version from "git version 2.39.2"
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    return parts[2]
        except Exception:
            pass
        return None
    
    async def execute_command(self, command: ToolCommand) -> ToolResult:
        """Execute Git command."""
        
        cmd_args = ["git", command.operation] + command.args
        
        return await self._run_command(cmd_args,
                                     cwd=command.working_directory,
                                     env=command.environment_vars,
                                     timeout=command.timeout)
    
    def get_capabilities(self) -> List[str]:
        """Get Git capabilities."""
        return [
            "commit",
            "branch",
            "merge", 
            "push",
            "pull",
            "status",
            "log",
            "diff",
            "remote_management"
        ]
    
    async def _run_command(self, cmd: List[str], **kwargs) -> ToolResult:
        """Run a Git command."""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            return ToolResult(
                success=process.returncode == 0,
                return_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                duration=duration,
                command=' '.join(cmd),
                tool_name="git"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=' '.join(cmd),
                tool_name="git",
                error_message=str(e)
            )


class NodeAdapter(ToolAdapter):
    """Node.js and npm adapter."""
    
    def __init__(self):
        super().__init__(ToolInfo(
            name="node",
            category=ToolCategory.PACKAGE_MANAGER,
            command="npm",
            capabilities=["package_management", "script_execution", "dependency_install"]
        ))
    
    async def check_available(self) -> bool:
        """Check if Node.js and npm are available."""
        try:
            node_result = await self._run_command(["node", "--version"])
            npm_result = await self._run_command(["npm", "--version"])
            return node_result.return_code == 0 and npm_result.return_code == 0
        except Exception:
            return False
    
    async def get_version(self) -> Optional[str]:
        """Get Node.js and npm versions."""
        try:
            node_result = await self._run_command(["node", "--version"])
            npm_result = await self._run_command(["npm", "--version"])
            
            if node_result.return_code == 0 and npm_result.return_code == 0:
                node_version = node_result.stdout.strip().lstrip('v')
                npm_version = npm_result.stdout.strip()
                return f"node-{node_version}/npm-{npm_version}"
        except Exception:
            pass
        return None
    
    async def execute_command(self, command: ToolCommand) -> ToolResult:
        """Execute npm command."""
        
        if command.operation in ["install", "run", "test", "build"]:
            cmd_args = ["npm", command.operation] + command.args
        else:
            # Direct node execution
            cmd_args = ["node"] + command.args
        
        return await self._run_command(cmd_args,
                                     cwd=command.working_directory,
                                     env=command.environment_vars,
                                     timeout=command.timeout)
    
    def get_capabilities(self) -> List[str]:
        """Get Node.js capabilities."""
        return [
            "install_packages",
            "run_scripts",
            "build_projects",
            "test_execution",
            "package_management"
        ]
    
    async def _run_command(self, cmd: List[str], **kwargs) -> ToolResult:
        """Run a Node.js/npm command."""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            return ToolResult(
                success=process.returncode == 0,
                return_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                duration=duration,
                command=' '.join(cmd),
                tool_name="node"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                command=' '.join(cmd),
                tool_name="node",
                error_message=str(e)
            )


class UniversalToolRegistry:
    """Registry for managing all tool adapters."""
    
    def __init__(self):
        self.adapters: Dict[str, ToolAdapter] = {}
        self.capabilities_map: Dict[str, List[str]] = {}
        self.category_map: Dict[ToolCategory, List[str]] = {}
        
        # Register default adapters
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default tool adapters."""
        
        default_adapters = [
            DockerAdapter(),
            GitAdapter(),
            NodeAdapter()
        ]
        
        for adapter in default_adapters:
            self.register_adapter(adapter)
    
    def register_adapter(self, adapter: ToolAdapter):
        """Register a tool adapter."""
        
        tool_name = adapter.tool_info.name
        self.adapters[tool_name] = adapter
        
        # Update capabilities map
        capabilities = adapter.get_capabilities()
        for capability in capabilities:
            if capability not in self.capabilities_map:
                self.capabilities_map[capability] = []
            self.capabilities_map[capability].append(tool_name)
        
        # Update category map
        category = adapter.tool_info.category
        if category not in self.category_map:
            self.category_map[category] = []
        self.category_map[category].append(tool_name)
    
    def get_adapter(self, tool_name: str) -> Optional[ToolAdapter]:
        """Get adapter by tool name."""
        return self.adapters.get(tool_name)
    
    def get_adapters_by_category(self, category: ToolCategory) -> List[ToolAdapter]:
        """Get all adapters in a category."""
        tool_names = self.category_map.get(category, [])
        return [self.adapters[name] for name in tool_names if name in self.adapters]
    
    def get_adapters_by_capability(self, capability: str) -> List[ToolAdapter]:
        """Get all adapters that provide a capability."""
        tool_names = self.capabilities_map.get(capability, [])
        return [self.adapters[name] for name in tool_names if name in self.adapters]
    
    def list_tools(self) -> List[ToolInfo]:
        """List all registered tools."""
        return [adapter.tool_info for adapter in self.adapters.values()]
    
    async def scan_available_tools(self) -> Dict[str, ToolInfo]:
        """Scan and update status of all registered tools."""
        
        available_tools = {}
        
        for tool_name, adapter in self.adapters.items():
            try:
                is_available = await adapter.health_check()
                
                if is_available:
                    version = await adapter.get_version()
                    adapter.update_status(ToolStatus.AVAILABLE, version)
                    available_tools[tool_name] = adapter.tool_info
                else:
                    adapter.update_status(ToolStatus.NOT_FOUND)
                    
            except Exception as e:
                logger.warning(f"Error checking tool {tool_name}: {e}")
                adapter.update_status(ToolStatus.CONFIG_ERROR)
        
        return available_tools


class ContextualToolRouter:
    """Routes operations to appropriate tools based on project context."""
    
    def __init__(self, registry: UniversalToolRegistry):
        self.registry = registry
    
    async def route_operation(self, operation: str, context: Dict[str, Any] = None) -> Optional[ToolAdapter]:
        """Route an operation to the most appropriate tool."""
        
        context = context or {}
        
        # Operation routing logic
        routing_rules = {
            "container_build": [ToolCategory.CONTAINER],
            "container_run": [ToolCategory.CONTAINER],
            "version_control": [ToolCategory.VERSION_CONTROL],
            "package_install": [ToolCategory.PACKAGE_MANAGER],
            "test_run": [ToolCategory.TESTING],
            "build": [ToolCategory.BUILD_SYSTEM, ToolCategory.PACKAGE_MANAGER],
            "deploy": [ToolCategory.DEPLOYMENT, ToolCategory.CONTAINER]
        }
        
        # Get candidate categories
        candidate_categories = routing_rules.get(operation, [])
        
        # Get available tools in those categories
        candidate_tools = []
        for category in candidate_categories:
            category_tools = self.registry.get_adapters_by_category(category)
            for tool in category_tools:
                if await tool.health_check():
                    candidate_tools.append(tool)
        
        if not candidate_tools:
            return None
        
        # Apply context-based selection
        return self._select_best_tool(candidate_tools, context)
    
    def _select_best_tool(self, tools: List[ToolAdapter], context: Dict[str, Any]) -> ToolAdapter:
        """Select the best tool based on context."""
        
        # Simple selection logic (can be enhanced with AGI reasoning)
        
        # Check for project-specific preferences
        project_type = context.get("project_type", "")
        
        # Prefer tools that match project context
        for tool in tools:
            tool_name = tool.tool_info.name
            
            if project_type == "node" and tool_name == "node":
                return tool
            elif "docker" in context.get("config", {}) and tool_name == "docker":
                return tool
        
        # Return first available tool as fallback
        return tools[0] if tools else None


class ToolIntegrationEngine:
    """
    Main engine for universal tool integration.
    
    Provides unified interface for executing operations across different development tools.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.registry = UniversalToolRegistry()
        self.router = ContextualToolRouter(self.registry)
        self.execution_history: List[ToolResult] = []
    
    async def initialize(self):
        """Initialize the integration engine."""
        
        # Scan available tools
        available_tools = await self.registry.scan_available_tools()
        
        # Observe initialization
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "tool_integration_init",
                "tool.integration_engine": "uvmgr_universal_tools",
                "available_tools_count": str(len(available_tools)),
                "workspace_root": str(self.workspace_root)
            },
            context={
                "tool_integration": True,
                "universal_tooling": True,
                "available_tools": list(available_tools.keys())
            }
        )
        
        return available_tools
    
    async def execute_operation(self, operation: str, args: List[str] = None, **kwargs) -> ToolResult:
        """Execute an operation using the most appropriate tool."""
        
        args = args or []
        context = kwargs.get("context", {})
        
        # Add workspace context
        workspace_config = get_workspace_config()
        context.update({
            "project_type": workspace_config.project_type,
            "environment": get_workspace_manager().load_state().current_environment,
            "workspace_root": str(self.workspace_root)
        })
        
        # Route to appropriate tool
        adapter = await self.router.route_operation(operation, context)
        
        if not adapter:
            return ToolResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"No suitable tool found for operation: {operation}",
                duration=0.0,
                command=f"{operation} {' '.join(args)}",
                tool_name="unknown",
                error_message=f"Operation '{operation}' not supported by available tools"
            )
        
        # Create tool command
        command = ToolCommand(
            tool_name=adapter.tool_info.name,
            operation=operation,
            args=args,
            working_directory=kwargs.get("working_directory", self.workspace_root),
            environment_vars=kwargs.get("environment_vars", {}),
            timeout=kwargs.get("timeout")
        )
        
        # Execute command
        result = await adapter.execute_command(command)
        
        # Store execution history
        self.execution_history.append(result)
        
        # Keep only recent executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        # Observe execution
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "tool_integration_execute",
                ToolAttributes.OPERATION: operation,
                ToolAttributes.TOOL_NAME: adapter.tool_info.name,
                "success": str(result.success),
                "duration": str(result.duration),
                "return_code": str(result.return_code)
            },
            context={
                "tool_execution": True,
                "operation": operation,
                "tool_used": adapter.tool_info.name
            }
        )
        
        return result
    
    async def check_tool_availability(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        
        adapter = self.registry.get_adapter(tool_name)
        if not adapter:
            return False
        
        return await adapter.health_check()
    
    def get_available_tools(self) -> List[ToolInfo]:
        """Get list of available tools."""
        
        return [
            adapter.tool_info for adapter in self.registry.adapters.values()
            if adapter.tool_info.status == ToolStatus.AVAILABLE
        ]
    
    def get_tool_capabilities(self, tool_name: str) -> List[str]:
        """Get capabilities of a specific tool."""
        
        adapter = self.registry.get_adapter(tool_name)
        if adapter:
            return adapter.get_capabilities()
        return []
    
    def get_execution_history(self, limit: int = 20) -> List[ToolResult]:
        """Get recent execution history."""
        
        return self.execution_history[-limit:] if self.execution_history else []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool integration statistics."""
        
        total_executions = len(self.execution_history)
        successful_executions = len([r for r in self.execution_history if r.success])
        
        tool_usage = {}
        for result in self.execution_history:
            tool_name = result.tool_name
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return {
            "registered_tools": len(self.registry.adapters),
            "available_tools": len([a for a in self.registry.adapters.values() 
                                  if a.tool_info.status == ToolStatus.AVAILABLE]),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / max(1, total_executions),
            "tool_usage": tool_usage,
            "capabilities_count": len(self.registry.capabilities_map),
            "categories_count": len(self.registry.category_map)
        }


# Global tool integration engine instance
_tool_integration_engine: Optional[ToolIntegrationEngine] = None

def get_tool_integration_engine(workspace_root: Optional[Path] = None) -> ToolIntegrationEngine:
    """Get the global tool integration engine instance."""
    global _tool_integration_engine
    
    if _tool_integration_engine is None:
        _tool_integration_engine = ToolIntegrationEngine(workspace_root)
    
    return _tool_integration_engine

async def initialize_tool_integration():
    """Initialize the global tool integration engine."""
    engine = get_tool_integration_engine()
    return await engine.initialize()

async def execute_universal_operation(operation: str, args: List[str] = None, **kwargs) -> ToolResult:
    """Execute an operation using the universal tool integration."""
    engine = get_tool_integration_engine()
    return await engine.execute_operation(operation, args, **kwargs)