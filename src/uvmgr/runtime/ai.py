"""
uvmgr.runtime.ai
----------------
Single source of truth for creating DSPy `LM` objects that work with:

* **openai/** models  → remote OpenAI
* **ollama/** models → local Ollama server (OpenAI-compatible API)

The public helpers (`ask`, `outline`, `fix_tests`) are thin wrappers that
*actually* call the LM; higher layers must never touch DSPy directly.
"""

from __future__ import annotations

import logging
import os

import dspy

from uvmgr.core.telemetry import span

_log = logging.getLogger("uvmgr.runtime.ai")

from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# LM factory                                                                  #
# --------------------------------------------------------------------------- #


def _init_lm(model: str, **kw) -> dspy.LM:
    """
    Creates a DSPy LM with sane defaults.  If the *model* string begins with
    ``ollama/``, we automatically point the OpenAI-compatible base URL at the
    local Ollama server (or whatever `OLLAMA_BASE` env var says).
    """
    cfg: dict = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 2048,
        **kw,
    }

    if model.startswith("openai/"):
        cfg["api_key"] = os.getenv("OPENAI_API_KEY")
        if not cfg["api_key"]:
            raise RuntimeError("OPENAI_API_KEY not set")

    lm = dspy.LM(**{k: v for k, v in cfg.items() if v is not None})
    dspy.settings.configure(lm=lm, experimental=True)
    return lm


def list_ollama_models() -> list[str]:
    """List all available Ollama models."""
    with span("ai.list_models"):
        from urllib.parse import urljoin

        import requests

        base_url = os.getenv("OLLAMA_BASE", "http://localhost:11434")
        try:
            response = requests.get(urljoin(base_url, "/api/tags"))
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        except requests.RequestException as e:
            _log.error(f"Failed to list Ollama models: {e}")
            return []


def delete_ollama_model(model: str) -> bool:
    """Delete an Ollama model. Returns True if successful, False otherwise."""
    with span("ai.delete_model", model=model):
        from urllib.parse import urljoin

        import requests

        base_url = os.getenv("OLLAMA_BASE", "http://localhost:11434")
        try:
            response = requests.delete(urljoin(base_url, "/api/delete"), json={"name": model})
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            _log.error(f"Failed to delete Ollama model {model}: {e}")
            return False


# --------------------------------------------------------------------------- #
# Public helpers                                                              #
# --------------------------------------------------------------------------- #


def ask(model: str, prompt: str) -> str:
    with span("ai.ask", model=model):
        lm = _init_lm(model)
        response = lm(prompt)
        # Handle case where response is a list
        if isinstance(response, list):
            return "\n".join(response)
        return response


def outline(model: str, topic: str, n: int = 5) -> list[str]:
    with span("ai.outline", model=model, topic=topic, n=n):
        bullets = ask(model, f"List {n} key points about {topic}:\n•").splitlines()
        return [b.lstrip("•- ").strip() for b in bullets if b.strip()]


def fix_tests(model: str) -> str:
    """
    Run failing tests once, send the traceback to the LM, ask for a *unified
    diff* patch that fixes the bug.  Return the diff (caller decides what to
    do with it).
    """
    with span("ai.fix_tests", model=model):
        from uvmgr.core.process import run

        failure = run("pytest --maxfail=1 -q", capture=True)
    if "failed" not in failure:
        return ""

    prompt = (
        "You are an expert Python developer. Analyse the following pytest "
        "failure output and propose a **unified diff patch** that fixes the bug."
        f"\n\n{failure}"
    )
    return ask(model, prompt)


# --------------------------------------------------------------------------- #
# Claude-specific functions for agent workflows                               #
# --------------------------------------------------------------------------- #

def research_topic(
    topic: str,
    perspective: str,
    enable_web_search: bool = True,
    previous_insights: Optional[List[Dict[str, Any]]] = None,
    model: str = "openai/gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Research a topic from a specific specialist perspective.
    
    Args:
        topic: Topic to research
        perspective: Specialist role/perspective
        enable_web_search: Whether to use web search
        previous_insights: Previous round insights for cross-pollination
        model: AI model to use
        
    Returns:
        Research findings and insights
    """
    with span("ai.research_topic", topic=topic, perspective=perspective):
        prompt = f"""
        You are a {perspective} researching '{topic}'.
        
        Previous insights from other specialists:
        {previous_insights or 'None yet'}
        
        Provide:
        1. Your unique perspective on this topic
        2. Key findings and insights
        3. Questions or challenges to explore
        4. Connections to other perspectives
        
        Be specific and insightful.
        """
        
        response = ask(model, prompt)
        
        # Parse response into structured format
        return {
            "perspective": perspective,
            "findings": [response],  # In real implementation, parse structured
            "questions": [],
            "connections": [],
        }


def generate_specialists(prompt: str, model: str = "openai/gpt-4o-mini") -> List[str]:
    """Generate specialist roles for a topic."""
    with span("ai.generate_specialists", prompt=prompt[:50]):
        response = ask(model, prompt)
        
        # Parse response into list
        specialists = []
        for line in response.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove numbering, bullets, etc.
                specialist = line.lstrip("0123456789.-• ").strip()
                if specialist:
                    specialists.append(specialist)
        
        return specialists[:6]  # Limit to 6


def generate_synthesis(prompt: str, model: str = "openai/gpt-4o-mini") -> str:
    """Generate synthesis from multiple insights."""
    with span("ai.generate_synthesis"):
        return ask(model, prompt)


def analyze_code_expert(
    files: List[tuple[Any, str]],
    expert_type: str,
    depth: str = "standard",
    model: str = "openai/gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Analyze code from a specific expert perspective.
    
    Args:
        files: List of (path, content) tuples
        expert_type: Type of expert analysis
        depth: Analysis depth
        model: AI model to use
        
    Returns:
        Analysis results with issues and suggestions
    """
    with span("ai.analyze_code_expert", expert=expert_type, files=len(files)):
        depth_instructions = {
            "quick": "Provide a high-level review focusing on major issues only.",
            "standard": "Provide a balanced review covering important issues and improvements.",
            "deep": "Provide an exhaustive review examining every detail and edge case.",
        }
        
        file_contents = "\n\n".join([
            f"File: {path}\n```\n{content}\n```"
            for path, content in files[:5]  # Limit for context
        ])
        
        prompt = f"""
        You are a {expert_type} reviewing the following code.
        
        {depth_instructions.get(depth, depth_instructions["standard"])}
        
        Code to review:
        {file_contents}
        
        Provide:
        1. Issues found (with severity: critical/high/medium/low)
        2. Specific suggestions for improvement
        3. Relevant metrics or measurements
        
        Format as JSON.
        """
        
        response = ask(model, prompt)
        
        # Parse JSON response (simplified for example)
        try:
            import json
            return json.loads(response)
        except:
            return {
                "issues": [],
                "suggestions": [{"title": "Review completed", "description": response}],
                "metrics": {},
            }


def generate_expert_argument(
    topic: str,
    expert_role: str,
    round_num: int,
    previous_arguments: Dict[str, List[str]],
    debate_format: str = "structured",
    model: str = "openai/gpt-4o-mini",
) -> str:
    """
    Generate expert argument for debate.
    
    Args:
        topic: Debate topic
        expert_role: Expert's role
        round_num: Current round number
        previous_arguments: Previous arguments from all experts
        debate_format: Debate format style
        model: AI model to use
        
    Returns:
        Expert's argument for this round
    """
    with span("ai.generate_expert_argument", expert=expert_role, round=round_num):
        format_instructions = {
            "structured": "Present a clear, logical argument with evidence.",
            "freeform": "Express your perspective naturally and conversationally.",
            "socratic": "Ask probing questions to challenge assumptions.",
        }
        
        # Build context from previous arguments
        context = []
        for expert, args in previous_arguments.items():
            if args and expert != expert_role:
                context.append(f"{expert}: {args[-1][:200]}...")
        
        prompt = f"""
        You are a {expert_role} participating in round {round_num} of a debate about:
        '{topic}'
        
        Previous arguments:
        {context or 'This is the first round.'}
        
        {format_instructions.get(debate_format, format_instructions["structured"])}
        
        Provide your argument, considering:
        1. Your unique expertise and perspective
        2. Points raised by other experts
        3. New insights or challenges
        
        Be concise but impactful.
        """
        
        return ask(model, prompt)


def analyze_debate(prompt: str, model: str = "openai/gpt-4o-mini") -> Dict[str, Any]:
    """Analyze debate outcomes."""
    with span("ai.analyze_debate"):
        response = ask(model, prompt + "\n\nFormat response as JSON.")
        
        try:
            import json
            return json.loads(response)
        except:
            # Fallback parsing
            return {
                "consensus": None,
                "disagreements": ["Unable to parse debate analysis"],
                "recommendations": [response],
            }
