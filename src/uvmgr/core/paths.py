"""
uvmgr.core.paths
----------------
Authoritative filesystem locations & helpers.
"""

from __future__ import annotations

import sys
from functools import cache
from pathlib import Path

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
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


ensure_dirs()  # create on first import


@cache
def project_root() -> Path:
    return Path.cwd()


@cache
def venv_path() -> Path:
    return (project_root() / VENV_DIR).resolve()


def bin_dir() -> Path:
    return venv_path() / ("Scripts" if sys.platform.startswith("win") else "bin")


def bin_path(cmd: str) -> Path:
    return bin_dir() / cmd
