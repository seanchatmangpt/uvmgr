"""
CI/CD Runtime Operations
========================

This module provides CI/CD pipeline management operations.
Implements the 80/20 principle: focuses on the most common CI/CD operations
that provide 80% of the value for typical Python development workflows.

Key Features:
- GitHub Actions integration
- GitLab CI/CD support
- Jenkins pipeline management
- Workflow status monitoring
- Artifact management
- Environment deployment
- Build status tracking
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import CICDAttributes, CICDOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span, record_exception


@dataclass
class WorkflowRun:
    """CI/CD workflow run information."""
    id: str
    name: str
    status: str
    conclusion: Optional[str]
    branch: str
    commit_sha: str
    created_at: str
    updated_at: str
    url: str


@dataclass
class BuildArtifact:
    """Build artifact information."""
    id: str
    name: str
    size: int
    download_url: str
    created_at: str


@dataclass
class DeploymentStatus:
    """Deployment status information."""
    id: str
    environment: str
    status: str
    url: Optional[str]
    created_at: str
    updated_at: str


def detect_cicd_platform() -> str:
    """Detect the CI/CD platform being used."""
    with span("cicd.platform.detect"):
        # Check for GitHub Actions
        if Path(".github/workflows").exists():
            add_span_event("cicd.platform.detected", {"platform": "github_actions"})
            return "github_actions"
        
        # Check for GitLab CI
        if Path(".gitlab-ci.yml").exists():
            add_span_event("cicd.platform.detected", {"platform": "gitlab_ci"})
            return "gitlab_ci"
        
        # Check for Jenkins
        if Path("Jenkinsfile").exists():
            add_span_event("cicd.platform.detected", {"platform": "jenkins"})
            return "jenkins"
        
        # Check for Azure Pipelines
        if Path("azure-pipelines.yml").exists() or Path(".azure-pipelines").exists():
            add_span_event("cicd.platform.detected", {"platform": "azure_pipelines"})
            return "azure_pipelines"
        
        # Default fallback
        add_span_event("cicd.platform.detected", {"platform": "unknown"})
        return "unknown"


@instrument_command("cicd_get_workflow_runs")
def get_workflow_runs(limit: int = 10, branch: Optional[str] = None) -> List[WorkflowRun]:
    """Get recent workflow runs."""
    platform = detect_cicd_platform()
    
    with span("cicd.workflow_runs",
              **{CICDAttributes.PLATFORM: platform,
                 CICDAttributes.OPERATION: CICDOperations.LIST_RUNS}):
        
        if platform == "github_actions":
            return _get_github_workflow_runs(limit, branch)
        elif platform == "gitlab_ci":
            return _get_gitlab_pipelines(limit, branch)
        else:
            # Generic implementation
            return []


def _get_github_workflow_runs(limit: int, branch: Optional[str]) -> List[WorkflowRun]:
    """Get GitHub Actions workflow runs."""
    try:
        # Use GitHub CLI if available
        cmd = ["gh", "run", "list", "--limit", str(limit)]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.append("--json=id,name,status,conclusion,headBranch,headSha,createdAt,updatedAt,url")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        runs_data = json.loads(result.stdout)
        runs = []
        
        for run in runs_data:
            runs.append(WorkflowRun(
                id=str(run["id"]),
                name=run["name"],
                status=run["status"],
                conclusion=run.get("conclusion"),
                branch=run["headBranch"],
                commit_sha=run["headSha"],
                created_at=run["createdAt"],
                updated_at=run["updatedAt"],
                url=run["url"]
            ))
        
        metric_counter("cicd.api_calls")(1, {
            "platform": "github_actions",
            "operation": "list_runs"
        })
        
        return runs
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        record_exception(e, attributes={
            "cicd.platform": "github_actions",
            "cicd.operation": "list_runs"
        })
        return []


def _get_gitlab_pipelines(limit: int, branch: Optional[str]) -> List[WorkflowRun]:
    """Get GitLab CI pipelines."""
    try:
        # Use GitLab CLI if available
        cmd = ["glab", "ci", "list", "--limit", str(limit)]
        if branch:
            cmd.extend(["--branch", branch])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        # Parse output (implementation would depend on GitLab CLI output format)
        # This is a simplified implementation
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        runs = []
        
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 6:
                    runs.append(WorkflowRun(
                        id=parts[0],
                        name=f"Pipeline {parts[0]}",
                        status=parts[1],
                        conclusion=parts[1] if parts[1] in ["success", "failed"] else None,
                        branch=parts[2],
                        commit_sha=parts[3][:8],
                        created_at=parts[4],
                        updated_at=parts[5],
                        url=f"https://gitlab.com/-/pipelines/{parts[0]}"
                    ))
        
        metric_counter("cicd.api_calls")(1, {
            "platform": "gitlab_ci",
            "operation": "list_runs"
        })
        
        return runs
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        record_exception(e, attributes={
            "cicd.platform": "gitlab_ci",
            "cicd.operation": "list_runs"
        })
        return []


@instrument_command("cicd_trigger_workflow")
def trigger_workflow(workflow_name: str, branch: Optional[str] = None,
                     inputs: Optional[Dict[str, str]] = None) -> str:
    """Trigger a workflow run."""
    platform = detect_cicd_platform()
    
    with span("cicd.trigger_workflow",
              **{CICDAttributes.PLATFORM: platform,
                 CICDAttributes.OPERATION: CICDOperations.TRIGGER,
                 CICDAttributes.WORKFLOW_NAME: workflow_name}):
        
        if platform == "github_actions":
            return _trigger_github_workflow(workflow_name, branch, inputs)
        elif platform == "gitlab_ci":
            return _trigger_gitlab_pipeline(workflow_name, branch, inputs)
        else:
            raise RuntimeError(f"Workflow triggering not supported for platform: {platform}")


def _trigger_github_workflow(workflow_name: str, branch: Optional[str],
                            inputs: Optional[Dict[str, str]]) -> str:
    """Trigger GitHub Actions workflow."""
    try:
        cmd = ["gh", "workflow", "run", workflow_name]
        
        if branch:
            cmd.extend(["--ref", branch])
        
        if inputs:
            for key, value in inputs.items():
                cmd.extend(["-f", f"{key}={value}"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        metric_counter("cicd.workflow_triggers")(1, {
            "platform": "github_actions",
            "workflow": workflow_name
        })
        
        add_span_event("cicd.workflow.triggered", {
            "workflow_name": workflow_name,
            "branch": branch or "default"
        })
        
        return f"Workflow '{workflow_name}' triggered successfully"
        
    except subprocess.CalledProcessError as e:
        record_exception(e, attributes={
            "cicd.platform": "github_actions",
            "cicd.operation": "trigger_workflow",
            "cicd.workflow": workflow_name
        })
        raise RuntimeError(f"Failed to trigger workflow '{workflow_name}': {e.stderr}")


def _trigger_gitlab_pipeline(workflow_name: str, branch: Optional[str],
                           inputs: Optional[Dict[str, str]]) -> str:
    """Trigger GitLab CI pipeline."""
    try:
        cmd = ["glab", "ci", "run"]
        
        if branch:
            cmd.extend(["--branch", branch])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        metric_counter("cicd.workflow_triggers")(1, {
            "platform": "gitlab_ci",
            "workflow": workflow_name
        })
        
        return f"Pipeline triggered successfully on branch '{branch or 'default'}'"
        
    except subprocess.CalledProcessError as e:
        record_exception(e, attributes={
            "cicd.platform": "gitlab_ci",
            "cicd.operation": "trigger_pipeline"
        })
        raise RuntimeError(f"Failed to trigger pipeline: {e.stderr}")


@instrument_command("cicd_get_artifacts")
def get_build_artifacts(run_id: str) -> List[BuildArtifact]:
    """Get build artifacts for a workflow run."""
    platform = detect_cicd_platform()
    
    with span("cicd.get_artifacts",
              **{CICDAttributes.PLATFORM: platform,
                 CICDAttributes.OPERATION: CICDOperations.GET_ARTIFACTS,
                 CICDAttributes.RUN_ID: run_id}):
        
        if platform == "github_actions":
            return _get_github_artifacts(run_id)
        else:
            return []


def _get_github_artifacts(run_id: str) -> List[BuildArtifact]:
    """Get GitHub Actions artifacts."""
    try:
        cmd = ["gh", "run", "download", run_id, "--dry-run"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        # Parse artifact list from dry-run output
        artifacts = []
        for line in result.stdout.split('\n'):
            if 'artifact:' in line:
                artifact_name = line.split('artifact:')[1].strip()
                artifacts.append(BuildArtifact(
                    id=artifact_name,
                    name=artifact_name,
                    size=0,  # Size not available in dry-run
                    download_url=f"gh://artifacts/{run_id}/{artifact_name}",
                    created_at=datetime.now().isoformat()
                ))
        
        metric_counter("cicd.artifact_requests")(1, {
            "platform": "github_actions",
            "run_id": run_id
        })
        
        return artifacts
        
    except subprocess.CalledProcessError as e:
        record_exception(e, attributes={
            "cicd.platform": "github_actions",
            "cicd.operation": "get_artifacts",
            "cicd.run_id": run_id
        })
        return []


@instrument_command("cicd_get_deployments")
def get_deployments(environment: Optional[str] = None) -> List[DeploymentStatus]:
    """Get deployment status."""
    platform = detect_cicd_platform()
    
    with span("cicd.get_deployments",
              **{CICDAttributes.PLATFORM: platform,
                 CICDAttributes.OPERATION: CICDOperations.GET_DEPLOYMENTS}):
        
        if platform == "github_actions":
            return _get_github_deployments(environment)
        else:
            return []


def _get_github_deployments(environment: Optional[str]) -> List[DeploymentStatus]:
    """Get GitHub deployments."""
    try:
        cmd = ["gh", "api", "repos/:owner/:repo/deployments"]
        if environment:
            cmd.extend(["--field", f"environment={environment}"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        deployments_data = json.loads(result.stdout)
        deployments = []
        
        for deployment in deployments_data:
            deployments.append(DeploymentStatus(
                id=str(deployment["id"]),
                environment=deployment["environment"],
                status=deployment.get("state", "pending"),
                url=deployment.get("payload", {}).get("web_url"),
                created_at=deployment["created_at"],
                updated_at=deployment["updated_at"]
            ))
        
        metric_counter("cicd.deployment_requests")(1, {
            "platform": "github_actions",
            "environment": environment or "all"
        })
        
        return deployments
        
    except subprocess.CalledProcessError as e:
        record_exception(e, attributes={
            "cicd.platform": "github_actions",
            "cicd.operation": "get_deployments"
        })
        return []


@instrument_command("cicd_create_workflow")
def create_workflow_template(workflow_type: str, output_path: Path) -> bool:
    """Create a CI/CD workflow template."""
    platform = detect_cicd_platform()
    
    with span("cicd.create_template",
              **{CICDAttributes.PLATFORM: platform,
                 CICDAttributes.OPERATION: CICDOperations.CREATE_WORKFLOW}):
        
        templates = {
            "python_test": _get_python_test_template(),
            "python_build": _get_python_build_template(),
            "docker_build": _get_docker_build_template(),
        }
        
        if workflow_type not in templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        template_content = templates[workflow_type]
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write template
        output_path.write_text(template_content)
        
        add_span_event("cicd.template.created", {
            "workflow_type": workflow_type,
            "output_path": str(output_path)
        })
        
        return True


def _get_python_test_template() -> str:
    """Get Python test workflow template."""
    return '''name: Python Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
    
    - name: Install dependencies
      run: uv sync --all-extras
    
    - name: Run tests
      run: uv run pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.python-version == '3.11'
'''


def _get_python_build_template() -> str:
    """Get Python build workflow template."""
    return '''name: Build and Release

on:
  push:
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
    
    - name: Build package
      run: uv build
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist
        path: dist/
    
    - name: Publish to PyPI
      if: startsWith(github.ref, 'refs/tags/')
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        uv tool install twine
        uv tool run twine upload dist/*
'''


def _get_docker_build_template() -> str:
    """Get Docker build workflow template."""
    return '''name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  docker:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
'''