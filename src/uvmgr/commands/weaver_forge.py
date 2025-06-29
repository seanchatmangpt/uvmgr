"""
uvmgr.commands.weaver_forge - Weaver Forge Integration (Hygen-like)
================================================================

Weaver Forge integration for uvmgr, providing Hygen-like template-based
code generation and scaffolding with DSPy-powered intelligent generation.

This module provides CLI commands for managing templates, generating code,
and creating scaffolds using Weaver Forge's intelligent generation capabilities.

Key Features
-----------
• **Template Management**: Create, manage, and version templates
• **Code Generation**: Generate code from templates with intelligent prompts
• **Scaffolding**: Create project structures and boilerplate
• **Interactive Generation**: Guided template creation and customization
• **DSPy Integration**: Intelligent decision making for code generation
• **OpenTelemetry**: Comprehensive instrumentation and monitoring
• **Lean Six Sigma**: Systematic template validation and improvement

Available Commands
-----------------
- **init**: Initialize Weaver Forge in project
- **generate**: Generate code from templates
- **create**: Create new templates
- **list**: List available templates
- **validate**: Validate templates using Lean Six Sigma
- **scaffold**: Create project scaffolds
- **prompt**: Interactive prompt-based generation
- **status**: Show Weaver Forge status and metrics
- **bulk-generate**: Generate multiple items from template in bulk
- **bulk-scaffold**: Create multiple project scaffolds in bulk
- **batch**: Generate from a batch specification file
- **bulk-create**: Create multiple templates in bulk
- **bulk-validate**: Validate multiple templates in bulk

Examples
--------
    >>> # Initialize Weaver Forge
    >>> uvmgr weaver-forge init
    >>> 
    >>> # Generate component from template
    >>> uvmgr weaver-forge generate component UserProfile
    >>> 
    >>> # Create new template
    >>> uvmgr weaver-forge create api-endpoint
    >>> 
    >>> # Scaffold new project
    >>> uvmgr weaver-forge scaffold react-app my-app

See Also
--------
- :mod:`uvmgr.ops.weaver_forge` : Weaver Forge operations
- :mod:`uvmgr.commands.forge` : Original Forge command
- :mod:`uvmgr.core.agi_reasoning` : AGI reasoning capabilities
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt, Confirm

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes, AIAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.ops.weaver_forge import (
    init_weaver_forge,
    generate_from_template,
    create_template,
    list_templates,
    validate_templates,
    create_scaffold,
    interactive_prompt_generation,
    get_weaver_forge_status,
    generate_bulk_from_templates,
    generate_bulk_scaffolds,
    generate_from_batch_file,
    create_bulk_template,
    validate_bulk_templates
)

app = typer.Typer(help="Weaver Forge integration with Hygen-like capabilities")
console = Console()


class TemplateType(Enum):
    """Template types for Weaver Forge."""
    COMPONENT = "component"
    API = "api"
    TEST = "test"
    DOCUMENTATION = "documentation"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class ScaffoldType(Enum):
    """Scaffold types for Weaver Forge."""
    REACT_APP = "react-app"
    NODE_API = "node-api"
    PYTHON_PACKAGE = "python-package"
    MICROSERVICE = "microservice"
    FULL_STACK = "full-stack"
    CUSTOM = "custom"


@app.command("init")
@instrument_command("weaver_forge_init", track_args=True)
def init_forge(
    project_path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Project path for initialization"
    ),
    template_source: Optional[str] = typer.Option(
        None,
        "--template-source",
        "-s",
        help="Template source repository"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinitialization"
    ),
):
    """
    Initialize Weaver Forge in project.
    
    This command initializes Weaver Forge with Hygen-like capabilities,
    setting up template directories and default templates.
    
    Examples:
        uvmgr weaver-forge init
        uvmgr weaver-forge init --path ./my-project
        uvmgr weaver-forge init --template-source custom/templates
    """
    add_span_attributes(**{
        "weaver_forge.operation": "init",
        "weaver_forge.force": force,
    })
    
    console.print(f"🔧 [bold cyan]Initializing Weaver Forge[/bold cyan]")
    if project_path:
        console.print(f"📁 Project Path: {project_path}")
    if template_source:
        console.print(f"📚 Template Source: {template_source}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Initialize Weaver Forge
            task1 = progress.add_task("Initializing Weaver Forge...", total=1)
            init_result = init_weaver_forge(
                project_path=project_path,
                template_source=template_source,
                force=force
            )
            progress.advance(task1)
        
        # Display initialization summary
        _display_init_summary(init_result)
        
        add_span_event("weaver_forge.initialized", {
            "project_path": str(init_result["project_path"]),
            "templates_created": init_result["templates_created"],
            "scaffolds_created": init_result["scaffolds_created"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Weaver Forge initialization failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("generate")
@instrument_command("weaver_forge_generate", track_args=True)
def generate_code(
    template_name: str = typer.Argument(..., help="Template name to use"),
    name: str = typer.Argument(..., help="Name for the generated item"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for generated files"
    ),
    parameters: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="Template parameters (JSON string)"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive parameter input"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be generated without creating files"
    ),
):
    """
    Generate code from templates.
    
    This command generates code from Weaver Forge templates using
    Hygen-like syntax with DSPy-powered intelligent generation.
    
    Examples:
        uvmgr weaver-forge generate component UserProfile
        uvmgr weaver-forge generate api-endpoint users --interactive
        uvmgr weaver-forge generate test UserService --dry-run
    """
    add_span_attributes(**{
        "weaver_forge.operation": "generate",
        "weaver_forge.template": template_name,
        "weaver_forge.name": name,
        "weaver_forge.interactive": interactive,
        "weaver_forge.dry_run": dry_run,
    })
    
    console.print(f"🚀 [bold cyan]Generating Code with Weaver Forge[/bold cyan]")
    console.print(f"📄 Template: {template_name}")
    console.print(f"📝 Name: {name}")
    console.print(f"💬 Interactive: {'✅' if interactive else '❌'}")
    console.print(f"🔍 Dry Run: {'✅' if dry_run else '❌'}")
    
    # Parse parameters
    template_params = {}
    if parameters:
        try:
            template_params = json.loads(parameters)
        except json.JSONDecodeError:
            console.print("[red]❌ Invalid JSON parameters[/red]")
            raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating code...", total=1)
            
            # Generate code
            generation_result = generate_from_template(
                template_name=template_name,
                name=name,
                output_path=output_path,
                parameters=template_params,
                interactive=interactive,
                dry_run=dry_run
            )
            progress.advance(task)
        
        # Display generation results
        _display_generation_results(generation_result, dry_run)
        
        add_span_event("weaver_forge.generated", {
            "template": template_name,
            "name": name,
            "files_created": len(generation_result.get("files", [])),
            "dry_run": dry_run,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Code generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
@instrument_command("weaver_forge_create", track_args=True)
def create_new_template(
    template_name: str = typer.Argument(..., help="Template name"),
    template_type: TemplateType = typer.Option(
        TemplateType.CUSTOM,
        "--type",
        "-t",
        help="Template type"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Template description"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i",
        help="Interactive template creation"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for template"
    ),
):
    """
    Create new templates.
    
    This command creates new Weaver Forge templates with Hygen-like
    structure and DSPy-powered intelligent content generation.
    
    Examples:
        uvmgr weaver-forge create my-component --type component
        uvmgr weaver-forge create api-service --type api --interactive
        uvmgr weaver-forge create test-suite --type test
    """
    add_span_attributes(**{
        "weaver_forge.operation": "create",
        "weaver_forge.template_name": template_name,
        "weaver_forge.template_type": template_type.value,
        "weaver_forge.interactive": interactive,
    })
    
    console.print(f"📝 [bold cyan]Creating New Template[/bold cyan]")
    console.print(f"📋 Name: {template_name}")
    console.print(f"📄 Type: {template_type.value}")
    console.print(f"💬 Interactive: {'✅' if interactive else '❌'}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Creating template...", total=1)
            
            # Create template
            template_result = create_template(
                template_name=template_name,
                template_type=template_type.value,
                description=description,
                interactive=interactive,
                output_dir=output_dir
            )
            progress.advance(task)
        
        # Display template creation results
        _display_template_creation_result(template_result)
        
        add_span_event("weaver_forge.template_created", {
            "template_name": template_name,
            "template_type": template_type.value,
            "output_path": str(template_result["output_path"]),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Template creation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
@instrument_command("weaver_forge_list", track_args=True)
def list_available_templates(
    template_type: Optional[TemplateType] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by template type"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed template information"
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, tree"
    ),
):
    """
    List available templates.
    
    This command lists all available Weaver Forge templates with
    their metadata and usage information.
    
    Examples:
        uvmgr weaver-forge list
        uvmgr weaver-forge list --type component --detailed
        uvmgr weaver-forge list --format json
    """
    add_span_attributes(**{
        "weaver_forge.operation": "list",
        "weaver_forge.template_type": template_type.value if template_type else None,
        "weaver_forge.detailed": detailed,
    })
    
    console.print(f"📚 [bold cyan]Available Templates[/bold cyan]")
    if template_type:
        console.print(f"🔍 Filter: {template_type.value}")
    console.print(f"📊 Detailed: {'✅' if detailed else '❌'}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Loading templates...", total=1)
            
            # List templates
            templates_result = list_templates(
                template_type=template_type.value if template_type else None,
                detailed=detailed
            )
            progress.advance(task)
        
        # Display templates
        if format == "json":
            console.print(json.dumps(templates_result, indent=2))
        elif format == "tree":
            _display_templates_tree(templates_result)
        else:
            _display_templates_table(templates_result, detailed)
        
        add_span_event("weaver_forge.templates_listed", {
            "templates_count": len(templates_result.get("templates", [])),
            "template_type": template_type.value if template_type else "all",
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Template listing failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("weaver_forge_validate", track_args=True)
def validate_templates_cmd(
    template_name: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Specific template to validate"
    ),
    fix_issues: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix validation issues"
    ),
    output_report: Optional[Path] = typer.Option(
        None,
        "--report",
        "-r",
        help="Output validation report to file"
    ),
):
    """
    Validate templates using Lean Six Sigma principles.
    
    This command validates Weaver Forge templates for quality,
    consistency, and best practices using systematic analysis.
    
    Examples:
        uvmgr weaver-forge validate
        uvmgr weaver-forge validate --template my-component --fix
        uvmgr weaver-forge validate --report validation-report.json
    """
    add_span_attributes(**{
        "weaver_forge.operation": "validate",
        "weaver_forge.template": template_name,
        "weaver_forge.fix_issues": fix_issues,
    })
    
    console.print(f"🔍 [bold cyan]Validating Templates[/bold cyan]")
    if template_name:
        console.print(f"📄 Template: {template_name}")
    else:
        console.print("📄 All templates")
    console.print(f"🔧 Auto-fix: {'✅' if fix_issues else '❌'}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Validating templates...", total=1)
            
            # Validate templates
            validation_result = validate_templates(
                template_name=template_name,
                fix_issues=fix_issues
            )
            progress.advance(task)
        
        # Display validation results
        _display_validation_results(validation_result)
        
        # Save report if requested
        if output_report:
            output_report.write_text(json.dumps(validation_result, indent=2))
            console.print(f"💾 Validation report saved to: {output_report}")
        
        add_span_event("weaver_forge.validated", {
            "templates_validated": validation_result.get("templates_validated", 0),
            "issues_found": len(validation_result.get("issues", [])),
            "fixes_applied": len(validation_result.get("fixes_applied", [])),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Template validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("scaffold")
@instrument_command("weaver_forge_scaffold", track_args=True)
def create_project_scaffold(
    scaffold_type: ScaffoldType = typer.Argument(..., help="Type of scaffold to create"),
    project_name: str = typer.Argument(..., help="Project name"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for scaffold"
    ),
    parameters: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="Scaffold parameters (JSON string)"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i",
        help="Interactive scaffold creation"
    ),
):
    """
    Create project scaffolds.
    
    This command creates complete project scaffolds using Weaver Forge
    templates with Hygen-like structure and intelligent generation.
    
    Examples:
        uvmgr weaver-forge scaffold react-app my-app
        uvmgr weaver-forge scaffold node-api backend-service --interactive
        uvmgr weaver-forge scaffold python-package my-lib
    """
    add_span_attributes(**{
        "weaver_forge.operation": "scaffold",
        "weaver_forge.scaffold_type": scaffold_type.value,
        "weaver_forge.project_name": project_name,
        "weaver_forge.interactive": interactive,
    })
    
    console.print(f"🏗️ [bold cyan]Creating Project Scaffold[/bold cyan]")
    console.print(f"📋 Type: {scaffold_type.value}")
    console.print(f"📝 Project: {project_name}")
    console.print(f"💬 Interactive: {'✅' if interactive else '❌'}")
    
    # Parse parameters
    scaffold_params = {}
    if parameters:
        try:
            scaffold_params = json.loads(parameters)
        except json.JSONDecodeError:
            console.print("[red]❌ Invalid JSON parameters[/red]")
            raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Creating scaffold...", total=1)
            
            # Create scaffold
            scaffold_result = create_scaffold(
                scaffold_type=scaffold_type.value,
                project_name=project_name,
                output_path=output_path,
                parameters=scaffold_params,
                interactive=interactive
            )
            progress.advance(task)
        
        # Display scaffold results
        _display_scaffold_results(scaffold_result)
        
        add_span_event("weaver_forge.scaffold_created", {
            "scaffold_type": scaffold_type.value,
            "project_name": project_name,
            "files_created": len(scaffold_result.get("files", [])),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Scaffold creation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("prompt")
@instrument_command("weaver_forge_prompt", track_args=True)
def interactive_prompt(
    description: str = typer.Argument(..., help="Description of what to generate"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for generated files"
    ),
    template_hint: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Hint for template type"
    ),
):
    """
    Interactive prompt-based generation.
    
    This command provides interactive prompt-based code generation
    using DSPy-powered intelligent analysis and Weaver Forge templates.
    
    Examples:
        uvmgr weaver-forge prompt "Create a user authentication component"
        uvmgr weaver-forge prompt "Build a REST API for user management"
        uvmgr weaver-forge prompt "Generate tests for UserService class"
    """
    add_span_attributes(**{
        "weaver_forge.operation": "prompt",
        "weaver_forge.description": description,
        "weaver_forge.template_hint": template_hint,
    })
    
    console.print(f"💬 [bold cyan]Interactive Prompt Generation[/bold cyan]")
    console.print(f"📝 Description: {description}")
    if template_hint:
        console.print(f"💡 Template Hint: {template_hint}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Analyzing and generating...", total=1)
            
            # Interactive generation
            prompt_result = interactive_prompt_generation(
                description=description,
                output_path=output_path,
                template_hint=template_hint
            )
            progress.advance(task)
        
        # Display prompt results
        _display_prompt_results(prompt_result)
        
        add_span_event("weaver_forge.prompt_generated", {
            "description": description,
            "files_created": len(prompt_result.get("files", [])),
            "template_used": prompt_result.get("template_used"),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Prompt generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
@instrument_command("weaver_forge_status", track_args=True)
def show_status(
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed status information"
    ),
    include_metrics: bool = typer.Option(
        True,
        "--metrics/--no-metrics",
        help="Include performance metrics"
    ),
):
    """
    Show Weaver Forge status and metrics.
    
    This command displays the current status of Weaver Forge, including
    template statistics, generation metrics, and performance indicators.
    
    Examples:
        uvmgr weaver-forge status
        uvmgr weaver-forge status --detailed --no-metrics
    """
    add_span_attributes(**{
        "weaver_forge.operation": "status",
        "weaver_forge.detailed": detailed,
        "weaver_forge.include_metrics": include_metrics,
    })
    
    console.print("📊 [bold cyan]Weaver Forge Status[/bold cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Gathering status information...", total=1)
            
            # Get status
            status_info = get_weaver_forge_status(detailed=detailed, include_metrics=include_metrics)
            progress.advance(task)
        
        # Display status
        _display_status_table(status_info, detailed, include_metrics)
        
        add_span_event("weaver_forge.status.displayed", {
            "templates_count": status_info.get("templates_count", 0),
            "detailed": detailed,
            "metrics_included": include_metrics,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Status retrieval failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("bulk-generate")
@instrument_command("weaver_forge_bulk_generate", track_args=True)
def bulk_generate_code(
    template_name: str = typer.Argument(..., help="Template name to use"),
    names: List[str] = typer.Argument(..., help="Names for the generated items"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for generated files"
    ),
    parameters: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="Template parameters (JSON string)"
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Run generations in parallel"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be generated without creating files"
    ),
):
    """
    Generate multiple items from template in bulk.
    
    This command generates multiple items using the same template,
    similar to Hygen's bulk generation capabilities.
    
    Examples:
        uvmgr weaver-forge bulk-generate component UserProfile ProductCard OrderItem
        uvmgr weaver-forge bulk-generate api users products orders --parallel
        uvmgr weaver-forge bulk-generate component Button Input Select --params '{"style": "styled-components"}'
    """
    add_span_attributes(**{
        "weaver_forge.operation": "bulk_generate",
        "weaver_forge.template": template_name,
        "weaver_forge.items_count": len(names),
        "weaver_forge.parallel": parallel,
        "weaver_forge.dry_run": dry_run,
    })
    
    console.print(f"🔧 [bold cyan]Bulk Generating {len(names)} items[/bold cyan]")
    console.print(f"📋 Template: {template_name}")
    console.print(f"📝 Items: {', '.join(names)}")
    if parallel:
        console.print(f"⚡ Parallel execution: enabled")
    if dry_run:
        console.print(f"👀 Dry run mode: enabled")
    
    # Parse parameters
    parsed_params = {}
    if parameters:
        try:
            parsed_params = json.loads(parameters)
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid JSON parameters: {e}[/red]")
            raise typer.Exit(1)
    
    # Prepare generation specifications
    generation_specs = []
    for name in names:
        spec = {
            "template": template_name,
            "name": name,
            "parameters": parsed_params,
            "subdir": name.lower().replace(" ", "_")
        }
        generation_specs.append(spec)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Bulk generation
            task1 = progress.add_task(f"Generating {len(names)} items...", total=len(names))
            
            bulk_result = generate_bulk_from_templates(
                generation_specs=generation_specs,
                output_path=output_path,
                parallel=parallel,
                dry_run=dry_run
            )
            
            progress.advance(task1, len(names))
        
        # Display bulk generation results
        _display_bulk_generation_results(bulk_result, dry_run)
        
        add_span_event("weaver_forge.bulk_generated", {
            "template": template_name,
            "items_count": len(names),
            "successful": bulk_result["successful"],
            "failed": bulk_result["failed"],
            "total_files": bulk_result["total_files"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Bulk generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("bulk-scaffold")
@instrument_command("weaver_forge_bulk_scaffold", track_args=True)
def bulk_create_scaffolds(
    scaffold_type: ScaffoldType = typer.Argument(..., help="Type of scaffold to create"),
    project_names: List[str] = typer.Argument(..., help="Project names"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for scaffolds"
    ),
    parameters: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="Scaffold parameters (JSON string)"
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Run scaffold generation in parallel"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be generated without creating files"
    ),
):
    """
    Create multiple project scaffolds in bulk.
    
    This command creates multiple project scaffolds of the same type,
    useful for creating multiple similar projects at once.
    
    Examples:
        uvmgr weaver-forge bulk-scaffold react-app frontend admin dashboard
        uvmgr weaver-forge bulk-scaffold node-api users-api products-api orders-api --parallel
        uvmgr weaver-forge bulk-scaffold python-package utils core models --params '{"testing": "pytest"}'
    """
    add_span_attributes(**{
        "weaver_forge.operation": "bulk_scaffold",
        "weaver_forge.scaffold_type": scaffold_type.value,
        "weaver_forge.projects_count": len(project_names),
        "weaver_forge.parallel": parallel,
        "weaver_forge.dry_run": dry_run,
    })
    
    console.print(f"🏗️ [bold cyan]Bulk Creating {len(project_names)} scaffolds[/bold cyan]")
    console.print(f"📋 Scaffold Type: {scaffold_type.value}")
    console.print(f"📝 Projects: {', '.join(project_names)}")
    if parallel:
        console.print(f"⚡ Parallel execution: enabled")
    if dry_run:
        console.print(f"👀 Dry run mode: enabled")
    
    # Parse parameters
    parsed_params = {}
    if parameters:
        try:
            parsed_params = json.loads(parameters)
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid JSON parameters: {e}[/red]")
            raise typer.Exit(1)
    
    # Prepare scaffold specifications
    scaffold_specs = []
    for name in project_names:
        spec = {
            "type": scaffold_type.value,
            "name": name,
            "parameters": parsed_params,
            "subdir": name.lower().replace(" ", "_")
        }
        scaffold_specs.append(spec)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Bulk scaffold generation
            task1 = progress.add_task(f"Creating {len(project_names)} scaffolds...", total=len(project_names))
            
            bulk_result = generate_bulk_scaffolds(
                scaffold_specs=scaffold_specs,
                output_path=output_path,
                parallel=parallel,
                dry_run=dry_run
            )
            
            progress.advance(task1, len(project_names))
        
        # Display bulk scaffold results
        _display_bulk_scaffold_results(bulk_result, dry_run)
        
        add_span_event("weaver_forge.bulk_scaffolded", {
            "scaffold_type": scaffold_type.value,
            "projects_count": len(project_names),
            "successful": bulk_result["successful"],
            "failed": bulk_result["failed"],
            "total_files": bulk_result["total_files"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Bulk scaffold generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("batch")
@instrument_command("weaver_forge_batch", track_args=True)
def batch_generate(
    batch_file: Path = typer.Argument(..., help="Batch specification file (JSON/YAML)"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for generated files"
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Run generations in parallel"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be generated without creating files"
    ),
):
    """
    Generate from a batch specification file.
    
    This command reads a batch specification file (JSON/YAML) and generates
    multiple templates and scaffolds according to the specification.
    
    Examples:
        uvmgr weaver-forge batch batch-spec.json
        uvmgr weaver-forge batch batch-spec.yaml --parallel --dry-run
        uvmgr weaver-forge batch my-batch.yml --output ./generated
    """
    add_span_attributes(**{
        "weaver_forge.operation": "batch",
        "weaver_forge.batch_file": str(batch_file),
        "weaver_forge.parallel": parallel,
        "weaver_forge.dry_run": dry_run,
    })
    
    console.print(f"📋 [bold cyan]Batch Generation from {batch_file.name}[/bold cyan]")
    console.print(f"📄 Batch File: {batch_file}")
    if parallel:
        console.print(f"⚡ Parallel execution: enabled")
    if dry_run:
        console.print(f"👀 Dry run mode: enabled")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Load and process batch file
            task1 = progress.add_task("Processing batch specification...", total=1)
            
            batch_result = generate_from_batch_file(
                batch_file=batch_file,
                output_path=output_path,
                parallel=parallel,
                dry_run=dry_run
            )
            
            progress.advance(task1)
        
        # Display batch generation results
        _display_batch_results(batch_result, dry_run)
        
        add_span_event("weaver_forge.batch_completed", {
            "batch_file": str(batch_file),
            "total_files": batch_result["total_files"],
            "total_errors": batch_result["total_errors"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Batch generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("bulk-create")
@instrument_command("weaver_forge_bulk_create", track_args=True)
def bulk_create_templates(
    template_specs_file: Path = typer.Argument(..., help="Template specifications file (JSON/YAML)"),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for templates"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive template creation"
    ),
):
    """
    Create multiple templates in bulk.
    
    This command reads a template specifications file and creates multiple
    templates according to the specification.
    
    Examples:
        uvmgr weaver-forge bulk-create template-specs.json
        uvmgr weaver-forge bulk-create template-specs.yaml --interactive
        uvmgr weaver-forge bulk-create my-templates.yml --output ./custom-templates
    """
    add_span_attributes(**{
        "weaver_forge.operation": "bulk_create",
        "weaver_forge.specs_file": str(template_specs_file),
        "weaver_forge.interactive": interactive,
    })
    
    console.print(f"📝 [bold cyan]Bulk Template Creation[/bold cyan]")
    console.print(f"📄 Specs File: {template_specs_file}")
    if interactive:
        console.print(f"🎯 Interactive mode: enabled")
    
    # Load template specifications
    try:
        with open(template_specs_file, 'r') as f:
            if template_specs_file.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                template_specs = yaml.safe_load(f)
            else:
                template_specs = json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Failed to load template specifications: {e}[/red]")
        raise typer.Exit(1)
    
    if not isinstance(template_specs, list):
        console.print(f"[red]❌ Template specifications must be a list[/red]")
        raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Bulk template creation
            task1 = progress.add_task(f"Creating {len(template_specs)} templates...", total=len(template_specs))
            
            bulk_result = create_bulk_template(
                template_specs=template_specs,
                output_dir=output_dir,
                interactive=interactive
            )
            
            progress.advance(task1, len(template_specs))
        
        # Display bulk template creation results
        _display_bulk_template_results(bulk_result)
        
        add_span_event("weaver_forge.bulk_templates_created", {
            "templates_count": len(template_specs),
            "successful": bulk_result["successful"],
            "failed": bulk_result["failed"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Bulk template creation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("bulk-validate")
@instrument_command("weaver_forge_bulk_validate", track_args=True)
def bulk_validate_templates_cmd(
    template_names: Optional[List[str]] = typer.Option(
        None,
        "--templates",
        "-t",
        help="Specific templates to validate (default: all)"
    ),
    fix_issues: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix validation issues"
    ),
    output_report: Optional[Path] = typer.Option(
        None,
        "--report",
        "-r",
        help="Output validation report to file"
    ),
):
    """
    Validate multiple templates in bulk.
    
    This command validates multiple templates at once, providing
    comprehensive validation reports and optional auto-fixing.
    
    Examples:
        uvmgr weaver-forge bulk-validate
        uvmgr weaver-forge bulk-validate --templates component api workflow
        uvmgr weaver-forge bulk-validate --fix --report validation-report.json
        uvmgr weaver-forge bulk-validate --report validation-report.yaml
    """
    add_span_attributes(**{
        "weaver_forge.operation": "bulk_validate",
        "weaver_forge.templates": template_names,
        "weaver_forge.fix_issues": fix_issues,
    })
    
    if template_names:
        console.print(f"🔍 [bold cyan]Bulk Validating {len(template_names)} Templates[/bold cyan]")
        console.print(f"📋 Templates: {', '.join(template_names)}")
    else:
        console.print(f"🔍 [bold cyan]Bulk Validating All Templates[/bold cyan]")
    
    if fix_issues:
        console.print(f"🔧 Auto-fix: enabled")
    if output_report:
        console.print(f"📄 Report: {output_report}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Bulk validation
            task1 = progress.add_task("Validating templates...", total=1)
            
            validation_result = validate_bulk_templates(
                template_names=template_names,
                fix_issues=fix_issues,
                output_report=output_report
            )
            
            progress.advance(task1)
        
        # Display bulk validation results
        _display_bulk_validation_results(validation_result)
        
        add_span_event("weaver_forge.bulk_validated", {
            "total_templates": validation_result["total_templates"],
            "total_issues": validation_result["total_issues"],
            "fixed_issues": validation_result["fixed_issues"],
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Bulk validation failed: {e}[/red]")
        raise typer.Exit(1)


def _display_init_summary(init_result: Dict[str, Any]):
    """Display initialization summary."""
    console.print("\n✅ [bold green]Weaver Forge Initialized Successfully[/bold green]")
    
    table = Table(title="Initialization Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project Path", str(init_result["project_path"]))
    table.add_row("Templates Created", str(init_result["templates_created"]))
    table.add_row("Scaffolds Created", str(init_result["scaffolds_created"]))
    table.add_row("Initialization Time", f"{init_result['duration']:.2f}s")
    
    console.print(table)
    
    if init_result.get("templates"):
        console.print("\n📚 [bold]Created Templates:[/bold]")
        for template in init_result["templates"][:5]:  # Show first 5
            console.print(f"  • {template}")
        if len(init_result["templates"]) > 5:
            console.print(f"  ... and {len(init_result['templates']) - 5} more")


def _display_generation_results(generation_result: Dict[str, Any], dry_run: bool):
    """Display code generation results."""
    if dry_run:
        console.print("\n🔍 [bold]Dry Run Results[/bold]")
    else:
        console.print("\n✅ [bold green]Code Generated Successfully[/bold green]")
    
    # Summary table
    table = Table(title="Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Template Used", generation_result.get("template_used", "Unknown"))
    table.add_row("Files Generated", str(len(generation_result.get("files", []))))
    table.add_row("Generation Time", f"{generation_result.get('duration', 0):.2f}s")
    table.add_row("Parameters Used", str(len(generation_result.get("parameters", {}))))
    
    console.print(table)
    
    # Generated files
    if generation_result.get("files"):
        console.print(f"\n📄 [bold]Generated Files:[/bold]")
        files_table = Table()
        files_table.add_column("File", style="cyan")
        files_table.add_column("Size", style="green")
        files_table.add_column("Status", style="yellow")
        
        for file_info in generation_result["files"]:
            status = "Would create" if dry_run else "Created"
            files_table.add_row(
                str(file_info.get("path", "Unknown")),
                f"{file_info.get('size', 0)} bytes",
                status
            )
        
        console.print(files_table)
    
    # Parameters used
    if generation_result.get("parameters"):
        console.print(f"\n⚙️ [bold]Parameters Used:[/bold]")
        for key, value in generation_result["parameters"].items():
            console.print(f"  • {key}: {value}")


def _display_template_creation_result(template_result: Dict[str, Any]):
    """Display template creation result."""
    console.print("\n✅ [bold green]Template Created Successfully[/bold green]")
    
    table = Table(title="Template Creation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Template Name", template_result.get("name", "Unknown"))
    table.add_row("Template Type", template_result.get("type", "Unknown"))
    table.add_row("Output Path", str(template_result.get("output_path", "Unknown")))
    table.add_row("Files Created", str(len(template_result.get("files", []))))
    table.add_row("Creation Time", f"{template_result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    # Template files
    if template_result.get("files"):
        console.print(f"\n📄 [bold]Template Files:[/bold]")
        for file_info in template_result["files"]:
            console.print(f"  • {file_info.get('path', 'Unknown')} ({file_info.get('size', 0)} bytes)")
    
    console.print(f"\n📝 [bold]Next Steps:[/bold]")
    console.print(f"  1. Customize the template: {template_result.get('output_path')}")
    console.print(f"  2. Test with: uvmgr weaver-forge generate {template_result.get('name')} TestName")


def _display_templates_table(templates_result: Dict[str, Any], detailed: bool):
    """Display templates as table."""
    console.print("\n📚 [bold]Available Templates[/bold]")
    
    if not templates_result.get("templates"):
        console.print("No templates found.")
        return
    
    if detailed:
        table = Table(title="Templates (Detailed)")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Description", style="yellow")
        table.add_column("Usage Count", style="green")
        table.add_column("Last Used", style="blue")
        
        for template in templates_result["templates"]:
            table.add_row(
                template.get("name", "Unknown"),
                template.get("type", "Unknown"),
                template.get("description", "No description")[:50] + "...",
                str(template.get("usage_count", 0)),
                template.get("last_used", "Never")
            )
    else:
        table = Table(title="Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Description", style="yellow")
        
        for template in templates_result["templates"]:
            table.add_row(
                template.get("name", "Unknown"),
                template.get("type", "Unknown"),
                template.get("description", "No description")[:50] + "..."
            )
    
    console.print(table)


def _display_templates_tree(templates_result: Dict[str, Any]):
    """Display templates as tree."""
    console.print("\n🌳 [bold]Templates Tree[/bold]")
    
    tree = Tree("📚 Templates")
    
    # Group by type
    templates_by_type = {}
    for template in templates_result.get("templates", []):
        template_type = template.get("type", "Unknown")
        if template_type not in templates_by_type:
            templates_by_type[template_type] = []
        templates_by_type[template_type].append(template)
    
    for template_type, templates in templates_by_type.items():
        type_node = tree.add(f"📄 {template_type}")
        for template in templates:
            template_node = type_node.add(f"📝 {template.get('name', 'Unknown')}")
            template_node.add(f"📖 {template.get('description', 'No description')[:50]}...")
            template_node.add(f"🔢 Usage: {template.get('usage_count', 0)}")
    
    console.print(tree)


def _display_validation_results(validation_result: Dict[str, Any]):
    """Display validation results."""
    console.print("\n🔍 [bold]Template Validation Results[/bold]")
    
    # Summary table
    table = Table(title="Validation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Templates Validated", str(validation_result.get("templates_validated", 0)))
    table.add_row("Valid Templates", str(validation_result.get("valid_templates", 0)))
    table.add_row("Issues Found", str(len(validation_result.get("issues", []))))
    table.add_row("Fixes Applied", str(len(validation_result.get("fixes_applied", []))))
    table.add_row("Validation Time", f"{validation_result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    # Issues
    if validation_result.get("issues"):
        console.print("\n⚠️ [bold]Issues Found:[/bold]")
        issues_table = Table()
        issues_table.add_column("Template", style="cyan")
        issues_table.add_column("Severity", style="red")
        issues_table.add_column("Issue", style="white")
        
        for issue in validation_result["issues"]:
            issues_table.add_row(
                issue.get("template", "Unknown"),
                issue.get("severity", "Unknown"),
                issue.get("description", "No description")
            )
        
        console.print(issues_table)
    
    # Fixes applied
    if validation_result.get("fixes_applied"):
        console.print("\n🔧 [bold]Fixes Applied:[/bold]")
        for fix in validation_result["fixes_applied"]:
            console.print(f"  • {fix.get('template', 'Unknown')}: {fix.get('description', 'No description')}")


def _display_scaffold_results(scaffold_result: Dict[str, Any]):
    """Display scaffold creation results."""
    console.print("\n✅ [bold green]Project Scaffold Created Successfully[/bold green]")
    
    # Summary table
    table = Table(title="Scaffold Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Scaffold Type", scaffold_result.get("scaffold_type", "Unknown"))
    table.add_row("Project Name", scaffold_result.get("project_name", "Unknown"))
    table.add_row("Output Path", str(scaffold_result.get("output_path", "Unknown")))
    table.add_row("Files Created", str(len(scaffold_result.get("files", []))))
    table.add_row("Creation Time", f"{scaffold_result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    # Generated files
    if scaffold_result.get("files"):
        console.print(f"\n📄 [bold]Generated Files:[/bold]")
        files_table = Table()
        files_table.add_column("File", style="cyan")
        files_table.add_column("Size", style="green")
        files_table.add_column("Type", style="yellow")
        
        for file_info in scaffold_result["files"]:
            files_table.add_row(
                str(file_info.get("path", "Unknown")),
                f"{file_info.get('size', 0)} bytes",
                file_info.get("type", "Unknown")
            )
        
        console.print(files_table)
    
    # Next steps
    console.print(f"\n📝 [bold]Next Steps:[/bold]")
    console.print(f"  1. Navigate to project: cd {scaffold_result.get('output_path')}")
    console.print(f"  2. Install dependencies: Check README.md for instructions")
    console.print(f"  3. Start development: Follow project-specific setup guide")


def _display_prompt_results(prompt_result: Dict[str, Any]):
    """Display prompt generation results."""
    console.print("\n✅ [bold green]Prompt Generation Completed[/bold green]")
    
    # Summary table
    table = Table(title="Prompt Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Template Used", prompt_result.get("template_used", "Custom"))
    table.add_row("Files Generated", str(len(prompt_result.get("files", []))))
    table.add_row("Generation Time", f"{prompt_result.get('duration', 0):.2f}s")
    table.add_row("AI Analysis", "✅ Used" if prompt_result.get("ai_analysis") else "❌ Not used")
    
    console.print(table)
    
    # Generated files
    if prompt_result.get("files"):
        console.print(f"\n📄 [bold]Generated Files:[/bold]")
        files_table = Table()
        files_table.add_column("File", style="cyan")
        files_table.add_column("Size", style="green")
        files_table.add_column("Description", style="yellow")
        
        for file_info in prompt_result["files"]:
            files_table.add_row(
                str(file_info.get("path", "Unknown")),
                f"{file_info.get('size', 0)} bytes",
                file_info.get("description", "No description")[:50] + "..."
            )
        
        console.print(files_table)
    
    # AI insights
    if prompt_result.get("ai_insights"):
        console.print(f"\n🤖 [bold]AI Insights:[/bold]")
        for insight in prompt_result["ai_insights"]:
            console.print(f"  • {insight}")


def _display_status_table(status_info: Dict[str, Any], detailed: bool, include_metrics: bool):
    """Display Weaver Forge status."""
    console.print("\n📊 [bold]Weaver Forge Status[/bold]")
    
    # Basic status
    basic_table = Table(title="Basic Status")
    basic_table.add_column("Metric", style="cyan")
    basic_table.add_column("Value", style="green")
    
    basic_table.add_row("Initialized", "✅ Yes" if status_info.get("initialized") else "❌ No")
    basic_table.add_row("Templates Count", str(status_info.get("templates_count", 0)))
    basic_table.add_row("Scaffolds Count", str(status_info.get("scaffolds_count", 0)))
    basic_table.add_row("Last Generation", status_info.get("last_generation", "Never"))
    
    console.print(basic_table)
    
    # Detailed information
    if detailed:
        if status_info.get("templates"):
            console.print("\n📚 [bold]Template Statistics:[/bold]")
            templates_table = Table()
            templates_table.add_column("Type", style="cyan")
            templates_table.add_column("Count", style="white")
            templates_table.add_column("Most Used", style="green")
            
            for template_type, stats in status_info["templates"].items():
                templates_table.add_row(
                    template_type,
                    str(stats.get("count", 0)),
                    stats.get("most_used", "None")
                )
            
            console.print(templates_table)
    
    # Metrics
    if include_metrics and status_info.get("metrics"):
        console.print("\n📈 [bold]Performance Metrics:[/bold]")
        metrics_table = Table()
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        for key, value in status_info["metrics"].items():
            if isinstance(value, float):
                metrics_table.add_row(key, f"{value:.2f}")
            else:
                metrics_table.add_row(key, str(value))
        
        console.print(metrics_table)


def _display_bulk_generation_results(bulk_result: Dict[str, Any], dry_run: bool):
    """Display bulk generation results."""
    console.print(f"\n📊 [bold]Bulk Generation Results[/bold]")
    
    # Summary table
    summary_table = Table(title="Generation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Items", str(bulk_result["total_specs"]))
    summary_table.add_row("Successful", str(bulk_result["successful"]))
    summary_table.add_row("Failed", str(bulk_result["failed"]))
    summary_table.add_row("Success Rate", f"{bulk_result['success_rate']:.1f}%")
    summary_table.add_row("Total Files", str(bulk_result["total_files"]))
    summary_table.add_row("Duration", f"{bulk_result['duration']:.2f}s")
    
    console.print(summary_table)
    
    # Show errors if any
    if bulk_result["errors"]:
        console.print(f"\n❌ [bold red]Errors ({len(bulk_result['errors'])}):[/bold red]")
        for error in bulk_result["errors"][:5]:  # Show first 5 errors
            console.print(f"   • {error}")
        if len(bulk_result["errors"]) > 5:
            console.print(f"   ... and {len(bulk_result['errors']) - 5} more errors")
    
    # Show individual results
    if bulk_result["results"]:
        console.print(f"\n📁 [bold]Generated Files:[/bold]")
        for result in bulk_result["results"][:3]:  # Show first 3 results
            if result.get("files"):
                for file_info in result["files"][:2]:  # Show first 2 files per result
                    status = "👀 Would create" if dry_run else "✅ Created"
                    console.print(f"   {status}: {file_info['path']}")
        if len(bulk_result["results"]) > 3:
            console.print(f"   ... and {len(bulk_result['results']) - 3} more results")


def _display_bulk_scaffold_results(bulk_result: Dict[str, Any], dry_run: bool):
    """Display bulk scaffold results."""
    console.print(f"\n📊 [bold]Bulk Scaffold Results[/bold]")
    
    # Summary table
    summary_table = Table(title="Scaffold Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Scaffolds", str(bulk_result["total_scaffolds"]))
    summary_table.add_row("Successful", str(bulk_result["successful"]))
    summary_table.add_row("Failed", str(bulk_result["failed"]))
    summary_table.add_row("Success Rate", f"{bulk_result['success_rate']:.1f}%")
    summary_table.add_row("Total Files", str(bulk_result["total_files"]))
    summary_table.add_row("Duration", f"{bulk_result['duration']:.2f}s")
    
    console.print(summary_table)
    
    # Show errors if any
    if bulk_result["errors"]:
        console.print(f"\n❌ [bold red]Errors ({len(bulk_result['errors'])}):[/bold red]")
        for error in bulk_result["errors"][:5]:
            console.print(f"   • {error}")
        if len(bulk_result["errors"]) > 5:
            console.print(f"   ... and {len(bulk_result['errors']) - 5} more errors")
    
    # Show individual results
    if bulk_result["results"]:
        console.print(f"\n📁 [bold]Generated Scaffolds:[/bold]")
        for result in bulk_result["results"][:3]:
            if result.get("files"):
                for file_info in result["files"][:2]:
                    status = "👀 Would create" if dry_run else "✅ Created"
                    console.print(f"   {status}: {file_info['path']}")
        if len(bulk_result["results"]) > 3:
            console.print(f"   ... and {len(bulk_result['results']) - 3} more results")


def _display_batch_results(batch_result: Dict[str, Any], dry_run: bool):
    """Display batch generation results."""
    console.print(f"\n📊 [bold]Batch Generation Results[/bold]")
    
    # Summary table
    summary_table = Table(title="Batch Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Batch File", batch_result["batch_file"])
    summary_table.add_row("Total Files", str(batch_result["total_files"]))
    summary_table.add_row("Total Errors", str(batch_result["total_errors"]))
    summary_table.add_row("Duration", f"{batch_result['total_duration']:.2f}s")
    
    console.print(summary_table)
    
    # Show generation results
    if batch_result["generations"]:
        gen_result = batch_result["generations"]
        console.print(f"\n📝 [bold]Template Generations:[/bold]")
        console.print(f"   • Items: {gen_result['total_specs']}")
        console.print(f"   • Successful: {gen_result['successful']}")
        console.print(f"   • Failed: {gen_result['failed']}")
        console.print(f"   • Files: {gen_result['total_files']}")
    
    # Show scaffold results
    if batch_result["scaffolds"]:
        scaffold_result = batch_result["scaffolds"]
        console.print(f"\n🏗️ [bold]Scaffolds:[/bold]")
        console.print(f"   • Projects: {scaffold_result['total_scaffolds']}")
        console.print(f"   • Successful: {scaffold_result['successful']}")
        console.print(f"   • Failed: {scaffold_result['failed']}")
        console.print(f"   • Files: {scaffold_result['total_files']}")


def _display_bulk_template_results(bulk_result: Dict[str, Any]):
    """Display bulk template creation results."""
    console.print(f"\n📊 [bold]Bulk Template Creation Results[/bold]")
    
    # Summary table
    summary_table = Table(title="Template Creation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Templates", str(bulk_result["total_templates"]))
    summary_table.add_row("Successful", str(bulk_result["successful"]))
    summary_table.add_row("Failed", str(bulk_result["failed"]))
    summary_table.add_row("Success Rate", f"{bulk_result['success_rate']:.1f}%")
    summary_table.add_row("Duration", f"{bulk_result['duration']:.2f}s")
    
    console.print(summary_table)
    
    # Show errors if any
    if bulk_result["errors"]:
        console.print(f"\n❌ [bold red]Errors ({len(bulk_result['errors'])}):[/bold red]")
        for error in bulk_result["errors"][:5]:
            console.print(f"   • {error}")
        if len(bulk_result["errors"]) > 5:
            console.print(f"   ... and {len(bulk_result['errors']) - 5} more errors")
    
    # Show individual results
    if bulk_result["results"]:
        console.print(f"\n📁 [bold]Created Templates:[/bold]")
        for result in bulk_result["results"][:3]:
            if result.get("name"):
                console.print(f"   ✅ {result['name']} ({result['type']})")
        if len(bulk_result["results"]) > 3:
            console.print(f"   ... and {len(bulk_result['results']) - 3} more templates")


def _display_bulk_validation_results(validation_result: Dict[str, Any]):
    """Display bulk validation results."""
    console.print(f"\n📊 [bold]Bulk Validation Results[/bold]")
    
    # Summary table
    summary_table = Table(title="Validation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Templates", str(validation_result["total_templates"]))
    summary_table.add_row("With Issues", str(validation_result["templates_with_issues"]))
    summary_table.add_row("Total Issues", str(validation_result["total_issues"]))
    summary_table.add_row("Fixed Issues", str(validation_result["fixed_issues"]))
    summary_table.add_row("Success Rate", f"{validation_result['success_rate']:.1f}%")
    summary_table.add_row("Duration", f"{validation_result['duration']:.2f}s")
    
    console.print(summary_table)
    
    # Show validation results
    if validation_result["results"]:
        console.print(f"\n🔍 [bold]Template Validation Details:[/bold]")
        for result in validation_result["results"][:5]:
            if result.get("issue_count", 0) > 0:
                console.print(f"   ⚠️  {result['template']}: {result['issue_count']} issues")
            else:
                console.print(f"   ✅ {result['template']}: No issues")
        if len(validation_result["results"]) > 5:
            console.print(f"   ... and {len(validation_result['results']) - 5} more templates") 