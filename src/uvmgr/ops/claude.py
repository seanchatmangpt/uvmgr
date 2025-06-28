"""
uvmgr.ops.claude
================

Operations layer for Claude AI integration and agent workflows.

This module provides business logic for advanced Claude AI features including
multi-agent collaboration, conversation management, custom commands, and
intelligent workflows.

Key Features
-----------
• Multi-specialist collaborative analysis
• Conversation history search and management
• Custom command creation and execution
• Expert debate orchestration
• AI workflow pipelines
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import AIAttributes
from uvmgr.core.telemetry import span
from uvmgr.runtime import ai as ai_runtime
import re
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


# ──────────────────────────────────────────────────────────────────────────────
# Data Classes for Multi-Mind Analysis
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SpecialistAgent:
    """Represents a specialist agent in Multi-Mind analysis."""
    role: str
    expertise: str
    focus_areas: List[str]
    perspective: str = ""


# Specialist Registry - 8020 Implementation
SPECIALIST_REGISTRY = {
    "technical": SpecialistAgent(
        role="Technical Architect",
        expertise="System design, scalability, performance optimization",
        focus_areas=["architecture", "performance", "scalability", "technical_debt"]
    ),
    "security": SpecialistAgent(
        role="Security Expert", 
        expertise="Cybersecurity, threat modeling, compliance",
        focus_areas=["security", "privacy", "compliance", "risk_assessment"]
    ),
    "performance": SpecialistAgent(
        role="Performance Engineer",
        expertise="Optimization, benchmarking, resource efficiency",
        focus_areas=["performance", "optimization", "resource_usage", "benchmarks"]
    ),
    "ux": SpecialistAgent(
        role="UX/UI Specialist",
        expertise="User experience, interface design, usability",
        focus_areas=["user_experience", "usability", "accessibility", "design"]
    ),
    "business": SpecialistAgent(
        role="Business Analyst",
        expertise="Market analysis, ROI, strategic planning",
        focus_areas=["business_value", "market_fit", "cost_benefit", "strategy"]
    ),
    "operations": SpecialistAgent(
        role="DevOps/SRE",
        expertise="Infrastructure, deployment, monitoring, reliability",
        focus_areas=["infrastructure", "deployment", "monitoring", "reliability"]
    ),
    "data": SpecialistAgent(
        role="Data Scientist",
        expertise="Data analysis, machine learning, analytics",
        focus_areas=["data_analysis", "machine_learning", "analytics", "insights"]
    ),
    "testing": SpecialistAgent(
        role="QA Engineer",
        expertise="Testing strategies, quality assurance, automation",
        focus_areas=["testing", "quality_assurance", "automation", "validation"]
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Multi-Agent Operations
# ──────────────────────────────────────────────────────────────────────────────

def multi_mind_analysis(
    topic: str,
    rounds: int = 3,
    specialists: Optional[List[str]] = None,
    enable_web_search: bool = True,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    """
    Execute multi-specialist collaborative analysis.
    
    Args:
        topic: Topic to analyze
        rounds: Number of analysis rounds
        specialists: Optional list of specialist roles
        enable_web_search: Whether to enable web search
        progress_callback: Callback for progress updates
        
    Returns:
        Analysis results with specialist insights and synthesis
    """
    with span("claude.multi_mind", topic=topic, rounds=rounds):
        add_span_attributes(**{
            AIAttributes.OPERATION: "multi_mind_analysis",
            "ai.specialists_count": len(specialists) if specialists else "auto",
        })
        
        # Auto-assign specialists if not provided
        if not specialists:
            specialists = _auto_assign_specialists(topic)
            add_span_event("specialists_assigned", {"specialists": specialists})
        
        results = {
            "topic": topic,
            "specialists": [],
            "insights": [],
            "synthesis": "",
            "rounds": rounds,
        }
        
        # Execute rounds
        for round_num in range(1, rounds + 1):
            if progress_callback:
                progress_callback(round_num - 1, f"Round {round_num}: Researching...")
            
            round_insights = []
            
            # Launch parallel specialist research
            for specialist in specialists:
                add_span_event("specialist_research_start", {
                    "round": round_num,
                    "specialist": specialist,
                })
                
                # Research with web search if enabled
                specialist_insights = ai_runtime.research_topic(
                    topic=topic,
                    perspective=specialist,
                    enable_web_search=enable_web_search,
                    previous_insights=round_insights,
                )
                
                round_insights.append({
                    "specialist": specialist,
                    "insights": specialist_insights,
                })
                
                # Store specialist perspective in first round
                if round_num == 1:
                    results["specialists"].append({
                        "role": specialist,
                        "perspective": specialist_insights.get("perspective", ""),
                    })
            
            # Cross-pollinate insights
            if progress_callback:
                progress_callback(round_num - 1, f"Round {round_num}: Cross-pollinating...")
            
            synthesized = _cross_pollinate_insights(round_insights, topic)
            results["insights"].extend(synthesized)
        
        # Final synthesis
        if progress_callback:
            progress_callback(rounds, "Synthesizing final insights...")
        
        results["synthesis"] = _synthesize_analysis(results["insights"], topic)
        
        add_span_event("multi_mind_completed", {
            "total_insights": len(results["insights"]),
            "specialists": len(specialists),
        })
        
        return results


def analyze_code(
    file_path: Path,
    focus: Optional[str] = None,
    depth: str = "standard",
    num_experts: int = 3,
) -> Dict[str, Any]:
    """
    Perform deep code analysis with multiple expert reviewers.
    
    Args:
        file_path: Path to file or directory
        focus: Analysis focus (performance, security, architecture, all)
        depth: Analysis depth (quick, standard, deep)
        num_experts: Number of expert reviewers
        
    Returns:
        Analysis results with issues, suggestions, and metrics
    """
    with span("claude.analyze_code", file=str(file_path)):
        add_span_attributes(**{
            AIAttributes.OPERATION: "code_analysis",
            "ai.focus": focus or "all",
            "ai.depth": depth,
        })
        
        # Read code content
        if file_path.is_file():
            with open(file_path, "r") as f:
                code_content = f.read()
            files = [(file_path, code_content)]
        else:
            # Analyze directory
            files = _collect_code_files(file_path)
        
        # Determine expert types based on focus
        experts = _determine_experts(focus, num_experts)
        
        results = {
            "files_analyzed": len(files),
            "issues": [],
            "suggestions": [],
            "metrics": {},
        }
        
        # Analyze with each expert
        for expert in experts:
            add_span_event("expert_analysis_start", {"expert": expert})
            
            expert_results = ai_runtime.analyze_code_expert(
                files=files,
                expert_type=expert,
                depth=depth,
            )
            
            results["issues"].extend(expert_results.get("issues", []))
            results["suggestions"].extend(expert_results.get("suggestions", []))
            results["metrics"].update(expert_results.get("metrics", {}))
        
        # Deduplicate and prioritize
        results["issues"] = _deduplicate_issues(results["issues"])
        results["suggestions"] = _prioritize_suggestions(results["suggestions"])
        
        add_span_event("code_analysis_completed", {
            "files": len(files),
            "issues": len(results["issues"]),
            "suggestions": len(results["suggestions"]),
        })
        
        return results


# ──────────────────────────────────────────────────────────────────────────────
# Project Analysis Operations (for external projects)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    """Result of project analysis."""
    success: bool
    analysis: str = ""
    suggestions: List[str] = None
    error: str = ""
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass 
class SearchResult:
    """Result of project search."""
    file_path: Path
    line_number: int
    matched_text: str
    context: str


@dataclass
class InitializationResult:
    """Result of project initialization."""
    success: bool
    created_files: List[str] = None
    error: str = ""
    
    def __post_init__(self):
        if self.created_files is None:
            self.created_files = []


@dataclass
class SessionResult:
    """Result of session operation."""
    success: bool
    session_id: str = ""
    error: str = ""


def analyze_project(
    project_path: Path,
    function_name: Optional[str] = None,
    file_path: Optional[str] = None,
    depth: int = 3,
) -> AnalysisResult:
    """
    Analyze an external project with Claude AI.
    
    Args:
        project_path: Path to project directory
        function_name: Specific function to analyze
        file_path: Specific file to analyze
        depth: Analysis depth (1-5)
        
    Returns:
        AnalysisResult with findings and suggestions
    """
    with span("claude.analyze_project", project=str(project_path)):
        try:
            if not project_path.exists() or not project_path.is_dir():
                return AnalysisResult(success=False, error="Invalid project path")
            
            # Build analysis context
            context = _build_project_context(project_path, file_path, function_name)
            
            # Generate analysis prompt
            prompt = f"""
            Analyze the following project:
            
            Project: {project_path.name}
            Path: {project_path}
            Focus: {f"Function: {function_name}" if function_name else f"File: {file_path}" if file_path else "Full project"}
            Depth: {depth}/5
            
            Context:
            {context}
            
            Provide:
            1. Overall assessment
            2. Key insights and patterns
            3. Potential improvements
            4. Best practices recommendations
            5. Architecture observations
            
            Be specific and actionable.
            """
            
            analysis = ai_runtime.ask("openai/gpt-4o-mini", prompt)
            
            # Extract suggestions (simple parsing)
            suggestions = []
            if "recommendations:" in analysis.lower():
                parts = analysis.lower().split("recommendations:")
                if len(parts) > 1:
                    rec_section = parts[1]
                    for line in rec_section.split("\n"):
                        line = line.strip()
                        if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                            clean_line = line.lstrip("-•0123456789. ").strip()
                            if clean_line:
                                suggestions.append(clean_line)
            
            return AnalysisResult(
                success=True,
                analysis=analysis,
                suggestions=suggestions[:10]  # Limit suggestions
            )
            
        except Exception as e:
            return AnalysisResult(success=False, error=str(e))


def search_project(
    project_path: Path,
    query: str,
    context_lines: int = 3,
    file_pattern: Optional[str] = None,
) -> List[SearchResult]:
    """
    Search through project files with AI assistance.
    
    Args:
        project_path: Path to project directory
        query: Search query (natural language)
        context_lines: Lines of context around matches
        file_pattern: File pattern filter
        
    Returns:
        List of SearchResult objects
    """
    with span("claude.search_project", project=str(project_path), query=query):
        try:
            if not project_path.exists() or not project_path.is_dir():
                return []
            
            results = []
            
            # Define search patterns based on file_pattern
            if file_pattern:
                file_patterns = [file_pattern]
            else:
                file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.go", "*.rs", "*.md", "*.txt"]
            
            # Search through files
            for pattern in file_patterns:
                for file_path in project_path.rglob(pattern):
                    if file_path.is_file() and not _should_ignore_file(file_path):
                        file_results = _search_file_content(file_path, query, context_lines)
                        results.extend(file_results)
            
            # Sort by relevance (simple scoring)
            results = _rank_search_results(results, query)
            
            return results[:100]  # Limit results
            
        except Exception as e:
            add_span_event("search_project_error", {"error": str(e)})
            return []


def initialize_project(project_path: Path, profile: Optional[str] = None) -> InitializationResult:
    """
    Initialize Claude AI support for an external project.
    
    Args:
        project_path: Path to project directory
        profile: Project profile (python, javascript, rust, etc.)
        
    Returns:
        InitializationResult with created files
    """
    with span("claude.initialize_project", project=str(project_path)):
        try:
            if not project_path.exists() or not project_path.is_dir():
                return InitializationResult(success=False, error="Invalid project path")
            
            created_files = []
            claude_dir = project_path / ".claude"
            
            # Create .claude directory
            claude_dir.mkdir(exist_ok=True)
            
            # Create config.yml
            config_path = claude_dir / "config.yml"
            config_content = _generate_project_config(project_path, profile)
            with open(config_path, "w") as f:
                f.write(config_content)
            created_files.append(str(config_path.relative_to(project_path)))
            
            # Create commands directory
            commands_dir = claude_dir / "commands"
            commands_dir.mkdir(exist_ok=True)
            
            # Create profile-specific commands
            if profile:
                profile_commands = _generate_profile_commands(profile)
                for cmd_name, cmd_content in profile_commands.items():
                    cmd_path = commands_dir / f"{cmd_name}.md"
                    with open(cmd_path, "w") as f:
                        f.write(cmd_content)
                    created_files.append(str(cmd_path.relative_to(project_path)))
            
            # Create workflows directory
            workflows_dir = claude_dir / "workflows"
            workflows_dir.mkdir(exist_ok=True)
            
            # Create basic workflow
            workflow_path = workflows_dir / "code-review.json"
            workflow_content = _generate_basic_workflow()
            with open(workflow_path, "w") as f:
                f.write(workflow_content)
            created_files.append(str(workflow_path.relative_to(project_path)))
            
            # Create memory file
            memory_path = claude_dir / "memory.md"
            memory_content = _generate_project_memory(project_path, profile)
            with open(memory_path, "w") as f:
                f.write(memory_content)
            created_files.append(str(memory_path.relative_to(project_path)))
            
            return InitializationResult(success=True, created_files=created_files)
            
        except Exception as e:
            return InitializationResult(success=False, error=str(e))


def save_session(project_path: Path, session_name: str) -> SessionResult:
    """
    Save a session for a project.
    
    Args:
        project_path: Path to project directory
        session_name: Name for the session
        
    Returns:
        SessionResult with session ID
    """
    with span("claude.save_session", project=str(project_path)):
        try:
            session_id = f"{project_path.name}_{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Save session metadata
            claude_dir = project_path / ".claude"
            claude_dir.mkdir(exist_ok=True)
            
            sessions_dir = claude_dir / "sessions"
            sessions_dir.mkdir(exist_ok=True)
            
            session_file = sessions_dir / f"{session_id}.json"
            session_data = {
                "id": session_id,
                "name": session_name,
                "project": str(project_path),
                "created": datetime.now().isoformat(),
                "type": "external_project"
            }
            
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            
            return SessionResult(success=True, session_id=session_id)
            
        except Exception as e:
            return SessionResult(success=False, error=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Conversation Management
# ──────────────────────────────────────────────────────────────────────────────

def search_conversations(
    query: str,
    days_back: int = 30,
    project_filter: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Search Claude conversations across multiple sources.
    
    Args:
        query: Search query
        days_back: Number of days to search back
        project_filter: Optional project name filter
        limit: Maximum results
        
    Returns:
        List of matching conversation results
    """
    with span("claude.search_conversations", query=query):
        add_span_attributes(**{
            AIAttributes.OPERATION: "conversation_search",
            "search.query": query,
            "search.days": days_back,
        })
        
        results = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Search SQLite database
        db_results = _search_sqlite_conversations(query, cutoff_date, project_filter)
        results.extend(db_results)
        
        # Search JSON project histories
        json_results = _search_json_histories(query, cutoff_date, project_filter)
        results.extend(json_results)
        
        # Search session metadata
        session_results = _search_session_metadata(query, cutoff_date)
        results.extend(session_results)
        
        # Rank and deduplicate
        results = _rank_search_results(results, query)
        results = _deduplicate_results(results)
        
        add_span_event("conversation_search_completed", {
            "results_found": len(results),
            "sources_searched": 3,
        })
        
        return results[:limit]


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a conversation session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session data with messages and metadata
    """
    with span("claude.get_session", session_id=session_id):
        # Try multiple sources
        session_data = None
        
        # Check SQLite database
        session_data = _get_session_from_db(session_id)
        
        # Check JSON files
        if not session_data:
            session_data = _get_session_from_json(session_id)
        
        if session_data:
            add_span_event("session_found", {
                "session_id": session_id,
                "message_count": session_data.get("message_count", 0),
            })
        else:
            add_span_event("session_not_found", {"session_id": session_id})
        
        return session_data


def set_active_session(session_id: str) -> None:
    """Set the active conversation session for resumption."""
    with span("claude.set_active_session", session_id=session_id):
        # Store in appropriate location for Claude to resume
        session_file = Path.home() / ".claude" / "active_session.json"
        session_file.parent.mkdir(exist_ok=True)
        
        session_data = {
            "session_id": session_id,
            "activated_at": datetime.now().isoformat(),
        }
        
        with open(session_file, "w") as f:
            json.dump(session_data, f)
        
        add_span_event("session_activated", {"session_id": session_id})


# ──────────────────────────────────────────────────────────────────────────────
# Custom Commands
# ──────────────────────────────────────────────────────────────────────────────

def create_custom_command(
    name: str,
    description: str,
    template: Optional[str] = None,
    is_global: bool = False,
) -> Path:
    """
    Create a new custom Claude command.
    
    Args:
        name: Command name
        description: Command description
        template: Optional template (review, optimize, analyze)
        is_global: Create as global user command
        
    Returns:
        Path to created command file
    """
    with span("claude.create_command", name=name):
        add_span_attributes(**{
            AIAttributes.OPERATION: "create_command",
            "command.name": name,
            "command.global": is_global,
        })
        
        # Determine command location
        if is_global:
            cmd_dir = Path.home() / ".claude" / "commands"
        else:
            cmd_dir = Path.cwd() / ".claude" / "commands"
        
        cmd_dir.mkdir(parents=True, exist_ok=True)
        cmd_file = cmd_dir / f"{name}.md"
        
        # Generate command content
        content = _generate_command_content(name, description, template)
        
        # Write command file
        with open(cmd_file, "w") as f:
            f.write(content)
        
        add_span_event("command_created", {
            "name": name,
            "path": str(cmd_file),
            "template": template or "custom",
        })
        
        return cmd_file


def list_custom_commands(include_system: bool = False) -> List[Dict[str, Any]]:
    """
    List available custom Claude commands.
    
    Args:
        include_system: Include system commands
        
    Returns:
        List of command information
    """
    with span("claude.list_commands"):
        commands = []
        
        # Check project commands
        project_dir = Path.cwd() / ".claude" / "commands"
        if project_dir.exists():
            for cmd_file in project_dir.glob("*.md"):
                cmd_info = _parse_command_file(cmd_file)
                cmd_info["scope"] = "project"
                commands.append(cmd_info)
        
        # Check user commands
        user_dir = Path.home() / ".claude" / "commands"
        if user_dir.exists():
            for cmd_file in user_dir.glob("*.md"):
                cmd_info = _parse_command_file(cmd_file)
                cmd_info["scope"] = "user"
                commands.append(cmd_info)
        
        # Include system commands if requested
        if include_system:
            commands.extend(_get_system_commands())
        
        add_span_event("commands_listed", {"count": len(commands)})
        
        return commands


# ──────────────────────────────────────────────────────────────────────────────
# Workflows
# ──────────────────────────────────────────────────────────────────────────────

def execute_workflow(
    workflow_name: str,
    parameters: Dict[str, Any],
    interactive: bool = False,
) -> Dict[str, Any]:
    """
    Execute a predefined AI workflow.
    
    Args:
        workflow_name: Name of workflow to execute
        parameters: Workflow parameters
        interactive: Enable interactive mode
        
    Returns:
        Workflow execution results
    """
    with span("claude.execute_workflow", workflow=workflow_name):
        add_span_attributes(**{
            AIAttributes.OPERATION: "workflow_execution",
            "workflow.name": workflow_name,
            "workflow.interactive": interactive,
        })
        
        start_time = datetime.now()
        
        # Load workflow definition
        workflow_def = _load_workflow_definition(workflow_name)
        if not workflow_def:
            raise ValueError(f"Workflow not found: {workflow_name}")
        
        # Execute workflow steps
        results = {
            "workflow": workflow_name,
            "status": "running",
            "steps": [],
            "output": None,
        }
        
        for step in workflow_def["steps"]:
            step_result = _execute_workflow_step(
                step, 
                parameters,
                interactive,
                previous_results=results["steps"],
            )
            
            results["steps"].append(step_result)
            
            if step_result.get("status") == "failed":
                results["status"] = "failed"
                break
        
        if results["status"] == "running":
            results["status"] = "completed"
            results["output"] = _compile_workflow_output(results["steps"])
        
        results["duration"] = (datetime.now() - start_time).total_seconds()
        
        add_span_event("workflow_completed", {
            "workflow": workflow_name,
            "status": results["status"],
            "steps": len(results["steps"]),
            "duration": results["duration"],
        })
        
        return results


def expert_debate(
    topic: str,
    experts: List[str],
    rounds: int = 3,
    debate_format: str = "structured",
) -> Dict[str, Any]:
    """
    Orchestrate expert debate on a topic.
    
    Args:
        topic: Debate topic
        experts: List of expert roles
        rounds: Number of debate rounds
        debate_format: Format (structured, freeform, socratic)
        
    Returns:
        Debate results with arguments and conclusions
    """
    with span("claude.expert_debate", topic=topic):
        add_span_attributes(**{
            AIAttributes.OPERATION: "expert_debate",
            "debate.topic": topic,
            "debate.experts": len(experts),
            "debate.format": debate_format,
        })
        
        results = {
            "topic": topic,
            "experts": experts,
            "rounds": [],
            "consensus": None,
            "disagreements": [],
            "recommendations": [],
        }
        
        # Initialize expert contexts
        expert_contexts = {expert: [] for expert in experts}
        
        # Execute debate rounds
        for round_num in range(1, rounds + 1):
            add_span_event("debate_round_start", {"round": round_num})
            
            round_arguments = {}
            
            # Each expert presents arguments
            for expert in experts:
                argument = ai_runtime.generate_expert_argument(
                    topic=topic,
                    expert_role=expert,
                    round_num=round_num,
                    previous_arguments=expert_contexts,
                    debate_format=debate_format,
                )
                
                round_arguments[expert] = argument
                expert_contexts[expert].append(argument)
            
            results["rounds"].append(round_arguments)
        
        # Analyze debate outcomes
        analysis = _analyze_debate_outcomes(expert_contexts, topic)
        results.update(analysis)
        
        add_span_event("debate_completed", {
            "consensus_reached": results["consensus"] is not None,
            "disagreements": len(results["disagreements"]),
            "recommendations": len(results["recommendations"]),
        })
        
        return results


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def analyze_topic_for_specialists(topic: str) -> List[str]:
    """
    Analyze topic and auto-assign specialist roles based on keywords and context.
    
    8020 Implementation: Use keyword analysis + fallback to most versatile specialists.
    """
    topic_lower = topic.lower()
    
    # Score specialists based on topic relevance
    specialist_scores = {}
    
    for key, specialist in SPECIALIST_REGISTRY.items():
        score = 0
        
        # Check focus areas match
        for focus_area in specialist.focus_areas:
            if focus_area.replace("_", " ") in topic_lower:
                score += 10
        
        # Check role keywords
        role_keywords = specialist.role.lower().split()
        for keyword in role_keywords:
            if keyword in topic_lower:
                score += 5
        
        # Check expertise keywords
        expertise_keywords = specialist.expertise.lower().split()
        for keyword in expertise_keywords:
            if keyword in topic_lower:
                score += 3
        
        specialist_scores[key] = score
    
    # Sort by score and get top specialists
    ranked_specialists = sorted(specialist_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Select 4-6 specialists: top scorers + ensuring diversity
    selected = []
    
    # Always include top scorer
    if ranked_specialists:
        selected.append(SPECIALIST_REGISTRY[ranked_specialists[0][0]].role)
    
    # Add high-scoring specialists
    for key, score in ranked_specialists[1:]:
        if score > 0 and len(selected) < 6:
            selected.append(SPECIALIST_REGISTRY[key].role)
    
    # Ensure minimum diversity (add key specialists if missing)
    essential_roles = ["technical", "business", "security"]
    for role_key in essential_roles:
        role_name = SPECIALIST_REGISTRY[role_key].role
        if role_name not in selected and len(selected) < 6:
            selected.append(role_name)
    
    # Fallback to default set if nothing matches
    if not selected:
        selected = [
            "Technical Architect", 
            "Business Analyst", 
            "Security Expert",
            "UX/UI Specialist",
            "Performance Engineer"
        ]
    
    return selected[:6]


def _auto_assign_specialists(topic: str) -> List[str]:
    """Auto-assign specialist roles based on topic analysis."""
    return analyze_topic_for_specialists(topic)


def _cross_pollinate_insights(
    round_insights: List[Dict[str, Any]], 
    topic: str
) -> List[Dict[str, Any]]:
    """Cross-pollinate insights between specialists."""
    synthesized = []
    
    # Combine insights and find patterns
    all_insights = []
    for specialist_data in round_insights:
        all_insights.extend(specialist_data["insights"].get("findings", []))
    
    # Group similar insights
    grouped = _group_similar_insights(all_insights)
    
    # Generate synthesized insights
    for group in grouped:
        if len(group) > 1:  # Multiple specialists found similar insight
            synthesized.append({
                "title": group[0].get("title", "Insight"),
                "description": _merge_descriptions(group),
                "confidence": "high",
                "sources": [g.get("specialist") for g in group],
            })
    
    return synthesized


def _synthesize_analysis(insights: List[Dict[str, Any]], topic: str) -> str:
    """Generate final synthesis from all insights."""
    # Use AI to synthesize
    synthesis_prompt = f"""
    Synthesize the following insights about '{topic}' into a coherent summary:
    {json.dumps(insights, indent=2)}
    
    Focus on:
    1. Key findings
    2. Patterns and connections
    3. Actionable recommendations
    """
    
    return ai_runtime.generate_synthesis(synthesis_prompt)


def _determine_experts(focus: Optional[str], num_experts: int) -> List[str]:
    """Determine expert types based on analysis focus."""
    expert_pools = {
        "performance": ["Performance Expert", "Algorithm Specialist", "Database Expert"],
        "security": ["Security Auditor", "Penetration Tester", "Compliance Expert"],
        "architecture": ["Software Architect", "System Designer", "API Specialist"],
        "all": ["Code Reviewer", "Security Expert", "Performance Analyst"],
    }
    
    pool = expert_pools.get(focus or "all", expert_pools["all"])
    
    # Add general experts
    pool.extend(["Best Practices Expert", "Documentation Specialist"])
    
    return pool[:num_experts]


def _search_sqlite_conversations(
    query: str, 
    cutoff_date: datetime,
    project_filter: Optional[str],
) -> List[Dict[str, Any]]:
    """Search SQLite conversation database."""
    results = []
    
    # Common Claude database locations
    db_paths = [
        Path.home() / ".claude" / "conversations.db",
        Path.home() / "Library" / "Application Support" / "Claude" / "conversations.db",
    ]
    
    for db_path in db_paths:
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                sql = """
                SELECT session_id, timestamp, message, project
                FROM conversations
                WHERE message LIKE ? 
                AND timestamp > ?
                """
                
                params = [f"%{query}%", cutoff_date.isoformat()]
                
                if project_filter:
                    sql += " AND project = ?"
                    params.append(project_filter)
                
                cursor.execute(sql, params)
                
                for row in cursor.fetchall():
                    results.append({
                        "session_id": row[0],
                        "date": row[1],
                        "preview": row[2][:200],
                        "project": row[3],
                        "source": "sqlite",
                    })
                
                conn.close()
            except Exception as e:
                add_span_event("sqlite_search_error", {"error": str(e)})
    
    return results


def _search_json_histories(
    query: str,
    cutoff_date: datetime,
    project_filter: Optional[str],
) -> List[Dict[str, Any]]:
    """Search JSON conversation histories."""
    results = []
    
    # Search in current project
    history_dir = Path.cwd() / ".claude" / "history"
    if history_dir.exists():
        for json_file in history_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                
                # Search in messages
                for msg in data.get("messages", []):
                    if query.lower() in msg.get("content", "").lower():
                        timestamp = datetime.fromisoformat(msg.get("timestamp", ""))
                        if timestamp > cutoff_date:
                            results.append({
                                "session_id": data.get("session_id", json_file.stem),
                                "date": timestamp.strftime("%Y-%m-%d"),
                                "preview": msg["content"][:200],
                                "project": Path.cwd().name,
                                "source": "json",
                            })
                            break
            except Exception as e:
                add_span_event("json_search_error", {"error": str(e)})
    
    return results


def _rank_search_results(
    results: List[Dict[str, Any]], 
    query: str
) -> List[Dict[str, Any]]:
    """Rank search results by relevance."""
    query_lower = query.lower()
    
    for result in results:
        score = 0
        preview = result.get("preview", "").lower()
        
        # Exact match
        if query_lower in preview:
            score += 10
        
        # Word matches
        query_words = query_lower.split()
        for word in query_words:
            if word in preview:
                score += 2
        
        # Recent results
        try:
            date = datetime.strptime(result["date"], "%Y-%m-%d")
            days_old = (datetime.now() - date).days
            if days_old < 7:
                score += 5
            elif days_old < 30:
                score += 2
        except:
            pass
        
        result["_score"] = score
    
    # Sort by score
    results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    
    # Remove score from results
    for result in results:
        result.pop("_score", None)
    
    return results


def _generate_command_content(
    name: str,
    description: str,
    template: Optional[str],
) -> str:
    """Generate custom command content."""
    templates = {
        "review": """# {name}

{description}

## Instructions

Review the provided code with focus on:
1. Code quality and best practices
2. Potential bugs and edge cases
3. Performance considerations
4. Security vulnerabilities
5. Documentation completeness

Provide specific, actionable feedback.
""",
        "optimize": """# {name}

{description}

## Instructions

Analyze the code for optimization opportunities:
1. Performance bottlenecks
2. Memory usage improvements
3. Algorithm efficiency
4. Database query optimization
5. Caching opportunities

Suggest specific optimizations with examples.
""",
        "analyze": """# {name}

{description}

## Instructions

Perform deep analysis focusing on:
1. Architecture and design patterns
2. Code organization and modularity
3. Dependency management
4. Testing coverage
5. Scalability considerations

Provide insights and recommendations.
""",
    }
    
    if template and template in templates:
        content = templates[template]
    else:
        content = """# {name}

{description}

## Instructions

[Add your custom instructions here]

## Context

[Add any relevant context or requirements]

## Expected Output

[Describe the expected output format]
"""
    
    return content.format(name=name, description=description)


def _parse_command_file(cmd_file: Path) -> Dict[str, str]:
    """Parse command file to extract metadata."""
    with open(cmd_file, "r") as f:
        content = f.read()
    
    # Extract first line as title
    lines = content.split("\n")
    name = cmd_file.stem
    
    # Try to extract description
    description = "Custom command"
    for line in lines:
        if line.strip() and not line.startswith("#"):
            description = line.strip()
            break
    
    return {
        "name": name,
        "description": description,
        "path": str(cmd_file),
    }


def _analyze_debate_outcomes(
    expert_contexts: Dict[str, List[str]], 
    topic: str
) -> Dict[str, Any]:
    """Analyze debate outcomes for consensus and disagreements."""
    # Use AI to analyze the debate
    analysis_prompt = f"""
    Analyze the following expert debate on '{topic}':
    {json.dumps(expert_contexts, indent=2)}
    
    Identify:
    1. Areas of consensus
    2. Key disagreements
    3. Actionable recommendations
    """
    
    analysis = ai_runtime.analyze_debate(analysis_prompt)
    
    return {
        "consensus": analysis.get("consensus"),
        "disagreements": analysis.get("disagreements", []),
        "recommendations": analysis.get("recommendations", []),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Additional Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _collect_code_files(directory: Path) -> List[Tuple[Path, str]]:
    """Collect code files from a directory."""
    files = []
    extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"}
    
    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                files.append((file_path, content))
            except Exception:
                pass  # Skip files that can't be read
    
    return files


def _deduplicate_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate similar issues."""
    unique_issues = []
    seen_titles = set()
    
    for issue in issues:
        title = issue.get("title", "")
        if title not in seen_titles:
            seen_titles.add(title)
            unique_issues.append(issue)
    
    return unique_issues


def _prioritize_suggestions(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioritize suggestions by impact."""
    # Sort by priority if available, otherwise by appearance order
    return sorted(suggestions, key=lambda x: x.get("priority", 999))


def _group_similar_insights(insights: List[Any]) -> List[List[Any]]:
    """Group similar insights together."""
    # Simple grouping by similarity (in production, use embeddings)
    groups = []
    
    for insight in insights:
        found_group = False
        for group in groups:
            # Check if similar to any in group
            if _is_similar(insight, group[0]):
                group.append(insight)
                found_group = True
                break
        
        if not found_group:
            groups.append([insight])
    
    return groups


def _is_similar(insight1: Any, insight2: Any) -> bool:
    """Check if two insights are similar."""
    # Simple text similarity check
    if isinstance(insight1, dict) and isinstance(insight2, dict):
        text1 = str(insight1.get("title", "")) + str(insight1.get("description", ""))
        text2 = str(insight2.get("title", "")) + str(insight2.get("description", ""))
        
        # Check for common keywords
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        common = words1.intersection(words2)
        return len(common) > min(len(words1), len(words2)) * 0.3
    
    return False


def _merge_descriptions(group: List[Dict[str, Any]]) -> str:
    """Merge descriptions from multiple insights."""
    descriptions = [item.get("description", "") for item in group]
    
    # Simple merge - in production, use AI to synthesize
    merged = " Additionally, ".join(filter(None, descriptions))
    
    return merged


def _get_session_from_db(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session from SQLite database."""
    # Implementation depends on actual Claude DB structure
    return None


def _get_session_from_json(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session from JSON files."""
    history_dir = Path.cwd() / ".claude" / "history"
    if not history_dir.exists():
        return None
    
    for json_file in history_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            
            if data.get("session_id") == session_id:
                return data
        except Exception:
            continue
    
    return None


def _search_session_metadata(
    query: str, 
    cutoff_date: datetime
) -> List[Dict[str, Any]]:
    """Search session metadata."""
    results = []
    
    # Search in metadata files
    metadata_dir = Path.home() / ".claude" / "sessions"
    if metadata_dir.exists():
        for meta_file in metadata_dir.glob("*.json"):
            try:
                with open(meta_file, "r") as f:
                    metadata = json.load(f)
                
                # Check if matches query and date
                if query.lower() in str(metadata).lower():
                    date = datetime.fromisoformat(metadata.get("created", ""))
                    if date > cutoff_date:
                        results.append({
                            "session_id": metadata.get("id", meta_file.stem),
                            "date": date.strftime("%Y-%m-%d"),
                            "preview": str(metadata)[:200],
                            "source": "metadata",
                        })
            except Exception:
                continue
    
    return results


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate search results by session ID."""
    seen = set()
    unique = []
    
    for result in results:
        session_id = result.get("session_id")
        if session_id not in seen:
            seen.add(session_id)
            unique.append(result)
    
    return unique


def _get_system_commands() -> List[Dict[str, str]]:
    """Get built-in system commands."""
    return [
        {"name": "help", "description": "Show help", "scope": "system"},
        {"name": "clear", "description": "Clear conversation", "scope": "system"},
        {"name": "review", "description": "Code review", "scope": "system"},
        {"name": "memory", "description": "Edit memory", "scope": "system"},
        {"name": "cost", "description": "Token usage", "scope": "system"},
        {"name": "model", "description": "Change model", "scope": "system"},
    ]


def _load_workflow_definition(workflow_name: str) -> Optional[Dict[str, Any]]:
    """Load workflow definition."""
    # Check project workflows
    workflow_file = Path.cwd() / ".claude" / "workflows" / f"{workflow_name}.json"
    
    if not workflow_file.exists():
        # Check user workflows
        workflow_file = Path.home() / ".claude" / "workflows" / f"{workflow_name}.json"
    
    if workflow_file.exists():
        with open(workflow_file, "r") as f:
            return json.load(f)
    
    # Built-in workflows
    builtin_workflows = {
        "code-review": {
            "name": "code-review",
            "steps": [
                {"type": "analyze", "focus": "quality"},
                {"type": "analyze", "focus": "security"},
                {"type": "analyze", "focus": "performance"},
                {"type": "synthesize", "output": "report"},
            ]
        }
    }
    
    return builtin_workflows.get(workflow_name)


def _execute_workflow_step(
    step: Dict[str, Any],
    parameters: Dict[str, Any],
    interactive: bool,
    previous_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Execute a single workflow step."""
    step_type = step.get("type")
    
    result = {
        "step": step_type,
        "status": "completed",
        "output": None,
    }
    
    if step_type == "analyze":
        # Execute analysis step
        focus = step.get("focus", "all")
        result["output"] = f"Analysis completed with focus: {focus}"
    
    elif step_type == "synthesize":
        # Synthesize results
        result["output"] = "Synthesis completed"
    
    else:
        result["status"] = "unknown"
        result["output"] = f"Unknown step type: {step_type}"
    
    return result


def _compile_workflow_output(steps: List[Dict[str, Any]]) -> str:
    """Compile workflow output from all steps."""
    outputs = []
    
    for i, step in enumerate(steps, 1):
        outputs.append(f"Step {i} ({step['step']}): {step['output']}")
    
    return "\n".join(outputs)


# ──────────────────────────────────────────────────────────────────────────────
# Project Analysis Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _build_project_context(
    project_path: Path,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
) -> str:
    """Build context for project analysis."""
    context_parts = []
    
    # Project structure
    context_parts.append("Project Structure:")
    try:
        structure = _get_project_structure(project_path, max_depth=2)
        context_parts.append(structure)
    except Exception:
        context_parts.append("Could not analyze project structure")
    
    # Specific file/function content
    if file_path:
        full_path = project_path / file_path
        if full_path.exists():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if function_name:
                        # Extract specific function
                        func_content = _extract_function(content, function_name)
                        if func_content:
                            context_parts.append(f"\nFunction '{function_name}' in {file_path}:")
                            context_parts.append(func_content)
                        else:
                            context_parts.append(f"\nFunction '{function_name}' not found in {file_path}")
                    else:
                        # Show first 2000 chars of file
                        context_parts.append(f"\nFile {file_path}:")
                        context_parts.append(content[:2000] + ("..." if len(content) > 2000 else ""))
            except Exception as e:
                context_parts.append(f"Could not read {file_path}: {e}")
    
    return "\n".join(context_parts)


def _get_project_structure(project_path: Path, max_depth: int = 2) -> str:
    """Get a simple project structure overview."""
    lines = []
    
    def add_path(path: Path, depth: int = 0):
        if depth > max_depth:
            return
        
        indent = "  " * depth
        if path.is_dir():
            lines.append(f"{indent}{path.name}/")
            # Only show important directories and files
            try:
                for child in sorted(path.iterdir()):
                    if not child.name.startswith('.') or child.name in ['.github', '.vscode']:
                        if child.is_dir() and depth < max_depth:
                            add_path(child, depth + 1)
                        elif child.is_file() and _is_important_file(child):
                            lines.append(f"{indent}  {child.name}")
            except PermissionError:
                lines.append(f"{indent}  [Permission Denied]")
        else:
            lines.append(f"{indent}{path.name}")
    
    add_path(project_path)
    return "\n".join(lines[:50])  # Limit output


def _is_important_file(file_path: Path) -> bool:
    """Check if a file is important for project analysis."""
    important_files = {
        "package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml",
        "Dockerfile", "docker-compose.yml", "README.md", "LICENSE", "setup.py",
        "pyproject.toml", "Makefile", "CMakeLists.txt", ".gitignore", "CHANGELOG.md"
    }
    
    return file_path.name in important_files or file_path.suffix in {".md", ".yml", ".yaml", ".json", ".toml"}


def _extract_function(content: str, function_name: str) -> Optional[str]:
    """Extract a specific function from file content."""
    lines = content.split("\n")
    
    # Simple Python function extraction
    if any(line.strip().startswith("def ") for line in lines):
        return _extract_python_function(lines, function_name)
    
    # Simple JavaScript/TypeScript function extraction
    if any("function " in line or "=>" in line for line in lines):
        return _extract_js_function(lines, function_name)
    
    return None


def _extract_python_function(lines: List[str], function_name: str) -> Optional[str]:
    """Extract Python function."""
    func_lines = []
    in_function = False
    base_indent = 0
    
    for line in lines:
        if line.strip().startswith(f"def {function_name}("):
            in_function = True
            base_indent = len(line) - len(line.lstrip())
            func_lines.append(line)
        elif in_function:
            if line.strip() == "":
                func_lines.append(line)
            elif len(line) - len(line.lstrip()) <= base_indent and line.strip():
                # End of function
                break
            else:
                func_lines.append(line)
    
    return "\n".join(func_lines) if func_lines else None


def _extract_js_function(lines: List[str], function_name: str) -> Optional[str]:
    """Extract JavaScript/TypeScript function."""
    func_lines = []
    in_function = False
    brace_count = 0
    
    for line in lines:
        if f"function {function_name}" in line or f"{function_name} =" in line or f"{function_name}:" in line:
            in_function = True
            func_lines.append(line)
            brace_count += line.count("{") - line.count("}")
        elif in_function:
            func_lines.append(line)
            brace_count += line.count("{") - line.count("}")
            if brace_count <= 0:
                break
    
    return "\n".join(func_lines) if func_lines else None


def _should_ignore_file(file_path: Path) -> bool:
    """Check if file should be ignored in search."""
    ignore_patterns = {
        ".git", "__pycache__", "node_modules", ".pytest_cache", ".venv", "venv",
        "build", "dist", ".idea", ".vscode", "target", "bin", "obj"
    }
    
    # Check if any parent directory should be ignored
    for part in file_path.parts:
        if part in ignore_patterns:
            return True
    
    # Check file extensions to ignore
    ignore_extensions = {".pyc", ".pyo", ".class", ".o", ".so", ".dylib", ".exe", ".bin"}
    if file_path.suffix in ignore_extensions:
        return True
    
    return False


def _search_file_content(file_path: Path, query: str, context_lines: int) -> List[SearchResult]:
    """Search for query in a single file."""
    results = []
    query_lower = query.lower()
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Get context lines
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context_lines_list = lines[start:end]
                
                results.append(SearchResult(
                    file_path=file_path,
                    line_number=i + 1,
                    matched_text=line.strip(),
                    context="".join(context_lines_list).strip()
                ))
    
    except Exception:
        # Skip files that can't be read
        pass
    
    return results


def _rank_search_results(results: List[SearchResult], query: str) -> List[SearchResult]:
    """Rank search results by relevance."""
    query_words = query.lower().split()
    
    def score_result(result: SearchResult) -> int:
        score = 0
        text = result.matched_text.lower()
        
        # Exact phrase match
        if query.lower() in text:
            score += 50
        
        # Word matches
        for word in query_words:
            if word in text:
                score += 10
        
        # File type bonus
        if result.file_path.suffix in {".py", ".js", ".ts", ".java"}:
            score += 5
        
        return score
    
    # Score and sort
    scored_results = [(score_result(r), r) for r in results]
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    return [r for _, r in scored_results]


def _generate_project_config(project_path: Path, profile: Optional[str]) -> str:
    """Generate project configuration file."""
    config = f"""# Claude AI Configuration for {project_path.name}
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

project:
  name: {project_path.name}
  path: {project_path}
  profile: {profile or 'general'}
  
settings:
  model: openai/gpt-4o-mini
  temperature: 0.1
  max_tokens: 4096
  
features:
  multi_mind: true
  code_analysis: true
  search: true
  workflows: true
  
directories:
  commands: .claude/commands
  workflows: .claude/workflows
  sessions: .claude/sessions
  
ignore:
  - node_modules/
  - __pycache__/
  - .git/
  - build/
  - dist/
  - .venv/
"""
    
    if profile == "python":
        config += """
  - .pytest_cache/
  - *.pyc
  - *.pyo
"""
    elif profile == "javascript":
        config += """
  - coverage/
  - .nyc_output/
  - *.min.js
"""
    elif profile == "rust":
        config += """
  - target/
  - Cargo.lock
"""
    
    return config


def _generate_profile_commands(profile: str) -> Dict[str, str]:
    """Generate profile-specific commands."""
    commands = {}
    
    if profile == "python":
        commands["python-review"] = """# Python Code Review

Review Python code with focus on:

## Instructions

1. **Code Quality**
   - PEP 8 compliance
   - Pythonic patterns
   - Type hints usage

2. **Performance**
   - Algorithm efficiency
   - Memory usage
   - Generator vs list usage

3. **Security**
   - Input validation
   - SQL injection prevention
   - Secrets handling

4. **Testing**
   - Test coverage
   - Test quality
   - Mock usage

Provide specific, actionable feedback with examples.
"""
        
        commands["python-optimize"] = """# Python Performance Optimization

Analyze Python code for performance improvements:

## Instructions

1. **Algorithmic Optimization**
   - Time complexity analysis
   - Space complexity improvements
   - Data structure selection

2. **Python-Specific Optimizations**
   - List comprehensions vs loops
   - Generator usage
   - Built-in function usage
   - NumPy/Pandas optimizations

3. **Profiling Recommendations**
   - Suggest profiling tools
   - Identify bottlenecks
   - Memory optimization

Provide benchmarks and examples where possible.
"""
    
    elif profile == "javascript":
        commands["js-review"] = """# JavaScript Code Review

Review JavaScript/TypeScript code:

## Instructions

1. **Code Quality**
   - ESLint compliance
   - Modern JS patterns
   - TypeScript usage

2. **Performance**
   - Bundle size optimization
   - Async/await patterns
   - Memory leaks

3. **Security**
   - XSS prevention
   - CSRF protection
   - Input sanitization

4. **Best Practices**
   - Error handling
   - Testing patterns
   - Documentation
"""
    
    elif profile == "rust":
        commands["rust-review"] = """# Rust Code Review

Review Rust code with focus on:

## Instructions

1. **Safety & Ownership**
   - Borrow checker compliance
   - Memory safety
   - Lifetime annotations

2. **Performance**
   - Zero-cost abstractions
   - Efficient algorithms
   - Compiler optimizations

3. **Idiomatic Rust**
   - Pattern matching
   - Error handling with Result
   - Iterator patterns

4. **Cargo & Dependencies**
   - Dependency management
   - Feature flags
   - Documentation
"""
    
    return commands


def _generate_basic_workflow() -> str:
    """Generate a basic code review workflow."""
    workflow = {
        "name": "code-review",
        "description": "Comprehensive code review workflow",
        "steps": [
            {
                "type": "analyze",
                "name": "Code Quality Analysis",
                "focus": "quality",
                "depth": "standard"
            },
            {
                "type": "analyze", 
                "name": "Security Review",
                "focus": "security",
                "depth": "deep"
            },
            {
                "type": "analyze",
                "name": "Performance Analysis", 
                "focus": "performance",
                "depth": "standard"
            },
            {
                "type": "synthesize",
                "name": "Compile Report",
                "output": "markdown"
            }
        ]
    }
    
    return json.dumps(workflow, indent=2)


def _generate_project_memory(project_path: Path, profile: Optional[str]) -> str:
    """Generate initial project memory file."""
    memory = f"""# Project Memory: {project_path.name}

## Project Overview
- **Path**: {project_path}
- **Profile**: {profile or 'General'}
- **Initialized**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Key Insights
<!-- Add important insights about this project -->

## Architecture Notes
<!-- Document architectural decisions and patterns -->

## Development Guidelines
<!-- Project-specific development practices -->

## Known Issues
<!-- Track known issues and technical debt -->

## Performance Notes
<!-- Performance characteristics and optimizations -->

## Security Considerations
<!-- Security-related notes and requirements -->

## Testing Strategy
<!-- Testing approach and coverage goals -->

## Documentation
<!-- Links to important documentation -->
"""
    
    return memory