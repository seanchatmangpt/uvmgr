"""
uvmgr.commands.claude - Claude AI Integration Commands
=====================================================

Advanced Claude AI integration with multi-agent workflows, conversation search,
and intelligent code analysis capabilities inspired by agent-guides.

This module provides sophisticated AI-driven development tools including
collaborative multi-specialist analysis, conversation history search,
code review workflows, and custom Claude commands.

Key Features
-----------
• **Multi-Mind Analysis**: Collaborative multi-specialist research
• **Conversation Search**: Search and resume Claude conversations
• **Code Analysis**: Deep code review and optimization
• **Custom Commands**: Project-specific Claude commands
• **Agent Workflows**: Coordinated AI agent patterns
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
Multi-Agent Commands
- **multi-mind**: Launch collaborative multi-specialist analysis
- **analyze**: Deep code analysis with configurable experts
- **review**: Comprehensive code review (security, performance, docs)
- **optimize**: Performance optimization analysis

Conversation Management
- **search**: Search conversation history across multiple sources
- **resume**: Resume a specific conversation session
- **history**: View recent conversation sessions
- **export**: Export conversation for analysis

Custom Commands
- **create**: Create new custom Claude commands
- **list**: List available custom commands
- **run**: Execute custom Claude commands
- **sync**: Sync commands between projects

Workflow Commands
- **workflow**: Execute predefined AI workflows
- **pipeline**: Run multi-stage AI pipelines
- **debate**: Expert debate on architecture decisions

Examples
--------
    >>> # Multi-specialist analysis
    >>> uvmgr claude multi-mind "microservices vs monolith" --rounds 4
    >>> 
    >>> # Search conversation history
    >>> uvmgr claude search "OTEL implementation"
    >>> 
    >>> # Deep code analysis
    >>> uvmgr claude analyze src/core/telemetry.py --focus performance
    >>> 
    >>> # Create custom command
    >>> uvmgr claude create security-audit --template review

See Also
--------
- :mod:`uvmgr.ops.claude` : Claude operations
- :mod:`uvmgr.runtime.ai` : AI runtime integration
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import AIAttributes, CliAttributes
from uvmgr.core.shell import colour
from uvmgr.ops import claude as claude_ops
from uvmgr.ops import ai as ai_ops

app = typer.Typer(help="Advanced Claude AI integration and workflows")
console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Multi-Agent Commands
# ──────────────────────────────────────────────────────────────────────────────

@app.command("multi-mind")
@instrument_command("claude_multi_mind", track_args=True)
def multi_mind(
    topic: str = typer.Argument(..., help="Topic for collaborative analysis"),
    rounds: int = typer.Option(
        3,
        "--rounds",
        "-r",
        min=1,
        max=10,
        help="Number of analysis rounds"
    ),
    specialists: Optional[str] = typer.Option(
        None,
        "--specialists",
        "-s",
        help="Comma-separated specialist roles (auto-assigned if not provided)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save analysis to file"
    ),
    web_search: bool = typer.Option(
        True,
        "--web-search/--no-web-search",
        help="Enable web search for research"
    ),
):
    """
    Execute collaborative multi-specialist analysis.
    
    Launches 4-6 independent AI specialists to research a topic from
    diverse perspectives, cross-pollinating insights across multiple
    rounds to generate comprehensive analysis.
    
    Examples:
        uvmgr claude multi-mind "quantum computing applications"
        uvmgr claude multi-mind "AI safety" --rounds 5 --specialists "ethicist,engineer,philosopher"
    """
    add_span_attributes(**{
        AIAttributes.OPERATION: "multi_mind",
        "ai.topic": topic,
        "ai.rounds": rounds,
        "ai.web_search": web_search,
    })
    
    console.print(f"🧠 Launching Multi-Mind Analysis: [bold cyan]{topic}[/bold cyan]")
    console.print(f"📊 Configuration: {rounds} rounds, web search: {web_search}")
    
    # Parse specialists if provided
    specialist_list = None
    if specialists:
        specialist_list = [s.strip() for s in specialists.split(",")]
        console.print(f"👥 Custom specialists: {', '.join(specialist_list)}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing multi-mind analysis...", total=rounds)
        
        try:
            # Execute multi-mind analysis
            results = claude_ops.multi_mind_analysis(
                topic=topic,
                rounds=rounds,
                specialists=specialist_list,
                enable_web_search=web_search,
                progress_callback=None  # Remove callback to avoid Callable type issue
            )
            
            progress.update(task, completed=rounds)
            
            # Display results
            _display_multi_mind_results(results)
            
            # Save if requested
            if output:
                _save_analysis(results, output)
                console.print(f"💾 Analysis saved to: {output}")
            
            add_span_event("multi_mind_completed", {
                "topic": topic,
                "rounds": rounds,
                "specialists": len(results.get("specialists", [])),
                "insights": len(results.get("insights", [])),
            })
            
        except Exception as e:
            add_span_event("multi_mind_failed", {"error": str(e)})
            console.print(f"[red]❌ Multi-mind analysis failed: {e}[/red]")
            raise typer.Exit(1)


@app.command("analyze")
@instrument_command("claude_analyze", track_args=True)
def analyze(
    project_path: Path = typer.Argument(..., help="External project path to analyze"),
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Specific file to analyze"),
    function: Optional[str] = typer.Option(None, "--function", help="Specific function to analyze"),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        help="Analysis focus: performance, security, architecture, all"
    ),
    depth: int = typer.Option(
        3,
        "--depth",
        "-d",
        min=1,
        max=5,
        help="Analysis depth (1-5)"
    ),
    save_session: bool = typer.Option(
        False,
        "--save-session",
        "-s",
        help="Save analysis session for this project"
    ),
):
    """
    Analyze code in external projects with Claude AI.
    
    This command performs deep code analysis on external projects, providing
    insights into function implementations, architecture patterns, and potential
    improvements. Designed specifically for working with codebases outside
    of the current uvmgr project.
    
    Examples:
        uvmgr claude analyze /path/to/project
        uvmgr claude analyze /path/to/project --file src/main.py --depth 5
        uvmgr claude analyze /path/to/project --function process_data --save-session
    """
    if not project_path.exists():
        console.print(f"[red]❌ Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    if not project_path.is_dir():
        console.print(f"[red]❌ Path must be a directory: {project_path}[/red]")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        AIAttributes.OPERATION: "external_project_analysis",
        "ai.project_path": str(project_path),
        "ai.file_path": file_path,
        "ai.function": function,
        "ai.focus": focus or "all",
        "ai.depth": depth,
    })
    
    console.print(f"🔍 Analyzing external project: [bold]{project_path.name}[/bold]")
    console.print(f"📁 Project: {project_path}")
    if file_path:
        console.print(f"📄 File: {file_path}")
    if function:
        console.print(f"🔧 Function: {function}")
    console.print(f"📋 Focus: {focus or 'comprehensive'}, Depth: {depth}/5")
    
    try:
        results = claude_ops.analyze_project(
            project_path=project_path,
            function_name=function,
            file_path=file_path,
            depth=depth
        )
        
        if results.success:
            console.print("\n[green]✅ Analysis Complete![/green]")
            console.print(Panel(
                results.analysis,
                title="Project Analysis Results",
                border_style="green"
            ))
            
            if results.suggestions:
                console.print("\n[bold cyan]💡 Recommendations:[/bold cyan]")
                for i, suggestion in enumerate(results.suggestions, 1):
                    console.print(f"  {i}. {suggestion}")
            
            # Save session if requested
            if save_session:
                session_result = claude_ops.save_session(project_path, "analysis_session")
                if session_result.success:
                    console.print(f"\n💾 Session saved: {session_result.session_id}")
        else:
            console.print(f"[red]❌ Analysis failed: {results.error}[/red]")
            raise typer.Exit(1)
        
        add_span_event("external_project_analysis_completed", {
            "project": str(project_path),
            "suggestions_count": len(results.suggestions),
            "session_saved": save_session,
        })
        
    except Exception as e:
        add_span_event("external_project_analysis_failed", {"error": str(e)})
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("search-project")
@instrument_command("claude_search_project", track_args=True)
def search_project(
    project_path: Path = typer.Argument(..., help="External project path to search"),
    query: str = typer.Option(..., "--query", "-q", help="Search query (natural language)"),
    context_lines: int = typer.Option(3, "--context", "-c", help="Context lines around matches"),
    file_pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="File pattern (e.g., '*.py')"),
    ai_rank: bool = typer.Option(True, "--ai-rank/--no-ai-rank", help="Use AI to rank results"),
    save_session: bool = typer.Option(False, "--save-session", "-s", help="Save search session"),
):
    """
    Search through external project files with AI assistance.
    
    This command searches through project files using Claude AI to understand
    context and provide intelligent search results beyond simple text matching.
    Perfect for exploring unfamiliar codebases.
    
    Examples:
        uvmgr claude search-project /path/to/project --query "authentication logic"
        uvmgr claude search-project /path/to/project -q "database connections" -p "*.py"
        uvmgr claude search-project /path/to/project --query "error handling" --save-session
    """
    if not project_path.exists():
        console.print(f"[red]❌ Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    if not project_path.is_dir():
        console.print(f"[red]❌ Path must be a directory: {project_path}[/red]")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        AIAttributes.OPERATION: "external_project_search",
        "ai.project_path": str(project_path),
        "ai.query": query,
        "ai.context_lines": context_lines,
        "ai.file_pattern": file_pattern,
        "ai.ai_rank": ai_rank,
    })
    
    console.print(f"🔍 Searching external project: [bold]{project_path.name}[/bold]")
    console.print(f"📁 Project: {project_path}")
    console.print(f"🔎 Query: [cyan]'{query}'[/cyan]")
    if file_pattern:
        console.print(f"📄 Pattern: {file_pattern}")
    
    try:
        results = claude_ops.search_project(
            project_path=project_path,
            query=query,
            context_lines=context_lines,
            file_pattern=file_pattern
        )
        
        if not results:
            console.print("\n[yellow]No matches found.[/yellow]")
            console.print("💡 Try adjusting your query or search pattern.")
            return
        
        # Display results in a table
        table = Table(title=f"Search Results for '{query}' in {project_path.name}")
        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("Line", style="magenta")
        table.add_column("Match", style="green")
        table.add_column("Context", style="dim")
        
        for result in results[:20]:  # Limit to 20 results for display
            file_rel = result.file_path.relative_to(project_path) if result.file_path.is_relative_to(project_path) else result.file_path
            match_text = result.matched_text[:60] + "..." if len(result.matched_text) > 60 else result.matched_text
            context_text = result.context[:80] + "..." if len(result.context) > 80 else result.context
            
            table.add_row(
                str(file_rel),
                str(result.line_number),
                match_text,
                context_text
            )
        
        console.print(f"\n[green]Found {len(results)} matches![/green]")
        console.print(table)
        
        if len(results) > 20:
            console.print(f"\n[dim]... and {len(results) - 20} more results[/dim]")
        
        # Save session if requested
        if save_session:
            session_result = claude_ops.save_session(project_path, f"search_{query.replace(' ', '_')}")
            if session_result.success:
                console.print(f"\n💾 Search session saved: {session_result.session_id}")
        
        add_span_event("external_project_search_completed", {
            "project": str(project_path),
            "query": query,
            "results_count": len(results),
            "session_saved": save_session,
        })
        
    except Exception as e:
        add_span_event("external_project_search_failed", {"error": str(e)})
        console.print(f"[red]❌ Search failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("init-project")
@instrument_command("claude_init_project", track_args=True)
def init_project(
    project_path: Path = typer.Argument(..., help="External project path to initialize"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Project profile (python, javascript, rust, etc.)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization even if .claude exists"),
):
    """
    Initialize Claude AI support for an external project.
    
    This command sets up Claude AI integration for an external project,
    creating necessary configuration files and directories to enable
    advanced AI-assisted development workflows.
    
    Examples:
        uvmgr claude init-project /path/to/project
        uvmgr claude init-project /path/to/project --profile python
        uvmgr claude init-project /path/to/project --profile rust --force
    """
    if not project_path.exists():
        console.print(f"[red]❌ Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    if not project_path.is_dir():
        console.print(f"[red]❌ Path must be a directory: {project_path}[/red]")
        raise typer.Exit(1)
    
    # Check if already initialized
    claude_dir = project_path / ".claude"
    if claude_dir.exists() and not force:
        console.print(f"[yellow]⚠️ Project already has Claude integration (.claude directory exists)[/yellow]")
        console.print("Use --force to reinitialize")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        AIAttributes.OPERATION: "initialize_external_project",
        "ai.project_path": str(project_path),
        "ai.profile": profile,
        "ai.force": force,
    })
    
    console.print(f"🚀 Initializing Claude AI for: [bold]{project_path.name}[/bold]")
    console.print(f"📁 Project: {project_path}")
    if profile:
        console.print(f"🏷️ Profile: {profile}")
    
    try:
        result = claude_ops.initialize_project(project_path, profile)
        
        if result.success:
            console.print(f"\n[green]✅ Claude AI initialized successfully![/green]")
            console.print("\n[bold]Created files:[/bold]")
            for file in result.created_files:
                console.print(f"  📄 {file}")
            
            console.print("\n[bold cyan]Next steps:[/bold cyan]")
            console.print("  1. Review .claude/config.yml for project settings")
            console.print("  2. Add custom commands in .claude/commands/")
            console.print("  3. Run analysis: uvmgr claude analyze /path/to/project")
            console.print("  4. Search project: uvmgr claude search-project /path/to/project -q 'your query'")
            
            if profile:
                console.print(f"\n💡 Profile-specific commands were added for {profile} development")
        else:
            console.print(f"[red]❌ Initialization failed: {result.error}[/red]")
            raise typer.Exit(1)
        
        add_span_event("external_project_initialized", {
            "project": str(project_path),
            "profile": profile,
            "files_created": len(result.created_files),
        })
        
    except Exception as e:
        add_span_event("external_project_init_failed", {"error": str(e)})
        console.print(f"[red]❌ Initialization failed: {e}[/red]")
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Conversation Management (80/20 Implementation)
# ──────────────────────────────────────────────────────────────────────────────

import sqlite3

# Core paths for Claude conversation history
CLAUDE_DB = Path.home() / ".claude" / "__store.db"
CLAUDE_JSON = Path.home() / ".claude.json"


@app.command("search")
@instrument_command("claude_search", track_args=True)
def search(
    query: str = typer.Argument(..., help="Search term or phrase"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of results"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="Limit to last N days"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project path"),
):
    """
    Search Claude conversations (80/20 approach).
    
    Quick keyword search across all conversations with smart ranking.
    Searches the actual Claude database and JSON history files.
    """
    add_span_attributes(**{
        AIAttributes.OPERATION: "conversation_search",
        "ai.query": query,
        "ai.days": days or "all",
        "ai.project": project or "all",
    })
    
    if not CLAUDE_DB.exists():
        console.print("[red]Claude database not found. Have you used Claude Code?[/red]")
        raise typer.Exit(1)
    
    # Build SQL query with optional filters
    base_query = """
    SELECT 
        b.session_id,
        b.cwd as project,
        datetime(b.timestamp, 'unixepoch') as date,
        substr(u.message, 1, 200) as preview,
        length(u.message) as msg_length
    FROM user_messages u 
    JOIN base_messages b ON u.uuid = b.uuid 
    WHERE u.message LIKE ?
    """
    
    params = [f'%{query}%']
    
    if days:
        base_query += " AND b.timestamp > strftime('%s', 'now', ?)"
        params.append(f'-{days} days')
    
    if project:
        base_query += " AND b.cwd LIKE ?"
        params.append(f'%{project}%')
    
    base_query += " ORDER BY b.timestamp DESC LIMIT ?"
    params.append(limit)
    
    # Execute search
    conn = sqlite3.connect(CLAUDE_DB)
    cursor = conn.cursor()
    results = cursor.execute(base_query, params).fetchall()
    conn.close()
    
    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return
    
    # Display results
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Session", style="cyan")
    table.add_column("Project", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Preview", style="white")
    
    for session_id, project, date, preview, length in results:
        project_name = Path(project).name if project else "Unknown"
        preview_text = preview.replace('\n', ' ')[:100] + "..."
        table.add_row(
            session_id[:8],
            project_name,
            date.split()[0],
            preview_text
        )
    
    console.print(table)
    console.print(f"\n[dim]Use 'uvmgr claude resume {results[0][0][:8]}' to continue a conversation[/dim]")
    
    add_span_event("conversation_search_completed", {
        "query": query,
        "results_found": len(results),
    })


@app.command("quick-search")
@instrument_command("claude_quick_search", track_args=True)
def quick_search(
    query: str = typer.Argument(..., help="Search query for conversation history"),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Search within last N days"
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project name"
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum results to show"
    ),
    export_results: bool = typer.Option(
        False,
        "--export",
        "-e",
        help="Export results to JSON"
    ),
):
    """
    Legacy search command (uses ops layer).
    
    For direct database search, use 'uvmgr claude search' instead.
    """
    add_span_attributes(**{
        AIAttributes.OPERATION: "conversation_search_ops",
        "ai.query": query,
        "ai.days": days,
        "ai.project": project or "all",
    })
    
    console.print(f"🔎 Searching conversations for: [bold cyan]{query}[/bold cyan]")
    console.print(f"📅 Time range: Last {days} days")
    
    try:
        # Search across multiple sources
        results = claude_ops.search_conversations(
            query=query,
            days_back=days,
            project_filter=project,
            limit=limit
        )
        
        if not results:
            console.print("[yellow]No matching conversations found.[/yellow]")
            return
        
        # Display results in a table
        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Date", style="green")
        table.add_column("Project", style="blue")
        table.add_column("Preview", style="white")
        table.add_column("Messages", style="magenta")
        
        for result in results[:limit]:
            table.add_row(
                result["session_id"][:8] + "...",
                result["date"],
                result.get("project", "N/A"),
                result["preview"][:50] + "...",
                str(result.get("message_count", "?"))
            )
        
        console.print(table)
        
        if len(results) > limit:
            console.print(f"\n[dim]... and {len(results) - limit} more results[/dim]")
        
        # Export if requested
        if export_results:
            export_path = Path(f"claude_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(export_path, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"\n💾 Results exported to: {export_path}")
        
        add_span_event("conversation_search_completed", {
            "query": query,
            "results_found": len(results),
            "exported": export_results,
        })
        
    except Exception as e:
        add_span_event("conversation_search_failed", {"error": str(e)})
        console.print(f"[red]❌ Search failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("recent")
@instrument_command("claude_recent", track_args=True)
def recent(
    days: int = typer.Option(7, "--days", "-d", help="Show conversations from last N days"),
    limit: int = typer.Option(15, "--limit", "-n", help="Number of results"),
):
    """
    Show recent Claude conversations (80/20).
    
    Common use case: "What was I working on recently?"
    """
    if not CLAUDE_DB.exists():
        console.print("[red]Claude database not found[/red]")
        raise typer.Exit(1)
    
    query = """
    SELECT 
        b.session_id,
        b.cwd,
        datetime(MIN(b.timestamp), 'unixepoch') as start_date,
        datetime(MAX(b.timestamp), 'unixepoch') as last_activity,
        COUNT(*) as message_count
    FROM base_messages b
    WHERE b.timestamp > strftime('%s', 'now', ?)
    GROUP BY b.session_id, b.cwd
    ORDER BY MAX(b.timestamp) DESC 
    LIMIT ?
    """
    
    conn = sqlite3.connect(CLAUDE_DB)
    cursor = conn.cursor()
    results = cursor.execute(query, (f'-{days} days', limit)).fetchall()
    conn.close()
    
    if not results:
        console.print(f"[yellow]No conversations in the last {days} days[/yellow]")
        return
    
    table = Table(title=f"Recent Conversations (Last {days} Days)")
    table.add_column("Session", style="cyan")
    table.add_column("Project", style="green")
    table.add_column("Started", style="yellow")
    table.add_column("Last Active", style="yellow")
    table.add_column("Messages", style="magenta")
    
    for session_id, cwd, start, last, count in results:
        project = Path(cwd).name if cwd else "Unknown"
        table.add_row(
            session_id[:8],
            project,
            start.split()[0],
            last.split()[0],
            str(count)
        )
    
    console.print(table)
    
    add_span_event("recent_conversations_listed", {
        "days": days,
        "results": len(results),
    })


@app.command("stats")
@instrument_command("claude_stats", track_args=True)  
def stats():
    """
    Show Claude usage statistics (80/20).
    
    Quick overview of Claude usage patterns.
    """
    if not CLAUDE_DB.exists():
        console.print("[red]Claude database not found[/red]")
        raise typer.Exit(1)
    
    conn = sqlite3.connect(CLAUDE_DB)
    cursor = conn.cursor()
    
    # Get overall stats
    total_messages = cursor.execute("SELECT COUNT(*) FROM user_messages").fetchone()[0]
    total_sessions = cursor.execute("SELECT COUNT(DISTINCT session_id) FROM base_messages").fetchone()[0]
    
    # Get project stats
    project_stats = cursor.execute("""
        SELECT 
            CASE 
                WHEN cwd IS NULL THEN 'Unknown'
                ELSE cwd
            END as project,
            COUNT(DISTINCT session_id) as sessions,
            COUNT(*) as messages
        FROM base_messages
        GROUP BY cwd
        ORDER BY messages DESC
        LIMIT 10
    """).fetchall()
    
    # Get time stats
    time_stats = cursor.execute("""
        SELECT 
            date(timestamp, 'unixepoch') as day,
            COUNT(*) as messages
        FROM base_messages
        WHERE timestamp > strftime('%s', 'now', '-30 days')
        GROUP BY day
        ORDER BY day DESC
    """).fetchall()
    
    conn.close()
    
    # Display stats
    console.print("\n[bold]Claude Usage Statistics[/bold]")
    console.print(f"Total Messages: [cyan]{total_messages:,}[/cyan]")
    console.print(f"Total Sessions: [cyan]{total_sessions:,}[/cyan]")
    
    # Project table
    console.print("\n[bold]Top Projects:[/bold]")
    project_table = Table()
    project_table.add_column("Project", style="green")
    project_table.add_column("Sessions", style="yellow") 
    project_table.add_column("Messages", style="magenta")
    
    for project, sessions, messages in project_stats[:5]:
        project_name = Path(project).name if project != 'Unknown' else 'Unknown'
        project_table.add_row(project_name, str(sessions), str(messages))
    
    console.print(project_table)
    
    # Activity graph (simple ASCII)
    if time_stats:
        console.print("\n[bold]Activity (Last 30 Days):[/bold]")
        max_messages = max(count for _, count in time_stats)
        for day, count in time_stats[:10]:
            bar_length = int((count / max_messages) * 40)
            bar = "█" * bar_length
            console.print(f"{day}: {bar} {count}")
    
    add_span_event("usage_stats_displayed", {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
    })


@app.command("project")
@instrument_command("claude_project", track_args=True)
def project(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project path to search"),
    here: bool = typer.Option(False, "--here", help="Search in current directory"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of results"),
):
    """
    Search conversations by project (80/20).
    
    Common use case: "What did I discuss about this project?"
    """
    if here:
        path = str(Path.cwd())
    elif not path:
        path = str(Path.cwd())
    
    # First check JSON for quick project history
    if CLAUDE_JSON.exists():
        with open(CLAUDE_JSON) as f:
            data = json.load(f)
        
        # Find matching projects
        matches = []
        for proj_path, proj_data in data.get('projects', {}).items():
            if path.lower() in proj_path.lower():
                history = proj_data.get('history', [])
                if history:
                    matches.append((proj_path, len(history)))
        
        if matches:
            console.print(f"\n[bold]Project History Summary:[/bold]")
            for proj_path, count in sorted(matches, key=lambda x: x[1], reverse=True)[:5]:
                project_name = Path(proj_path).name
                console.print(f"  • {project_name}: {count} interactions")
    
    # Then search database for detailed results
    if CLAUDE_DB.exists():
        conn = sqlite3.connect(CLAUDE_DB)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            b.session_id,
            datetime(MIN(b.timestamp), 'unixepoch') as start_date,
            COUNT(*) as messages,
            GROUP_CONCAT(DISTINCT 
                CASE 
                    WHEN LENGTH(u.message) > 50 
                    THEN SUBSTR(u.message, 1, 50) || '...'
                    ELSE u.message 
                END, ' | '
            ) as topics
        FROM base_messages b
        LEFT JOIN user_messages u ON b.uuid = u.uuid
        WHERE b.cwd LIKE ?
        GROUP BY b.session_id
        ORDER BY MAX(b.timestamp) DESC
        LIMIT ?
        """
        
        results = cursor.execute(query, (f'%{path}%', limit)).fetchall()
        conn.close()
        
        if results:
            console.print(f"\n[bold]Detailed Sessions:[/bold]")
            table = Table()
            table.add_column("Session", style="cyan")
            table.add_column("Date", style="yellow")
            table.add_column("Messages", style="magenta")
            table.add_column("Topics Preview", style="white")
            
            for session_id, date, count, topics in results:
                topics_preview = topics[:100] + "..." if topics and len(topics) > 100 else (topics or "")
                table.add_row(
                    session_id[:8],
                    date.split()[0],
                    str(count),
                    topics_preview
                )
            
            console.print(table)
    
    add_span_event("project_search_completed", {
        "path": path,
        "matches_found": len(matches) if 'matches' in locals() else 0,
    })


@app.command("resume")
@instrument_command("claude_resume", track_args=True)
def resume(
    session_id: Optional[str] = typer.Argument(None, help="Session ID to resume (partial match)"),
    last: bool = typer.Option(False, "--last", "-l", help="Resume most recent conversation"),
):
    """Resume a previous Claude conversation."""
    add_span_attributes(**{
        AIAttributes.OPERATION: "conversation_resume",
        "ai.resume_method": "last" if last else "manual",
    })
    
    try:
        if last:
            # Get most recent session
            recent_sessions = claude_ops.search_conversations("", days_back=7, limit=1)
            if not recent_sessions:
                console.print("[red]❌ No recent conversations found[/red]")
                raise typer.Exit(1)
            
            session_id = recent_sessions[0]["session_id"]
            console.print(f"[cyan]Resuming most recent session: {session_id}[/cyan]")
        
        if not session_id:
            console.print("[yellow]Recent sessions to resume:[/yellow]")
            recent(days=7, limit=10)
            return
        
        # Resume session using ops layer
        result = claude_ops.resume_session(session_id)
        console.print(f"[green]✓ {result['message']}[/green]")
        
        add_span_event("conversation_resumed", {
            "session_id": session_id,
            "method": "last" if last else "manual",
        })
        
    except Exception as e:
        add_span_event("conversation_resume_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to resume session: {e}[/red]")
        raise typer.Exit(1)


@app.command("export-resume")
@instrument_command("claude_export_resume", track_args=True)
def export_resume(
    session_id: str = typer.Argument(..., help="Session ID to resume"),
    show_context: bool = typer.Option(
        True,
        "--context/--no-context",
        help="Show conversation context"
    ),
):
    """Legacy resume command (uses ops layer)."""
    add_span_attributes(**{
        AIAttributes.OPERATION: "conversation_resume",
        "ai.session_id": session_id,
    })
    
    try:
        session_data = claude_ops.get_session(session_id)
        
        if not session_data:
            console.print(f"[red]❌ Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        
        # Display session info
        panel = Panel(
            f"[bold]Session:[/bold] {session_data['id']}\n"
            f"[bold]Date:[/bold] {session_data['date_range']}\n"
            f"[bold]Messages:[/bold] {session_data['message_count']}\n"
            f"[bold]Project:[/bold] {session_data.get('project', 'N/A')}",
            title="Resuming Conversation",
            border_style="cyan"
        )
        console.print(panel)
        
        if show_context:
            console.print("\n[bold]Recent messages:[/bold]")
            for msg in session_data.get("recent_messages", [])[-5:]:
                role = "You" if msg["role"] == "user" else "Claude"
                console.print(f"\n[dim]{role}:[/dim] {msg['content'][:200]}...")
        
        # Set up session for resumption
        claude_ops.set_active_session(session_id)
        console.print(f"\n✅ Session {session_id} is now active")
        
        add_span_event("conversation_resumed", {
            "session_id": session_id,
            "message_count": session_data['message_count'],
        })
        
    except Exception as e:
        add_span_event("conversation_resume_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to resume session: {e}[/red]")
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Custom Commands
# ──────────────────────────────────────────────────────────────────────────────

@app.command("create")
@instrument_command("claude_create_command", track_args=True)
def create_command(
    name: str = typer.Argument(..., help="Command name"),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Template: review, optimize, analyze, custom"
    ),
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Command description"
    ),
    global_cmd: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Create as global command"
    ),
):
    """Create a new custom Claude command."""
    add_span_attributes(**{
        AIAttributes.OPERATION: "create_command",
        "ai.command_name": name,
        "ai.template": template or "custom",
        "ai.global": global_cmd,
    })
    
    try:
        # Validate command name
        if not name.replace("-", "_").isidentifier():
            console.print(f"[red]❌ Invalid command name: {name}[/red]")
            raise typer.Exit(1)
        
        # Create command
        command_path = claude_ops.create_custom_command(
            name=name,
            description=description,
            template=template,
            is_global=global_cmd
        )
        
        console.print(f"✅ Created command: [bold cyan]{name}[/bold cyan]")
        console.print(f"📁 Location: {command_path}")
        console.print(f"\n💡 Usage: `/{'user' if global_cmd else 'project'}:{name}`")
        
        add_span_event("command_created", {
            "name": name,
            "template": template or "custom",
            "path": str(command_path),
        })
        
    except Exception as e:
        add_span_event("command_creation_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to create command: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
@instrument_command("claude_list_commands", track_args=True)
def list_commands(
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all commands including system"
    ),
):
    """List available Claude custom commands."""
    add_span_attributes(**{
        AIAttributes.OPERATION: "list_commands",
        "ai.show_all": show_all,
    })
    
    try:
        commands = claude_ops.list_custom_commands(include_system=show_all)
        
        if not commands:
            console.print("[yellow]No custom commands found.[/yellow]")
            return
        
        # Group by scope
        project_cmds = [c for c in commands if c["scope"] == "project"]
        user_cmds = [c for c in commands if c["scope"] == "user"]
        system_cmds = [c for c in commands if c["scope"] == "system"]
        
        # Display project commands
        if project_cmds:
            console.print("\n[bold]Project Commands:[/bold]")
            for cmd in project_cmds:
                console.print(f"  • /project:{cmd['name']} - {cmd['description']}")
        
        # Display user commands
        if user_cmds:
            console.print("\n[bold]User Commands:[/bold]")
            for cmd in user_cmds:
                console.print(f"  • /user:{cmd['name']} - {cmd['description']}")
        
        # Display system commands
        if system_cmds and show_all:
            console.print("\n[bold]System Commands:[/bold]")
            for cmd in system_cmds:
                console.print(f"  • /{cmd['name']} - {cmd['description']}")
        
        console.print(f"\n📊 Total: {len(commands)} commands")
        
        add_span_event("commands_listed", {
            "total": len(commands),
            "project": len(project_cmds),
            "user": len(user_cmds),
            "system": len(system_cmds),
        })
        
    except Exception as e:
        add_span_event("list_commands_failed", {"error": str(e)})
        console.print(f"[red]❌ Failed to list commands: {e}[/red]")
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Workflow Commands
# ──────────────────────────────────────────────────────────────────────────────

@app.command("workflow")
@instrument_command("claude_workflow", track_args=True)
def workflow(
    name: str = typer.Argument(..., help="Workflow name to execute"),
    params: Optional[str] = typer.Option(
        None,
        "--params",
        "-p",
        help="JSON parameters for workflow"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode"
    ),
):
    """Execute predefined AI workflows."""
    add_span_attributes(**{
        AIAttributes.OPERATION: "workflow",
        "ai.workflow_name": name,
        "ai.interactive": interactive,
    })
    
    try:
        # Parse parameters
        workflow_params = {}
        if params:
            workflow_params = json.loads(params)
        
        console.print(f"🔄 Executing workflow: [bold cyan]{name}[/bold cyan]")
        
        # Execute workflow
        results = claude_ops.execute_workflow(
            workflow_name=name,
            parameters=workflow_params,
            interactive=interactive
        )
        
        # Display results
        if results.get("status") == "completed":
            console.print("✅ Workflow completed successfully!")
            if results.get("output"):
                console.print("\n[bold]Output:[/bold]")
                console.print(results["output"])
        else:
            console.print(f"[yellow]⚠️ Workflow status: {results.get('status')}[/yellow]")
        
        add_span_event("workflow_completed", {
            "workflow": name,
            "status": results.get("status"),
            "duration": results.get("duration"),
        })
        
    except json.JSONDecodeError:
        console.print("[red]❌ Invalid JSON parameters[/red]")
        raise typer.Exit(1)
    except Exception as e:
        add_span_event("workflow_failed", {"error": str(e)})
        console.print(f"[red]❌ Workflow failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("debate")
@instrument_command("claude_debate", track_args=True)
def debate(
    topic: str = typer.Argument(..., help="Topic for expert debate"),
    experts: str = typer.Option(
        ...,
        "--experts",
        "-e",
        help="Comma-separated expert roles"
    ),
    rounds: int = typer.Option(
        3,
        "--rounds",
        "-r",
        help="Number of debate rounds"
    ),
    format: str = typer.Option(
        "structured",
        "--format",
        "-f",
        help="Debate format: structured, freeform, socratic"
    ),
):
    """
    Launch expert debate on architecture or design decisions.
    
    Multiple AI experts debate a topic from their perspectives,
    challenging assumptions and exploring trade-offs.
    """
    add_span_attributes(**{
        AIAttributes.OPERATION: "expert_debate",
        "ai.topic": topic,
        "ai.rounds": rounds,
        "ai.format": format,
    })
    
    expert_list = [e.strip() for e in experts.split(",")]
    
    console.print(f"🎭 Starting Expert Debate: [bold cyan]{topic}[/bold cyan]")
    console.print(f"👥 Experts: {', '.join(expert_list)}")
    console.print(f"📋 Format: {format}, Rounds: {rounds}")
    
    try:
        debate_results = claude_ops.expert_debate(
            topic=topic,
            experts=expert_list,
            rounds=rounds,
            debate_format=format
        )
        
        # Display debate summary
        _display_debate_results(debate_results)
        
        add_span_event("debate_completed", {
            "topic": topic,
            "experts": len(expert_list),
            "consensus_reached": debate_results.get("consensus", False),
        })
        
    except Exception as e:
        add_span_event("debate_failed", {"error": str(e)})
        console.print(f"[red]❌ Debate failed: {e}[/red]")
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _display_multi_mind_results(results: Dict[str, Any]) -> None:
    """Display multi-mind analysis results."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]🎯 Multi-Mind Analysis Complete[/bold green]")
    console.print("=" * 80)
    
    # Display specialists
    if "specialists" in results:
        console.print("\n[bold]Specialist Perspectives:[/bold]")
        for specialist in results["specialists"]:
            console.print(f"\n🧑‍🔬 [cyan]{specialist['role']}[/cyan]")
            console.print(f"   {specialist['perspective']}")
    
    # Display key insights
    if "insights" in results:
        console.print("\n[bold]Key Insights:[/bold]")
        for i, insight in enumerate(results["insights"], 1):
            console.print(f"\n{i}. [green]{insight['title']}[/green]")
            console.print(f"   {insight['description']}")
    
    # Display synthesis
    if "synthesis" in results:
        console.print("\n[bold]Synthesis:[/bold]")
        console.print(results["synthesis"])


def _display_analysis_results(results: Dict[str, Any]) -> None:
    """Display code analysis results."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]📊 Code Analysis Results[/bold green]")
    console.print("=" * 80)
    
    # Display issues
    if results.get("issues"):
        console.print("\n[bold red]🚨 Issues Found:[/bold red]")
        for issue in results["issues"]:
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim"
            }.get(issue.get("severity", "medium"), "white")
            
            console.print(f"\n• [{severity_color}]{issue['title']}[/{severity_color}]")
            console.print(f"  Location: {issue.get('location', 'N/A')}")
            console.print(f"  {issue['description']}")
    
    # Display suggestions
    if results.get("suggestions"):
        console.print("\n[bold cyan]💡 Suggestions:[/bold cyan]")
        for suggestion in results["suggestions"]:
            console.print(f"\n• {suggestion['title']}")
            console.print(f"  {suggestion['description']}")
    
    # Display metrics
    if results.get("metrics"):
        console.print("\n[bold]📈 Metrics:[/bold]")
        for metric, value in results["metrics"].items():
            console.print(f"  • {metric}: {value}")


def _display_debate_results(results: Dict[str, Any]) -> None:
    """Display expert debate results."""
    console.print("\n" + "=" * 80)
    console.print("[bold green]🎭 Expert Debate Summary[/bold green]")
    console.print("=" * 80)
    
    # Display rounds
    if "rounds" in results:
        for round_num, round_data in enumerate(results["rounds"], 1):
            console.print(f"\n[bold]Round {round_num}:[/bold]")
            for expert, argument in round_data.items():
                console.print(f"\n👤 [cyan]{expert}:[/cyan]")
                console.print(f"   {argument}")
    
    # Display consensus or disagreements
    if results.get("consensus"):
        console.print("\n[bold green]✅ Consensus Reached:[/bold green]")
        console.print(results["consensus"])
    else:
        console.print("\n[bold yellow]⚖️ Key Disagreements:[/bold yellow]")
        for disagreement in results.get("disagreements", []):
            console.print(f"• {disagreement}")
    
    # Display recommendations
    if results.get("recommendations"):
        console.print("\n[bold]📋 Recommendations:[/bold]")
        for rec in results["recommendations"]:
            console.print(f"• {rec}")


def _save_analysis(results: Dict[str, Any], output_path: Path) -> None:
    """Save analysis results to file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": results.get("type", "multi_mind"),
        "results": results
    }
    
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)