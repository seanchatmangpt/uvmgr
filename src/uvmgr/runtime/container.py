"""
Container Runtime Operations
============================

This module provides container management operations with Docker/Podman support.
Implements the 80/20 principle: focuses on the most common container operations
that provide 80% of the value for typical Python development workflows.

Key Features:
- Container lifecycle management (create, start, stop, remove)
- Image operations (build, pull, push, list)
- Volume and network management
- Container inspection and logs
- Docker Compose integration
- Cross-platform support (Docker/Podman)
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import ContainerAttributes, ContainerOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span, record_exception


@dataclass
class ContainerInfo:
    """Container information."""
    id: str
    name: str
    image: str
    status: str
    ports: List[str]
    created: str
    command: str


@dataclass
class ImageInfo:
    """Container image information."""
    id: str
    repository: str
    tag: str
    size: str
    created: str


def detect_container_runtime() -> str:
    """Detect available container runtime (docker or podman)."""
    with span("container.runtime.detect"):
        # Try Docker first (most common)
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                add_span_event("container.runtime.detected", {"runtime": "docker"})
                return "docker"
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try Podman as fallback
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                add_span_event("container.runtime.detected", {"runtime": "podman"})
                return "podman"
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        raise RuntimeError("No container runtime (docker/podman) found")


@instrument_command("container_list")
def list_containers(all_containers: bool = False, runtime: Optional[str] = None) -> List[ContainerInfo]:
    """List containers."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.list",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.LIST}):
        
        cmd = [runtime, "ps"]
        if all_containers:
            cmd.append("-a")
        cmd.extend(["--format", "json"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    containers.append(ContainerInfo(
                        id=data.get("ID", "")[:12],
                        name=data.get("Names", ""),
                        image=data.get("Image", ""),
                        status=data.get("Status", ""),
                        ports=data.get("Ports", "").split(",") if data.get("Ports") else [],
                        created=data.get("CreatedAt", ""),
                        command=data.get("Command", "")
                    ))
            
            duration = time.time() - start_time
            metric_histogram("container.operation.duration")(duration, {
                "operation": "list",
                "runtime": runtime
            })
            metric_counter("container.operations")(1, {
                "operation": "list",
                "runtime": runtime
            })
            
            add_span_attributes(**{
                "container.count": len(containers),
                "operation.duration": duration
            })
            
            return containers
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "list"
            })
            raise RuntimeError(f"Failed to list containers: {e.stderr}")


@instrument_command("container_create")
def create_container(image: str, name: Optional[str] = None, 
                    ports: Optional[Dict[str, str]] = None,
                    volumes: Optional[Dict[str, str]] = None,
                    environment: Optional[Dict[str, str]] = None,
                    command: Optional[str] = None,
                    runtime: Optional[str] = None) -> str:
    """Create a new container."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.create",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.CREATE,
                 ContainerAttributes.IMAGE: image}):
        
        cmd = [runtime, "create"]
        
        if name:
            cmd.extend(["--name", name])
        
        if ports:
            for host_port, container_port in ports.items():
                cmd.extend(["-p", f"{host_port}:{container_port}"])
        
        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        if environment:
            for key, value in environment.items():
                cmd.extend(["-e", f"{key}={value}"])
        
        cmd.append(image)
        
        if command:
            cmd.extend(command.split())
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            
            container_id = result.stdout.strip()
            
            duration = time.time() - start_time
            metric_histogram("container.operation.duration")(duration, {
                "operation": "create",
                "runtime": runtime
            })
            metric_counter("container.operations")(1, {
                "operation": "create",
                "runtime": runtime
            })
            
            add_span_attributes(**{
                ContainerAttributes.ID: container_id,
                "operation.duration": duration
            })
            
            return container_id
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "create",
                "container.image": image
            })
            raise RuntimeError(f"Failed to create container: {e.stderr}")


@instrument_command("container_start")
def start_container(container: str, runtime: Optional[str] = None) -> bool:
    """Start a container."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.start",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.START,
                 ContainerAttributes.ID: container}):
        
        try:
            subprocess.run(
                [runtime, "start", container],
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            metric_counter("container.operations")(1, {
                "operation": "start",
                "runtime": runtime
            })
            
            return True
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "start",
                "container.id": container
            })
            raise RuntimeError(f"Failed to start container {container}: {e.stderr}")


@instrument_command("container_stop")
def stop_container(container: str, timeout: int = 10, runtime: Optional[str] = None) -> bool:
    """Stop a container."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.stop",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.STOP,
                 ContainerAttributes.ID: container}):
        
        try:
            subprocess.run(
                [runtime, "stop", "-t", str(timeout), container],
                capture_output=True,
                text=True,
                timeout=timeout + 30,
                check=True
            )
            
            metric_counter("container.operations")(1, {
                "operation": "stop",
                "runtime": runtime
            })
            
            return True
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "stop",
                "container.id": container
            })
            raise RuntimeError(f"Failed to stop container {container}: {e.stderr}")


@instrument_command("container_build")
def build_image(dockerfile_path: Path, tag: str, 
               build_args: Optional[Dict[str, str]] = None,
               runtime: Optional[str] = None) -> bool:
    """Build container image from Dockerfile."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.build",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.BUILD,
                 ContainerAttributes.IMAGE: tag}):
        
        cmd = [runtime, "build", "-t", tag]
        
        if build_args:
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
        
        cmd.append(str(dockerfile_path.parent))
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
                check=True
            )
            
            duration = time.time() - start_time
            metric_histogram("container.build.duration")(duration, {
                "runtime": runtime
            })
            metric_counter("container.builds")(1, {
                "runtime": runtime,
                "success": "true"
            })
            
            add_span_attributes(**{
                "build.duration": duration,
                "build.success": True
            })
            
            return True
            
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            metric_counter("container.builds")(1, {
                "runtime": runtime,
                "success": "false"
            })
            
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "build",
                "container.image": tag,
                "build.duration": duration
            })
            raise RuntimeError(f"Failed to build image {tag}: {e.stderr}")


@instrument_command("container_logs")
def get_container_logs(container: str, lines: int = 100, 
                      follow: bool = False, runtime: Optional[str] = None) -> str:
    """Get container logs."""
    runtime = runtime or detect_container_runtime()
    
    with span("container.logs",
              **{ContainerAttributes.RUNTIME: runtime,
                 ContainerAttributes.OPERATION: ContainerOperations.LOGS,
                 ContainerAttributes.ID: container}):
        
        cmd = [runtime, "logs"]
        
        if lines > 0:
            cmd.extend(["--tail", str(lines)])
        
        if follow:
            cmd.append("-f")
        
        cmd.append(container)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30 if not follow else None,
                check=True
            )
            
            metric_counter("container.operations")(1, {
                "operation": "logs",
                "runtime": runtime
            })
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "container.runtime": runtime,
                "container.operation": "logs",
                "container.id": container
            })
            raise RuntimeError(f"Failed to get logs for container {container}: {e.stderr}")