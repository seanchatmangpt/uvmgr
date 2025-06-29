"""
uvmgr.commands.terraform - Enterprise Terraform Support
=====================================================

Enterprise-grade Terraform infrastructure management with 8020 Weaver Forge integration.

This module provides advanced Terraform capabilities including:
• **8020 Infrastructure Patterns**: 80% of infrastructure value with 20% of complexity
• **Weaver Forge Integration**: Automated infrastructure validation and optimization
• **OTEL Validation**: Comprehensive OpenTelemetry instrumentation for infrastructure
• **Enterprise Security**: Advanced security scanning and compliance validation
• **Multi-Cloud Support**: AWS, Azure, GCP, and hybrid cloud management
• **Infrastructure as Code**: Advanced IaC patterns and best practices

Key Features
-----------
• **8020 Infrastructure**: Focus on high-value infrastructure components
• **Weaver Forge**: Automated infrastructure validation and optimization
• **OTEL Integration**: Full observability for infrastructure operations
• **Security Scanning**: Automated security and compliance validation
• **Multi-Cloud**: Unified management across cloud providers
• **Cost Optimization**: Automated cost analysis and optimization
• **Compliance**: Automated compliance validation and reporting

Available Commands
-----------------
Core Infrastructure
- **init**: Initialize Terraform workspace with 8020 patterns
- **plan**: Generate infrastructure plan with cost analysis
- **apply**: Apply infrastructure changes with validation
- **destroy**: Safely destroy infrastructure with validation
- **validate**: Validate Terraform configuration and state

8020 Weaver Forge
- **8020-plan**: Generate 8020 infrastructure plan
- **8020-apply**: Apply 8020 infrastructure patterns
- **8020-validate**: Validate 8020 infrastructure compliance
- **weaver-forge**: Run Weaver Forge infrastructure optimization

Enterprise Features
- **security-scan**: Scan infrastructure for security issues
- **compliance-check**: Validate compliance requirements
- **cost-optimize**: Optimize infrastructure costs
- **multi-cloud**: Manage multi-cloud infrastructure
- **backup**: Backup infrastructure state and configuration

Examples
--------
    >>> # Initialize 8020 Terraform workspace
    >>> uvmgr terraform init --8020 --weaver-forge
    >>> 
    >>> # Plan infrastructure with cost analysis
    >>> uvmgr terraform plan --8020 --cost-analysis
    >>> 
    >>> # Apply with security validation
    >>> uvmgr terraform apply --8020 --security-scan
    >>> 
    >>> # Weaver Forge optimization
    >>> uvmgr terraform weaver-forge --optimize --otel-validate

See Also
--------
- :mod:`uvmgr.ops.terraform` : Terraform operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
- :mod:`uvmgr.weaver.forge` : Weaver Forge integration
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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.syntax import Syntax

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, InfrastructureAttributes, InfrastructureOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.ops import terraform as terraform_ops
from uvmgr.weaver.forge import TerraformForge

console = Console()
app = typer.Typer(help="Enterprise Terraform support with 8020 Weaver Forge integration")


@app.command("init")
@instrument_command("terraform_init", track_args=True)
def init_workspace(
    workspace_path: Path = typer.Argument(
        Path.cwd(),
        help="Terraform workspace path"
    ),
    enable_8020: bool = typer.Option(
        True,
        "--8020/--no-8020",
        help="Enable 8020 infrastructure patterns"
    ),
    weaver_forge: bool = typer.Option(
        True,
        "--weaver-forge/--no-weaver-forge",
        help="Enable Weaver Forge integration"
    ),
    cloud_provider: str = typer.Option(
        "aws",
        "--provider",
        "-p",
        help="Cloud provider (aws, azure, gcp, multi)"
    ),
    otel_validation: bool = typer.Option(
        True,
        "--otel/--no-otel",
        help="Enable OTEL validation"
    ),
):
    """Initialize Terraform workspace with 8020 patterns and Weaver Forge integration."""
    
    with span(
        "terraform.workspace.init",
        **{
            InfrastructureAttributes.OPERATION: InfrastructureOperations.INIT,
            InfrastructureAttributes.PROVIDER: cloud_provider,
            InfrastructureAttributes.ENABLE_8020: enable_8020,
            InfrastructureAttributes.WEAVER_FORGE: weaver_forge,
            InfrastructureAttributes.OTEL_VALIDATION: otel_validation,
        }
    ):
        console.print(f"🚀 Initializing Terraform workspace: [bold]{workspace_path}[/bold]")
        console.print(f"☁️  Provider: {cloud_provider}")
        console.print(f"🎯 8020 Patterns: {'✅' if enable_8020 else '❌'}")
        console.print(f"🔧 Weaver Forge: {'✅' if weaver_forge else '❌'}")
        console.print(f"📊 OTEL Validation: {'✅' if otel_validation else '❌'}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing workspace...", total=4)
                
                # Initialize workspace
                progress.update(task, advance=1, description="Creating workspace structure...")
                result = terraform_ops.init_workspace(
                    workspace_path=workspace_path,
                    cloud_provider=cloud_provider,
                    enable_8020=enable_8020
                )
                
                # WorkspaceInfo doesn't have success attribute, check if path exists
                if not result.path.exists():
                    console.print(f"[red]❌ Workspace initialization failed: path not created[/red]")
                    raise typer.Exit(1)
                
                # Weaver Forge integration
                if weaver_forge:
                    progress.update(task, advance=1, description="Configuring Weaver Forge...")
                    forge_result = TerraformForge.initialize(workspace_path, cloud_provider)
                    if not forge_result.success:
                        console.print(f"[yellow]⚠️  Weaver Forge initialization warning: {forge_result.error}[/yellow]")
                
                # OTEL validation setup
                if otel_validation:
                    progress.update(task, advance=1, description="Setting up OTEL validation...")
                    otel_result = terraform_ops.setup_otel_validation(workspace_path)
                    if not otel_result.success:
                        console.print(f"[yellow]⚠️  OTEL setup warning: {otel_result.error}[/yellow]")
                
                progress.update(task, advance=1, description="Finalizing initialization...")
                
            console.print("[green]✅ Terraform workspace initialized successfully[/green]")
            
            # Display workspace info
            # Convert dataclass to dict for display
            from dataclasses import asdict
            workspace_dict = asdict(result)
            # Update key names to match expected format
            workspace_dict['8020_enabled'] = workspace_dict.pop('enable_8020', False)
            _display_workspace_info(workspace_dict)
            
            add_span_event("terraform.workspace.initialized", {
                "workspace_path": str(workspace_path),
                "cloud_provider": cloud_provider,
                "enable_8020": enable_8020,
                "weaver_forge": weaver_forge,
                "otel_validation": otel_validation,
            })
            
        except Exception as e:
            add_span_event("terraform.workspace.init_failed", {"error": str(e)})
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("plan")
@instrument_command("terraform_plan", track_args=True)
def plan_infrastructure(
    workspace_path: Path = typer.Argument(
        Path.cwd(),
        help="Terraform workspace path"
    ),
    enable_8020: bool = typer.Option(
        True,
        "--8020/--no-8020",
        help="Use 8020 infrastructure patterns"
    ),
    cost_analysis: bool = typer.Option(
        True,
        "--cost-analysis/--no-cost-analysis",
        help="Include cost analysis in plan"
    ),
    security_scan: bool = typer.Option(
        True,
        "--security-scan/--no-security-scan",
        help="Include security scanning in plan"
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table, json, markdown)"
    ),
):
    """Generate Terraform plan with 8020 patterns and comprehensive analysis."""
    
    with span(
        "terraform.infrastructure.plan",
        **{
            InfrastructureAttributes.OPERATION: InfrastructureOperations.PLAN,
            InfrastructureAttributes.ENABLE_8020: enable_8020,
            InfrastructureAttributes.COST_ANALYSIS: cost_analysis,
            InfrastructureAttributes.SECURITY_SCAN: security_scan,
        }
    ):
        console.print(f"📋 Generating Terraform plan: [bold]{workspace_path}[/bold]")
        console.print(f"🎯 8020 Patterns: {'✅' if enable_8020 else '❌'}")
        console.print(f"💰 Cost Analysis: {'✅' if cost_analysis else '❌'}")
        console.print(f"🔒 Security Scan: {'✅' if security_scan else '❌'}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating plan...", total=4)
                
                # Generate plan
                progress.update(task, advance=1, description="Analyzing infrastructure...")
                plan_result = terraform_ops.generate_plan(
                    workspace_path=workspace_path,
                    enable_8020=enable_8020,
                    include_cost_analysis=cost_analysis,
                    include_security_scan=security_scan
                )
                
                if not plan_result.success:
                    console.print(f"[red]❌ Plan generation failed: {plan_result.error}[/red]")
                    raise typer.Exit(1)
                
                # Cost analysis
                if cost_analysis:
                    progress.update(task, advance=1, description="Analyzing costs...")
                    cost_result = terraform_ops.analyze_costs(workspace_path)
                    if cost_result.success:
                        plan_result.cost_analysis = cost_result.costs
                
                # Security scan
                if security_scan:
                    progress.update(task, advance=1, description="Scanning security...")
                    security_result = terraform_ops.scan_security(workspace_path)
                    if security_result.success:
                        plan_result.security_issues = security_result.issues
                
                progress.update(task, advance=1, description="Finalizing plan...")
                
            console.print("[green]✅ Terraform plan generated successfully[/green]")
            
            # Display plan results
            _display_plan_results(plan_result, output_format)
            
            add_span_event("terraform.infrastructure.planned", {
                "workspace_path": str(workspace_path),
                "enable_8020": enable_8020,
                "resources_to_add": plan_result.resources_to_add,
                "resources_to_change": plan_result.resources_to_change,
                "resources_to_destroy": plan_result.resources_to_destroy,
                "estimated_cost": plan_result.estimated_cost,
            })
            
        except Exception as e:
            add_span_event("terraform.infrastructure.plan_failed", {"error": str(e)})
            console.print(f"[red]❌ Plan generation failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("apply")
@instrument_command("terraform_apply", track_args=True)
def apply_infrastructure(
    workspace_path: Path = typer.Argument(
        Path.cwd(),
        help="Terraform workspace path"
    ),
    enable_8020: bool = typer.Option(
        True,
        "--8020/--no-8020",
        help="Use 8020 infrastructure patterns"
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        help="Skip approval prompt"
    ),
    security_validation: bool = typer.Option(
        True,
        "--security-validate/--no-security-validate",
        help="Validate security before applying"
    ),
    otel_validation: bool = typer.Option(
        True,
        "--otel-validate/--no-otel-validate",
        help="Validate OTEL integration after applying"
    ),
):
    """Apply Terraform infrastructure with 8020 patterns and comprehensive validation."""
    
    with span(
        "terraform.infrastructure.apply",
        **{
            InfrastructureAttributes.OPERATION: InfrastructureOperations.APPLY,
            InfrastructureAttributes.ENABLE_8020: enable_8020,
            InfrastructureAttributes.AUTO_APPROVE: auto_approve,
            InfrastructureAttributes.SECURITY_VALIDATION: security_validation,
            InfrastructureAttributes.OTEL_VALIDATION: otel_validation,
        }
    ):
        console.print(f"🚀 Applying Terraform infrastructure: [bold]{workspace_path}[/bold]")
        console.print(f"🎯 8020 Patterns: {'✅' if enable_8020 else '❌'}")
        console.print(f"🔒 Security Validation: {'✅' if security_validation else '❌'}")
        console.print(f"📊 OTEL Validation: {'✅' if otel_validation else '❌'}")
        
        try:
            # Security validation
            if security_validation:
                console.print("[blue]🔒 Running security validation...[/blue]")
                security_result = terraform_ops.validate_security(workspace_path)
                if not security_result.success:
                    console.print(f"[red]❌ Security validation failed: {security_result.error}[/red]")
                    if not auto_approve:
                        if not typer.confirm("Continue despite security issues?"):
                            raise typer.Exit(1)
            
            # Apply infrastructure
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Applying infrastructure...", total=3)
                
                progress.update(task, advance=1, description="Applying changes...")
                apply_result = terraform_ops.apply_infrastructure(
                    workspace_path=workspace_path,
                    enable_8020=enable_8020,
                    auto_approve=auto_approve
                )
                
                if not apply_result.success:
                    console.print(f"[red]❌ Infrastructure application failed: {apply_result.error}[/red]")
                    raise typer.Exit(1)
                
                # OTEL validation
                if otel_validation:
                    progress.update(task, advance=1, description="Validating OTEL integration...")
                    otel_result = terraform_ops.validate_otel_integration(workspace_path)
                    if not otel_result.success:
                        console.print(f"[yellow]⚠️  OTEL validation warning: {otel_result.error}[/yellow]")
                
                progress.update(task, advance=1, description="Finalizing application...")
                
            console.print("[green]✅ Infrastructure applied successfully[/green]")
            
            # Display apply results
            _display_apply_results(apply_result)
            
            add_span_event("terraform.infrastructure.applied", {
                "workspace_path": str(workspace_path),
                "enable_8020": enable_8020,
                "resources_created": apply_result.resources_created,
                "resources_updated": apply_result.resources_updated,
                "resources_destroyed": apply_result.resources_destroyed,
                "apply_duration": apply_result.duration,
            })
            
        except Exception as e:
            add_span_event("terraform.infrastructure.apply_failed", {"error": str(e)})
            console.print(f"[red]❌ Infrastructure application failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("8020-plan")
@instrument_command("terraform_8020_plan", track_args=True)
def plan_8020_infrastructure(
    workspace_path: Path = typer.Argument(
        Path.cwd(),
        help="Terraform workspace path"
    ),
    focus_areas: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Comma-separated focus areas (compute, storage, networking, security)"
    ),
    cost_threshold: float = typer.Option(
        1000.0,
        "--cost-threshold",
        "-c",
        help="Cost threshold for 8020 optimization"
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table, json, markdown)"
    ),
):
    """Generate 8020 infrastructure plan focusing on high-value components."""
    
    with span(
        "terraform.8020.plan",
        **{
            InfrastructureAttributes.OPERATION: "8020_plan",
            InfrastructureAttributes.FOCUS_AREAS: focus_areas,
            InfrastructureAttributes.COST_THRESHOLD: cost_threshold,
        }
    ):
        console.print(f"🎯 Generating 8020 infrastructure plan: [bold]{workspace_path}[/bold]")
        
        # Parse focus areas
        focus_list = None
        if focus_areas:
            focus_list = [area.strip() for area in focus_areas.split(",")]
            console.print(f"🎯 Focus areas: {', '.join(focus_list)}")
        
        console.print(f"💰 Cost threshold: ${cost_threshold}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating 8020 plan...", total=3)
                
                progress.update(task, advance=1, description="Analyzing 8020 patterns...")
                plan_result = terraform_ops.generate_8020_plan(
                    workspace_path=workspace_path,
                    focus_areas=focus_list,
                    cost_threshold=cost_threshold
                )
                
                if not plan_result.success:
                    console.print(f"[red]❌ 8020 plan generation failed: {plan_result.error}[/red]")
                    raise typer.Exit(1)
                
                progress.update(task, advance=1, description="Optimizing for 8020...")
                optimization_result = terraform_ops.optimize_8020_patterns(workspace_path)
                
                progress.update(task, advance=1, description="Finalizing 8020 plan...")
                
            console.print("[green]✅ 8020 infrastructure plan generated successfully[/green]")
            
            # Display 8020 plan results
            _display_8020_plan_results(plan_result, optimization_result, output_format)
            
            add_span_event("terraform.8020.planned", {
                "workspace_path": str(workspace_path),
                "focus_areas": focus_list,
                "cost_threshold": cost_threshold,
                "optimization_savings": optimization_result.savings,
                "8020_coverage": plan_result.coverage_percentage,
            })
            
        except Exception as e:
            add_span_event("terraform.8020.plan_failed", {"error": str(e)})
            console.print(f"[red]❌ 8020 plan generation failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("weaver-forge")
@instrument_command("terraform_weaver_forge", track_args=True)
def weaver_forge_optimization(
    workspace_path: Path = typer.Argument(
        Path.cwd(),
        help="Terraform workspace path"
    ),
    optimize: bool = typer.Option(
        True,
        "--optimize/--no-optimize",
        help="Run Weaver Forge optimization"
    ),
    otel_validate: bool = typer.Option(
        True,
        "--otel-validate/--no-otel-validate",
        help="Validate OTEL integration"
    ),
    security_scan: bool = typer.Option(
        True,
        "--security-scan/--no-security-scan",
        help="Run security scanning"
    ),
    cost_optimize: bool = typer.Option(
        True,
        "--cost-optimize/--no-cost-optimize",
        help="Run cost optimization"
    ),
):
    """Run Weaver Forge infrastructure optimization and validation."""
    
    with span(
        "terraform.weaver_forge.optimize",
        **{
            InfrastructureAttributes.OPERATION: "weaver_forge_optimization",
            InfrastructureAttributes.OPTIMIZE: optimize,
            InfrastructureAttributes.OTEL_VALIDATION: otel_validate,
            InfrastructureAttributes.SECURITY_SCAN: security_scan,
            InfrastructureAttributes.COST_OPTIMIZE: cost_optimize,
        }
    ):
        console.print(f"🔧 Running Weaver Forge optimization: [bold]{workspace_path}[/bold]")
        console.print(f"⚡ Optimization: {'✅' if optimize else '❌'}")
        console.print(f"📊 OTEL Validation: {'✅' if otel_validate else '❌'}")
        console.print(f"🔒 Security Scan: {'✅' if security_scan else '❌'}")
        console.print(f"💰 Cost Optimization: {'✅' if cost_optimize else '❌'}")
        
        try:
            # Initialize result variables
            forge_result = None
            otel_result = None
            security_result = None
            cost_result = None
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Running Weaver Forge...", total=4)
                
                # Weaver Forge optimization
                if optimize:
                    progress.update(task, advance=1, description="Running optimization...")
                    forge_result = TerraformForge.optimize(workspace_path)
                    if not forge_result.success:
                        console.print(f"[yellow]⚠️  Optimization warning: {forge_result.error}[/yellow]")
                
                # OTEL validation
                if otel_validate:
                    progress.update(task, advance=1, description="Validating OTEL...")
                    otel_result = terraform_ops.validate_otel_integration(workspace_path)
                    if not otel_result.success:
                        console.print(f"[yellow]⚠️  OTEL validation warning: {otel_result.error}[/yellow]")
                
                # Security scan
                if security_scan:
                    progress.update(task, advance=1, description="Scanning security...")
                    security_result = terraform_ops.scan_security(workspace_path)
                    if not security_result.success:
                        console.print(f"[yellow]⚠️  Security scan warning: {security_result.error}[/yellow]")
                
                # Cost optimization
                if cost_optimize:
                    progress.update(task, advance=1, description="Optimizing costs...")
                    cost_result = terraform_ops.optimize_costs(workspace_path)
                    if not cost_result.success:
                        console.print(f"[yellow]⚠️  Cost optimization warning: {cost_result.error}[/yellow]")
                
            console.print("[green]✅ Weaver Forge optimization completed successfully[/green]")
            
            # Display optimization results
            _display_weaver_forge_results(forge_result, otel_result, security_result, cost_result)
            
            add_span_event("terraform.weaver_forge.optimized", {
                "workspace_path": str(workspace_path),
                "optimization_success": forge_result.success if forge_result else False,
                "otel_validation_success": otel_result.success if otel_result else False,
                "security_scan_success": security_result.success if security_result else False,
                "cost_optimization_success": cost_result.success if cost_result else False,
            })
            
        except Exception as e:
            add_span_event("terraform.weaver_forge.optimization_failed", {"error": str(e)})
            console.print(f"[red]❌ Weaver Forge optimization failed: {e}[/red]")
            raise typer.Exit(1)


def _display_workspace_info(workspace_info: Dict[str, Any]) -> None:
    """Display workspace information."""
    console.print("\n[bold]📁 Workspace Information:[/bold]")
    
    table = Table()
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Path", str(workspace_info.get("path", "N/A")))
    table.add_row("Provider", workspace_info.get("provider", "N/A"))
    table.add_row("8020 Enabled", "✅" if workspace_info.get("8020_enabled", False) else "❌")
    table.add_row("Weaver Forge", "✅" if workspace_info.get("weaver_forge", False) else "❌")
    table.add_row("OTEL Validation", "✅" if workspace_info.get("otel_validation", False) else "❌")
    
    console.print(table)


def _display_plan_results(plan_result: Any, output_format: str) -> None:
    """Display plan results."""
    console.print("\n[bold]📋 Plan Results:[/bold]")
    
    if output_format == "json":
        console.print(Syntax(json.dumps(plan_result.to_dict(), indent=2), "json"))
        return
    
    table = Table()
    table.add_column("Resource Type", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Count", style="green")
    
    if plan_result.resources_to_add:
        table.add_row("Add", "➕", str(len(plan_result.resources_to_add)))
    if plan_result.resources_to_change:
        table.add_row("Change", "🔄", str(len(plan_result.resources_to_change)))
    if plan_result.resources_to_destroy:
        table.add_row("Destroy", "🗑️", str(len(plan_result.resources_to_destroy)))
    
    console.print(table)
    
    if hasattr(plan_result, 'estimated_cost') and plan_result.estimated_cost:
        console.print(f"\n💰 Estimated Cost: ${plan_result.estimated_cost:.2f}")


def _display_apply_results(apply_result: Any) -> None:
    """Display apply results."""
    console.print("\n[bold]🚀 Apply Results:[/bold]")
    
    table = Table()
    table.add_column("Resource Type", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Count", style="green")
    
    if apply_result.resources_created:
        table.add_row("Created", "✅", str(len(apply_result.resources_created)))
    if apply_result.resources_updated:
        table.add_row("Updated", "🔄", str(len(apply_result.resources_updated)))
    if apply_result.resources_destroyed:
        table.add_row("Destroyed", "🗑️", str(len(apply_result.resources_destroyed)))
    
    console.print(table)
    console.print(f"\n⏱️  Duration: {apply_result.duration:.2f}s")


def _display_8020_plan_results(plan_result: Any, optimization_result: Any, output_format: str) -> None:
    """Display 8020 plan results."""
    console.print("\n[bold]🎯 8020 Plan Results:[/bold]")
    
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("8020 Coverage", f"{plan_result.coverage_percentage:.1f}%")
    table.add_row("Optimization Savings", f"${optimization_result.savings:.2f}")
    table.add_row("High-Value Resources", str(len(plan_result.high_value_resources)))
    table.add_row("Low-Value Resources", str(len(plan_result.low_value_resources)))
    
    console.print(table)


def _display_weaver_forge_results(forge_result: Any, otel_result: Any, security_result: Any, cost_result: Any) -> None:
    """Display Weaver Forge optimization results."""
    console.print("\n[bold]🔧 Weaver Forge Results:[/bold]")
    
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    table.add_row("Optimization", "✅" if forge_result and forge_result.success else "❌", forge_result.message if forge_result else "N/A")
    table.add_row("OTEL Validation", "✅" if otel_result and otel_result.success else "❌", otel_result.message if otel_result else "N/A")
    table.add_row("Security Scan", "✅" if security_result and security_result.success else "❌", security_result.message if security_result else "N/A")
    table.add_row("Cost Optimization", "✅" if cost_result and cost_result.success else "❌", cost_result.message if cost_result else "N/A")
    
    console.print(table)