# Weaver Forge - OpenTelemetry Implementation for uvmgr

This directory contains the OpenTelemetry Weaver Forge implementation for uvmgr, providing comprehensive observability through standardized telemetry.

## Overview

The implementation includes:
- **Semantic Conventions**: Standardized attributes for CLI commands, package operations, builds, and tests
- **Automatic Instrumentation**: Decorators that automatically trace command execution
- **Metrics Collection**: Counters, histograms, and gauges for operational insights
- **Error Tracking**: Automatic exception recording with semantic attributes
- **Weaver Integration**: Code generation from semantic convention definitions

## Directory Structure

```
weaver-forge/
├── registry/                      # Weaver semantic convention registry
│   ├── registry_manifest.yaml     # Registry metadata
│   └── uvmgr.yaml                # Semantic convention definitions
├── command-instrumentation-example.py  # Example instrumentation patterns
├── validate_semconv.py            # Validation and code generation script
└── docs/                         # Generated documentation (after validation)
```

## Quick Start

### 1. Validate Semantic Conventions
```bash
python weaver-forge/validate_semconv.py
```

### 2. Use OTEL Commands
```bash
# Validate configuration
uvmgr otel validate

# Check instrumentation status
uvmgr otel status

# Generate test telemetry
uvmgr otel test

# Manage semantic conventions
uvmgr otel semconv --validate --generate
```

### 3. Run with Docker
```bash
# Start OTEL infrastructure
docker-compose -f docker-compose.otel.yml up -d

# Run the demo
./demo/otel-demo.sh
```

## Implementation Details

### Instrumentation Decorator

The `@instrument_command` decorator automatically:
- Creates spans for command execution
- Records command arguments and options
- Tracks success/failure status
- Measures execution time
- Increments metrics counters

Example:
```python
@app.command()
@instrument_command("deps_add", track_args=True)
def add(pkgs: list[str], dev: bool = False):
    # Command is automatically instrumented
    pass
```

### Semantic Conventions

Attributes follow OpenTelemetry standards:
- `cli.command`: Primary command name
- `package.operation`: Package management operation type
- `build.type`: Build artifact type (wheel, sdist, exe)
- `test.framework`: Testing framework used

### Generated Code

Running validation generates:
- `src/uvmgr/core/semconv.py`: Python constants for attributes
- `docs/`: Markdown documentation of conventions

## Customization

### Adding New Conventions

1. Edit `registry/uvmgr.yaml`:
```yaml
- id: my_attribute
  type: string
  brief: 'Description of the attribute'
  note: 'Detailed explanation'
  examples: ['value1', 'value2']
  requirement_level: recommended
  stability: stable
```

2. Validate and regenerate:
```bash
python weaver-forge/validate_semconv.py
```

### Creating New Instrumentation

1. Import the decorator:
```python
from uvmgr.core.instrumentation import instrument_command
```

2. Apply to commands:
```python
@instrument_command("command_name")
def my_command():
    pass
```

3. Add custom attributes:
```python
from uvmgr.core.instrumentation import add_span_attributes

add_span_attributes(custom_attr="value")
```

## Testing

Run the test suite:
```bash
pytest tests/e2e/test_otel_instrumentation.py
```

With a real collector:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
pytest tests/e2e/test_otel_instrumentation.py::test_real_otel_integration -v
```

## Troubleshooting

### No Traces Appearing
1. Check collector is running: `docker ps`
2. Verify endpoint: `uvmgr otel validate`
3. Check for errors in uvmgr output

### Validation Errors
1. Ensure all attributes have `stability` field
2. Remove deprecated `prefix` fields
3. Add `note` field to all attributes

### Performance Issues
1. Batch size: Adjust in `otel-collector-config.yaml`
2. Memory limits: Increase collector memory limit
3. Sampling: Implement sampling for high-volume operations

## Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Weaver GitHub](https://github.com/open-telemetry/weaver)
- [Semantic Conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/)
- [OTLP Specification](https://opentelemetry.io/docs/reference/specification/protocol/otlp/)