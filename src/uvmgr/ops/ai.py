"""
uvmgr.ops.ai – orchestration wrapper around runtime.ai.
Returns JSON-safe data for the CLI layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from uvmgr.core.fs import safe_write
from uvmgr.core.shell import timed
from uvmgr.runtime import ai as _rt


@timed
def ask(model: str, prompt: str) -> str:
    return _rt.ask(model, prompt)


@timed
def plan(model: str, topic: str, outfile: Path | None = None) -> str:
    steps = _rt.outline(model, topic)
    md = "# " + topic + "\n\n" + "\n".join(f"- {s}" for s in steps) + "\n"
    if outfile:
        safe_write(outfile, md)
    return md


@timed
def fix_tests(model: str, out_patch: Path = Path("fix.patch")) -> str:
    diff = _rt.fix_tests(model)
    if diff:
        safe_write(out_patch, diff)
    return diff


@timed
def list_models() -> List[str]:
    """List all available Ollama models."""
    return _rt.list_ollama_models()


@timed
def delete_model(model: str) -> bool:
    """Delete an Ollama model. Returns True if successful, False otherwise."""
    return _rt.delete_ollama_model(model)
