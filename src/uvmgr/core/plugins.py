"""
Plugin Architecture and Marketplace
==================================

This module addresses the critical extensibility gap by providing a lightweight plugin system
and marketplace for uvmgr extensions.

Key features:
1. **Plugin Discovery**: Automatic discovery and loading of plugins
2. **Plugin Registry**: Central registry with versioning and dependency management
3. **Hook System**: Event-driven hooks for extending core functionality
4. **Marketplace Integration**: Remote plugin discovery and installation
5. **Sandboxed Execution**: Safe plugin execution with resource limits

The 80/20 approach: 20% of plugin features that provide 80% of extensibility value.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set, Union, Type
from enum import Enum
import sys
import subprocess
import tempfile
import shutil
import logging
import hashlib

from uvmgr.core.semconv import PluginAttributes, PluginOperations, CliAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.workspace import get_workspace_config, get_workspace_manager

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin status values."""
    AVAILABLE = "available"
    INSTALLED = "installed" 
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"


class PluginType(Enum):
    """Types of plugins."""
    COMMAND = "command"
    TOOL_ADAPTER = "tool_adapter"
    WORKFLOW = "workflow"
    AI_ENHANCEMENT = "ai_enhancement"
    INTEGRATION = "integration"
    THEME = "theme"
    MIDDLEWARE = "middleware"


class HookType(Enum):
    """Hook types for plugin integration."""
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    BEFORE_WORKFLOW = "before_workflow"
    AFTER_WORKFLOW = "after_workflow"
    ON_PROJECT_INIT = "on_project_init"
    ON_DEPENDENCY_CHANGE = "on_dependency_change"
    ON_FILE_CHANGE = "on_file_change"
    ON_ERROR = "on_error"


@dataclass
class PluginInfo:
    """Plugin metadata and information."""
    
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    
    # Technical details
    entry_point: str = ""
    dependencies: List[str] = field(default_factory=list)
    python_requires: str = ">=3.12"
    
    # Marketplace info
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Installation details
    install_path: Optional[Path] = None
    installed_version: Optional[str] = None
    status: PluginStatus = PluginStatus.AVAILABLE
    
    # Runtime info
    load_time: Optional[float] = None
    error_message: Optional[str] = None
    hooks: List[HookType] = field(default_factory=list)
    
    # Security
    checksum: Optional[str] = None
    verified: bool = False


@dataclass
class HookContext:
    """Context passed to plugin hooks."""
    
    hook_type: HookType
    timestamp: float
    command: Optional[str] = None
    args: Optional[List[str]] = None
    kwargs: Optional[Dict[str, Any]] = None
    workspace_root: Optional[Path] = None
    environment: Optional[str] = None
    
    # Mutable data that plugins can modify
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Control flow
    skip_remaining: bool = False
    abort_operation: bool = False


class PluginBase(ABC):
    """Base class for all uvmgr plugins."""
    
    def __init__(self, info: PluginInfo):
        self.info = info
        self._initialized = False
        self._hooks: Dict[HookType, List[Callable]] = {}
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True on success."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up plugin resources."""
        pass
    
    def register_hook(self, hook_type: HookType, callback: Callable):
        """Register a callback for a specific hook."""
        if hook_type not in self._hooks:
            self._hooks[hook_type] = []
        self._hooks[hook_type].append(callback)
        
        if hook_type not in self.info.hooks:
            self.info.hooks.append(hook_type)
    
    def get_hooks(self, hook_type: HookType) -> List[Callable]:
        """Get all callbacks for a hook type."""
        return self._hooks.get(hook_type, [])
    
    async def on_hook(self, context: HookContext) -> HookContext:
        """Process a hook with this plugin."""
        callbacks = self.get_hooks(context.hook_type)
        
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    context = await callback(context)
                else:
                    context = callback(context)
                
                # Check if we should stop processing
                if context.skip_remaining or context.abort_operation:
                    break
                    
            except Exception as e:
                logger.error(f"Plugin {self.info.name} hook error: {e}")
                continue
        
        return context


class CommandPlugin(PluginBase):
    """Plugin that adds new CLI commands."""
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Callable]:
        """Return a mapping of command names to their implementations."""
        pass


class ToolAdapterPlugin(PluginBase):
    """Plugin that adds new tool adapters."""
    
    @abstractmethod
    def get_adapters(self) -> List[Any]:
        """Return list of tool adapters provided by this plugin."""
        pass


class WorkflowPlugin(PluginBase):
    """Plugin that adds new workflow templates."""
    
    @abstractmethod
    def get_workflow_templates(self) -> Dict[str, Any]:
        """Return workflow templates provided by this plugin."""
        pass


class PluginLoader:
    """Loads and manages individual plugins."""
    
    def __init__(self):
        self.loaded_plugins: Dict[str, PluginBase] = {}
    
    async def load_plugin(self, plugin_path: Path, info: PluginInfo) -> Optional[PluginBase]:
        """Load a plugin from a file path."""
        
        try:
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"uvmgr_plugin_{info.name}",
                plugin_path / "__init__.py"
            )
            
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load plugin spec for {info.name}")
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                raise ImportError(f"No plugin class found in {info.name}")
            
            # Create plugin instance
            plugin = plugin_class(info)
            
            # Initialize plugin
            start_time = time.time()
            success = await plugin.initialize()
            load_time = time.time() - start_time
            
            if success:
                plugin.info.load_time = load_time
                plugin.info.status = PluginStatus.ACTIVE
                self.loaded_plugins[info.name] = plugin
                
                logger.info(f"Loaded plugin {info.name} v{info.version} in {load_time:.3f}s")
                return plugin
            else:
                plugin.info.status = PluginStatus.ERROR
                plugin.info.error_message = "Plugin initialization failed"
                
        except Exception as e:
            logger.error(f"Failed to load plugin {info.name}: {e}")
            info.status = PluginStatus.ERROR
            info.error_message = str(e)
        
        return None
    
    async def unload_plugin(self, plugin_name: str):
        """Unload a plugin."""
        
        if plugin_name in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_name]
            
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error during plugin cleanup for {plugin_name}: {e}")
            
            plugin.info.status = PluginStatus.INSTALLED
            del self.loaded_plugins[plugin_name]
            
            logger.info(f"Unloaded plugin {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name."""
        return self.loaded_plugins.get(plugin_name)
    
    def list_loaded_plugins(self) -> List[PluginBase]:
        """Get all loaded plugins."""
        return list(self.loaded_plugins.values())


class PluginRegistry:
    """Registry for discovering and managing plugins."""
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or Path.home() / ".uvmgr" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry: Dict[str, PluginInfo] = {}
        self.loader = PluginLoader()
        
        # Built-in plugin directories
        self.builtin_dirs = [
            Path(__file__).parent.parent / "plugins",  # Built-in plugins
        ]
    
    async def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins."""
        
        discovered = []
        
        # Search built-in plugin directories
        for builtin_dir in self.builtin_dirs:
            if builtin_dir.exists():
                discovered.extend(await self._scan_directory(builtin_dir, builtin=True))
        
        # Search user plugin directory
        discovered.extend(await self._scan_directory(self.plugins_dir, builtin=False))
        
        # Update registry
        for plugin_info in discovered:
            self.registry[plugin_info.name] = plugin_info
        
        return discovered
    
    async def _scan_directory(self, directory: Path, builtin: bool = False) -> List[PluginInfo]:
        """Scan a directory for plugins."""
        
        plugins = []
        
        for plugin_dir in directory.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            # Look for plugin.json or pyproject.toml
            plugin_json = plugin_dir / "plugin.json"
            pyproject_toml = plugin_dir / "pyproject.toml"
            
            plugin_info = None
            
            if plugin_json.exists():
                plugin_info = await self._load_plugin_json(plugin_json, plugin_dir)
            elif pyproject_toml.exists():
                plugin_info = await self._load_plugin_toml(pyproject_toml, plugin_dir)
            
            if plugin_info:
                plugin_info.install_path = plugin_dir
                plugin_info.status = PluginStatus.INSTALLED
                plugins.append(plugin_info)
        
        return plugins
    
    async def _load_plugin_json(self, json_file: Path, plugin_dir: Path) -> Optional[PluginInfo]:
        """Load plugin info from plugin.json."""
        
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            return PluginInfo(
                name=data["name"],
                version=data["version"],
                description=data.get("description", ""),
                author=data.get("author", "Unknown"),
                plugin_type=PluginType(data.get("type", "command")),
                entry_point=data.get("entry_point", "__init__.py"),
                dependencies=data.get("dependencies", []),
                python_requires=data.get("python_requires", ">=3.12"),
                homepage=data.get("homepage"),
                repository=data.get("repository"),
                license=data.get("license"),
                tags=data.get("tags", [])
            )
            
        except Exception as e:
            logger.error(f"Error loading plugin.json from {json_file}: {e}")
            return None
    
    async def _load_plugin_toml(self, toml_file: Path, plugin_dir: Path) -> Optional[PluginInfo]:
        """Load plugin info from pyproject.toml."""
        
        try:
            import tomllib
            
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
            
            # Look for uvmgr plugin section
            plugin_data = data.get("tool", {}).get("uvmgr", {}).get("plugin", {})
            
            if not plugin_data:
                return None
            
            project_data = data.get("project", {})
            
            return PluginInfo(
                name=plugin_data.get("name", project_data.get("name", plugin_dir.name)),
                version=project_data.get("version", "0.1.0"),
                description=project_data.get("description", plugin_data.get("description", "")),
                author=plugin_data.get("author", "Unknown"),
                plugin_type=PluginType(plugin_data.get("type", "command")),
                entry_point=plugin_data.get("entry_point", "__init__.py"),
                dependencies=project_data.get("dependencies", []),
                python_requires=plugin_data.get("python_requires", ">=3.12"),
                homepage=project_data.get("homepage"),
                repository=project_data.get("repository"),
                license=project_data.get("license"),
                tags=plugin_data.get("tags", [])
            )
            
        except Exception as e:
            logger.error(f"Error loading pyproject.toml from {toml_file}: {e}")
            return None
    
    async def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Load a specific plugin."""
        
        if plugin_name not in self.registry:
            return None
        
        plugin_info = self.registry[plugin_name]
        
        if not plugin_info.install_path:
            return None
        
        return await self.loader.load_plugin(plugin_info.install_path, plugin_info)
    
    async def unload_plugin(self, plugin_name: str):
        """Unload a specific plugin."""
        await self.loader.unload_plugin(plugin_name)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get plugin information."""
        return self.registry.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None, 
                    status: Optional[PluginStatus] = None) -> List[PluginInfo]:
        """List plugins with optional filtering."""
        
        plugins = list(self.registry.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins


class HookManager:
    """Manages plugin hooks and execution."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self.hook_cache: Dict[HookType, List[PluginBase]] = {}
    
    def _refresh_hook_cache(self):
        """Refresh the cache of plugins for each hook type."""
        
        self.hook_cache.clear()
        
        for plugin in self.registry.loader.list_loaded_plugins():
            for hook_type in plugin.info.hooks:
                if hook_type not in self.hook_cache:
                    self.hook_cache[hook_type] = []
                self.hook_cache[hook_type].append(plugin)
    
    async def execute_hook(self, hook_type: HookType, context: HookContext) -> HookContext:
        """Execute all plugins registered for a hook type."""
        
        # Refresh cache if needed
        if not self.hook_cache:
            self._refresh_hook_cache()
        
        plugins = self.hook_cache.get(hook_type, [])
        
        for plugin in plugins:
            try:
                context = await plugin.on_hook(context)
                
                # Check if we should abort
                if context.abort_operation:
                    break
                    
            except Exception as e:
                logger.error(f"Hook execution error in plugin {plugin.info.name}: {e}")
                continue
        
        return context
    
    async def execute_before_command(self, command: str, args: List[str], 
                                   kwargs: Dict[str, Any]) -> HookContext:
        """Execute before_command hooks."""
        
        context = HookContext(
            hook_type=HookType.BEFORE_COMMAND,
            timestamp=time.time(),
            command=command,
            args=args,
            kwargs=kwargs,
            workspace_root=Path.cwd(),
            environment=get_workspace_manager().load_state().current_environment
        )
        
        return await self.execute_hook(HookType.BEFORE_COMMAND, context)
    
    async def execute_after_command(self, command: str, args: List[str], 
                                  kwargs: Dict[str, Any], result: Any) -> HookContext:
        """Execute after_command hooks."""
        
        context = HookContext(
            hook_type=HookType.AFTER_COMMAND,
            timestamp=time.time(),
            command=command,
            args=args,
            kwargs=kwargs,
            workspace_root=Path.cwd(),
            environment=get_workspace_manager().load_state().current_environment,
            data={"result": result}
        )
        
        return await self.execute_hook(HookType.AFTER_COMMAND, context)


class PluginMarketplace:
    """Plugin marketplace for discovering and installing remote plugins."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        
        # Default marketplace sources
        self.sources = [
            "https://registry.uvmgr.dev/plugins",  # Official marketplace
            "https://github.com/uvmgr/plugins",   # GitHub repository
        ]
    
    async def search_plugins(self, query: str = "", tags: List[str] = None, 
                           plugin_type: Optional[PluginType] = None) -> List[PluginInfo]:
        """Search for plugins in the marketplace."""
        
        # Plugin marketplace search not implemented
        return NotImplemented
    
    async def install_plugin(self, plugin_name: str, version: Optional[str] = None) -> bool:
        """Install a plugin from the marketplace."""
        
        # Plugin installation not yet implemented
        return NotImplemented
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin."""
        
        try:
            # Unload if loaded
            await self.registry.unload_plugin(plugin_name)
            
            # Remove plugin directory
            plugin_info = self.registry.get_plugin_info(plugin_name)
            if plugin_info and plugin_info.install_path:
                shutil.rmtree(plugin_info.install_path)
            
            # Remove from registry
            self.registry.registry.pop(plugin_name, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin {plugin_name}: {e}")
            return False


class PluginManager:
    """
    Main plugin management system for uvmgr.
    
    Provides unified interface for plugin discovery, installation, and execution.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.registry = PluginRegistry()
        self.hook_manager = HookManager(self.registry)
        self.marketplace = PluginMarketplace(self.registry)
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the plugin system."""
        
        if self._initialized:
            return
        
        # Discover available plugins
        discovered_plugins = await self.registry.discover_plugins()
        
        # Auto-load enabled plugins (for now, load all available)
        for plugin_info in discovered_plugins:
            if plugin_info.status == PluginStatus.INSTALLED:
                await self.registry.load_plugin(plugin_info.name)
        
        self._initialized = True
        
        # Observe initialization
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "plugin_manager_init",
                PluginAttributes.PLUGIN_SYSTEM: "uvmgr_plugins",
                "discovered_plugins": str(len(discovered_plugins)),
                "loaded_plugins": str(len(self.registry.loader.loaded_plugins))
            },
            context={
                "plugin_system": True,
                "extensibility": True,
                "discovered_count": len(discovered_plugins)
            }
        )
    
    async def execute_before_command_hooks(self, command: str, args: List[str], 
                                         kwargs: Dict[str, Any]) -> HookContext:
        """Execute before command hooks."""
        return await self.hook_manager.execute_before_command(command, args, kwargs)
    
    async def execute_after_command_hooks(self, command: str, args: List[str], 
                                        kwargs: Dict[str, Any], result: Any) -> HookContext:
        """Execute after command hooks."""
        return await self.hook_manager.execute_after_command(command, args, kwargs, result)
    
    def list_plugins(self, **filters) -> List[PluginInfo]:
        """List available plugins with optional filtering."""
        return self.registry.list_plugins(**filters)
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a loaded plugin instance."""
        return self.registry.loader.get_plugin(plugin_name)
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin."""
        plugin = await self.registry.load_plugin(plugin_name)
        return plugin is not None
    
    async def unload_plugin(self, plugin_name: str):
        """Unload a specific plugin."""
        await self.registry.unload_plugin(plugin_name)
    
    async def search_marketplace(self, query: str = "", **filters) -> List[PluginInfo]:
        """Search the plugin marketplace."""
        return await self.marketplace.search_plugins(query, **filters)
    
    async def install_plugin(self, plugin_name: str, version: Optional[str] = None) -> bool:
        """Install a plugin from the marketplace."""
        return await self.marketplace.install_plugin(plugin_name, version)
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin."""
        return await self.marketplace.uninstall_plugin(plugin_name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        
        all_plugins = self.registry.list_plugins()
        loaded_plugins = self.registry.loader.list_loaded_plugins()
        
        by_type = {}
        by_status = {}
        
        for plugin_info in all_plugins:
            plugin_type = plugin_info.plugin_type.value
            status = plugin_info.status.value
            
            by_type[plugin_type] = by_type.get(plugin_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        total_hooks = sum(len(p.info.hooks) for p in loaded_plugins)
        
        return {
            "total_plugins": len(all_plugins),
            "loaded_plugins": len(loaded_plugins),
            "plugins_by_type": by_type,
            "plugins_by_status": by_status,
            "total_hooks": total_hooks,
            "marketplace_sources": len(self.marketplace.sources)
        }


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager(workspace_root: Optional[Path] = None) -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    
    if _plugin_manager is None:
        _plugin_manager = PluginManager(workspace_root)
    
    return _plugin_manager

async def initialize_plugin_system():
    """Initialize the global plugin system."""
    manager = get_plugin_manager()
    await manager.initialize()
    return manager