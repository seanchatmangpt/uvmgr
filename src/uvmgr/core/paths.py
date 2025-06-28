"""
uvmgr.core.paths
----------------
Authoritative filesystem locations & helpers.

Enhanced with comprehensive OpenTelemetry instrumentation for filesystem operations monitoring.
"""

from __future__ import annotations

import sys
import time
from functools import cache
from pathlib import Path

from .instrumentation import add_span_attributes, add_span_event
from .telemetry import metric_counter, metric_histogram, span

__all__ = [
    "CACHE_DIR",
    "CONFIG_DIR",
    "VENV_DIR",
    "bin_dir",
    "bin_path",
    "ensure_dirs",
    "project_root",
    "venv_path",
]

CONFIG_DIR: Path = Path.home() / ".config" / "uvmgr"
CACHE_DIR: Path = Path.home() / ".uvmgr_cache"
VENV_DIR: Path = Path(".venv")


def ensure_dirs() -> None:
    """Ensure uvmgr directories exist with telemetry tracking."""
    with span("paths.ensure_dirs"):
        start_time = time.time()

        add_span_event("paths.ensure_dirs.starting", {
            "config_dir": str(CONFIG_DIR),
            "cache_dir": str(CACHE_DIR),
        })

        # Create directories
        config_existed = CONFIG_DIR.exists()
        cache_existed = CACHE_DIR.exists()

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        duration = time.time() - start_time

        # Record metrics
        metric_counter("paths.ensure_dirs.calls")(1)
        metric_histogram("paths.ensure_dirs.duration")(duration)

        if not config_existed:
            metric_counter("paths.config_dir.created")(1)
        if not cache_existed:
            metric_counter("paths.cache_dir.created")(1)

        add_span_attributes(**{
            "paths.config_dir": str(CONFIG_DIR),
            "paths.cache_dir": str(CACHE_DIR),
            "paths.config_existed": config_existed,
            "paths.cache_existed": cache_existed,
            "paths.duration": duration,
        })

        add_span_event("paths.ensure_dirs.completed", {
            "config_created": not config_existed,
            "cache_created": not cache_existed,
            "duration": duration,
        })


ensure_dirs()  # create on first import


@cache
def project_root() -> Path:
    """Get project root directory with caching and telemetry."""
    # Add minimal telemetry for cached function
    metric_counter("paths.project_root.calls")(1)
    result = Path.cwd()

    # Record path info (only on cache miss)
    try:
        add_span_event("paths.project_root.resolved", {
            "path": str(result),
            "exists": result.exists(),
        })
    except:
        # Avoid breaking on telemetry issues
        pass

    return result


@cache
def venv_path() -> Path:
    """Get virtual environment path with caching and telemetry."""
    metric_counter("paths.venv_path.calls")(1)
    result = (project_root() / VENV_DIR).resolve()

    try:
        add_span_event("paths.venv_path.resolved", {
            "path": str(result),
            "exists": result.exists(),
            "venv_dir": str(VENV_DIR),
        })
    except:
        pass

    return result


def bin_dir() -> Path:
    """Get binary directory path with telemetry."""
    with span("paths.bin_dir", platform=sys.platform):
        is_windows = sys.platform.startswith("win")
        subdir = "Scripts" if is_windows else "bin"
        result = venv_path() / subdir

        metric_counter("paths.bin_dir.calls")(1)

        add_span_attributes(**{
            "paths.platform": sys.platform,
            "paths.is_windows": is_windows,
            "paths.bin_subdir": subdir,
            "paths.bin_path": str(result),
        })

        add_span_event("paths.bin_dir.resolved", {
            "platform": sys.platform,
            "subdir": subdir,
            "path": str(result),
            "exists": result.exists(),
        })

        return result


def bin_path(cmd: str) -> Path:
    """Get executable path in bin directory with telemetry."""
    with span("paths.bin_path", command=cmd):
        start_time = time.time()

        result = bin_dir() / cmd
        duration = time.time() - start_time

        # Record metrics
        metric_counter("paths.bin_path.calls")(1)
        metric_histogram("paths.bin_path.duration")(duration)

        add_span_attributes(**{
            "paths.command": cmd,
            "paths.executable_path": str(result),
            "paths.exists": result.exists(),
            "paths.duration": duration,
        })

        add_span_event("paths.bin_path.resolved", {
            "command": cmd,
            "path": str(result),
            "exists": result.exists(),
            "duration": duration,
        })

        return result
