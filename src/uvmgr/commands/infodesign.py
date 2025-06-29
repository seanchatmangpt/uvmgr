"""
uvmgr.commands.infodesign - Information Design with DSPy
======================================================

Commands for intelligent information design using DSPy framework.
Implements three-layer architecture: Commands → Operations → Runtime.

This module provides DSPy-powered information design capabilities including:
- Automatic documentation generation
- Information architecture design
- Content structure optimization
- Knowledge graph creation

Key Features
-----------
• **Intelligent Documentation**: AI-generated docs from code/data
• **Information Architecture**: Structured information design
• **Content Optimization**: Format and structure optimization
• **Knowledge Extraction**: Extract entities, relationships, concepts
• **Multi-format Output**: Markdown, JSON, HTML, graphs

Available Commands
-----------------
- **analyze**: Analyze information structure and patterns
- **generate**: Generate documentation and content
- **optimize**: Optimize information architecture
- **extract**: Extract knowledge from unstructured data
- **graph**: Create knowledge graphs and visualizations
- **template**: Create reusable information templates

Examples
--------
    >>> # Analyze codebase for documentation patterns
    >>> uvmgr infodesign analyze --source src/ --type code
    >>> 
    >>> # Generate comprehensive documentation
    >>> uvmgr infodesign generate --input docs/ --format markdown
    >>> 
    >>> # Create knowledge graph from project
    >>> uvmgr infodesign graph --source . --output knowledge.json
    >>> 
    >>> # Optimize information architecture
    >>> uvmgr infodesign optimize --docs docs/ --structure hierarchical

Architecture
-----------
- **Commands**: CLI interface and user interaction
- **Operations**: DSPy-powered business logic and AI processing
- **Runtime**: File I/O, data processing, format conversion

See Also
--------
- :mod:`uvmgr.ops.infodesign` : DSPy operations and AI logic
- :mod:`uvmgr.runtime.infodesign` : Runtime processing and I/O
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import InfoDesignAttributes, InfoDesignOperations
from uvmgr.cli_utils import maybe_json

console = Console()
app = typer.Typer(help="Intelligent information design with DSPy")


class OutputFormat(str, Enum):
    """Output format options"""
    markdown = "markdown"
    json = "json"
    html = "html"
    yaml = "yaml"
    graph = "graph"


class AnalysisType(str, Enum):
    """Analysis type options"""
    code = "code"
    docs = "docs"
    data = "data"
    structure = "structure"
    content = "content"


class DesignPattern(str, Enum):
    """Information design patterns"""
    hierarchical = "hierarchical"
    network = "network"
    linear = "linear"
    modular = "modular"
    layered = "layered"


@app.command("analyze")
@instrument_command("infodesign_analyze", track_args=True)
def analyze_information(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Source directory or file to analyze"),
    analysis_type: AnalysisType = typer.Option(AnalysisType.structure, "--type", "-t", help="Type of analysis"),
    depth: int = typer.Option(3, "--depth", "-d", help="Analysis depth (1-5)"),
    include_metrics: bool = typer.Option(True, "--metrics/--no-metrics", help="Include quantitative metrics"),
    output_format: OutputFormat = typer.Option(OutputFormat.json, "--format", "-f", help="Output format"),
):
    """Analyze information structure and patterns using DSPy."""
    add_span_attributes(**{
        InfoDesignAttributes.OPERATION: InfoDesignOperations.ANALYZE,
        InfoDesignAttributes.SOURCE: str(source),
        InfoDesignAttributes.ANALYSIS_TYPE: analysis_type.value,
        "infodesign.depth": depth,
        "infodesign.metrics": include_metrics,
        InfoDesignAttributes.OUTPUT_FORMAT: output_format.value,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Analyzing {analysis_type.value} structure...", total=None)
            
            result = info_ops.analyze_information_structure(
                source=source,
                analysis_type=analysis_type.value,
                depth=depth,
                include_metrics=include_metrics,
                output_format=output_format.value,
            )
            
            progress.update(task, description="Analysis complete")
        
        add_span_event("infodesign.analysis.completed", {
            "entities_found": result.get("entities_count", 0),
            "relationships_found": result.get("relationships_count", 0),
            "complexity_score": result.get("complexity_score", 0),
        })
        
        if output_format == OutputFormat.json:
            maybe_json(ctx, result, exit_code=0)
            return
        
        # Display results
        console.print(f"[bold green]✅ Analysis Complete: {source}[/bold green]")
        console.print(f"[blue]📊 Type: {analysis_type.value.title()}[/blue]")
        
        # Show summary
        summary = result.get("summary", {})
        if summary:
            table = Table(title="📈 Analysis Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")
            table.add_column("Score", style="green")
            
            for metric, data in summary.items():
                table.add_row(
                    metric.replace("_", " ").title(),
                    str(data.get("value", "N/A")),
                    f"{data.get('score', 0):.1f}/10"
                )
            
            console.print(table)
        
        # Show recommendations
        if result.get("recommendations"):
            console.print("\n[bold]💡 Recommendations:[/bold]")
            for i, rec in enumerate(result["recommendations"][:5], 1):
                console.print(f"  {i}. {rec}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.analysis.failed", {"error": str(e)})
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("generate")
@instrument_command("infodesign_generate", track_args=True)
def generate_documentation(
    ctx: typer.Context,
    input_path: Path = typer.Argument(..., help="Input source for documentation"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file/directory"),
    doc_type: str = typer.Option("comprehensive", "--type", "-t", help="Documentation type"),
    template: Optional[str] = typer.Option(None, "--template", help="Template to use"),
    include_diagrams: bool = typer.Option(True, "--diagrams/--no-diagrams", help="Include diagrams"),
    output_format: OutputFormat = typer.Option(OutputFormat.markdown, "--format", "-f", help="Output format"),
):
    """Generate intelligent documentation using DSPy."""
    add_span_attributes(**{
        "infodesign.operation": "generate",
        "infodesign.input": str(input_path),
        "infodesign.doc_type": doc_type,
        "infodesign.template": template or "default",
        "infodesign.diagrams": include_diagrams,
        "infodesign.format": output_format.value,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating documentation...", total=None)
            
            result = info_ops.generate_documentation(
                input_path=input_path,
                output_path=output_path,
                doc_type=doc_type,
                template=template,
                include_diagrams=include_diagrams,
                output_format=output_format.value,
            )
            
            progress.update(task, description="Documentation generated")
        
        add_span_event("infodesign.generation.completed", {
            "files_generated": len(result.get("generated_files", [])),
            "words_generated": result.get("word_count", 0),
            "sections_created": result.get("sections_count", 0),
        })
        
        console.print(f"[bold green]✅ Documentation Generated[/bold green]")
        if result.get("output_path"):
            console.print(f"[blue]📄 Output: {result['output_path']}[/blue]")
        
        # Show generation statistics
        stats = result.get("statistics", {})
        if stats:
            console.print(f"\n[bold]📊 Generation Statistics:[/bold]")
            console.print(f"  • Files: {stats.get('files_count', 0)}")
            console.print(f"  • Words: {stats.get('word_count', 0):,}")
            console.print(f"  • Sections: {stats.get('sections_count', 0)}")
            console.print(f"  • Diagrams: {stats.get('diagrams_count', 0)}")
        
        # Show generated files
        if result.get("generated_files"):
            console.print("\n[bold]📁 Generated Files:[/bold]")
            tree = Tree("📂 Documentation")
            for file_info in result["generated_files"]:
                tree.add(f"📄 {file_info['name']} ({file_info.get('size', 'N/A')})")
            console.print(tree)
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.generation.failed", {"error": str(e)})
        console.print(f"[red]❌ Generation failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("optimize")
@instrument_command("infodesign_optimize", track_args=True)
def optimize_structure(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Source to optimize"),
    pattern: DesignPattern = typer.Option(DesignPattern.hierarchical, "--pattern", "-p", help="Design pattern"),
    target_audience: str = typer.Option("general", "--audience", "-a", help="Target audience"),
    optimize_for: str = typer.Option("readability", "--optimize", help="Optimization target"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
):
    """Optimize information architecture using DSPy."""
    add_span_attributes(**{
        "infodesign.operation": "optimize",
        "infodesign.source": str(source),
        "infodesign.pattern": pattern.value,
        "infodesign.audience": target_audience,
        "infodesign.optimize_for": optimize_for,
        "infodesign.dry_run": dry_run,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing current structure...", total=None)
            
            result = info_ops.optimize_information_structure(
                source=source,
                pattern=pattern.value,
                target_audience=target_audience,
                optimize_for=optimize_for,
                dry_run=dry_run,
            )
            
            progress.update(task, description="Optimization complete")
        
        add_span_event("infodesign.optimization.completed", {
            "changes_proposed": len(result.get("proposed_changes", [])),
            "improvement_score": result.get("improvement_score", 0),
            "applied": not dry_run,
        })
        
        console.print(f"[bold green]✅ Optimization {'Analysis' if dry_run else 'Complete'}[/bold green]")
        
        # Show optimization results
        if result.get("current_score") and result.get("optimized_score"):
            console.print(f"[blue]📈 Score Improvement: {result['current_score']:.1f} → {result['optimized_score']:.1f}[/blue]")
        
        # Show proposed changes
        changes = result.get("proposed_changes", [])
        if changes:
            console.print(f"\n[bold]🔧 {'Proposed' if dry_run else 'Applied'} Changes:[/bold]")
            table = Table()
            table.add_column("Type", style="cyan")
            table.add_column("Target", style="yellow")
            table.add_column("Change", style="green")
            table.add_column("Impact", style="blue")
            
            for change in changes[:10]:  # Show top 10
                table.add_row(
                    change.get("type", ""),
                    change.get("target", ""),
                    change.get("description", ""),
                    f"+{change.get('impact_score', 0):.1f}"
                )
            
            console.print(table)
            
            if len(changes) > 10:
                console.print(f"[dim]... and {len(changes) - 10} more changes[/dim]")
        
        # Show recommendations
        if result.get("recommendations"):
            console.print(f"\n[bold]💡 Additional Recommendations:[/bold]")
            for rec in result["recommendations"][:3]:
                console.print(f"  • {rec}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.optimization.failed", {"error": str(e)})
        console.print(f"[red]❌ Optimization failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("extract")
@instrument_command("infodesign_extract", track_args=True)
def extract_knowledge(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Source to extract knowledge from"),
    extract_type: str = typer.Option("entities", "--type", "-t", help="Type: entities, concepts, relationships"),
    model: str = typer.Option("gpt-3.5-turbo", "--model", "-m", help="AI model to use"),
    confidence_threshold: float = typer.Option(0.7, "--confidence", "-c", help="Confidence threshold (0-1)"),
    max_items: int = typer.Option(100, "--limit", "-l", help="Maximum items to extract"),
):
    """Extract knowledge entities and relationships using DSPy."""
    add_span_attributes(**{
        "infodesign.operation": "extract",
        "infodesign.source": str(source),
        "infodesign.extract_type": extract_type,
        "infodesign.model": model,
        "infodesign.confidence": confidence_threshold,
        "infodesign.limit": max_items,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Extracting {extract_type}...", total=None)
            
            result = info_ops.extract_knowledge(
                source=source,
                extract_type=extract_type,
                model=model,
                confidence_threshold=confidence_threshold,
                max_items=max_items,
            )
            
            progress.update(task, description="Extraction complete")
        
        add_span_event("infodesign.extraction.completed", {
            "items_extracted": len(result.get("extracted_items", [])),
            "avg_confidence": result.get("average_confidence", 0),
            "processing_time": result.get("processing_time", 0),
        })
        
        console.print(f"[bold green]✅ Knowledge Extraction Complete[/bold green]")
        console.print(f"[blue]🔍 Extracted {len(result.get('extracted_items', []))} {extract_type}[/blue]")
        
        # Show extraction results
        items = result.get("extracted_items", [])
        if items:
            table = Table(title=f"🧠 Extracted {extract_type.title()}")
            table.add_column("Item", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Confidence", style="green")
            table.add_column("Context", style="dim")
            
            for item in items[:15]:  # Show top 15
                table.add_row(
                    item.get("name", ""),
                    item.get("type", ""),
                    f"{item.get('confidence', 0):.2f}",
                    item.get("context", "")[:50] + "..." if len(item.get("context", "")) > 50 else item.get("context", "")
                )
            
            console.print(table)
            
            if len(items) > 15:
                console.print(f"[dim]... and {len(items) - 15} more items[/dim]")
        
        # Show statistics
        stats = result.get("statistics", {})
        if stats:
            console.print(f"\n[bold]📊 Extraction Statistics:[/bold]")
            console.print(f"  • Total items: {stats.get('total_items', 0)}")
            console.print(f"  • High confidence: {stats.get('high_confidence_items', 0)}")
            console.print(f"  • Processing time: {stats.get('processing_time', 0):.2f}s")
            console.print(f"  • Average confidence: {stats.get('average_confidence', 0):.2f}")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.extraction.failed", {"error": str(e)})
        console.print(f"[red]❌ Extraction failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("graph")
@instrument_command("infodesign_graph", track_args=True)
def create_knowledge_graph(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Source for knowledge graph"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for graph"),
    graph_type: str = typer.Option("semantic", "--type", "-t", help="Graph type: semantic, dependency, flow"),
    layout: str = typer.Option("force", "--layout", "-l", help="Graph layout algorithm"),
    include_metadata: bool = typer.Option(True, "--metadata/--no-metadata", help="Include node metadata"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, gml, dot"),
):
    """Create knowledge graphs and visualizations using DSPy."""
    add_span_attributes(**{
        "infodesign.operation": "graph",
        "infodesign.source": str(source),
        "infodesign.graph_type": graph_type,
        "infodesign.layout": layout,
        "infodesign.metadata": include_metadata,
        "infodesign.format": format,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Building knowledge graph...", total=None)
            
            result = info_ops.create_knowledge_graph(
                source=source,
                output=output,
                graph_type=graph_type,
                layout=layout,
                include_metadata=include_metadata,
                output_format=format,
            )
            
            progress.update(task, description="Graph created")
        
        add_span_event("infodesign.graph.completed", {
            "nodes_count": result.get("nodes_count", 0),
            "edges_count": result.get("edges_count", 0),
            "graph_density": result.get("graph_density", 0),
        })
        
        console.print(f"[bold green]✅ Knowledge Graph Created[/bold green]")
        if result.get("output_path"):
            console.print(f"[blue]📊 Output: {result['output_path']}[/blue]")
        
        # Show graph statistics
        console.print(f"\n[bold]🕸️ Graph Statistics:[/bold]")
        console.print(f"  • Nodes: {result.get('nodes_count', 0)}")
        console.print(f"  • Edges: {result.get('edges_count', 0)}")
        console.print(f"  • Density: {result.get('graph_density', 0):.3f}")
        console.print(f"  • Clusters: {result.get('clusters_count', 0)}")
        
        # Show top nodes by centrality
        if result.get("top_nodes"):
            console.print(f"\n[bold]⭐ Most Central Nodes:[/bold]")
            for i, node in enumerate(result["top_nodes"][:5], 1):
                console.print(f"  {i}. {node['name']} (centrality: {node['centrality']:.3f})")
        
        # Show clusters
        if result.get("clusters"):
            console.print(f"\n[bold]🎯 Main Clusters:[/bold]")
            for i, cluster in enumerate(result["clusters"][:3], 1):
                console.print(f"  {i}. {cluster['name']} ({cluster['size']} nodes)")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.graph.failed", {"error": str(e)})
        console.print(f"[red]❌ Graph creation failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("template")
@instrument_command("infodesign_template", track_args=True)
def manage_templates(
    ctx: typer.Context,
    action: str = typer.Argument(..., help="Action: create, list, apply, delete"),
    template_name: Optional[str] = typer.Option(None, "--name", "-n", help="Template name"),
    source: Optional[Path] = typer.Option(None, "--source", "-s", help="Source for template creation"),
    target: Optional[Path] = typer.Option(None, "--target", "-t", help="Target for template application"),
    template_type: str = typer.Option("documentation", "--type", help="Template type"),
):
    """Create and manage reusable information templates."""
    add_span_attributes(**{
        "infodesign.operation": "template",
        "infodesign.action": action,
        "infodesign.template_name": template_name or "",
        "infodesign.template_type": template_type,
    })
    
    try:
        from uvmgr.ops import infodesign as info_ops
        
        result = info_ops.manage_templates(
            action=action,
            template_name=template_name,
            source=source,
            target=target,
            template_type=template_type,
        )
        
        add_span_event("infodesign.template.completed", {
            "action": action,
            "template_count": len(result.get("templates", [])) if action == "list" else 1,
        })
        
        if action == "list":
            console.print("[bold]📋 Available Templates:[/bold]")
            templates = result.get("templates", [])
            
            if not templates:
                console.print("[yellow]No templates found[/yellow]")
            else:
                table = Table()
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="yellow")
                table.add_column("Created", style="dim")
                table.add_column("Usage", style="green")
                
                for template in templates:
                    table.add_row(
                        template["name"],
                        template["type"],
                        template.get("created", "Unknown"),
                        str(template.get("usage_count", 0))
                    )
                
                console.print(table)
        
        elif action == "create":
            console.print(f"[bold green]✅ Template '{template_name}' created[/bold green]")
            if result.get("template_path"):
                console.print(f"[blue]📄 Location: {result['template_path']}[/blue]")
        
        elif action == "apply":
            console.print(f"[bold green]✅ Template '{template_name}' applied[/bold green]")
            if result.get("generated_files"):
                console.print(f"[blue]📁 Generated {len(result['generated_files'])} files[/blue]")
        
        elif action == "delete":
            console.print(f"[bold green]✅ Template '{template_name}' deleted[/bold green]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("infodesign.template.failed", {"error": str(e)})
        console.print(f"[red]❌ Template {action} failed: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)