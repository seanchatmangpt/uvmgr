"""
uvmgr.commands.automation
========================

Event-driven automation and intelligent workflow triggers.

This command module addresses the critical automation gap by providing:

• **Event-driven workflows**: Automatic triggers on file changes and git events
• **Intelligent scheduling**: Adaptive scheduling based on usage patterns
• **Rule management**: Create and manage automation rules
• **Execution monitoring**: Track automated workflow executions
• **Self-healing**: Automatic retry and failure recovery

Example
-------
    $ uvmgr automation start             # Start automation engine
    $ uvmgr automation rules list        # List automation rules
    $ uvmgr automation events            # Show recent events
    $ uvmgr automation status            # Show automation status

See Also
--------
- :mod:`uvmgr.core.automation` : Automation engine implementation
- :mod:`uvmgr.core.workflows` : Workflow integration
"""

from __future__ import annotations

import asyncio
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, WorkflowAttributes, WorkflowOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.automation import (
    get_automation_engine,
    start_automation,
    stop_automation,
    AutomationRule,
    EventType,
    TriggerCondition,
    WATCHDOG_AVAILABLE
)

app = typer.Typer(help="Event-driven automation and intelligent workflow triggers")


@app.command("start")
@instrument_command("automation_start", track_args=True)
def start_engine(
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root directory"),
    watch_files: bool = typer.Option(True, "--watch-files/--no-watch-files", help="Enable file watching"),
    setup_git_hooks: bool = typer.Option(True, "--git-hooks/--no-git-hooks", help="Set up git hooks")
):
    """Start the automation engine with intelligent event processing."""
    
    if not WATCHDOG_AVAILABLE and watch_files:
        typer.echo("⚠️  File watching requires 'watchdog' package")
        typer.echo("Install with: pip install 'uvmgr[automation]' or 'pip install watchdog'")
        watch_files = False
    
    typer.echo("🤖 Starting uvmgr automation engine...")
    
    # Start automation engine
    async def start_async():
        engine = get_automation_engine(workspace)
        await engine.start()
        return engine
    
    try:
        engine = asyncio.run(start_async())
        
        add_span_attributes(**{
            CliAttributes.COMMAND: "automation_start",
            WorkflowAttributes.ENGINE: "uvmgr_automation_engine",
            "workspace": str(workspace or Path.cwd()),
            "file_watching": str(watch_files and WATCHDOG_AVAILABLE),
            "git_hooks": str(setup_git_hooks)
        })
        
        typer.echo("✅ Automation engine started successfully!")
        
        stats = engine.get_statistics()
        typer.echo(f"📊 Active rules: {stats['active_rules']}/{stats['rules_count']}")
        typer.echo(f"👁️  File watching: {'✅ Enabled' if stats['file_watching_enabled'] else '❌ Disabled'}")
        typer.echo(f"⏰ Scheduler: {'✅ Running' if stats['scheduler_running'] else '❌ Stopped'}")
        
        typer.echo("\n💡 The automation engine will now monitor for events and trigger workflows.")
        typer.echo("Use 'uvmgr automation status' to check activity.")
        
        add_span_event("automation.engine_started", {
            "rules_count": stats["rules_count"],
            "file_watching": stats["file_watching_enabled"]
        })
        
    except Exception as e:
        typer.echo(f"❌ Failed to start automation engine: {e}")
        raise typer.Exit(1)


@app.command("stop")
@instrument_command("automation_stop", track_args=True)
def stop_engine():
    """Stop the automation engine."""
    
    typer.echo("🛑 Stopping automation engine...")
    
    async def stop_async():
        await stop_automation()
    
    try:
        asyncio.run(stop_async())
        
        add_span_attributes(**{
            CliAttributes.COMMAND: "automation_stop"
        })
        
        typer.echo("✅ Automation engine stopped")
        
    except Exception as e:
        typer.echo(f"❌ Failed to stop automation engine: {e}")
        raise typer.Exit(1)


@app.command("status")
@instrument_command("automation_status", track_args=True)
def show_status(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show automation engine status and statistics."""
    
    engine = get_automation_engine()
    stats = engine.get_statistics()
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_status",
        "rules_active": str(stats["active_rules"]),
        "total_executions": str(stats["total_executions"])
    })
    
    if json_output:
        dump_json(stats)
        return
    
    typer.echo("🤖 [bold]Automation Engine Status[/bold]")
    typer.echo("=" * 35)
    
    # Engine status
    running_status = "🟢 Running" if engine.running else "🔴 Stopped"
    typer.echo(f"Engine: {running_status}")
    
    # Component status
    typer.echo(f"File Watching: {'✅ Active' if stats['file_watching_enabled'] else '❌ Inactive'}")
    typer.echo(f"Scheduler: {'✅ Running' if stats['scheduler_running'] else '❌ Stopped'}")
    
    # Rules
    typer.echo(f"\n📋 Rules: {stats['active_rules']} active / {stats['rules_count']} total")
    
    # Execution statistics
    typer.echo(f"\n📊 Execution Statistics:")
    typer.echo(f"   Total: {stats['total_executions']}")
    typer.echo(f"   ✅ Successful: {stats['successful_executions']}")
    typer.echo(f"   ❌ Failed: {stats['failed_executions']}")
    
    if stats['total_executions'] > 0:
        success_rate = stats['success_rate'] * 100
        success_color = "green" if success_rate > 80 else "yellow" if success_rate > 60 else "red"
        typer.echo(f"   📈 Success Rate: {colour(f'{success_rate:.1f}%', success_color)}")
    
    # Recent activity
    if detailed:
        recent_events = engine.get_recent_events(5)
        if recent_events:
            typer.echo(f"\n🕐 Recent Events (last 5):")
            for event in recent_events:
                timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
                typer.echo(f"   {timestamp} {event.event_type.value}: {event.source}")


@app.command("rules")
def rules_commands():
    """Automation rules management."""
    pass


@rules_commands.command("list")
@instrument_command("automation_rules_list", track_args=True)
def list_rules(
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled rules"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List automation rules."""
    
    engine = get_automation_engine()
    rules = engine.list_rules()
    
    # Apply filters
    if enabled_only:
        rules = [r for r in rules if r.enabled]
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_rules_list",
        "rules_count": str(len(rules)),
        "enabled_only": str(enabled_only)
    })
    
    if json_output:
        rules_data = []
        for rule in rules:
            rules_data.append({
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "event_types": [et.value for et in rule.event_types],
                "trigger_condition": rule.trigger_condition.value,
                "workflow_template": rule.workflow_template,
                "command": rule.command,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered
            })
        dump_json(rules_data)
        return
    
    if not rules:
        typer.echo("📋 No automation rules found")
        return
    
    typer.echo(f"📋 [bold]Automation Rules ({len(rules)})[/bold]")
    
    for rule in rules:
        status_icon = "✅" if rule.enabled else "❌"
        trigger_count_str = f" (triggered {rule.trigger_count}x)" if rule.trigger_count > 0 else ""
        
        typer.echo(f"\n{status_icon} [bold]{rule.name}[/bold]{trigger_count_str}")
        typer.echo(f"   📝 {rule.description}")
        typer.echo(f"   🎯 Events: {', '.join([et.value for et in rule.event_types])}")
        typer.echo(f"   ⚡ Trigger: {rule.trigger_condition.value}")
        
        if rule.workflow_template:
            typer.echo(f"   🔄 Workflow: {rule.workflow_template}")
        elif rule.command:
            typer.echo(f"   💻 Command: {rule.command}")
        
        if rule.file_patterns:
            typer.echo(f"   📁 Files: {', '.join(rule.file_patterns)}")


@rules_commands.command("create")
@instrument_command("automation_rules_create", track_args=True)
def create_rule(
    name: str = typer.Argument(..., help="Rule name"),
    description: str = typer.Option("", "--desc", help="Rule description"),
    event_types: List[str] = typer.Option(["file_changed"], "--event", "-e", help="Event types to trigger on"),
    file_patterns: List[str] = typer.Option([], "--pattern", "-p", help="File patterns to match"),
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Workflow template to execute"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Command to execute"),
    trigger_condition: str = typer.Option("debounced", "--trigger", "-t", help="Trigger condition"),
    debounce_seconds: float = typer.Option(5.0, "--debounce", help="Debounce time in seconds")
):
    """Create a new automation rule."""
    
    if not workflow and not command:
        typer.echo("❌ Must specify either --workflow or --command")
        raise typer.Exit(1)
    
    # Parse event types
    try:
        parsed_event_types = [EventType(et) for et in event_types]
    except ValueError as e:
        typer.echo(f"❌ Invalid event type: {e}")
        raise typer.Exit(1)
    
    # Parse trigger condition
    try:
        parsed_trigger_condition = TriggerCondition(trigger_condition)
    except ValueError as e:
        typer.echo(f"❌ Invalid trigger condition: {e}")
        raise typer.Exit(1)
    
    # Create rule
    rule = AutomationRule(
        id=name.lower().replace(' ', '_'),
        name=name,
        description=description or f"Automation rule: {name}",
        event_types=parsed_event_types,
        file_patterns=file_patterns,
        trigger_condition=parsed_trigger_condition,
        debounce_seconds=debounce_seconds,
        workflow_template=workflow or "",
        command=command or ""
    )
    
    # Add to engine
    engine = get_automation_engine()
    engine.add_rule(rule)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_rules_create",
        "rule_id": rule.id,
        "event_types": str(event_types),
        "has_workflow": bool(workflow),
        "has_command": bool(command)
    })
    
    typer.echo(f"✅ Created automation rule: {colour(rule.name, 'green')}")
    typer.echo(f"   🆔 ID: {rule.id}")
    typer.echo(f"   🎯 Events: {', '.join([et.value for et in rule.event_types])}")
    
    if workflow:
        typer.echo(f"   🔄 Workflow: {workflow}")
    if command:
        typer.echo(f"   💻 Command: {command}")


@rules_commands.command("enable")
@instrument_command("automation_rules_enable", track_args=True)
def enable_rule(
    rule_id: str = typer.Argument(..., help="Rule ID to enable")
):
    """Enable an automation rule."""
    
    engine = get_automation_engine()
    rule = engine.get_rule(rule_id)
    
    if not rule:
        typer.echo(f"❌ Rule '{rule_id}' not found")
        raise typer.Exit(1)
    
    rule.enabled = True
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_rules_enable",
        "rule_id": rule_id
    })
    
    typer.echo(f"✅ Enabled rule: {colour(rule.name, 'green')}")


@rules_commands.command("disable")
@instrument_command("automation_rules_disable", track_args=True)
def disable_rule(
    rule_id: str = typer.Argument(..., help="Rule ID to disable")
):
    """Disable an automation rule."""
    
    engine = get_automation_engine()
    rule = engine.get_rule(rule_id)
    
    if not rule:
        typer.echo(f"❌ Rule '{rule_id}' not found")
        raise typer.Exit(1)
    
    rule.enabled = False
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_rules_disable",
        "rule_id": rule_id
    })
    
    typer.echo(f"❌ Disabled rule: {colour(rule.name, 'red')}")


@app.command("events")
@instrument_command("automation_events", track_args=True)
def show_events(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of events to show"),
    event_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by event type"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show recent automation events."""
    
    engine = get_automation_engine()
    events = engine.get_recent_events(limit * 2)  # Get more to filter
    
    # Filter by event type if specified
    if event_type:
        try:
            filter_type = EventType(event_type)
            events = [e for e in events if e.event_type == filter_type]
        except ValueError:
            typer.echo(f"❌ Invalid event type: {event_type}")
            raise typer.Exit(1)
    
    events = events[-limit:]  # Take latest after filtering
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_events",
        "events_count": str(len(events)),
        "event_type_filter": event_type or "all"
    })
    
    if json_output:
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "source": event.source,
                "metadata": event.metadata,
                "processed": event.processed
            })
        dump_json(events_data)
        return
    
    if not events:
        typer.echo("📅 No recent automation events")
        return
    
    typer.echo(f"📅 [bold]Recent Automation Events ({len(events)})[/bold]")
    
    for event in reversed(events):  # Show newest first
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        processed_icon = "✅" if event.processed else "⏳"
        
        typer.echo(f"\n{processed_icon} {timestamp} - {event.event_type.value}")
        typer.echo(f"   📁 {event.source}")
        
        if event.metadata:
            metadata_str = ", ".join([f"{k}={v}" for k, v in event.metadata.items()][:2])
            typer.echo(f"   📋 {metadata_str}")


@app.command("executions")
@instrument_command("automation_executions", track_args=True)
def show_executions(
    rule_id: Optional[str] = typer.Option(None, "--rule", "-r", help="Filter by rule ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of executions to show"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show automation execution history."""
    
    engine = get_automation_engine()
    executions = engine.get_executions(rule_id)
    
    # Filter by status if specified
    if status:
        executions = [e for e in executions if e.status == status]
    
    executions = executions[:limit]
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_executions",
        "executions_count": str(len(executions)),
        "rule_filter": rule_id or "all",
        "status_filter": status or "all"
    })
    
    if json_output:
        executions_data = []
        for execution in executions:
            executions_data.append({
                "id": execution.id,
                "rule_id": execution.rule_id,
                "trigger_event_id": execution.trigger_event_id,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "execution_time": execution.execution_time,
                "retry_count": execution.retry_count,
                "workflow_execution_id": execution.workflow_execution_id,
                "error_message": execution.error_message
            })
        dump_json(executions_data)
        return
    
    if not executions:
        typer.echo("📊 No automation executions found")
        return
    
    typer.echo(f"📊 [bold]Automation Executions ({len(executions)})[/bold]")
    
    for execution in executions:
        status_icon = {
            "completed": "✅",
            "failed": "❌",
            "running": "🔄",
            "cancelled": "⏹️"
        }.get(execution.status, "❓")
        
        timestamp = datetime.fromtimestamp(execution.started_at).strftime("%Y-%m-%d %H:%M:%S")
        duration_str = ""
        
        if execution.execution_time:
            duration_str = f" ({execution.execution_time:.1f}s)"
        
        typer.echo(f"\n{status_icon} {timestamp}{duration_str}")
        typer.echo(f"   🆔 {execution.id}")
        typer.echo(f"   📋 Rule: {execution.rule_id}")
        typer.echo(f"   🎯 Status: {execution.status}")
        
        if execution.workflow_execution_id:
            typer.echo(f"   🔄 Workflow: {execution.workflow_execution_id}")
        
        if execution.error_message:
            typer.echo(f"   ❌ Error: {execution.error_message}")
        
        if execution.retry_count > 0:
            typer.echo(f"   🔄 Retries: {execution.retry_count}")


@app.command("trigger")
@instrument_command("automation_trigger", track_args=True)
def trigger_event(
    event_type: str = typer.Argument(..., help="Event type to trigger"),
    source: str = typer.Argument(..., help="Event source"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="Event metadata as JSON")
):
    """Manually trigger an automation event."""
    
    try:
        parsed_event_type = EventType(event_type)
    except ValueError:
        typer.echo(f"❌ Invalid event type: {event_type}")
        typer.echo(f"Valid types: {', '.join([et.value for et in EventType])}")
        raise typer.Exit(1)
    
    # Parse metadata
    event_metadata = {}
    if metadata:
        try:
            import json
            event_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            typer.echo(f"❌ Invalid metadata JSON: {metadata}")
            raise typer.Exit(1)
    
    # Trigger event
    engine = get_automation_engine()
    engine.emit_event(parsed_event_type, source, event_metadata)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "automation_trigger",
        "event_type": event_type,
        "source": source,
        "has_metadata": bool(metadata)
    })
    
    typer.echo(f"✅ Triggered automation event: {colour(event_type, 'green')}")
    typer.echo(f"   📁 Source: {source}")
    if event_metadata:
        typer.echo(f"   📋 Metadata: {event_metadata}")


# Add subcommands
app.add_typer(rules_commands, name="rules")