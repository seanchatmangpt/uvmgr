"""
uvmgr.commands.mermaid - Full Mermaid Support with Weaver Forge + DSPy
=====================================================================

Comprehensive Mermaid diagram generation using 80/20 principles with
Weaver Forge semantic conventions and DSPy intelligent processing.

This module provides complete Mermaid diagram support including:
- All major Mermaid diagram types (80/20 prioritized)
- Weaver Forge integration for semantic conventions
- DSPy-powered intelligent diagram generation
- OTEL instrumentation and validation
- Rich CLI experience with preview and export

Key Features (80/20 Priority)
----------------------------
• **Flowcharts** (Priority 1) - Most commonly used
• **Sequence Diagrams** (Priority 2) - High business value
• **Class Diagrams** (Priority 3) - Code documentation
• **Git Graphs** (Priority 4) - Development workflow
• **Architecture Diagrams** (Priority 5) - System design
• **All Other Types** (Priority 6) - Complete coverage

Weaver Forge Integration
-----------------------
• Semantic convention validation
• Auto-generation from telemetry data
• Architecture diagram generation
• Service dependency mapping

DSPy Intelligence
----------------
• Content-aware diagram generation
• Smart layout optimization
• Auto-entity detection
• Relationship inference

Available Commands
-----------------
- **generate**: Generate Mermaid diagrams from various sources
- **preview**: Preview diagrams in browser/terminal
- **export**: Export to PNG, SVG, PDF formats
- **validate**: Validate Mermaid syntax and semantics
- **templates**: Manage reusable diagram templates
- **weaver**: Generate diagrams from Weaver Forge data
- **analyze**: Analyze existing diagrams and suggest improvements

Examples
--------
    >>> # Generate flowchart from code
    >>> uvmgr mermaid generate --type flowchart --source src/
    >>> 
    >>> # Create sequence diagram with DSPy
    >>> uvmgr mermaid generate --type sequence --input "user login process"
    >>> 
    >>> # Generate architecture from OTEL data
    >>> uvmgr mermaid weaver --type architecture --service-map
    >>> 
    >>> # Export diagram to PNG
    >>> uvmgr mermaid export diagram.mmd --format png

See Also
--------
- :mod:`uvmgr.ops.mermaid` : Mermaid operations with Weaver + DSPy
- :mod:`uvmgr.runtime.mermaid` : Runtime processing and export
- :mod:`uvmgr.core.weaver` : Weaver Forge integration
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
from rich.syntax import Syntax

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import InfoDesignAttributes, InfoDesignOperations
from uvmgr.cli_utils import maybe_json

console = Console()
app = typer.Typer(help="Full Mermaid support with Weaver Forge + DSPy")


class MermaidType(str, Enum):
    """Mermaid diagram types (80/20 prioritized)"""
    # Priority 1-2: Most commonly used (80% of use cases)
    flowchart = "flowchart"
    sequence = "sequence"
    
    # Priority 3-4: High value for development
    class_diagram = "class"
    git_graph = "gitgraph"
    
    # Priority 5-6: Architecture and system design
    architecture = "architecture"
    c4_context = "c4context"
    
    # Complete coverage: All other types
    state = "state"
    entity_relationship = "er"
    user_journey = "journey"
    gantt = "gantt"
    pie = "pie"
    requirement = "requirement"
    mindmap = "mindmap"
    timeline = "timeline"
    sankey = "sankey"
    block = "block"


class ExportFormat(str, Enum):
    """Export format options"""
    mermaid = "mmd"
    png = "png"
    svg = "svg"
    pdf = "pdf"
    html = "html"


class SourceType(str, Enum):
    """Source type for diagram generation"""
    code = "code"
    text = "text"
    yaml = "yaml"
    json = "json"
    otel = "otel"
    weaver = "weaver"
    auto = "auto"


@app.command("generate")
@instrument_command("mermaid_generate", track_args=True)
def generate_diagram(
    ctx: typer.Context,
    diagram_type: MermaidType = typer.Argument(..., help="Type of Mermaid diagram to generate"),
    source: Optional[Path] = typer.Option(None, "--source", "-s", help="Source file or directory"),
    input_text: Optional[str] = typer.Option(None, "--input", "-i", help="Input text for DSPy generation"),
    source_type: SourceType = typer.Option(SourceType.auto, "--source-type", "-t", help="Source type"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    title: Optional[str] = typer.Option(None, "--title", help="Diagram title"),
    use_dspy: bool = typer.Option(True, "--dspy/--no-dspy", help="Use DSPy for intelligent generation"),
    weaver_integration: bool = typer.Option(False, "--weaver", help="Use Weaver Forge integration"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview diagram after generation"),
):
    """Generate Mermaid diagrams from various sources using DSPy intelligence."""
    add_span_attributes(**{
        "mermaid.operation": "generate",
        "mermaid.type": diagram_type.value,
        "mermaid.source": str(source) if source else "",
        "mermaid.source_type": source_type.value,
        "mermaid.use_dspy": use_dspy,
        "mermaid.weaver_integration": weaver_integration,
        "mermaid.has_input_text": bool(input_text),
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating {diagram_type.value} diagram...", total=None)
            
            result = mermaid_ops.generate_mermaid_diagram(
                diagram_type=diagram_type.value,
                source=source,
                input_text=input_text,
                source_type=source_type.value,
                title=title,
                use_dspy=use_dspy,
                weaver_integration=weaver_integration,
            )
            
            progress.update(task, description="Diagram generated successfully")
        
        add_span_event("mermaid.generation.completed", {
            "diagram_type": diagram_type.value,
            "nodes_count": result.get("nodes_count", 0),
            "edges_count": result.get("edges_count", 0),
            "complexity_score": result.get("complexity_score", 0),
            "generation_method": "dspy" if use_dspy else "template",
        })
        
        # Display generation results
        console.print(f"[bold green]✅ {diagram_type.value.title()} diagram generated successfully![/bold green]")
        
        if result.get("mermaid_code"):
            # Save to output file if specified
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(result["mermaid_code"])
                console.print(f"[blue]💾 Saved to: {output}[/blue]")
            
            # Show diagram code with syntax highlighting
            console.print("\n[bold]📊 Generated Mermaid Code:[/bold]")
            syntax = Syntax(result["mermaid_code"], "mermaid", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Mermaid Diagram", border_style="cyan"))
            
            # Show generation statistics
            if result.get("statistics"):
                stats = result["statistics"]
                console.print(f"\n[bold]📈 Generation Statistics:[/bold]")
                console.print(f"  • Nodes: {stats.get('nodes_count', 0)}")
                console.print(f"  • Connections: {stats.get('edges_count', 0)}")
                console.print(f"  • Complexity: {stats.get('complexity_score', 0):.1f}/10")
                console.print(f"  • Generation time: {stats.get('generation_time', 0):.2f}s")
                
                if use_dspy and stats.get("dspy_confidence"):
                    console.print(f"  • DSPy confidence: {stats['dspy_confidence']:.2f}")
            
            # Show suggestions if available
            if result.get("suggestions"):
                console.print(f"\n[bold]💡 Suggestions:[/bold]")
                for suggestion in result["suggestions"][:3]:
                    console.print(f"  • {suggestion}")
            
            # Preview if requested
            if preview:
                console.print(f"\n[yellow]🔍 Opening preview...[/yellow]")
                preview_result = mermaid_ops.preview_diagram(result["mermaid_code"])
                if preview_result.get("preview_url"):
                    console.print(f"[blue]🌐 Preview: {preview_result['preview_url']}[/blue]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.generation.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to generate diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("weaver")
@instrument_command("mermaid_weaver", track_args=True)
def weaver_generate(
    ctx: typer.Context,
    diagram_type: MermaidType = typer.Argument(MermaidType.architecture, help="Diagram type"),
    service_map: bool = typer.Option(False, "--service-map", help="Generate service dependency map"),
    telemetry_flow: bool = typer.Option(False, "--telemetry-flow", help="Generate telemetry flow diagram"),
    semantic_conventions: bool = typer.Option(False, "--semconv", help="Include semantic conventions"),
    trace_analysis: bool = typer.Option(False, "--traces", help="Analyze trace data"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    format: ExportFormat = typer.Option(ExportFormat.mermaid, "--format", "-f", help="Export format"),
):
    """Generate diagrams from Weaver Forge and OTEL data."""
    add_span_attributes(**{
        "mermaid.operation": "weaver_generate",
        "mermaid.type": diagram_type.value,
        "mermaid.service_map": service_map,
        "mermaid.telemetry_flow": telemetry_flow,
        "mermaid.semantic_conventions": semantic_conventions,
        "mermaid.trace_analysis": trace_analysis,
        "mermaid.format": format.value,
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing Weaver Forge data...", total=None)
            
            result = mermaid_ops.generate_weaver_diagram(
                diagram_type=diagram_type.value,
                service_map=service_map,
                telemetry_flow=telemetry_flow,
                semantic_conventions=semantic_conventions,
                trace_analysis=trace_analysis,
            )
            
            progress.update(task, description="Weaver diagram generated")
        
        add_span_event("mermaid.weaver.completed", {
            "diagram_type": diagram_type.value,
            "services_found": result.get("services_count", 0),
            "spans_analyzed": result.get("spans_count", 0),
            "conventions_used": result.get("conventions_count", 0),
        })
        
        console.print(f"[bold green]✅ Weaver Forge {diagram_type.value} diagram generated![/bold green]")
        
        # Show Weaver analysis results
        if result.get("weaver_analysis"):
            analysis = result["weaver_analysis"]
            console.print(f"\n[bold]🔍 Weaver Forge Analysis:[/bold]")
            console.print(f"  • Services discovered: {analysis.get('services_count', 0)}")
            console.print(f"  • Spans analyzed: {analysis.get('spans_count', 0)}")
            console.print(f"  • Semantic conventions: {analysis.get('conventions_count', 0)}")
            console.print(f"  • Trace depth: {analysis.get('max_depth', 0)} levels")
        
        # Display generated diagram
        if result.get("mermaid_code"):
            console.print("\n[bold]📊 Generated Architecture Diagram:[/bold]")
            syntax = Syntax(result["mermaid_code"], "mermaid", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Weaver Forge Diagram", border_style="blue"))
        
        # Export if requested
        if output and result.get("mermaid_code"):
            export_result = mermaid_ops.export_diagram(
                result["mermaid_code"], 
                output, 
                format.value
            )
            console.print(f"[blue]💾 Exported to: {export_result['output_path']}[/blue]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.weaver.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to generate Weaver diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("export")
@instrument_command("mermaid_export", track_args=True)
def export_diagram(
    ctx: typer.Context,
    input_file: Path = typer.Argument(..., help="Input Mermaid file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    format: ExportFormat = typer.Option(ExportFormat.png, "--format", "-f", help="Export format"),
    width: int = typer.Option(1920, "--width", help="Image width for raster formats"),
    height: int = typer.Option(1080, "--height", help="Image height for raster formats"),
    theme: str = typer.Option("default", "--theme", help="Mermaid theme"),
    background: str = typer.Option("white", "--background", help="Background color"),
):
    """Export Mermaid diagrams to various formats."""
    add_span_attributes(**{
        "mermaid.operation": "export",
        "mermaid.input": str(input_file),
        "mermaid.format": format.value,
        "mermaid.width": width,
        "mermaid.height": height,
        "mermaid.theme": theme,
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Exporting to {format.value.upper()}...", total=None)
            
            # Read Mermaid content
            with open(input_file, 'r', encoding='utf-8') as f:
                mermaid_code = f.read()
            
            result = mermaid_ops.export_diagram(
                mermaid_code=mermaid_code,
                output_path=output or input_file.with_suffix(f'.{format.value}'),
                export_format=format.value,
                width=width,
                height=height,
                theme=theme,
                background=background,
            )
            
            progress.update(task, description="Export completed")
        
        add_span_event("mermaid.export.completed", {
            "format": format.value,
            "output_size": result.get("file_size", 0),
            "export_time": result.get("export_time", 0),
        })
        
        console.print(f"[bold green]✅ Exported to {format.value.upper()} successfully![/bold green]")
        console.print(f"[blue]📁 Output: {result['output_path']}[/blue]")
        console.print(f"[cyan]📏 Size: {result.get('file_size_human', 'Unknown')}[/cyan]")
        
        if result.get("export_time"):
            console.print(f"[dim]⏱️  Export time: {result['export_time']:.2f}s[/dim]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.export.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to export diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("validate")
@instrument_command("mermaid_validate", track_args=True)
def validate_diagram(
    ctx: typer.Context,
    input_file: Path = typer.Argument(..., help="Mermaid file to validate"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation mode"),
    check_syntax: bool = typer.Option(True, "--syntax/--no-syntax", help="Check syntax"),
    check_semantics: bool = typer.Option(True, "--semantics/--no-semantics", help="Check semantics"),
    suggest_improvements: bool = typer.Option(True, "--suggestions/--no-suggestions", help="Suggest improvements"),
):
    """Validate Mermaid diagram syntax and semantics."""
    add_span_attributes(**{
        "mermaid.operation": "validate",
        "mermaid.input": str(input_file),
        "mermaid.strict": strict,
        "mermaid.check_syntax": check_syntax,
        "mermaid.check_semantics": check_semantics,
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            mermaid_code = f.read()
        
        result = mermaid_ops.validate_mermaid_diagram(
            mermaid_code=mermaid_code,
            strict=strict,
            check_syntax=check_syntax,
            check_semantics=check_semantics,
            suggest_improvements=suggest_improvements,
        )
        
        add_span_event("mermaid.validation.completed", {
            "is_valid": result.get("is_valid", False),
            "syntax_errors": len(result.get("syntax_errors", [])),
            "semantic_errors": len(result.get("semantic_errors", [])),
            "suggestions_count": len(result.get("suggestions", [])),
        })
        
        # Display validation results
        is_valid = result.get("is_valid", False)
        
        if is_valid:
            console.print(f"[bold green]✅ Diagram validation passed![/bold green]")
        else:
            console.print(f"[bold red]❌ Diagram validation failed![/bold red]")
        
        # Show syntax errors
        syntax_errors = result.get("syntax_errors", [])
        if syntax_errors:
            console.print(f"\n[bold red]🚫 Syntax Errors ({len(syntax_errors)}):[/bold red]")
            table = Table()
            table.add_column("Line", style="cyan")
            table.add_column("Error", style="red")
            table.add_column("Suggestion", style="yellow")
            
            for error in syntax_errors:
                table.add_row(
                    str(error.get("line", "?")),
                    error.get("message", ""),
                    error.get("suggestion", "")
                )
            console.print(table)
        
        # Show semantic errors
        semantic_errors = result.get("semantic_errors", [])
        if semantic_errors:
            console.print(f"\n[bold yellow]⚠️  Semantic Issues ({len(semantic_errors)}):[/bold yellow]")
            for error in semantic_errors:
                console.print(f"  • {error.get('message', '')}")
        
        # Show improvement suggestions
        suggestions = result.get("suggestions", [])
        if suggestions and suggest_improvements:
            console.print(f"\n[bold blue]💡 Improvement Suggestions:[/bold blue]")
            for suggestion in suggestions[:5]:
                console.print(f"  • {suggestion}")
        
        # Show validation statistics
        if result.get("statistics"):
            stats = result["statistics"]
            console.print(f"\n[bold]📊 Diagram Statistics:[/bold]")
            console.print(f"  • Nodes: {stats.get('nodes_count', 0)}")
            console.print(f"  • Connections: {stats.get('edges_count', 0)}")
            console.print(f"  • Complexity: {stats.get('complexity_score', 0):.1f}/10")
            console.print(f"  • Type: {stats.get('diagram_type', 'unknown')}")
        
        maybe_json(ctx, result, exit_code=0 if is_valid else 1)
        
        if not is_valid and strict:
            raise typer.Exit(1)
        
    except Exception as e:
        add_span_event("mermaid.validation.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to validate diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("preview")
@instrument_command("mermaid_preview", track_args=True)
def preview_diagram(
    ctx: typer.Context,
    input_file: Path = typer.Argument(..., help="Mermaid file to preview"),
    browser: bool = typer.Option(True, "--browser/--terminal", help="Open in browser vs terminal"),
    theme: str = typer.Option("default", "--theme", help="Mermaid theme"),
    port: int = typer.Option(8080, "--port", help="Local server port for browser preview"),
):
    """Preview Mermaid diagrams in browser or terminal."""
    add_span_attributes(**{
        "mermaid.operation": "preview",
        "mermaid.input": str(input_file),
        "mermaid.browser": browser,
        "mermaid.theme": theme,
        "mermaid.port": port,
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            mermaid_code = f.read()
        
        result = mermaid_ops.preview_diagram(
            mermaid_code=mermaid_code,
            browser=browser,
            theme=theme,
            port=port,
        )
        
        add_span_event("mermaid.preview.completed", {
            "browser": browser,
            "preview_method": result.get("preview_method", "unknown"),
        })
        
        if browser and result.get("preview_url"):
            console.print(f"[bold green]🌐 Opening browser preview...[/bold green]")
            console.print(f"[blue]📱 URL: {result['preview_url']}[/blue]")
            console.print(f"[yellow]Press Ctrl+C to stop the preview server[/yellow]")
        else:
            console.print(f"[bold green]📺 Terminal preview:[/bold green]")
            if result.get("terminal_preview"):
                console.print(result["terminal_preview"])
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.preview.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to preview diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("templates")
@instrument_command("mermaid_templates", track_args=True)
def manage_templates(
    ctx: typer.Context,
    action: str = typer.Argument(..., help="Action: list, create, apply, delete"),
    template_name: Optional[str] = typer.Option(None, "--name", "-n", help="Template name"),
    diagram_type: Optional[MermaidType] = typer.Option(None, "--type", "-t", help="Diagram type"),
    source: Optional[Path] = typer.Option(None, "--source", "-s", help="Source for template creation"),
):
    """Manage reusable Mermaid diagram templates."""
    add_span_attributes(**{
        "mermaid.operation": "templates",
        "mermaid.action": action,
        "mermaid.template_name": template_name or "",
        "mermaid.diagram_type": diagram_type.value if diagram_type else "",
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        result = mermaid_ops.manage_mermaid_templates(
            action=action,
            template_name=template_name,
            diagram_type=diagram_type.value if diagram_type else None,
            source=source,
        )
        
        add_span_event("mermaid.templates.completed", {
            "action": action,
            "template_count": len(result.get("templates", [])) if action == "list" else 1,
        })
        
        if action == "list":
            templates = result.get("templates", [])
            if not templates:
                console.print("[yellow]No Mermaid templates found[/yellow]")
            else:
                console.print("[bold]📋 Available Mermaid Templates:[/bold]")
                table = Table()
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="yellow")
                table.add_column("Created", style="dim")
                table.add_column("Usage", style="green")
                table.add_column("Description", style="white")
                
                for template in templates:
                    table.add_row(
                        template["name"],
                        template["diagram_type"],
                        template.get("created", "Unknown"),
                        str(template.get("usage_count", 0)),
                        template.get("description", "")[:50] + "..." if len(template.get("description", "")) > 50 else template.get("description", "")
                    )
                
                console.print(table)
        
        elif action == "create":
            console.print(f"[bold green]✅ Template '{template_name}' created![/bold green]")
            if result.get("template_path"):
                console.print(f"[blue]📄 Location: {result['template_path']}[/blue]")
        
        elif action == "apply":
            console.print(f"[bold green]✅ Template '{template_name}' applied![/bold green]")
            if result.get("output_file"):
                console.print(f"[blue]📁 Generated: {result['output_file']}[/blue]")
        
        elif action == "delete":
            console.print(f"[bold green]✅ Template '{template_name}' deleted![/bold green]")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.templates.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to manage templates: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)


@app.command("analyze")
@instrument_command("mermaid_analyze", track_args=True)
def analyze_diagram(
    ctx: typer.Context,
    input_file: Path = typer.Argument(..., help="Mermaid file to analyze"),
    complexity_analysis: bool = typer.Option(True, "--complexity/--no-complexity", help="Analyze complexity"),
    layout_analysis: bool = typer.Option(True, "--layout/--no-layout", help="Analyze layout"),
    accessibility_check: bool = typer.Option(False, "--accessibility", help="Check accessibility"),
    performance_check: bool = typer.Option(False, "--performance", help="Check rendering performance"),
):
    """Analyze existing Mermaid diagrams and suggest improvements."""
    add_span_attributes(**{
        "mermaid.operation": "analyze",
        "mermaid.input": str(input_file),
        "mermaid.complexity": complexity_analysis,
        "mermaid.layout": layout_analysis,
        "mermaid.accessibility": accessibility_check,
        "mermaid.performance": performance_check,
    })
    
    try:
        from uvmgr.ops import mermaid as mermaid_ops
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            mermaid_code = f.read()
        
        result = mermaid_ops.analyze_mermaid_diagram(
            mermaid_code=mermaid_code,
            complexity_analysis=complexity_analysis,
            layout_analysis=layout_analysis,
            accessibility_check=accessibility_check,
            performance_check=performance_check,
        )
        
        add_span_event("mermaid.analysis.completed", {
            "complexity_score": result.get("complexity_score", 0),
            "layout_score": result.get("layout_score", 0),
            "recommendations_count": len(result.get("recommendations", [])),
        })
        
        console.print(f"[bold green]📊 Diagram Analysis Complete![/bold green]")
        
        # Show analysis results
        if complexity_analysis and result.get("complexity_analysis"):
            complexity = result["complexity_analysis"]
            console.print(f"\n[bold]🔍 Complexity Analysis:[/bold]")
            console.print(f"  • Overall score: {complexity['score']:.1f}/10")
            console.print(f"  • Nodes: {complexity['nodes_count']}")
            console.print(f"  • Connections: {complexity['edges_count']}")
            console.print(f"  • Depth: {complexity.get('max_depth', 0)} levels")
            console.print(f"  • Branching factor: {complexity.get('branching_factor', 0):.1f}")
        
        if layout_analysis and result.get("layout_analysis"):
            layout = result["layout_analysis"]
            console.print(f"\n[bold]📐 Layout Analysis:[/bold]")
            console.print(f"  • Layout score: {layout['score']:.1f}/10")
            console.print(f"  • Balance: {layout.get('balance_score', 0):.1f}/10")
            console.print(f"  • Symmetry: {layout.get('symmetry_score', 0):.1f}/10")
            console.print(f"  • Readability: {layout.get('readability_score', 0):.1f}/10")
        
        # Show recommendations
        recommendations = result.get("recommendations", [])
        if recommendations:
            console.print(f"\n[bold]💡 Recommendations:[/bold]")
            for i, rec in enumerate(recommendations[:5], 1):
                console.print(f"  {i}. {rec['description']} (Impact: {rec.get('impact', 'Medium')})")
        
        # Show performance metrics
        if performance_check and result.get("performance_analysis"):
            perf = result["performance_analysis"]
            console.print(f"\n[bold]⚡ Performance Analysis:[/bold]")
            console.print(f"  • Estimated render time: {perf.get('estimated_render_time', 0):.2f}s")
            console.print(f"  • Memory usage: {perf.get('memory_estimate', 'Unknown')}")
            console.print(f"  • Optimization potential: {perf.get('optimization_score', 0):.1f}/10")
        
        maybe_json(ctx, result, exit_code=0)
        
    except Exception as e:
        add_span_event("mermaid.analysis.failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to analyze diagram: {e}[/red]")
        maybe_json(ctx, {"error": str(e)}, exit_code=1)
        raise typer.Exit(1)