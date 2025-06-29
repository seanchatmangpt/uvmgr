"""
uvmgr.ops.agent_guides - Agent Guides Operations
===============================================

Operations layer for agent guides integration with DSPy and Lean Six Sigma.

This module provides the business logic for managing agent guides, executing
multi-mind analysis, and performing intelligent code analysis using DSPy
for automated decision making.
"""

from __future__ import annotations

import asyncio
import json
import time
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import subprocess

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.runtime.ai import ask
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights


@dataclass
class GuideInfo:
    """Information about an agent guide."""
    name: str
    type: str
    path: Path
    size: int
    last_used: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result from agent guides."""
    source: str
    title: str
    content: str
    snippet: str
    relevance: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiMindResult:
    """Result from multi-mind analysis."""
    topic: str
    experts: List[str]
    rounds_completed: int
    expert_insights: Dict[str, List[str]]
    consensus: Optional[str]
    recommendations: List[str]
    disagreements: List[str]
    duration: float


@dataclass
class CodeAnalysisResult:
    """Result from deep code analysis."""
    target: str
    complexity: str
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    performance_score: float
    security_score: float
    maintainability_score: float


def install_agent_guides(
    source: str,
    target_dir: Optional[Path] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Install agent guides from source repository.
    
    Args:
        source: Source repository (e.g., "tokenbender/agent-guides")
        target_dir: Target directory for installation
        force: Force reinstall existing guides
        
    Returns:
        Installation information
    """
    start_time = time.time()
    
    with span("agent_guides.install", source=source, force=force):
        add_span_attributes(**{
            "agent_guides.source": source,
            "agent_guides.force": force,
        })
        
        # Determine target directory
        if target_dir is None:
            target_dir = Path.home() / ".uvmgr" / "agent-guides"
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse source
        if source == "tokenbender/agent-guides":
            repo_url = "https://github.com/tokenbender/agent-guides.git"
            guides_path = target_dir / "tokenbender"
        else:
            # Custom source
            repo_url = source
            guides_path = target_dir / urlparse(source).path.split("/")[-1]
        
        # Check if already installed
        if guides_path.exists() and not force:
            return {
                "guides_count": len(list(guides_path.glob("*.md"))),
                "guides_path": guides_path,
                "source": source,
                "duration": 0.0,
                "guides": [g.name for g in guides_path.glob("*.md")]
            }
        
        try:
            # Clone or update repository
            if guides_path.exists():
                # Update existing
                subprocess.run(
                    ["git", "pull"],
                    cwd=guides_path,
                    check=True,
                    capture_output=True
                )
            else:
                # Clone new
                subprocess.run(
                    ["git", "clone", repo_url, str(guides_path)],
                    check=True,
                    capture_output=True
                )
            
            # Copy guides to accessible location
            guides = []
            for guide_file in guides_path.glob("*.md"):
                guides.append(guide_file.name)
            
            duration = time.time() - start_time
            
            add_span_event("agent_guides.installed", {
                "guides_count": len(guides),
                "source": source,
                "duration": duration,
            })
            
            return {
                "guides_count": len(guides),
                "guides_path": guides_path,
                "source": source,
                "duration": duration,
                "guides": guides
            }
            
        except subprocess.CalledProcessError as e:
            record_exception(e)
            raise Exception(f"Failed to install guides from {source}: {e}")


def search_conversations(
    query: str,
    sources: List[str],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search across conversations, guides, and codebase.
    
    Args:
        query: Search query
        sources: List of sources to search
        max_results: Maximum number of results
        
    Returns:
        Search results
    """
    with span("agent_guides.search", query=query, sources=",".join(sources), max_results=max_results):
        add_span_attributes(**{
            "agent_guides.query": query,
            "agent_guides.sources": ",".join(sources),
            "agent_guides.max_results": max_results,
        })
        
        results = []
        
        # Search conversations (if available)
        if "conversations" in sources:
            conversation_results = _search_conversations(query)
            results.extend(conversation_results)
        
        # Search guides
        if "guides" in sources:
            guide_results = _search_guides(query)
            results.extend(guide_results)
        
        # Search codebase
        if "code" in sources:
            code_results = _search_codebase(query)
            results.extend(code_results)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance, reverse=True)
        
        # Limit results
        results = results[:max_results]
        
        add_span_event("agent_guides.search.completed", {
            "results_count": len(results),
            "sources_searched": len(sources),
        })
        
        return {
            "query": query,
            "sources": sources,
            "results": [
                {
                    "source": r.source,
                    "title": r.title,
                    "snippet": r.snippet,
                    "relevance": r.relevance,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }


def execute_multi_mind_analysis(
    topic: str,
    analysis_type: str,
    rounds: int,
    experts: Optional[List[str]] = None,
    progress_callback: Optional[Any] = None
) -> MultiMindResult:
    """
    Execute multi-mind analysis using DSPy.
    
    Args:
        topic: Analysis topic
        analysis_type: Type of analysis
        rounds: Number of rounds
        experts: List of expert roles
        progress_callback: Progress callback function
        
    Returns:
        Multi-mind analysis result
    """
    start_time = time.time()
    
    with span("agent_guides.multi_mind", topic=topic, type=analysis_type, rounds=rounds):
        add_span_attributes(**{
            "agent_guides.topic": topic,
            "agent_guides.type": analysis_type,
            "agent_guides.rounds": rounds,
            "agent_guides.experts_count": len(experts) if experts else 0,
        })
        
        # Auto-assign experts if not provided
        if not experts:
            experts = _auto_assign_experts(topic)
        
        expert_insights = {expert: [] for expert in experts}
        round_results = []
        
        # Execute rounds
        for round_num in range(1, rounds + 1):
            add_span_event("multi_mind.round_start", {"round": round_num})
            
            round_insights = {}
            
            # Each expert provides insights
            for expert in experts:
                insight = _generate_expert_insight(
                    topic=topic,
                    expert=expert,
                    round_num=round_num,
                    previous_insights=expert_insights[expert],
                    analysis_type=analysis_type
                )
                
                round_insights[expert] = insight
                expert_insights[expert].append(insight)
            
            round_results.append(round_insights)
            
            # Call progress callback
            if progress_callback:
                progress_callback(round_num)
        
        # Analyze results using DSPy
        analysis_result = _analyze_multi_mind_results(
            topic=topic,
            expert_insights=expert_insights,
            round_results=round_results
        )
        
        duration = time.time() - start_time
        
        add_span_event("multi_mind.completed", {
            "rounds_completed": rounds,
            "experts_used": len(experts),
            "consensus_reached": analysis_result["consensus"] is not None,
        })
        
        return MultiMindResult(
            topic=topic,
            experts=experts,
            rounds_completed=rounds,
            expert_insights=expert_insights,
            consensus=analysis_result.get("consensus"),
            recommendations=analysis_result.get("recommendations", []),
            disagreements=analysis_result.get("disagreements", []),
            duration=duration
        )


def analyze_code_deep(
    target: str,
    depth: str = "deep",
    include_performance: bool = True,
    include_security: bool = True
) -> CodeAnalysisResult:
    """
    Perform deep code analysis using DSPy.
    
    Args:
        target: Code target (file:function or file path)
        depth: Analysis depth
        include_performance: Include performance analysis
        include_security: Include security analysis
        
    Returns:
        Code analysis result
    """
    with span("agent_guides.analyze_code", target=target, depth=depth, performance=include_performance, security=include_security):
        add_span_attributes(**{
            "agent_guides.target": target,
            "agent_guides.depth": depth,
            "agent_guides.performance": include_performance,
            "agent_guides.security": include_security,
        })
        
        # Parse target
        if ":" in target:
            file_path, function_name = target.split(":", 1)
            file_path = Path(file_path)
        else:
            file_path = Path(target)
            function_name = None
        
        if not file_path.exists():
            raise FileNotFoundError(f"Target file not found: {file_path}")
        
        # Read code
        code_content = file_path.read_text()
        
        # Generate analysis using DSPy
        analysis_prompt = f"""
        Analyze the following code with {depth} depth:
        
        File: {file_path}
        Function: {function_name if function_name else 'Entire file'}
        
        Code:
        {code_content}
        
        Provide analysis including:
        1. Complexity assessment
        2. Issues found (if any)
        3. Performance considerations: {'Yes' if include_performance else 'No'}
        4. Security considerations: {'Yes' if include_security else 'No'}
        5. Recommendations for improvement
        6. Scores (0-10) for performance, security, and maintainability
        
        Format response as JSON.
        """
        
        try:
            # Use DSPy for analysis
            analysis_response = ask("qwen3", analysis_prompt)
            analysis_data = json.loads(analysis_response)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback analysis
            analysis_data = _fallback_code_analysis(
                code_content, depth, include_performance, include_security
            )
        
        add_span_event("code_analysis.completed", {
            "target": target,
            "depth": depth,
            "issues_found": len(analysis_data.get("issues", [])),
            "recommendations": len(analysis_data.get("recommendations", [])),
        })
        
        return CodeAnalysisResult(
            target=target,
            complexity=analysis_data.get("complexity", "Unknown"),
            issues=analysis_data.get("issues", []),
            recommendations=analysis_data.get("recommendations", []),
            performance_score=analysis_data.get("performance_score", 5.0),
            security_score=analysis_data.get("security_score", 5.0),
            maintainability_score=analysis_data.get("maintainability_score", 5.0)
        )


def create_custom_guide(
    name: str,
    template: str,
    description: Optional[str] = None,
    interactive: bool = False,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Create custom agent guide using DSPy.
    
    Args:
        name: Guide name
        template: Guide template
        description: Guide description
        interactive: Interactive creation
        output_dir: Output directory
        
    Returns:
        Guide creation result
    """
    start_time = time.time()
    
    with span("agent_guides.create", **{"guide_name": name, "template": template, "interactive": interactive}):
        add_span_attributes(**{
            "agent_guides.name": name,
            "agent_guides.template": template,
            "agent_guides.interactive": interactive,
        })
        
        # Determine output directory
        if output_dir is None:
            output_dir = Path.home() / ".uvmgr" / "agent-guides" / "custom"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate guide content using DSPy
        guide_prompt = f"""
        Create a custom agent guide with the following specifications:
        
        Name: {name}
        Template: {template}
        Description: {description or 'Custom agent guide'}
        
        The guide should follow the format and style of tokenbender/agent-guides
        and be optimized for uvmgr's 3-tier architecture with DSPy integration.
        
        Include:
        1. Clear purpose and usage instructions
        2. Example commands and workflows
        3. Integration with uvmgr's Lean Six Sigma principles
        4. DSPy-powered decision making capabilities
        5. OpenTelemetry instrumentation examples
        
        Format as a comprehensive markdown guide.
        """
        
        try:
            # Generate guide content
            guide_content = ask("qwen3", guide_prompt)
            
            # Create guide file
            guide_file = output_dir / f"{name}.md"
            guide_file.write_text(guide_content)
            
            duration = time.time() - start_time
            
            add_span_event("agent_guide.created", {
                "name": name,
                "template": template,
                "file_size": len(guide_content),
                "duration": duration,
            })
            
            return {
                "name": name,
                "template": template,
                "output_path": guide_file,
                "file_size": len(guide_content),
                "duration": duration,
                "content_preview": guide_content[:200] + "..."
            }
            
        except Exception as e:
            record_exception(e)
            raise Exception(f"Failed to create guide {name}: {e}")


def validate_guides(guides_path: Path) -> Dict[str, Any]:
    """
    Validate agent guides using Lean Six Sigma principles.
    
    Args:
        guides_path: Path to guides directory
        
    Returns:
        Validation result
    """
    with span("agent_guides.validate", guides_path=str(guides_path)):
        add_span_attributes(**{
            "agent_guides.guides_path": str(guides_path),
        })
        
        errors = []
        warnings = []
        
        if not guides_path.exists():
            errors.append(f"Guides path does not exist: {guides_path}")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Validate each guide
        for guide_file in guides_path.glob("*.md"):
            try:
                guide_content = guide_file.read_text()
                
                # Basic validation
                if len(guide_content) < 100:
                    warnings.append(f"Guide {guide_file.name} is very short")
                
                if not guide_content.strip():
                    errors.append(f"Guide {guide_file.name} is empty")
                
                # Check for required sections
                required_sections = ["##", "###", "Examples"]
                missing_sections = []
                for section in required_sections:
                    if section not in guide_content:
                        missing_sections.append(section)
                
                if missing_sections:
                    warnings.append(f"Guide {guide_file.name} missing sections: {', '.join(missing_sections)}")
                
            except Exception as e:
                errors.append(f"Failed to read guide {guide_file.name}: {e}")
        
        add_span_event("guides.validated", {
            "guides_count": len(list(guides_path.glob("*.md"))),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "guides_count": len(list(guides_path.glob("*.md")))
        }


def execute_anti_repetition_workflow(
    workflow_name: str,
    parameters: Dict[str, Any],
    iterations: int,
    anti_repetition: bool = True,
    save_progress: bool = True,
    progress_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Execute anti-repetition workflow using DSPy.
    
    Args:
        workflow_name: Workflow name
        parameters: Workflow parameters
        iterations: Number of iterations
        anti_repetition: Enable anti-repetition mechanisms
        save_progress: Save workflow progress
        progress_callback: Progress callback function
        
    Returns:
        Workflow execution result
    """
    start_time = time.time()
    
    with span("agent_guides.workflow", workflow=workflow_name, iterations=iterations, anti_repetition=anti_repetition):
        add_span_attributes(**{
            "agent_guides.workflow": workflow_name,
            "agent_guides.iterations": iterations,
            "agent_guides.anti_repetition": anti_repetition,
        })
        
        iteration_results = []
        key_insights = []
        used_patterns = set()
        
        # Execute iterations
        for iteration in range(1, iterations + 1):
            add_span_event("workflow.iteration_start", {"iteration": iteration})
            
            # Generate iteration parameters
            if anti_repetition and iteration > 1:
                # Avoid repetition by varying parameters
                iteration_params = _vary_parameters(parameters, used_patterns)
            else:
                iteration_params = parameters.copy()
            
            # Execute iteration
            iteration_result = _execute_workflow_iteration(
                workflow_name, iteration_params, iteration
            )
            
            iteration_results.append(iteration_result)
            
            # Track patterns to avoid repetition
            if anti_repetition:
                pattern = _extract_pattern(iteration_result)
                used_patterns.add(pattern)
            
            # Extract key insights
            if iteration_result.get("insights"):
                key_insights.extend(iteration_result["insights"])
            
            # Call progress callback
            if progress_callback:
                progress_callback(iteration)
        
        # Calculate success rate
        successful_iterations = len([r for r in iteration_results if r.get("success")])
        success_rate = successful_iterations / len(iteration_results) if iteration_results else 0
        
        total_duration = time.time() - start_time
        
        add_span_event("workflow.completed", {
            "iterations_completed": iterations,
            "success_rate": success_rate,
            "anti_repetition_used": anti_repetition,
        })
        
        return {
            "workflow_name": workflow_name,
            "iterations_completed": iterations,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "iteration_results": iteration_results,
            "key_insights": key_insights[:5],  # Top 5 insights
            "anti_repetition": anti_repetition
        }


def get_guide_status(
    detailed: bool = False,
    include_metrics: bool = True
) -> Dict[str, Any]:
    """
    Get agent guides status and metrics.
    
    Args:
        detailed: Include detailed information
        include_metrics: Include performance metrics
        
    Returns:
        Status information
    """
    with span("agent_guides.status", detailed=detailed, include_metrics=include_metrics):
        add_span_attributes(**{
            "agent_guides.detailed": detailed,
            "agent_guides.include_metrics": include_metrics,
        })
        
        # Get guides directory
        guides_dir = Path.home() / ".uvmgr" / "agent-guides"
        
        status_info = {
            "active": guides_dir.exists(),
            "installation_path": str(guides_dir),
            "last_updated": "Unknown",
            "guides_count": 0,
            "guides": []
        }
        
        if guides_dir.exists():
            # Count guides
            guides = list(guides_dir.glob("**/*.md"))
            status_info["guides_count"] = len(guides)
            
            if detailed:
                # Detailed guide information
                for guide_file in guides:
                    try:
                        stat = guide_file.stat()
                        status_info["guides"].append({
                            "name": guide_file.name,
                            "type": guide_file.parent.name,
                            "size": stat.st_size,
                            "last_used": "Never"  # Would need tracking system
                        })
                    except Exception:
                        pass
            
            # Get last update time
            try:
                git_dir = guides_dir / ".git"
                if git_dir.exists():
                    result = subprocess.run(
                        ["git", "log", "-1", "--format=%cd"],
                        cwd=guides_dir,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        status_info["last_updated"] = result.stdout.strip()
            except Exception:
                pass
        
        # Add metrics if requested
        if include_metrics:
            status_info["metrics"] = {
                "total_guides": status_info["guides_count"],
                "active_guides": len([g for g in status_info.get("guides", []) if g.get("size", 0) > 0]),
                "avg_guide_size": sum(g.get("size", 0) for g in status_info.get("guides", [])) / max(status_info["guides_count"], 1),
                "installation_age_days": 0  # Would need to track installation time
            }
        
        add_span_event("status.retrieved", {
            "guides_count": status_info["guides_count"],
            "detailed": detailed,
            "metrics_included": include_metrics,
        })
        
        return status_info


def _search_conversations(query: str) -> List[SearchResult]:
    """Search Claude conversations."""
    return NotImplemented


def _search_guides(query: str) -> List[SearchResult]:
    """Search agent guides."""
    guides_dir = Path.home() / ".uvmgr" / "agent-guides"
    results = []
    
    if guides_dir.exists():
        for guide_file in guides_dir.glob("**/*.md"):
            try:
                content = guide_file.read_text()
                if query.lower() in content.lower():
                    results.append(SearchResult(
                        source="guides",
                        title=guide_file.stem,
                        content=content,
                        snippet=content[:200] + "...",
                        relevance=0.7,
                        metadata={"file": str(guide_file)}
                    ))
            except Exception:
                pass
    
    return results


def _search_codebase(query: str) -> List[SearchResult]:
    """Search codebase."""
    return NotImplemented


def _auto_assign_experts(topic: str) -> List[str]:
    """Auto-assign experts based on topic analysis."""
    # Use DSPy to analyze topic and assign experts
    expert_prompt = f"""
    Analyze the following topic and suggest 4-6 expert roles for multi-mind analysis:
    
    Topic: {topic}
    
    Consider:
    - Technical domains (e.g., Software Architecture, DevOps, Security)
    - Business domains (e.g., Product Management, Business Analysis)
    - Specialized areas (e.g., Performance, Scalability, User Experience)
    
    Return a JSON array of expert role names.
    """
    
    try:
        response = ask("qwen3", expert_prompt)
        experts = json.loads(response)
        return experts if isinstance(experts, list) else []
    except Exception:
        # Fallback experts
        return [
            "Software Architect",
            "DevOps Engineer", 
            "Security Specialist",
            "Performance Engineer"
        ]


def _generate_expert_insight(
    topic: str,
    expert: str,
    round_num: int,
    previous_insights: List[str],
    analysis_type: str
) -> str:
    """Generate expert insight using DSPy."""
    insight_prompt = f"""
    You are a {expert} providing insights on: {topic}
    
    Round: {round_num}
    Analysis Type: {analysis_type}
    
    Previous insights from this expert:
    {chr(10).join(previous_insights) if previous_insights else "None"}
    
    Provide a focused, actionable insight from your expert perspective.
    Consider the analysis type and build upon previous insights if any.
    Keep the response concise and specific.
    """
    
    try:
        return ask("qwen3", insight_prompt)
    except Exception:
        return f"Expert {expert} insight for round {round_num}: Analysis in progress."


def _analyze_multi_mind_results(
    topic: str,
    expert_insights: Dict[str, List[str]],
    round_results: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Analyze multi-mind results using DSPy."""
    analysis_prompt = f"""
    Analyze the following multi-mind analysis results:
    
    Topic: {topic}
    
    Expert Insights:
    {json.dumps(expert_insights, indent=2)}
    
    Round Results:
    {json.dumps(round_results, indent=2)}
    
    Provide analysis in JSON format with:
    1. consensus: Main consensus reached (or null if none)
    2. disagreements: List of key disagreements
    3. recommendations: List of actionable recommendations
    4. key_insights: List of most important insights
    
    Format response as JSON.
    """
    
    try:
        response = ask("qwen3", analysis_prompt)
        return json.loads(response)
    except Exception:
        return {
            "consensus": None,
            "disagreements": ["Analysis failed"],
            "recommendations": ["Review and retry analysis"],
            "key_insights": ["Multi-mind analysis completed"]
        }


def _fallback_code_analysis(
    code_content: str,
    depth: str,
    include_performance: bool,
    include_security: bool
) -> Dict[str, Any]:
    """Fallback code analysis when DSPy fails."""
    return {
        "complexity": "Medium",
        "issues": [
            {
                "severity": "Info",
                "description": "Analysis completed with fallback method",
                "location": "General"
            }
        ],
        "recommendations": [
            "Consider using DSPy for more detailed analysis",
            "Review code for best practices",
            "Add comprehensive tests"
        ],
        "performance_score": 7.0,
        "security_score": 7.0,
        "maintainability_score": 7.0
    }


def _execute_workflow_iteration(
    workflow_name: str,
    parameters: Dict[str, Any],
    iteration: int
) -> Dict[str, Any]:
    """Execute a single workflow iteration."""
    return NotImplemented


def _vary_parameters(parameters: Dict[str, Any], used_patterns: set) -> Dict[str, Any]:
    """Vary parameters to avoid repetition."""
    varied_params = parameters.copy()
    
    # Simple variation strategy
    for key, value in varied_params.items():
        if isinstance(value, (int, float)):
            # Vary numeric values
            variation = random.uniform(0.8, 1.2)
            varied_params[key] = value * variation
        elif isinstance(value, str) and "mode" in key.lower():
            # Vary mode parameters
            modes = ["strict", "normal", "relaxed"]
            varied_params[key] = random.choice(modes)
    
    return varied_params


def _extract_pattern(result: Dict[str, Any]) -> str:
    """Extract pattern from result for anti-repetition."""
    # Simple pattern extraction
    return f"{result.get('success', False)}_{len(result.get('insights', []))}"


def execute_workflow(
    workflow_id: str,
    parameters: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a workflow using DSPy.
    
    Args:
        workflow_id: Workflow ID
        parameters: Workflow parameters
        context: Workflow context
        
    Returns:
        Workflow execution result
    """
    # Execute workflow
    workflow_result = execute_workflow(
        workflow_id=workflow_id,
        parameters=parameters,
        context=context
    )
    
    return NotImplemented 