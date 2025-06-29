"""
uvmgr.commands.workspace
=======================

Workspace management commands for unified configuration and environment handling.

This command module addresses the critical gap in uvmgr's configuration management by providing:

• **Workspace initialization**: Set up unified project configuration
• **Environment management**: Switch between dev/staging/prod environments  
• **Configuration management**: View and modify workspace settings
• **State tracking**: Monitor workspace status and command history
• **Environment switching**: Seamless environment transitions

Example
-------
    $ uvmgr workspace init myproject --type fastapi
    $ uvmgr workspace env switch staging
    $ uvmgr workspace status
    $ uvmgr workspace config set global.auto_test true

See Also
--------
- :mod:`uvmgr.core.workspace` : Workspace management implementation
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, Dict, Any
import json
import yaml

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, ProjectAttributes, ProjectOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.workspace import (
    get_workspace_manager, 
    get_workspace_config, 
    get_environment_config,
    WorkspaceManager
)

app = typer.Typer(help="Workspace and configuration management")


@app.command()
@instrument_command("workspace_init", track_args=True)
def init(
    project_name: Optional[str] = typer.Argument(None, help="Project name (defaults to directory name)"),
    project_type: str = typer.Option("python", "--type", "-t", help="Project type (python, fastapi, cli, library)"),
    workspace_root: Optional[Path] = typer.Option(None, "--root", "-r", help="Workspace root directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization even if workspace exists")
):
    """Initialize a new uvmgr workspace with unified configuration."""
    
    workspace_root = workspace_root or Path.cwd()
    project_name = project_name or workspace_root.name
    
    manager = WorkspaceManager(workspace_root)
    
    # Check if workspace already exists
    if manager.config_file.exists() and not force:
        typer.echo(f"❌ Workspace already exists at {workspace_root}")
        typer.echo("Use --force to reinitialize")
        raise typer.Exit(1)
    
    # Initialize workspace
    config = manager.initialize_workspace(project_name, project_type)
    
    add_span_attributes(**{
        ProjectAttributes.NAME: project_name,
        ProjectAttributes.LANGUAGE: "python",
        ProjectAttributes.OPERATION: ProjectOperations.CREATE,
        "project_type": project_type,
        "workspace_root": str(workspace_root)
    })
    
    typer.echo(f"✅ Initialized uvmgr workspace: {project_name}")
    typer.echo(f"📁 Location: {workspace_root}")
    typer.echo(f"🏗️  Project type: {project_type}")
    typer.echo(f"🌍 Environments: {list(config.environments.keys())}")
    typer.echo(f"⚙️  Configuration: {manager.config_file}")
    
    add_span_event("workspace.initialized", {
        "project_name": project_name,
        "environments_count": len(config.environments)
    })


@app.command()
@instrument_command("workspace_status", track_args=True)
def status(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """Show current workspace status and configuration."""
    
    manager = get_workspace_manager()
    summary = manager.get_workspace_summary()
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "workspace_status",
        "current_environment": summary["current_environment"],
        "environments_count": len(summary["available_environments"])
    })
    
    if json_output:
        dump_json(summary)
        return
    
    # Display formatted status
    typer.echo("🏗️  uvmgr Workspace Status")
    typer.echo("=" * 30)
    
    project = summary["project"]
    typer.echo(f"📦 Project: {project['name']} v{project['version']}")
    typer.echo(f"🏷️  Type: {project['type']}")
    typer.echo(f"📁 Root: {summary['workspace_root']}")
    
    typer.echo(f"\n🌍 Environment: {colour(summary['current_environment'], 'green')}")
    typer.echo(f"🔄 Available: {', '.join(summary['available_environments'])}")
    
    # Global settings
    settings = summary["global_settings"]
    typer.echo(f"\n⚙️  Global Settings:")
    for key, value in settings.items():
        status_icon = "✅" if value else "❌"
        typer.echo(f"   {status_icon} {key}: {value}")
    
    # Recent commands
    recent = summary["recent_commands"]
    if recent and detailed:
        typer.echo(f"\n📋 Recent Commands:")
        for cmd in recent[-3:]:
            status_icon = "✅" if cmd["success"] else "❌"
            typer.echo(f"   {status_icon} {cmd['command']} ({cmd['duration']:.2f}s)")
    
    # Features status
    typer.echo(f"\n🔧 Features:")
    typer.echo(f"   {'✅' if summary['ai_enabled'] else '❌'} AI/AGI: {summary['ai_enabled']}")
    typer.echo(f"   {'✅' if summary['workflows_enabled'] else '❌'} Workflows: {summary['workflows_enabled']}")
    typer.echo(f"   {'✅' if summary['telemetry_enabled'] else '❌'} Telemetry: {summary['telemetry_enabled']}")
    
    add_span_event("workspace.status_displayed", {
        "project_name": project["name"],
        "detailed": detailed
    })


# Create environment sub-app
env_app = typer.Typer(help="Environment management commands")
app.add_typer(env_app, name="env")


@env_app.command("list")
@instrument_command("workspace_env_list", track_args=True)
def list_environments(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """List all available environments."""
    
    config = get_workspace_config()
    current_env = get_workspace_manager().load_state().current_environment
    
    if json_output:
        env_data = {}
        for name, env in config.environments.items():
            env_data[name] = {
                "current": name == current_env,
                "python_version": env.python_version,
                "deployment_target": env.deployment_target,
                "dependencies_count": len(env.dependencies)
            }
        dump_json(env_data)
        return
    
    typer.echo("🌍 Available Environments:")
    for name, env in config.environments.items():
        current_marker = " (current)" if name == current_env else ""
        typer.echo(f"  📁 {colour(name, 'green' if name == current_env else 'white')}{current_marker}")
        typer.echo(f"     🐍 Python: {env.python_version or 'default'}")
        if env.deployment_target:
            typer.echo(f"     🚀 Deploy: {env.deployment_target}")
        typer.echo(f"     📦 Dependencies: {len(env.dependencies)}")


@env_app.command("switch")
@instrument_command("workspace_env_switch", track_args=True)
def switch_environment(
    environment: str = typer.Argument(..., help="Environment name to switch to")
):
    """Switch to a different environment."""
    
    try:
        manager = get_workspace_manager()
        manager.switch_environment(environment)
        
        add_span_attributes(**{
            CliAttributes.COMMAND: "workspace_env_switch",
            "environment": environment
        })
        
        typer.echo(f"✅ Switched to environment: {colour(environment, 'green')}")
        
        # Show environment details
        env_config = get_environment_config(environment)
        typer.echo(f"🐍 Python: {env_config.python_version or 'default'}")
        if env_config.deployment_target:
            typer.echo(f"🚀 Deployment target: {env_config.deployment_target}")
        
        add_span_event("workspace.environment_switched", {
            "environment": environment
        })
        
    except ValueError as e:
        typer.echo(f"❌ {e}")
        raise typer.Exit(1)


@env_app.command("create")
@instrument_command("workspace_env_create", track_args=True)
def create_environment(
    name: str = typer.Argument(..., help="Environment name"),
    python_version: Optional[str] = typer.Option(None, "--python", "-p", help="Python version requirement"),
    deployment_target: Optional[str] = typer.Option(None, "--deploy", "-d", help="Deployment target"),
    copy_from: Optional[str] = typer.Option(None, "--copy-from", "-c", help="Copy settings from existing environment")
):
    """Create a new environment."""
    
    manager = get_workspace_manager()
    config = manager.load_config()
    
    if name in config.environments:
        typer.echo(f"❌ Environment '{name}' already exists")
        raise typer.Exit(1)
    
    # Create environment config
    from uvmgr.core.workspace import EnvironmentConfig
    
    if copy_from:
        if copy_from not in config.environments:
            typer.echo(f"❌ Source environment '{copy_from}' not found")
            raise typer.Exit(1)
        
        # Copy from existing environment
        source_env = config.environments[copy_from]
        new_env = EnvironmentConfig(
            name=name,
            python_version=python_version or source_env.python_version,
            dependencies=source_env.dependencies.copy(),
            environment_variables=source_env.environment_variables.copy(),
            deployment_target=deployment_target or source_env.deployment_target,
            build_settings=source_env.build_settings.copy(),
            test_settings=source_env.test_settings.copy(),
            ai_settings=source_env.ai_settings.copy()
        )
    else:
        # Create new environment
        new_env = EnvironmentConfig(
            name=name,
            python_version=python_version,
            deployment_target=deployment_target
        )
    
    config.environments[name] = new_env
    manager.save_config()
    
    typer.echo(f"✅ Created environment: {colour(name, 'green')}")
    if copy_from:
        typer.echo(f"📋 Copied settings from: {copy_from}")
    
    add_span_event("workspace.environment_created", {
        "environment": name,
        "copied_from": copy_from
    })


# Create config sub-app
config_app = typer.Typer(help="Configuration management commands")


@config_app.command("show")
@instrument_command("workspace_config_show", track_args=True)
def show_config(
    section: Optional[str] = typer.Argument(None, help="Configuration section to show"),
    environment: Optional[str] = typer.Option(None, "--env", "-e", help="Show environment-specific config"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show workspace configuration."""
    
    config = get_workspace_config()
    
    if environment:
        if environment not in config.environments:
            typer.echo(f"❌ Environment '{environment}' not found")
            raise typer.Exit(1)
        
        env_config = config.environments[environment]
        if json_output:
            dump_json(env_config.__dict__)
        else:
            typer.echo(f"🌍 Environment: {environment}")
            typer.echo(f"🐍 Python: {env_config.python_version or 'default'}")
            typer.echo(f"🚀 Deploy: {env_config.deployment_target or 'none'}")
            typer.echo(f"📦 Dependencies: {len(env_config.dependencies)}")
        return
    
    config_dict = config.__dict__.copy()
    
    if section:
        if section not in config_dict:
            typer.echo(f"❌ Configuration section '{section}' not found")
            raise typer.Exit(1)
        
        data = config_dict[section]
        if json_output:
            dump_json(data)
        else:
            typer.echo(f"⚙️  {section}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    typer.echo(f"  {key}: {value}")
            else:
                typer.echo(f"  {data}")
    else:
        if json_output:
            dump_json(config_dict)
        else:
            typer.echo("⚙️  Workspace Configuration:")
            typer.echo(f"📦 Project: {config.project_name} v{config.project_version}")
            typer.echo(f"🏷️  Type: {config.project_type}")
            typer.echo(f"🌍 Default environment: {config.default_environment}")
            typer.echo(f"🔧 Global settings: {len(config.global_settings)} items")
            typer.echo(f"📋 Command defaults: {len(config.command_defaults)} commands")


@config_app.command("set")
@instrument_command("workspace_config_set", track_args=True)
def set_config(
    key: str = typer.Argument(..., help="Configuration key (dot notation supported)"),
    value: str = typer.Argument(..., help="Configuration value"),
    environment: Optional[str] = typer.Option(None, "--env", "-e", help="Set for specific environment")
):
    """Set configuration value."""
    
    manager = get_workspace_manager()
    config = manager.load_config()
    
    # Parse key path (support dot notation)
    key_parts = key.split('.')
    
    if environment:
        if environment not in config.environments:
            typer.echo(f"❌ Environment '{environment}' not found")
            raise typer.Exit(1)
        
        # Set environment-specific config
        env_config = config.environments[environment]
        target = env_config.__dict__
    else:
        # Set global config
        target = config.__dict__
    
    # Navigate to the target location
    for part in key_parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    
    # Convert value to appropriate type
    try:
        # Try to parse as JSON for complex types
        import json
        parsed_value = json.loads(value)
    except:
        # Fall back to string
        parsed_value = value
        if value.lower() in ('true', 'false'):
            parsed_value = value.lower() == 'true'
        elif value.isdigit():
            parsed_value = int(value)
        elif value.replace('.', '').isdigit():
            parsed_value = float(value)
    
    target[key_parts[-1]] = parsed_value
    manager.save_config()
    
    scope = f"environment '{environment}'" if environment else "global"
    typer.echo(f"✅ Set {scope} config: {key} = {parsed_value}")
    
    add_span_event("workspace.config_updated", {
        "key": key,
        "scope": scope
    })


@app.command("history")
@instrument_command("workspace_history", track_args=True)
def show_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent commands to show"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show command execution history."""
    
    manager = get_workspace_manager()
    state = manager.load_state()
    
    recent_commands = state.command_history[-limit:] if state.command_history else []
    
    if json_output:
        dump_json(recent_commands)
        return
    
    if not recent_commands:
        typer.echo("📋 No command history found")
        return
    
    typer.echo(f"📋 Recent Commands (last {len(recent_commands)}):")
    for cmd in reversed(recent_commands):
        status_icon = "✅" if cmd["success"] else "❌"
        duration = f"{cmd['duration']:.2f}s"
        timestamp = cmd["timestamp"][:19]  # Remove microseconds
        env = cmd.get("environment", "unknown")
        
        typer.echo(f"  {status_icon} {cmd['command']} ({duration}) [{env}] {timestamp}")


# Add environment and config subcommands
app.add_typer(env_app, name="env")
app.add_typer(config_app, name="config")