"""
uvmgr.runtime.project
====================

Project scaffolding using Copier templates, with Substrate as the default.
"""

from __future__ import annotations

import logging
import shlex
from pathlib import Path
from typing import Optional

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span
from uvmgr.core.shell import colour

_log = logging.getLogger("uvmgr.runtime.project")

# Default template and version
DEFAULT_TEMPLATE = "gh:superlinear-ai/substrate"
DEFAULT_VERSION = "main"  # or specific version tag

def _get_template_url(template: str, version: Optional[str] = None) -> str:
    """Construct the full template URL with optional version."""
    if template.startswith(("http://", "https://", "gh:")):
        base = template
    else:
        base = f"gh:{template}"
    
    if version:
        return f"{base}@{version}"
    return base

def scaffold(
    dest: Path,
    *,
    template: str = DEFAULT_TEMPLATE,
    version: Optional[str] = None,
    interactive: bool = True,
    **kwargs
) -> None:
    """
    Run Copier to scaffold a new project into *dest* directory.

    Parameters
    ----------
    dest
        Destination directory for the new project
    template
        Template URL or GitHub shorthand (e.g. "user/repo")
    version
        Optional template version/tag to use
    interactive
        Whether to run in interactive mode
    **kwargs
        Additional template variables to pass to Copier
    """
    template_url = _get_template_url(template, version)
    
    # Build Copier command
    args = ["copier", "copy"]
    
    if not interactive:
        args.append("--non-interactive")
    
    # Add template variables
    for key, value in kwargs.items():
        if isinstance(value, bool):
            value = str(int(value))
        args.extend(["-d", f"{key}={value}"])
    
    # Add template and destination
    args.extend([template_url, str(dest)])
    
    with span("project.scaffold", template=template_url, dest=str(dest)):
        try:
            run_logged(args)
            colour(f"✔ Project scaffolded at {dest}", "green")
        except Exception as e:
            _log.error("Failed to scaffold project: %s", e)
            raise

def update(
    path: Path,
    *,
    template: Optional[str] = None,
    version: Optional[str] = None,
    interactive: bool = True,
    **kwargs
) -> None:
    """
    Update an existing project to the latest template version.

    Parameters
    ----------
    path
        Path to the existing project
    template
        Optional template URL to update from (defaults to project's template)
    version
        Optional template version/tag to use
    interactive
        Whether to run in interactive mode
    **kwargs
        Additional template variables to pass to Copier
    """
    template_url = _get_template_url(template or DEFAULT_TEMPLATE, version)
    
    args = ["copier", "update"]
    
    if not interactive:
        args.append("--non-interactive")
    
    # Add template variables
    for key, value in kwargs.items():
        if isinstance(value, bool):
            value = str(int(value))
        args.extend(["-d", f"{key}={value}"])
    
    # Add destination
    args.append(str(path))
    
    with span("project.update", template=template_url, path=str(path)):
        try:
            run_logged(args)
            colour(f"✔ Project updated at {path}", "green")
        except Exception as e:
            _log.error("Failed to update project: %s", e)
            raise

def clean_cache() -> None:
    """Clean Copier's template cache."""
    with span("project.clean_cache"):
        try:
            run_logged(["copier", "clean"])
            colour("✔ Template cache cleaned", "green")
        except Exception as e:
            _log.error("Failed to clean template cache: %s", e)
            raise
