"""
uvmgr.ops.project
=================

Project scaffolding operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from uvmgr.core.shell import timed


@timed
def new(name: str, *, fastapi: bool = False, typer_cli: bool = True) -> Dict[str, str]:
    """
    Create a new Python project.
    
    NOTE: This is currently a stub implementation.
    TODO: Implement actual project scaffolding logic.
    """
    project_path = Path(name)
    
    # For now, just return a stub response
    return {
        "path": str(project_path.absolute()),
        "name": name,
        "fastapi": fastapi,
        "typer_cli": typer_cli,
        "status": "not_implemented"
    }
