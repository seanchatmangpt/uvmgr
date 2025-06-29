"""
uvmgr.runtime.ai
----------------
Single source of truth for creating DSPy `LM` objects that work with Qwen3 via Ollama by default,
but allows specific model overrides for flexibility.

The public helpers (`ask`, `outline`, `fix_tests`) are thin wrappers that
*actually* call the LM; higher layers must never touch DSPy directly.

This module defaults to Qwen3 for consistency but allows other models when explicitly specified.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import dspy

from uvmgr.core.telemetry import span

_log = logging.getLogger("uvmgr.runtime.ai")

# --------------------------------------------------------------------------- #
# LM factory                                                                  #
# --------------------------------------------------------------------------- #


def _init_lm(model: str, **kw) -> dspy.LM:
    """
    Creates a DSPy LM with Qwen3 as default, but allows specific model overrides.
    Supports any model format supported by LiteLLM.
    """
    # Default to Qwen3 if not specified or if using old OpenAI format
    if model == "qwen3" or model.startswith("openai/gpt"):
        model = "ollama/qwen3"
    
    cfg: dict = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 2048,
        **kw,
    }

    lm = dspy.LM(**{k: v for k, v in cfg.items() if v is not None})
    dspy.settings.configure(lm=lm, experimental=True)
    return lm


# --------------------------------------------------------------------------- #
# Public AI helpers                                                          #
# --------------------------------------------------------------------------- #


@span("ai.ask")
def ask(prompt: str, model: str = "qwen3", **kw) -> str:
    """
    General-purpose AI query using Qwen3 by default, but allows other models.
    """
    lm = _init_lm(model, **kw)
    with span("ai.query", model=model):
        return lm(prompt)


@span("ai.outline")
def outline(topic: str, model: str = "qwen3", **kw) -> str:
    """
    Generate an outline for a topic using Qwen3 by default, but allows other models.
    """
    lm = _init_lm(model, **kw)
    prompt = f"Create a detailed outline for: {topic}"
    with span("ai.outline_generation", topic=topic):
        return lm(prompt)


@span("ai.fix_tests")
def fix_tests(test_output: str, model: str = "qwen3", **kw) -> str:
    """
    Analyze test failures and suggest fixes using Qwen3 by default, but allows other models.
    """
    lm = _init_lm(model, **kw)
    prompt = f"Analyze these test failures and suggest fixes:\n\n{test_output}"
    with span("ai.test_analysis"):
        return lm(prompt)


# --------------------------------------------------------------------------- #
# Claude Integration AI Functions                                            #
# --------------------------------------------------------------------------- #


@span("ai.research_topic")
def research_topic(
    topic: str,
    perspective: str,
    enable_web_search: bool = True,
    previous_insights: List[Dict[str, Any]] = None,
    model: str = "qwen3",
    **kw
) -> Dict[str, Any]:
    """
    Research a topic from a specific specialist perspective using Qwen3 by default, but allows other models.
    
    Args:
        topic: Topic to research
        perspective: Specialist perspective (e.g., "technical", "security")
        enable_web_search: Whether to enable web search (placeholder)
        previous_insights: Previous round insights for context
        model: AI model to use (defaults to Qwen3, but allows any LiteLLM-supported model)
        
    Returns:
        Research insights from the specialist perspective
    """
    lm = _init_lm(model, **kw)
    
    # Build research prompt based on perspective
    prompt = f"""As a {perspective} specialist, research and analyze: {topic}

Perspective: {perspective}
Topic: {topic}

Please provide:
1. Key insights from your expertise area
2. Critical considerations and risks
3. Recommendations and best practices
4. Any concerns or red flags

Format your response as structured insights."""

    if previous_insights:
        prompt += f"\n\nPrevious insights to build upon:\n{previous_insights}"
    
    with span("ai.specialist_research", perspective=perspective, topic=topic):
        response = lm(prompt)
        
        return {
            "perspective": perspective,
            "insights": response,
            "topic": topic,
            "web_search_enabled": enable_web_search,
        }


@span("ai.analyze_code_expert")
def analyze_code_expert(
    files: List[tuple],
    expert_type: str,
    depth: str = "standard",
    model: str = "qwen3",
    **kw
) -> Dict[str, Any]:
    """
    Analyze code from a specific expert perspective using Qwen3 by default, but allows other models.
    
    Args:
        files: List of (file_path, content) tuples
        expert_type: Type of expert (performance, security, architecture)
        depth: Analysis depth (quick, standard, deep)
        model: AI model to use (defaults to Qwen3, but allows any LiteLLM-supported model)
        
    Returns:
        Expert analysis results with issues and suggestions
    """
    lm = _init_lm(model, **kw)
    
    # Build code analysis prompt
    code_summary = "\n\n".join([
        f"File: {path}\n{content[:1000]}..." if len(content) > 1000 else f"File: {path}\n{content}"
        for path, content in files[:5]  # Limit to first 5 files
    ])
    
    prompt = f"""As a {expert_type} expert, analyze this code with {depth} depth:

{code_summary}

Focus on {expert_type} aspects and provide:
1. Issues found (with severity levels)
2. Specific recommendations
3. Best practice suggestions
4. Code quality metrics

Format as structured analysis."""
    
    with span("ai.code_expert_analysis", expert_type=expert_type, depth=depth):
        response = lm(prompt)
        
        # Parse response into structured format
        return {
            "expert_type": expert_type,
            "depth": depth,
            "issues": _parse_issues_from_response(response),
            "suggestions": _parse_suggestions_from_response(response),
            "metrics": _parse_metrics_from_response(response),
        }


@span("ai.conversation_search")
def search_conversations(
    query: str,
    max_results: int = 10,
    model: str = "qwen3",
    **kw
) -> List[Dict[str, Any]]:
    """
    Search through conversation history using Qwen3 by default, but allows other models (placeholder implementation).
    
    Args:
        query: Search query
        max_results: Maximum results to return
        model: AI model to use (defaults to Qwen3, but allows any LiteLLM-supported model)
        
    Returns:
        List of matching conversation snippets
    """
    # This is a placeholder implementation
    # In a real system, this would search through stored conversations
    return [
        {
            "id": "conv_001",
            "snippet": f"Found conversation about {query}",
            "relevance": 0.85,
            "timestamp": "2024-01-01T12:00:00Z",
        }
    ]


@span("ai.create_custom_command")
def create_custom_command(
    description: str,
    examples: List[str] = None,
    model: str = "qwen3",
    **kw
) -> Dict[str, Any]:
    """
    Create a custom command based on description using Qwen3 by default, but allows other models.
    
    Args:
        description: Description of desired command
        examples: Example use cases
        model: AI model to use (defaults to Qwen3, but allows any LiteLLM-supported model)
        
    Returns:
        Custom command specification
    """
    lm = _init_lm(model, **kw)
    
    prompt = f"""Create a custom command specification for: {description}

Please provide:
1. Command name and syntax
2. Parameters and options
3. Implementation outline
4. Usage examples
5. Error handling

Examples of use cases:
{chr(10).join(examples or ["General purpose command"])}

Format as a structured command specification."""
    
    with span("ai.custom_command_creation", description=description):
        response = lm(prompt)
        
        return {
            "description": description,
            "specification": response,
            "examples": examples or [],
        }


# --------------------------------------------------------------------------- #
# Helper Functions                                                           #
# --------------------------------------------------------------------------- #


def _parse_issues_from_response(response: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """Parse issues from AI response."""
    # Handle DSPy responses which are lists
    if isinstance(response, list):
        response = response[0] if response else ""
    
    # Simplified parser - in practice would use more sophisticated parsing
    issues = []
    lines = response.split('\n')
    
    for line in lines:
        if 'issue:' in line.lower() or 'problem:' in line.lower():
            issues.append({
                "description": line.strip(),
                "severity": "medium",  # Default severity
                "line": 0,
            })
    
    return issues


def _parse_suggestions_from_response(response: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """Parse suggestions from AI response."""
    # Handle DSPy responses which are lists
    if isinstance(response, list):
        response = response[0] if response else ""
    
    suggestions = []
    lines = response.split('\n')
    
    for line in lines:
        if 'suggest:' in line.lower() or 'recommend:' in line.lower():
            suggestions.append({
                "description": line.strip(),
                "priority": "medium",
            })
    
    return suggestions


def _parse_metrics_from_response(response: Union[str, List[str]]) -> Dict[str, Any]:
    """Parse metrics from AI response."""
    # Handle DSPy responses which are lists
    if isinstance(response, list):
        response = response[0] if response else ""
    
    # Simplified metrics extraction
    return {
        "complexity": "medium",
        "maintainability": "good",
        "performance": "acceptable",
    }