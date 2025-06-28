"""
uvmgr.commands.plugins
=====================

Plugin system commands for discovering, managing, and extending uvmgr functionality.

This command module addresses the critical extensibility gap by providing:

• **Plugin discovery**: Automatically find and register available plugins
• **Plugin management**: Install, uninstall, enable, and disable plugins
• **Marketplace access**: Search and install plugins from remote sources
• **Hook system**: Manage plugin hooks and integrations
• **Plugin development**: Tools for creating and testing plugins

Example
-------
    $ uvmgr plugins list                         # List all available plugins
    $ uvmgr plugins search docker               # Search marketplace for Docker plugins
    $ uvmgr plugins install uvmgr-docker-enhanced  # Install a plugin
    $ uvmgr plugins load my-plugin              # Load a specific plugin
    $ uvmgr plugins hooks                       # Show active hooks
    $ uvmgr plugins status                       # Show plugin system status

See Also
--------
- :mod:`uvmgr.core.plugins` : Plugin system implementation
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import asyncio
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, PluginAttributes, PluginOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.plugins import (
    get_plugin_manager,
    initialize_plugin_system,
    PluginType,
    PluginStatus,
    HookType
)

app = typer.Typer(help="Plugin system management")


@app.command()
@instrument_command("plugins_list", track_args=True)
def list_plugins(
    plugin_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by plugin type"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List all available plugins."""
    
    async def _list():
        manager = get_plugin_manager()
        await manager.initialize()
        
        filters = {}
        if plugin_type:
            try:
                filters["plugin_type"] = PluginType(plugin_type)
            except ValueError:
                typer.echo(f"❌ Invalid plugin type: {plugin_type}")
                raise typer.Exit(1)
        
        if status:
            try:
                filters["status"] = PluginStatus(status)
            except ValueError:
                typer.echo(f"❌ Invalid status: {status}")
                raise typer.Exit(1)
        
        return manager.list_plugins(**filters)
    
    plugins = asyncio.run(_list())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_list",
        PluginAttributes.PLUGIN_SYSTEM: "uvmgr_plugins",
        "plugins_found": str(len(plugins)),
        "type_filter": plugin_type or "none",
        "status_filter": status or "none"
    })
    
    if json_output:
        plugin_data = []
        for plugin in plugins:
            plugin_data.append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "type": plugin.plugin_type.value,
                "status": plugin.status.value,
                "hooks": [h.value for h in plugin.hooks],
                "install_path": str(plugin.install_path) if plugin.install_path else None,
                "load_time": plugin.load_time,
                "verified": plugin.verified
            })
        dump_json(plugin_data)
        return
    
    if not plugins:
        typer.echo("📦 No plugins found")
        if plugin_type or status:
            typer.echo("💡 Try adjusting your filters or run 'uvmgr plugins search' to find plugins")
        else:
            typer.echo("💡 Run 'uvmgr plugins search' to discover plugins from the marketplace")
        return
    
    typer.echo("📦 Available Plugins")
    typer.echo("=" * 30)
    
    # Group by status
    by_status: Dict[PluginStatus, List[Any]] = {}
    for plugin in plugins:
        if plugin.status not in by_status:
            by_status[plugin.status] = []
        by_status[plugin.status].append(plugin)
    
    # Show loaded/active plugins first
    status_order = [PluginStatus.ACTIVE, PluginStatus.INSTALLED, PluginStatus.AVAILABLE, PluginStatus.ERROR, PluginStatus.DISABLED]
    
    for status in status_order:
        if status not in by_status:
            continue
        
        status_plugins = by_status[status]
        status_icon = {
            PluginStatus.ACTIVE: "✅",
            PluginStatus.INSTALLED: "📦",
            PluginStatus.AVAILABLE: "🔍",
            PluginStatus.ERROR: "❌",
            PluginStatus.DISABLED: "⏸️"
        }.get(status, "📦")
        
        typer.echo(f"\n{status_icon} {status.value.title()} ({len(status_plugins)}):")
        
        for plugin in status_plugins:
            type_icon = {
                PluginType.COMMAND: "💻",
                PluginType.TOOL_ADAPTER: "🔧",
                PluginType.WORKFLOW: "🔄",
                PluginType.AI_ENHANCEMENT: "🤖",
                PluginType.INTEGRATION: "🔗",
                PluginType.THEME: "🎨",
                PluginType.MIDDLEWARE: "⚙️"
            }.get(plugin.plugin_type, "📦")
            
            name_color = "green" if plugin.status == PluginStatus.ACTIVE else "white"
            typer.echo(f"  {type_icon} {colour(plugin.name, name_color)} v{plugin.version}")
            typer.echo(f"     📝 {plugin.description}")
            typer.echo(f"     👤 By {plugin.author}")
            
            if plugin.status == PluginStatus.ACTIVE and plugin.load_time:
                typer.echo(f"     ⏱️  Loaded in {plugin.load_time:.3f}s")
            
            if plugin.hooks:
                hook_count = len(plugin.hooks)
                typer.echo(f"     🪝 {hook_count} hook(s): {', '.join([h.value for h in plugin.hooks[:3]])}")
                if hook_count > 3:
                    typer.echo(f"        (+{hook_count - 3} more)")
            
            if plugin.tags:
                typer.echo(f"     🏷️  Tags: {', '.join(plugin.tags)}")
            
            if plugin.status == PluginStatus.ERROR and plugin.error_message:
                typer.echo(f"     💥 Error: {plugin.error_message[:80]}...")
    
    typer.echo(f"\n📊 Total: {len(plugins)} plugins")
    
    add_span_event("plugins.list_displayed", {
        "plugins_count": len(plugins),
        "filters_applied": bool(plugin_type or status)
    })


@app.command()
@instrument_command("plugins_search", track_args=True)
def search(
    query: str = typer.Argument("", help="Search query"),
    plugin_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by plugin type"),
    tags: List[str] = typer.Option([], "--tag", help="Filter by tags"),
    verified_only: bool = typer.Option(False, "--verified", help="Show only verified plugins"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Search for plugins in the marketplace."""
    
    async def _search():
        manager = get_plugin_manager()
        await manager.initialize()
        
        filters = {}
        if plugin_type:
            try:
                filters["plugin_type"] = PluginType(plugin_type)
            except ValueError:
                typer.echo(f"❌ Invalid plugin type: {plugin_type}")
                raise typer.Exit(1)
        
        if tags:
            filters["tags"] = tags
        
        return await manager.search_marketplace(query, **filters)
    
    plugins = asyncio.run(_search())
    
    # Apply verified filter
    if verified_only:
        plugins = [p for p in plugins if p.verified]
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_search",
        PluginAttributes.PLUGIN_SYSTEM: "uvmgr_marketplace",
        "search_query": query,
        "results_found": str(len(plugins)),
        "verified_only": str(verified_only)
    })
    
    if json_output:
        search_data = {
            "query": query,
            "results_count": len(plugins),
            "plugins": []
        }
        
        for plugin in plugins:
            search_data["plugins"].append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "type": plugin.plugin_type.value,
                "repository": plugin.repository,
                "tags": plugin.tags,
                "verified": plugin.verified
            })
        
        dump_json(search_data)
        return
    
    if not plugins:
        typer.echo(f"🔍 No plugins found for query: '{query}'")
        if verified_only:
            typer.echo("💡 Try removing --verified filter to see more results")
        typer.echo("💡 Check your spelling or try broader search terms")
        return
    
    typer.echo(f"🔍 Marketplace Search Results: '{query}'")
    typer.echo("=" * 50)
    typer.echo(f"📊 Found {len(plugins)} plugin(s)")
    
    for i, plugin in enumerate(plugins, 1):
        type_icon = {
            PluginType.COMMAND: "💻",
            PluginType.TOOL_ADAPTER: "🔧", 
            PluginType.WORKFLOW: "🔄",
            PluginType.AI_ENHANCEMENT: "🤖",
            PluginType.INTEGRATION: "🔗",
            PluginType.THEME: "🎨",
            PluginType.MIDDLEWARE: "⚙️"
        }.get(plugin.plugin_type, "📦")
        
        verified_icon = "✅" if plugin.verified else "⚠️"
        
        typer.echo(f"\n{i}. {type_icon} {colour(plugin.name, 'green')} v{plugin.version} {verified_icon}")
        typer.echo(f"   📝 {plugin.description}")
        typer.echo(f"   👤 By {plugin.author}")
        
        if plugin.repository:
            typer.echo(f"   🔗 {plugin.repository}")
        
        if plugin.tags:
            typer.echo(f"   🏷️  Tags: {', '.join(plugin.tags)}")
        
        if not plugin.verified:
            typer.echo(f"   ⚠️  Unverified plugin - install at your own risk")
    
    typer.echo(f"\n💡 Install with: uvmgr plugins install <plugin-name>")
    
    add_span_event("plugins.search_completed", {
        "query": query,
        "results_count": len(plugins)
    })


@app.command()
@instrument_command("plugins_install", track_args=True)
def install(
    plugin_name: str = typer.Argument(..., help="Name of the plugin to install"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version to install"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if already installed")
):
    """Install a plugin from the marketplace."""
    
    async def _install():
        manager = get_plugin_manager()
        await manager.initialize()
        
        # Check if already installed
        existing_plugin = manager.registry.get_plugin_info(plugin_name)
        if existing_plugin and existing_plugin.status in [PluginStatus.INSTALLED, PluginStatus.ACTIVE] and not force:
            typer.echo(f"❌ Plugin '{plugin_name}' is already installed")
            typer.echo("Use --force to reinstall")
            return False
        
        return await manager.install_plugin(plugin_name, version)
    
    success = asyncio.run(_install())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_install",
        PluginAttributes.PLUGIN_NAME: plugin_name,
        PluginAttributes.PLUGIN_VERSION: version or "latest",
        "success": str(success),
        "force_install": str(force)
    })
    
    if success:
        typer.echo(f"✅ Successfully installed plugin: {colour(plugin_name, 'green')}")
        if version:
            typer.echo(f"📦 Version: {version}")
        typer.echo("💡 Run 'uvmgr plugins load' to activate the plugin")
        
        add_span_event("plugins.install_success", {
            "plugin_name": plugin_name,
            "version": version
        })
    else:
        typer.echo(f"❌ Failed to install plugin: {plugin_name}")
        typer.echo("💡 Check your network connection and plugin name")
        raise typer.Exit(1)


@app.command()
@instrument_command("plugins_uninstall", track_args=True)
def uninstall(
    plugin_name: str = typer.Argument(..., help="Name of the plugin to uninstall"),
    force: bool = typer.Option(False, "--force", "-f", help="Force uninstall even if active")
):
    """Uninstall a plugin."""
    
    async def _uninstall():
        manager = get_plugin_manager()
        await manager.initialize()
        
        # Check if plugin exists
        plugin_info = manager.registry.get_plugin_info(plugin_name)
        if not plugin_info:
            typer.echo(f"❌ Plugin '{plugin_name}' not found")
            return False
        
        # Check if plugin is active
        if plugin_info.status == PluginStatus.ACTIVE and not force:
            typer.echo(f"❌ Plugin '{plugin_name}' is currently active")
            typer.echo("Use --force to uninstall anyway or unload it first")
            return False
        
        return await manager.uninstall_plugin(plugin_name)
    
    success = asyncio.run(_uninstall())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_uninstall",
        PluginAttributes.PLUGIN_NAME: plugin_name,
        "success": str(success),
        "force_uninstall": str(force)
    })
    
    if success:
        typer.echo(f"✅ Successfully uninstalled plugin: {plugin_name}")
        
        add_span_event("plugins.uninstall_success", {
            "plugin_name": plugin_name
        })
    else:
        typer.echo(f"❌ Failed to uninstall plugin: {plugin_name}")
        raise typer.Exit(1)


@app.command()
@instrument_command("plugins_load", track_args=True)
def load(
    plugin_name: str = typer.Argument(..., help="Name of the plugin to load")
):
    """Load and activate a specific plugin."""
    
    async def _load():
        manager = get_plugin_manager()
        await manager.initialize()
        return await manager.load_plugin(plugin_name)
    
    success = asyncio.run(_load())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_load",
        PluginAttributes.PLUGIN_NAME: plugin_name,
        "success": str(success)
    })
    
    if success:
        typer.echo(f"✅ Successfully loaded plugin: {colour(plugin_name, 'green')}")
        
        # Show plugin info
        manager = get_plugin_manager()
        plugin = manager.get_plugin(plugin_name)
        if plugin:
            typer.echo(f"📦 Version: {plugin.info.version}")
            typer.echo(f"📝 {plugin.info.description}")
            if plugin.info.hooks:
                typer.echo(f"🪝 Registered {len(plugin.info.hooks)} hook(s)")
        
        add_span_event("plugins.load_success", {
            "plugin_name": plugin_name
        })
    else:
        typer.echo(f"❌ Failed to load plugin: {plugin_name}")
        typer.echo("💡 Check if the plugin is installed and compatible")
        raise typer.Exit(1)


@app.command()
@instrument_command("plugins_unload", track_args=True)
def unload(
    plugin_name: str = typer.Argument(..., help="Name of the plugin to unload")
):
    """Unload a specific plugin."""
    
    async def _unload():
        manager = get_plugin_manager()
        await manager.initialize()
        await manager.unload_plugin(plugin_name)
        return True
    
    asyncio.run(_unload())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_unload",
        PluginAttributes.PLUGIN_NAME: plugin_name
    })
    
    typer.echo(f"✅ Successfully unloaded plugin: {plugin_name}")
    
    add_span_event("plugins.unload_success", {
        "plugin_name": plugin_name
    })


@app.command()
@instrument_command("plugins_hooks", track_args=True)
def hooks(
    hook_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by hook type"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show active plugin hooks."""
    
    async def _get_hooks():
        manager = get_plugin_manager()
        await manager.initialize()
        
        loaded_plugins = manager.registry.loader.list_loaded_plugins()
        
        hooks_data = []
        for plugin in loaded_plugins:
            for hook in plugin.info.hooks:
                if not hook_type or hook.value == hook_type:
                    hooks_data.append({
                        "plugin": plugin.info.name,
                        "hook_type": hook.value,
                        "plugin_version": plugin.info.version,
                        "plugin_type": plugin.info.plugin_type.value
                    })
        
        return hooks_data
    
    hooks_data = asyncio.run(_get_hooks())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_hooks",
        "hooks_found": str(len(hooks_data)),
        "hook_type_filter": hook_type or "none"
    })
    
    if json_output:
        dump_json(hooks_data)
        return
    
    if not hooks_data:
        typer.echo("🪝 No active plugin hooks found")
        if hook_type:
            typer.echo(f"🔍 No hooks of type: {hook_type}")
        else:
            typer.echo("💡 Load some plugins to see their hooks")
        return
    
    typer.echo("🪝 Active Plugin Hooks")
    typer.echo("=" * 30)
    
    # Group by hook type
    by_hook_type: Dict[str, List[Dict]] = {}
    for hook_data in hooks_data:
        hook_type_name = hook_data["hook_type"]
        if hook_type_name not in by_hook_type:
            by_hook_type[hook_type_name] = []
        by_hook_type[hook_type_name].append(hook_data)
    
    for hook_type_name, hooks in sorted(by_hook_type.items()):
        hook_icon = {
            "before_command": "⬅️",
            "after_command": "➡️",
            "before_workflow": "🔄",
            "after_workflow": "✅",
            "on_project_init": "🏗️",
            "on_dependency_change": "📦",
            "on_file_change": "📝",
            "on_error": "🚨"
        }.get(hook_type_name, "🪝")
        
        typer.echo(f"\n{hook_icon} {hook_type_name} ({len(hooks)} plugin(s)):")
        
        for hook_data in hooks:
            type_icon = {
                "command": "💻",
                "tool_adapter": "🔧",
                "workflow": "🔄",
                "ai_enhancement": "🤖",
                "integration": "🔗",
                "theme": "🎨",
                "middleware": "⚙️"
            }.get(hook_data["plugin_type"], "📦")
            
            typer.echo(f"  {type_icon} {hook_data['plugin']} v{hook_data['plugin_version']}")
    
    total_hooks = len(hooks_data)
    unique_plugins = len(set(h["plugin"] for h in hooks_data))
    
    typer.echo(f"\n📊 Summary: {total_hooks} hooks from {unique_plugins} plugin(s)")


@app.command()
@instrument_command("plugins_status", track_args=True)
def status(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show plugin system status and statistics."""
    
    async def _get_status():
        manager = get_plugin_manager()
        await manager.initialize()
        return manager.get_statistics()
    
    stats = asyncio.run(_get_status())
    
    add_span_attributes({
        CliAttributes.COMMAND: "plugins_status",
        PluginAttributes.PLUGIN_SYSTEM: "uvmgr_plugins"
    })
    
    if json_output:
        dump_json(stats)
        return
    
    typer.echo("📦 Plugin System Status")
    typer.echo("=" * 30)
    
    # Overview
    typer.echo(f"📊 Overview:")
    typer.echo(f"  📦 Total plugins: {stats['total_plugins']}")
    typer.echo(f"  ✅ Loaded plugins: {stats['loaded_plugins']}")
    typer.echo(f"  🪝 Total hooks: {stats['total_hooks']}")
    typer.echo(f"  🛒 Marketplace sources: {stats['marketplace_sources']}")
    
    # Plugin types
    if stats["plugins_by_type"]:
        typer.echo(f"\n🏷️  Plugins by Type:")
        for plugin_type, count in stats["plugins_by_type"].items():
            type_icon = {
                "command": "💻",
                "tool_adapter": "🔧",
                "workflow": "🔄", 
                "ai_enhancement": "🤖",
                "integration": "🔗",
                "theme": "🎨",
                "middleware": "⚙️"
            }.get(plugin_type, "📦")
            
            typer.echo(f"  {type_icon} {plugin_type.replace('_', ' ').title()}: {count}")
    
    # Plugin status
    if stats["plugins_by_status"]:
        typer.echo(f"\n📊 Plugins by Status:")
        for status, count in stats["plugins_by_status"].items():
            status_icon = {
                "active": "✅",
                "installed": "📦",
                "available": "🔍",
                "error": "❌",
                "disabled": "⏸️"
            }.get(status, "📦")
            
            typer.echo(f"  {status_icon} {status.title()}: {count}")
    
    # Health check
    health_status = "🟢 Healthy" if stats["loaded_plugins"] > 0 else "🟡 No plugins loaded"
    typer.echo(f"\n🏥 System Health: {health_status}")
    
    if stats["loaded_plugins"] == 0:
        typer.echo("💡 Install and load plugins to extend uvmgr functionality")
    
    add_span_event("plugins.status_displayed", {
        "total_plugins": stats["total_plugins"],
        "loaded_plugins": stats["loaded_plugins"]
    })