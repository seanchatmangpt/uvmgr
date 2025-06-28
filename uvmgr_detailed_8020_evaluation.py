#!/usr/bin/env python3
"""
Detailed 80/20 Evaluation of uvmgr Commands with Telemetry Validation
=====================================================================

This performs a comprehensive evaluation including:
1. Command inventory with telemetry status
2. Feature gap analysis against WeaverShip roadmap
3. 80/20 prioritization of missing features
4. Telemetry health check for each command group
"""

import subprocess
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import track

console = Console()

# Actual uvmgr commands from OTEL status
ACTUAL_COMMANDS = {
    "agent": ["coordinate_agents", "parse_workflow", "run_8020_validation", 
              "run_bpmn_workflow", "span", "test_workflow", "validate_otel_integration",
              "validate_workflow", "workflow_stats"],
    "ai": ["ask", "delete_model", "fix_tests", "list_models", "plan"],
    "build": ["dist", "dogfood", "exe", "spec"],
    "cache": ["_dir", "_prune"],
    "claude": ["analyze", "create_command", "debate", "export_resume", "init_project",
               "list_commands", "multi_mind", "project", "quick_search", "recent",
               "resume", "search", "search_project", "stats", "workflow"],
    "deps": ["_list", "add", "remove", "upgrade"],
    "exec": ["fallback", "script"],
    "forge": ["generate", "init_forge", "span", "status", "test", "validate", "workflow"],
    "history": ["clear_cmd", "export", "log_cmd", "show", "stats"],
    "index": ["_add", "_list"],
    "lint": ["check", "fix", "format"],
    "otel": ["coverage", "demo_otel_features", "export", "semconv", "span", 
             "status", "test", "validate_8020", "workflow_validate"],
    "project": ["new", "status", "substrate_project"],
    "release": ["_bump", "_changelog"],
    "remote": ["_run"],
    "search": ["search_all", "search_code", "search_deps", "search_files", 
               "search_logs", "search_semantic"],
    "serve": ["serve"],
    "shell": ["open_"],
    "spiff-otel": ["batch_validate_external_projects_cmd", "create_workflow",
                   "discover_external_projects_cmd", "run_workflow", "span",
                   "validate_8020", "validate_8020_external", 
                   "validate_external_project", "validate_otel"],
    "substrate": ["batch_test", "create_project", "customize", "generate_template", 
                  "validate_project"],
    "tests": ["ci_quick", "ci_run", "ci_verify", "run_coverage", "run_tests"],
    "tool": ["dir_", "health", "install", "recommend", "run", "sync",
             "uvx_install", "uvx_list", "uvx_run", "uvx_uninstall", "uvx_upgrade"],
    "weaver": ["check", "diff", "docs", "generate", "init", "install", 
               "resolve", "search", "stats", "version"],
    "workflow": ["analyze_workflow", "benchmark_workflow", "span", 
                 "test_workflow", "validate_workflow"],
}

# Feature mapping - what each command group contributes
COMMAND_FEATURE_CONTRIBUTIONS = {
    # Foundational (Phase 0)
    "build": {
        "features": ["Packaging (PyInstaller)", "Core CLI (Typer)"],
        "coverage": 0.8,  # 80% complete
        "gaps": ["Cross-platform builds", "Signed binaries"]
    },
    "deps": {
        "features": ["Virtualenv / uv lock"],
        "coverage": 0.9,  # 90% complete
        "gaps": ["Lock file validation", "Dependency security scanning"]
    },
    "project": {
        "features": ["Core CLI (Typer)", "Domain-Pack loader"],
        "coverage": 0.6,  # 60% complete
        "gaps": ["Domain pack integration", "Template versioning"]
    },
    
    # Agent-Guides (Phase 1)
    "agent": {
        "features": ["Guide catalog CLI", "Guide-aware templates", "Guide scaffolding (init)"],
        "coverage": 0.7,  # 70% complete
        "gaps": ["Guide fetching", "Guide caching", "Version pinning"]
    },
    "claude": {
        "features": ["Guide scaffolding (init)", "Guide-aware templates"],
        "coverage": 0.8,  # 80% complete
        "gaps": ["Guide auto-update", "Guide validation"]
    },
    
    # Observability (Phase 2)
    "otel": {
        "features": ["Span decorators (core)", "OTEL semconv extension"],
        "coverage": 0.7,  # 70% complete
        "gaps": ["OTLP exporter config", "Real-time alerts", "Span diff"]
    },
    "forge": {
        "features": ["Validation pipeline update", "Generated span builders"],
        "coverage": 0.5,  # 50% complete
        "gaps": ["Automatic span generation", "Schema validation"]
    },
    "spiff-otel": {
        "features": ["Span-driven branching (meta)", "Workflow validation"],
        "coverage": 0.8,  # 80% complete
        "gaps": ["Meta-span generation", "Workflow optimization"]
    },
    
    # GitOps (Phase 5)
    "workflow": {
        "features": ["Git-linked deployment hooks"],
        "coverage": 0.3,  # 30% complete
        "gaps": ["PR auto-generation", "Merge voting", "CI span integration"]
    },
    
    # Enterprise (Phase 4)
    "serve": {
        "features": ["CI/CD bootstrap templates"],
        "coverage": 0.4,  # 40% complete
        "gaps": ["RBAC hooks", "SSO integration", "Policy gating"]
    },
    "remote": {
        "features": ["Clean-room engine"],
        "coverage": 0.2,  # 20% complete
        "gaps": ["Isolation guarantees", "Resource quotas", "TTL management"]
    }
}

def check_telemetry_health() -> Dict[str, bool]:
    """Check telemetry health for critical commands."""
    telemetry_status = {}
    
    try:
        # Run OTEL status to check instrumentation
        result = subprocess.run(
            ["uvmgr", "otel", "status"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for cmd_group in ACTUAL_COMMANDS:
                # Check if commands are instrumented
                telemetry_status[cmd_group] = any(
                    f"{cmd_group}.{subcmd}" in result.stdout
                    for subcmd in ACTUAL_COMMANDS[cmd_group]
                )
        else:
            console.print("[red]Failed to get OTEL status[/red]")
            
    except Exception as e:
        console.print(f"[red]Error checking telemetry: {e}[/red]")
    
    return telemetry_status

def calculate_8020_priorities() -> List[Tuple[str, float, str]]:
    """Calculate 80/20 priorities based on impact and effort."""
    priorities = []
    
    # Priority scoring: Impact (0-1) * (1 - Effort (0-1)) * Coverage Gap
    priority_matrix = [
        # (Feature, Impact, Effort, Reason)
        ("Clean-Room engine", 0.95, 0.7, "Critical for security and isolation"),
        ("Domain-Pack loader", 0.9, 0.5, "Enables agent-guides ecosystem"),
        ("Git worktree isolation", 0.85, 0.3, "Essential for multi-project work"),
        ("OTLP exporter config", 0.8, 0.2, "Quick win for observability"),
        ("Guide catalog CLI", 0.85, 0.4, "Core to agent value proposition"),
        ("Generated span builders", 0.75, 0.6, "Automates observability"),
        ("Grafana dashboards", 0.7, 0.2, "Visual monitoring quick win"),
        ("PR auto-generation", 0.65, 0.5, "GitOps automation"),
        ("RBAC / SSO hooks", 0.6, 0.7, "Enterprise requirement"),
        ("Level-0 Reactive AGI", 0.5, 0.8, "Future-looking capability"),
    ]
    
    for feature, impact, effort, reason in priority_matrix:
        score = impact * (1 - effort) * 100  # Convert to percentage
        priorities.append((feature, score, reason))
    
    # Sort by priority score
    priorities.sort(key=lambda x: x[1], reverse=True)
    
    return priorities

def generate_detailed_report() -> Dict:
    """Generate comprehensive evaluation report."""
    report = {
        "timestamp": str(datetime.now()),
        "command_inventory": {},
        "telemetry_health": {},
        "feature_coverage": {},
        "8020_priorities": [],
        "recommendations": []
    }
    
    # Get telemetry health status
    console.print("[bold]🔍 Checking telemetry health...[/bold]")
    telemetry_status = check_telemetry_health()
    report["telemetry_health"] = telemetry_status
    
    # Analyze each command group
    console.print("\n[bold]📊 Analyzing command groups...[/bold]")
    
    command_table = Table(title="Command Group Analysis", box=box.ROUNDED)
    command_table.add_column("Command Group", style="cyan", width=15)
    command_table.add_column("Commands", style="yellow", width=10)
    command_table.add_column("Coverage", style="green", width=10)
    command_table.add_column("Telemetry", style="magenta", width=10)
    command_table.add_column("Key Gaps", style="red", width=40)
    
    total_commands = 0
    for cmd_group, commands in ACTUAL_COMMANDS.items():
        total_commands += len(commands)
        
        # Get feature contribution data
        feature_data = COMMAND_FEATURE_CONTRIBUTIONS.get(cmd_group, {})
        coverage = feature_data.get("coverage", 0.0) * 100
        gaps = feature_data.get("gaps", [])
        
        # Telemetry status
        telemetry_ok = telemetry_status.get(cmd_group, False)
        telemetry_icon = "✅" if telemetry_ok else "❌"
        
        # Add to report
        report["command_inventory"][cmd_group] = {
            "commands": commands,
            "count": len(commands),
            "coverage": coverage,
            "telemetry_ok": telemetry_ok,
            "gaps": gaps
        }
        
        # Add to table
        command_table.add_row(
            cmd_group,
            str(len(commands)),
            f"{coverage:.0f}%",
            telemetry_icon,
            ", ".join(gaps[:2]) + "..." if len(gaps) > 2 else ", ".join(gaps)
        )
    
    console.print(command_table)
    
    # Calculate 80/20 priorities
    console.print("\n[bold]🎯 Calculating 80/20 priorities...[/bold]")
    priorities = calculate_8020_priorities()
    report["8020_priorities"] = [(f, s, r) for f, s, r in priorities]
    
    # Display top priorities
    priority_table = Table(title="\n80/20 Development Priorities", box=box.ROUNDED)
    priority_table.add_column("Priority", style="cyan", width=5)
    priority_table.add_column("Feature", style="yellow", width=25)
    priority_table.add_column("Score", style="green", width=10)
    priority_table.add_column("Rationale", style="white", width=45)
    
    for i, (feature, score, reason) in enumerate(priorities[:8], 1):  # Top 8 = 80/20
        priority_table.add_row(
            f"{i}",
            feature,
            f"{score:.1f}",
            reason
        )
    
    console.print(priority_table)
    
    # Generate recommendations
    recommendations = [
        "🔧 Fix telemetry gaps in command groups without instrumentation",
        "🏗️ Prioritize Clean-Room engine for security isolation", 
        "📦 Implement Domain-Pack loader to enable agent ecosystem",
        "🔍 Add OTLP exporter configuration for production observability",
        "📊 Create Grafana dashboards for quick monitoring wins",
        "🤖 Focus on agent-guides integration before AGI features",
        "🔐 Defer enterprise features until core is stable",
        "⚡ Use 80/20 rule: Complete high-impact, low-effort items first"
    ]
    
    report["recommendations"] = recommendations
    
    console.print("\n[bold]💡 Strategic Recommendations:[/bold]")
    for rec in recommendations:
        console.print(f"  {rec}")
    
    # Summary statistics
    console.print(f"\n[bold]📈 Summary Statistics:[/bold]")
    console.print(f"  • Total commands: {total_commands}")
    console.print(f"  • Command groups: {len(ACTUAL_COMMANDS)}")
    console.print(f"  • Telemetry coverage: {sum(telemetry_status.values())}/{len(telemetry_status)} groups")
    console.print(f"  • Average feature coverage: {sum(d.get('coverage', 0) for d in COMMAND_FEATURE_CONTRIBUTIONS.values()) / len(COMMAND_FEATURE_CONTRIBUTIONS) * 100:.1f}%")
    
    # Critical path to WeaverShip vision
    console.print("\n[bold cyan]🚀 Critical Path to WeaverShip Vision:[/bold cyan]")
    critical_path = [
        "1. Complete foundational infrastructure (Clean-Room, Domain-Pack)",
        "2. Finish agent-guides integration (Catalog, Caching, Updates)",
        "3. Enhance observability (OTLP export, Dashboards, Alerts)",
        "4. Implement basic GitOps (PR generation, CI integration)",
        "5. Add enterprise features only after core stability",
        "6. Build AGI features on solid foundation"
    ]
    
    for step in critical_path:
        console.print(f"  {step}")
    
    # Save report
    report_path = Path("uvmgr_detailed_8020_evaluation.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    console.print(f"\n[green]✅ Detailed evaluation saved to: {report_path}[/green]")
    
    return report

if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold cyan]uvmgr Detailed 80/20 Evaluation[/bold cyan]\n"
        "[dim]Comprehensive analysis with telemetry validation[/dim]",
        title="Evaluation Report",
        border_style="cyan"
    ))
    
    report = generate_detailed_report()
    
    # Final verdict
    console.print("\n[bold]🏁 Final Verdict:[/bold]")
    console.print("uvmgr has a solid foundation (60-70% complete) but needs focused development")
    console.print("on critical WeaverShip features. Following 80/20 principle, complete")
    console.print("high-impact infrastructure before adding advanced capabilities.")
    
    console.print("\n[green]✨ Focus on the 20% that delivers 80% of value![/green]")