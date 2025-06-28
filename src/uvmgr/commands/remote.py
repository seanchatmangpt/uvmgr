"""
uvmgr.commands.remote - Remote Execution
=====================================

Remote runner for executing commands on remote hosts.

This module provides CLI commands for executing commands on remote hosts,
enabling distributed development and deployment workflows.

Key Features
-----------
• **Remote Execution**: Execute commands on remote hosts
• **Host Management**: Support for multiple remote hosts
• **Command Execution**: Run arbitrary commands remotely
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **run**: Execute command on remote host

Examples
--------
    >>> # Execute command on remote host
    >>> uvmgr remote run hostname "python --version"

See Also
--------
- :mod:`uvmgr.ops.remote` : Remote operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import RemoteAttributes, RemoteOperations
from uvmgr.ops import remote as remote_ops

# Standard uvmgr command pattern
app = typer.Typer(help="Remote execution and management for distributed development")


@app.command("run")
@instrument_command("remote_run", track_args=True)
def run_remote(
    host: str = typer.Argument(..., help="Remote host (hostname, IP, or ssh://user@host:port)"),
    command: str = typer.Argument(..., help="Command to execute remotely"),
    ctx: typer.Context = typer.Option(None, help="Typer context"),
    user: str = typer.Option(None, "--user", "-u", help="SSH username"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    key_file: str = typer.Option(None, "--key", "-k", help="SSH private key file"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Command timeout in seconds"),
    env: str = typer.Option("", "--env", "-e", help="Environment variables (KEY=VALUE,KEY2=VALUE2)"),
    working_dir: str = typer.Option("", "--cwd", "-d", help="Remote working directory"),
    capture_output: bool = typer.Option(True, "--capture/--no-capture", help="Capture command output"),
):
    """Execute a command on a remote host via SSH."""
    
    add_span_attributes({
        RemoteAttributes.HOST: host,
        RemoteAttributes.OPERATION: RemoteOperations.EXECUTE_COMMAND,
        "remote.command": command,
        "remote.user": user or "default",
        "remote.port": port,
        "remote.timeout": timeout
    })
    
    try:
        # Parse environment variables
        env_vars = {}
        if env:
            for pair in env.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        result = remote_ops.run(
            host=host,
            command=command, 
            user=user,
            port=port,
            key_file=key_file,
            timeout=timeout,
            env_vars=env_vars,
            working_dir=working_dir,
            capture_output=capture_output
        )
        
        add_span_event("remote.command_executed", {
            "success": result.get("success", False),
            "exit_code": result.get("exit_code", -1),
            "output_lines": len(result.get("stdout", "").split('\n'))
        })
        
        if capture_output:
            if result.get("stdout"):
                typer.echo(result["stdout"])
            if result.get("stderr"):
                typer.echo(result["stderr"], err=True)
        
        if ctx and ctx.meta.get("json"):
            from uvmgr.core.shell import dump_json
            dump_json(result)
        
        if not result.get("success", False):
            raise typer.Exit(result.get("exit_code", 1))
            
    except Exception as e:
        add_span_event("remote.command_failed", {"error": str(e)})
        typer.echo(f"❌ Remote execution failed: {e}", err=True)
        raise typer.Exit(1)


@app.command("hosts")
@instrument_command("remote_hosts", track_args=True)
def list_hosts(
    ctx: typer.Context = typer.Option(None, help="Typer context"),
):
    """List configured remote hosts."""
    
    try:
        hosts = remote_ops.list_hosts()
        
        add_span_attributes({
            RemoteAttributes.OPERATION: "list_hosts",
            "hosts_count": len(hosts)
        })
        
        if ctx and ctx.meta.get("json"):
            from uvmgr.core.shell import dump_json
            dump_json(hosts)
        else:
            if not hosts:
                typer.echo("No remote hosts configured")
                return
                
            typer.echo("🌐 Configured Remote Hosts:")
            for host_config in hosts:
                name = host_config.get("name", "unknown")
                host = host_config.get("host", "unknown")
                user = host_config.get("user", "")
                port = host_config.get("port", 22)
                
                user_str = f"{user}@" if user else ""
                port_str = f":{port}" if port != 22 else ""
                
                typer.echo(f"  📡 {name}: {user_str}{host}{port_str}")
                
                if host_config.get("description"):
                    typer.echo(f"     {host_config['description']}")
                    
    except Exception as e:
        add_span_event("remote.list_hosts_failed", {"error": str(e)})
        typer.echo(f"❌ Failed to list hosts: {e}", err=True)
        raise typer.Exit(1)


@app.command("add-host")
@instrument_command("remote_add_host", track_args=True)
def add_host(
    name: str = typer.Argument(..., help="Host alias name"),
    host: str = typer.Argument(..., help="Hostname or IP address"),
    user: str = typer.Option("", "--user", "-u", help="Default SSH username"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    key_file: str = typer.Option("", "--key", "-k", help="SSH private key file"),
    description: str = typer.Option("", "--desc", "-d", help="Host description"),
):
    """Add a new remote host configuration."""
    
    try:
        result = remote_ops.add_host(
            name=name,
            host=host,
            user=user,
            port=port,
            key_file=key_file,
            description=description
        )
        
        add_span_attributes({
            RemoteAttributes.HOST: host,
            RemoteAttributes.OPERATION: "add_host",
            "host_name": name
        })
        
        add_span_event("remote.host_added", {
            "name": name,
            "host": host,
            "port": port
        })
        
        typer.echo(f"✅ Added remote host: {name} ({host})")
        
    except Exception as e:
        add_span_event("remote.add_host_failed", {"error": str(e)})
        typer.echo(f"❌ Failed to add host: {e}", err=True)
        raise typer.Exit(1)
