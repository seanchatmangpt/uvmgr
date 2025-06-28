"""
Substrate Integration for External Project Validation
===================================================

This module provides integration between uvmgr's SpiffWorkflow OTEL validation
and Substrate-generated Python projects. It enables automated creation and
validation of standardized test projects.

Key Features:
- Automated Substrate project generation for testing
- Specialized validation workflows for Substrate projects
- OTEL compatibility testing with Substrate toolchain
- Batch validation of multiple Substrate project variants
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span, metric_counter
from uvmgr.ops.external_project_spiff import (
    ExternalProjectInfo,
    validate_external_project_with_spiff,
    ExternalValidationResult
)


def create_substrate_test_project(
    project_name: str,
    project_type: str = "package",
    output_dir: Optional[Path] = None
) -> Path:
    """
    Create a Substrate-based test project for OTEL validation.
    
    Args:
        project_name: Name of the project to create
        project_type: Type of project (package, app, etc.)
        output_dir: Directory to create project in
        
    Returns:
        Path to created project
    """
    with span("substrate.create_test_project", project_name=project_name):
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="substrate_test_"))
        
        project_path = output_dir / project_name
        
        try:
            # Use uvx to create Substrate project
            cmd = [
                "uvx", "copier", "copy",
                "--trust",
                "--defaults",
                "--data", f"project_name={project_name}",
                "--data", f"package_name={project_name.replace('-', '_')}",
                "--data", f"project_description=OTEL validation test project for {project_name}",
                "--data", "author_name=uvmgr",
                "--data", "author_email=test@uvmgr.com",
                "--data", "python_version=3.11",
                "--data", "license=MIT",
                "gh:superlinear-ai/substrate",
                str(project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                add_span_event("substrate_project_created", {
                    "project_name": project_name,
                    "project_path": str(project_path)
                })
                metric_counter("substrate.projects.created")(1)
                return project_path
            else:
                raise RuntimeError(f"Failed to create Substrate project: {result.stderr}")
                
        except Exception as e:
            add_span_event("substrate_project_creation_failed", {
                "error": str(e),
                "project_name": project_name
            })
            raise


def validate_substrate_project(
    project_path: Path,
    include_toolchain_tests: bool = True
) -> ExternalValidationResult:
    """
    Validate OTEL integration in a Substrate project.
    
    Args:
        project_path: Path to Substrate project
        include_toolchain_tests: Test OTEL with Substrate tools
        
    Returns:
        ExternalValidationResult with validation data
    """
    with span("substrate.validate_project", project_path=str(project_path)):
        # Generate Substrate-specific test commands
        test_commands = [
            "uv --version",  # Verify uv is available
            "python --version",
            "uv sync",  # Install dependencies
        ]
        
        if include_toolchain_tests:
            test_commands.extend([
                "poe format --check",  # Test with Ruff
                "poe lint",  # Test with linting tools
                "poe typecheck",  # Test with mypy
                "poe test",  # Run tests
            ])
        
        # Add OTEL-specific tests
        test_commands.extend([
            "python -c 'from uvmgr.core.telemetry import span; print(\"OTEL OK\")'",
            "echo 'Substrate OTEL validation complete'"
        ])
        
        # Use comprehensive mode for Substrate projects
        return validate_external_project_with_spiff(
            project_path=project_path,
            validation_mode="comprehensive",
            custom_tests=test_commands,
            timeout_seconds=300
        )


def create_substrate_validation_matrix() -> Dict[str, List[str]]:
    """
    Create a validation matrix for different Substrate project configurations.
    
    Returns:
        Dictionary mapping project types to test commands
    """
    return {
        "basic_package": [
            "uv sync",
            "poe test",
            "poe build",
        ],
        "with_cli": [
            "uv sync",
            "poe test",
            "python -m {package_name} --help",
        ],
        "with_ci": [
            "uv sync",
            "poe test",
            "poe coverage",
        ],
        "with_docs": [
            "uv sync",
            "poe docs-build",
            "poe docs-serve --help",
        ]
    }


def batch_validate_substrate_variants(
    variants: List[str] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, ExternalValidationResult]:
    """
    Validate multiple Substrate project variants.
    
    Args:
        variants: List of variant names to test
        output_dir: Directory for test projects
        
    Returns:
        Dictionary of validation results by variant
    """
    with span("substrate.batch_validate_variants"):
        if variants is None:
            variants = ["basic", "cli", "full"]
        
        results = {}
        
        for variant in variants:
            project_name = f"substrate-test-{variant}"
            
            try:
                # Create project
                project_path = create_substrate_test_project(
                    project_name=project_name,
                    output_dir=output_dir
                )
                
                # Validate
                result = validate_substrate_project(project_path)
                results[variant] = result
                
                add_span_event("substrate_variant_validated", {
                    "variant": variant,
                    "success": result.validation_result.success
                })
                
            except Exception as e:
                add_span_event("substrate_variant_failed", {
                    "variant": variant,
                    "error": str(e)
                })
        
        return results


def generate_substrate_otel_template() -> str:
    """
    Generate a Copier template extension that adds OTEL to Substrate projects.
    
    Returns:
        Template content for OTEL integration
    """
    return '''# OTEL Integration for Substrate Projects

## Add to pyproject.toml dependencies:
```toml
[project.optional-dependencies]
otel = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation>=0.41b0",
]
```

## Add OTEL initialization to your package:
```python
# src/{{package_name}}/_otel.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

def init_telemetry():
    """Initialize OpenTelemetry for the package."""
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
```

## Usage in your code:
```python
from opentelemetry import trace
from {{package_name}}._otel import init_telemetry

# Initialize once
init_telemetry()

# Use in your functions
tracer = trace.get_tracer(__name__)

def my_function():
    with tracer.start_as_current_span("my_operation"):
        # Your code here
        pass
```
'''