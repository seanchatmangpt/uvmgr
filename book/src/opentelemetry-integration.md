# OpenTelemetry Integration

uvmgr has built-in support for OpenTelemetry, enabling tracing and metrics for your workflows.

## Start OTEL Infrastructure

```bash
docker-compose -f docker-compose.otel.yml up -d
```

## Run Commands with Telemetry

```bash
uvmgr deps add requests
uvmgr tests run
```

- View traces in Jaeger: http://localhost:16686
- View metrics in Prometheus: http://localhost:9090 