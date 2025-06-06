"""
DX shortcuts: lint / test / serve
"""

from __future__ import annotations

from typing import List

from uvmgr.core.shell import timed
from uvmgr.runtime import poetask as _rt, ai as _ai


@timed
def lint() -> None:
    _rt.exec_task("lint")


@timed
def test(extra: list[str] | None = None) -> None:
    _rt.exec_task("test", *(extra or []))


@timed
def explain_tests(model: str = "ollama/phi3:medium-128k") -> str:
    """
    Run tests and use AI to explain any failures in plain English.
    Returns an explanation if tests failed, empty string if they passed.
    """
    from uvmgr.core.process import run
    failure = run("pytest --maxfail=1 -q", capture=True)
    if "failed" not in failure:
        return ""

    prompt = (
        "You are an expert Python developer. Analyze the following pytest "
        "failure output and explain in plain English:\n"
        "1. What test failed and why\n"
        "2. What the test was expecting vs what actually happened\n"
        "3. What might have caused this failure\n\n"
        f"{failure}"
    )
    return _ai.ask(model, prompt)


@timed
def serve(dev: bool = False, host: str = "0.0.0.0", port: str = "8000") -> None:
    args = ["--dev"] if dev else []
    args += ["--host", host, "--port", port]
    _rt.exec_task("api", *args)
