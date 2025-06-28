"""
uvmgr.runtime.exec – script execution using uv run.
"""

from __future__ import annotations

import sys
from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span


def script(
    path: Path | None = None,
    *,
    argv: list[str] | None = None,
    stdin: bool = False,
    no_project: bool = False,
    with_deps: list[str] | None = None,
) -> None:
    """
    Execute a Python script using uv run.

    Parameters
    ----------
    path
        Path to the script file. If None and stdin is True, read from stdin.
    argv
        Arguments to pass to the script.
    stdin
        Whether to read script from stdin.
    no_project
        Whether to skip installing the current project.
    with_deps
        Dependencies to install before running the script.
    """
    cmd = ["uv", "run"]

    if no_project:
        cmd.append("--no-project")

    if with_deps:
        for dep in with_deps:
            cmd.extend(["--with", dep])

    if stdin:
        cmd.append("-")
    elif path:
        cmd.append(str(path))
    else:
        raise ValueError("Either path must be provided or stdin must be True")

    if argv:
        cmd.extend(argv)

    with span("exec.script", cmd=" ".join(cmd)):
        if stdin:
            # For stdin, we need to handle the input stream
            import subprocess

            process = subprocess.Popen(
                cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, text=True
            )
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
        else:
            run_logged(cmd)
