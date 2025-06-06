"""
uvmgr.ops.project
----------------
Project scaffolding operations using Copier templates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from uvmgr.core.shell import timed
from uvmgr.runtime import project as _rt

_log = logging.getLogger("uvmgr.ops.project")

@timed
def new(
    name: str,
    *,
    template: str = _rt.DEFAULT_TEMPLATE,
    version: Optional[str] = None,
    interactive: bool = True,
    **kwargs: Any
) -> Dict[str, str]:
    """
    Create a new project using a Copier template.

    Parameters
    ----------
    name
        Project name (will be converted to kebab-case)
    template
        Template URL or GitHub shorthand
    version
        Optional template version/tag
    interactive
        Whether to run in interactive mode
    **kwargs
        Additional template variables

    Returns
    -------
    dict
        Project metadata including path
    """
    dest = Path(name).resolve()
    if dest.exists():
        raise FileExistsError(dest)
    
    _rt.scaffold(
        dest,
        template=template,
        version=version,
        interactive=interactive,
        **kwargs
    )
    
    _log.info("Project scaffolded at %s", dest)
    return {
        "path": str(dest),
        "template": template,
        "version": version or "latest"
    }

@timed
def update(
    path: Optional[str] = None,
    *,
    template: Optional[str] = None,
    version: Optional[str] = None,
    interactive: bool = True,
    **kwargs: Any
) -> Dict[str, str]:
    """
    Update an existing project to the latest template version.

    Parameters
    ----------
    path
        Path to the project (defaults to current directory)
    template
        Optional template URL to update from
    version
        Optional template version/tag
    interactive
        Whether to run in interactive mode
    **kwargs
        Additional template variables

    Returns
    -------
    dict
        Update metadata
    """
    project_path = Path(path or ".").resolve()
    if not project_path.exists():
        raise FileNotFoundError(project_path)
    
    _rt.update(
        project_path,
        template=template,
        version=version,
        interactive=interactive,
        **kwargs
    )
    
    _log.info("Project updated at %s", project_path)
    return {
        "path": str(project_path),
        "template": template or _rt.DEFAULT_TEMPLATE,
        "version": version or "latest"
    }

@timed
def clean_cache() -> Dict[str, str]:
    """
    Clean Copier's template cache.

    Returns
    -------
    dict
        Status message
    """
    _rt.clean_cache()
    return {"status": "Template cache cleaned"}
