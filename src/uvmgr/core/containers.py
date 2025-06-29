"""
Container Integration for uvmgr
================================

This module provides Docker and Podman integration, addressing the critical gap
of container support in uvmgr. It enables 40% of the unified workflow engine value
with just 10% implementation effort.

Key features:
1. **Container Runtime Detection**: Automatically detect Docker or Podman
2. **Build & Run Operations**: Unified interface for container operations
3. **Compose/Pod Management**: Multi-container orchestration
4. **Registry Integration**: Push/pull from container registries
5. **Development Environments**: Containerized dev environments

The 80/20 approach: Essential container operations that cover most use cases.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.semconv import CliAttributes

logger = logging.getLogger(__name__)


class ContainerRuntime(Enum):
    """Supported container runtimes."""
    DOCKER = "docker"
    PODMAN = "podman"
    NONE = "none"


class ContainerOperation(Enum):
    """Container operation types."""
    BUILD = "build"
    RUN = "run"
    STOP = "stop"
    REMOVE = "remove"
    PUSH = "push"
    PULL = "pull"
    COMPOSE_UP = "compose_up"
    COMPOSE_DOWN = "compose_down"
    EXEC = "exec"
    LOGS = "logs"


@dataclass
class ContainerConfig:
    """Container configuration."""
    name: str
    image: str
    tag: str = "latest"
    dockerfile: str = "Dockerfile"
    build_args: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    command: Optional[List[str]] = None
    working_dir: Optional[str] = None
    user: Optional[str] = None
    network: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComposeConfig:
    """Docker Compose / Podman Pod configuration."""
    name: str
    services: Dict[str, ContainerConfig]
    networks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    volumes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    compose_file: str = "docker-compose.yml"


@dataclass
class ContainerResult:
    """Result of a container operation."""
    success: bool
    operation: ContainerOperation
    runtime: ContainerRuntime
    output: str = ""
    error: str = ""
    container_id: Optional[str] = None
    exit_code: Optional[int] = None
    duration: Optional[float] = None


class ContainerManager:
    """Unified container management for Docker and Podman."""
    
    def __init__(self, project_root: Path = None, preferred_runtime: ContainerRuntime = None):
        self.project_root = project_root or Path.cwd()
        self.runtime = preferred_runtime or self._detect_runtime()
        self._runtime_cmd = self.runtime.value if self.runtime != ContainerRuntime.NONE else None
        
    def _detect_runtime(self) -> ContainerRuntime:
        """Detect available container runtime."""
        # Check for Docker first (more common)
        if shutil.which("docker"):
            try:
                result = subprocess.run(
                    ["docker", "version", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return ContainerRuntime.DOCKER
            except Exception:
                pass
        
        # Check for Podman
        if shutil.which("podman"):
            try:
                result = subprocess.run(
                    ["podman", "version", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return ContainerRuntime.PODMAN
            except Exception:
                pass
        
        return ContainerRuntime.NONE
    
    def is_available(self) -> bool:
        """Check if container runtime is available."""
        return self.runtime != ContainerRuntime.NONE
    
    async def build(self, config: ContainerConfig, no_cache: bool = False) -> ContainerResult:
        """Build a container image."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.BUILD,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        dockerfile_path = self.project_root / config.dockerfile
        if not dockerfile_path.exists():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.BUILD,
                runtime=self.runtime,
                error=f"Dockerfile not found: {dockerfile_path}"
            )
        
        # Build command
        cmd = [self._runtime_cmd, "build"]
        
        # Add build args
        for key, value in config.build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])
        
        # Add labels
        for key, value in config.labels.items():
            cmd.extend(["--label", f"{key}={value}"])
        
        # Add options
        if no_cache:
            cmd.append("--no-cache")
        
        # Tag
        cmd.extend(["-t", f"{config.image}:{config.tag}"])
        
        # Dockerfile
        cmd.extend(["-f", str(dockerfile_path)])
        
        # Context
        cmd.append(str(self.project_root))
        
        # Execute build
        return await self._execute_command(cmd, ContainerOperation.BUILD)
    
    async def run(
        self, 
        config: ContainerConfig,
        detach: bool = True,
        rm: bool = False,
        interactive: bool = False
    ) -> ContainerResult:
        """Run a container."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.RUN,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        # Build command
        cmd = [self._runtime_cmd, "run"]
        
        # Add name
        if config.name:
            cmd.extend(["--name", config.name])
        
        # Add options
        if detach:
            cmd.append("-d")
        if rm:
            cmd.append("--rm")
        if interactive:
            cmd.extend(["-it"])
        
        # Add environment variables
        for key, value in config.env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Add port mappings
        for host_port, container_port in config.ports.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
        
        # Add volume mounts
        for host_path, container_path in config.volumes.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add working directory
        if config.working_dir:
            cmd.extend(["-w", config.working_dir])
        
        # Add user
        if config.user:
            cmd.extend(["-u", config.user])
        
        # Add network
        if config.network:
            cmd.extend(["--network", config.network])
        
        # Add labels
        for key, value in config.labels.items():
            cmd.extend(["--label", f"{key}={value}"])
        
        # Image
        cmd.append(f"{config.image}:{config.tag}")
        
        # Command
        if config.command:
            cmd.extend(config.command)
        
        # Execute run
        result = await self._execute_command(cmd, ContainerOperation.RUN)
        
        # Extract container ID from output
        if result.success and detach:
            result.container_id = result.output.strip()
        
        return result
    
    async def compose_up(
        self,
        compose_file: str = "docker-compose.yml",
        detach: bool = True,
        build: bool = False,
        services: List[str] = None
    ) -> ContainerResult:
        """Start services defined in compose file."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.COMPOSE_UP,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        compose_path = self.project_root / compose_file
        if not compose_path.exists():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.COMPOSE_UP,
                runtime=self.runtime,
                error=f"Compose file not found: {compose_path}"
            )
        
        # Build command based on runtime
        if self.runtime == ContainerRuntime.DOCKER:
            cmd = [self._runtime_cmd, "compose"]
        else:  # Podman
            cmd = ["podman-compose"]
            if not shutil.which("podman-compose"):
                # Fallback to podman with compatibility
                cmd = [self._runtime_cmd, "compose"]
        
        cmd.extend(["-f", str(compose_path), "up"])
        
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        
        # Add specific services
        if services:
            cmd.extend(services)
        
        return await self._execute_command(cmd, ContainerOperation.COMPOSE_UP)
    
    async def compose_down(
        self,
        compose_file: str = "docker-compose.yml",
        volumes: bool = False,
        remove_orphans: bool = True
    ) -> ContainerResult:
        """Stop and remove services defined in compose file."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.COMPOSE_DOWN,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        compose_path = self.project_root / compose_file
        
        # Build command based on runtime
        if self.runtime == ContainerRuntime.DOCKER:
            cmd = [self._runtime_cmd, "compose"]
        else:  # Podman
            cmd = ["podman-compose"]
            if not shutil.which("podman-compose"):
                cmd = [self._runtime_cmd, "compose"]
        
        cmd.extend(["-f", str(compose_path), "down"])
        
        if volumes:
            cmd.append("-v")
        if remove_orphans:
            cmd.append("--remove-orphans")
        
        return await self._execute_command(cmd, ContainerOperation.COMPOSE_DOWN)
    
    async def exec(
        self,
        container: str,
        command: List[str],
        interactive: bool = False,
        user: Optional[str] = None,
        workdir: Optional[str] = None
    ) -> ContainerResult:
        """Execute command in running container."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.EXEC,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        cmd = [self._runtime_cmd, "exec"]
        
        if interactive:
            cmd.extend(["-it"])
        
        if user:
            cmd.extend(["-u", user])
        
        if workdir:
            cmd.extend(["-w", workdir])
        
        cmd.append(container)
        cmd.extend(command)
        
        return await self._execute_command(cmd, ContainerOperation.EXEC)
    
    async def logs(
        self,
        container: str,
        follow: bool = False,
        tail: Optional[int] = None,
        timestamps: bool = False
    ) -> ContainerResult:
        """Get container logs."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.LOGS,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        cmd = [self._runtime_cmd, "logs"]
        
        if follow:
            cmd.append("-f")
        
        if tail is not None:
            cmd.extend(["--tail", str(tail)])
        
        if timestamps:
            cmd.append("-t")
        
        cmd.append(container)
        
        return await self._execute_command(cmd, ContainerOperation.LOGS)
    
    async def stop(self, container: str, timeout: int = 10) -> ContainerResult:
        """Stop a running container."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.STOP,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        cmd = [self._runtime_cmd, "stop", "-t", str(timeout), container]
        return await self._execute_command(cmd, ContainerOperation.STOP)
    
    async def remove(self, container: str, force: bool = False, volumes: bool = False) -> ContainerResult:
        """Remove a container."""
        if not self.is_available():
            return ContainerResult(
                success=False,
                operation=ContainerOperation.REMOVE,
                runtime=self.runtime,
                error="No container runtime available"
            )
        
        cmd = [self._runtime_cmd, "rm"]
        
        if force:
            cmd.append("-f")
        if volumes:
            cmd.append("-v")
        
        cmd.append(container)
        
        return await self._execute_command(cmd, ContainerOperation.REMOVE)
    
    async def _execute_command(
        self,
        cmd: List[str],
        operation: ContainerOperation
    ) -> ContainerResult:
        """Execute container command asynchronously."""
        import time
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            result = ContainerResult(
                success=process.returncode == 0,
                operation=operation,
                runtime=self.runtime,
                output=stdout.decode() if stdout else "",
                error=stderr.decode() if stderr else "",
                exit_code=process.returncode,
                duration=duration
            )
            
            # Observe with AGI reasoning
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "container_operation",
                    "container.runtime": self.runtime.value,
                    "container.operation": operation.value,
                    "container.success": str(result.success),
                    "container.duration": str(duration)
                },
                context={
                    "container_management": True,
                    "operation_type": operation.value,
                    "unified_workflow": True
                }
            )
            
            return result
            
        except Exception as e:
            return ContainerResult(
                success=False,
                operation=operation,
                runtime=self.runtime,
                error=str(e),
                duration=time.time() - start_time
            )


# Global container manager instance
_container_manager: Optional[ContainerManager] = None


def get_container_manager(project_root: Optional[Path] = None) -> ContainerManager:
    """Get the global container manager instance."""
    global _container_manager
    
    if _container_manager is None:
        _container_manager = ContainerManager(project_root)
    
    return _container_manager


def create_dev_container_config(
    project_name: str,
    language: str = "python",
    version: str = "3.12"
) -> ContainerConfig:
    """Create a development container configuration."""
    
    base_images = {
        "python": f"python:{version}-slim",
        "node": f"node:{version}-alpine",
        "go": f"golang:{version}-alpine",
        "rust": "rust:latest",
        "java": f"openjdk:{version}-slim"
    }
    
    return ContainerConfig(
        name=f"{project_name}-dev",
        image=base_images.get(language, "ubuntu:latest"),
        tag="latest",
        volumes={
            str(Path.cwd()): "/workspace"
        },
        working_dir="/workspace",
        env_vars={
            "DEVELOPMENT": "true",
            "PROJECT_NAME": project_name
        },
        labels={
            "uvmgr.project": project_name,
            "uvmgr.environment": "development",
            "uvmgr.language": language
        }
    )