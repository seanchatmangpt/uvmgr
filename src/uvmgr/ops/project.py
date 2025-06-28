"""
uvmgr.ops.project
=================

Project scaffolding operations with Substrate-inspired features.
"""

from __future__ import annotations

import time
from pathlib import Path

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.metrics import OperationResult, project_metrics
from uvmgr.core.semconv import ProjectAttributes
from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.runtime import project as _rt


@timed
def new(
    name: str, 
    *,
    template: str = "basic",
    substrate: bool = False,
    fastapi: bool = False, 
    typer_cli: bool = True,
    dev_containers: bool = False,
    github_actions: bool = False,
    pre_commit: bool = False,
    conventional_commits: bool = False,
    semantic_versioning: bool = False,
) -> dict[str, str]:
    """
    Create a new Python project with Substrate-inspired features.
    
    Args:
        name: Project name and directory
        template: Project template type (basic, substrate, fastapi, cli)
        substrate: Enable Substrate-inspired project structure
        fastapi: Include FastAPI skeleton
        typer_cli: Include Typer CLI skeleton  
        dev_containers: Include DevContainer configuration
        github_actions: Include GitHub Actions CI/CD
        pre_commit: Include pre-commit hooks
        conventional_commits: Enable conventional commits
        semantic_versioning: Enable semantic versioning
        
    Returns:
        Dictionary with project creation details
    """
    start_time = time.time()
    
    with span("ops.project.new", project_name=name, template=template):
        add_span_attributes(**{
            ProjectAttributes.NAME: name,
            ProjectAttributes.LANGUAGE: "python",
            "project.template": template,
            "project.substrate": substrate,
            "project.feature_count": sum([
                fastapi, typer_cli, dev_containers, github_actions,
                pre_commit, conventional_commits, semantic_versioning
            ]),
        })
        
        add_span_event("project.creation.started", {
            "name": name,
            "template": template,
            "features_enabled": {
                "substrate": substrate,
                "fastapi": fastapi,
                "typer_cli": typer_cli,
                "dev_containers": dev_containers,
                "github_actions": github_actions,
                "pre_commit": pre_commit,
                "conventional_commits": conventional_commits,
                "semantic_versioning": semantic_versioning,
            }
        })
        
        try:
            # Create the project using runtime layer
            result = _rt.create_project(
                name=name,
                template=template,
                substrate=substrate,
                fastapi=fastapi,
                typer_cli=typer_cli,
                dev_containers=dev_containers,
                github_actions=github_actions,
                pre_commit=pre_commit,
                conventional_commits=conventional_commits,
                semantic_versioning=semantic_versioning,
            )
            
            duration = time.time() - start_time
            
            # Record successful project creation metrics
            operation_result = OperationResult(
                success=True, 
                duration=duration,
                metadata={
                    "template": template,
                    "feature_count": sum([
                        fastapi, typer_cli, dev_containers, github_actions,
                        pre_commit, conventional_commits, semantic_versioning
                    ]),
                    "files_created": result.get("files_created", 0),
                }
            )
            
            project_metrics.record_creation(
                name=name,
                template=template,
                files_created=result.get("files_created", 0),
                result=operation_result
            )
            
            add_span_attributes(**{
                "project.files_created": result.get("files_created", 0),
                "project.duration": duration,
            })
            
            add_span_event("project.creation.completed", {
                "name": name,
                "path": result.get("path"),
                "files_created": result.get("files_created", 0),
                "duration": duration,
                "success": True,
            })
            
            return {
                "path": result.get("path", str(Path(name).absolute())),
                "name": name,
                "template": template,
                "substrate": substrate,
                "fastapi": fastapi,
                "typer_cli": typer_cli,
                "dev_containers": dev_containers,
                "github_actions": github_actions,
                "pre_commit": pre_commit,
                "conventional_commits": conventional_commits,
                "semantic_versioning": semantic_versioning,
                "files_created": result.get("files_created", 0),
                "status": "created",
                "duration": duration,
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed project creation metrics
            operation_result = OperationResult(
                success=False,
                duration=duration, 
                error=e,
                metadata={"template": template}
            )
            
            project_metrics.record_creation(
                name=name,
                template=template,
                files_created=0,
                result=operation_result
            )
            
            add_span_event("project.creation.failed", {
                "name": name,
                "template": template,
                "error": str(e),
                "duration": duration,
            })
            
            raise
