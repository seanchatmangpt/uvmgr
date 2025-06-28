# OpenTelemetry Integration Guide for uvmgr

This guide explains how to use OpenTelemetry (OTEL) with uvmgr for observability, including tracing, metrics, and logging.

## Overview

uvmgr includes built-in OpenTelemetry instrumentation that automatically tracks:
- CLI command execution with semantic conventions
- Package management operations
- Build and test processes
- Subprocess execution
- Errors and exceptions

## Quick Start

### 1. Run OTEL Infrastructure

Start the OTEL collector, Jaeger, Prometheus, and Grafana:

```bash
docker-compose -f docker-compose.otel.yml up -d
```

This starts:
- **OTEL Collector**: Receives and processes telemetry data (port 4317)
- **Jaeger**: Distributed tracing UI (http://localhost:16686)
- **Prometheus**: Metrics storage (http://localhost:9090)
- **Grafana**: Dashboards (http://localhost:3000, admin/admin)

### 2. Configure uvmgr

By default, uvmgr automatically sends telemetry to `localhost:4317` if the OpenTelemetry SDK is installed. No additional configuration is required!

To use a different endpoint:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
```

### 3. View Telemetry

- **Traces**: Open Jaeger at http://localhost:16686
- **Metrics**: Open Prometheus at http://localhost:9090
- **Dashboards**: Open Grafana at http://localhost:3000

## Semantic Conventions

uvmgr follows OpenTelemetry semantic conventions for consistent telemetry data.

### CLI Attributes
- `cli.command`: Primary command (e.g., "deps", "build")
- `cli.subcommand`: Subcommand (e.g., "add", "remove")
- `cli.exit_code`: Command exit code
- `cli.options`: JSON-encoded command options

### Package Attributes
- `package.operation`: Operation type (add, remove, update, etc.)
- `package.name`: Package name
- `package.version`: Package version
- `package.dev_dependency`: Whether it's a dev dependency

### Example Trace

When you run `uvmgr deps add pytest --dev`, you'll see:
```
Span: cli.command.deps_add
├── Attributes:
│   ├── cli.command: deps_add
│   ├── package.operation: add
│   ├── package.names: pytest
│   └── package.dev_dependency: true
└── Child Spans:
    └── subprocess (uv add pytest --dev)
```

## Custom Instrumentation

### Adding Spans to Your Commands

```python
from uvmgr.core.instrumentation import instrument_command, add_span_attributes
from uvmgr.core.telemetry import span

@app.command()
@instrument_command("my_command")
def my_command(name: str):
    # Add custom attributes
    add_span_attributes(custom_attr="value")
    
    # Create child spans
    with span("my_operation", operation_type="custom"):
        # Your operation here
        pass
```

### Recording Metrics

```python
from uvmgr.core.telemetry import metric_counter, metric_histogram

# Count operations
counter = metric_counter("my_command.calls")
counter(1)

# Record durations
histogram = metric_histogram("operation.duration", unit="s")
histogram(elapsed_time)
```

### Handling Errors

```python
from uvmgr.core.telemetry import record_exception

try:
    risky_operation()
except Exception as e:
    record_exception(e, attributes={"operation": "risky"})
    raise
```

## Weaver Forge Integration

uvmgr uses OpenTelemetry Weaver to manage semantic conventions:

### Validate Conventions
```bash
python weaver-forge/validate_semconv.py
```

### Generate Code from Conventions
The semantic convention constants are auto-generated in `src/uvmgr/core/semconv.py`.

### Modify Conventions
Edit `weaver-forge/registry/uvmgr.yaml` and run validation to regenerate constants.

## Performance Considerations

- Telemetry has minimal overhead when OTEL SDK is not installed (no-op mode)
- Batch processing reduces network overhead
- Memory limiter prevents OOM in the collector
- File exporter provides persistence for analysis

## Troubleshooting

### No traces appearing?
1. Check OTEL collector is running: `docker-compose ps`
2. Verify endpoint: `curl http://localhost:13133/health`
3. Check uvmgr logs for connection errors

### Missing attributes?
1. Ensure you're using the latest instrumentation decorators
2. Check semantic convention definitions in `weaver-forge/registry/`

### High memory usage?
1. Adjust batch processor settings in `otel-collector-config.yaml`
2. Reduce sampling rate for high-volume operations

## Example Dashboards

### Grafana Dashboard JSON
Create a new dashboard in Grafana with these queries:

1. **Command Rate**: 
   ```promql
   rate(uvmgr_cli_command_calls_total[5m])
   ```

2. **Error Rate**:
   ```promql
   rate(uvmgr_cli_command_errors_total[5m])
   ```

3. **Command Duration (p95)**:
   ```promql
   histogram_quantile(0.95, rate(uvmgr_cli_command_duration_bucket[5m]))
   ```

4. **Package Operations**:
   ```promql
   sum by (operation) (rate(uvmgr_package_operations_total[5m]))
   ```

## Next Steps

1. Set up alerting rules in Prometheus
2. Create custom Grafana dashboards
3. Integrate with your existing observability platform
4. Add application-specific metrics

For more information, see the [OpenTelemetry documentation](https://opentelemetry.io/docs/).