"""
MCP commands for uvmgr CLI.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from uvmgr.core.telemetry import span
from uvmgr.mcp.client import UvmgrMCPClient
from uvmgr.core.validation import ValidationLevel

logger = logging.getLogger(__name__)
console = Console()


@click.group("mcp")
def mcp_group():
    """MCP (Model Context Protocol) commands for uvmgr."""
    pass


@mcp_group.command("server")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def start_server(host: str, port: int, reload: bool):
    """Start the uvmgr MCP server."""
    with span("mcp.start_server", host=host, port=port):
        try:
            import uvicorn
            from uvmgr.mcp.server import server
            
            console.print(f"🚀 Starting uvmgr MCP server on {host}:{port}")
            
            if reload:
                uvicorn.run(
                    "uvmgr.mcp.server:server.app",
                    host=host,
                    port=port,
                    reload=True
                )
            else:
                uvicorn.run(server.app, host=host, port=port)
                
        except Exception as e:
            console.print(f"❌ Failed to start server: {e}", style="red")
            raise


@mcp_group.command("status")
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
@click.option("--validation-level", default="strict", help="Validation level")
@click.option("--format", "output_format", default="table", help="Output format (table, json, rich)")
def get_status(owner: str, repo: str, server_url: str, validation_level: str, output_format: str):
    """Get GitHub Actions status via MCP."""
    with span("mcp.get_status", owner=owner, repo=repo):
        async def _get_status():
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching status...", total=None)
                
                result = await client.get_github_actions_status(
                    owner, repo, validation_level
                )
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                if output_format == "json":
                    console.print(json.dumps(result, indent=2))
                elif output_format == "rich":
                    _display_rich_status(result)
                else:
                    _display_table_status(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_get_status())


@mcp_group.command("workflows")
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
@click.option("--validation-level", default="strict", help="Validation level")
def list_workflows(owner: str, repo: str, server_url: str, validation_level: str):
    """List GitHub Actions workflows via MCP."""
    with span("mcp.list_workflows", owner=owner, repo=repo):
        async def _list_workflows():
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching workflows...", total=None)
                
                result = await client.list_workflows(owner, repo, validation_level)
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                _display_workflows(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_list_workflows())


@mcp_group.command("runs")
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--workflow-id", help="Workflow ID to filter by")
@click.option("--status", help="Status to filter by")
@click.option("--per-page", default=30, help="Number of runs per page")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
@click.option("--validation-level", default="strict", help="Validation level")
def get_runs(owner: str, repo: str, workflow_id: Optional[str], status: Optional[str], 
             per_page: int, server_url: str, validation_level: str):
    """Get workflow runs via MCP."""
    with span("mcp.get_runs", owner=owner, repo=repo):
        async def _get_runs():
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching workflow runs...", total=None)
                
                result = await client.get_workflow_runs(
                    owner, repo, workflow_id, status, per_page, validation_level
                )
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                _display_runs(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_get_runs())


@mcp_group.command("dashboard")
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--time-window", default="1h", help="Time window for metrics")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
@click.option("--validation-level", default="strict", help="Validation level")
def get_dashboard(owner: str, repo: str, time_window: str, server_url: str, validation_level: str):
    """Get validation dashboard via MCP."""
    with span("mcp.get_dashboard", owner=owner, repo=repo):
        async def _get_dashboard():
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating dashboard...", total=None)
                
                result = await client.get_validation_dashboard(
                    owner, repo, time_window, validation_level
                )
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                _display_dashboard(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_get_dashboard())


@mcp_group.command("optimize")
@click.option("--owner", required=True, help="Repository owner")
@click.option("--repo", required=True, help="Repository name")
@click.option("--target", default="performance", help="Optimization target")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
def optimize_workflows(owner: str, repo: str, target: str, server_url: str):
    """Optimize workflows via MCP."""
    with span("mcp.optimize_workflows", owner=owner, repo=repo):
        async def _optimize_workflows():
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing workflows...", total=None)
                
                result = await client.optimize_workflows(owner, repo, target)
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                _display_optimization(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_optimize_workflows())


@mcp_group.command("validate")
@click.option("--data", required=True, help="JSON data to validate")
@click.option("--validation-level", default="strict", help="Validation level")
@click.option("--server-url", default="http://localhost:8000", help="MCP server URL")
def validate_data(data: str, validation_level: str, server_url: str):
    """Validate data via MCP."""
    with span("mcp.validate_data"):
        async def _validate_data():
            try:
                data_dict = json.loads(data)
            except json.JSONDecodeError:
                console.print("❌ Invalid JSON data", style="red")
                return
            
            client = UvmgrMCPClient(server_url)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Validating data...", total=None)
                
                result = await client.validate_data(data_dict, validation_level)
                
                progress.update(task, completed=True)
            
            if result["status"] == "success":
                _display_validation(result)
            else:
                console.print(f"❌ Error: {result.get('message', 'Unknown error')}", style="red")
        
        asyncio.run(_validate_data())


def _display_rich_status(result: Dict[str, Any]):
    """Display status in rich format."""
    data = result["data"]["data"]
    validation = result["data"]["validation"]
    interpretation = result.get("interpretation", {})
    
    # Status overview
    status_table = Table(title="GitHub Actions Status")
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="green")
    
    if "workflow_runs" in data:
        runs = data["workflow_runs"]
        status_table.add_row("Total Runs", str(len(runs)))
        
        # Count by status
        status_counts = {}
        for run in runs:
            status = run.get("conclusion", run.get("status", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            status_table.add_row(f"Status: {status}", str(count))
    
    console.print(status_table)
    
    # Validation info
    if validation:
        validation_panel = Panel(
            f"Valid: {validation['is_valid']}\n"
            f"Confidence: {validation['confidence']:.2f}\n"
            f"Issues: {len(validation['issues'])}",
            title="Validation Results",
            border_style="blue"
        )
        console.print(validation_panel)
    
    # Interpretation
    if interpretation:
        insights = interpretation.get("key_insights", "No insights available")
        next_actions = interpretation.get("next_actions", "No actions suggested")
        
        insights_panel = Panel(
            f"Insights: {insights}\n\nNext Actions: {next_actions}",
            title="AI Analysis",
            border_style="green"
        )
        console.print(insights_panel)


def _display_table_status(result: Dict[str, Any]):
    """Display status in table format."""
    data = result["data"]["data"]
    validation = result["data"]["validation"]
    
    table = Table(title="GitHub Actions Status")
    table.add_column("Metric")
    table.add_column("Value")
    
    if "workflow_runs" in data:
        runs = data["workflow_runs"]
        table.add_row("Total Runs", str(len(runs)))
        
        # Count by status
        status_counts = {}
        for run in runs:
            status = run.get("conclusion", run.get("status", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            table.add_row(f"Status: {status}", str(count))
    
    table.add_row("Validation Valid", str(validation["is_valid"]))
    table.add_row("Confidence", f"{validation['confidence']:.2f}")
    table.add_row("Issues", str(len(validation["issues"])))
    
    console.print(table)


def _display_workflows(result: Dict[str, Any]):
    """Display workflows."""
    data = result["data"]["data"]
    validation = result["data"]["validation"]
    
    table = Table(title="GitHub Actions Workflows")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Created At")
    
    for workflow in data:
        table.add_row(
            str(workflow.get("id", "")),
            workflow.get("name", ""),
            workflow.get("state", ""),
            workflow.get("created_at", "")
        )
    
    console.print(table)
    
    # Validation info
    if validation:
        console.print(f"Validation: {'✅' if validation['is_valid'] else '❌'} "
                     f"(confidence: {validation['confidence']:.2f})")


def _display_runs(result: Dict[str, Any]):
    """Display workflow runs."""
    data = result["data"]["data"]
    validation = result["data"]["validation"]
    
    table = Table(title="Workflow Runs")
    table.add_column("ID")
    table.add_column("Workflow")
    table.add_column("Status")
    table.add_column("Conclusion")
    table.add_column("Created At")
    
    for run in data.get("workflow_runs", []):
        table.add_row(
            str(run.get("id", "")),
            run.get("name", ""),
            run.get("status", ""),
            run.get("conclusion", ""),
            run.get("created_at", "")
        )
    
    console.print(table)
    
    # Validation info
    if validation:
        console.print(f"Validation: {'✅' if validation['is_valid'] else '❌'} "
                     f"(confidence: {validation['confidence']:.2f})")


def _display_dashboard(result: Dict[str, Any]):
    """Display validation dashboard."""
    data = result["data"]
    metrics = data.get("metrics", {})
    recommendations = data.get("recommendations", {})
    
    # Metrics table
    metrics_table = Table(title="Validation Metrics")
    metrics_table.add_column("Metric")
    metrics_table.add_column("Value")
    
    metrics_table.add_row("Total Requests", str(metrics.get("total_requests", 0)))
    metrics_table.add_row("Valid Requests", str(metrics.get("valid_requests", 0)))
    metrics_table.add_row("Invalid Requests", str(metrics.get("invalid_requests", 0)))
    metrics_table.add_row("Average Confidence", f"{metrics.get('average_confidence', 0):.2f}")
    
    if "average_response_time" in metrics:
        metrics_table.add_row("Avg Response Time", f"{metrics['average_response_time']:.2f}ms")
    
    console.print(metrics_table)
    
    # Issue types
    if metrics.get("issue_types"):
        issue_table = Table(title="Issue Types")
        issue_table.add_column("Type")
        issue_table.add_column("Count")
        
        for issue_type, count in metrics["issue_types"].items():
            issue_table.add_row(issue_type, str(count))
        
        console.print(issue_table)
    
    # Recommendations
    if recommendations:
        rec_panel = Panel(
            f"Recommendations: {recommendations.get('recommendations', 'No recommendations')}\n\n"
            f"Reasoning: {recommendations.get('reasoning', 'No reasoning provided')}",
            title="AI Recommendations",
            border_style="green"
        )
        console.print(rec_panel)


def _display_optimization(result: Dict[str, Any]):
    """Display optimization results."""
    data = result["data"]
    optimization = data.get("optimization", {})
    
    # Optimization suggestions
    suggestions = optimization.get("optimization_suggestions", "No suggestions available")
    improvement = optimization.get("expected_improvement", "Unknown")
    
    opt_panel = Panel(
        f"Suggestions: {suggestions}\n\n"
        f"Expected Improvement: {improvement}",
        title="Workflow Optimization",
        border_style="yellow"
    )
    console.print(opt_panel)
    
    # Statistics
    stats_table = Table(title="Analysis Statistics")
    stats_table.add_column("Metric")
    stats_table.add_column("Value")
    
    stats_table.add_row("Workflows Analyzed", str(data.get("workflows_count", 0)))
    stats_table.add_row("Runs Analyzed", str(data.get("runs_count", 0)))
    
    console.print(stats_table)


def _display_validation(result: Dict[str, Any]):
    """Display validation results."""
    data = result["data"]
    validation = data.get("validation", {})
    interpretation = result.get("interpretation", {})
    
    # Validation results
    val_table = Table(title="Validation Results")
    val_table.add_column("Metric")
    val_table.add_column("Value")
    
    val_table.add_row("Is Valid", str(validation.get("is_valid", False)))
    val_table.add_row("Confidence", f"{validation.get('confidence', 0):.2f}")
    val_table.add_row("Issues Count", str(len(validation.get("issues", []))))
    
    console.print(val_table)
    
    # Issues
    if validation.get("issues"):
        issues_table = Table(title="Validation Issues")
        issues_table.add_column("Issue")
        
        for issue in validation["issues"]:
            issues_table.add_row(issue)
        
        console.print(issues_table)
    
    # Interpretation
    if interpretation:
        insights = interpretation.get("key_insights", "No insights available")
        next_actions = interpretation.get("next_actions", "No actions suggested")
        
        int_panel = Panel(
            f"Insights: {insights}\n\nNext Actions: {next_actions}",
            title="AI Interpretation",
            border_style="green"
        )
        console.print(int_panel) 