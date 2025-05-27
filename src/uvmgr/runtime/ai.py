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
from typing import List

import dspy
from uvmgr.core.telemetry import span

_log = logging.getLogger("uvmgr.runtime.ai")

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

    # if model.startswith("ollama/"):
        # strip prefix; Ollama doesn't need it
        # cfg["api_base"] = os.getenv("OLLAMA_BASE", "http://localhost:11434/v1")
        # cfg["api_key"] = os.getenv("OLLAMA_API_KEY", "ollama-no-key")  # dummy token
    if model.startswith("openai/"):
        cfg["api_key"] = os.getenv("OPENAI_API_KEY")
        if not cfg["api_key"]:
            raise RuntimeError("OPENAI_API_KEY not set")

    lm = dspy.LM(**{k: v for k, v in cfg.items() if v is not None})
    dspy.settings.configure(lm=lm, experimental=True)
    return lm


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


def outline(model: str, topic: str, n: int = 5) -> List[str]:
    bullets = ask(model, f"List {n} key points about {topic}:\n•").splitlines()
    return [b.lstrip("•- ").strip() for b in bullets if b.strip()]


def fix_tests(model: str) -> str:
    """
    Run failing tests once, send the traceback to the LM, ask for a *unified
    diff* patch that fixes the bug.  Return the diff (caller decides what to
    do with it).
    """
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
