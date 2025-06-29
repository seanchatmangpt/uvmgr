"""
Simple Definition of Done automation commands.
Streamlined implementation for immediate functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uvmgr.ops.dod import (
    DOD_CRITERIA_WEIGHTS,
    analyze_project_status,
    create_exoskeleton,
    execute_complete_automation,
    generate_devops_pipeline,
    run_e2e_automation,
    validate_dod_criteria,
)

app = typer.Typer(
    name="dod",
    help="🎯 Definition of Done automation with Weaver Forge exoskeleton"
)

console = Console()

@app.command("complete")
def complete_automation(
    environment: str = typer.Option("development", "--env", "-e"),
    auto_fix: bool = typer.Option(False, "--auto-fix"),
    parallel: bool = typer.Option(True, "--parallel/--sequential"),
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """🎯 Execute complete Definition of Done automation."""
    console.print("🎯 [bold blue]Definition of Done Automation[/bold blue]")

    project_path = project or Path.cwd()
    result = execute_complete_automation(
        project_path=project_path,
        environment=environment,
        auto_fix=auto_fix,
        parallel=parallel
    )

    # Display results
    table = Table(title="DoD Results")
    table.add_column("Criteria", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="right")

    for criteria, details in result.get("criteria_results", {}).items():
        status = "✅ PASS" if details.get("passed", False) else "❌ FAIL"
        score = f"{details.get('score', 0):.1f}%"
        table.add_row(criteria.title(), status, score)

    console.print(table)

    success = result.get("success", False)
    if success:
        console.print("\n✅ [green]DoD automation completed successfully![/green]")
    else:
        console.print("\n❌ [red]DoD automation failed. Check results above.[/red]")
        raise typer.Exit(1)

@app.command("exoskeleton")
def setup_exoskeleton(
    template: str = typer.Option("standard", "--template", "-t"),
    force: bool = typer.Option(False, "--force"),
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """🏗️ Initialize Weaver Forge exoskeleton."""
    console.print("🏗️ [bold blue]Initializing Weaver Forge Exoskeleton[/bold blue]")

    project_path = project or Path.cwd()
    result = create_exoskeleton(project_path, template, force)

    if result.get("success", False):
        console.print("✅ [green]Exoskeleton initialized successfully![/green]")

        files = result.get("created_files", [])
        if files:
            console.print(f"📁 Created {len(files)} files:")
            for file_info in files[:5]:  # Show first 5 files
                console.print(f"   📄 {file_info.get('path', 'Unknown')}")
    else:
        console.print("❌ [red]Failed to initialize exoskeleton[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("validate")
def validate_criteria(
    criteria: list[str] | None = typer.Option(None, "--criteria", "-c"),
    detailed: bool = typer.Option(False, "--detailed"),
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """✅ Validate Definition of Done criteria."""
    console.print("✅ [bold blue]DoD Criteria Validation[/bold blue]")

    project_path = project or Path.cwd()
    criteria_list = criteria or list(DOD_CRITERIA_WEIGHTS.keys())

    result = validate_dod_criteria(
        project_path=project_path,
        criteria=criteria_list,
        detailed=detailed,
        fix_suggestions=True
    )

    # Display results
    table = Table(title="Validation Results")
    table.add_column("Criteria", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status", justify="center")

    for criteria, details in result.get("criteria_scores", {}).items():
        score = f"{details.get('score', 0):.1f}%"
        status = "✅ PASS" if details.get("passed", False) else "❌ FAIL"
        table.add_row(criteria.title(), score, status)

    console.print(table)

    overall_score = result.get("overall_score", 0)
    console.print(f"\n📊 Overall Score: {overall_score:.1f}%")

    if result.get("success", False):
        console.print("✅ [green]All validations passed![/green]")
    else:
        console.print("⚠️ [yellow]Some validations failed[/yellow]")

@app.command("pipeline")
def create_devops_pipeline(
    provider: str = typer.Option("github", "--provider", "-p"),
    environments: str = typer.Option("dev,staging,prod", "--environments", "-e"),
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """🚀 Create DevOps pipeline automation."""
    console.print("🚀 [bold blue]DevOps Pipeline Creation[/bold blue]")

    project_path = project or Path.cwd()
    env_list = [env.strip() for env in environments.split(",")]

    result = generate_devops_pipeline(
        project_path=project_path,
        provider=provider,
        environments=env_list,
        features=["testing", "security"],
        template="standard"
    )

    if result.get("success", False):
        console.print("✅ [green]Pipeline created successfully![/green]")
        console.print(f"📁 Provider: {provider}")
        console.print(f"🌍 Environments: {', '.join(env_list)}")
    else:
        console.print("❌ [red]Failed to create pipeline[/red]")
        console.print(f"Error: {result.get('error', 'Unknown error')}")

@app.command("testing")
def run_comprehensive_tests(
    strategy: str = typer.Option("comprehensive", "--strategy", "-s"),
    coverage: int = typer.Option(80, "--coverage", "-c"),
    parallel: bool = typer.Option(True, "--parallel/--sequential"),
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """🧪 Execute comprehensive testing strategy."""
    console.print("🧪 [bold blue]Comprehensive Testing[/bold blue]")

    project_path = project or Path.cwd()
    result = run_e2e_automation(
        project_path=project_path,
        environment="development",
        parallel=parallel,
        headless=True,
        record_video=False,
        generate_report=True
    )

    # Display test results
    table = Table(title="Test Results")
    table.add_column("Test Type", style="cyan")
    table.add_column("Coverage", justify="right")
    table.add_column("Status", justify="center")

    for test_type, details in result.get("test_suites", {}).items():
        coverage_pct = f"{details.get('passed', 0)}/{details.get('total', 0)}"
        status = "✅ PASS" if details.get("failed", 0) == 0 else "❌ FAIL"
        table.add_row(test_type.title(), coverage_pct, status)

    console.print(table)

    if result.get("success", False):
        console.print("✅ [green]All tests passed![/green]")
    else:
        console.print("❌ [red]Some tests failed[/red]")
        raise typer.Exit(1)

@app.command("status")
def show_project_status(
    project: Path | None = typer.Option(None, "--project", help="Path to external project root")
):
    """📊 Show project DoD status overview."""
    console.print("📊 [bold blue]Project DoD Status[/bold blue]")

    project_path = project or Path.cwd()
    result = analyze_project_status(
        project_path=project_path,
        detailed=False,
        suggestions=True
    )

    overall_score = result.get("health_score", 0)

    # Status panel
    if overall_score >= 80:
        status_color = "green"
        status_text = "EXCELLENT"
    elif overall_score >= 60:
        status_color = "yellow"
        status_text = "GOOD"
    else:
        status_color = "red"
        status_text = "NEEDS WORK"

    panel = Panel(
        f"Overall Health Score: {overall_score:.1f}%\n"
        f"Status: {status_text}\n"
        f"DoD Compliance: {result.get('dod_status', {}).get('overall_score', 0):.1f}%\n"
        f"Security Score: {result.get('security_posture', {}).get('score', 0):.1f}%",
        title="📊 DoD Status Summary",
        border_style=status_color
    )

    console.print(panel)

    # Quick recommendations
    suggestions = result.get("suggestions", [])

    if suggestions:
        console.print("\n🔧 [bold yellow]Recommendations:[/bold yellow]")
        for suggestion in suggestions[:3]:  # Show top 3
            console.print(f"   • {suggestion}")

        console.print("\nRun [cyan]uvmgr dod complete --auto-fix[/cyan] to address issues")

if __name__ == "__main__":
    app()
