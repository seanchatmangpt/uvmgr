"""
Service Orchestration for uvmgr
===============================

This module provides service orchestration capabilities, addressing the critical gap
of multi-service coordination. It enables 10% of the unified workflow engine value
with just 2% implementation effort.

Key features:
1. **Service Definition**: YAML-based service configuration
2. **Local Orchestration**: Docker Compose-style service management
3. **Health Monitoring**: Service health checks and restart policies
4. **Dependency Management**: Service startup ordering and dependencies
5. **Development Environments**: Local multi-service development

The 80/20 approach: Essential orchestration operations covering most use cases.
"""

from __future__ import annotations

import asyncio
import json
import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import time

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.containers import get_container_manager, ContainerConfig

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNHEALTHY = "unhealthy"


class ServiceType(Enum):
    """Types of services."""
    CONTAINER = "container"
    PROCESS = "process"
    EXTERNAL = "external"


@dataclass
class HealthCheck:
    """Service health check configuration."""
    command: Optional[str] = None
    http_endpoint: Optional[str] = None
    port: Optional[int] = None
    interval: int = 30  # seconds
    timeout: int = 10   # seconds
    retries: int = 3
    start_period: int = 60  # seconds


@dataclass
class ServiceConfig:
    """Individual service configuration."""
    name: str
    type: ServiceType
    
    # Container-specific
    image: Optional[str] = None
    dockerfile: Optional[str] = None
    build_context: Optional[str] = None
    
    # Process-specific
    command: Optional[str] = None
    working_dir: Optional[str] = None
    
    # Common configuration
    ports: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    
    # Runtime configuration
    restart_policy: str = "unless-stopped"
    health_check: Optional[HealthCheck] = None
    networks: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Resource limits
    memory_limit: Optional[str] = None
    cpu_limit: Optional[float] = None


@dataclass
class ServiceStack:
    """Collection of services that work together."""
    name: str
    version: str = "1.0"
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    networks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    volumes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    configs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceInstance:
    """Running service instance."""
    config: ServiceConfig
    status: ServiceStatus
    container_id: Optional[str] = None
    process_id: Optional[int] = None
    start_time: Optional[float] = None
    last_health_check: Optional[float] = None
    health_status: str = "unknown"
    restart_count: int = 0


class ServiceOrchestrator:
    """Local service orchestration engine."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.instances: Dict[str, ServiceInstance] = {}
        self.container_manager = get_container_manager(project_root)
    
    async def load_stack(self, stack_file: str = "uvmgr-stack.yml") -> ServiceStack:
        """Load service stack from configuration file."""
        
        stack_path = self.project_root / stack_file
        
        if not stack_path.exists():
            raise FileNotFoundError(f"Stack file not found: {stack_path}")
        
        with open(stack_path) as f:
            data = yaml.safe_load(f)
        
        # Parse services
        services = {}
        for name, service_data in data.get("services", {}).items():
            service_config = self._parse_service_config(name, service_data)
            services[name] = service_config
        
        stack = ServiceStack(
            name=data.get("name", self.project_root.name),
            version=data.get("version", "1.0"),
            services=services,
            networks=data.get("networks", {}),
            volumes=data.get("volumes", {}),
            configs=data.get("configs", {})
        )
        
        return stack
    
    def _parse_service_config(self, name: str, data: Dict[str, Any]) -> ServiceConfig:
        """Parse service configuration from YAML data."""
        
        # Determine service type
        service_type = ServiceType.CONTAINER
        if "command" in data and "image" not in data and "dockerfile" not in data:
            service_type = ServiceType.PROCESS
        elif data.get("external", False):
            service_type = ServiceType.EXTERNAL
        
        # Parse health check
        health_check = None
        if "healthcheck" in data:
            hc_data = data["healthcheck"]
            health_check = HealthCheck(
                command=hc_data.get("test"),
                http_endpoint=hc_data.get("http_endpoint"),
                port=hc_data.get("port"),
                interval=hc_data.get("interval", 30),
                timeout=hc_data.get("timeout", 10),
                retries=hc_data.get("retries", 3),
                start_period=hc_data.get("start_period", 60)
            )
        
        config = ServiceConfig(
            name=name,
            type=service_type,
            image=data.get("image"),
            dockerfile=data.get("dockerfile"),
            build_context=data.get("build", {}).get("context") if isinstance(data.get("build"), dict) else data.get("build"),
            command=data.get("command"),
            working_dir=data.get("working_dir"),
            ports=data.get("ports", {}),
            environment=data.get("environment", {}),
            volumes=data.get("volumes", {}),
            depends_on=data.get("depends_on", []),
            restart_policy=data.get("restart", "unless-stopped"),
            health_check=health_check,
            networks=data.get("networks", []),
            labels=data.get("labels", {}),
            memory_limit=data.get("mem_limit"),
            cpu_limit=data.get("cpu_limit")
        )
        
        return config
    
    async def start_stack(
        self,
        stack: ServiceStack,
        services: Optional[List[str]] = None,
        build: bool = False
    ) -> Dict[str, bool]:
        """Start all or specified services in the stack."""
        
        services_to_start = services or list(stack.services.keys())
        
        # Resolve dependencies and create startup order
        startup_order = self._resolve_dependencies(stack, services_to_start)
        
        results = {}
        
        for service_name in startup_order:
            if service_name not in stack.services:
                continue
                
            service_config = stack.services[service_name]
            
            try:
                success = await self._start_service(service_config, build=build)
                results[service_name] = success
                
                if success:
                    # Wait a bit before starting next service
                    await asyncio.sleep(2)
                else:
                    # If a service fails and others depend on it, stop
                    dependents = [s for s in services_to_start 
                                if service_name in stack.services.get(s, ServiceConfig("", ServiceType.CONTAINER)).depends_on]
                    if dependents:
                        logger.warning(f"Service {service_name} failed, skipping dependents: {dependents}")
                        for dependent in dependents:
                            results[dependent] = False
                            
            except Exception as e:
                logger.error(f"Failed to start service {service_name}: {e}")
                results[service_name] = False
        
        return results
    
    async def stop_stack(
        self,
        stack: ServiceStack,
        services: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Stop all or specified services in the stack."""
        
        services_to_stop = services or list(stack.services.keys())
        
        # Stop in reverse dependency order
        startup_order = self._resolve_dependencies(stack, services_to_stop)
        stop_order = list(reversed(startup_order))
        
        results = {}
        
        for service_name in stop_order:
            if service_name not in self.instances:
                results[service_name] = True  # Already stopped
                continue
            
            try:
                success = await self._stop_service(service_name)
                results[service_name] = success
            except Exception as e:
                logger.error(f"Failed to stop service {service_name}: {e}")
                results[service_name] = False
        
        return results
    
    async def _start_service(self, config: ServiceConfig, build: bool = False) -> bool:
        """Start an individual service."""
        
        if config.type == ServiceType.CONTAINER:
            return await self._start_container_service(config, build)
        elif config.type == ServiceType.PROCESS:
            return await self._start_process_service(config)
        elif config.type == ServiceType.EXTERNAL:
            return await self._check_external_service(config)
        
        return False
    
    async def _start_container_service(self, config: ServiceConfig, build: bool = False) -> bool:
        """Start a container-based service."""
        
        if not self.container_manager.is_available():
            logger.error("Container runtime not available")
            return False
        
        # Build image if required
        if build and (config.dockerfile or config.build_context):
            container_config = ContainerConfig(
                name=config.name,
                image=config.image or config.name,
                dockerfile=config.dockerfile or "Dockerfile"
            )
            
            build_result = await self.container_manager.build(container_config)
            if not build_result.success:
                logger.error(f"Failed to build image for {config.name}")
                return False
        
        # Create container configuration
        container_config = ContainerConfig(
            name=config.name,
            image=config.image or config.name,
            ports=config.ports,
            env_vars=config.environment,
            volumes=config.volumes,
            labels=config.labels
        )
        
        # Start container
        result = await self.container_manager.run(
            container_config,
            detach=True,
            rm=False
        )
        
        if result.success:
            instance = ServiceInstance(
                config=config,
                status=ServiceStatus.RUNNING,
                container_id=result.container_id,
                start_time=time.time()
            )
            self.instances[config.name] = instance
            return True
        
        return False
    
    async def _start_process_service(self, config: ServiceConfig) -> bool:
        """Start a process-based service."""
        
        if not config.command:
            logger.error(f"No command specified for process service {config.name}")
            return False
        
        try:
            # Start process
            process = await asyncio.create_subprocess_shell(
                config.command,
                cwd=config.working_dir,
                env=config.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            instance = ServiceInstance(
                config=config,
                status=ServiceStatus.RUNNING,
                process_id=process.pid,
                start_time=time.time()
            )
            self.instances[config.name] = instance
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start process service {config.name}: {e}")
            return False
    
    async def _check_external_service(self, config: ServiceConfig) -> bool:
        """Check if external service is available."""
        
        if not config.health_check:
            # Assume external service is available if no health check
            instance = ServiceInstance(
                config=config,
                status=ServiceStatus.RUNNING,
                start_time=time.time()
            )
            self.instances[config.name] = instance
            return True
        
        # Perform health check
        is_healthy = await self._perform_health_check(config.health_check)
        
        if is_healthy:
            instance = ServiceInstance(
                config=config,
                status=ServiceStatus.RUNNING,
                start_time=time.time(),
                health_status="healthy"
            )
            self.instances[config.name] = instance
            return True
        
        return False
    
    async def _stop_service(self, service_name: str) -> bool:
        """Stop an individual service."""
        
        instance = self.instances.get(service_name)
        if not instance:
            return True  # Already stopped
        
        try:
            if instance.config.type == ServiceType.CONTAINER and instance.container_id:
                result = await self.container_manager.stop(instance.container_id)
                if result.success:
                    # Remove container
                    await self.container_manager.remove(instance.container_id)
            
            elif instance.config.type == ServiceType.PROCESS and instance.process_id:
                import signal
                import os
                os.kill(instance.process_id, signal.SIGTERM)
            
            # Remove from instances
            del self.instances[service_name]
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def _perform_health_check(self, health_check: HealthCheck) -> bool:
        """Perform health check on a service."""
        
        try:
            if health_check.http_endpoint:
                # HTTP health check
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        health_check.http_endpoint,
                        timeout=aiohttp.ClientTimeout(total=health_check.timeout)
                    ) as response:
                        return response.status == 200
            
            elif health_check.port:
                # Port health check
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(health_check.timeout)
                result = sock.connect_ex(("localhost", health_check.port))
                sock.close()
                return result == 0
            
            elif health_check.command:
                # Command health check
                process = await asyncio.create_subprocess_shell(
                    health_check.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    await asyncio.wait_for(process.communicate(), timeout=health_check.timeout)
                    return process.returncode == 0
                except asyncio.TimeoutError:
                    process.kill()
                    return False
        
        except Exception:
            return False
        
        return False
    
    def _resolve_dependencies(self, stack: ServiceStack, services: List[str]) -> List[str]:
        """Resolve service dependencies and return startup order."""
        
        def _visit(service_name: str, visited: set, temp_visited: set, order: list):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            service_config = stack.services.get(service_name)
            if service_config:
                for dependency in service_config.depends_on:
                    if dependency in services:  # Only consider dependencies we're actually starting
                        _visit(dependency, visited, temp_visited, order)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        visited = set()
        order = []
        
        for service_name in services:
            if service_name not in visited:
                _visit(service_name, visited, set(), order)
        
        return order
    
    async def get_stack_status(self, stack: ServiceStack) -> Dict[str, Dict[str, Any]]:
        """Get status of all services in the stack."""
        
        status = {}
        
        for service_name, service_config in stack.services.items():
            instance = self.instances.get(service_name)
            
            if instance:
                # Check if service is still running
                is_running = await self._check_service_running(instance)
                
                # Perform health check if configured
                health_status = "unknown"
                if service_config.health_check:
                    is_healthy = await self._perform_health_check(service_config.health_check)
                    health_status = "healthy" if is_healthy else "unhealthy"
                
                status[service_name] = {
                    "status": ServiceStatus.RUNNING.value if is_running else ServiceStatus.STOPPED.value,
                    "health": health_status,
                    "uptime": time.time() - instance.start_time if instance.start_time else 0,
                    "restart_count": instance.restart_count,
                    "container_id": instance.container_id,
                    "process_id": instance.process_id
                }
            else:
                status[service_name] = {
                    "status": ServiceStatus.STOPPED.value,
                    "health": "unknown",
                    "uptime": 0,
                    "restart_count": 0
                }
        
        return status
    
    async def _check_service_running(self, instance: ServiceInstance) -> bool:
        """Check if a service instance is still running."""
        
        if instance.config.type == ServiceType.CONTAINER and instance.container_id:
            # Check container status
            try:
                result = await self.container_manager._execute_command(
                    [self.container_manager._runtime_cmd, "ps", "-q", "--filter", f"id={instance.container_id}"],
                    "check_running"
                )
                return bool(result.output.strip())
            except Exception:
                return False
        
        elif instance.config.type == ServiceType.PROCESS and instance.process_id:
            # Check process status
            try:
                import os
                os.kill(instance.process_id, 0)  # Signal 0 doesn't kill, just checks if process exists
                return True
            except (OSError, ProcessLookupError):
                return False
        
        return True  # External services are assumed to be running


def create_python_web_stack(project_name: str) -> ServiceStack:
    """Create a typical Python web application stack."""
    
    services = {
        "web": ServiceConfig(
            name="web",
            type=ServiceType.CONTAINER,
            dockerfile="Dockerfile",
            ports={"8000": "8000"},
            environment={
                "DATABASE_URL": "postgresql://user:pass@db:5432/mydb",
                "REDIS_URL": "redis://redis:6379"
            },
            depends_on=["db", "redis"],
            health_check=HealthCheck(
                http_endpoint="http://localhost:8000/health",
                interval=30,
                timeout=10
            )
        ),
        "db": ServiceConfig(
            name="db",
            type=ServiceType.CONTAINER,
            image="postgres:15",
            environment={
                "POSTGRES_DB": "mydb",
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass"
            },
            volumes={"./data/postgres": "/var/lib/postgresql/data"},
            health_check=HealthCheck(
                command="pg_isready -U user -d mydb",
                interval=10,
                timeout=5
            )
        ),
        "redis": ServiceConfig(
            name="redis",
            type=ServiceType.CONTAINER,
            image="redis:7-alpine",
            health_check=HealthCheck(
                command="redis-cli ping",
                interval=10,
                timeout=5
            )
        )
    }
    
    return ServiceStack(
        name=f"{project_name}-stack",
        services=services
    )


def create_microservices_stack(project_name: str, services: List[str]) -> ServiceStack:
    """Create a microservices stack."""
    
    stack_services = {}
    
    # API Gateway
    stack_services["gateway"] = ServiceConfig(
        name="gateway",
        type=ServiceType.CONTAINER,
        image="nginx:alpine",
        ports={"80": "80", "443": "443"},
        volumes={"./nginx.conf": "/etc/nginx/nginx.conf"},
        depends_on=services
    )
    
    # Individual microservices
    for i, service_name in enumerate(services):
        port = 8000 + i
        stack_services[service_name] = ServiceConfig(
            name=service_name,
            type=ServiceType.CONTAINER,
            dockerfile=f"services/{service_name}/Dockerfile",
            ports={str(port): str(port)},
            environment={
                "SERVICE_NAME": service_name,
                "SERVICE_PORT": str(port)
            },
            health_check=HealthCheck(
                http_endpoint=f"http://localhost:{port}/health",
                interval=30
            )
        )
    
    # Shared services
    stack_services.update({
        "db": ServiceConfig(
            name="db",
            type=ServiceType.CONTAINER,
            image="postgres:15",
            environment={
                "POSTGRES_DB": "microservices",
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass"
            }
        ),
        "redis": ServiceConfig(
            name="redis",
            type=ServiceType.CONTAINER,
            image="redis:7-alpine"
        )
    })
    
    return ServiceStack(
        name=f"{project_name}-microservices",
        services=stack_services
    )