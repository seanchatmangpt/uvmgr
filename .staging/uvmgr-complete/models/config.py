"""Declarative configuration models for uvmgr."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DependencySpec(BaseModel):
    """Declarative dependency specification."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str | None = None
    extras: list[str] = Field(default_factory=list)
    source: str | None = None
    editable: bool = False

    @property
    def spec_string(self) -> str:
        """Generate uv-compatible spec string."""
        parts = [self.name]
        if self.extras:
            parts[0] += f"[{','.join(self.extras)}]"
        if self.version:
            parts.append(self.version)
        if self.source:
            parts.append(f"@ {self.source}")
        return "".join(parts)


class CommandSpec(BaseModel):
    """Declarative command specification."""

    model_config = ConfigDict(extra="forbid")

    name: str
    command: str
    description: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    working_dir: Path | None = None
    timeout: int | None = None
    shell: bool = False


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str = "0.1.0"
    python_version: str = ">=3.12"
    template: str = "default"
    dependencies: list[DependencySpec] = Field(default_factory=list)
    dev_dependencies: list[DependencySpec] = Field(default_factory=list)
    scripts: dict[str, CommandSpec] = Field(default_factory=dict)


class UvmgrConfig(BaseModel):
    """Global uvmgr configuration."""

    model_config = ConfigDict(extra="forbid")

    project_defaults: ProjectConfig = Field(
        default_factory=lambda: ProjectConfig(name="default")
    )
    uv_path: Path = Field(default_factory=lambda: Path("uv"))
    cache_dir: Path | None = None
    index_url: str | None = None
    extra_index_urls: list[str] = Field(default_factory=list)
    trusted_hosts: list[str] = Field(default_factory=list)
    keyring_provider: str | None = None
    performance_mode: bool = True
    telemetry_enabled: bool = True
    event_stream_url: str | None = None
