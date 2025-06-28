# Substrate Project Customization Plan for uvmgr

## Overview
This document outlines the plan for customizing Substrate-generated Python projects to integrate with uvmgr's OTEL capabilities and development workflows.

## Phase 1: Initial Integration (Completed ✅)
- Created `substrate_integration.py` module for project generation
- Added CLI commands for creating and validating Substrate projects
- Implemented batch testing capabilities
- Successfully created test projects with uvmgr metadata

## Phase 2: OTEL Enhancement 🚀

### 2.1 Add OTEL Dependencies
Modify the project generation to include OTEL dependencies:

```toml
# Add to pyproject.toml dependencies
dependencies = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation>=0.41b0",
    "opentelemetry-exporter-otlp>=1.20.0",
]

[dependency-groups]
otel = [
    "opentelemetry-instrumentation-pytest>=0.41b0",
    "opentelemetry-instrumentation-logging>=0.41b0",
    "opentelemetry-instrumentation-system-metrics>=0.41b0",
]
```

### 2.2 Create OTEL Configuration Module
Add `src/{package_name}/_telemetry.py`:

```python
"""OpenTelemetry configuration for {project_name}."""

from opentelemetry import trace, metrics
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
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def configure_telemetry(service_name: str = "{project_name}"):
    """Configure OpenTelemetry for the project."""
    # Tracing
    tracer_provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    tracer_provider.add_span_processor(processor)
    trace.set_tracer_provider(tracer_provider)
    
    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        exporter=ConsoleMetricExporter(),
        export_interval_millis=10000,
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # Logging
    LoggingInstrumentor().instrument()
    
    return trace.get_tracer(service_name), metrics.get_meter(service_name)
```

### 2.3 Instrument Main Module
Update `src/{package_name}/__init__.py`:

```python
"""
{project_name}: {project_description}

This package includes built-in OpenTelemetry instrumentation.
"""

from {package_name}._telemetry import configure_telemetry

# Initialize telemetry on import
tracer, meter = configure_telemetry()

# Create metrics
request_counter = meter.create_counter(
    "{package_name}.requests",
    description="Number of requests",
    unit="1",
)

__version__ = "0.0.0"
__all__ = ["tracer", "meter", "request_counter"]
```

## Phase 3: Development Workflow Integration 🔧

### 3.1 Add uvmgr-specific Poe Tasks
Extend the poethepoet tasks in `pyproject.toml`:

```toml
[tool.poe.tasks.otel-validate]
help = "Validate OTEL instrumentation"
cmd = "uvmgr otel validate"

[tool.poe.tasks.otel-coverage]
help = "Check OTEL coverage"
cmd = "uvmgr otel coverage --threshold 80"

[tool.poe.tasks.spiff-validate]
help = "Run SpiffWorkflow OTEL validation"
cmd = "uvmgr spiff-otel validate"

[tool.poe.tasks.substrate-sync]
help = "Sync with latest Substrate template"
cmd = "uvx copier update --trust"
```

### 3.2 Pre-commit Hooks
Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: otel-validation
        name: OTEL Validation
        entry: uvmgr otel validate
        language: system
        pass_filenames: false
        
      - id: semconv-check
        name: Semantic Convention Check
        entry: uvmgr otel semconv --validate
        language: system
        pass_filenames: false
```

## Phase 4: CI/CD Integration 🚀

### 4.1 GitHub Actions Workflow
Create `.github/workflows/otel-validation.yml`:

```yaml
name: OTEL Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        
      - name: Install uvmgr
        run: |
          uv tool install uvmgr
          
      - name: Validate OTEL
        run: |
          uvmgr spiff-otel external-validate . --mode comprehensive
          
      - name: Check OTEL Coverage
        run: |
          uvmgr otel coverage --threshold 80
```

## Phase 5: Template Variations 🎨

### 5.1 Create Project Types
Implement different Substrate variations for common use cases:

1. **CLI Application**
   - Pre-configured with Click/Typer
   - OTEL instrumentation for commands
   - Performance tracking

2. **Web Service**
   - FastAPI/Flask integration
   - HTTP instrumentation
   - Request/response tracking

3. **Data Pipeline**
   - Pandas/Polars integration
   - Data processing instrumentation
   - Memory/CPU metrics

4. **ML Model**
   - MLOps instrumentation
   - Model performance tracking
   - Training metrics

### 5.2 Template Selection
Enhance the substrate command:

```python
uvmgr substrate create my-project --type cli --with-otel
uvmgr substrate create my-service --type web --framework fastapi
uvmgr substrate create my-pipeline --type data --with-dask
```

## Phase 6: Documentation & Examples 📚

### 6.1 Project README Template
Enhance the generated README with:
- OTEL usage examples
- Performance monitoring guide
- Troubleshooting section
- uvmgr integration guide

### 6.2 Example Code
Include example modules showing:
- Span creation patterns
- Metric collection
- Error tracking
- Performance optimization

## Phase 7: Advanced Features 🚀

### 7.1 Custom BPMN Workflows
Create project-specific workflows:
- Development workflow
- Testing workflow
- Deployment workflow
- Monitoring workflow

### 7.2 Project Health Dashboard
Implement a dashboard command:
```bash
uvmgr substrate dashboard ./my-project
```

Shows:
- OTEL coverage
- Code quality metrics
- Dependency health
- Performance baselines

## Implementation Timeline

1. **Week 1**: Phase 2 - OTEL Enhancement
2. **Week 2**: Phase 3 - Development Workflow
3. **Week 3**: Phase 4 - CI/CD Integration
4. **Week 4**: Phase 5 - Template Variations
5. **Week 5-6**: Phase 6 - Documentation
6. **Week 7-8**: Phase 7 - Advanced Features

## Success Metrics

- ✅ All Substrate projects have OTEL out-of-the-box
- ✅ 80%+ OTEL coverage in generated projects
- ✅ < 5 minute setup time for new projects
- ✅ Seamless integration with existing tools
- ✅ Positive developer experience feedback

## Next Steps

1. Implement OTEL enhancement module
2. Create template variation system
3. Build example projects
4. Write comprehensive documentation
5. Gather user feedback and iterate