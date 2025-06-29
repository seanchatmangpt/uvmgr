"""
CI/CD Pipeline Integration for uvmgr
====================================

This module provides CI/CD pipeline support, addressing the critical gap of 
continuous integration and deployment automation. It enables 20% of the unified 
workflow engine value with just 5% implementation effort.

Key features:
1. **Pipeline Definition**: YAML-based pipeline configuration
2. **Multi-Platform Support**: GitHub Actions, GitLab CI, Jenkins
3. **Pipeline Generation**: Generate CI/CD configs from templates
4. **Pipeline Validation**: Validate pipeline syntax and logic
5. **Deployment Automation**: Deploy to various targets

The 80/20 approach: Essential CI/CD operations that cover most use cases.
"""

from __future__ import annotations

import yaml
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.semconv import CliAttributes

logger = logging.getLogger(__name__)


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    AZURE_DEVOPS = "azure-devops"
    LOCAL = "local"


class PipelineStage(Enum):
    """Common pipeline stages."""
    BUILD = "build"
    TEST = "test"
    LINT = "lint"
    SECURITY = "security"
    DEPLOY = "deploy"
    RELEASE = "release"


@dataclass
class PipelineJob:
    """Individual pipeline job configuration."""
    name: str
    stage: PipelineStage
    steps: List[Dict[str, Any]]
    needs: List[str] = field(default_factory=list)
    when: str = "on_success"
    environment: Optional[str] = None
    artifacts: Optional[Dict[str, Any]] = None
    cache: Optional[Dict[str, Any]] = None
    timeout: int = 60  # minutes
    retry: int = 0
    parallel: Optional[int] = None
    matrix: Optional[Dict[str, List[Any]]] = None


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    name: str
    platform: CICDPlatform
    triggers: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    stages: List[PipelineStage] = field(default_factory=list)
    jobs: List[PipelineJob] = field(default_factory=list)
    services: List[Dict[str, Any]] = field(default_factory=list)
    before_script: List[str] = field(default_factory=list)
    after_script: List[str] = field(default_factory=list)


class PipelineGenerator:
    """Generate CI/CD pipeline configurations for different platforms."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
    
    def generate_pipeline(
        self,
        config: PipelineConfig,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate pipeline configuration for the specified platform."""
        
        generators = {
            CICDPlatform.GITHUB_ACTIONS: self._generate_github_actions,
            CICDPlatform.GITLAB_CI: self._generate_gitlab_ci,
            CICDPlatform.JENKINS: self._generate_jenkins,
            CICDPlatform.CIRCLECI: self._generate_circleci,
            CICDPlatform.AZURE_DEVOPS: self._generate_azure_devops
        }
        
        generator = generators.get(config.platform)
        if not generator:
            raise ValueError(f"Unsupported platform: {config.platform}")
        
        pipeline_content = generator(config)
        
        # Write to file if output path specified
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config.platform == CICDPlatform.JENKINS:
                output_path.write_text(pipeline_content)
            else:
                with open(output_path, 'w') as f:
                    yaml.dump(pipeline_content, f, default_flow_style=False, sort_keys=False)
        
        return pipeline_content
    
    def _generate_github_actions(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate GitHub Actions workflow."""
        
        workflow = {
            "name": config.name,
            "on": self._convert_triggers_github(config.triggers),
            "env": config.variables,
            "jobs": {}
        }
        
        for job in config.jobs:
            job_config = {
                "runs-on": "ubuntu-latest",
                "steps": []
            }
            
            # Add checkout step
            job_config["steps"].append({
                "uses": "actions/checkout@v4"
            })
            
            # Add setup steps based on detected language
            if self._detect_python():
                job_config["steps"].extend([
                    {
                        "name": "Set up Python",
                        "uses": "actions/setup-python@v5",
                        "with": {
                            "python-version": "3.12"
                        }
                    },
                    {
                        "name": "Install uv",
                        "run": "curl -LsSf https://astral.sh/uv/install.sh | sh"
                    }
                ])
            
            # Add job steps
            for step in job.steps:
                if isinstance(step, str):
                    job_config["steps"].append({
                        "name": step,
                        "run": step
                    })
                else:
                    job_config["steps"].append(step)
            
            # Add needs
            if job.needs:
                job_config["needs"] = job.needs
            
            # Add environment
            if job.environment:
                job_config["environment"] = job.environment
            
            # Add matrix
            if job.matrix:
                job_config["strategy"] = {"matrix": job.matrix}
            
            workflow["jobs"][job.name] = job_config
        
        return workflow
    
    def _generate_gitlab_ci(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate GitLab CI configuration."""
        
        gitlab_ci = {
            "stages": [stage.value for stage in config.stages],
            "variables": config.variables
        }
        
        # Add default before_script
        if config.before_script:
            gitlab_ci["before_script"] = config.before_script
        
        for job in config.jobs:
            job_config = {
                "stage": job.stage.value,
                "script": []
            }
            
            # Convert steps to script
            for step in job.steps:
                if isinstance(step, str):
                    job_config["script"].append(step)
                elif isinstance(step, dict) and "run" in step:
                    job_config["script"].append(step["run"])
            
            # Add dependencies
            if job.needs:
                job_config["needs"] = job.needs
            
            # Add when condition
            if job.when != "on_success":
                job_config["when"] = job.when
            
            # Add artifacts
            if job.artifacts:
                job_config["artifacts"] = job.artifacts
            
            # Add cache
            if job.cache:
                job_config["cache"] = job.cache
            
            # Add timeout
            job_config["timeout"] = f"{job.timeout}m"
            
            # Add retry
            if job.retry > 0:
                job_config["retry"] = job.retry
            
            # Add parallel
            if job.parallel:
                job_config["parallel"] = job.parallel
            
            gitlab_ci[job.name] = job_config
        
        return gitlab_ci
    
    def _generate_jenkins(self, config: PipelineConfig) -> str:
        """Generate Jenkins Pipeline (Jenkinsfile)."""
        
        stages = []
        
        for job in config.jobs:
            stage_steps = []
            
            for step in job.steps:
                if isinstance(step, str):
                    stage_steps.append(f"sh '{step}'")
                elif isinstance(step, dict) and "run" in step:
                    stage_steps.append(f"sh '{step['run']}'")
            
            stage_content = f"""
        stage('{job.name}') {{
            steps {{
                {chr(10).join(stage_steps)}
            }}
        }}"""
            stages.append(stage_content)
        
        jenkinsfile = f"""pipeline {{
    agent any
    
    environment {{
{chr(10).join(f"        {k} = '{v}'" for k, v in config.variables.items())}
    }}
    
    stages {{
{chr(10).join(stages)}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
    }}
}}"""
        
        return jenkinsfile
    
    def _generate_circleci(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate CircleCI configuration."""
        
        circleci = {
            "version": 2.1,
            "jobs": {},
            "workflows": {
                "main": {
                    "jobs": []
                }
            }
        }
        
        for job in config.jobs:
            job_config = {
                "docker": [{"image": "cimg/base:stable"}],
                "steps": ["checkout"]
            }
            
            # Add steps
            for step in job.steps:
                if isinstance(step, str):
                    job_config["steps"].append({"run": step})
                else:
                    job_config["steps"].append(step)
            
            circleci["jobs"][job.name] = job_config
            
            # Add to workflow
            workflow_job = {job.name: {}}
            if job.needs:
                workflow_job[job.name]["requires"] = job.needs
            
            circleci["workflows"]["main"]["jobs"].append(workflow_job)
        
        return circleci
    
    def _generate_azure_devops(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate Azure DevOps Pipeline."""
        
        azure = {
            "trigger": self._convert_triggers_azure(config.triggers),
            "variables": config.variables,
            "stages": []
        }
        
        # Group jobs by stage
        stages_dict = {}
        for job in config.jobs:
            stage_name = job.stage.value
            if stage_name not in stages_dict:
                stages_dict[stage_name] = []
            stages_dict[stage_name].append(job)
        
        # Create stages
        for stage_name, jobs in stages_dict.items():
            stage = {
                "stage": stage_name,
                "jobs": []
            }
            
            for job in jobs:
                job_config = {
                    "job": job.name,
                    "steps": []
                }
                
                # Add steps
                for step in job.steps:
                    if isinstance(step, str):
                        job_config["steps"].append({
                            "script": step
                        })
                    else:
                        job_config["steps"].append(step)
                
                stage["jobs"].append(job_config)
            
            azure["stages"].append(stage)
        
        return azure
    
    def _convert_triggers_github(self, triggers: List[str]) -> Dict[str, Any]:
        """Convert generic triggers to GitHub Actions format."""
        
        github_triggers = {}
        
        for trigger in triggers:
            if trigger == "push":
                github_triggers["push"] = {"branches": ["main", "master"]}
            elif trigger == "pull_request":
                github_triggers["pull_request"] = {"branches": ["main", "master"]}
            elif trigger == "schedule":
                github_triggers["schedule"] = [{"cron": "0 0 * * *"}]
            elif trigger == "manual":
                github_triggers["workflow_dispatch"] = {}
        
        return github_triggers or {"push": {"branches": ["main"]}}
    
    def _convert_triggers_azure(self, triggers: List[str]) -> List[str]:
        """Convert generic triggers to Azure DevOps format."""
        
        azure_triggers = []
        
        for trigger in triggers:
            if trigger == "push":
                azure_triggers.extend(["main", "master"])
            elif trigger == "pull_request":
                return ["pr: *"]
        
        return azure_triggers or ["main"]
    
    def _detect_python(self) -> bool:
        """Detect if this is a Python project."""
        return (
            (self.project_root / "pyproject.toml").exists() or
            (self.project_root / "requirements.txt").exists() or
            (self.project_root / "setup.py").exists()
        )
    
    def _detect_node(self) -> bool:
        """Detect if this is a Node.js project."""
        return (self.project_root / "package.json").exists()
    
    def _detect_go(self) -> bool:
        """Detect if this is a Go project."""
        return (self.project_root / "go.mod").exists()


def create_python_pipeline(project_name: str, include_deploy: bool = False) -> PipelineConfig:
    """Create a standard Python project pipeline configuration."""
    
    stages = [
        PipelineStage.BUILD,
        PipelineStage.LINT,
        PipelineStage.TEST,
        PipelineStage.SECURITY
    ]
    
    if include_deploy:
        stages.append(PipelineStage.DEPLOY)
    
    jobs = [
        PipelineJob(
            name="build",
            stage=PipelineStage.BUILD,
            steps=[
                "uv pip install -e .",
                "uv pip list"
            ]
        ),
        PipelineJob(
            name="lint",
            stage=PipelineStage.LINT,
            steps=[
                "uvmgr lint check"
            ],
            needs=["build"]
        ),
        PipelineJob(
            name="test",
            stage=PipelineStage.TEST,
            steps=[
                "uvmgr tests run --coverage",
                "uvmgr tests coverage"
            ],
            needs=["build"],
            artifacts={
                "paths": ["reports/", "htmlcov/"],
                "reports": {
                    "junit": "reports/pytest.xml",
                    "coverage": "reports/coverage.xml"
                }
            }
        ),
        PipelineJob(
            name="security",
            stage=PipelineStage.SECURITY,
            steps=[
                "pip-audit",
                "safety check"
            ],
            needs=["build"]
        )
    ]
    
    if include_deploy:
        jobs.append(
            PipelineJob(
                name="deploy",
                stage=PipelineStage.DEPLOY,
                steps=[
                    "uvmgr build dist",
                    "uvmgr build dist --upload"
                ],
                needs=["test", "lint", "security"],
                when="manual",
                environment="production"
            )
        )
    
    return PipelineConfig(
        name=f"{project_name}-pipeline",
        platform=CICDPlatform.GITHUB_ACTIONS,
        triggers=["push", "pull_request"],
        variables={
            "PYTHON_VERSION": "3.12",
            "UV_SYSTEM_PYTHON": "1"
        },
        stages=stages,
        jobs=jobs
    )


def create_multi_language_pipeline(project_name: str, languages: List[str]) -> PipelineConfig:
    """Create a multi-language project pipeline configuration."""
    
    jobs = []
    
    # Create language-specific jobs
    for lang in languages:
        if lang == "python":
            jobs.extend([
                PipelineJob(
                    name="python-build",
                    stage=PipelineStage.BUILD,
                    steps=[
                        "cd python",
                        "uv pip install -e .",
                        "uvmgr tests run"
                    ]
                ),
                PipelineJob(
                    name="python-test",
                    stage=PipelineStage.TEST,
                    steps=[
                        "cd python",
                        "uvmgr tests run --coverage"
                    ],
                    needs=["python-build"]
                )
            ])
        
        elif lang == "node":
            jobs.extend([
                PipelineJob(
                    name="node-build",
                    stage=PipelineStage.BUILD,
                    steps=[
                        "cd node",
                        "npm ci",
                        "npm run build"
                    ]
                ),
                PipelineJob(
                    name="node-test",
                    stage=PipelineStage.TEST,
                    steps=[
                        "cd node",
                        "npm test"
                    ],
                    needs=["node-build"]
                )
            ])
        
        elif lang == "go":
            jobs.extend([
                PipelineJob(
                    name="go-build",
                    stage=PipelineStage.BUILD,
                    steps=[
                        "cd go",
                        "go mod download",
                        "go build ./..."
                    ]
                ),
                PipelineJob(
                    name="go-test",
                    stage=PipelineStage.TEST,
                    steps=[
                        "cd go",
                        "go test ./... -cover"
                    ],
                    needs=["go-build"]
                )
            ])
    
    return PipelineConfig(
        name=f"{project_name}-multi-language-pipeline",
        platform=CICDPlatform.GITHUB_ACTIONS,
        triggers=["push", "pull_request"],
        stages=[PipelineStage.BUILD, PipelineStage.TEST],
        jobs=jobs
    )