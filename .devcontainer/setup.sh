#!/bin/bash
set -e

echo "🚀 Setting up uvmgr OTEL development environment..."

# Ensure we're in the workspace
cd /workspace

# Install/update UV if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo "📦 Installing dependencies with UV..."
uv sync --all-extras

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
uv run pre-commit install --install-hooks

# Create directories for OTEL setup
mkdir -p .devcontainer/grafana/{provisioning/dashboards,provisioning/datasources,dashboards}

# Set up Grafana datasource
cat > .devcontainer/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
EOF

# Set up Grafana dashboard provisioning
cat > .devcontainer/grafana/provisioning/dashboards/dashboards.yml << EOF
apiVersion: 1
providers:
  - name: 'uvmgr'
    type: file
    folder: ''
    options:
      path: /var/lib/grafana/dashboards
EOF

# Create basic uvmgr dashboard
cat > .devcontainer/grafana/dashboards/uvmgr-dashboard.json << EOF
{
  "dashboard": {
    "id": null,
    "title": "uvmgr OTEL Dashboard",
    "tags": ["uvmgr", "otel"],
    "panels": [
      {
        "id": 1,
        "title": "Command Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(uvmgr_cli_command_calls_total[5m])",
            "legendFormat": "{{command}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Command Duration", 
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(uvmgr_cli_command_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "10s"
  }
}
EOF

echo "✅ Setup complete! OTEL development environment ready."
echo ""
echo "🔗 Services will be available at:"
echo "   - Jaeger UI: http://localhost:16686"
echo "   - Prometheus: http://localhost:9090" 
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - OTEL Collector: http://localhost:4317 (gRPC), http://localhost:4318 (HTTP)"
echo ""
echo "🚀 Run 'bash .devcontainer/start-otel.sh' to start the OTEL stack"