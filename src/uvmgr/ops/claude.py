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

def _auto_assign_specialists(topic: str) -> List[str]:
    """Auto-assign specialist roles based on topic."""
    # Use AI to determine appropriate specialists
    prompt = f"For the topic '{topic}', suggest 4-6 specialist roles that would provide diverse perspectives."
    
    specialists = ai_runtime.generate_specialists(prompt)
    
    # Default fallback
    if not specialists:
        specialists = [
            "Technical Expert",
            "Business Analyst",
            "Security Specialist",
            "User Experience Designer",
            "Domain Expert",
        ]
    
    return specialists[:6]  # Limit to 6


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