"""
uvmgr.commands.substrate - Substrate Project Integration
======================================================

Commands for integrating with Substrate-generated Python projects.

This module provides CLI commands for creating, validating, and testing
Substrate-based Python projects with uvmgr's OTEL capabilities. It demonstrates
how uvmgr can work seamlessly with modern Python project templates.

Key Features
-----------
• **Project Generation**: Create Substrate projects for testing
• **OTEL Validation**: Validate OTEL in Substrate projects
• **Toolchain Testing**: Test OTEL with Substrate's tools
• **Batch Validation**: Test multiple project variants
• **Template Generation**: Create OTEL-enabled templates

Available Commands
-----------------
- **create**: Create a Substrate test project
- **validate**: Validate OTEL in a Substrate project
- **batch-test**: Test multiple Substrate variants
- **generate-template**: Generate OTEL template for Substrate

Examples
--------
    >>> # Create a test project
    >>> uvmgr substrate create my-test-project
    >>> 
    >>> # Validate existing Substrate project
    >>> uvmgr substrate validate ./my-substrate-app
    >>> 
    >>> # Test multiple variants
    >>> uvmgr substrate batch-test --variants basic cli full
    >>> 
    >>> # Generate OTEL template
    >>> uvmgr substrate generate-template

See Also
--------
- :mod:`uvmgr.commands.spiff_otel` : SpiffWorkflow OTEL validation
- :mod:`uvmgr.ops.substrate_integration` : Substrate integration operations
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uvmgr.core.instrumentation import instrument_command
from uvmgr.ops.substrate_integration import (
    create_substrate_test_project,
    validate_substrate_project,
    batch_validate_substrate_variants,
    generate_substrate_otel_template
)

app = typer.Typer(help="Substrate project integration and validation")
console = Console()


@app.command("create")
@instrument_command("substrate_create", track_args=True)
def create_project(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    project_type: str = typer.Option("package", "--type", "-t", help="Project type"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Create a Substrate-based test project."""
    
    console.print(Panel(
        f"🚀 Creating Substrate Project: [bold]{project_name}[/bold]",
        title="Substrate Project Generator"
    ))
    
    try:
        with console.status("Creating project..."):
            project_path = create_substrate_test_project(
                project_name=project_name,
                project_type=project_type,
                output_dir=output_dir
            )
        
        console.print(f"✅ Project created successfully at: [green]{project_path}[/green]")
        
        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print(f"1. cd {project_path}")
        console.print("2. uv sync")
        console.print("3. uvmgr substrate validate .")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create project: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("substrate_validate", track_args=True)
def validate_project(
    project_path: Path = typer.Argument(..., help="Path to Substrate project"),
    include_toolchain: bool = typer.Option(True, "--toolchain/--no-toolchain", help="Test with Substrate toolchain"),
    save_results: bool = typer.Option(False, "--save", "-s", help="Save validation results"),
):
    """Validate OTEL integration in a Substrate project."""
    
    if not project_path.exists():
        console.print(f"[red]❌ Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🔍 Validating Substrate Project\n📁 Path: {project_path}",
        title="Substrate OTEL Validation"
    ))
    
    try:
        with console.status("Running validation..."):
            result = validate_substrate_project(
                project_path=project_path,
                include_toolchain_tests=include_toolchain
            )
        
        # Display results
        if result.validation_result.success:
            console.print("✅ [green]Validation PASSED[/green]")
        else:
            console.print("❌ [red]Validation FAILED[/red]")
        
        # Show details table
        table = Table(title="Validation Details")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Installation", "✅" if result.installation_success else "❌")
        table.add_row("OTEL Integration", "✅" if result.uvmgr_integration_success else "❌")
        table.add_row("Metrics Validated", str(result.validation_result.metrics_validated))
        table.add_row("Spans Validated", str(result.validation_result.spans_validated))
        table.add_row("Duration", f"{result.validation_result.duration_seconds:.2f}s")
        table.add_row("Errors", str(len(result.validation_result.errors)))
        
        console.print(table)
        
        if result.validation_result.errors:
            console.print("\n[red]Errors:[/red]")
            for error in result.validation_result.errors:
                console.print(f"  • {error}")
        
        if save_results:
            results_file = project_path / "substrate_validation_results.json"
            import json
            with open(results_file, "w") as f:
                json.dump({
                    "success": result.validation_result.success,
                    "metrics": result.validation_result.metrics_validated,
                    "spans": result.validation_result.spans_validated,
                    "errors": result.validation_result.errors
                }, f, indent=2)
            console.print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("batch-test")
@instrument_command("substrate_batch_test", track_args=True)
def batch_test(
    variants: Optional[List[str]] = typer.Option(None, "--variant", "-v", help="Variants to test"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Test multiple Substrate project variants."""
    
    console.print(Panel(
        "🧪 Substrate Batch Testing\n" + 
        f"Variants: {', '.join(variants) if variants else 'default set'}",
        title="Batch Validation"
    ))
    
    try:
        with console.status("Running batch tests..."):
            results = batch_validate_substrate_variants(
                variants=variants,
                output_dir=output_dir
            )
        
        # Display results table
        table = Table(title="Batch Test Results")
        table.add_column("Variant", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Metrics", style="yellow")
        table.add_column("Spans", style="yellow")
        table.add_column("Duration", style="magenta")
        
        total_success = 0
        for variant, result in results.items():
            status = "✅ PASS" if result.validation_result.success else "❌ FAIL"
            if result.validation_result.success:
                total_success += 1
            
            table.add_row(
                variant,
                status,
                str(result.validation_result.metrics_validated),
                str(result.validation_result.spans_validated),
                f"{result.validation_result.duration_seconds:.2f}s"
            )
        
        console.print(table)
        
        success_rate = (total_success / len(results)) * 100 if results else 0
        console.print(f"\n✨ Success Rate: {success_rate:.1f}% ({total_success}/{len(results)})")
        
    except Exception as e:
        console.print(f"[red]❌ Batch testing failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("generate-template")
@instrument_command("substrate_generate_template", track_args=True)
def generate_template(
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate OTEL integration template for Substrate projects."""
    
    console.print(Panel(
        "📝 Generating OTEL Template for Substrate",
        title="Template Generator"
    ))
    
    template_content = generate_substrate_otel_template()
    
    if output_file:
        output_file.write_text(template_content)
        console.print(f"✅ Template saved to: [green]{output_file}[/green]")
    else:
        console.print("\n" + template_content)
    
    console.print("\n[bold]Integration Steps:[/bold]")
    console.print("1. Add the OTEL dependencies to your Substrate project")
    console.print("2. Create the _otel.py module in your package")
    console.print("3. Initialize telemetry in your main entry point")
    console.print("4. Use spans to instrument your critical code paths")


if __name__ == "__main__":
    app()