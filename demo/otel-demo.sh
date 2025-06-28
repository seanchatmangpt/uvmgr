#!/bin/bash
# OpenTelemetry Demo Script for uvmgr
# This script demonstrates the complete OTEL integration

set -e

echo "=== OpenTelemetry Demo for uvmgr ==="
echo

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Start OTEL infrastructure
echo "1. Starting OTEL infrastructure..."
echo "   - OTEL Collector (port 4317)"
echo "   - Jaeger UI (http://localhost:16686)"
echo "   - Prometheus (http://localhost:9090)"
echo "   - Grafana (http://localhost:3000)"
echo

docker-compose -f docker-compose.otel.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Validate OTEL configuration
echo
echo "2. Validating OTEL configuration..."
uvmgr otel validate

# Check semantic conventions
echo
echo "3. Checking semantic conventions..."
uvmgr otel semconv --validate

# Show instrumentation status
echo
echo "4. Instrumentation status..."
uvmgr otel status

# Generate test telemetry
echo
echo "5. Generating test telemetry data..."
uvmgr otel test --iterations 10

# Run some real commands to generate telemetry
echo
echo "6. Running instrumented commands..."

# Create a test project
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

echo "   Creating test project in $TEST_DIR"
uvmgr project init test-otel-demo

echo "   Adding dependencies..."
uvmgr deps add pytest rich typer --dev
uvmgr deps add fastapi httpx

echo "   Listing dependencies..."
uvmgr deps list

echo "   Running tests..."
uvmgr tests run || true

echo "   Building wheel..."
uvmgr build wheel || true

# Return to original directory
cd - > /dev/null

# Display results
echo
echo "=== Demo Complete! ==="
echo
echo "View your telemetry data at:"
echo "  - Traces: http://localhost:16686 (Jaeger)"
echo "  - Metrics: http://localhost:9090 (Prometheus)"
echo "  - Dashboards: http://localhost:3000 (Grafana, admin/admin)"
echo
echo "Example Jaeger queries:"
echo "  - Service: uvmgr"
echo "  - Operation: cli.command.deps_add"
echo "  - Tags: package.operation=add"
echo
echo "Example Prometheus queries:"
echo "  - rate(uvmgr_cli_command_calls_total[5m])"
echo "  - histogram_quantile(0.95, rate(uvmgr_cli_command_duration_bucket[5m]))"
echo
echo "To stop the OTEL infrastructure:"
echo "  docker-compose -f docker-compose.otel.yml down"
echo
echo "To export telemetry configuration:"
echo "  uvmgr otel export --format json"

# Cleanup
rm -rf "$TEST_DIR"