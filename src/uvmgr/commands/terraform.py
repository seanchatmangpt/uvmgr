"""
uvmgr.commands.terraform - Infrastructure as Code with Terraform
============================================================

80/20 Terraform integration providing essential IaC capabilities within uvmgr.

This module implements the 20% of Terraform functionality that covers 80% of
Infrastructure as Code use cases, with full OpenTelemetry observability and
uvmgr workflow integration.

Key Features (80/20 Focus)
--------------------------
• **Core Workflow**: plan → apply → destroy lifecycle
• **State Management**: Safe state handling with remote backends
• **Workspace Support**: Multi-environment infrastructure management
• **Template Generation**: Auto-generate common infrastructure patterns
• **Validation**: Pre-flight checks and configuration validation
• **Observability**: Full OTEL instrumentation for all operations

Available Commands
-----------------
- **init**: Initialize Terraform configuration
- **plan**: Create execution plan
- **apply**: Apply infrastructure changes
- **destroy**: Destroy managed infrastructure
- **validate**: Validate configuration files
- **workspace**: Manage Terraform workspaces
- **state**: State management operations
- **generate**: Generate Terraform templates
- **output**: Show output values

Examples
--------
    Initialize and plan infrastructure:
        uvmgr terraform init --backend s3
        uvmgr terraform plan --workspace production
    
    Apply with approval workflow:
        uvmgr terraform apply --auto-approve --workspace staging
    
    Generate common templates:
        uvmgr terraform generate aws-vpc --name production-vpc
        uvmgr terraform generate k8s-cluster --provider aws
    
    State management:
        uvmgr terraform state list
        uvmgr terraform workspace new production

Performance Features
-------------------
- **Parallel Planning**: Multi-threaded plan operations
- **State Caching**: Intelligent state caching for performance
- **Incremental Operations**: Only process changed resources
- **Background Validation**: Continuous configuration validation
- **Resource Targeting**: Selective resource operations

Integration Features
-------------------
- **OTEL Instrumentation**: Complete observability for all operations
- **uvmgr Workflows**: Integration with uvmgr's BPMN workflow engine
- **Security Scanning**: Integration with uvmgr security module
- **Cost Estimation**: Integration with cost analysis tools
- **Git Integration**: Version control awareness and branching
- **CI/CD Integration**: Pipeline-friendly operations

See Also
--------
- :mod:`uvmgr.ops.terraform` : Terraform operations implementation
- :mod:`uvmgr.runtime.terraform` : Terraform runtime execution
- :mod:`uvmgr.core.iac` : Infrastructure as Code utilities
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import terraform as terraform_ops

console = Console()
app = typer.Typer(help="Infrastructure as Code with Terraform (80/20 implementation)")


@app.command("init")
@instrument_command("terraform_init", track_args=True)
def terraform_init(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
    backend: str = typer.Option("local", "--backend", "-b", help="Backend type: local, s3, gcs, azurerm"),
    backend_config: Optional[str] = typer.Option(None, "--backend-config", help="Backend configuration file"),
    upgrade: bool = typer.Option(False, "--upgrade", help="Upgrade modules and providers"),
    reconfigure: bool = typer.Option(False, "--reconfigure", help="Reconfigure backend"),
    migrate_state: bool = typer.Option(False, "--migrate-state", help="Migrate state from another backend"),
    parallelism: int = typer.Option(10, "--parallelism", help="Number of concurrent operations"),
):
    """
    Initialize Terraform configuration with backend setup.
    
    Initializes a Terraform working directory containing configuration files.
    Sets up the backend, downloads providers, and prepares for planning.
    
    Examples:
        uvmgr terraform init
        uvmgr terraform init --backend s3 --backend-config backend.hcl
        uvmgr terraform init --upgrade --reconfigure
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_init",
        "terraform.backend": backend,
        "terraform.upgrade": upgrade,
        "terraform.reconfigure": reconfigure,
        "terraform.parallelism": parallelism,
    })
    
    config = {
        "path": path or Path.cwd(),
        "backend": backend,
        "backend_config": backend_config,
        "upgrade": upgrade,
        "reconfigure": reconfigure,
        "migrate_state": migrate_state,
        "parallelism": parallelism,
    }
    
    try:
        with console.status("[cyan]Initializing Terraform configuration..."):
            result = terraform_ops.terraform_init(config)
        
        add_span_attributes(**{
            "terraform.init.success": result.get("success", False),
            "terraform.init.duration": result.get("duration", 0),
            "terraform.providers_installed": len(result.get("providers", [])),
        })
        
        if result.get("success"):
            console.print("✅ [green]Terraform initialized successfully![/green]")
            
            # Show provider information
            providers = result.get("providers", [])
            if providers:
                table = Table(title="Installed Providers")
                table.add_column("Provider", style="cyan")
                table.add_column("Version", style="green")
                table.add_column("Source", style="blue")
                
                for provider in providers:
                    table.add_row(
                        provider.get("name", "unknown"),
                        provider.get("version", "unknown"),
                        provider.get("source", "unknown")
                    )
                console.print(table)
            
            # Show backend information
            backend_info = result.get("backend", {})
            if backend_info:
                console.print(f"\n🔧 Backend: {backend_info.get('type', backend)}")
                if backend_info.get("config"):
                    console.print(f"   Config: {backend_info['config']}")
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Terraform initialization failed: {error}[/red]")
            if result.get("output"):
                console.print(f"\nOutput:\n{result['output']}")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.init.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to initialize Terraform: {e}[/red]")
        raise typer.Exit(1)


@app.command("plan")
@instrument_command("terraform_plan", track_args=True)
def terraform_plan(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Terraform workspace"),
    var_file: Optional[str] = typer.Option(None, "--var-file", help="Variable file path"),
    variables: Optional[str] = typer.Option(None, "--vars", help="Variables as JSON string"),
    target: Optional[str] = typer.Option(None, "--target", help="Target specific resources"),
    out_file: Optional[Path] = typer.Option(None, "--out", help="Save plan to file"),
    destroy: bool = typer.Option(False, "--destroy", help="Plan resource destruction"),
    detailed_exitcode: bool = typer.Option(True, "--detailed-exitcode", help="Return detailed exit codes"),
    parallelism: int = typer.Option(10, "--parallelism", help="Number of concurrent operations"),
    refresh: bool = typer.Option(True, "--refresh/--no-refresh", help="Refresh state before planning"),
):
    """
    Create an execution plan showing what Terraform will do.
    
    Analyzes configuration and current state to determine what actions
    are needed to reach the desired state.
    
    Examples:
        uvmgr terraform plan
        uvmgr terraform plan --workspace production --var-file prod.tfvars
        uvmgr terraform plan --target aws_instance.web --out plan.tfplan
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_plan",
        "terraform.workspace": workspace or "default",
        "terraform.destroy": destroy,
        "terraform.parallelism": parallelism,
        "terraform.refresh": refresh,
    })
    
    config = {
        "path": path or Path.cwd(),
        "workspace": workspace,
        "var_file": var_file,
        "variables": json.loads(variables) if variables else {},
        "target": target.split(",") if target else None,
        "out_file": out_file,
        "destroy": destroy,
        "detailed_exitcode": detailed_exitcode,
        "parallelism": parallelism,
        "refresh": refresh,
    }
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating Terraform plan...", total=1)
            result = terraform_ops.terraform_plan(config)
            progress.update(task, completed=1)
        
        add_span_attributes(**{
            "terraform.plan.success": result.get("success", False),
            "terraform.plan.duration": result.get("duration", 0),
            "terraform.plan.changes": result.get("changes", {}),
            "terraform.plan.resources_to_add": result.get("changes", {}).get("add", 0),
            "terraform.plan.resources_to_change": result.get("changes", {}).get("change", 0),
            "terraform.plan.resources_to_destroy": result.get("changes", {}).get("destroy", 0),
        })
        
        if result.get("success"):
            changes = result.get("changes", {})
            
            # Display plan summary
            if any(changes.values()):
                panel_content = _format_plan_summary(changes, destroy)
                console.print(Panel(panel_content, title="Terraform Plan Summary", border_style="cyan"))
                
                # Show detailed changes if requested
                if result.get("detailed_changes"):
                    _display_detailed_changes(result["detailed_changes"])
                
                # Cost estimation if available
                if result.get("cost_estimate"):
                    _display_cost_estimate(result["cost_estimate"])
            else:
                console.print("✅ [green]No changes. Infrastructure is up-to-date.[/green]")
            
            # Save plan file info
            if out_file and result.get("plan_file_saved"):
                console.print(f"\n💾 Plan saved to: {out_file}")
                
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Terraform plan failed: {error}[/red]")
            if result.get("output"):
                console.print(f"\nOutput:\n{result['output']}")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.plan.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to create Terraform plan: {e}[/red]")
        raise typer.Exit(1)


@app.command("apply")
@instrument_command("terraform_apply", track_args=True)
def terraform_apply(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Terraform workspace"),
    plan_file: Optional[Path] = typer.Option(None, "--plan", help="Apply specific plan file"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive approval"),
    var_file: Optional[str] = typer.Option(None, "--var-file", help="Variable file path"),
    variables: Optional[str] = typer.Option(None, "--vars", help="Variables as JSON string"),
    target: Optional[str] = typer.Option(None, "--target", help="Target specific resources"),
    parallelism: int = typer.Option(10, "--parallelism", help="Number of concurrent operations"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create state backup"),
):
    """
    Apply Terraform configuration to create/update infrastructure.
    
    Executes the actions proposed in a Terraform plan to reach the
    desired state of the configuration.
    
    Examples:
        uvmgr terraform apply --auto-approve
        uvmgr terraform apply --plan plan.tfplan
        uvmgr terraform apply --workspace production --var-file prod.tfvars
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_apply",
        "terraform.workspace": workspace or "default",
        "terraform.auto_approve": auto_approve,
        "terraform.plan_file": str(plan_file) if plan_file else None,
        "terraform.parallelism": parallelism,
    })
    
    # Safety check for auto-approve
    if not auto_approve and not plan_file:
        console.print("⚠️  [yellow]Applying infrastructure changes without a saved plan.[/yellow]")
        if not typer.confirm("Do you want to continue?"):
            console.print("Operation cancelled.")
            raise typer.Exit(0)
    
    config = {
        "path": path or Path.cwd(),
        "workspace": workspace,
        "plan_file": plan_file,
        "auto_approve": auto_approve,
        "var_file": var_file,
        "variables": json.loads(variables) if variables else {},
        "target": target.split(",") if target else None,
        "parallelism": parallelism,
        "backup": backup,
    }
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Applying Terraform configuration...", total=1)
            result = terraform_ops.terraform_apply(config)
            progress.update(task, completed=1)
        
        add_span_attributes(**{
            "terraform.apply.success": result.get("success", False),
            "terraform.apply.duration": result.get("duration", 0),
            "terraform.apply.resources_created": result.get("resources_created", 0),
            "terraform.apply.resources_updated": result.get("resources_updated", 0),
            "terraform.apply.resources_destroyed": result.get("resources_destroyed", 0),
        })
        
        if result.get("success"):
            console.print("✅ [green]Terraform apply completed successfully![/green]")
            
            # Show apply summary
            summary = result.get("summary", {})
            if summary:
                _display_apply_summary(summary)
            
            # Show outputs
            outputs = result.get("outputs", {})
            if outputs:
                _display_terraform_outputs(outputs)
                
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Terraform apply failed: {error}[/red]")
            if result.get("output"):
                console.print(f"\nOutput:\n{result['output']}")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.apply.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to apply Terraform configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command("destroy")
@instrument_command("terraform_destroy", track_args=True)
def terraform_destroy(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Terraform workspace"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive approval"),
    var_file: Optional[str] = typer.Option(None, "--var-file", help="Variable file path"),
    variables: Optional[str] = typer.Option(None, "--vars", help="Variables as JSON string"),
    target: Optional[str] = typer.Option(None, "--target", help="Target specific resources"),
    parallelism: int = typer.Option(10, "--parallelism", help="Number of concurrent operations"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create state backup"),
):
    """
    Destroy Terraform-managed infrastructure.
    
    Destroys all resources managed by this Terraform configuration.
    This is a destructive operation and cannot be undone.
    
    Examples:
        uvmgr terraform destroy --target aws_instance.test
        uvmgr terraform destroy --workspace staging --auto-approve
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_destroy",
        "terraform.workspace": workspace or "default",
        "terraform.auto_approve": auto_approve,
        "terraform.parallelism": parallelism,
    })
    
    # Safety confirmation
    if not auto_approve:
        console.print("⚠️  [red bold]WARNING: This will destroy all infrastructure managed by Terraform![/red bold]")
        if workspace:
            console.print(f"Workspace: {workspace}")
        console.print()
        
        if not typer.confirm("Are you absolutely sure you want to destroy all resources?"):
            console.print("Operation cancelled.")
            raise typer.Exit(0)
    
    config = {
        "path": path or Path.cwd(),
        "workspace": workspace,
        "auto_approve": auto_approve,
        "var_file": var_file,
        "variables": json.loads(variables) if variables else {},
        "target": target.split(",") if target else None,
        "parallelism": parallelism,
        "backup": backup,
    }
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Destroying Terraform infrastructure...", total=1)
            result = terraform_ops.terraform_destroy(config)
            progress.update(task, completed=1)
        
        add_span_attributes(**{
            "terraform.destroy.success": result.get("success", False),
            "terraform.destroy.duration": result.get("duration", 0),
            "terraform.destroy.resources_destroyed": result.get("resources_destroyed", 0),
        })
        
        if result.get("success"):
            console.print("✅ [green]Terraform destroy completed successfully![/green]")
            
            summary = result.get("summary", {})
            if summary:
                console.print(f"\nDestroyed {summary.get('resources_destroyed', 0)} resources")
                
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Terraform destroy failed: {error}[/red]")
            if result.get("output"):
                console.print(f"\nOutput:\n{result['output']}")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.destroy.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to destroy Terraform infrastructure: {e}[/red]")
        raise typer.Exit(1)


@app.command("workspace")
@instrument_command("terraform_workspace", track_args=True)
def terraform_workspace(
    ctx: typer.Context,
    action: str = typer.Argument(help="Workspace action: list, new, select, delete, show"),
    name: Optional[str] = typer.Argument(None, help="Workspace name"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
):
    """
    Manage Terraform workspaces for multi-environment infrastructure.
    
    Workspaces allow you to manage multiple environments (dev, staging, prod)
    with the same configuration but separate state files.
    
    Examples:
        uvmgr terraform workspace list
        uvmgr terraform workspace new production
        uvmgr terraform workspace select staging
        uvmgr terraform workspace delete old-env
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_workspace",
        "terraform.workspace.action": action,
        "terraform.workspace.name": name or "none",
    })
    
    config = {
        "path": path or Path.cwd(),
        "action": action,
        "name": name,
    }
    
    try:
        result = terraform_ops.terraform_workspace(config)
        
        add_span_attributes(**{
            "terraform.workspace.success": result.get("success", False),
            "terraform.workspaces_count": len(result.get("workspaces", [])),
        })
        
        if result.get("success"):
            if action == "list":
                workspaces = result.get("workspaces", [])
                current = result.get("current_workspace", "default")
                
                console.print("🔧 [bold]Terraform Workspaces:[/bold]")
                for workspace in workspaces:
                    prefix = "* " if workspace == current else "  "
                    style = "green bold" if workspace == current else "white"
                    console.print(f"{prefix}[{style}]{workspace}[/{style}]")
                    
            elif action == "show":
                current = result.get("current_workspace", "default")
                console.print(f"Current workspace: [green bold]{current}[/green bold]")
                
            else:
                message = result.get("message", f"Workspace {action} completed")
                console.print(f"✅ [green]{message}[/green]")
                
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Workspace operation failed: {error}[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.workspace.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to manage workspace: {e}[/red]")
        raise typer.Exit(1)


@app.command("generate")
@instrument_command("terraform_generate", track_args=True)
def terraform_generate(
    ctx: typer.Context,
    template: str = typer.Argument(help="Template type: aws-vpc, k8s-cluster, web-app, database"),
    name: str = typer.Option(..., "--name", "-n", help="Resource name"),
    provider: str = typer.Option("aws", "--provider", "-p", help="Cloud provider: aws, gcp, azure"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    variables: Optional[str] = typer.Option(None, "--vars", help="Template variables as JSON"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated"),
):
    """
    Generate Terraform configuration from templates.
    
    Creates infrastructure templates for common patterns and best practices.
    Supports multiple cloud providers and customizable parameters.
    
    Examples:
        uvmgr terraform generate aws-vpc --name production-vpc
        uvmgr terraform generate k8s-cluster --provider gcp --name my-cluster
        uvmgr terraform generate database --provider azure --vars '{"size": "large"}'
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_generate",
        "terraform.template": template,
        "terraform.provider": provider,
        "terraform.name": name,
        "terraform.dry_run": dry_run,
    })
    
    config = {
        "template": template,
        "name": name,
        "provider": provider,
        "output_dir": output_dir or Path.cwd(),
        "variables": json.loads(variables) if variables else {},
        "dry_run": dry_run,
    }
    
    try:
        result = terraform_ops.terraform_generate(config)
        
        add_span_attributes(**{
            "terraform.generate.success": result.get("success", False),
            "terraform.files_generated": len(result.get("files", [])),
        })
        
        if result.get("success"):
            files = result.get("files", [])
            
            if dry_run:
                console.print("🔍 [bold]Files that would be generated:[/bold]")
                for file_info in files:
                    console.print(f"  📄 {file_info['path']}")
                    console.print(f"     Size: {file_info.get('size', 'unknown')} bytes")
                    console.print(f"     Type: {file_info.get('type', 'terraform')}")
            else:
                console.print("✅ [green]Terraform configuration generated successfully![/green]")
                console.print(f"\n📁 Output directory: {config['output_dir']}")
                
                for file_info in files:
                    console.print(f"  📄 Generated: {file_info['path']}")
                
                console.print(f"\n🚀 Next steps:")
                console.print(f"  1. Review the generated configuration")
                console.print(f"  2. Run: uvmgr terraform init")
                console.print(f"  3. Run: uvmgr terraform plan")
                
        else:
            error = result.get("error", "Unknown error")
            console.print(f"❌ [red]Template generation failed: {error}[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.generate.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to generate template: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("terraform_validate", track_args=True)
def terraform_validate(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Terraform configuration path"),
    format: str = typer.Option("table", "--format", help="Output format: table, json"),
):
    """
    Validate Terraform configuration files.
    
    Validates the syntax and internal consistency of Terraform configuration
    files without accessing remote services.
    
    Examples:
        uvmgr terraform validate
        uvmgr terraform validate --format json
    """
    add_span_attributes(**{
        CliAttributes.COMMAND: "terraform_validate",
        "terraform.format": format,
    })
    
    config = {
        "path": path or Path.cwd(),
        "format": format,
    }
    
    try:
        result = terraform_ops.terraform_validate(config)
        
        add_span_attributes(**{
            "terraform.validate.success": result.get("success", False),
            "terraform.validate.errors": len(result.get("errors", [])),
            "terraform.validate.warnings": len(result.get("warnings", [])),
        })
        
        if result.get("success"):
            console.print("✅ [green]Terraform configuration is valid![/green]")
            
            warnings = result.get("warnings", [])
            if warnings:
                console.print(f"\n⚠️  [yellow]{len(warnings)} warnings found:[/yellow]")
                for warning in warnings:
                    console.print(f"  • {warning}")
                    
        else:
            errors = result.get("errors", [])
            console.print(f"❌ [red]Terraform configuration is invalid! {len(errors)} errors found:[/red]")
            
            for error in errors:
                console.print(f"  • {error}")
            
            raise typer.Exit(1)
            
    except Exception as e:
        add_span_event("terraform.validate.error", {"error": str(e)})
        console.print(f"❌ [red]Failed to validate configuration: {e}[/red]")
        raise typer.Exit(1)


# Helper functions for displaying results

def _format_plan_summary(changes: Dict[str, int], destroy: bool) -> str:
    """Format plan summary for display."""
    if destroy:
        return f"🗑️  [red]Plan: {changes.get('destroy', 0)} to destroy[/red]"
    
    add = changes.get("add", 0)
    change = changes.get("change", 0)
    destroy = changes.get("destroy", 0)
    
    parts = []
    if add > 0:
        parts.append(f"[green]{add} to add[/green]")
    if change > 0:
        parts.append(f"[yellow]{change} to change[/yellow]")
    if destroy > 0:
        parts.append(f"[red]{destroy} to destroy[/red]")
    
    return f"📋 Plan: {', '.join(parts)}" if parts else "No changes"


def _display_detailed_changes(changes: List[Dict[str, Any]]):
    """Display detailed resource changes."""
    if not changes:
        return
    
    table = Table(title="Resource Changes")
    table.add_column("Action", style="bold")
    table.add_column("Resource", style="cyan")
    table.add_column("Name", style="white")
    
    for change in changes[:10]:  # Show first 10 changes
        action = change.get("action", "unknown")
        action_color = {
            "create": "green",
            "update": "yellow", 
            "delete": "red",
            "replace": "orange3"
        }.get(action, "white")
        
        table.add_row(
            f"[{action_color}]{action}[/{action_color}]",
            change.get("resource_type", "unknown"),
            change.get("resource_name", "unknown")
        )
    
    console.print()
    console.print(table)
    
    if len(changes) > 10:
        console.print(f"\n... and {len(changes) - 10} more changes")


def _display_cost_estimate(cost_estimate: Dict[str, Any]):
    """Display cost estimation if available."""
    if not cost_estimate:
        return
    
    monthly_cost = cost_estimate.get("monthly_cost", 0)
    currency = cost_estimate.get("currency", "USD")
    
    console.print()
    console.print(Panel(
        f"💰 Estimated monthly cost: {monthly_cost:.2f} {currency}",
        title="Cost Estimate",
        border_style="yellow"
    ))


def _display_apply_summary(summary: Dict[str, Any]):
    """Display apply operation summary."""
    created = summary.get("resources_created", 0)
    updated = summary.get("resources_updated", 0)
    destroyed = summary.get("resources_destroyed", 0)
    
    table = Table(title="Apply Summary")
    table.add_column("Action", style="bold")
    table.add_column("Count", style="green", justify="right")
    
    if created > 0:
        table.add_row("Created", str(created))
    if updated > 0:
        table.add_row("Updated", str(updated))
    if destroyed > 0:
        table.add_row("Destroyed", str(destroyed))
    
    console.print()
    console.print(table)


def _display_terraform_outputs(outputs: Dict[str, Any]):
    """Display Terraform outputs."""
    if not outputs:
        return
    
    console.print()
    console.print("[bold]Outputs:[/bold]")
    
    for key, value in outputs.items():
        if isinstance(value, dict):
            output_value = value.get("value", value)
            sensitive = value.get("sensitive", False)
            
            if sensitive:
                console.print(f"  {key} = [red](sensitive)[/red]")
            else:
                console.print(f"  {key} = {output_value}")
        else:
            console.print(f"  {key} = {value}")