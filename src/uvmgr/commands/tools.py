"""
uvmgr.commands.tools
===================

Universal tool integration commands that provide unified access to external development tools.

This command module addresses the critical gap in uvmgr's tool integration by providing:

• **Universal tool interface**: Execute operations across different tools with unified commands
• **Tool discovery**: Automatically detect and configure available development tools
• **Context-aware routing**: Intelligent tool selection based on project context
• **Tool health monitoring**: Status checks and health monitoring for integrated tools
• **Execution history**: Track and analyze tool usage patterns

Example
-------
    $ uvmgr tools scan                           # Discover available tools
    $ uvmgr tools status                         # Show tool health status
    $ uvmgr tools exec docker build .           # Execute Docker build
    $ uvmgr tools exec git commit -m "message"  # Execute Git commit
    $ uvmgr tools route build                   # Show which tool would handle build
    $ uvmgr tools history                        # Show recent tool executions

See Also
--------
- :mod:`uvmgr.core.integrations` : Universal tool integration implementation
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import asyncio
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, ToolAttributes, ToolOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.integrations import (
    get_tool_integration_engine,
    initialize_tool_integration,
    execute_universal_operation,
    ToolCategory,
    ToolStatus
)

app = typer.Typer(help="Universal tool integration commands")


@app.command()
@instrument_command("tools_scan", track_args=True)
def scan(
    force: bool = typer.Option(False, "--force", "-f", help="Force rescan even if cached"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Scan and discover available development tools."""
    
    async def _scan():
        engine = get_tool_integration_engine()
        return await engine.initialize()
    
    # Run the async scan
    available_tools = asyncio.run(_scan())
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_scan",
        ToolAttributes.OPERATION: "discovery",
        "tools_found": str(len(available_tools)),
        "force_scan": str(force)
    })
    
    if json_output:
        tool_data = {}
        for tool_name, tool_info in available_tools.items():
            tool_data[tool_name] = {
                "category": tool_info.category.value,
                "version": tool_info.version,
                "status": tool_info.status.value,
                "capabilities": tool_info.capabilities
            }
        dump_json(tool_data)
        return
    
    typer.echo("🔧 Development Tools Discovery")
    typer.echo("=" * 40)
    
    if not available_tools:
        typer.echo("❌ No development tools found")
        typer.echo("💡 Install tools like Docker, Git, Node.js to expand capabilities")
        return
    
    # Group by category
    by_category: Dict[ToolCategory, List[Any]] = {}
    for tool_info in available_tools.values():
        if tool_info.category not in by_category:
            by_category[tool_info.category] = []
        by_category[tool_info.category].append(tool_info)
    
    for category, tools in by_category.items():
        category_icon = {
            ToolCategory.CONTAINER: "🐳",
            ToolCategory.VERSION_CONTROL: "📝",
            ToolCategory.PACKAGE_MANAGER: "📦",
            ToolCategory.BUILD_SYSTEM: "🔨",
            ToolCategory.DATABASE: "🗄️",
            ToolCategory.TESTING: "🧪",
            ToolCategory.DEPLOYMENT: "🚀",
            ToolCategory.CLOUD: "☁️"
        }.get(category, "🔧")
        
        typer.echo(f"\n{category_icon} {category.value.replace('_', ' ').title()}:")
        
        for tool in tools:
            status_icon = "✅" if tool.status == ToolStatus.AVAILABLE else "❌"
            version_info = f" v{tool.version}" if tool.version else ""
            capabilities_count = len(tool.capabilities)
            
            typer.echo(f"  {status_icon} {tool.name}{version_info}")
            typer.echo(f"     📋 {capabilities_count} capabilities")
            
            if tool.capabilities:
                cap_preview = ", ".join(tool.capabilities[:3])
                if len(tool.capabilities) > 3:
                    cap_preview += f" (+{len(tool.capabilities) - 3} more)"
                typer.echo(f"     🎯 {cap_preview}")
    
    total_capabilities = sum(len(tool.capabilities) for tool in available_tools.values())
    typer.echo(f"\n📊 Summary: {len(available_tools)} tools, {total_capabilities} total capabilities")
    
    add_span_event("tools.scan_completed", {
        "tools_count": len(available_tools),
        "capabilities_count": total_capabilities
    })


@app.command()
@instrument_command("tools_status", track_args=True)
def status(
    tool_name: Optional[str] = typer.Argument(None, help="Specific tool to check"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show status and health of integrated tools."""
    
    engine = get_tool_integration_engine()
    
    if tool_name:
        # Check specific tool
        async def _check_tool():
            return await engine.check_tool_availability(tool_name)
        
        is_available = asyncio.run(_check_tool())
        
        if json_output:
            dump_json({
                "tool": tool_name,
                "available": is_available,
                "capabilities": engine.get_tool_capabilities(tool_name)
            })
            return
        
        status_icon = "✅" if is_available else "❌"
        status_text = "Available" if is_available else "Not Available"
        
        typer.echo(f"{status_icon} {tool_name}: {status_text}")
        
        if is_available and detailed:
            capabilities = engine.get_tool_capabilities(tool_name)
            typer.echo(f"📋 Capabilities: {', '.join(capabilities)}")
        
        return
    
    # Show all tools status
    available_tools = engine.get_available_tools()
    all_tools = engine.registry.list_tools()
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_status",
        "available_tools": str(len(available_tools)),
        "total_tools": str(len(all_tools))
    })
    
    if json_output:
        status_data = {
            "available_tools": len(available_tools),
            "total_tools": len(all_tools),
            "tools": {}
        }
        
        for tool_info in all_tools:
            status_data["tools"][tool_info.name] = {
                "status": tool_info.status.value,
                "category": tool_info.category.value,
                "version": tool_info.version,
                "capabilities": tool_info.capabilities
            }
        
        dump_json(status_data)
        return
    
    typer.echo("🔧 Tool Integration Status")
    typer.echo("=" * 30)
    
    # Summary
    available_count = len(available_tools)
    total_count = len(all_tools)
    typer.echo(f"📊 Tools: {available_count}/{total_count} available")
    
    if available_count == 0:
        typer.echo("❌ No tools are currently available")
        typer.echo("💡 Run 'uvmgr tools scan' to discover tools")
        return
    
    # Show available tools
    typer.echo(f"\n✅ Available Tools ({available_count}):")
    for tool_info in available_tools:
        version_info = f" v{tool_info.version}" if tool_info.version else ""
        capabilities_count = len(tool_info.capabilities)
        
        typer.echo(f"  🔧 {tool_info.name}{version_info}")
        if detailed:
            typer.echo(f"     📂 Category: {tool_info.category.value}")
            typer.echo(f"     📋 Capabilities: {capabilities_count}")
            if tool_info.capabilities:
                typer.echo(f"     🎯 {', '.join(tool_info.capabilities[:5])}")
    
    # Show unavailable tools
    unavailable_tools = [t for t in all_tools if t.status != ToolStatus.AVAILABLE]
    if unavailable_tools:
        typer.echo(f"\n❌ Unavailable Tools ({len(unavailable_tools)}):")
        for tool_info in unavailable_tools:
            reason = {
                ToolStatus.NOT_FOUND: "not installed",
                ToolStatus.VERSION_INCOMPATIBLE: "incompatible version",
                ToolStatus.CONFIG_ERROR: "configuration error"
            }.get(tool_info.status, "unknown issue")
            
            typer.echo(f"  ❌ {tool_info.name}: {reason}")
    
    # Statistics
    if detailed:
        stats = engine.get_statistics()
        typer.echo(f"\n📈 Integration Statistics:")
        typer.echo(f"  🔧 Registered tools: {stats['registered_tools']}")
        typer.echo(f"  ✅ Available tools: {stats['available_tools']}")
        typer.echo(f"  🎯 Total capabilities: {stats['capabilities_count']}")
        typer.echo(f"  📂 Categories: {stats['categories_count']}")
        
        if stats['total_executions'] > 0:
            typer.echo(f"  📊 Executions: {stats['total_executions']} (success rate: {stats['success_rate']*100:.1f}%)")


@app.command()
@instrument_command("tools_exec", track_args=True)
def exec_command(
    tool_operation: List[str] = typer.Argument(..., help="Tool and operation (e.g., 'docker build .')"),
    working_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Working directory"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Command timeout in seconds"),
    env_vars: List[str] = typer.Option([], "--env", "-e", help="Environment variables (KEY=VALUE)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Execute a command using the appropriate integrated tool."""
    
    if len(tool_operation) < 2:
        typer.echo("❌ Please specify tool and operation (e.g., 'docker build .')")
        raise typer.Exit(1)
    
    tool_name = tool_operation[0]
    operation = tool_operation[1]
    args = tool_operation[2:] if len(tool_operation) > 2 else []
    
    # Parse environment variables
    environment_vars = {}
    for env_var in env_vars:
        if "=" in env_var:
            key, value = env_var.split("=", 1)
            environment_vars[key] = value
    
    async def _execute():
        return await execute_universal_operation(
            operation=operation,
            args=args,
            working_directory=working_dir,
            timeout=timeout,
            environment_vars=environment_vars,
            context={"requested_tool": tool_name}
        )
    
    result = asyncio.run(_execute())
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_exec",
        ToolAttributes.OPERATION: operation,
        ToolAttributes.TOOL_NAME: result.tool_name,
        "success": str(result.success),
        "return_code": str(result.return_code),
        "duration": str(result.duration)
    })
    
    if json_output:
        dump_json({
            "success": result.success,
            "return_code": result.return_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": result.duration,
            "tool_used": result.tool_name,
            "command": result.command
        })
        return
    
    # Show execution result
    status_icon = "✅" if result.success else "❌"
    duration_info = f" ({result.duration:.2f}s)"
    
    typer.echo(f"{status_icon} {result.command}{duration_info}")
    typer.echo(f"🔧 Tool used: {result.tool_name}")
    
    if result.stdout:
        typer.echo(f"\n📤 Output:")
        typer.echo(result.stdout)
    
    if result.stderr:
        typer.echo(f"\n🚨 Errors:")
        typer.echo(result.stderr)
    
    if not result.success:
        typer.echo(f"\n❌ Command failed with exit code {result.return_code}")
        if result.error_message:
            typer.echo(f"💥 Error: {result.error_message}")
        raise typer.Exit(result.return_code)
    
    add_span_event("tools.command_executed", {
        "tool": result.tool_name,
        "operation": operation,
        "success": result.success
    })


@app.command()
@instrument_command("tools_route", track_args=True)
def route(
    operation: str = typer.Argument(..., help="Operation to route (e.g., 'build', 'test', 'deploy')"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show which tool would be used for a given operation."""
    
    async def _route():
        engine = get_tool_integration_engine()
        return await engine.router.route_operation(operation)
    
    adapter = asyncio.run(_route())
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_route",
        ToolAttributes.OPERATION: operation,
        "tool_found": str(adapter is not None)
    })
    
    if json_output:
        if adapter:
            dump_json({
                "operation": operation,
                "tool": adapter.tool_info.name,
                "category": adapter.tool_info.category.value,
                "capabilities": adapter.get_capabilities()
            })
        else:
            dump_json({
                "operation": operation,
                "tool": None,
                "error": "No suitable tool found"
            })
        return
    
    if adapter:
        typer.echo(f"🎯 Operation '{operation}' → {colour(adapter.tool_info.name, 'green')}")
        typer.echo(f"📂 Category: {adapter.tool_info.category.value}")
        
        capabilities = adapter.get_capabilities()
        if capabilities:
            typer.echo(f"🔧 Capabilities: {', '.join(capabilities[:5])}")
            if len(capabilities) > 5:
                typer.echo(f"   (+{len(capabilities) - 5} more)")
    else:
        typer.echo(f"❌ No tool available for operation '{operation}'")
        typer.echo("💡 Try running 'uvmgr tools scan' to discover available tools")
        raise typer.Exit(1)


@app.command()
@instrument_command("tools_history", track_args=True)
def history(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of recent executions to show"),
    tool_name: Optional[str] = typer.Option(None, "--tool", "-t", help="Filter by tool name"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show recent tool execution history."""
    
    engine = get_tool_integration_engine()
    executions = engine.get_execution_history(limit)
    
    # Filter by tool if specified
    if tool_name:
        executions = [e for e in executions if e.tool_name == tool_name]
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_history",
        "executions_found": str(len(executions)),
        "tool_filter": tool_name or "none"
    })
    
    if json_output:
        execution_data = []
        for execution in executions:
            execution_data.append({
                "tool": execution.tool_name,
                "command": execution.command,
                "success": execution.success,
                "return_code": execution.return_code,
                "duration": execution.duration,
                "stdout": execution.stdout[:200] + "..." if len(execution.stdout) > 200 else execution.stdout,
                "stderr": execution.stderr[:200] + "..." if len(execution.stderr) > 200 else execution.stderr
            })
        dump_json(execution_data)
        return
    
    if not executions:
        typer.echo("📋 No tool executions found")
        if tool_name:
            typer.echo(f"🔍 No executions for tool: {tool_name}")
        else:
            typer.echo("💡 Run some commands with 'uvmgr tools exec' to see history")
        return
    
    typer.echo(f"📋 Tool Execution History (last {len(executions)})")
    typer.echo("=" * 50)
    
    for execution in reversed(executions):  # Show most recent first
        status_icon = "✅" if execution.success else "❌"
        duration_info = f"({execution.duration:.2f}s)"
        
        typer.echo(f"{status_icon} {execution.command} {duration_info}")
        typer.echo(f"   🔧 Tool: {execution.tool_name}")
        
        if not execution.success:
            typer.echo(f"   ❌ Exit code: {execution.return_code}")
            if execution.error_message:
                typer.echo(f"   💥 Error: {execution.error_message[:100]}...")
        
        typer.echo()  # Empty line for readability
    
    # Show statistics
    total_executions = len(executions)
    successful_executions = len([e for e in executions if e.success])
    
    typer.echo(f"📊 Statistics: {successful_executions}/{total_executions} successful " +
               f"({successful_executions/max(1, total_executions)*100:.1f}%)")


@app.command()
@instrument_command("tools_capabilities", track_args=True)
def capabilities(
    capability: Optional[str] = typer.Argument(None, help="Specific capability to search for"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List available capabilities and which tools provide them."""
    
    engine = get_tool_integration_engine()
    
    add_span_attributes({
        CliAttributes.COMMAND: "tools_capabilities",
        "capability_filter": capability or "none"
    })
    
    if capability:
        # Show tools that provide specific capability
        adapters = engine.registry.get_adapters_by_capability(capability)
        
        if json_output:
            tool_data = []
            for adapter in adapters:
                tool_data.append({
                    "name": adapter.tool_info.name,
                    "category": adapter.tool_info.category.value,
                    "status": adapter.tool_info.status.value,
                    "version": adapter.tool_info.version
                })
            dump_json({
                "capability": capability,
                "tools": tool_data
            })
            return
        
        if not adapters:
            typer.echo(f"❌ No tools provide capability: {capability}")
            return
        
        typer.echo(f"🎯 Capability: {colour(capability, 'green')}")
        typer.echo(f"🔧 Provided by {len(adapters)} tool(s):")
        
        for adapter in adapters:
            status_icon = "✅" if adapter.tool_info.status == ToolStatus.AVAILABLE else "❌"
            version_info = f" v{adapter.tool_info.version}" if adapter.tool_info.version else ""
            
            typer.echo(f"  {status_icon} {adapter.tool_info.name}{version_info}")
        
        return
    
    # Show all capabilities
    capabilities_map = engine.registry.capabilities_map
    
    if json_output:
        dump_json(capabilities_map)
        return
    
    typer.echo("🎯 Available Capabilities")
    typer.echo("=" * 30)
    
    if not capabilities_map:
        typer.echo("❌ No capabilities registered")
        typer.echo("💡 Run 'uvmgr tools scan' to discover tools and capabilities")
        return
    
    for capability_name, tool_names in sorted(capabilities_map.items()):
        available_tools = []
        unavailable_tools = []
        
        for tool_name in tool_names:
            adapter = engine.registry.get_adapter(tool_name)
            if adapter and adapter.tool_info.status == ToolStatus.AVAILABLE:
                available_tools.append(tool_name)
            else:
                unavailable_tools.append(tool_name)
        
        status_info = ""
        if available_tools:
            status_info = f"✅ {', '.join(available_tools)}"
        if unavailable_tools:
            if status_info:
                status_info += f" (❌ {', '.join(unavailable_tools)})"
            else:
                status_info = f"❌ {', '.join(unavailable_tools)}"
        
        typer.echo(f"  🎯 {capability_name}: {status_info}")
    
    total_capabilities = len(capabilities_map)
    available_capabilities = len([cap for cap, tools in capabilities_map.items()
                                if any(engine.registry.get_adapter(t) and 
                                      engine.registry.get_adapter(t).tool_info.status == ToolStatus.AVAILABLE
                                      for t in tools)])
    
    typer.echo(f"\n📊 Summary: {available_capabilities}/{total_capabilities} capabilities available")