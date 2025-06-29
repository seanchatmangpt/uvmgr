"""
uvmgr.commands.agent_guides - Agent Guides Integration
====================================================

Agent guides integration for uvmgr, adapting the tokenbender/agent-guides approach
to our 3-tier architecture with DSPy and Lean Six Sigma capabilities.

This module provides CLI commands for managing agent guides, custom commands,
and AI-assisted development workflows using the 8020 principle.

Key Features
-----------
• **Guide Management**: Install, update, and manage agent guides
• **Custom Commands**: Create and execute custom slash commands
• **Multi-Mind Analysis**: Collaborative multi-specialist analysis
• **Conversation Search**: Search across Claude conversation history
• **Deep Code Analysis**: Line-by-line code analysis with insights
• **Anti-Repetition Workflows**: Progressive knowledge building
• **DSPy Integration**: Intelligent decision making and optimization
• **Lean Six Sigma**: End-to-end project creation and validation

Available Commands
-----------------
- **install**: Install agent guides from repository
- **search**: Search conversation history and guides
- **multi-mind**: Execute collaborative multi-specialist analysis
- **analyze**: Deep code analysis with performance insights
- **create**: Create custom agent guides and commands
- **validate**: Validate guides using Lean Six Sigma principles
- **workflow**: Execute anti-repetition workflows
- **status**: Show guide status and metrics

Examples
--------
    >>> # Install agent guides
    >>> uvmgr agent-guides install --source tokenbender/agent-guides
    >>> 
    >>> # Multi-mind analysis
    >>> uvmgr agent-guides multi-mind "Should we implement quantum error correction?"
    >>> 
    >>> # Search conversations
    >>> uvmgr agent-guides search "machine learning pipeline"
    >>> 
    >>> # Deep code analysis
    >>> uvmgr agent-guides analyze src/uvmgr/core/telemetry.py:span

See Also
--------
- :mod:`uvmgr.ops.agent_guides` : Agent guides operations
- :mod:`uvmgr.commands.claude` : Claude AI integration
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

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes, AIAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.ops.agent_guides import (
    install_agent_guides,
    search_conversations,
    execute_multi_mind_analysis,
    analyze_code_deep,
    create_custom_guide,
    validate_guides,
    execute_anti_repetition_workflow,
    get_guide_status
)

app = typer.Typer(help="Agent guides integration with DSPy and Lean Six Sigma")
console = Console()


class GuideSource(Enum):
    """Agent guide sources."""
    TOKENBENDER = "tokenbender/agent-guides"
    CUSTOM = "custom"
    LOCAL = "local"


class AnalysisType(Enum):
    """Multi-mind analysis types."""
    COLLABORATIVE = "collaborative"
    DEBATE = "debate"
    STRUCTURED = "structured"
    PROGRESSIVE = "progressive"


@app.command("install")
@instrument_command("agent_guides_install", track_args=True)
def install_guides(
    source: GuideSource = typer.Option(
        GuideSource.TOKENBENDER,
        "--source",
        "-s",
        help="Guide source repository"
    ),
    target_dir: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Target directory for guides"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinstall existing guides"
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate guides after installation"
    ),
):
    """
    Install agent guides from repository.
    
    This command installs agent guides from the specified source, adapting them
    to uvmgr's 3-tier architecture and Lean Six Sigma principles.
    
    Examples:
        uvmgr agent-guides install --source tokenbender/agent-guides
        uvmgr agent-guides install --target ~/.uvmgr/guides --force
    """
    add_span_attributes(**{
        "agent_guides.operation": "install",
        "agent_guides.source": source.value,
        "agent_guides.force": force,
        "agent_guides.validate": validate,
    })
    
    console.print(f"📚 [bold cyan]Installing Agent Guides[/bold cyan]")
    console.print(f"🔗 Source: {source.value}")
    if target_dir:
        console.print(f"📁 Target: {target_dir}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Step 1: Download guides
            task1 = progress.add_task("Downloading agent guides...", total=1)
            guides_info = install_agent_guides(source.value, target_dir, force)
            progress.advance(task1)
            
            # Step 2: Validate guides (if requested)
            if validate:
                task2 = progress.add_task("Validating guides...", total=1)
                validation_result = validate_guides(guides_info["guides_path"])
                progress.advance(task2)
                
                if not validation_result["valid"]:
                    console.print(f"[red]❌ Guide validation failed: {validation_result['errors']}[/red]")
                    raise typer.Exit(1)
            
            # Step 3: Display results
            task3 = progress.add_task("Finalizing installation...", total=1)
            progress.advance(task3)
        
        # Display installation summary
        _display_installation_summary(guides_info)
        
        add_span_event("agent_guides.installed", {
            "guides_count": guides_info["guides_count"],
            "source": source.value,
            "validation_passed": validation_result["valid"] if validate else True,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Guide installation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("search")
@instrument_command("agent_guides_search", track_args=True)
def search_guides(
    query: str = typer.Argument(..., help="Search query"),
    sources: List[str] = typer.Option(
        ["conversations", "guides", "code"],
        "--sources",
        "-s",
        help="Search sources"
    ),
    max_results: int = typer.Option(
        10,
        "--max-results",
        "-m",
        help="Maximum number of results"
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, tree"
    ),
):
    """
    Search conversation history and agent guides.
    
    This command searches across Claude conversations, agent guides, and codebase
    using intelligent search algorithms and DSPy-powered relevance ranking.
    
    Examples:
        uvmgr agent-guides search "machine learning pipeline"
        uvmgr agent-guides search "debugging memory issues" --sources conversations
        uvmgr agent-guides search "database optimization" --format json
    """
    add_span_attributes(**{
        "agent_guides.operation": "search",
        "agent_guides.query": query,
        "agent_guides.sources": ",".join(sources),
        "agent_guides.max_results": max_results,
    })
    
    console.print(f"🔍 [bold cyan]Searching Agent Guides[/bold cyan]")
    console.print(f"📝 Query: {query}")
    console.print(f"📚 Sources: {', '.join(sources)}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Searching across sources...", total=1)
            
            # Execute search
            search_results = search_conversations(
                query=query,
                sources=sources,
                max_results=max_results
            )
            progress.advance(task)
        
        # Display results
        if format == "json":
            console.print(json.dumps(search_results, indent=2))
        elif format == "tree":
            _display_search_tree(search_results)
        else:
            _display_search_table(search_results)
        
        add_span_event("agent_guides.search.completed", {
            "results_count": len(search_results.get("results", [])),
            "sources_searched": len(sources),
            "query": query,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Search failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("multi-mind")
@instrument_command("agent_guides_multi_mind", track_args=True)
def multi_mind_analysis(
    topic: str = typer.Argument(..., help="Analysis topic"),
    analysis_type: AnalysisType = typer.Option(
        AnalysisType.COLLABORATIVE,
        "--type",
        "-t",
        help="Analysis type"
    ),
    rounds: int = typer.Option(
        3,
        "--rounds",
        "-r",
        help="Number of analysis rounds"
    ),
    experts: Optional[str] = typer.Option(
        None,
        "--experts",
        "-e",
        help="Comma-separated expert roles (auto-assigned if not specified)"
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save results to file"
    ),
):
    """
    Execute collaborative multi-specialist analysis.
    
    This command orchestrates multi-specialist analysis using DSPy for intelligent
    expert assignment and Lean Six Sigma principles for systematic problem-solving.
    
    Examples:
        uvmgr agent-guides multi-mind "Should we implement quantum error correction?"
        uvmgr agent-guides multi-mind "Climate change mitigation strategies" --rounds 5
        uvmgr agent-guides multi-mind "Scaling transformer architectures" --type debate
    """
    add_span_attributes(**{
        "agent_guides.operation": "multi_mind",
        "agent_guides.topic": topic,
        "agent_guides.type": analysis_type.value,
        "agent_guides.rounds": rounds,
    })
    
    console.print(f"🧠 [bold cyan]Multi-Mind Analysis[/bold cyan]")
    console.print(f"📋 Topic: {topic}")
    console.print(f"🔬 Type: {analysis_type.value}")
    console.print(f"🔄 Rounds: {rounds}")
    
    if experts:
        expert_list = [e.strip() for e in experts.split(",")]
        console.print(f"👥 Experts: {', '.join(expert_list)}")
    else:
        console.print("🤖 Auto-assigning experts based on topic complexity...")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Executing multi-mind analysis...", total=rounds)
            
            # Execute analysis
            analysis_result = execute_multi_mind_analysis(
                topic=topic,
                analysis_type=analysis_type.value,
                rounds=rounds,
                experts=expert_list if experts else None,
                progress_callback=lambda r: progress.advance(task, advance=1)
            )
        
        # Display results
        _display_multi_mind_results(analysis_result)
        
        # Save results if requested
        if output_file:
            output_file.write_text(json.dumps(analysis_result, indent=2))
            console.print(f"💾 Results saved to: {output_file}")
        
        add_span_event("agent_guides.multi_mind.completed", {
            "topic": topic,
            "rounds_completed": rounds,
            "experts_used": len(analysis_result.get("experts", [])),
            "consensus_reached": analysis_result.get("consensus") is not None,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Multi-mind analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("analyze")
@instrument_command("agent_guides_analyze", track_args=True)
def analyze_code(
    target: str = typer.Argument(..., help="Code target (file:function or file path)"),
    analysis_depth: str = typer.Option(
        "deep",
        "--depth",
        "-d",
        help="Analysis depth: quick, standard, deep, comprehensive"
    ),
    include_performance: bool = typer.Option(
        True,
        "--performance/--no-performance",
        help="Include performance analysis"
    ),
    include_security: bool = typer.Option(
        True,
        "--security/--no-security",
        help="Include security analysis"
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, markdown"
    ),
):
    """
    Deep code analysis with performance insights.
    
    This command performs comprehensive code analysis using DSPy for intelligent
    insights and Lean Six Sigma principles for systematic evaluation.
    
    Examples:
        uvmgr agent-guides analyze src/uvmgr/core/telemetry.py:span
        uvmgr agent-guides analyze utils.js:validateInput --depth comprehensive
        uvmgr agent-guides analyze train.py --no-performance --format markdown
    """
    add_span_attributes(**{
        "agent_guides.operation": "analyze",
        "agent_guides.target": target,
        "agent_guides.depth": analysis_depth,
        "agent_guides.performance": include_performance,
        "agent_guides.security": include_security,
    })
    
    console.print(f"🔍 [bold cyan]Deep Code Analysis[/bold cyan]")
    console.print(f"🎯 Target: {target}")
    console.print(f"📊 Depth: {analysis_depth}")
    console.print(f"⚡ Performance: {'✅' if include_performance else '❌'}")
    console.print(f"🔒 Security: {'✅' if include_security else '❌'}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Analyzing code...", total=1)
            
            # Execute analysis
            analysis_result = analyze_code_deep(
                target=target,
                depth=analysis_depth,
                include_performance=include_performance,
                include_security=include_security
            )
            progress.advance(task)
        
        # Display results
        if output_format == "json":
            console.print(json.dumps(analysis_result, indent=2))
        elif output_format == "markdown":
            _display_analysis_markdown(analysis_result)
        else:
            _display_analysis_table(analysis_result)
        
        add_span_event("agent_guides.analyze.completed", {
            "target": target,
            "depth": analysis_depth,
            "issues_found": len(analysis_result.get("issues", [])),
            "recommendations": len(analysis_result.get("recommendations", [])),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Code analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
@instrument_command("agent_guides_create", track_args=True)
def create_guide(
    name: str = typer.Argument(..., help="Guide name"),
    template: str = typer.Option(
        "custom",
        "--template",
        "-t",
        help="Guide template: custom, command, workflow, analysis"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Guide description"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive guide creation"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory"
    ),
):
    """
    Create custom agent guides and commands.
    
    This command creates custom agent guides using DSPy for intelligent
    content generation and Lean Six Sigma principles for systematic design.
    
    Examples:
        uvmgr agent-guides create my-guide --template custom
        uvmgr agent-guides create ml-pipeline --template workflow --interactive
        uvmgr agent-guides create code-review --template analysis
    """
    add_span_attributes(**{
        "agent_guides.operation": "create",
        "agent_guides.name": name,
        "agent_guides.template": template,
        "agent_guides.interactive": interactive,
    })
    
    console.print(f"📝 [bold cyan]Creating Agent Guide[/bold cyan]")
    console.print(f"📋 Name: {name}")
    console.print(f"📄 Template: {template}")
    console.print(f"💬 Interactive: {'✅' if interactive else '❌'}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Creating guide...", total=1)
            
            # Create guide
            guide_result = create_custom_guide(
                name=name,
                template=template,
                description=description,
                interactive=interactive,
                output_dir=output_dir
            )
            progress.advance(task)
        
        # Display results
        _display_guide_creation_result(guide_result)
        
        add_span_event("agent_guides.created", {
            "guide_name": name,
            "template": template,
            "output_path": str(guide_result["output_path"]),
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Guide creation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("workflow")
@instrument_command("agent_guides_workflow", track_args=True)
def execute_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    parameters: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="Workflow parameters (JSON string)"
    ),
    iterations: int = typer.Option(
        1,
        "--iterations",
        "-i",
        help="Number of workflow iterations"
    ),
    anti_repetition: bool = typer.Option(
        True,
        "--anti-repetition/--no-anti-repetition",
        help="Enable anti-repetition mechanisms"
    ),
    save_progress: bool = typer.Option(
        True,
        "--save-progress/--no-save-progress",
        help="Save workflow progress"
    ),
):
    """
    Execute anti-repetition workflows.
    
    This command executes progressive knowledge building workflows using DSPy
    for intelligent adaptation and Lean Six Sigma principles for continuous improvement.
    
    Examples:
        uvmgr agent-guides workflow knowledge-building --iterations 5
        uvmgr agent-guides workflow code-review --params '{"strict": true}'
        uvmgr agent-guides workflow problem-solving --anti-repetition
    """
    add_span_attributes(**{
        "agent_guides.operation": "workflow",
        "agent_guides.workflow": workflow_name,
        "agent_guides.iterations": iterations,
        "agent_guides.anti_repetition": anti_repetition,
    })
    
    console.print(f"🔄 [bold cyan]Executing Anti-Repetition Workflow[/bold cyan]")
    console.print(f"📋 Workflow: {workflow_name}")
    console.print(f"🔄 Iterations: {iterations}")
    console.print(f"🚫 Anti-repetition: {'✅' if anti_repetition else '❌'}")
    
    # Parse parameters
    workflow_params = {}
    if parameters:
        try:
            workflow_params = json.loads(parameters)
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
            
            task = progress.add_task("Executing workflow...", total=iterations)
            
            # Execute workflow
            workflow_result = execute_anti_repetition_workflow(
                workflow_name=workflow_name,
                parameters=workflow_params,
                iterations=iterations,
                anti_repetition=anti_repetition,
                save_progress=save_progress,
                progress_callback=lambda i: progress.advance(task, advance=1)
            )
        
        # Display results
        _display_workflow_results(workflow_result)
        
        add_span_event("agent_guides.workflow.completed", {
            "workflow": workflow_name,
            "iterations_completed": iterations,
            "anti_repetition_used": anti_repetition,
            "progress_saved": save_progress,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
@instrument_command("agent_guides_status", track_args=True)
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
    Show guide status and metrics.
    
    This command displays the current status of agent guides, including
    installation status, usage metrics, and performance indicators.
    
    Examples:
        uvmgr agent-guides status
        uvmgr agent-guides status --detailed --no-metrics
    """
    add_span_attributes(**{
        "agent_guides.operation": "status",
        "agent_guides.detailed": detailed,
        "agent_guides.include_metrics": include_metrics,
    })
    
    console.print("📊 [bold cyan]Agent Guides Status[/bold cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Gathering status information...", total=1)
            
            # Get status
            status_info = get_guide_status(detailed=detailed, include_metrics=include_metrics)
            progress.advance(task)
        
        # Display status
        _display_status_table(status_info, detailed, include_metrics)
        
        add_span_event("agent_guides.status.displayed", {
            "guides_count": status_info.get("guides_count", 0),
            "detailed": detailed,
            "metrics_included": include_metrics,
        })
        
    except Exception as e:
        record_exception(e)
        console.print(f"[red]❌ Status retrieval failed: {e}[/red]")
        raise typer.Exit(1)


def _display_installation_summary(guides_info: Dict[str, Any]):
    """Display installation summary."""
    console.print("\n✅ [bold green]Installation Complete[/bold green]")
    
    table = Table(title="Installation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Guides Installed", str(guides_info["guides_count"]))
    table.add_row("Installation Path", str(guides_info["guides_path"]))
    table.add_row("Source Repository", guides_info["source"])
    table.add_row("Installation Time", f"{guides_info['duration']:.2f}s")
    
    console.print(table)
    
    if guides_info.get("guides"):
        console.print("\n📚 [bold]Installed Guides:[/bold]")
        for guide in guides_info["guides"][:5]:  # Show first 5
            console.print(f"  • {guide}")
        if len(guides_info["guides"]) > 5:
            console.print(f"  ... and {len(guides_info['guides']) - 5} more")


def _display_search_table(search_results: Dict[str, Any]):
    """Display search results as table."""
    console.print("\n🔍 [bold]Search Results[/bold]")
    
    if not search_results.get("results"):
        console.print("No results found.")
        return
    
    table = Table(title="Search Results")
    table.add_column("Source", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Relevance", style="green")
    table.add_column("Snippet", style="yellow")
    
    for result in search_results["results"]:
        table.add_row(
            result.get("source", "Unknown"),
            result.get("title", "No title")[:50],
            f"{result.get('relevance', 0):.2f}",
            result.get("snippet", "")[:100] + "..."
        )
    
    console.print(table)


def _display_search_tree(search_results: Dict[str, Any]):
    """Display search results as tree."""
    console.print("\n🌳 [bold]Search Results Tree[/bold]")
    
    tree = Tree("🔍 Search Results")
    
    for result in search_results.get("results", []):
        source_node = tree.add(f"📚 {result.get('source', 'Unknown')}")
        title_node = source_node.add(f"📄 {result.get('title', 'No title')}")
        title_node.add(f"🎯 Relevance: {result.get('relevance', 0):.2f}")
        title_node.add(f"📝 {result.get('snippet', '')[:100]}...")
    
    console.print(tree)


def _display_multi_mind_results(analysis_result: Dict[str, Any]):
    """Display multi-mind analysis results."""
    console.print("\n🧠 [bold]Multi-Mind Analysis Results[/bold]")
    
    # Summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Topic", analysis_result.get("topic", "Unknown"))
    table.add_row("Rounds Completed", str(analysis_result.get("rounds_completed", 0)))
    table.add_row("Experts Used", str(len(analysis_result.get("experts", []))))
    table.add_row("Consensus Reached", "✅ Yes" if analysis_result.get("consensus") else "❌ No")
    table.add_row("Duration", f"{analysis_result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    # Expert insights
    if analysis_result.get("expert_insights"):
        console.print("\n👥 [bold]Expert Insights:[/bold]")
        for expert, insights in analysis_result["expert_insights"].items():
            console.print(f"\n🔬 {expert}:")
            for insight in insights[:3]:  # Show first 3 insights
                console.print(f"  • {insight}")
    
    # Consensus
    if analysis_result.get("consensus"):
        console.print(f"\n✅ [bold green]Consensus:[/bold green]")
        console.print(analysis_result["consensus"])
    
    # Recommendations
    if analysis_result.get("recommendations"):
        console.print(f"\n💡 [bold]Recommendations:[/bold]")
        for i, rec in enumerate(analysis_result["recommendations"], 1):
            console.print(f"  {i}. {rec}")


def _display_analysis_table(analysis_result: Dict[str, Any]):
    """Display code analysis results as table."""
    console.print("\n🔍 [bold]Code Analysis Results[/bold]")
    
    # Summary
    summary_table = Table(title="Analysis Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Target", analysis_result.get("target", "Unknown"))
    summary_table.add_row("Complexity", str(analysis_result.get("complexity", "Unknown")))
    summary_table.add_row("Issues Found", str(len(analysis_result.get("issues", []))))
    summary_table.add_row("Recommendations", str(len(analysis_result.get("recommendations", []))))
    summary_table.add_row("Performance Score", f"{analysis_result.get('performance_score', 0):.1f}/10")
    
    console.print(summary_table)
    
    # Issues
    if analysis_result.get("issues"):
        console.print("\n⚠️ [bold]Issues Found:[/bold]")
        issues_table = Table()
        issues_table.add_column("Severity", style="red")
        issues_table.add_column("Issue", style="white")
        issues_table.add_column("Location", style="cyan")
        
        for issue in analysis_result["issues"]:
            issues_table.add_row(
                issue.get("severity", "Unknown"),
                issue.get("description", "No description"),
                issue.get("location", "Unknown")
            )
        
        console.print(issues_table)
    
    # Recommendations
    if analysis_result.get("recommendations"):
        console.print("\n💡 [bold]Recommendations:[/bold]")
        for i, rec in enumerate(analysis_result["recommendations"], 1):
            console.print(f"  {i}. {rec}")


def _display_analysis_markdown(analysis_result: Dict[str, Any]):
    """Display code analysis results as markdown."""
    console.print("\n# Code Analysis Report")
    console.print(f"\n**Target:** {analysis_result.get('target', 'Unknown')}")
    console.print(f"**Complexity:** {analysis_result.get('complexity', 'Unknown')}")
    console.print(f"**Performance Score:** {analysis_result.get('performance_score', 0):.1f}/10")
    
    if analysis_result.get("issues"):
        console.print("\n## Issues Found")
        for issue in analysis_result["issues"]:
            console.print(f"- **{issue.get('severity', 'Unknown')}:** {issue.get('description', 'No description')}")
    
    if analysis_result.get("recommendations"):
        console.print("\n## Recommendations")
        for rec in analysis_result["recommendations"]:
            console.print(f"- {rec}")


def _display_guide_creation_result(guide_result: Dict[str, Any]):
    """Display guide creation result."""
    console.print("\n✅ [bold green]Guide Created Successfully[/bold green]")
    
    table = Table(title="Creation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Guide Name", guide_result.get("name", "Unknown"))
    table.add_row("Template Used", guide_result.get("template", "Unknown"))
    table.add_row("Output Path", str(guide_result.get("output_path", "Unknown")))
    table.add_row("File Size", f"{guide_result.get('file_size', 0)} bytes")
    table.add_row("Creation Time", f"{guide_result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    console.print(f"\n📝 [bold]Next Steps:[/bold]")
    console.print(f"  1. Review the guide: {guide_result.get('output_path')}")
    console.print(f"  2. Customize as needed")
    console.print(f"  3. Install with: uvmgr agent-guides install --source local")


def _display_workflow_results(workflow_result: Dict[str, Any]):
    """Display workflow execution results."""
    console.print("\n🔄 [bold]Workflow Execution Results[/bold]")
    
    # Summary table
    table = Table(title="Workflow Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Workflow", workflow_result.get("workflow_name", "Unknown"))
    table.add_row("Iterations Completed", str(workflow_result.get("iterations_completed", 0)))
    table.add_row("Success Rate", f"{workflow_result.get('success_rate', 0):.1%}")
    table.add_row("Total Duration", f"{workflow_result.get('total_duration', 0):.2f}s")
    table.add_row("Anti-Repetition Used", "✅ Yes" if workflow_result.get("anti_repetition") else "❌ No")
    
    console.print(table)
    
    # Iteration results
    if workflow_result.get("iteration_results"):
        console.print("\n📊 [bold]Iteration Results:[/bold]")
        for i, result in enumerate(workflow_result["iteration_results"], 1):
            status = "✅ Success" if result.get("success") else "❌ Failed"
            console.print(f"  Iteration {i}: {status} ({result.get('duration', 0):.2f}s)")
    
    # Key insights
    if workflow_result.get("key_insights"):
        console.print("\n💡 [bold]Key Insights:[/bold]")
        for insight in workflow_result["key_insights"]:
            console.print(f"  • {insight}")


def _display_status_table(status_info: Dict[str, Any], detailed: bool, include_metrics: bool):
    """Display status information."""
    console.print("\n📊 [bold]Agent Guides Status[/bold cyan]")
    
    # Basic status
    basic_table = Table(title="Basic Status")
    basic_table.add_column("Metric", style="cyan")
    basic_table.add_column("Value", style="green")
    
    basic_table.add_row("Guides Installed", str(status_info.get("guides_count", 0)))
    basic_table.add_row("Installation Path", str(status_info.get("installation_path", "Unknown")))
    basic_table.add_row("Last Updated", status_info.get("last_updated", "Unknown"))
    basic_table.add_row("Status", "✅ Active" if status_info.get("active") else "❌ Inactive")
    
    console.print(basic_table)
    
    # Detailed information
    if detailed:
        if status_info.get("guides"):
            console.print("\n📚 [bold]Installed Guides:[/bold]")
            guides_table = Table()
            guides_table.add_column("Guide", style="cyan")
            guides_table.add_column("Type", style="white")
            guides_table.add_column("Size", style="green")
            guides_table.add_column("Last Used", style="yellow")
            
            for guide in status_info["guides"]:
                guides_table.add_row(
                    guide.get("name", "Unknown"),
                    guide.get("type", "Unknown"),
                    f"{guide.get('size', 0)} bytes",
                    guide.get("last_used", "Never")
                )
            
            console.print(guides_table)
    
    # Metrics
    if include_metrics and status_info.get("metrics"):
        console.print("\n📈 [bold]Performance Metrics:[/bold]")
        metrics_table = Table()
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        for key, value in status_info["metrics"].items():
            if isinstance(value, float):
                metrics_table.add_column(key, f"{value:.2f}")
            else:
                metrics_table.add_column(key, str(value))
        
        console.print(metrics_table) 