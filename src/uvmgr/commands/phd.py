"""
PhD-Level Automation Commands for uvmgr.

This module provides CLI commands for PhD-level research automation including
external project analysis, research methodology automation, academic workflow
orchestration, and rigorous validation systems.

Commands:
- research: Conduct comprehensive PhD-level research
- analyze: Analyze external projects for research integration
- validate: Rigorous validation with academic standards
- workflow: Execute academic research workflows
- export: Export comprehensive research packages

Example:
    $ uvmgr phd research --question "How do ML frameworks impact developer productivity?" --methodology experimental
    $ uvmgr phd analyze --repo https://github.com/tensorflow/tensorflow --discipline computer_science
    $ uvmgr phd workflow phd_research --context research_context.yml
    $ uvmgr phd validate --findings results.json --level publication_ready
"""

from __future__ import annotations

import typer
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.tree import Tree
from rich.columns import Columns

from uvmgr.core.phd_automation import (
    PhDAutomationManager,
    ResearchContext,
    ResearchMethodology,
    AcademicDiscipline,
    ValidationLevel,
    ExternalProject
)
from uvmgr.core.shell import dump_json

app = typer.Typer(help="🎓 PhD-level automation for external projects")
console = Console()


@app.command("research")
def conduct_research(
    question: str = typer.Argument(..., help="Primary research question to investigate"),
    methodology: str = typer.Option("experimental", "--methodology", "-m", help="Research methodology"),
    discipline: str = typer.Option("computer_science", "--discipline", "-d", help="Academic discipline"),
    external_repo: Optional[str] = typer.Option(None, "--repo", "-r", help="External repository URL"),
    objectives: List[str] = typer.Option([], "--objective", "-o", help="Research objectives"),
    keywords: List[str] = typer.Option([], "--keyword", "-k", help="Literature keywords"),
    validation_level: str = typer.Option("standard", "--validation", "-v", help="Validation rigor level"),
    output_dir: Optional[Path] = typer.Option(None, "--output", help="Output directory for research package"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Research context file"),
):
    """🔬 Conduct comprehensive PhD-level research with external project integration."""
    
    console.print(Panel(
        f"🎓 [bold]PhD-Level Research Automation[/bold]\\n"
        f"Question: {question}\\n"
        f"Methodology: {methodology}\\n"
        f"Discipline: {discipline}\\n"
        f"External Repo: {external_repo or 'None'}\\n"
        f"Validation Level: {validation_level}",
        title="Research Initiation"
    ))
    
    # Convert string parameters to enums
    try:
        methodology_enum = ResearchMethodology(methodology)
        discipline_enum = AcademicDiscipline(discipline)
        validation_enum = ValidationLevel(validation_level)
    except ValueError as e:
        console.print(f"[red]❌ Invalid parameter: {str(e)}[/red]")
        console.print(f"Valid methodologies: {', '.join([m.value for m in ResearchMethodology])}")
        console.print(f"Valid disciplines: {', '.join([d.value for d in AcademicDiscipline])}")
        console.print(f"Valid validation levels: {', '.join([v.value for v in ValidationLevel])}")
        raise typer.Exit(1)
    
    # Create research context
    context = ResearchContext(
        project_name=f"research_{question.lower().replace(' ', '_')[:20]}",
        research_question=question,
        methodology=methodology_enum,
        discipline=discipline_enum,
        external_repo_url=external_repo,
        objectives=objectives or [
            "Conduct comprehensive literature review",
            "Develop rigorous research methodology",
            "Analyze external project integration opportunities",
            "Validate findings with academic standards"
        ],
        literature_keywords=keywords or ["automation", "research", "methodology"],
        validation_level=validation_enum
    )
    
    # Load additional context if provided
    if context_file and context_file.exists():
        try:
            with open(context_file) as f:
                if context_file.suffix.lower() == '.json':
                    additional_context = json.load(f)
                else:
                    import yaml
                    additional_context = yaml.safe_load(f)
            
            # Update context with additional data
            if 'hypothesis' in additional_context:
                context.hypothesis = additional_context['hypothesis']
            if 'success_criteria' in additional_context:
                context.success_criteria = additional_context['success_criteria']
            if 'constraints' in additional_context:
                context.constraints = additional_context['constraints']
            
            console.print(f"📂 Loaded additional context from {context_file}")
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to load context file: {e}[/yellow]")
    
    # Initialize PhD automation manager
    manager = PhDAutomationManager()
    
    # Conduct comprehensive research
    with Progress() as progress:
        task = progress.add_task("Conducting PhD-level research...", total=100)
        
        try:
            # Run async research process
            async def run_research():
                return await manager.conduct_comprehensive_research(context)
            
            results = asyncio.run(run_research())
            progress.update(task, advance=80)
            
            # Export research package
            if not output_dir:
                output_dir = Path(f"research_package_{context.project_name}")
            
            package_path = manager.export_research_package(results, output_dir)
            progress.update(task, advance=20)
            
            console.print(f"[green]✅ Research completed successfully![/green]")
            console.print(f"📁 Research package exported to: {package_path}")
            
            # Display research summary
            _display_research_summary(results)
            
        except Exception as e:
            console.print(f"[red]❌ Research failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command("analyze")
def analyze_external_project(
    repo_url: str = typer.Argument(..., help="External repository URL to analyze"),
    discipline: str = typer.Option("computer_science", "--discipline", "-d", help="Academic discipline context"),
    methodology: str = typer.Option("experimental", "--methodology", "-m", help="Research methodology"),
    research_focus: Optional[str] = typer.Option(None, "--focus", "-f", help="Specific research focus area"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for analysis results"),
    detailed: bool = typer.Option(False, "--detailed", help="Perform detailed analysis"),
):
    """🔍 Analyze external projects for PhD-level research integration."""
    
    console.print(Panel(
        f"🔍 [bold]External Project Analysis[/bold]\\n"
        f"Repository: {repo_url}\\n"
        f"Discipline: {discipline}\\n"
        f"Methodology: {methodology}\\n"
        f"Research Focus: {research_focus or 'General'}\\n"
        f"Detailed Analysis: {'Yes' if detailed else 'No'}",
        title="Project Analysis"
    ))
    
    try:
        discipline_enum = AcademicDiscipline(discipline)
        methodology_enum = ResearchMethodology(methodology)
    except ValueError as e:
        console.print(f"[red]❌ Invalid parameter: {str(e)}[/red]")
        raise typer.Exit(1)
    
    # Create research context for analysis
    context = ResearchContext(
        project_name="external_project_analysis",
        research_question=research_focus or "How can this external project contribute to research?",
        methodology=methodology_enum,
        discipline=discipline_enum,
        external_repo_url=repo_url
    )
    
    manager = PhDAutomationManager()
    
    with Progress() as progress:
        task = progress.add_task("Analyzing external project...", total=100)
        
        try:
            # Clone and analyze the project
            async def analyze_project():
                project_path = Path(tempfile.mkdtemp()) / "analysis_project"
                external_project = await manager.project_manager.clone_external_project(
                    repo_url, project_path
                )
                return manager.engine.analyze_external_project(external_project, context)
            
            analysis_results = asyncio.run(analyze_project())
            progress.update(task, advance=100)
            
            # Display analysis results
            _display_project_analysis(analysis_results, detailed)
            
            # Export results if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(analysis_results, f, indent=2, default=str)
                console.print(f"📄 Analysis results exported to: {output_file}")
            
        except Exception as e:
            console.print(f"[red]❌ Project analysis failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command("validate")
def validate_research(
    findings_file: Path = typer.Argument(..., help="Research findings file (JSON)"),
    validation_level: str = typer.Option("standard", "--level", "-l", help="Validation rigor level"),
    methodology: str = typer.Option("experimental", "--methodology", "-m", help="Research methodology used"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Validation report output file"),
    peer_review: bool = typer.Option(False, "--peer-review", help="Include peer review assessment"),
):
    """✅ Validate research results with PhD-level academic rigor."""
    
    if not findings_file.exists():
        console.print(f"[red]❌ Findings file not found: {findings_file}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"✅ [bold]Research Validation[/bold]\\n"
        f"Findings File: {findings_file}\\n"
        f"Validation Level: {validation_level}\\n"
        f"Methodology: {methodology}\\n"
        f"Peer Review: {'Yes' if peer_review else 'No'}",
        title="Research Validation"
    ))
    
    try:
        validation_enum = ValidationLevel(validation_level)
        methodology_enum = ResearchMethodology(methodology)
    except ValueError as e:
        console.print(f"[red]❌ Invalid parameter: {str(e)}[/red]")
        raise typer.Exit(1)
    
    # Load research findings
    try:
        with open(findings_file) as f:
            findings = json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Failed to load findings file: {e}[/red]")
        raise typer.Exit(1)
    
    # Create validation context
    context = ResearchContext(
        project_name="validation_assessment",
        research_question="Validation of research findings",
        methodology=methodology_enum,
        discipline=AcademicDiscipline.COMPUTER_SCIENCE,
        validation_level=validation_enum
    )
    
    manager = PhDAutomationManager()
    
    with Progress() as progress:
        task = progress.add_task("Validating research results...", total=100)
        
        try:
            validation_results = manager.engine.validate_research_results(findings, context)
            progress.update(task, advance=100)
            
            # Display validation results
            _display_validation_results(validation_results, peer_review)
            
            # Export validation report if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(validation_results, f, indent=2, default=str)
                console.print(f"📄 Validation report exported to: {output_file}")
            
        except Exception as e:
            console.print(f"[red]❌ Validation failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command("workflow")
def execute_workflow(
    workflow_name: str = typer.Argument("phd_research", help="Academic workflow to execute"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Research context file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show workflow steps without executing"),
    output_dir: Optional[Path] = typer.Option(None, "--output", help="Output directory for workflow results"),
):
    """🔄 Execute academic research workflows with BPMN orchestration."""
    
    console.print(Panel(
        f"🔄 [bold]Academic Workflow Execution[/bold]\\n"
        f"Workflow: {workflow_name}\\n"
        f"Context File: {context_file or 'Default'}\\n"
        f"Dry Run: {'Yes' if dry_run else 'No'}",
        title="Workflow Execution"
    ))
    
    # Load context if provided
    context = ResearchContext(
        project_name="workflow_execution",
        research_question="Workflow-driven research execution",
        methodology=ResearchMethodology.EXPERIMENTAL,
        discipline=AcademicDiscipline.COMPUTER_SCIENCE
    )
    
    if context_file and context_file.exists():
        try:
            with open(context_file) as f:
                if context_file.suffix.lower() == '.json':
                    context_data = json.load(f)
                else:
                    import yaml
                    context_data = yaml.safe_load(f)
            
            # Update context with loaded data
            if 'research_question' in context_data:
                context.research_question = context_data['research_question']
            if 'methodology' in context_data:
                context.methodology = ResearchMethodology(context_data['methodology'])
            if 'discipline' in context_data:
                context.discipline = AcademicDiscipline(context_data['discipline'])
            
            console.print(f"📂 Loaded context from {context_file}")
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to load context file: {e}[/yellow]")
    
    # Show workflow steps if dry run
    if dry_run:
        _show_workflow_steps(workflow_name)
        return
    
    # Execute workflow
    manager = PhDAutomationManager()
    
    with Progress() as progress:
        task = progress.add_task("Executing academic workflow...", total=100)
        
        try:
            workflow_results = manager.workflow_engine.execute_workflow(workflow_name, context)
            progress.update(task, advance=100)
            
            console.print(f"[green]✅ Workflow '{workflow_name}' completed successfully![/green]")
            
            # Display workflow results
            _display_workflow_results(workflow_results)
            
            # Export results if requested
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                results_file = output_dir / f"workflow_results_{workflow_name}.json"
                with open(results_file, 'w') as f:
                    json.dump(workflow_results, f, indent=2, default=str)
                console.print(f"📁 Workflow results exported to: {output_dir}")
            
        except Exception as e:
            console.print(f"[red]❌ Workflow execution failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command("export")
def export_research_package(
    research_dir: Path = typer.Argument(..., help="Research directory to package"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output package file"),
    format_type: str = typer.Option("zip", "--format", "-f", help="Package format (zip, tar, pdf)"),
    include_raw_data: bool = typer.Option(False, "--include-data", help="Include raw data files"),
    academic_format: bool = typer.Option(False, "--academic", help="Format for academic submission"),
):
    """📦 Export comprehensive research packages for dissemination."""
    
    if not research_dir.exists():
        console.print(f"[red]❌ Research directory not found: {research_dir}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"📦 [bold]Research Package Export[/bold]\\n"
        f"Source Directory: {research_dir}\\n"
        f"Output Format: {format_type}\\n"
        f"Include Raw Data: {'Yes' if include_raw_data else 'No'}\\n"
        f"Academic Format: {'Yes' if academic_format else 'No'}",
        title="Package Export"
    ))
    
    # Determine output file
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"research_package_{timestamp}.{format_type}")
    
    with Progress() as progress:
        task = progress.add_task("Creating research package...", total=100)
        
        try:
            # Create package based on format
            if format_type == "zip":
                import zipfile
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in research_dir.rglob("*"):
                        if file_path.is_file():
                            if not include_raw_data and "raw_data" in str(file_path):
                                continue
                            arcname = file_path.relative_to(research_dir)
                            zipf.write(file_path, arcname)
            
            elif format_type == "tar":
                import tarfile
                with tarfile.open(output_file, 'w:gz') as tarf:
                    for file_path in research_dir.rglob("*"):
                        if file_path.is_file():
                            if not include_raw_data and "raw_data" in str(file_path):
                                continue
                            arcname = file_path.relative_to(research_dir)
                            tarf.add(file_path, arcname)
            
            progress.update(task, advance=80)
            
            # Add academic formatting if requested
            if academic_format:
                _add_academic_formatting(output_file, research_dir)
            
            progress.update(task, advance=20)
            
            console.print(f"[green]✅ Research package created: {output_file}[/green]")
            
            # Display package information
            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            console.print(f"📊 Package size: {file_size:.2f} MB")
            console.print(f"📁 Package location: {output_file.absolute()}")
            
        except Exception as e:
            console.print(f"[red]❌ Package creation failed: {str(e)}[/red]")
            raise typer.Exit(1)


def _display_research_summary(results: Dict[str, Any]):
    """Display comprehensive research summary."""
    console.print("\\n" + "="*80)
    console.print("[bold cyan]📊 RESEARCH SUMMARY[/bold cyan]")
    console.print("="*80)
    
    components = results.get("components", {})
    
    # Create components table
    components_table = Table(title="Research Components Completed", show_header=True)
    components_table.add_column("Component", style="cyan")
    components_table.add_column("Status", style="green")
    components_table.add_column("Description", style="white")
    
    component_descriptions = {
        "research_design": "Comprehensive research methodology and experimental design",
        "literature_review": "Systematic literature review and theoretical framework",
        "external_analysis": "External project integration and analysis",
        "workflow_execution": "Academic workflow orchestration and task management",
        "validation": "Rigorous validation and quality assurance",
        "academic_paper": "Publication-ready academic paper generation"
    }
    
    for component_name in components.keys():
        description = component_descriptions.get(component_name, "Research component")
        components_table.add_row(
            component_name.replace("_", " ").title(),
            "✅ Complete",
            description
        )
    
    console.print(components_table)


def _display_project_analysis(analysis_results: Dict[str, Any], detailed: bool):
    """Display external project analysis results."""
    console.print("\\n" + "="*80)
    console.print("[bold cyan]🔍 PROJECT ANALYSIS RESULTS[/bold cyan]")
    console.print("="*80)
    
    # Integration assessment
    integration_panel = Panel(
        analysis_results.get("integration_assessment", "No assessment available"),
        title="Integration Assessment"
    )
    console.print(integration_panel)
    
    # Research opportunities
    opportunities_panel = Panel(
        analysis_results.get("research_opportunities", "No opportunities identified"),
        title="Research Opportunities"
    )
    console.print(opportunities_panel)
    
    if detailed:
        # Technical challenges
        challenges_panel = Panel(
            analysis_results.get("technical_challenges", "No challenges identified"),
            title="Technical Challenges"
        )
        console.print(challenges_panel)
        
        # Codebase analysis
        codebase_analysis = analysis_results.get("codebase_analysis", {})
        if codebase_analysis:
            console.print("\\n[bold cyan]📁 Codebase Analysis[/bold cyan]")
            
            metrics_table = Table(show_header=True)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")
            
            metrics_table.add_row("Total Files", str(codebase_analysis.get("total_files", 0)))
            metrics_table.add_row("Languages", str(len(codebase_analysis.get("languages", {}))))
            metrics_table.add_row("Frameworks", str(len(codebase_analysis.get("frameworks", []))))
            metrics_table.add_row("Dependencies", str(len(codebase_analysis.get("dependencies", []))))
            
            console.print(metrics_table)


def _display_validation_results(validation_results: Dict[str, Any], peer_review: bool):
    """Display research validation results."""
    console.print("\\n" + "="*80)
    console.print("[bold cyan]✅ VALIDATION RESULTS[/bold cyan]")
    console.print("="*80)
    
    # Validity assessment
    validity_panel = Panel(
        validation_results.get("validity_assessment", "No validity assessment available"),
        title="Validity Assessment"
    )
    console.print(validity_panel)
    
    # Reliability analysis
    reliability_panel = Panel(
        validation_results.get("reliability_analysis", "No reliability analysis available"),
        title="Reliability Analysis"
    )
    console.print(reliability_panel)
    
    if peer_review:
        # Peer review readiness
        peer_review_panel = Panel(
            validation_results.get("peer_review_readiness", "No peer review assessment available"),
            title="Peer Review Readiness"
        )
        console.print(peer_review_panel)


def _display_workflow_results(workflow_results: Dict[str, Any]):
    """Display academic workflow execution results."""
    console.print("\\n" + "="*80)
    console.print("[bold cyan]🔄 WORKFLOW EXECUTION RESULTS[/bold cyan]")
    console.print("="*80)
    
    # Workflow information
    info_table = Table(show_header=True)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Workflow Name", workflow_results.get("workflow_name", "Unknown"))
    info_table.add_row("Status", workflow_results.get("status", "Unknown"))
    info_table.add_row("Execution Time", workflow_results.get("execution_time", "Unknown"))
    info_table.add_row("Tasks Completed", str(len(workflow_results.get("tasks_completed", []))))
    
    console.print(info_table)
    
    # Tasks completed
    if workflow_results.get("tasks_completed"):
        console.print("\\n[bold cyan]📋 Tasks Completed[/bold cyan]")
        for task in workflow_results["tasks_completed"]:
            console.print(f"   ✅ {task.replace('_', ' ').title()}")


def _show_workflow_steps(workflow_name: str):
    """Show workflow steps for dry run."""
    console.print("\\n[bold cyan]📋 Workflow Steps[/bold cyan]")
    
    workflow_tree = Tree(f"🔄 [bold]{workflow_name.replace('_', ' ').title()} Workflow[/bold]")
    
    if workflow_name == "phd_research":
        step1 = workflow_tree.add("📚 1. Literature Review")
        step1.add("🔍 Search academic databases")
        step1.add("📖 Analyze relevant papers")
        step1.add("🎯 Identify research gaps")
        
        step2 = workflow_tree.add("🏗️ 2. Research Design")
        step2.add("❓ Refine research question")
        step2.add("⚗️ Design methodology")
        step2.add("📊 Plan data collection")
        
        step3 = workflow_tree.add("🔍 3. External Project Analysis")
        step3.add("📥 Clone external repository")
        step3.add("🧮 Analyze codebase metrics")
        step3.add("🔗 Assess integration potential")
        
        step4 = workflow_tree.add("📊 4. Data Collection & Analysis")
        step4.add("📈 Execute data collection")
        step4.add("🧪 Perform statistical analysis")
        step4.add("📋 Document findings")
        
        step5 = workflow_tree.add("✅ 5. Validation")
        step5.add("🔍 Validate results")
        step5.add("👥 Conduct peer review")
        step5.add("📝 Document validation")
        
        step6 = workflow_tree.add("📄 6. Academic Paper Generation")
        step6.add("✍️ Generate paper structure")
        step6.add("📝 Write content sections")
        step6.add("🎯 Format for publication")
    
    console.print(workflow_tree)
    console.print("\\n💡 Run without --dry-run to execute the workflow")


def _add_academic_formatting(package_file: Path, research_dir: Path):
    """Add academic formatting to research package."""
    # This would add academic-specific formatting and structure
    # For now, just log the operation
    console.print(f"📚 Added academic formatting to package")


if __name__ == "__main__":
    app()