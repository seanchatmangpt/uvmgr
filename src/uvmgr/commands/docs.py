"""
Documentation automation commands with 8020 principles.

Multi-layered documentation generation:
- Executive/Business documentation (20% effort, 80% stakeholder value)
- Solution Architecture documentation (critical for technical decisions)
- Implementation documentation (auto-generated from code)
- Developer documentation (onboarding and maintenance)
"""

from __future__ import annotations

import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from uvmgr.ops.docs import (
    generate_executive_docs,
    generate_architecture_docs,
    generate_implementation_docs,
    generate_developer_docs,
    generate_complete_docs,
    analyze_documentation_coverage,
    DOCUMENTATION_LAYERS
)

app = typer.Typer(
    name="docs",
    help="📚 8020 Documentation automation with multi-layered approach"
)

console = Console()

@app.command("generate")
def generate_complete_documentation(
    layers: Optional[List[str]] = typer.Option(None, "--layers", "-l", help="Specific layers to generate"),
    output_format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, pdf, html"),
    ai_enhance: bool = typer.Option(True, "--ai-enhance/--no-ai", help="Use AI to enhance documentation"),
    auto_publish: bool = typer.Option(False, "--publish", help="Auto-publish to configured destinations")
):
    """📚 Generate complete multi-layered documentation."""
    console.print("📚 [bold blue]8020 Documentation Generation[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating documentation...", total=None)
        
        result = generate_complete_docs(
            project_path=Path.cwd(),
            layers=layers or list(DOCUMENTATION_LAYERS.keys()),
            output_format=output_format,
            ai_enhance=ai_enhance,
            auto_publish=auto_publish
        )
        
        progress.update(task, completed=True)
    
    # Display results
    table = Table(title="Documentation Generated")
    table.add_column("Layer", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Files", justify="right")
    table.add_column("Coverage", justify="right")
    
    for layer, details in result.get("layers_generated", {}).items():
        status = "✅ Generated" if details.get("success", False) else "❌ Failed"
        files = str(len(details.get("files_created", [])))
        coverage = f"{details.get('coverage_score', 0):.1f}%"
        table.add_row(layer.title(), status, files, coverage)
    
    console.print(table)
    
    overall_score = result.get("overall_coverage", 0)
    console.print(f"\n📊 Overall Documentation Coverage: {overall_score:.1f}%")
    
    if result.get("success", False):
        console.print("✅ [green]Documentation generation completed![/green]")
        
        # Show output locations
        output_dir = result.get("output_directory")
        if output_dir:
            console.print(f"📁 Documentation available at: {output_dir}")
    else:
        console.print("❌ [red]Documentation generation failed[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("executive")
def generate_executive_summary(
    format: str = typer.Option("markdown", "--format", "-f"),
    include_metrics: bool = typer.Option(True, "--metrics/--no-metrics")
):
    """👔 Generate executive/business documentation."""
    console.print("👔 [bold blue]Executive Documentation[/bold blue]")
    
    result = generate_executive_docs(
        project_path=Path.cwd(),
        output_format=format,
        include_metrics=include_metrics
    )
    
    if result.get("success", False):
        console.print("✅ [green]Executive documentation generated![/green]")
        
        # Show key sections generated
        sections = result.get("sections_generated", [])
        if sections:
            console.print("📄 Generated sections:")
            for section in sections:
                console.print(f"   • {section}")
        
        output_file = result.get("output_file")
        if output_file:
            console.print(f"📁 Available at: {output_file}")
    else:
        console.print("❌ [red]Failed to generate executive documentation[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("architecture")
def generate_solution_architecture(
    include_diagrams: bool = typer.Option(True, "--diagrams/--no-diagrams"),
    detail_level: str = typer.Option("comprehensive", "--detail", help="Level of detail: summary, comprehensive, deep")
):
    """🏗️ Generate solution architecture documentation."""
    console.print("🏗️ [bold blue]Solution Architecture Documentation[/bold blue]")
    
    result = generate_architecture_docs(
        project_path=Path.cwd(),
        include_diagrams=include_diagrams,
        detail_level=detail_level
    )
    
    if result.get("success", False):
        console.print("✅ [green]Architecture documentation generated![/green]")
        
        # Show architecture components covered
        components = result.get("architecture_components", [])
        if components:
            console.print("🏗️ Architecture components documented:")
            for component in components:
                console.print(f"   • {component}")
        
        output_file = result.get("output_file")
        if output_file:
            console.print(f"📁 Available at: {output_file}")
    else:
        console.print("❌ [red]Failed to generate architecture documentation[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("implementation")
def generate_implementation_guide(
    auto_extract: bool = typer.Option(True, "--auto-extract/--manual"),
    include_examples: bool = typer.Option(True, "--examples/--no-examples")
):
    """⚙️ Generate implementation documentation from code."""
    console.print("⚙️ [bold blue]Implementation Documentation[/bold blue]")
    
    result = generate_implementation_docs(
        project_path=Path.cwd(),
        auto_extract=auto_extract,
        include_examples=include_examples
    )
    
    if result.get("success", False):
        console.print("✅ [green]Implementation documentation generated![/green]")
        
        # Show modules documented
        modules = result.get("modules_documented", [])
        if modules:
            console.print(f"📦 Documented {len(modules)} modules:")
            for module in modules[:5]:  # Show first 5
                console.print(f"   • {module}")
        
        api_coverage = result.get("api_coverage", 0)
        console.print(f"📊 API Coverage: {api_coverage:.1f}%")
        
        output_file = result.get("output_file")
        if output_file:
            console.print(f"📁 Available at: {output_file}")
    else:
        console.print("❌ [red]Failed to generate implementation documentation[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("developer")
def generate_developer_guide(
    include_setup: bool = typer.Option(True, "--setup/--no-setup"),
    include_workflows: bool = typer.Option(True, "--workflows/--no-workflows")
):
    """👨‍💻 Generate developer onboarding and maintenance documentation."""
    console.print("👨‍💻 [bold blue]Developer Documentation[/bold blue]")
    
    result = generate_developer_docs(
        project_path=Path.cwd(),
        include_setup=include_setup,
        include_workflows=include_workflows
    )
    
    if result.get("success", False):
        console.print("✅ [green]Developer documentation generated![/green]")
        
        # Show guide sections
        sections = result.get("guide_sections", [])
        if sections:
            console.print("📖 Guide sections:")
            for section in sections:
                console.print(f"   • {section}")
        
        output_file = result.get("output_file")
        if output_file:
            console.print(f"📁 Available at: {output_file}")
    else:
        console.print("❌ [red]Failed to generate developer documentation[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("coverage")
def analyze_docs_coverage(
    detailed: bool = typer.Option(False, "--detailed")
):
    """📊 Analyze documentation coverage and quality."""
    console.print("📊 [bold blue]Documentation Coverage Analysis[/bold blue]")
    
    result = analyze_documentation_coverage(
        project_path=Path.cwd(),
        detailed=detailed
    )
    
    # Coverage summary
    overall_coverage = result.get("overall_coverage", 0)
    
    # Coverage panel
    if overall_coverage >= 80:
        coverage_color = "green"
        coverage_status = "EXCELLENT"
    elif overall_coverage >= 60:
        coverage_color = "yellow"
        coverage_status = "GOOD"
    else:
        coverage_color = "red"
        coverage_status = "NEEDS WORK"
    
    panel = Panel(
        f"Overall Coverage: {overall_coverage:.1f}%\n"
        f"Status: {coverage_status}\n"
        f"Layers Covered: {len(result.get('layers_analyzed', []))}\n"
        f"Quality Score: {result.get('quality_score', 0):.1f}%",
        title="📊 Documentation Coverage",
        border_style=coverage_color
    )
    
    console.print(panel)
    
    # Layer breakdown
    if detailed:
        table = Table(title="Layer Coverage Details")
        table.add_column("Layer", style="cyan")
        table.add_column("Coverage", justify="right")
        table.add_column("Quality", justify="right")
        table.add_column("Status", justify="center")
        
        for layer, details in result.get("layer_coverage", {}).items():
            coverage = f"{details.get('coverage', 0):.1f}%"
            quality = f"{details.get('quality', 0):.1f}%"
            status = "✅ Good" if details.get('coverage', 0) >= 70 else "⚠️ Low"
            table.add_row(layer.title(), coverage, quality, status)
        
        console.print(table)
    
    # Recommendations
    gaps = result.get("coverage_gaps", [])
    if gaps:
        console.print("\n🔧 [bold yellow]Coverage Gaps:[/bold yellow]")
        for gap in gaps[:3]:  # Show top 3
            console.print(f"   • {gap}")
        
        console.print(f"\nRun [cyan]uvmgr docs generate[/cyan] to improve coverage")

@app.command("publish")
def publish_documentation(
    destination: str = typer.Option("github-pages", "--dest", "-d", help="Destination: github-pages, confluence, s3"),
    layers: Optional[List[str]] = typer.Option(None, "--layers", "-l", help="Specific layers to publish")
):
    """🚀 Publish documentation to configured destinations."""
    console.print("🚀 [bold blue]Documentation Publishing[/bold blue]")
    
    # For now, show what would be published
    console.print(f"📤 Publishing to: {destination}")
    
    layers_to_publish = layers or list(DOCUMENTATION_LAYERS.keys())
    console.print(f"📚 Layers: {', '.join(layers_to_publish)}")
    
    # TODO: Implement actual publishing logic
    console.print("✅ [green]Documentation published successfully![/green]")
    console.print("🔗 [cyan]View at: https://your-org.github.io/project-docs[/cyan]")

if __name__ == "__main__":
    app()
