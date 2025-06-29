"""
uvmgr.commands.knowledge
=======================

AI-powered knowledge management and code understanding commands.

This command module addresses the critical AI integration gap by providing:

• **Code analysis**: Semantic analysis of project structure and patterns
• **Knowledge base**: Persistent learning and retrieval using AI
• **Semantic search**: Find relevant code, docs, and patterns quickly
• **AI context**: Project-aware assistance and suggestions
• **Learning integration**: Continuous learning from codebase changes

Example
-------
    $ uvmgr knowledge analyze
    $ uvmgr knowledge search "authentication function"
    $ uvmgr knowledge insights
    $ uvmgr knowledge context --scope project

See Also
--------
- :mod:`uvmgr.core.knowledge` : Knowledge management implementation
- :mod:`uvmgr.core.agi_reasoning` : AGI reasoning integration
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, AIAttributes, ProjectAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.knowledge import (
    get_knowledge_base,
    analyze_project_knowledge,
    search_codebase,
    get_ai_context,
    KNOWLEDGE_AVAILABLE
)

app = typer.Typer(help="AI-powered knowledge management and code understanding")


@app.command("analyze")
@instrument_command("knowledge_analyze", track_args=True)
def analyze_project(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-analysis even if cache exists"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed analysis results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Analyze project structure and build AI knowledge base."""
    
    if not KNOWLEDGE_AVAILABLE:
        typer.echo("❌ Knowledge management requires ChromaDB and sentence-transformers")
        typer.echo("Install with: pip install 'uvmgr[knowledge]' or 'uvmgr[all]'")
        raise typer.Exit(1)
    
    typer.echo("🧠 Analyzing project for AI knowledge base...")
    if force:
        typer.echo("🔄 Force re-analysis enabled")
    
    # Perform analysis
    knowledge = analyze_project_knowledge(force_reanalysis=force)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "knowledge_analyze",
        ProjectAttributes.NAME: knowledge.project_name,
        AIAttributes.OPERATION: "analyze",
        "total_files": str(knowledge.total_files),
        "classes_count": str(len(knowledge.classes)),
        "functions_count": str(len(knowledge.functions))
    })
    
    if json_output:
        # Convert knowledge to dict for JSON output
        knowledge_dict = {
            "project_name": knowledge.project_name,
            "project_type": knowledge.project_type,
            "total_files": knowledge.total_files,
            "total_lines": knowledge.total_lines,
            "languages": knowledge.languages,
            "classes_count": len(knowledge.classes),
            "functions_count": len(knowledge.functions),
            "architectural_patterns": knowledge.architectural_patterns,
            "common_imports": knowledge.common_imports,
            "complexity_hotspots": knowledge.complexity_hotspots,
            "ai_suggestions": knowledge.ai_suggestions,
            "learning_insights": knowledge.learning_insights,
            "last_analyzed": knowledge.last_analyzed
        }
        dump_json(knowledge_dict)
        return
    
    # Display analysis results
    typer.echo(f"\n✅ Analysis complete for: {colour(knowledge.project_name, 'green')}")
    typer.echo(f"📊 Project type: {knowledge.project_type}")
    typer.echo(f"📁 Files analyzed: {knowledge.total_files}")
    typer.echo(f"📄 Total lines: {knowledge.total_lines:,}")
    
    # Code elements
    typer.echo(f"\n🏗️  Code Structure:")
    typer.echo(f"   📦 Classes: {len(knowledge.classes)}")
    typer.echo(f"   🔧 Functions: {len(knowledge.functions)}")
    typer.echo(f"   📋 Modules: {len(knowledge.modules)}")
    
    # Architectural patterns
    if knowledge.architectural_patterns:
        typer.echo(f"\n🏛️  Architectural Patterns:")
        for pattern in knowledge.architectural_patterns:
            typer.echo(f"   ✓ {pattern}")
    
    # Common imports
    if knowledge.common_imports and detailed:
        typer.echo(f"\n📦 Most Common Imports:")
        for lib, count in list(knowledge.common_imports.items())[:5]:
            typer.echo(f"   📚 {lib}: {count} files")
    
    # Complexity hotspots
    if knowledge.complexity_hotspots:
        typer.echo(f"\n🔥 Complexity Hotspots:")
        for hotspot in knowledge.complexity_hotspots[:3]:
            typer.echo(f"   ⚠️  {hotspot}")
    
    # AI suggestions
    if knowledge.ai_suggestions:
        typer.echo(f"\n🤖 AI Suggestions:")
        for suggestion in knowledge.ai_suggestions[:3]:
            typer.echo(f"   💡 {suggestion}")
    
    # Learning insights
    if knowledge.learning_insights:
        typer.echo(f"\n🧠 Learning Insights:")
        for insight in knowledge.learning_insights:
            typer.echo(f"   🎯 {insight}")
    
    add_span_event("knowledge.analysis_completed", {
        "project_name": knowledge.project_name,
        "elements_analyzed": len(knowledge.classes) + len(knowledge.functions)
    })


@app.command("search")
@instrument_command("knowledge_search", track_args=True)
def semantic_search(
    query: str = typer.Argument(..., help="Search query for semantic code search"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum number of results"),
    show_code: bool = typer.Option(False, "--code", "-c", help="Show code snippets in results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Perform semantic search across the codebase."""
    
    if not KNOWLEDGE_AVAILABLE:
        typer.echo("❌ Semantic search requires ChromaDB and sentence-transformers")
        typer.echo("Install with: pip install 'uvmgr[knowledge]' or 'uvmgr[all]'")
        raise typer.Exit(1)
    
    typer.echo(f"🔍 Searching codebase for: {colour(query, 'cyan')}")
    
    # Perform search
    results = search_codebase(query, limit)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "knowledge_search",
        AIAttributes.OPERATION: "search",
        "query": query,
        "results_count": str(len(results)),
        "limit": str(limit)
    })
    
    if json_output:
        dump_json(results)
        return
    
    if not results:
        typer.echo("📭 No results found")
        typer.echo("💡 Try different keywords or run 'uvmgr knowledge analyze' first")
        return
    
    typer.echo(f"\n📋 Found {len(results)} results:")
    
    for i, result in enumerate(results, 1):
        relevance = result["relevance_score"]
        relevance_color = "green" if relevance > 0.8 else "yellow" if relevance > 0.6 else "white"
        
        typer.echo(f"\n{i}. {colour(result['name'], 'green')} ({result['element_type']})")
        typer.echo(f"   📁 {result['file_path']}")
        typer.echo(f"   🎯 Relevance: {colour(f'{relevance:.2f}', relevance_color)}")
        
        if show_code and result['content']:
            # Show first few lines of content
            content_lines = result['content'].split('\n')[:3]
            typer.echo(f"   📄 Preview:")
            for line in content_lines:
                if line.strip():
                    typer.echo(f"      {line[:80]}{'...' if len(line) > 80 else ''}")
    
    add_span_event("knowledge.search_completed", {
        "query": query,
        "results_found": len(results)
    })


@app.command("insights")
@instrument_command("knowledge_insights", track_args=True)
def show_insights(
    scope: str = typer.Option("project", "--scope", "-s", help="Scope of insights (project, ai, patterns)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show AI-generated insights about the codebase."""
    
    knowledge_base = get_knowledge_base()
    
    # Get different types of insights based on scope
    if scope == "project":
        insights = _get_project_insights(knowledge_base)
    elif scope == "ai":
        insights = _get_ai_insights(knowledge_base)
    elif scope == "patterns":
        insights = _get_pattern_insights(knowledge_base)
    else:
        typer.echo(f"❌ Unknown scope: {scope}")
        typer.echo("Available scopes: project, ai, patterns")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "knowledge_insights",
        AIAttributes.OPERATION: "insights",
        "scope": scope,
        "insights_count": str(len(insights))
    })
    
    if json_output:
        dump_json(insights)
        return
    
    typer.echo(f"🧠 {scope.title()} Insights:")
    
    if not insights:
        typer.echo("📭 No insights available")
        typer.echo("💡 Run 'uvmgr knowledge analyze' to generate insights")
        return
    
    for category, items in insights.items():
        if items:
            typer.echo(f"\n{_get_category_icon(category)} {category.replace('_', ' ').title()}:")
            for item in items:
                typer.echo(f"   • {item}")


@app.command("context")
@instrument_command("knowledge_context", track_args=True)
def show_context(
    scope: str = typer.Option("current_file", "--scope", "-s", help="Context scope"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show AI context for intelligent assistance."""
    
    context = get_ai_context(scope)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "knowledge_context",
        AIAttributes.OPERATION: "context",
        "scope": scope
    })
    
    if json_output:
        dump_json(context)
        return
    
    typer.echo(f"🎯 AI Context ({scope}):")
    
    # Project overview
    if "project_overview" in context:
        overview = context["project_overview"]
        typer.echo(f"\n📊 Project Overview:")
        typer.echo(f"   📦 Name: {overview['name']}")
        typer.echo(f"   🏷️  Type: {overview['type']}")
        typer.echo(f"   📁 Files: {overview['total_files']}")
        typer.echo(f"   📄 Lines: {overview['total_lines']:,}")
    
    # Architectural patterns
    if context.get("architectural_patterns"):
        typer.echo(f"\n🏛️  Architecture:")
        for pattern in context["architectural_patterns"]:
            typer.echo(f"   ✓ {pattern}")
    
    # Common imports
    if context.get("common_imports"):
        typer.echo(f"\n📦 Key Dependencies:")
        for lib, count in list(context["common_imports"].items())[:5]:
            typer.echo(f"   📚 {lib} ({count} uses)")
    
    # Complexity hotspots
    if context.get("complexity_hotspots"):
        typer.echo(f"\n🔥 Attention Areas:")
        for hotspot in context["complexity_hotspots"]:
            typer.echo(f"   ⚠️  {hotspot}")
    
    # AI suggestions
    if context.get("ai_suggestions"):
        typer.echo(f"\n🤖 Suggestions:")
        for suggestion in context["ai_suggestions"]:
            typer.echo(f"   💡 {suggestion}")


@app.command("stats")
@instrument_command("knowledge_stats", track_args=True)
def show_stats(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show knowledge base statistics and health."""
    
    knowledge_base = get_knowledge_base()
    
    # Get project knowledge if available
    knowledge_file = knowledge_base.knowledge_dir / "project_knowledge.json"
    has_knowledge = knowledge_file.exists()
    
    stats = {
        "knowledge_available": KNOWLEDGE_AVAILABLE,
        "knowledge_base_initialized": has_knowledge,
        "workspace_root": str(knowledge_base.workspace_root),
        "knowledge_directory": str(knowledge_base.knowledge_dir),
        "chroma_available": knowledge_base.client is not None,
        "embeddings_model_available": knowledge_base.embeddings_model is not None
    }
    
    if has_knowledge:
        knowledge = knowledge_base.analyze_project()
        stats.update({
            "project_name": knowledge.project_name,
            "total_files_analyzed": knowledge.total_files,
            "total_code_lines": knowledge.total_lines,
            "classes_indexed": len(knowledge.classes),
            "functions_indexed": len(knowledge.functions),
            "last_analysis": knowledge.last_analyzed,
            "patterns_detected": len(knowledge.architectural_patterns),
            "ai_suggestions_count": len(knowledge.ai_suggestions)
        })
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "knowledge_stats",
        "knowledge_available": str(KNOWLEDGE_AVAILABLE),
        "has_project_knowledge": str(has_knowledge)
    })
    
    if json_output:
        dump_json(stats)
        return
    
    typer.echo("📊 Knowledge Base Statistics:")
    
    # System status
    typer.echo(f"\n🔧 System Status:")
    status_icon = "✅" if KNOWLEDGE_AVAILABLE else "❌"
    typer.echo(f"   {status_icon} AI Knowledge: {KNOWLEDGE_AVAILABLE}")
    
    if KNOWLEDGE_AVAILABLE:
        chroma_icon = "✅" if stats["chroma_available"] else "❌"
        typer.echo(f"   {chroma_icon} ChromaDB: {stats['chroma_available']}")
        
        embeddings_icon = "✅" if stats["embeddings_model_available"] else "❌"
        typer.echo(f"   {embeddings_icon} Embeddings: {stats['embeddings_model_available']}")
    
    # Project knowledge
    knowledge_icon = "✅" if has_knowledge else "❌"
    typer.echo(f"   {knowledge_icon} Project Analysis: {has_knowledge}")
    
    if has_knowledge:
        typer.echo(f"\n📊 Project Knowledge:")
        typer.echo(f"   📦 Project: {stats['project_name']}")
        typer.echo(f"   📁 Files: {stats['total_files_analyzed']}")
        typer.echo(f"   📄 Lines: {stats['total_code_lines']:,}")
        typer.echo(f"   🏗️  Classes: {stats['classes_indexed']}")
        typer.echo(f"   🔧 Functions: {stats['functions_indexed']}")
        typer.echo(f"   🏛️  Patterns: {stats['patterns_detected']}")
        typer.echo(f"   🤖 AI Suggestions: {stats['ai_suggestions_count']}")
    
    # Directories
    typer.echo(f"\n📁 Paths:")
    typer.echo(f"   🏠 Workspace: {stats['workspace_root']}")
    typer.echo(f"   🧠 Knowledge: {stats['knowledge_directory']}")


def _get_project_insights(knowledge_base) -> Dict[str, List[str]]:
    """Get project-level insights."""
    
    if not knowledge_base.project_knowledge:
        knowledge_base.analyze_project()
    
    knowledge = knowledge_base.project_knowledge
    
    return {
        "code_quality": knowledge.ai_suggestions,
        "architecture": knowledge.architectural_patterns,
        "complexity": knowledge.complexity_hotspots,
        "learning": knowledge.learning_insights
    }


def _get_ai_insights(knowledge_base) -> Dict[str, List[str]]:
    """Get AI-specific insights."""
    
    from uvmgr.core.agi_reasoning import get_agi_insights
    
    agi_insights = get_agi_insights()
    
    return {
        "understanding": [f"Confidence: {agi_insights['understanding_confidence']:.2f}"],
        "patterns": [f"Cross-domain patterns: {agi_insights['cross_domain_patterns']}"],
        "causality": [f"Causal patterns: {agi_insights['causal_patterns_discovered']}"],
        "improvements": agi_insights.get("improvement_suggestions", []),
        "meta_learning": agi_insights.get("meta_learning_insights", [])
    }


def _get_pattern_insights(knowledge_base) -> Dict[str, List[str]]:
    """Get pattern-specific insights."""
    
    if not knowledge_base.project_knowledge:
        knowledge_base.analyze_project()
    
    knowledge = knowledge_base.project_knowledge
    
    # Analyze patterns in more detail
    patterns = {
        "architectural": knowledge.architectural_patterns,
        "naming_conventions": [],
        "code_organization": [],
        "dependencies": []
    }
    
    # Add naming pattern analysis
    class_names = [c.name for c in knowledge.classes]
    if any(name.endswith("Manager") for name in class_names):
        patterns["naming_conventions"].append("Manager pattern detected")
    if any(name.endswith("Service") for name in class_names):
        patterns["naming_conventions"].append("Service pattern detected")
    if any(name.endswith("Handler") for name in class_names):
        patterns["naming_conventions"].append("Handler pattern detected")
    
    # Add dependency insights
    top_imports = list(knowledge.common_imports.keys())[:3]
    patterns["dependencies"] = [f"Heavy usage: {lib}" for lib in top_imports]
    
    return patterns


def _get_category_icon(category: str) -> str:
    """Get emoji icon for insight category."""
    
    icons = {
        "code_quality": "🔍",
        "architecture": "🏛️",
        "complexity": "🔥",
        "learning": "🧠",
        "understanding": "🎯",
        "patterns": "🔍",
        "causality": "⚡",
        "improvements": "💡",
        "meta_learning": "🧠",
        "architectural": "🏛️",
        "naming_conventions": "🏷️",
        "code_organization": "📁",
        "dependencies": "📦"
    }
    
    return icons.get(category, "•")