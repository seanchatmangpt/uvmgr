"""
Security scanning and vulnerability management commands.

This module provides security analysis capabilities for Python projects,
following the 80/20 principle: 20% of security checks catch 80% of vulnerabilities.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from uvmgr.core.instrumentation import instrument_command
from uvmgr.ops import security as security_ops

app = typer.Typer(help="🔒 Security scanning and vulnerability management")
console = Console()


@app.command("scan")
@instrument_command
def scan_vulnerabilities(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path to scan"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, sarif)"),
    severity: str = typer.Option("medium", "--severity", "-s", help="Minimum severity (low, medium, high, critical)"),
    fix_mode: bool = typer.Option(False, "--fix", help="Attempt to fix vulnerabilities automatically"),
    audit_deps: bool = typer.Option(True, "--audit-deps/--no-audit-deps", help="Audit dependencies for vulnerabilities"),
    code_scan: bool = typer.Option(True, "--code-scan/--no-code-scan", help="Scan code for security issues"),
    secrets_scan: bool = typer.Option(True, "--secrets-scan/--no-secrets-scan", help="Scan for exposed secrets"),
) -> None:
    """
    🔍 Comprehensive security vulnerability scanning.
    
    Performs multi-layered security analysis:
    - Dependency vulnerability scanning
    - Code security analysis 
    - Secret detection
    - Configuration security review
    """
    scan_path = path or Path.cwd()
    
    if not scan_path.exists():
        console.print(f"[red]❌ Path does not exist: {scan_path}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"🔒 [bold]Security Vulnerability Scan[/bold]\\n"
        f"Path: {scan_path}\\n"
        f"Severity: {severity}+\\n"
        f"Format: {output_format}",
        title="Security Analysis"
    ))
    
    try:
        # Run comprehensive security scan using the operations layer
        results = security_ops.run_comprehensive_scan(
            project_path=scan_path,
            severity_threshold=severity,
            audit_dependencies=audit_deps,
            scan_code=code_scan,
            scan_secrets=secrets_scan,
            fix_mode=fix_mode
        )
        
        # Display results based on format
        if output_format == "table":
            _display_security_table(results)
        elif output_format == "json":
            console.print_json(data=results)
        elif output_format == "sarif":
            sarif_output = "{}"  # Placeholder SARIF output
            console.print(sarif_output)
        
        # Summary
        total_issues = sum(len(category_results) for category_results in results.values() if isinstance(category_results, list))
        critical_issues = sum(
            1 for category_results in results.values() 
            if isinstance(category_results, list)
            for issue in category_results 
            if issue.get("severity") == "critical"
        )
        
        if critical_issues > 0:
            console.print(f"\\n[red]⚠️  {critical_issues} critical security issues found![/red]")
            console.print("[yellow]Run with --fix to attempt automatic remediation[/yellow]")
            raise typer.Exit(1)
        elif total_issues > 0:
            console.print(f"\\n[yellow]⚠️  {total_issues} security issues found[/yellow]")
        else:
            console.print("\\n[green]✅ No security vulnerabilities detected![/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Security scan failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("audit")
@instrument_command  
def audit_dependencies(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
    fix_mode: bool = typer.Option(False, "--fix", help="Update vulnerable dependencies")
) -> None:
    """
    🔍 Audit dependencies for known vulnerabilities.
    
    Uses multiple vulnerability databases to check for known security issues
    in project dependencies.
    """
    audit_path = path or Path.cwd()
    
    console.print(Panel(
        f"🔍 [bold]Dependency Security Audit[/bold]\\n"
        f"Path: {audit_path}",
        title="Dependency Audit"
    ))
    
    try:
        # Run dependency audit using the operations layer
        results = security_ops.audit_dependencies(
            project_path=audit_path,
            fix_mode=fix_mode
        )
        
        if output_format == "table":
            _display_dependency_audit_table(results)
        else:
            console.print_json(data=results)
            
        vulnerable_count = len(results.get("vulnerabilities", []))
        if vulnerable_count > 0:
            console.print(f"\\n[red]⚠️  {vulnerable_count} vulnerable dependencies found![/red]")
            if not fix_mode:
                console.print("[yellow]Run with --fix to update vulnerable packages[/yellow]")
        else:
            console.print("\\n[green]✅ All dependencies are secure![/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Dependency audit failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("secrets")
@instrument_command
def scan_secrets(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
    patterns_file: Optional[Path] = typer.Option(None, "--patterns", help="Custom secret patterns file"),
    exclude_patterns: str = typer.Option("", "--exclude", help="Exclude file patterns (comma-separated)"),
) -> None:
    """
    🔐 Scan for exposed secrets and credentials.
    
    Detects common patterns for API keys, passwords, tokens, and other
    sensitive information that shouldn't be committed to version control.
    """
    scan_path = path or Path.cwd()
    
    console.print(Panel(
        f"🔐 [bold]Secret Detection Scan[/bold]\\n"
        f"Path: {scan_path}",
        title="Secret Scanning"
    ))
    
    try:
        # Run secret scan using the operations layer
        results = security_ops.scan_secrets(
            project_path=scan_path,
            patterns_file=patterns_file,
            exclude_patterns=exclude_patterns.split(",") if exclude_patterns else []
        )
        
        _display_secrets_table(results)
        
        secret_count = len(results.get("secrets", []))
        if secret_count > 0:
            console.print(f"\\n[red]⚠️  {secret_count} potential secrets detected![/red]")
            console.print("[yellow]Review and remove sensitive data from version control[/yellow]")
        else:
            console.print("\\n[green]✅ No secrets detected![/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Secret scan failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("config")
@instrument_command
def check_security_config(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
) -> None:
    """
    ⚙️ Check project security configuration.
    
    Reviews project configuration files for security best practices:
    - Requirements pinning
    - Dependency management
    - Build configuration
    - CI/CD security
    """
    config_path = path or Path.cwd()
    
    console.print(Panel(
        f"⚙️ [bold]Security Configuration Review[/bold]\\n"
        f"Path: {config_path}",
        title="Configuration Security"
    ))
    
    try:
        # Run security config check using the operations layer
        results = security_ops.check_security_config(
            project_path=config_path
        )
        
        _display_config_security_table(results)
        
        issues_count = len(results.get("issues", []))
        if issues_count > 0:
            console.print(f"\\n[yellow]⚠️  {issues_count} configuration security issues found[/yellow]")
        else:
            console.print("\\n[green]✅ Security configuration looks good![/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Security config check failed: {e}[/red]")
        raise typer.Exit(1)


def _display_security_table(results: dict) -> None:
    """Display comprehensive security scan results in table format."""
    table = Table(title="Security Scan Results")
    table.add_column("Category", style="cyan")
    table.add_column("Issue", style="red")
    table.add_column("Severity", style="yellow")
    table.add_column("File", style="blue")
    table.add_column("Description", style="white")
    
    for category, issues in results.items():
        if isinstance(issues, list):
            for issue in issues:
                table.add_row(
                    category.title(),
                    issue.get("type", "Unknown"),
                    issue.get("severity", "medium"),
                    issue.get("file", "N/A"),
                    issue.get("description", "No description")[:50] + "..."
                )
    
    console.print(table)


def _display_dependency_audit_table(results: dict) -> None:
    """Display dependency audit results in table format."""
    table = Table(title="Dependency Audit Results")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="yellow")
    table.add_column("Vulnerability", style="red")
    table.add_column("Severity", style="yellow")
    table.add_column("Fixed In", style="green")
    
    for vuln in results.get("vulnerabilities", []):
        table.add_row(
            vuln.get("package", "Unknown"),
            vuln.get("version", "Unknown"),
            vuln.get("id", "N/A"),
            vuln.get("severity", "medium"),
            vuln.get("fixed_in", "Not available")
        )
    
    console.print(table)


def _display_secrets_table(results: dict) -> None:
    """Display secret scan results in table format."""
    table = Table(title="Secret Detection Results")
    table.add_column("File", style="cyan")
    table.add_column("Line", style="yellow")
    table.add_column("Type", style="red")
    table.add_column("Context", style="white")
    
    for secret in results.get("secrets", []):
        context = secret.get("context", "")[:50] + "..." if len(secret.get("context", "")) > 50 else secret.get("context", "")
        table.add_row(
            secret.get("file", "Unknown"),
            str(secret.get("line", 0)),
            secret.get("type", "Unknown"),
            context
        )
    
    console.print(table)


def _display_config_security_table(results: dict) -> None:
    """Display security configuration results in table format."""
    table = Table(title="Security Configuration Review")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("File", style="blue")
    table.add_column("Recommendation", style="white")
    
    for issue in results.get("issues", []):
        status = "❌ Failed" if issue.get("failed", False) else "⚠️ Warning"
        table.add_row(
            issue.get("check", "Unknown"),
            status,
            issue.get("file", "N/A"),
            issue.get("recommendation", "No recommendation")[:60] + "..."
        )
    
    console.print(table)


if __name__ == "__main__":
    app()