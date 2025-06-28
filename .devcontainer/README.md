# uvmgr OTEL Devcontainer

Complete development environment with full OpenTelemetry observability stack for uvmgr.

## 🚀 Quick Start

### 1. Open in DevContainer
```bash
# VS Code
code . 
# Then: Ctrl+Shift+P -> "Dev Containers: Reopen in Container"

# Or with devcontainer CLI
devcontainer up --workspace-folder .
```

### 2. OTEL Stack Auto-Starts
The following services start automatically:
- **OTEL Collector** (localhost:4317) - Telemetry collection
- **Jaeger** (localhost:16686) - Trace visualization  
- **Prometheus** (localhost:9090) - Metrics storage
- **Grafana** (localhost:3000) - Dashboards (admin/admin)

### 3. Test OTEL Integration
```bash
# Run any uvmgr command with OTEL
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
uvmgr --help

# Check traces in Jaeger UI
open http://localhost:16686

# Run comprehensive validation
python .devcontainer/e2e-otel-validation.py
```

## 🏗️ Architecture

### Services Stack
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   uvmgr CLI     │───▶│ OTEL Collector  │───▶│     Jaeger      │
│   (Port N/A)    │    │   (Port 4317)   │    │  (Port 16686)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Prometheus    │───▶│    Grafana      │
                       │   (Port 9090)   │    │   (Port 3000)   │
                       └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **uvmgr commands** → Generate traces & metrics
2. **OTEL Collector** → Receives OTLP data on port 4317
3. **Jaeger** → Stores and visualizes traces
4. **Prometheus** → Scrapes and stores metrics  
5. **Grafana** → Creates dashboards from Prometheus data

## 📊 Validation & Testing

### E2E Validation Script
```bash
# Run comprehensive validation
python .devcontainer/e2e-otel-validation.py

# Expected output:
# 🚀 uvmgr E2E OTEL Validation in Devcontainer
# ✅ All 18 commands tested successfully
# ✅ Traces collected in Jaeger
# ✅ Metrics available in Prometheus
# 🎯 Overall Assessment: PRODUCTION READY
```

### Manual Testing
```bash
# Test individual commands
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# High-impact commands (80/20)
uvmgr deps --help       # Check traces in Jaeger
uvmgr lint --help       # Verify span hierarchy  
uvmgr tests --help      # Confirm metrics export
uvmgr build --help      # Validate semantic conventions

# All 18 instrumented commands work
uvmgr ai --help         # AI tools
uvmgr agent --help      # BPMN workflows
uvmgr weaver --help     # Semantic conventions
# ... etc
```

### Trace Verification
1. Open **Jaeger UI**: http://localhost:16686
2. Select service: `uvmgr-dev`
3. Search for recent traces
4. Verify span hierarchy:
   ```
   cli.command.deps_help          (ROOT)
   └── operation.help.display     (CHILD)
       └── subprocess.typer.help  (LEAF)
   ```

### Metrics Verification  
1. Open **Prometheus**: http://localhost:9090
2. Query metrics:
   ```promql
   # Command execution counts
   uvmgr_cli_command_calls_total
   
   # Operation durations
   uvmgr_cli_command_duration_seconds
   
   # Error rates
   uvmgr_cli_command_errors_total
   ```

### Dashboard Verification
1. Open **Grafana**: http://localhost:3000 (admin/admin)
2. View **uvmgr OTEL Dashboard**
3. Verify panels:
   - Command execution rate
   - Duration percentiles
   - Error rate trends

## 🔧 Configuration

### OTEL Environment Variables
```bash
# Automatically set in devcontainer
OTEL_SERVICE_NAME=uvmgr-dev
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_RESOURCE_ATTRIBUTES=service.name=uvmgr,service.version=dev,environment=devcontainer
```

### Custom Configuration
Edit `.devcontainer/otel-collector-config.yaml` to modify:
- Sampling rates
- Export destinations  
- Processing pipelines
- Resource attributes

### Performance Tuning
```yaml
# In otel-collector-config.yaml
processors:
  batch:
    send_batch_size: 1024
    timeout: 1s
  memory_limiter:
    limit_mib: 512
```

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check service status
docker-compose -f .devcontainer/docker-compose.otel.yml ps

# Restart services
docker-compose -f .devcontainer/docker-compose.otel.yml restart

# View logs
docker-compose -f .devcontainer/docker-compose.otel.yml logs otel-collector
```

### No Traces in Jaeger
```bash
# Check OTEL environment
echo $OTEL_EXPORTER_OTLP_ENDPOINT

# Test collector endpoint
curl http://localhost:8888/metrics

# Check uvmgr with debug logging
OTEL_LOG_LEVEL=DEBUG uvmgr --help
```

### No Metrics in Prometheus
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Verify collector metrics endpoint
curl http://localhost:8889/metrics | grep uvmgr
```

### Permission Issues
```bash
# Fix workspace permissions
sudo chown -R $USER:$USER /workspace

# Rebuild container
docker-compose -f .devcontainer/docker-compose.otel.yml down
docker-compose -f .devcontainer/docker-compose.otel.yml build --no-cache
```

## 📈 Performance Validation

### Expected Results
- **Command coverage**: 100% (18/18 commands)
- **OTEL overhead**: <5% average
- **Trace collection**: >90% success rate
- **Metrics export**: 100% success rate

### Performance Benchmarks
```bash
# Baseline (no OTEL)
time uvmgr --help

# With OTEL  
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 time uvmgr --help

# Acceptable overhead: <10ms or <5% whichever is larger
```

## 🔗 Useful Links

- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000 (admin/admin)
- **OTEL Collector Metrics**: http://localhost:8888/metrics
- **OTEL Collector Config**: `.devcontainer/otel-collector-config.yaml`

## 🎯 Production Deployment

This devcontainer setup mirrors production OTEL deployment:

```bash
# Production environment variables
export OTEL_SERVICE_NAME="uvmgr"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-otel-collector:4317"
export OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer YOUR_TOKEN"
export OTEL_RESOURCE_ATTRIBUTES="service.name=uvmgr,service.version=1.0.0,environment=production"

# Sampling for production (1% sampling)
export OTEL_TRACES_SAMPLER="traceidratio" 
export OTEL_TRACES_SAMPLER_ARG="0.01"
```

The devcontainer provides a complete testing environment that validates the production OTEL setup with 100% command coverage and enterprise-grade observability.