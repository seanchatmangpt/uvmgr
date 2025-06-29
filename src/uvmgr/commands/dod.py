"""
uvmgr.commands.dod - Definition of Done Automation System
========================================================

Comprehensive Definition of Done automation that orchestrates entire project
lifecycles using Weaver Forge exoskeleton, DevOps integration, E2E testing,
and complete automation for enterprise-grade project delivery.

This module implements a revolutionary approach to project completion by:
1. **Exoskeleton Architecture**: Using Weaver Forge as the backbone for automation
2. **Complete DevOps Integration**: CI/CD, containers, infrastructure as code
3. **E2E Testing Automation**: From unit tests to integration to user acceptance
4. **Definition of Done Validation**: Automated verification of all completion criteria
5. **Exponential Technology Integration**: AI-driven optimization and acceleration

Key Features
-----------
• **Project Lifecycle Automation**: Complete automation from inception to production
• **Weaver Forge Exoskeleton**: Semantic convention-driven automation framework
• **DevOps Pipeline Integration**: GitHub Actions, containers, infrastructure
• **Multi-Layer Testing**: Unit, integration, E2E, performance, security
• **AI-Driven Quality Assurance**: Automated code review and optimization
• **Compliance Automation**: Security, accessibility, performance standards
• **Production Readiness Validation**: Comprehensive deployment verification

Available Commands
-----------------
- **complete**: Run complete Definition of Done automation for entire project
- **validate**: Validate all Definition of Done criteria
- **pipeline**: Set up complete DevOps pipeline automation
- **testing**: Execute comprehensive testing strategy (unit, integration, E2E)
- **security**: Run security audit and compliance validation
- **performance**: Execute performance testing and optimization
- **deploy**: Automated deployment with rollback capabilities
- **monitor**: Set up comprehensive monitoring and observability
- **exoskeleton**: Initialize Weaver Forge exoskeleton for project automation

Definition of Done Criteria
---------------------------
1. **Code Quality**: Linting, formatting, type checking, complexity analysis
2. **Testing Coverage**: Unit (90%+), integration (80%+), E2E (critical paths)
3. **Security**: Vulnerability scanning, dependency audit, security headers
4. **Performance**: Load testing, benchmarks, optimization validation
5. **Documentation**: API docs, user guides, deployment instructions
6. **DevOps**: CI/CD pipeline, containerization, infrastructure as code
7. **Monitoring**: OTEL integration, alerts, dashboards, SLIs/SLOs
8. **Compliance**: Accessibility, data protection, industry standards

Exoskeleton Architecture
-----------------------
The Weaver Forge exoskeleton provides:
- **Semantic Conventions**: Consistent automation patterns
- **OTEL Integration**: Complete observability from development to production
- **Workflow Orchestration**: BPMN-driven automation sequences
- **AI Integration**: Claude and DSPy for intelligent automation
- **Template System**: Reusable automation blueprints

Examples
--------
    >>> # Complete project automation
    >>> uvmgr dod complete --project myproject --environment production
    >>> 
    >>> # Initialize exoskeleton for existing project
    >>> uvmgr dod exoskeleton init --template enterprise
    >>> 
    >>> # Run specific validation
    >>> uvmgr dod validate --criteria security,performance,testing
    >>> 
    >>> # Set up DevOps pipeline
    >>> uvmgr dod pipeline create --provider github --environments dev,staging,prod

See Also
--------
- :mod:`uvmgr.commands.forge` : Weaver Forge workflow management
- :mod:`uvmgr.commands.agent` : BPMN workflow execution
- :mod:`uvmgr.commands.container` : Container management
- :mod:`uvmgr.commands.cicd` : CI/CD pipeline management
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.tree import Tree
from rich.text import Text

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes
from uvmgr.cli_utils import maybe_json
from uvmgr.ops import dod as dod_ops

app = typer.Typer(help="🎯 Definition of Done automation system with Weaver Forge exoskeleton")
console = Console()


@app.command("complete")
@instrument_command("dod_complete", track_args=True)
def complete_project(
    ctx: typer.Context,
    project_path: Optional[Path] = typer.Option(None, "--project", "-p", help="Project path (default: current directory)"),
    environment: str = typer.Option("development", "--environment", "-e", help="Target environment (development, staging, production)"),
    criteria: Optional[str] = typer.Option(None, "--criteria", "-c", help="Specific criteria to validate (comma-separated)"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip testing phase"),
    skip_security: bool = typer.Option(False, "--skip-security", help="Skip security validation"),
    skip_performance: bool = typer.Option(False, "--skip-performance", help="Skip performance testing"),
    auto_fix: bool = typer.Option(False, "--auto-fix", help="Automatically fix issues where possible"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Run validations in parallel"),
    report_format: str = typer.Option("rich", "--format", help="Report format: rich, json, markdown"),
    export_report: Optional[Path] = typer.Option(None, "--export", help="Export detailed report to file"),
):
    """
    🎯 Execute complete Definition of Done automation for entire project.
    
    This command orchestrates a comprehensive project completion workflow including:
    - Code quality validation and auto-fixing
    - Comprehensive testing strategy execution
    - Security audit and vulnerability assessment
    - Performance testing and optimization
    - DevOps pipeline validation
    - Monitoring and observability setup
    - Documentation completeness verification
    - Production readiness assessment
    
    Examples:
        uvmgr dod complete --environment production --auto-fix
        uvmgr dod complete --criteria testing,security --export report.json
    """
    project_path = project_path or Path.cwd()
    start_time = time.time()
    
    console.print(Panel(
        f"🎯 [bold]Definition of Done - Complete Project Automation[/bold]\n"
        f"Project: {project_path.name}\n"
        f"Environment: {environment}\n"
        f"Auto-fix: {'✅ Enabled' if auto_fix else '❌ Disabled'}\n"
        f"Parallel: {'✅ Enabled' if parallel else '❌ Sequential'}",
        title="DoD Automation",
        border_style="green"
    ))
    
    add_span_attributes(**{
        CliAttributes.CLI_COMMAND: "dod_complete",
        "dod.project": str(project_path),
        "dod.environment": environment,
        "dod.auto_fix": auto_fix,
        "dod.parallel": parallel,
    })
    
    try:
        # Parse criteria
        criteria_list = []
        if criteria:
            criteria_list = [c.strip() for c in criteria.split(",")]
        
        # Execute complete DoD automation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Initializing DoD automation...", total=100)
            
            result = dod_ops.execute_complete_automation(
                project_path=project_path,
                environment=environment,
                criteria=criteria_list,
                skip_tests=skip_tests,
                skip_security=skip_security,
                skip_performance=skip_performance,
                auto_fix=auto_fix,
                parallel=parallel,
                progress_callback=lambda pct, msg: progress.update(task, completed=pct, description=msg)
            )
            
            progress.update(task, completed=100, description="DoD automation complete!")
        
        # Display results
        _display_dod_results(result, report_format)
        
        # Export report if requested
        if export_report:
            _export_dod_report(result, export_report)
            console.print(f"\n📄 Detailed report exported to: {export_report}")
        
        # JSON output for CI/CD integration
        if ctx.meta.get("json"):
            maybe_json(ctx, {
                "success": result["success"],
                "criteria_passed": result["criteria_passed"],
                "total_criteria": result["total_criteria"],
                "completion_time": time.time() - start_time,
                "environment": environment,
                "auto_fixes_applied": result.get("auto_fixes_applied", 0)
            })
        
        add_span_event("dod_complete_finished", {
            "success": result["success"],
            "criteria_passed": result["criteria_passed"],
            "total_criteria": result["total_criteria"],
            "duration": time.time() - start_time
        })
        
        if not result["success"]:
            console.print(f"\n❌ [red]Definition of Done validation failed[/red]")
            console.print(f"Passed: {result['criteria_passed']}/{result['total_criteria']} criteria")
            raise typer.Exit(1)
        
        console.print(f"\n✅ [green]Definition of Done validation successful![/green]")
        console.print(f"🎉 Project is ready for {environment} deployment")
        
    except Exception as e:
        add_span_event("dod_complete_failed", {"error": str(e)})
        console.print(f"[red]❌ DoD automation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("exoskeleton")
@instrument_command("dod_exoskeleton", track_args=True)
def setup_exoskeleton(
    ctx: typer.Context,
    action: str = typer.Argument(..., help="Action: init, update, validate, status"),
    project_path: Optional[Path] = typer.Option(None, "--project", "-p", help="Project path"),
    template: str = typer.Option("standard", "--template", "-t", help="Exoskeleton template: standard, enterprise, ai-native"),
    force: bool = typer.Option(False, "--force", help="Force overwrite existing configuration"),
):
    """
    🦴 Initialize or manage Weaver Forge exoskeleton for project automation.
    
    The exoskeleton provides a complete automation framework using:
    - Semantic conventions for consistent automation
    - OTEL integration for full observability
    - BPMN workflows for complex orchestration
    - AI integration for intelligent automation
    - Template system for reusable patterns
    
    Templates:
        standard: Basic DoD automation for typical projects
        enterprise: Advanced automation with compliance and governance
        ai-native: AI-first automation with Claude and DSPy integration
    
    Examples:
        uvmgr dod exoskeleton init --template enterprise
        uvmgr dod exoskeleton validate --project /path/to/project
    """
    project_path = project_path or Path.cwd()
    
    console.print(Panel(
        f"🦴 [bold]Weaver Forge Exoskeleton - {action.title()}[/bold]\n"
        f"Project: {project_path.name}\n"
        f"Template: {template}\n"
        f"Force: {'✅ Yes' if force else '❌ No'}",
        title="Exoskeleton Management",
        border_style="cyan"
    ))
    
    try:
        if action == "init":
            result = dod_ops.initialize_exoskeleton(project_path, template, force)
            _display_exoskeleton_init_result(result)
        elif action == "update":
            result = dod_ops.update_exoskeleton(project_path, template)
            _display_exoskeleton_update_result(result)
        elif action == "validate":
            result = dod_ops.validate_exoskeleton(project_path)
            _display_exoskeleton_validation_result(result)
        elif action == "status":
            result = dod_ops.get_exoskeleton_status(project_path)
            _display_exoskeleton_status(result)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: init, update, validate, status")
            raise typer.Exit(1)
        
        if ctx.meta.get("json"):
            maybe_json(ctx, result)
            
    except Exception as e:
        console.print(f"[red]❌ Exoskeleton {action} failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("pipeline")
@instrument_command("dod_pipeline", track_args=True)
def setup_pipeline(
    ctx: typer.Context,
    action: str = typer.Argument(..., help="Action: create, update, validate, deploy"),
    provider: str = typer.Option("github", "--provider", "-p", help="CI/CD provider: github, gitlab, azure"),
    environments: str = typer.Option("dev,staging,prod", "--environments", "-e", help="Environments (comma-separated)"),
    features: Optional[str] = typer.Option(None, "--features", "-f", help="Pipeline features: testing,security,performance,deploy"),
    template: str = typer.Option("enterprise", "--template", "-t", help="Pipeline template"),
):
    """
    🚀 Set up comprehensive DevOps pipeline automation.
    
    Creates complete CI/CD pipelines with:
    - Multi-environment deployment (dev, staging, production)
    - Comprehensive testing strategy
    - Security scanning and compliance
    - Performance testing and monitoring
    - Container orchestration
    - Infrastructure as Code
    - Automated rollback capabilities
    
    Examples:
        uvmgr dod pipeline create --provider github --environments dev,prod
        uvmgr dod pipeline validate --features testing,security
    """
    environments_list = [env.strip() for env in environments.split(",")]
    features_list = []
    if features:
        features_list = [f.strip() for f in features.split(",")]
    
    console.print(Panel(
        f"🚀 [bold]DevOps Pipeline Automation - {action.title()}[/bold]\n"
        f"Provider: {provider}\n"
        f"Environments: {', '.join(environments_list)}\n"
        f"Features: {', '.join(features_list) if features_list else 'All'}\n"
        f"Template: {template}",
        title="Pipeline Setup",
        border_style="blue"
    ))
    
    try:
        if action == "create":
            result = dod_ops.create_pipeline(provider, environments_list, features_list, template)
            _display_pipeline_creation_result(result)
        elif action == "update":
            result = dod_ops.update_pipeline(provider, environments_list, features_list)
            _display_pipeline_update_result(result)
        elif action == "validate":
            result = dod_ops.validate_pipeline(provider, environments_list)
            _display_pipeline_validation_result(result)
        elif action == "deploy":
            result = dod_ops.deploy_pipeline(provider, environments_list[0] if environments_list else "dev")
            _display_pipeline_deployment_result(result)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            raise typer.Exit(1)
        
        if ctx.meta.get("json"):
            maybe_json(ctx, result)
            
    except Exception as e:
        console.print(f"[red]❌ Pipeline {action} failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("testing")
@instrument_command("dod_testing", track_args=True)
def comprehensive_testing(
    ctx: typer.Context,
    strategy: str = typer.Option("comprehensive", "--strategy", "-s", help="Testing strategy: unit, integration, e2e, comprehensive"),
    coverage_threshold: int = typer.Option(90, "--coverage", "-c", help="Code coverage threshold percentage"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Run tests in parallel"),
    performance: bool = typer.Option(False, "--performance", help="Include performance testing"),
    security: bool = typer.Option(False, "--security", help="Include security testing"),
    ai_generated: bool = typer.Option(False, "--ai-generated", help="Generate additional AI-powered tests"),
):
    """
    🧪 Execute comprehensive testing strategy automation.
    
    Implements multi-layer testing approach:
    - Unit Testing: High coverage with edge cases
    - Integration Testing: API and service integration
    - E2E Testing: Critical user journeys
    - Performance Testing: Load and stress testing
    - Security Testing: Vulnerability and penetration testing
    - AI-Generated Testing: Claude-powered test generation
    
    Examples:
        uvmgr dod testing --strategy comprehensive --coverage 95
        uvmgr dod testing --strategy e2e --performance --security
    """
    console.print(Panel(
        f"🧪 [bold]Comprehensive Testing Strategy - {strategy.title()}[/bold]\n"
        f"Coverage Threshold: {coverage_threshold}%\n"
        f"Parallel Execution: {'✅ Yes' if parallel else '❌ No'}\n"
        f"Performance: {'✅ Included' if performance else '❌ Skipped'}\n"
        f"Security: {'✅ Included' if security else '❌ Skipped'}\n"
        f"AI-Generated: {'✅ Enabled' if ai_generated else '❌ Disabled'}",
        title="Testing Automation",
        border_style="yellow"
    ))
    
    try:
        result = dod_ops.execute_comprehensive_testing(
            strategy=strategy,
            coverage_threshold=coverage_threshold,
            parallel=parallel,
            include_performance=performance,
            include_security=security,
            ai_generated=ai_generated
        )
        
        _display_testing_results(result)
        
        if ctx.meta.get("json"):
            maybe_json(ctx, result)
        
        if not result["success"]:
            console.print(f"\n❌ [red]Testing validation failed[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n✅ [green]All tests passed successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Testing automation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("dod_validate", track_args=True)
def validate_criteria(
    ctx: typer.Context,
    criteria: Optional[str] = typer.Option(None, "--criteria", "-c", help="Specific criteria (comma-separated)"),
    environment: str = typer.Option("development", "--environment", "-e", help="Target environment"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed validation results"),
    fix_issues: bool = typer.Option(False, "--fix", help="Attempt to fix validation issues"),
):
    """
    ✅ Validate specific Definition of Done criteria.
    
    Available criteria:
    - code_quality: Linting, formatting, type checking
    - testing: Unit, integration, E2E test coverage
    - security: Vulnerability scanning, dependency audit
    - performance: Performance benchmarks and optimization
    - documentation: API docs, user guides, deployment docs
    - devops: CI/CD pipeline, containerization
    - monitoring: OTEL integration, alerts, dashboards
    - compliance: Accessibility, data protection standards
    
    Examples:
        uvmgr dod validate --criteria code_quality,testing
        uvmgr dod validate --environment production --detailed --fix
    """
    criteria_list = []
    if criteria:
        criteria_list = [c.strip() for c in criteria.split(",")]
    
    console.print(Panel(
        f"✅ [bold]Definition of Done Validation[/bold]\n"
        f"Criteria: {', '.join(criteria_list) if criteria_list else 'All'}\n"
        f"Environment: {environment}\n"
        f"Detailed: {'✅ Yes' if detailed else '❌ No'}\n"
        f"Auto-fix: {'✅ Enabled' if fix_issues else '❌ Disabled'}",
        title="Criteria Validation",
        border_style="magenta"
    ))
    
    try:
        result = dod_ops.validate_specific_criteria(
            criteria=criteria_list,
            environment=environment,
            detailed=detailed,
            fix_issues=fix_issues
        )
        
        _display_validation_results(result, detailed)
        
        if ctx.meta.get("json"):
            maybe_json(ctx, result)
        
        if not result["success"]:
            console.print(f"\n❌ [red]Validation failed[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n✅ [green]All validations passed![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1)


# Helper functions for display
def _display_dod_results(result: Dict[str, Any], format_type: str):
    """Display Definition of Done results."""
    if format_type == "rich":
        # Create results tree
        tree = Tree("🎯 Definition of Done Results")
        
        # Overall status
        status_icon = "✅" if result["success"] else "❌"
        tree.add(f"{status_icon} Overall Status: {'PASSED' if result['success'] else 'FAILED'}")
        
        # Criteria breakdown
        criteria_node = tree.add("📋 Criteria Results")
        for criterion, details in result.get("criteria_results", {}).items():
            icon = "✅" if details["passed"] else "❌"
            criteria_node.add(f"{icon} {criterion}: {details['score']:.1f}%")
        
        # Performance metrics
        if "performance_metrics" in result:
            metrics_node = tree.add("📊 Performance Metrics")
            for metric, value in result["performance_metrics"].items():
                metrics_node.add(f"• {metric}: {value}")
        
        console.print(tree)


def _display_exoskeleton_init_result(result: Dict[str, Any]):
    """Display exoskeleton initialization results."""
    console.print("🦴 [green]Exoskeleton initialized successfully![/green]")
    
    table = Table(title="Created Files")
    table.add_column("File", style="cyan")
    table.add_column("Description", style="white")
    
    for file_info in result.get("created_files", []):
        table.add_row(file_info["path"], file_info["description"])
    
    console.print(table)


def _display_testing_results(result: Dict[str, Any]):
    """Display comprehensive testing results."""
    # Test summary table
    table = Table(title="Testing Results Summary")
    table.add_column("Test Type", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Coverage", style="green")
    table.add_column("Duration", style="yellow")
    
    for test_type, details in result.get("test_results", {}).items():
        status = "✅ PASSED" if details["passed"] else "❌ FAILED"
        coverage = f"{details.get('coverage', 0):.1f}%"
        duration = f"{details.get('duration', 0):.2f}s"
        table.add_row(test_type.title(), status, coverage, duration)
    
    console.print(table)


def _display_validation_results(result: Dict[str, Any], detailed: bool):
    """Display validation results."""
    if detailed:
        # Detailed view with individual check results
        for criterion, details in result.get("criteria_details", {}).items():
            panel_style = "green" if details["passed"] else "red"
            panel_title = f"{'✅' if details['passed'] else '❌'} {criterion.title()}"
            
            content = f"Score: {details['score']:.1f}%\n"
            content += f"Checks: {details['checks_passed']}/{details['total_checks']}\n"
            
            if details.get("issues"):
                content += "\nIssues:\n"
                for issue in details["issues"][:5]:  # Show top 5 issues
                    content += f"• {issue}\n"
            
            console.print(Panel(content, title=panel_title, border_style=panel_style))
    else:
        # Simple summary view
        _display_dod_results(result, "rich")


def _display_pipeline_creation_result(result: Dict[str, Any]):
    """Display pipeline creation results."""
    console.print("🚀 [green]Pipeline created successfully![/green]")


def _display_pipeline_update_result(result: Dict[str, Any]):
    """Display pipeline update results.""" 
    console.print("🔄 [green]Pipeline updated successfully![/green]")


def _display_pipeline_validation_result(result: Dict[str, Any]):
    """Display pipeline validation results."""
    status = "✅ VALID" if result["valid"] else "❌ INVALID"
    console.print(f"🔍 Pipeline Validation: {status}")


def _display_pipeline_deployment_result(result: Dict[str, Any]):
    """Display pipeline deployment results."""
    console.print("🚀 [green]Pipeline deployed successfully![/green]")


def _export_dod_report(result: Dict[str, Any], export_path: Path):
    """Export detailed DoD report to file."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "success": result["success"],
            "criteria_passed": result["criteria_passed"],
            "total_criteria": result["total_criteria"],
            "completion_percentage": (result["criteria_passed"] / result["total_criteria"]) * 100
        },
        "criteria_results": result.get("criteria_results", {}),
        "performance_metrics": result.get("performance_metrics", {}),
        "recommendations": result.get("recommendations", []),
        "auto_fixes_applied": result.get("auto_fixes_applied", [])
    }
    
    if export_path.suffix.lower() == ".json":
        with open(export_path, "w") as f:
            json.dump(report_data, f, indent=2)
    else:
        # Generate markdown report
        markdown_content = _generate_markdown_report(report_data)
        with open(export_path, "w") as f:
            f.write(markdown_content)


def _generate_markdown_report(data: Dict[str, Any]) -> str:
    """Generate markdown report from DoD results."""
    md = f"""# Definition of Done Report

**Generated:** {data['timestamp']}
**Success:** {'✅ PASSED' if data['summary']['success'] else '❌ FAILED'}
**Completion:** {data['summary']['completion_percentage']:.1f}%

## Summary

- **Criteria Passed:** {data['summary']['criteria_passed']}/{data['summary']['total_criteria']}
- **Overall Status:** {'PASSED' if data['summary']['success'] else 'FAILED'}

## Criteria Results

"""
    
    for criterion, details in data.get('criteria_results', {}).items():
        status = '✅ PASSED' if details['passed'] else '❌ FAILED'
        md += f"### {criterion.title()} {status}\n"
        md += f"- **Score:** {details['score']:.1f}%\n"
        md += f"- **Checks:** {details.get('checks_passed', 0)}/{details.get('total_checks', 0)}\n\n"
    
    if data.get('recommendations'):
        md += "## Recommendations\n\n"
        for rec in data['recommendations']:
            md += f"- {rec}\n"
    
    return md