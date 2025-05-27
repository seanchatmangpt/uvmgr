"""
uvmgr.core.config – env override & typed TOML loader.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel

from .paths import CONFIG_DIR

T = TypeVar("T", bound=BaseModel)

__all__ = ["env_or", "load_toml"]


def env_or(key: str, default: str | None = None) -> str | None:
    if key in os.environ:
        return os.environ[key]
    env_file = CONFIG_DIR / "env.toml"
    if env_file.exists():
        data = tomllib.loads(env_file.read_text())
        if key in data:
            return str(data[key])
    return default


def load_toml(path: Path, model: type[T]) -> T:
    data = tomllib.loads(path.read_text())
    return model.model_validate(data)
