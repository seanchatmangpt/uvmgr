#!/usr/bin/env python3
"""
80/20 Evaluation of uvmgr Commands vs WeaverShip Roadmap
========================================================

This script evaluates all existing uvmgr commands against the WeaverShip 
master roadmap to identify gaps and prioritize development.

Following the 80/20 principle:
- 20% of features provide 80% of value
- Focus on critical path items first
- Identify what's missing for each roadmap phase
"""

import subprocess
import json
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# WeaverShip Roadmap Phases (from Gantt chart)
ROADMAP_PHASES = {
    "0_FOUNDATIONAL": {
        "name": "Foundational Infrastructure",
        "required_features": [
            "Core CLI (Typer)",
            "Clean-Room engine", 
            "Domain-Pack loader",
            "Virtualenv / uv lock",
            "Git worktree isolation",
            "DevContainer & Codespaces",
            "Packaging (PyInstaller)"
        ]
    },
    "1_AGENT_GUIDES": {
        "name": "Agent-Guides Integration",
        "required_features": [
            "Fetch & cache guides pack",
            "Guide catalog CLI",
            "Guide-aware templates",
            "Guide scaffolding (init)",
            "OTEL semconv extension",
            "Validation pipeline update",
            "Guides version pinning",
            "Guides auto-update command"
        ]
    },
    "2_OBSERVABILITY": {
        "name": "Observability & OTEL",
        "required_features": [
            "Span decorators (core)",
            "Generated span builders",
            "Span-driven branching (meta)",
            "OTLP exporter config",
            "Grafana dashboards",
            "Real-time span diff alerts"
        ]
    },
    "3_AGI_MATURITY": {
        "name": "AGI Maturity Ladders",
        "required_features": [
            "Level-0 Reactive",
            "Level-1 Deliberative",
            "Level-2 Meta-Cognitive",
            "Level-3 Reflective Learning",
            "Level-4 Autonomous Gov",
            "Level-5 Self-Improving AGI"
        ]
    },
    "4_ENTERPRISE": {
        "name": "Enterprise Hardening",
        "required_features": [
            "RBAC / SSO hooks",
            "Vault secret injection",
            "Policy-as-code gating",
            "CI/CD bootstrap templates",
            "Artifact registry push",
            "Clean-room quotas & TTL"
        ]
    },
    "5_GITOPS": {
        "name": "GitOps & DevOps",
        "required_features": [
            "PR auto-generation",
            "MergeOracle federated votes",
            "Liquid democracy graph",
            "Git-linked deployment hooks",
            "Trace-linked CI span glue"
        ]
    }
}

def get_all_uvmgr_commands() -> Dict[str, List[str]]:
    """Get all available uvmgr commands."""
    try:
        # Get main commands
        result = subprocess.run(
            ["uvmgr", "--help"],
            capture_output=True,
            text=True
        )
        
        # Parse commands from help output
        commands = {}
        
        # Get list of main command groups
        main_commands = [
            "agent", "ai", "build", "cache", "claude", "deps", "exec",
            "forge", "history", "index", "lint", "otel", "project",
            "release", "remote", "search", "serve", "shell", "spiff-otel",
            "substrate", "tests", "tool", "weaver", "workflow"
        ]
        
        for cmd in main_commands:
            try:
                # Get subcommands for each main command
                sub_result = subprocess.run(
                    ["uvmgr", cmd, "--help"],
                    capture_output=True,
                    text=True
                )
                if sub_result.returncode == 0:
                    # Extract subcommands (simplified parsing)
                    commands[cmd] = parse_subcommands(sub_result.stdout)
            except:
                commands[cmd] = []
                
        return commands
    except Exception as e:
        console.print(f"[red]Error getting commands: {e}[/red]")
        return {}

def parse_subcommands(help_text: str) -> List[str]:
    """Parse subcommands from help text."""
    subcommands = []
    in_commands_section = False
    
    for line in help_text.split('\n'):
        if "Commands:" in line:
            in_commands_section = True
            continue
        if in_commands_section and line.strip():
            if line.startswith("│"):
                parts = line.split("│")
                if len(parts) >= 2:
                    cmd = parts[1].strip()
                    if cmd and not cmd.startswith("-"):
                        subcommands.append(cmd)
    
    return subcommands

def evaluate_command_coverage() -> Dict[str, Dict]:
    """Evaluate which roadmap features are covered by existing commands."""
    commands = get_all_uvmgr_commands()
    
    evaluation = {
        "existing_commands": commands,
        "total_commands": sum(len(subs) for subs in commands.values()),
        "phase_coverage": {},
        "critical_gaps": [],
        "implemented_features": [],
        "8020_analysis": {}
    }
    
    # Map existing commands to roadmap features
    command_feature_map = {
        # Foundational
        "build": ["Packaging (PyInstaller)", "Core CLI (Typer)"],
        "deps": ["Virtualenv / uv lock"],
        "project": ["Core CLI (Typer)"],
        
        # Agent-Guides
        "agent": ["Guide catalog CLI", "Guide-aware templates"],
        "claude": ["Guide scaffolding (init)"],
        
        # Observability
        "otel": ["Span decorators (core)", "OTEL semconv extension"],
        "forge": ["Validation pipeline update"],
        "spiff-otel": ["Span-driven branching (meta)"],
        
        # GitOps
        "workflow": ["Git-linked deployment hooks"],
        
        # Enterprise
        "serve": ["CI/CD bootstrap templates"],
        "remote": ["Clean-room engine"],
    }
    
    # Analyze coverage for each phase
    for phase_id, phase in ROADMAP_PHASES.items():
        covered = []
        missing = []
        
        for feature in phase["required_features"]:
            found = False
            for cmd, features in command_feature_map.items():
                if feature in features and cmd in commands:
                    covered.append(feature)
                    found = True
                    break
            
            if not found:
                missing.append(feature)
        
        coverage_percent = (len(covered) / len(phase["required_features"])) * 100 if phase["required_features"] else 0
        
        evaluation["phase_coverage"][phase_id] = {
            "name": phase["name"],
            "coverage_percent": coverage_percent,
            "covered_features": covered,
            "missing_features": missing,
            "total_features": len(phase["required_features"])
        }
        
        # Identify critical gaps (high-impact missing features)
        if phase_id in ["0_FOUNDATIONAL", "1_AGENT_GUIDES", "2_OBSERVABILITY"]:
            evaluation["critical_gaps"].extend(missing)
    
    # 80/20 Analysis - identify the 20% of commands providing 80% value
    high_value_commands = [
        "otel",        # Core observability
        "agent",       # Agent integration
        "project",     # Project management
        "build",       # Deployment
        "spiff-otel",  # Workflow validation
        "deps",        # Dependency management
        "forge",       # Weaver Forge integration
    ]
    
    evaluation["8020_analysis"] = {
        "high_value_commands": high_value_commands,
        "high_value_coverage": len([c for c in high_value_commands if c in commands]),
        "total_high_value": len(high_value_commands),
        "recommendation": "Focus on completing high-value command features first"
    }
    
    return evaluation

def generate_gap_report(evaluation: Dict) -> None:
    """Generate comprehensive gap analysis report."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]uvmgr 80/20 Command Evaluation[/bold cyan]\n"
        "[dim]Evaluating existing commands against WeaverShip roadmap[/dim]",
        title="Gap Analysis Report",
        border_style="cyan"
    ))
    
    # Summary statistics
    console.print(f"\n[bold]Total Commands:[/bold] {evaluation['total_commands']}")
    console.print(f"[bold]Command Groups:[/bold] {len(evaluation['existing_commands'])}")
    
    # Phase coverage table
    phase_table = Table(title="\nRoadmap Phase Coverage", box=box.ROUNDED)
    phase_table.add_column("Phase", style="cyan", width=30)
    phase_table.add_column("Coverage", style="green", width=10)
    phase_table.add_column("Features", style="yellow", width=15)
    phase_table.add_column("Status", style="white", width=20)
    
    for phase_id, data in evaluation["phase_coverage"].items():
        coverage = data["coverage_percent"]
        status_color = "green" if coverage >= 70 else "yellow" if coverage >= 40 else "red"
        status = "✅ Good" if coverage >= 70 else "⚠️ Partial" if coverage >= 40 else "❌ Critical Gap"
        
        phase_table.add_row(
            data["name"],
            f"[{status_color}]{coverage:.1f}%[/{status_color}]",
            f"{len(data['covered_features'])}/{data['total_features']}",
            f"[{status_color}]{status}[/{status_color}]"
        )
    
    console.print(phase_table)
    
    # Critical gaps
    console.print("\n[bold red]🚨 Critical Gaps (High Priority):[/bold red]")
    for gap in evaluation["critical_gaps"][:10]:  # Top 10 gaps
        console.print(f"  • {gap}")
    
    # 80/20 Analysis
    console.print(f"\n[bold green]📊 80/20 Analysis:[/bold green]")
    analysis = evaluation["8020_analysis"]
    coverage_percent = (analysis["high_value_coverage"] / analysis["total_high_value"]) * 100
    console.print(f"  High-value command coverage: {coverage_percent:.1f}%")
    console.print(f"  Recommendation: {analysis['recommendation']}")
    
    # Missing high-value commands
    console.print("\n[bold]High-Value Commands Status:[/bold]")
    for cmd in analysis["high_value_commands"]:
        exists = cmd in evaluation["existing_commands"]
        status = "✅" if exists else "❌"
        console.print(f"  {status} {cmd}")
    
    # Detailed gap analysis by phase
    console.print("\n[bold]Detailed Gap Analysis:[/bold]")
    
    for phase_id, data in evaluation["phase_coverage"].items():
        if data["missing_features"]:
            console.print(f"\n[yellow]{data['name']}:[/yellow]")
            console.print("  Missing features:")
            for feature in data["missing_features"][:5]:  # Top 5 per phase
                console.print(f"    • {feature}")
    
    # Development priorities
    console.print("\n[bold cyan]🎯 Development Priorities (80/20 Approach):[/bold cyan]")
    
    priorities = [
        ("1️⃣", "Complete Clean-Room engine", "Critical for isolation and security"),
        ("2️⃣", "Implement Domain-Pack loader", "Required for agent-guides integration"),
        ("3️⃣", "Add Git worktree isolation", "Essential for multi-project work"),
        ("4️⃣", "Build Guide catalog CLI", "Core to agent-guides vision"),
        ("5️⃣", "Enhance OTEL span builders", "Critical for observability"),
    ]
    
    for num, priority, reason in priorities:
        console.print(f"  {num} [bold]{priority}[/bold]")
        console.print(f"     [dim]{reason}[/dim]")
    
    # Save detailed report
    report_path = Path("uvmgr_gap_analysis_report.json")
    with open(report_path, 'w') as f:
        json.dump(evaluation, f, indent=2, default=str)
    
    console.print(f"\n[green]✅ Detailed report saved to: {report_path}[/green]")

def run_8020_evaluation():
    """Run the complete 80/20 evaluation."""
    console.print("[bold]🔍 Running uvmgr 80/20 Command Evaluation...[/bold]\n")
    
    # Get current command inventory
    evaluation = evaluate_command_coverage()
    
    # Generate gap report
    generate_gap_report(evaluation)
    
    # Key insights
    console.print("\n[bold]🔑 Key Insights:[/bold]")
    console.print("1. uvmgr has strong foundation but missing critical WeaverShip features")
    console.print("2. Agent-guides integration is partially implemented but incomplete")
    console.print("3. Observability (OTEL) is functional but needs enhancement")
    console.print("4. Enterprise and GitOps features are largely missing")
    console.print("5. Following 80/20: Focus on completing foundational features first")
    
    return evaluation

if __name__ == "__main__":
    evaluation = run_8020_evaluation()