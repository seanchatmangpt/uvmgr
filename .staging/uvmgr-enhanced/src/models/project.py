"""
Project Creation Models (DSLModel Pattern)
==========================================

Declarative Pydantic models for project scaffolding configuration.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class LicenseType(str, Enum):
    MIT = "MIT"
    APACHE2 = "Apache-2.0"
    GPL3 = "GPL-3.0"
    BSD3 = "BSD-3-Clause"
    PROPRIETARY = "Proprietary"


class CICDPlatform(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    NONE = "none"


class ProjectTemplate(BaseModel):
    """Declarative model for project templates"""

    url: HttpUrl = Field(
        default="https://github.com/superlinear-ai/substrate",
        description="Copier template URL"
    )
    version: str | None = Field(None, description="Template version tag")
    cache_dir: str | None = Field(None, description="Local cache directory")


class ProjectConfig(BaseModel):
    """Declarative configuration for new project creation"""

    # Basic Information
    project_name: str = Field(..., description="Project name (kebab-case)")
    package_name: str | None = Field(None, description="Package name (snake_case)")
    description: str = Field("A Python project", description="Project description")

    # Author Information
    author_name: str = Field(..., description="Author's full name")
    author_email: str = Field(..., description="Author's email address")

    # Project Settings
    python_version: str = Field("3.12", description="Python version requirement")
    license: LicenseType = Field(LicenseType.MIT, description="Project license")

    # Development Tools
    pre_commit: bool = Field(True, description="Enable pre-commit hooks")
    conventional_commits: bool = Field(True, description="Use conventional commits")
    gpg_signing: bool = Field(False, description="Enable GPG commit signing")
    cicd_platform: CICDPlatform = Field(CICDPlatform.GITHUB, description="CI/CD platform")
    test_coverage: bool = Field(True, description="Enable test coverage tracking")

    # Template Configuration
    template: ProjectTemplate = Field(
        default_factory=ProjectTemplate,
        description="Template configuration"
    )

    # Additional Features
    fastapi: bool = Field(False, description="Include FastAPI skeleton")
    typer_cli: bool = Field(True, description="Include Typer CLI skeleton")
    docker: bool = Field(True, description="Include Docker configuration")
    devcontainer: bool = Field(True, description="Include dev container setup")

    # Advanced Options
    extra_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional template context variables"
    )

    class Config:
        use_enum_values = True


class ProjectCreationResult(BaseModel):
    """Result of project creation operation"""

    project_path: str
    package_name: str
    template_used: str
    duration_ms: float
    files_created: int
    next_steps: list[str] = Field(default_factory=list)
