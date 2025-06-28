#!/bin/bash
set -e

echo "🚀 Starting OTEL stack..."

# Wait for services to be ready
wait_for_service() {
    local service=$1
    local port=$2
    local timeout=60
    local count=0
    
    echo "⏳ Waiting for $service on port $port..."
    while ! nc -z localhost $port && [ $count -lt $timeout ]; do
        sleep 1
        count=$((count + 1))
    done
    
    if [ $count -eq $timeout ]; then
        echo "❌ Timeout waiting for $service"
        return 1
    else
        echo "✅ $service is ready"
        return 0
    fi
}

# Check if services are already running
if docker-compose -f .devcontainer/docker-compose.otel.yml ps | grep -q "Up"; then
    echo "🔄 OTEL stack already running"
else
    echo "🏗️  Starting OTEL services..."
    docker-compose -f .devcontainer/docker-compose.otel.yml up -d
fi

# Wait for key services
wait_for_service "OTEL Collector" 14317
wait_for_service "Jaeger" 26686
wait_for_service "Prometheus" 19090
wait_for_service "Grafana" 13000

echo ""
echo "✅ OTEL stack is running!"
echo ""
echo "🔗 Access points:"
echo "   📊 Jaeger UI: http://localhost:26686"
echo "   📈 Prometheus: http://localhost:19090"
echo "   📋 Grafana: http://localhost:13000 (admin/admin)"
echo "   🔧 OTEL Collector: http://localhost:18888/metrics"
echo ""
echo "🧪 Test OTEL integration:"
echo "   export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:14317"
echo "   uvmgr --help"
echo "   # Then check Jaeger UI for traces"