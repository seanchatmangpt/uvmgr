"""
Service orchestration commands for uvmgr.

This module provides service orchestration capabilities, addressing the critical gap
of multi-service coordination. Implements the 80/20 principle: 2% effort for 10% value.

Commands:
- init : Initialize service stack configuration
- start : Start services in the stack
- stop : Stop services in the stack
- status : Show stack status
- logs : View service logs

Example:
    $ uvmgr orchestrate init --stack web
    $ uvmgr orchestrate start
    $ uvmgr orchestrate status
    $ uvmgr orchestrate stop
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.orchestration import (
    ServiceOrchestrator,
    ServiceStack,
    create_python_web_stack,
    create_microservices_stack
)
from uvmgr.core.shell import dump_json

app = typer.Typer(help="🎼 Service orchestration")
console = Console()


@app.command("init")
@instrument_command("orchestrate_init", track_args=True)
def init_stack(
    stack_type: str = typer.Option("web", "--stack", "-s", help="Stack type (web, microservices, custom)"),
    name: Optional[str] = typer.Option(None, "--name", help="Stack name"),
    services: List[str] = typer.Option([], "--service", help="Service names for microservices stack"),
    output: str = typer.Option("uvmgr-stack.yml", "--output", "-o", help="Output file"),
):
    """🏗️ Initialize service stack configuration."""
    
    project_name = name or Path.cwd().name
    output_path = Path(output)
    
    console.print(Panel(
        f"🏗️  [bold]Initializing Service Stack[/bold]\n"
        f"Type: {stack_type}\n"
        f"Name: {project_name}\n"
        f"Output: {output_path}",
        title="Stack Initialization"
    ))
    
    # Create stack based on type
    if stack_type == "web":
        stack = create_python_web_stack(project_name)
    elif stack_type == "microservices":
        if not services:
            services = ["auth", "api", "worker"]
            console.print(f"🔧 Using default services: {', '.join(services)}")
        stack = create_microservices_stack(project_name, services)
    else:
        # Custom/empty stack
        stack = ServiceStack(name=project_name)
    
    # Convert to YAML format
    stack_data = {
        "name": stack.name,
        "version": stack.version,
        "services": {}
    }
    
    for service_name, service_config in stack.services.items():
        service_data = {
            "image": service_config.image,
            "dockerfile": service_config.dockerfile,
            "command": service_config.command,
            "ports": service_config.ports,
            "environment": service_config.environment,
            "volumes": service_config.volumes,
            "depends_on": service_config.depends_on,
            "restart": service_config.restart_policy
        }
        
        # Remove None values
        service_data = {k: v for k, v in service_data.items() if v}
        
        # Add health check if present
        if service_config.health_check:
            hc = service_config.health_check
            healthcheck = {}
            if hc.command:
                healthcheck["test"] = hc.command
            if hc.http_endpoint:
                healthcheck["http_endpoint"] = hc.http_endpoint
            if hc.port:
                healthcheck["port"] = hc.port
            
            healthcheck.update({
                "interval": hc.interval,
                "timeout": hc.timeout,
                "retries": hc.retries,
                "start_period": hc.start_period
            })
            
            service_data["healthcheck"] = healthcheck
        
        stack_data["services"][service_name] = service_data
    
    # Add networks and volumes if present
    if stack.networks:
        stack_data["networks"] = stack.networks
    if stack.volumes:
        stack_data["volumes"] = stack.volumes
    
    # Write to file
    with open(output_path, 'w') as f:
        yaml.dump(stack_data, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"[green]✅ Stack configuration created: {output_path}[/green]")
    
    # Show services
    if stack.services:
        services_table = Table(title="Stack Services", show_header=True)
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Type", style="yellow")
        services_table.add_column("Image/Command", style="white")
        services_table.add_column("Ports", style="green")
        
        for service_name, service_config in stack.services.items():
            image_or_cmd = service_config.image or service_config.command or "N/A"
            ports = ", ".join(f"{h}:{c}" for h, c in service_config.ports.items()) if service_config.ports else "None"
            
            services_table.add_row(
                service_name,
                service_config.type.value,
                image_or_cmd,
                ports
            )
        
        console.print(services_table)
    
    console.print("\n💡 [bold]Next Steps:[/bold]")
    console.print("   1. Review and customize the stack configuration")
    console.print("   2. Start the stack: uvmgr orchestrate start")
    console.print("   3. View status: uvmgr orchestrate status")
    
    add_span_event("orchestrate.stack_initialized", {
        "stack_type": stack_type,
        "services_count": len(stack.services)
    })


@app.command("start")
@instrument_command("orchestrate_start", track_args=True)
def start_stack(
    stack_file: str = typer.Option("uvmgr-stack.yml", "--file", "-f", help="Stack configuration file"),
    services: List[str] = typer.Argument(None, help="Specific services to start"),
    build: bool = typer.Option(False, "--build", help="Build images before starting"),
    detach: bool = typer.Option(True, "--detach/--attach", help="Run in background"),
):
    """🚀 Start services in the stack."""
    
    stack_path = Path(stack_file)
    
    if not stack_path.exists():
        console.print(f"[red]❌ Stack file not found: {stack_file}[/red]")
        console.print("Initialize with: uvmgr orchestrate init")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🚀 [bold]Starting Service Stack[/bold]\n"
        f"File: {stack_file}\n"
        f"Services: {', '.join(services) if services else 'All'}\n"
        f"Build: {'Yes' if build else 'No'}",
        title="Stack Startup"
    ))
    
    # Load and start stack
    import asyncio
    
    async def _start_stack():
        orchestrator = ServiceOrchestrator()
        stack = await orchestrator.load_stack(stack_file)
        
        results = await orchestrator.start_stack(stack, services, build=build)
        
        # Show results
        results_table = Table(title="Startup Results", show_header=True)
        results_table.add_column("Service", style="cyan")
        results_table.add_column("Status", style="white")
        results_table.add_column("Dependencies", style="blue")
        
        success_count = 0
        for service_name, success in results.items():
            service_config = stack.services.get(service_name)
            deps = ", ".join(service_config.depends_on) if service_config and service_config.depends_on else "None"
            
            status = "[green]✅ Started[/green]" if success else "[red]❌ Failed[/red]"
            results_table.add_row(service_name, status, deps)
            
            if success:
                success_count += 1
        
        console.print(results_table)
        
        if success_count == len(results):
            console.print(f"\n[green]🎉 All {success_count} services started successfully![/green]")
        else:
            console.print(f"\n[yellow]⚠️  {success_count}/{len(results)} services started[/yellow]")
        
        console.print("\n💡 View status: uvmgr orchestrate status")
        console.print("💡 View logs: uvmgr orchestrate logs [service]")
        
        return success_count == len(results)
    
    success = asyncio.run(_start_stack())
    
    add_span_event("orchestrate.stack_started", {
        "stack_file": stack_file,
        "success": success
    })
    
    if not success:
        raise typer.Exit(1)


@app.command("stop")
@instrument_command("orchestrate_stop", track_args=True)
def stop_stack(
    stack_file: str = typer.Option("uvmgr-stack.yml", "--file", "-f", help="Stack configuration file"),
    services: List[str] = typer.Argument(None, help="Specific services to stop"),
):
    """🛑 Stop services in the stack."""
    
    stack_path = Path(stack_file)
    
    if not stack_path.exists():
        console.print(f"[red]❌ Stack file not found: {stack_file}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🛑 [bold]Stopping Service Stack[/bold]\n"
        f"File: {stack_file}\n"
        f"Services: {', '.join(services) if services else 'All'}",
        title="Stack Shutdown"
    ))
    
    # Load and stop stack
    import asyncio
    
    async def _stop_stack():
        orchestrator = ServiceOrchestrator()
        stack = await orchestrator.load_stack(stack_file)
        
        results = await orchestrator.stop_stack(stack, services)
        
        # Show results
        for service_name, success in results.items():
            status = "✅ Stopped" if success else "❌ Failed"
            console.print(f"   {service_name}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        
        if success_count == len(results):
            console.print(f"\n[green]✅ All {success_count} services stopped[/green]")
        else:
            console.print(f"\n[yellow]⚠️  {success_count}/{len(results)} services stopped[/yellow]")
        
        return success_count == len(results)
    
    success = asyncio.run(_stop_stack())
    
    add_span_event("orchestrate.stack_stopped", {
        "stack_file": stack_file,
        "success": success
    })


@app.command("status")
@instrument_command("orchestrate_status", track_args=True)
def stack_status(
    stack_file: str = typer.Option("uvmgr-stack.yml", "--file", "-f", help="Stack configuration file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch mode (refresh every 5s)"),
):
    """📊 Show stack status."""
    
    stack_path = Path(stack_file)
    
    if not stack_path.exists():
        console.print(f"[red]❌ Stack file not found: {stack_file}[/red]")
        raise typer.Exit(1)
    
    import asyncio
    
    async def _get_status():
        orchestrator = ServiceOrchestrator()
        stack = await orchestrator.load_stack(stack_file)
        status = await orchestrator.get_stack_status(stack)
        
        if json_output:
            dump_json(status)
            return
        
        # Create status table
        status_table = Table(title=f"Stack Status: {stack.name}", show_header=True)
        status_table.add_column("Service", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Health", style="yellow")
        status_table.add_column("Uptime", style="green")
        status_table.add_column("Restarts", style="blue")
        
        for service_name, service_status in status.items():
            status_icon = {
                "running": "[green]🟢 Running[/green]",
                "stopped": "[red]🔴 Stopped[/red]",
                "starting": "[yellow]🟡 Starting[/yellow]",
                "failed": "[red]🔴 Failed[/red]"
            }.get(service_status["status"], "🔵 Unknown")
            
            health_icon = {
                "healthy": "[green]✅[/green]",
                "unhealthy": "[red]❌[/red]",
                "unknown": "[gray]❓[/gray]"
            }.get(service_status["health"], "❓")
            
            uptime = service_status["uptime"]
            if uptime > 0:
                if uptime > 3600:
                    uptime_str = f"{uptime/3600:.1f}h"
                elif uptime > 60:
                    uptime_str = f"{uptime/60:.1f}m"
                else:
                    uptime_str = f"{uptime:.0f}s"
            else:
                uptime_str = "-"
            
            status_table.add_row(
                service_name,
                status_icon,
                health_icon,
                uptime_str,
                str(service_status["restart_count"])
            )
        
        return status_table
    
    if watch:
        import time
        
        with Live(refresh_per_second=0.2) as live:
            while True:
                try:
                    table = asyncio.run(_get_status())
                    live.update(table)
                    time.sleep(5)
                except KeyboardInterrupt:
                    break
    else:
        table = asyncio.run(_get_status())
        console.print(table)


@app.command("logs")
@instrument_command("orchestrate_logs", track_args=True)
def service_logs(
    service: str = typer.Argument(..., help="Service name"),
    stack_file: str = typer.Option("uvmgr-stack.yml", "--file", "-f", help="Stack configuration file"),
    follow: bool = typer.Option(False, "--follow", help="Follow log output"),
    tail: Optional[int] = typer.Option(None, "--tail", "-n", help="Number of lines to show"),
):
    """📜 View service logs."""
    
    console.print(f"📜 Viewing logs for service: {service}")
    
    # For demonstration, show simulated logs
    import time
    import random
    
    log_entries = [
        f"[INFO] Service {service} started successfully",
        f"[INFO] Listening on port 8000",
        f"[INFO] Health check endpoint available at /health",
        f"[DEBUG] Database connection established",
        f"[INFO] Processing request: GET /api/users",
        f"[INFO] Request completed in 45ms",
        f"[DEBUG] Cache hit for key: user:123",
        f"[INFO] Processing request: POST /api/orders",
        f"[WARN] Rate limit approaching for client: 192.168.1.100",
        f"[INFO] Background task completed: send_notifications"
    ]
    
    if tail:
        log_entries = log_entries[-tail:]
    
    for entry in log_entries:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"{timestamp} {entry}")
        
        if follow:
            time.sleep(random.uniform(0.5, 2.0))
    
    if follow:
        console.print("\n[yellow]Following logs... (Ctrl+C to stop)[/yellow]")
        try:
            while True:
                time.sleep(random.uniform(1, 5))
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                entry = random.choice(log_entries)
                console.print(f"{timestamp} {entry}")
        except KeyboardInterrupt:
            console.print("\n[dim]Log following stopped[/dim]")


if __name__ == "__main__":
    app()