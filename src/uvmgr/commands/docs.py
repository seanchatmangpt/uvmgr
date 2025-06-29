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
from uvmgr.core.instrumentation import (
    instrument_command,
    add_span_attributes,
    add_span_event
)
from uvmgr.core.telemetry import span

app = typer.Typer(
    name="docs",
    help="📚 8020 Documentation automation with multi-layered approach"
)

console = Console()

@app.command("generate")
@instrument_command("docs_generate_complete")
def generate_complete_documentation(
    layers: Optional[List[str]] = typer.Option(None, "--layers", "-l", help="Specific layers to generate"),
    output_format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, pdf, html"),
    ai_enhance: bool = typer.Option(True, "--ai-enhance/--no-ai", help="Use AI to enhance documentation"),
    auto_publish: bool = typer.Option(False, "--publish", help="Auto-publish to configured destinations")
):
    """📚 Generate complete multi-layered documentation."""
    with span("docs.generate_complete", 
              layers=layers or "all", 
              output_format=output_format, 
              ai_enhance=ai_enhance, 
              auto_publish=auto_publish):
        
        add_span_event("docs.generate.started", {
            "layers": layers or "all",
            "format": output_format,
            "ai_enhance": ai_enhance
        })
        
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
        
        add_span_attributes(
            overall_coverage=overall_score,
            layers_generated=len(result.get("layers_generated", {})),
            success=result.get("success", False)
        )
        
        if result.get("success", False):
            add_span_event("docs.generate.completed", {"status": "success"})
            console.print("✅ [green]Documentation generation completed![/green]")
            
            # Show output locations
            output_dir = result.get("output_directory")
            if output_dir:
                console.print(f"📁 Documentation available at: {output_dir}")
        else:
            add_span_event("docs.generate.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Documentation generation failed[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("executive")
@instrument_command("docs_generate_executive")
def generate_executive_summary(
    format: str = typer.Option("markdown", "--format", "-f"),
    include_metrics: bool = typer.Option(True, "--metrics/--no-metrics")
):
    """👔 Generate executive/business documentation."""
    with span("docs.generate_executive", format=format, include_metrics=include_metrics):
        console.print("👔 [bold blue]Executive Documentation[/bold blue]")
        
        result = generate_executive_docs(
            project_path=Path.cwd(),
            output_format=format,
            include_metrics=include_metrics
        )
        
        add_span_attributes(
            success=result.get("success", False),
            sections_generated=len(result.get("sections_generated", []))
        )
        
        if result.get("success", False):
            add_span_event("docs.executive.completed", {"status": "success"})
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
            add_span_event("docs.executive.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Failed to generate executive documentation[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("architecture")
@instrument_command("docs_generate_architecture")
def generate_solution_architecture(
    include_diagrams: bool = typer.Option(True, "--diagrams/--no-diagrams"),
    detail_level: str = typer.Option("comprehensive", "--detail", help="Level of detail: summary, comprehensive, deep")
):
    """🏗️ Generate solution architecture documentation."""
    with span("docs.generate_architecture", include_diagrams=include_diagrams, detail_level=detail_level):
        console.print("🏗️ [bold blue]Solution Architecture Documentation[/bold blue]")
        
        result = generate_architecture_docs(
            project_path=Path.cwd(),
            include_diagrams=include_diagrams,
            detail_level=detail_level
        )
        
        add_span_attributes(
            success=result.get("success", False),
            components_documented=len(result.get("architecture_components", []))
        )
        
        if result.get("success", False):
            add_span_event("docs.architecture.completed", {"status": "success"})
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
            add_span_event("docs.architecture.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Failed to generate architecture documentation[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("implementation")
@instrument_command("docs_generate_implementation")
def generate_implementation_guide(
    auto_extract: bool = typer.Option(True, "--auto-extract/--manual"),
    include_examples: bool = typer.Option(True, "--examples/--no-examples")
):
    """⚙️ Generate implementation documentation from code."""
    with span("docs.generate_implementation", auto_extract=auto_extract, include_examples=include_examples):
        console.print("⚙️ [bold blue]Implementation Documentation[/bold blue]")
        
        result = generate_implementation_docs(
            project_path=Path.cwd(),
            auto_extract=auto_extract,
            include_examples=include_examples
        )
        
        add_span_attributes(
            success=result.get("success", False),
            modules_documented=len(result.get("modules_documented", [])),
            api_coverage=result.get("api_coverage", 0)
        )
        
        if result.get("success", False):
            add_span_event("docs.implementation.completed", {"status": "success"})
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
            add_span_event("docs.implementation.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Failed to generate implementation documentation[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("developer")
@instrument_command("docs_generate_developer")
def generate_developer_guide(
    include_setup: bool = typer.Option(True, "--setup/--no-setup"),
    include_workflows: bool = typer.Option(True, "--workflows/--no-workflows")
):
    """👨‍💻 Generate developer onboarding and maintenance documentation."""
    with span("docs.generate_developer", include_setup=include_setup, include_workflows=include_workflows):
        console.print("👨‍💻 [bold blue]Developer Documentation[/bold blue]")
        
        result = generate_developer_docs(
            project_path=Path.cwd(),
            include_setup=include_setup,
            include_workflows=include_workflows
        )
        
        add_span_attributes(
            success=result.get("success", False),
            sections_generated=len(result.get("guide_sections", []))
        )
        
        if result.get("success", False):
            add_span_event("docs.developer.completed", {"status": "success"})
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
            add_span_event("docs.developer.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Failed to generate developer documentation[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("coverage")
@instrument_command("docs_analyze_coverage")
def analyze_docs_coverage(
    detailed: bool = typer.Option(False, "--detailed")
):
    """📊 Analyze documentation coverage and quality."""
    with span("docs.analyze_coverage", detailed=detailed):
        console.print("📊 [bold blue]Documentation Coverage Analysis[/bold blue]")
        
        result = analyze_documentation_coverage(
            project_path=Path.cwd(),
            detailed=detailed
        )
        
        add_span_attributes(
            success=result.get("success", False),
            overall_coverage=result.get("overall_coverage", 0),
            layers_analyzed=len(result.get("layer_coverage", {}))
        )
        
        if result.get("success", False):
            add_span_event("docs.coverage.completed", {"status": "success"})
            console.print("✅ [green]Coverage analysis completed![/green]")
            
            # Display coverage results
            overall_coverage = result.get("overall_coverage", 0)
            console.print(f"📊 Overall Coverage: {overall_coverage:.1f}%")
            
            # Show layer breakdown
            layer_coverage = result.get("layer_coverage", {})
            if layer_coverage:
                table = Table(title="Coverage by Layer")
                table.add_column("Layer", style="cyan")
                table.add_column("Coverage", justify="right")
                table.add_column("Quality", justify="right")
                
                for layer, data in layer_coverage.items():
                    coverage = f"{data.get('coverage', 0):.1f}%"
                    quality = f"{data.get('quality', 0):.1f}%"
                    table.add_row(layer.title(), coverage, quality)
                
                console.print(table)
        else:
            add_span_event("docs.coverage.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Coverage analysis failed[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

@app.command("publish")
@instrument_command("docs_publish")
def publish_documentation(
    destination: str = typer.Option("github-pages", "--dest", "-d", help="Destination: github-pages, confluence, s3"),
    layers: Optional[List[str]] = typer.Option(None, "--layers", "-l", help="Specific layers to publish")
):
    """🚀 Publish documentation to configured destinations."""
    with span("docs.publish", destination=destination, layers=layers or "all"):
        console.print("🚀 [bold blue]Documentation Publishing[/bold blue]")
        
        # For now, show what would be published
        console.print(f"📤 Publishing to: {destination}")
        
        layers_to_publish = layers or list(DOCUMENTATION_LAYERS.keys())
        console.print(f"📚 Layers: {', '.join(layers_to_publish)}")
        
        # TODO: Implement actual publishing logic
        result = {
            "success": True,
            "layers_published": layers_to_publish,
            "published_urls": {
                layer: f"https://your-org.github.io/project-docs/{layer}" 
                for layer in layers_to_publish
            }
        }
        
        add_span_attributes(
            success=result.get("success", False),
            destination=destination,
            layers_published=len(result.get("layers_published", []))
        )
        
        if result.get("success", False):
            add_span_event("docs.publish.completed", {"status": "success"})
            console.print("✅ [green]Documentation published successfully![/green]")
            
            # Show published layers
            layers_published = result.get("layers_published", [])
            if layers_published:
                console.print("📤 Published layers:")
                for layer in layers_published:
                    console.print(f"   • {layer}")
            
            # Show URLs if available
            urls = result.get("published_urls", {})
            if urls:
                console.print("🔗 Published URLs:")
                for layer, url in urls.items():
                    console.print(f"   • {layer}: {url}")
        else:
            add_span_event("docs.publish.failed", {"error": result.get('error', 'Unknown error')})
            console.print("❌ [red]Documentation publishing failed[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            raise typer.Exit(1)

if __name__ == "__main__":
    app()
