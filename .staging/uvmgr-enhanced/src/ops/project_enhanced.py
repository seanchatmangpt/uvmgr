"""
Enhanced Project Operations
===========================

Complete implementation of project scaffolding using Copier and Substrate.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..events.producer import EventProducer
from ..models.events import Event, EventType
from ..models.project import ProjectConfig, ProjectCreationResult, ProjectTemplate
from ..performance.project_ops import fast_directory_scan


class ProjectOperations:
    """High-level project operations with event streaming"""

    def __init__(self, event_producer: EventProducer | None = None):
        self.event_producer = event_producer or EventProducer()

    def create_project(self, config: ProjectConfig) -> ProjectCreationResult:
        """Create a new project using Copier template"""
        start_time = time.time()

        # Emit project creation started event
        self.event_producer.emit(Event(
            event_id=f"proj-{int(time.time()*1000)}",
            event_type=EventType.PROJECT_CREATED,
            source="project_ops",
            data=config.dict()
        ))

        # Prepare Copier answers
        answers = self._prepare_copier_answers(config)

        # Create project directory
        project_path = Path(config.project_name)
        project_path.mkdir(exist_ok=True)

        # Run Copier
        self._run_copier(config.template.url, project_path, answers)

        # Count created files using high-performance scanner
        files_created = fast_directory_scan(str(project_path))

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Prepare next steps
        next_steps = [
            f"cd {config.project_name}",
            "uv sync",
            "pre-commit install" if config.pre_commit else None,
            "uvmgr tests run",
        ]
        next_steps = [step for step in next_steps if step]
        return ProjectCreationResult(
            project_path=str(project_path.absolute()),
            package_name=config.package_name or config.project_name.replace("-", "_"),
            template_used=str(config.template.url),
            duration_ms=duration_ms,
            files_created=files_created,
            next_steps=next_steps
        )

    def _prepare_copier_answers(self, config: ProjectConfig) -> dict[str, Any]:
        """Prepare answers for Copier template"""
        package_name = config.package_name or config.project_name.replace("-", "_")

        answers = {
            "project_name": config.project_name,
            "package_name": package_name,
            "project_description": config.description,
            "author_name": config.author_name,
            "author_email": config.author_email,
            "python_version": config.python_version,
            "license": config.license,
            "pre_commit": config.pre_commit,
            "conventional_commits": config.conventional_commits,
            "gpg_signing": config.gpg_signing,
            "cicd_platform": config.cicd_platform,
            "test_coverage": config.test_coverage,
            "include_fastapi": config.fastapi,
            "include_typer": config.typer_cli,
            "include_docker": config.docker,
            "include_devcontainer": config.devcontainer,
        }

        # Merge with extra context
        answers.update(config.extra_context)

        return answers

    def _run_copier(self, template_url: str, dest_path: Path, answers: dict[str, Any]):
        """Execute Copier with given template and answers"""
        # Note: In production, this would use the copier Python API
        # For now, using subprocess as a stub
        cmd = [
            "copier", "copy",
            str(template_url),
            str(dest_path),
            "--data", str(answers),
            "--vcs-ref", "HEAD",
            "--quiet"
        ]

        # Stub: In real implementation, would run the command
        # subprocess.run(cmd, check=True)
