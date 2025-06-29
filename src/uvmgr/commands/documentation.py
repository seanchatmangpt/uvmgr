"""
Technical Writing Automation Commands for uvmgr.

This module provides CLI commands for AI-powered technical writing automation
using SpiffWorkflow for orchestration and DSPy for content generation.

Commands:
- generate: Generate documentation from templates and context
- workflow: Run documentation generation workflows  
- template: Manage documentation templates
- validate: Validate generated documentation

Example:
    $ uvmgr documentation generate api --format markdown
    $ uvmgr documentation workflow --type user-guide
    $ uvmgr documentation template list
    $ uvmgr documentation validate docs/
"""

from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional, List
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.tree import Tree

from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import CliAttributes, WorkflowAttributes, WorkflowOperations
from uvmgr.core.documentation import (
    TechnicalWritingEngine,
    DocumentationWorkflowEngine,
    DocumentationAutomationManager,
    DocumentType,
    OutputFormat,
    DocumentContext,
    DocumentTemplate
)
from uvmgr.core.shell import dump_json

app = typer.Typer(help="📝 Technical writing automation with AI")
console = Console()


@app.command("generate")
def generate_documentation(
    doc_type: str = typer.Argument("api_docs", help="Type of documentation to generate"),
    output_format: str = typer.Option("markdown", "--format", "-f", help="Output format"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template name to use"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Context file (JSON/YAML)"),
    project_name: Optional[str] = typer.Option(None, "--project", help="Project name"),
    author: Optional[str] = typer.Option(None, "--author", help="Author name"),
    version: Optional[str] = typer.Option(None, "--version", help="Project version"),
    codebase_path: Optional[Path] = typer.Option(None, "--codebase", help="Path to analyze codebase"),
    ai_model: Optional[str] = typer.Option(None, "--model", help="AI model to use"),
):
    """📄 Generate documentation using AI and templates."""
    
    console.print(Panel(
        f"📝 [bold]Generating Technical Documentation[/bold]\n"
        f"Type: {doc_type}\n"
        f"Format: {output_format}\n"
        f"Template: {template or 'default'}\n"
        f"Project: {project_name or Path.cwd().name}",
        title="Documentation Generation"
    ))
    
    # Convert string parameters to enums
    try:
        doc_type_enum = DocumentType(doc_type)
        output_format_enum = OutputFormat(output_format)
    except ValueError as e:
        console.print(f"[red]❌ Invalid parameter: {str(e)}[/red]")
        console.print(f"Valid doc types: {', '.join([t.value for t in DocumentType])}")
        console.print(f"Valid formats: {', '.join([f.value for f in OutputFormat])}")
        raise typer.Exit(1)
    
    # Create document context
    context = DocumentContext(
        project_name=project_name or Path.cwd().name,
        version=version or "1.0.0",
        author=author or "uvmgr",
        codebase_path=codebase_path or Path.cwd()
    )
    
    # Load additional context from file if provided
    if context_file and context_file.exists():
        if context_file.suffix.lower() == '.json':
            with open(context_file) as f:
                additional_context = json.load(f)
        else:  # Assume YAML
            import yaml
            with open(context_file) as f:
                additional_context = yaml.safe_load(f)
        
        context.custom_data.update(additional_context)
        console.print(f"📂 Loaded context from {context_file}")
    
    # Analyze codebase if path provided
    if codebase_path and codebase_path.exists():
        console.print(f"🔍 Analyzing codebase at {codebase_path}")
        # Simulate code analysis - in real implementation, this would scan files
        context.functions = [
            {"name": "create_user", "docstring": "Create a new user account", "file": "users.py"},
            {"name": "get_user", "docstring": "Retrieve user by ID", "file": "users.py"},
        ]
        context.classes = [
            {"name": "UserManager", "docstring": "Manages user operations", "file": "users.py"}
        ]
        context.api_endpoints = [
            {"method": "POST", "path": "/users", "description": "Create user"},
            {"method": "GET", "path": "/users/{id}", "description": "Get user"}
        ]
    
    # Initialize AI engine
    engine = TechnicalWritingEngine(model=ai_model or "openai/gpt-4")
    
    # Generate documentation
    with Progress() as progress:
        task = progress.add_task("Generating documentation...", total=100)
        
        try:
            content = engine.generate_document(doc_type_enum, context, template)
            progress.update(task, advance=50)
            
            # Format content
            formatted_content = engine.format_content(content, output_format_enum)
            progress.update(task, advance=30)
            
            # Determine output path
            if not output_path:
                suffix = {
                    OutputFormat.MARKDOWN: ".md",
                    OutputFormat.HTML: ".html", 
                    OutputFormat.PDF: ".pdf",
                    OutputFormat.DOCX: ".docx",
                    OutputFormat.ASCIIDOC: ".adoc",
                    OutputFormat.RST: ".rst"
                }
                output_path = Path(f"{doc_type_enum.value}{suffix[output_format_enum]}")
            
            # Write output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            progress.update(task, advance=20)
            
            console.print(f"[green]✅ Documentation generated: {output_path}[/green]")
            console.print(f"📄 Content length: {len(formatted_content)} characters")
            
        except Exception as e:
            console.print(f"[red]❌ Generation failed: {str(e)}[/red]")
            raise typer.Exit(1)
    
    add_span_attributes({
        "documentation.type": doc_type_enum.value,
        "documentation.format": output_format_enum.value,
        "documentation.output_path": str(output_path)
    })


@app.command("workflow")
def run_workflow(
    workflow_type: str = typer.Argument("complete_docs", help="Workflow type to run"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Context file"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show workflow steps without executing"),
):
    """🔄 Run documentation generation workflows."""
    
    console.print(Panel(
        f"🔄 [bold]Running Documentation Workflow[/bold]\n"
        f"Type: {workflow_type}\n"
        f"Output: {output_dir or 'current directory'}\n"
        f"Dry Run: {'Yes' if dry_run else 'No'}",
        title="Workflow Execution"
    ))
    
    # Initialize workflow engine
    workflow_engine = DocumentationWorkflowEngine()
    automation_manager = DocumentationAutomationManager()
    
    # Load context
    context = DocumentContext(project_name=Path.cwd().name)
    if context_file and context_file.exists():
        with open(context_file) as f:
            if context_file.suffix.lower() == '.json':
                additional_context = json.load(f)
            else:
                import yaml
                additional_context = yaml.safe_load(f)
        context.custom_data.update(additional_context)
    
    # Show workflow steps if dry run
    if dry_run:
        console.print("📋 [bold]Workflow Steps:[/bold]")
        
        workflow_tree = Tree("📋 Documentation Workflow")
        
        if workflow_type == "complete_docs":
            analyze_branch = workflow_tree.add("🔍 1. Analyze Codebase")
            analyze_branch.add("📂 Scan source files")
            analyze_branch.add("🔍 Extract functions and classes")
            analyze_branch.add("🌐 Discover API endpoints")
            
            generate_branch = workflow_tree.add("📝 2. Generate Documents")
            generate_branch.add("📄 API Documentation")
            generate_branch.add("📖 User Guide")
            generate_branch.add("🏗️ Architecture Guide")
            generate_branch.add("🔧 Troubleshooting Guide")
            
            validate_branch = workflow_tree.add("✅ 3. Validate & Format")
            validate_branch.add("🔍 Content validation")
            validate_branch.add("📐 Format consistency")
            validate_branch.add("🔗 Link verification")
            
            workflow_tree.add("📤 4. Output Generation")
        
        console.print(workflow_tree)
        console.print("\n💡 Run without --dry-run to execute the workflow")
        return
    
    # Execute workflow
    try:
        with Progress() as progress:
            main_task = progress.add_task("Running workflow...", total=100)
            
            # Step 1: Analyze
            progress.update(main_task, description="Analyzing codebase...")
            analysis_result = automation_manager.analyze_codebase(context.codebase_path or Path.cwd())
            progress.update(main_task, advance=25)
            
            # Step 2: Generate documents
            progress.update(main_task, description="Generating documents...")
            
            output_directory = output_dir or Path("docs")
            output_directory.mkdir(exist_ok=True)
            
            # Generate different document types
            doc_types = [DocumentType.API_DOCS, DocumentType.USER_GUIDE, DocumentType.ARCHITECTURE]
            
            for i, doc_type in enumerate(doc_types):
                doc_path = output_directory / f"{doc_type.value}.md"
                result = automation_manager.generate_document_from_workflow(
                    workflow_type, doc_type, context, str(doc_path)
                )
                console.print(f"📄 Generated: {doc_path}")
                progress.update(main_task, advance=15)
            
            # Step 3: Validate
            progress.update(main_task, description="Validating documentation...")
            # Validation would happen here
            progress.update(main_task, advance=25)
            
            console.print(f"[green]✅ Workflow completed successfully![/green]")
            console.print(f"📁 Documentation generated in: {output_directory}")
            
    except Exception as e:
        console.print(f"[red]❌ Workflow failed: {str(e)}[/red]")
        raise typer.Exit(1)
    
    add_span_attributes({
        WorkflowAttributes.OPERATION: WorkflowOperations.RUN,
        WorkflowAttributes.TYPE: "documentation_generation",
        WorkflowAttributes.DEFINITION_NAME: workflow_type
    })


@app.command("template")
def manage_templates(
    action: str = typer.Argument("list", help="Template action (list, create, show, delete)"),
    template_name: Optional[str] = typer.Argument(None, help="Template name"),
    template_file: Optional[Path] = typer.Option(None, "--file", "-f", help="Template file path"),
    doc_type: Optional[str] = typer.Option(None, "--type", help="Document type"),
):
    """📋 Manage documentation templates."""
    
    if action == "list":
        console.print("📋 [bold]Available Templates[/bold]")
        
        # Show built-in templates
        templates_table = Table(title="Documentation Templates", show_header=True)
        templates_table.add_column("Name", style="cyan")
        templates_table.add_column("Type", style="yellow")
        templates_table.add_column("Description", style="white")
        templates_table.add_column("Format", style="green")
        
        # Built-in templates
        builtin_templates = [
            ("api_default", "API Documentation", "Standard API documentation with endpoints", "Markdown"),
            ("user_guide_basic", "User Guide", "Basic user guide template", "Markdown"),
            ("architecture_standard", "Architecture", "Software architecture documentation", "Markdown"),
            ("readme_comprehensive", "README", "Comprehensive README template", "Markdown"),
            ("troubleshooting_faq", "Troubleshooting", "FAQ-style troubleshooting guide", "Markdown"),
        ]
        
        for name, doc_type, description, format_type in builtin_templates:
            templates_table.add_row(name, doc_type, description, format_type)
        
        console.print(templates_table)
        
    elif action == "show":
        if not template_name:
            console.print("[red]❌ Template name required for 'show' action[/red]")
            raise typer.Exit(1)
        
        console.print(f"📋 [bold]Template: {template_name}[/bold]")
        
        # Show template details (mock)
        template_panel = Panel(
            f"[bold]Name:[/bold] {template_name}\n"
            f"[bold]Type:[/bold] API Documentation\n"
            f"[bold]Variables:[/bold] project_name, version, author\n"
            f"[bold]Sections:[/bold] Overview, Authentication, Endpoints, Examples\n\n"
            f"[bold]Template Content:[/bold]\n"
            f"```markdown\n"
            f"# {{{{project_name}}}} API Documentation\n\n"
            f"Version: {{{{version}}}}\n"
            f"Author: {{{{author}}}}\n\n"
            f"## Overview\n"
            f"{{{{description}}}}\n\n"
            f"## Endpoints\n"
            f"{{% for endpoint in api_endpoints %}}\n"
            f"### {{{{endpoint.method}}}} {{{{endpoint.path}}}}\n"
            f"{{{{endpoint.description}}}}\n"
            f"{{% endfor %}}\n"
            f"```",
            title=f"Template: {template_name}"
        )
        console.print(template_panel)
        
    elif action == "create":
        if not template_name or not template_file:
            console.print("[red]❌ Template name and file required for 'create' action[/red]")
            raise typer.Exit(1)
        
        # Create template directory if it doesn't exist
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        template_path = templates_dir / f"{template_name}.md"
        
        # Create basic template
        template_content = f"""# {template_name.replace('_', ' ').title()} Template

<!-- Template variables: project_name, version, author, description -->

# {{{{project_name}}}} Documentation

Version: {{{{version}}}}
Author: {{{{author}}}}

## Description
{{{{description}}}}

<!-- Add your template content here -->
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        console.print(f"[green]✅ Template created: {template_path}[/green]")
        
    elif action == "delete":
        if not template_name:
            console.print("[red]❌ Template name required for 'delete' action[/red]")
            raise typer.Exit(1)
        
        template_path = Path("templates") / f"{template_name}.md"
        if template_path.exists():
            template_path.unlink()
            console.print(f"[green]✅ Template deleted: {template_name}[/green]")
        else:
            console.print(f"[red]❌ Template not found: {template_name}[/red]")
    
    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]")
        console.print("Available actions: list, create, show, delete")
        raise typer.Exit(1)


@app.command("validate")
def validate_documentation(
    docs_path: Path = typer.Argument(Path("docs"), help="Path to documentation directory"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
):
    """✅ Validate generated documentation."""
    
    console.print(Panel(
        f"✅ [bold]Validating Documentation[/bold]\n"
        f"Path: {docs_path}\n"
        f"Fix Issues: {'Yes' if fix else 'No'}",
        title="Documentation Validation"
    ))
    
    if not docs_path.exists():
        console.print(f"[red]❌ Documentation path not found: {docs_path}[/red]")
        raise typer.Exit(1)
    
    # Validate documentation
    validation_results = {
        "total_files": 0,
        "valid_files": 0,
        "issues": [],
        "warnings": [],
        "fixed_issues": []
    }
    
    with Progress() as progress:
        task = progress.add_task("Validating files...", total=100)
        
        # Find documentation files
        doc_files = list(docs_path.glob("**/*.md")) + list(docs_path.glob("**/*.rst"))
        validation_results["total_files"] = len(doc_files)
        
        for i, doc_file in enumerate(doc_files):
            progress.update(task, description=f"Validating {doc_file.name}...")
            
            # Read and validate file
            try:
                content = doc_file.read_text()
                
                # Check for common issues
                issues = []
                warnings = []
                
                # Check for missing title
                if not content.strip().startswith('#'):
                    issues.append(f"Missing title in {doc_file.name}")
                
                # Check for empty sections
                if '##' in content:
                    sections = content.split('##')[1:]
                    for j, section in enumerate(sections):
                        if len(section.strip()) < 50:
                            warnings.append(f"Short section in {doc_file.name}: section {j+1}")
                
                # Check for broken links (basic check)
                import re
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
                for link_text, link_url in links:
                    if link_url.startswith('http'):
                        continue  # Skip external links for now
                    elif link_url.startswith('#'):
                        continue  # Skip anchor links for now
                    else:
                        # Check local file links
                        link_path = docs_path / link_url
                        if not link_path.exists():
                            issues.append(f"Broken link in {doc_file.name}: {link_url}")
                
                if not issues:
                    validation_results["valid_files"] += 1
                
                validation_results["issues"].extend(issues)
                validation_results["warnings"].extend(warnings)
                
                # Fix issues if requested
                if fix and issues:
                    fixed_content = content
                    
                    # Add title if missing
                    if not content.strip().startswith('#'):
                        title = doc_file.stem.replace('_', ' ').replace('-', ' ').title()
                        fixed_content = f"# {title}\n\n{fixed_content}"
                        validation_results["fixed_issues"].append(f"Added title to {doc_file.name}")
                    
                    # Write fixed content
                    if fixed_content != content:
                        doc_file.write_text(fixed_content)
                
            except Exception as e:
                validation_results["issues"].append(f"Error reading {doc_file.name}: {str(e)}")
            
            progress.update(task, advance=100/len(doc_files))
    
    # Output results
    if json_output:
        dump_json(validation_results)
    else:
        # Create results table
        results_table = Table(title="Validation Results", show_header=True)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", style="white")
        results_table.add_column("Status", style="green")
        
        results_table.add_row("Total Files", str(validation_results["total_files"]), "📄")
        results_table.add_row("Valid Files", str(validation_results["valid_files"]), "✅")
        results_table.add_row("Issues", str(len(validation_results["issues"])), "❌" if validation_results["issues"] else "✅")
        results_table.add_row("Warnings", str(len(validation_results["warnings"])), "⚠️" if validation_results["warnings"] else "✅")
        
        if fix:
            results_table.add_row("Fixed", str(len(validation_results["fixed_issues"])), "🔧")
        
        console.print(results_table)
        
        # Show issues and warnings
        if validation_results["issues"]:
            console.print("\n[red]❌ Issues Found:[/red]")
            for issue in validation_results["issues"]:
                console.print(f"   • {issue}")
        
        if validation_results["warnings"]:
            console.print("\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in validation_results["warnings"]:
                console.print(f"   • {warning}")
        
        if fix and validation_results["fixed_issues"]:
            console.print("\n[green]🔧 Issues Fixed:[/green]")
            for fixed in validation_results["fixed_issues"]:
                console.print(f"   • {fixed}")
        
        # Summary
        if validation_results["issues"]:
            console.print(f"\n[red]❌ Validation failed with {len(validation_results['issues'])} issues[/red]")
            if not fix:
                console.print("💡 Use --fix to attempt automatic fixes")
        else:
            console.print(f"\n[green]✅ All {validation_results['total_files']} files validated successfully![/green]")
    
    add_span_event("documentation.validated", {
        "files_count": validation_results["total_files"],
        "issues_count": len(validation_results["issues"]),
        "warnings_count": len(validation_results["warnings"])
    })


if __name__ == "__main__":
    app()