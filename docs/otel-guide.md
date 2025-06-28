# OpenTelemetry Comprehensive Guide

`uvmgr` provides comprehensive OpenTelemetry (OTEL) integration for observability, tracing, metrics, and semantic conventions. This guide covers all OTEL features and capabilities.

## Overview

The OpenTelemetry integration in `uvmgr` provides:

- **Automatic Instrumentation**: Built-in tracing for all CLI commands
- **Semantic Conventions**: Standardized attributes and metrics
- **Validation Tools**: Comprehensive OTEL validation and testing
- **Coverage Analysis**: Telemetry coverage across the codebase
- **Weaver Integration**: Semantic convention management
- **Multiple Exporters**: Support for various telemetry backends

## Quick Start

### 1. Start OTEL Infrastructure

```bash
# Start all OTEL services
docker-compose -f docker-compose.otel.yml up -d

# Verify services are running
docker-compose -f docker-compose.otel.yml ps
```

This starts:
- **OTEL Collector**: Receives and processes telemetry (port 4317)
- **Jaeger**: Distributed tracing UI (http://localhost:16686)
- **Prometheus**: Metrics storage (http://localhost:9090)
- **Grafana**: Dashboards (http://localhost:3000, admin/admin)

### 2. Run Commands with Telemetry

```bash
# All commands automatically send telemetry
uvmgr deps add requests
uvmgr tests run
uvmgr build dist

# View traces in Jaeger: http://localhost:16686
# View metrics in Prometheus: http://localhost:9090
# View dashboards in Grafana: http://localhost:3000
```

### 3. Validate OTEL Setup

```bash
# Run comprehensive validation
uvmgr otel validate --comprehensive

# Test telemetry functionality
uvmgr otel test --iterations 10

# Check OTEL status
uvmgr otel status
```

## Telemetry Coverage Analysis

### Analyze Coverage

```bash
# Analyze telemetry coverage across the codebase
uvmgr otel coverage

# Check coverage with custom threshold
uvmgr otel coverage --threshold 90

# Analyze specific layer
uvmgr otel coverage --layer Command

# Show detailed function analysis
uvmgr otel coverage --detailed
```

### Coverage Reports

The coverage analysis provides:

- **Overall Coverage**: Percentage of instrumented functions
- **Layer Breakdown**: Coverage by architecture layer (Command, Operations, Runtime, Core)
- **Function Details**: Individual function instrumentation status
- **Recommendations**: Suggestions for improving coverage

### Example Output

```
OpenTelemetry Coverage Analysis
===============================

Overall Coverage: 85.2% (234/275 functions)

Layer Breakdown:
├── Command: 92.1% (58/63 functions)
├── Operations: 78.3% (47/60 functions)
├── Runtime: 88.9% (32/36 functions)
├── Core: 82.1% (23/28 functions)
└── MCP: 75.0% (12/16 functions)

Files Needing Attention:
├── src/uvmgr/ops/legacy.py (0% coverage)
├── src/uvmgr/runtime/experimental.py (25% coverage)
└── src/uvmgr/commands/helper.py (60% coverage)
```

## Validation and Testing

### Comprehensive Validation

```bash
# Run full validation suite
uvmgr otel validate --comprehensive

# Export validation results
uvmgr otel validate --export --output validation.json

# Validate with custom endpoint
uvmgr otel validate --endpoint http://custom-collector:4317
```

### Telemetry Testing

```bash
# Test basic telemetry functionality
uvmgr otel test

# Test with custom iterations
uvmgr otel test --iterations 20

# Test specific components
uvmgr otel test --component tracing
uvmgr otel test --component metrics
```

### Validation Components

The validation suite tests:

1. **Span Creation**: Verify spans are created correctly
2. **Metrics Collection**: Test metric recording
3. **Semantic Conventions**: Validate attribute usage
4. **Error Handling**: Test exception recording
5. **Performance Tracking**: Verify timing measurements
6. **Workflow Integration**: Test end-to-end scenarios
7. **Exporters**: Validate telemetry export

## Semantic Conventions

### Validate Conventions

```bash
# Validate semantic conventions
uvmgr otel semconv --validate

# Generate code from conventions
uvmgr otel semconv --generate

# Check convention coverage
uvmgr otel semconv --coverage
```

### Weaver Integration

```bash
# Install Weaver tool
uvmgr weaver install

# Validate registry
uvmgr weaver check

# Generate Python constants
uvmgr weaver generate python

# Search conventions
uvmgr weaver search "package" --type attribute
```

### Available Conventions

#### CLI Attributes
- `cli.command`: Primary command (e.g., "deps", "build")
- `cli.subcommand`: Subcommand (e.g., "add", "remove")
- `cli.exit_code`: Command exit code
- `cli.options`: JSON-encoded command options

#### Package Attributes
- `package.operation`: Operation type (add, remove, update, etc.)
- `package.name`: Package name
- `package.version`: Package version
- `package.dev_dependency`: Whether it's a dev dependency

#### Server Attributes
- `server.operation`: Server operation (start, stop, etc.)
- `server.protocol`: Protocol used (mcp, http, etc.)
- `server.host`: Server host address
- `server.port`: Server port number

## Status and Monitoring

### Check OTEL Status

```bash
# Check overall OTEL status
uvmgr otel status

# Check specific components
uvmgr otel status --component collector
uvmgr otel status --component jaeger
uvmgr otel status --component prometheus
```

### Demo Features

```bash
# Run OTEL demo
uvmgr otel demo

# Demo specific features
uvmgr otel demo --feature tracing
uvmgr otel demo --feature metrics
uvmgr otel demo --feature logging
```

### Export Telemetry Data

```bash
# Export to JSON
uvmgr otel export --format json --output telemetry.json

# Export to YAML
uvmgr otel export --format yaml --output telemetry.yaml

# Export specific time range
uvmgr otel export --start 2024-01-01 --end 2024-01-31
```

## Configuration

### Environment Variables

```bash
# OTEL Collector endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Service name
export OTEL_SERVICE_NAME=uvmgr

# Service version
export OTEL_SERVICE_VERSION=1.0.0

# Sampling rate (0.0 to 1.0)
export OTEL_TRACES_SAMPLER_ARG=1.0

# Log level
export OTEL_LOG_LEVEL=INFO
```

### Collector Configuration

The OTEL collector configuration (`otel-collector-config.yaml`) includes:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 1s
    limit_mib: 1500

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:9464
  logging:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, memory_limiter]
      exporters: [jaeger, logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
```

### Docker Compose

The `docker-compose.otel.yml` file sets up the complete observability stack:

```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "9464:9464"   # Prometheus metrics
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    command: ["--config", "/etc/otel-collector-config.yaml"]

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "14250:14250"  # gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

## Best Practices

### Instrumentation Guidelines

1. **Use Decorators**: Apply `@instrument_command` to CLI functions
2. **Add Attributes**: Use semantic conventions for consistent attributes
3. **Handle Errors**: Record exceptions with `record_exception`
4. **Measure Performance**: Use `span` context managers for timing
5. **Batch Operations**: Group related operations in single spans

### Example Instrumentation

```python
from uvmgr.core.instrumentation import instrument_command, add_span_attributes
from uvmgr.core.telemetry import span, record_exception

@app.command()
@instrument_command("my_command")
def my_command(name: str, verbose: bool = False):
    # Add custom attributes
    add_span_attributes(
        custom_name=name,
        verbose_mode=verbose
    )
    
    try:
        # Create child span for operation
        with span("my_operation", operation_type="custom"):
            result = perform_operation(name)
            return result
    except Exception as e:
        # Record exception with context
        record_exception(e, attributes={"operation": "my_operation"})
        raise
```

### Performance Considerations

1. **Sampling**: Use appropriate sampling rates for production
2. **Batch Processing**: Configure batch processors for efficiency
3. **Memory Limits**: Set memory limits to prevent OOM
4. **Export Timeouts**: Configure appropriate export timeouts
5. **Resource Limits**: Monitor collector resource usage

## Troubleshooting

### Common Issues

#### No Traces Appearing
```bash
# Check collector is running
curl http://localhost:13133/health

# Check endpoint configuration
echo $OTEL_EXPORTER_OTLP_ENDPOINT

# Test connection
uvmgr otel test --iterations 1
```

#### High Memory Usage
```bash
# Check collector memory usage
docker stats otel-collector

# Adjust batch processor settings
# Reduce send_batch_size in otel-collector-config.yaml

# Increase memory limits
# Adjust limit_mib in memory_limiter processor
```

#### Missing Attributes
```bash
# Check semantic convention definitions
uvmgr weaver check

# Validate attribute usage
uvmgr otel semconv --validate

# Check instrumentation decorators
uvmgr otel coverage --detailed
```

### Debug Mode

```bash
# Enable debug logging
export OTEL_LOG_LEVEL=DEBUG

# Run with verbose output
uvmgr otel validate --comprehensive -v

# Check collector logs
docker-compose -f docker-compose.otel.yml logs otel-collector
```

### Health Checks

```bash
# Check all services
uvmgr otel status

# Test individual components
curl http://localhost:16686/api/services  # Jaeger
curl http://localhost:9090/api/v1/status  # Prometheus
curl http://localhost:3000/api/health     # Grafana
```

## Advanced Features

### Custom Exporters

```python
# Custom exporter configuration
from opentelemetry.exporter.otlp.proto.grpc import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

exporter = OTLPSpanExporter(
    endpoint="http://custom-collector:4317",
    headers={"Authorization": "Bearer token"}
)

processor = BatchSpanProcessor(exporter)
```

### Custom Metrics

```python
from uvmgr.core.telemetry import metric_counter, metric_histogram

# Custom counters
custom_counter = metric_counter("my.custom.counter")
custom_counter(1, {"label": "value"})

# Custom histograms
custom_histogram = metric_histogram("my.custom.duration", unit="s")
custom_histogram(1.5, {"operation": "custom"})
```

### Custom Semantic Conventions

```yaml
# weaver-forge/registry/custom.yaml
groups:
  - id: custom
    type: attribute_group
    attributes:
      - id: custom.operation
        type: string
        description: Custom operation type
      - id: custom.result
        type: string
        description: Custom operation result
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI with OTEL

on: [push, pull_request]

jobs:
  test-with-telemetry:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start OTEL infrastructure
        run: docker-compose -f docker-compose.otel.yml up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run tests with telemetry
        run: uvmgr tests run
      
      - name: Validate telemetry
        run: uvmgr otel validate --comprehensive
      
      - name: Check coverage
        run: uvmgr otel coverage --threshold 80
```

### Production Deployment

```bash
# Production OTEL setup
export OTEL_EXPORTER_OTLP_ENDPOINT=https://prod-collector:4317
export OTEL_SERVICE_NAME=uvmgr-prod
export OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling

# Run with production settings
uvmgr deps add requests
uvmgr tests run
```

### Monitoring Dashboards

Create Grafana dashboards for:

1. **Command Performance**: Response times by command
2. **Error Rates**: Error frequency by command
3. **Resource Usage**: Memory and CPU usage
4. **Dependency Operations**: Package management metrics
5. **Test Results**: Test execution metrics

## Support and Resources

### Documentation
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Weaver Documentation](https://opentelemetry.io/docs/weaver/)
- [Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)

### Community
- [OpenTelemetry Slack](https://cloud-native.slack.com/archives/C01N7PP1THC)
- [GitHub Discussions](https://github.com/open-telemetry/opentelemetry-python/discussions)

### Tools
- [Jaeger UI](http://localhost:16686)
- [Prometheus UI](http://localhost:9090)
- [Grafana Dashboards](http://localhost:3000)

This comprehensive OpenTelemetry guide should help you implement and maintain observability in your Python projects using `uvmgr`. 