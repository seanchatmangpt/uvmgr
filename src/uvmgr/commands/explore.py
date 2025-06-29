"""
uvmgr.commands.explore
=====================

Progressive command discovery and interactive exploration.

This command module addresses the critical UX gap by providing:

• **Interactive exploration**: Discover commands through guided interaction
• **Context-aware suggestions**: Get relevant commands for your project
• **Workflow guidance**: Step-by-step guides for common tasks
• **Smart completion**: Fuzzy search and intelligent auto-complete
• **Learning integration**: Adapts to your usage patterns

Example
-------
    $ uvmgr explore                    # Interactive exploration
    $ uvmgr explore suggest            # Get context-based suggestions
    $ uvmgr explore workflows          # Show guided workflows
    $ uvmgr explore search "testing"   # Search for testing commands

See Also
--------
- :mod:`uvmgr.core.discovery` : Command discovery engine
- :mod:`uvmgr.core.workspace` : Workspace context
"""

from __future__ import annotations

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.text import Text

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.core.discovery import (
    get_discovery_engine,
    suggest_commands,
    suggest_workflows,
    ProjectAnalyzer,
    UserContext,
    CommandSuggestion,
    WorkflowGuide
)

app = typer.Typer(help="Progressive command discovery and interactive exploration")
console = Console()


@app.command()
@instrument_command("explore_interactive", track_args=True)
def main(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    user_level: Optional[str] = typer.Option(None, "--level", "-l", help="User experience level"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Interactive command exploration and discovery."""
    
    console.print("🧭 [bold blue]uvmgr Command Explorer[/bold blue]")
    console.print("Discover commands and workflows tailored to your project\n")
    
    # Analyze current context
    context = ProjectAnalyzer.analyze_current_context()
    
    if user_level:
        context.user_level = user_level
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "explore_interactive",
        "project_type": context.project_type,
        "user_level": context.user_level,
        "category_filter": category or "none"
    })
    
    if json_output:
        suggestions = suggest_commands(context=context)
        workflows = suggest_workflows(context)
        
        exploration_data = {
            "context": {
                "project_type": context.project_type,
                "user_level": context.user_level,
                "environment": context.environment,
                "recent_commands": context.recent_commands
            },
            "suggestions": [
                {
                    "command": s.command,
                    "description": s.description,
                    "confidence": s.confidence,
                    "category": s.category,
                    "examples": s.examples
                }
                for s in suggestions
            ],
            "workflows": [
                {
                    "name": w.name,
                    "description": w.description,
                    "category": w.category,
                    "difficulty": w.difficulty,
                    "estimated_time": w.estimated_time
                }
                for w in workflows
            ]
        }
        dump_json(exploration_data)
        return
    
    # Show project context
    _display_project_context(context)
    
    # Interactive exploration loop
    while True:
        console.print("\n[bold]What would you like to explore?[/bold]")
        console.print("1. 💡 Get command suggestions for this project")
        console.print("2. 📋 Browse workflow guides")
        console.print("3. 🔍 Search for specific commands")
        console.print("4. 🎯 Category-based exploration")
        console.print("5. ❓ Get help with a specific task")
        console.print("6. 🚪 Exit")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "1":
            _explore_suggestions(context, category)
        elif choice == "2":
            _explore_workflows(context)
        elif choice == "3":
            _explore_search()
        elif choice == "4":
            _explore_categories(context)
        elif choice == "5":
            _explore_task_help()
        elif choice == "6":
            console.print("👋 Happy exploring! Run [bold]uvmgr explore[/bold] anytime for guidance.")
            break
    
    add_span_event("explore.session_completed", {
        "project_type": context.project_type,
        "user_level": context.user_level
    })


@app.command("suggest")
@instrument_command("explore_suggest", track_args=True)
def show_suggestions(
    query: Optional[str] = typer.Argument(None, help="Search query for suggestions"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of suggestions"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Get intelligent command suggestions based on your project context."""
    
    context = ProjectAnalyzer.analyze_current_context()
    suggestions = suggest_commands(query or "", context)
    
    # Filter by category if specified
    if category:
        suggestions = [s for s in suggestions if s.category == category]
    
    suggestions = suggestions[:limit]
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "explore_suggest",
        "query": query or "",
        "category": category or "all",
        "suggestions_count": str(len(suggestions))
    })
    
    if json_output:
        suggestion_data = [
            {
                "command": s.command,
                "description": s.description,
                "confidence": s.confidence,
                "rationale": s.rationale,
                "category": s.category,
                "examples": s.examples
            }
            for s in suggestions
        ]
        dump_json(suggestion_data)
        return
    
    if not suggestions:
        console.print("💭 No suggestions found for your query")
        return
    
    console.print(f"💡 [bold]Command Suggestions[/bold] (Project: {context.project_type})")
    
    for i, suggestion in enumerate(suggestions, 1):
        confidence_color = "green" if suggestion.confidence > 0.7 else "yellow" if suggestion.confidence > 0.4 else "white"
        
        console.print(f"\n{i}. [bold]{suggestion.command}[/bold] (confidence: [{confidence_color}]{suggestion.confidence:.1f}[/{confidence_color}])")
        console.print(f"   📝 {suggestion.description}")
        console.print(f"   🎯 {suggestion.rationale}")
        
        if suggestion.examples:
            console.print(f"   💡 Examples: {', '.join(suggestion.examples[:2])}")


@app.command("workflows")
@instrument_command("explore_workflows", track_args=True)
def show_workflows(
    difficulty: Optional[str] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Show guided workflow recommendations."""
    
    context = ProjectAnalyzer.analyze_current_context()
    workflows = suggest_workflows(context)
    
    # Apply filters
    if difficulty:
        workflows = [w for w in workflows if w.difficulty == difficulty]
    if category:
        workflows = [w for w in workflows if w.category == category]
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "explore_workflows",
        "difficulty_filter": difficulty or "all",
        "category_filter": category or "all",
        "workflows_count": str(len(workflows))
    })
    
    if json_output:
        workflow_data = [
            {
                "name": w.name,
                "description": w.description,
                "category": w.category,
                "difficulty": w.difficulty,
                "estimated_time": w.estimated_time,
                "steps": w.steps,
                "prerequisites": w.prerequisites
            }
            for w in workflows
        ]
        dump_json(workflow_data)
        return
    
    if not workflows:
        console.print("📋 No workflows match your criteria")
        return
    
    console.print("📋 [bold]Guided Workflows[/bold]")
    
    for workflow in workflows:
        difficulty_icon = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(workflow.difficulty, "⚪")
        
        console.print(f"\n📋 [bold]{workflow.name.replace('_', ' ').title()}[/bold] {difficulty_icon}")
        console.print(f"   📝 {workflow.description}")
        console.print(f"   ⏱️  {workflow.estimated_time} • 📊 {workflow.difficulty}")
        console.print(f"   🏷️  Category: {workflow.category}")
        
        if workflow.prerequisites:
            console.print(f"   ⚠️  Prerequisites: {', '.join(workflow.prerequisites)}")


@app.command("guide")
@instrument_command("explore_guide", track_args=True)
def show_guide(
    workflow_name: str = typer.Argument(..., help="Workflow guide name"),
    run: bool = typer.Option(False, "--run", "-r", help="Execute the workflow interactively")
):
    """Show detailed workflow guide with step-by-step instructions."""
    
    engine = get_discovery_engine()
    guide = engine.get_workflow_guide(workflow_name)
    
    if not guide:
        console.print(f"❌ Workflow guide '{workflow_name}' not found")
        console.print("\n💡 Available guides:")
        for w in engine.workflow_guides:
            console.print(f"   • {w.name}")
        raise typer.Exit(1)
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "explore_guide",
        "workflow_name": workflow_name,
        "interactive_run": str(run)
    })
    
    # Display guide details
    console.print(f"📋 [bold]{guide.name.replace('_', ' ').title()}[/bold]")
    console.print(f"📝 {guide.description}")
    console.print(f"⏱️  Estimated time: {guide.estimated_time}")
    console.print(f"📊 Difficulty: {guide.difficulty}")
    
    if guide.prerequisites:
        console.print(f"\n⚠️  [bold]Prerequisites:[/bold]")
        for prereq in guide.prerequisites:
            console.print(f"   • {prereq}")
    
    console.print(f"\n📋 [bold]Steps ({len(guide.steps)}):[/bold]")
    
    for i, step in enumerate(guide.steps, 1):
        console.print(f"\n{i}. [bold]{step.get('description', 'Step description')}[/bold]")
        console.print(f"   💻 Command: [cyan]{step.get('command', '')}[/cyan]")
        
        if 'verification' in step:
            console.print(f"   ✅ Verify: {step['verification']}")
        
        if run:
            should_execute = Confirm.ask(f"Execute step {i}?", default=True)
            if should_execute:
                console.print(f"🚀 Executing: {step.get('command', '')}")
                # Here you would integrate with the actual command execution
                console.print("✅ Step completed (simulated)")
            else:
                console.print("⏭️  Step skipped")
    
    if run:
        console.print("\n🎉 [bold green]Workflow completed![/bold green]")
    else:
        console.print("\n💡 Run with [bold]--run[/bold] to execute this workflow interactively")


@app.command("search")
@instrument_command("explore_search", track_args=True)
def search_commands(
    query: str = typer.Argument(..., help="Search query"),
    fuzzy: bool = typer.Option(True, "--fuzzy/--exact", help="Use fuzzy matching"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """Search for commands using fuzzy matching."""
    
    engine = get_discovery_engine()
    
    if fuzzy:
        # Fuzzy search
        matches = engine.fuzzy_search_commands(query)
        results = []
        
        for cmd, similarity in matches[:10]:
            info = engine.command_registry.get(cmd, {})
            results.append({
                "command": cmd,
                "similarity": similarity,
                "description": info.get("description", ""),
                "category": info.get("category", ""),
                "examples": info.get("examples", [])
            })
    else:
        # Exact search using suggestions
        suggestions = suggest_commands(query)
        results = [
            {
                "command": s.command,
                "similarity": s.confidence,
                "description": s.description,
                "category": s.category,
                "examples": s.examples
            }
            for s in suggestions
        ]
    
    add_span_attributes(**{
        CliAttributes.COMMAND: "explore_search",
        "query": query,
        "fuzzy_search": str(fuzzy),
        "results_count": str(len(results))
    })
    
    if json_output:
        dump_json(results)
        return
    
    if not results:
        console.print(f"🔍 No commands found matching '{query}'")
        return
    
    console.print(f"🔍 [bold]Search Results for '{query}'[/bold]")
    
    for result in results:
        similarity_color = "green" if result["similarity"] > 0.7 else "yellow" if result["similarity"] > 0.4 else "white"
        
        console.print(f"\n• [bold]{result['command']}[/bold] (match: [{similarity_color}]{result['similarity']:.1f}[/{similarity_color}])")
        console.print(f"  📝 {result['description']}")
        console.print(f"  🏷️  {result['category']}")
        
        if result['examples']:
            console.print(f"  💡 {', '.join(result['examples'][:2])}")


def _display_project_context(context: UserContext):
    """Display current project context."""
    
    table = Table(title="🏠 Project Context", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    
    table.add_row("Project Type", context.project_type)
    table.add_row("User Level", context.user_level)
    table.add_row("Environment", context.environment)
    table.add_row("Directory", context.current_directory.split('/')[-1])
    
    if context.git_status:
        table.add_row("Git Status", context.git_status)
    
    if context.recent_commands:
        table.add_row("Recent Commands", ", ".join(context.recent_commands[-3:]))
    
    console.print(table)


def _explore_suggestions(context: UserContext, category_filter: Optional[str]):
    """Interactive suggestion exploration."""
    
    suggestions = suggest_commands(context=context)
    
    if category_filter:
        suggestions = [s for s in suggestions if s.category == category_filter]
    
    if not suggestions:
        console.print("💭 No suggestions available for your current context")
        return
    
    console.print(f"\n💡 [bold]Suggestions for your {context.project_type} project:[/bold]")
    
    for i, suggestion in enumerate(suggestions[:5], 1):
        confidence_color = "green" if suggestion.confidence > 0.7 else "yellow"
        
        panel_content = f"[bold]{suggestion.description}[/bold]\n"
        panel_content += f"🎯 {suggestion.rationale}\n"
        
        if suggestion.examples:
            panel_content += f"💡 Example: [cyan]{suggestion.examples[0]}[/cyan]"
        
        panel = Panel(
            panel_content,
            title=f"{i}. {suggestion.command}",
            title_align="left",
            border_style=confidence_color
        )
        console.print(panel)
    
    # Ask if user wants to try a command
    if Confirm.ask("\nWould you like to try one of these commands?"):
        choice = Prompt.ask("Which command? (1-5)", choices=[str(i) for i in range(1, min(6, len(suggestions) + 1))])
        selected = suggestions[int(choice) - 1]
        console.print(f"\n🚀 Great choice! Try: [bold cyan]uvmgr {selected.command}[/bold cyan]")
        
        if selected.examples:
            console.print(f"💡 Examples:")
            for example in selected.examples:
                console.print(f"   uvmgr {example}")


def _explore_workflows(context: UserContext):
    """Interactive workflow exploration."""
    
    workflows = suggest_workflows(context)
    
    if not workflows:
        console.print("📋 No workflow guides available")
        return
    
    console.print(f"\n📋 [bold]Recommended Workflows:[/bold]")
    
    for i, workflow in enumerate(workflows[:3], 1):
        difficulty_icon = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(workflow.difficulty, "⚪")
        
        console.print(f"\n{i}. [bold]{workflow.name.replace('_', ' ').title()}[/bold] {difficulty_icon}")
        console.print(f"   📝 {workflow.description}")
        console.print(f"   ⏱️  {workflow.estimated_time}")
    
    if Confirm.ask("\nWould you like to see a detailed guide?"):
        choice = Prompt.ask("Which workflow? (1-3)", choices=[str(i) for i in range(1, min(4, len(workflows) + 1))])
        selected = workflows[int(choice) - 1]
        console.print(f"\n📋 Run: [bold cyan]uvmgr explore guide {selected.name}[/bold cyan]")


def _explore_search():
    """Interactive command search."""
    
    query = Prompt.ask("\n🔍 What are you looking for?", default="")
    if query:
        # Use the search command internally
        search_commands(query, fuzzy=True, json_output=False)


def _explore_categories(context: UserContext):
    """Category-based exploration."""
    
    engine = get_discovery_engine()
    categories = set(info["category"] for info in engine.command_registry.values())
    
    console.print("\n🏷️  [bold]Command Categories:[/bold]")
    
    category_list = list(categories)
    for i, category in enumerate(category_list, 1):
        console.print(f"{i}. {category.replace('_', ' ').title()}")
    
    choice = Prompt.ask("Choose a category", choices=[str(i) for i in range(1, len(category_list) + 1)])
    selected_category = category_list[int(choice) - 1]
    
    # Show commands in category
    commands = [cmd for cmd, info in engine.command_registry.items() if info["category"] == selected_category]
    
    console.print(f"\n🏷️  [bold]{selected_category.replace('_', ' ').title()} Commands:[/bold]")
    for cmd in commands:
        info = engine.command_registry[cmd]
        console.print(f"• [bold]{cmd}[/bold] - {info['description']}")


def _explore_task_help():
    """Task-specific help."""
    
    common_tasks = {
        "1": "Set up a new project",
        "2": "Add dependencies to my project", 
        "3": "Run tests and check quality",
        "4": "Build and package my application",
        "5": "Set up CI/CD automation",
        "6": "Use AI features for development"
    }
    
    console.print("\n❓ [bold]What do you want to accomplish?[/bold]")
    for key, task in common_tasks.items():
        console.print(f"{key}. {task}")
    
    choice = Prompt.ask("Choose a task", choices=list(common_tasks.keys()))
    task = common_tasks[choice]
    
    # Map tasks to command suggestions
    task_commands = {
        "1": "workspace init",
        "2": "deps add", 
        "3": "tests run",
        "4": "build dist",
        "5": "workflow run ci_cd",
        "6": "ai assist"
    }
    
    suggested_command = task_commands.get(choice, "")
    
    console.print(f"\n💡 For '{task}', try: [bold cyan]uvmgr {suggested_command}[/bold cyan]")
    console.print(f"📖 Get more help: [bold cyan]uvmgr {suggested_command.split()[0]} --help[/bold cyan]")