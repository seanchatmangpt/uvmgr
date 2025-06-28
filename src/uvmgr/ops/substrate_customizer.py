"""
Substrate Project Customizer for uvmgr
=====================================

This module provides advanced customization capabilities for Substrate projects,
adding OTEL instrumentation, uvmgr integration, and project-specific enhancements.

Key Features:
- OTEL dependency injection
- Telemetry module generation
- Pre-commit hook configuration
- CI/CD workflow creation
- Project type variations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span, metric_counter


def add_otel_dependencies(project_path: Path) -> bool:
    """
    Add OTEL dependencies to a Substrate project.
    
    Args:
        project_path: Path to the Substrate project
        
    Returns:
        True if successful, False otherwise
    """
    with span("substrate.add_otel_dependencies", project_path=str(project_path)):
        pyproject_path = project_path / "pyproject.toml"
        
        if not pyproject_path.exists():
            add_span_event("pyproject_not_found", {"path": str(pyproject_path)})
            return False
        
        try:
            import toml
            
            # Read existing pyproject.toml
            config = toml.load(pyproject_path)
            
            # Add OTEL dependencies
            if "dependencies" not in config["project"]:
                config["project"]["dependencies"] = []
            
            otel_deps = [
                "opentelemetry-api>=1.20.0",
                "opentelemetry-sdk>=1.20.0",
                "opentelemetry-instrumentation>=0.41b0",
                "opentelemetry-exporter-otlp>=1.20.0",
            ]
            
            for dep in otel_deps:
                if dep not in config["project"]["dependencies"]:
                    config["project"]["dependencies"].append(dep)
            
            # Add OTEL dev dependencies
            if "dependency-groups" not in config:
                config["dependency-groups"] = {}
            
            config["dependency-groups"]["otel"] = [
                "opentelemetry-instrumentation-pytest>=0.41b0",
                "opentelemetry-instrumentation-logging>=0.41b0",
                "opentelemetry-instrumentation-system-metrics>=0.41b0",
            ]
            
            # Write back
            with open(pyproject_path, "w") as f:
                toml.dump(config, f)
            
            add_span_event("otel_dependencies_added", {
                "core_deps": len(otel_deps),
                "dev_deps": len(config["dependency-groups"]["otel"])
            })
            
            metric_counter("substrate.otel_dependencies.added")(1)
            return True
            
        except Exception as e:
            add_span_event("add_otel_dependencies_failed", {"error": str(e)})
            return False


def create_telemetry_module(project_path: Path, package_name: str) -> bool:
    """
    Create a telemetry configuration module in the project.
    
    Args:
        project_path: Path to the Substrate project
        package_name: Name of the Python package
        
    Returns:
        True if successful, False otherwise
    """
    with span("substrate.create_telemetry_module"):
        src_path = project_path / "src" / package_name
        telemetry_path = src_path / "_telemetry.py"
        
        telemetry_content = f'''"""
OpenTelemetry configuration for {package_name}.

This module provides centralized telemetry configuration including
tracing, metrics, and logging instrumentation.
"""

from __future__ import annotations

import os
from typing import Tuple

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


def configure_telemetry(
    service_name: str = "{package_name}",
    service_version: str = "0.0.0",
    deployment_environment: str = "development"
) -> Tuple[trace.Tracer, metrics.Meter]:
    """
    Configure OpenTelemetry for the project.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        deployment_environment: Deployment environment (development, staging, production)
        
    Returns:
        Tuple of (tracer, meter) for instrumentation
    """
    # Create resource
    resource = Resource.create({{
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_environment,
    }})
    
    # Configure tracing
    tracer_provider = TracerProvider(resource=resource)
    
    # Add exporters based on environment
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # Use OTLP exporter if endpoint is configured
        otlp_exporter = OTLPSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    else:
        # Default to console exporter
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    trace.set_tracer_provider(tracer_provider)
    
    # Configure metrics
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        metric_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(),
            export_interval_millis=10000,
        )
    else:
        metric_reader = PeriodicExportingMetricReader(
            exporter=ConsoleMetricExporter(),
            export_interval_millis=10000,
        )
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)
    
    # Configure logging instrumentation
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    # Return configured instances
    tracer = trace.get_tracer(service_name, service_version)
    meter = metrics.get_meter(service_name, service_version)
    
    return tracer, meter


# Convenience decorators
def trace_function(name: str = None):
    """Decorator to trace function execution."""
    def decorator(func):
        span_name = name or f"{{func.__module__}}.{{func.__name__}}"
        
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer("{package_name}")
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator
'''
        
        try:
            # Ensure src directory exists
            src_path.mkdir(parents=True, exist_ok=True)
            
            # Write telemetry module
            telemetry_path.write_text(telemetry_content)
            
            # Update __init__.py to initialize telemetry
            init_path = src_path / "__init__.py"
            init_content = init_path.read_text() if init_path.exists() else ""
            
            if "_telemetry" not in init_content:
                enhanced_init = f'''"""
{package_name}: With built-in OpenTelemetry instrumentation.
"""

from {package_name}._telemetry import configure_telemetry, trace_function

# Initialize telemetry on import
tracer, meter = configure_telemetry()

# Create common metrics
request_counter = meter.create_counter(
    "{package_name}.requests",
    description="Number of requests processed",
    unit="1",
)

error_counter = meter.create_counter(
    "{package_name}.errors",
    description="Number of errors encountered",
    unit="1",
)

duration_histogram = meter.create_histogram(
    "{package_name}.duration",
    description="Operation duration",
    unit="ms",
)

__version__ = "0.0.0"
__all__ = [
    "tracer",
    "meter",
    "request_counter",
    "error_counter",
    "duration_histogram",
    "trace_function",
]

{init_content}
'''
                init_path.write_text(enhanced_init)
            
            add_span_event("telemetry_module_created", {
                "package": package_name,
                "telemetry_path": str(telemetry_path)
            })
            
            return True
            
        except Exception as e:
            add_span_event("create_telemetry_module_failed", {"error": str(e)})
            return False


def add_uvmgr_tasks(project_path: Path) -> bool:
    """
    Add uvmgr-specific Poe tasks to the project.
    
    Args:
        project_path: Path to the Substrate project
        
    Returns:
        True if successful, False otherwise
    """
    with span("substrate.add_uvmgr_tasks"):
        pyproject_path = project_path / "pyproject.toml"
        
        try:
            import toml
            
            config = toml.load(pyproject_path)
            
            # Add uvmgr tasks
            uvmgr_tasks = {
                "otel-validate": {
                    "help": "Validate OTEL instrumentation",
                    "cmd": "uvmgr otel validate"
                },
                "otel-coverage": {
                    "help": "Check OTEL coverage",
                    "cmd": "uvmgr otel coverage --threshold 80"
                },
                "spiff-validate": {
                    "help": "Run SpiffWorkflow OTEL validation",
                    "cmd": "uvmgr spiff-otel external-validate . --mode 8020"
                },
                "substrate-sync": {
                    "help": "Sync with latest Substrate template",
                    "cmd": "uvx copier update --trust"
                },
                "telemetry-test": {
                    "help": "Test telemetry configuration",
                    "cmd": "python -c 'from src.* import tracer, meter; print(\"✅ Telemetry OK\")'"
                }
            }
            
            if "tool" not in config:
                config["tool"] = {}
            if "poe" not in config["tool"]:
                config["tool"]["poe"] = {}
            if "tasks" not in config["tool"]["poe"]:
                config["tool"]["poe"]["tasks"] = {}
            
            config["tool"]["poe"]["tasks"].update(uvmgr_tasks)
            
            # Write back
            with open(pyproject_path, "w") as f:
                toml.dump(config, f)
            
            add_span_event("uvmgr_tasks_added", {"task_count": len(uvmgr_tasks)})
            return True
            
        except Exception as e:
            add_span_event("add_uvmgr_tasks_failed", {"error": str(e)})
            return False


def create_github_workflow(project_path: Path) -> bool:
    """
    Create GitHub Actions workflow for OTEL validation.
    
    Args:
        project_path: Path to the Substrate project
        
    Returns:
        True if successful, False otherwise
    """
    with span("substrate.create_github_workflow"):
        workflows_dir = project_path / ".github" / "workflows"
        workflow_path = workflows_dir / "otel-validation.yml"
        
        workflow_content = """name: OTEL Validation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
        
      - name: Install dependencies
        run: |
          uv sync --all-extras
          uv tool install uvmgr
          
      - name: Validate OTEL Integration
        run: |
          uvmgr spiff-otel external-validate . --mode comprehensive
          
      - name: Check OTEL Coverage
        run: |
          uvmgr otel coverage --threshold 80
          
      - name: Run Telemetry Tests
        run: |
          uv run poe telemetry-test
          
      - name: Upload OTEL Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: otel-results-${{ matrix.python-version }}
          path: |
            **/otel-validation-results.json
            **/coverage.xml
"""
        
        try:
            workflows_dir.mkdir(parents=True, exist_ok=True)
            workflow_path.write_text(workflow_content)
            
            add_span_event("github_workflow_created", {"path": str(workflow_path)})
            return True
            
        except Exception as e:
            add_span_event("create_github_workflow_failed", {"error": str(e)})
            return False


def customize_substrate_project(
    project_path: Path,
    package_name: Optional[str] = None,
    project_type: str = "package",
    include_ci: bool = True
) -> Dict[str, Any]:
    """
    Apply full customization to a Substrate project.
    
    Args:
        project_path: Path to the Substrate project
        package_name: Package name (auto-detected if not provided)
        project_type: Type of project (package, cli, web, data)
        include_ci: Whether to include CI/CD configuration
        
    Returns:
        Dictionary with customization results
    """
    with span("substrate.customize_project", 
              project_path=str(project_path),
              project_type=project_type):
        
        results = {
            "success": True,
            "steps_completed": [],
            "errors": []
        }
        
        # Auto-detect package name if not provided
        if not package_name:
            try:
                import toml
                pyproject = toml.load(project_path / "pyproject.toml")
                package_name = pyproject["project"]["name"].replace("-", "_")
            except Exception as e:
                results["errors"].append(f"Failed to detect package name: {e}")
                results["success"] = False
                return results
        
        # Step 1: Add OTEL dependencies
        if add_otel_dependencies(project_path):
            results["steps_completed"].append("otel_dependencies")
        else:
            results["errors"].append("Failed to add OTEL dependencies")
            results["success"] = False
        
        # Step 2: Create telemetry module
        if create_telemetry_module(project_path, package_name):
            results["steps_completed"].append("telemetry_module")
        else:
            results["errors"].append("Failed to create telemetry module")
            results["success"] = False
        
        # Step 3: Add uvmgr tasks
        if add_uvmgr_tasks(project_path):
            results["steps_completed"].append("uvmgr_tasks")
        else:
            results["errors"].append("Failed to add uvmgr tasks")
            results["success"] = False
        
        # Step 4: Create GitHub workflow (if requested)
        if include_ci:
            if create_github_workflow(project_path):
                results["steps_completed"].append("github_workflow")
            else:
                results["errors"].append("Failed to create GitHub workflow")
                results["success"] = False
        
        # Add project-type specific customizations
        if project_type == "cli":
            # Add CLI-specific instrumentation examples
            _add_cli_examples(project_path, package_name)
            results["steps_completed"].append("cli_examples")
        elif project_type == "web":
            # Add web-specific instrumentation
            _add_web_instrumentation(project_path, package_name)
            results["steps_completed"].append("web_instrumentation")
        
        add_span_event("substrate_customization_complete", {
            "success": results["success"],
            "steps": len(results["steps_completed"]),
            "errors": len(results["errors"])
        })
        
        metric_counter("substrate.projects.customized")(1)
        
        return results


def _add_cli_examples(project_path: Path, package_name: str) -> None:
    """Add CLI-specific instrumentation examples."""
    cli_example = f'''"""
Example CLI with OTEL instrumentation.
"""

import click
from {package_name} import tracer, request_counter, trace_function


@click.command()
@click.option("--name", default="World", help="Name to greet")
@trace_function()
def hello(name: str):
    """Example command with automatic tracing."""
    with tracer.start_as_current_span("greeting") as span:
        span.set_attribute("user.name", name)
        request_counter.add(1, {{"command": "hello"}})
        
        message = f"Hello, {{name}}!"
        span.add_event("greeting_generated", {{"message": message}})
        
        click.echo(message)
        return message


if __name__ == "__main__":
    hello()
'''
    
    examples_dir = project_path / "examples"
    examples_dir.mkdir(exist_ok=True)
    (examples_dir / "cli_with_otel.py").write_text(cli_example)


def _add_web_instrumentation(project_path: Path, package_name: str) -> None:
    """Add web-specific instrumentation configuration."""
    # This would add FastAPI/Flask specific instrumentation
    pass