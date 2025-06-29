#!/bin/bash
set -e

echo "🐳 Starting uvmgr Terraform Cleanroom Validation"
echo "================================================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "   Please install Docker to run cleanroom tests"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "   Please install Docker Compose to run cleanroom tests"
    exit 1
fi

# Set Docker Compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "🔧 Environment Check:"
echo "   Docker: $(docker --version)"
echo "   Compose: $($DOCKER_COMPOSE --version)"
echo ""

# Build and run the cleanroom test
echo "🏗️  Building cleanroom test environment..."
$DOCKER_COMPOSE build --no-cache uvmgr-terraform-test

echo ""
echo "🚀 Running cleanroom validation tests..."
echo "----------------------------------------"

# Run the tests and capture the exit code
set +e
$DOCKER_COMPOSE run --rm uvmgr-terraform-test
TEST_EXIT_CODE=$?
set -e

# Copy results out of the container if they exist
echo ""
echo "📊 Collecting test results..."

# Create results directory
mkdir -p ./results

# Copy test results using docker cp
CONTAINER_ID=$($DOCKER_COMPOSE ps -q uvmgr-terraform-test 2>/dev/null | head -1)
if [ ! -z "$CONTAINER_ID" ]; then
    echo "Copying results from container..."
    docker cp $CONTAINER_ID:/test-workspace/benchmarks/results.json ./results/ 2>/dev/null || echo "No benchmark results found"
    docker cp $CONTAINER_ID:/test-workspace/results/ ./results/ 2>/dev/null || echo "No test results directory found"
fi

# Alternative: Use volume mounts to get results
if [ -d "./results" ]; then
    echo "✅ Test results available in ./results/"
    ls -la ./results/
else
    echo "⚠️  No test results directory found"
fi

# Clean up
echo ""
echo "🧹 Cleaning up..."
$DOCKER_COMPOSE down --volumes --remove-orphans

# Report final status
echo ""
echo "📋 Cleanroom Validation Summary"
echo "==============================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 ✅ All cleanroom tests PASSED!"
    echo ""
    echo "🚀 uvmgr Terraform integration is validated and production-ready!"
    echo ""
    echo "Key validations completed:"
    echo "  ✅ Clean environment installation"
    echo "  ✅ Module imports and registration"
    echo "  ✅ Operations layer functionality"
    echo "  ✅ Template generation (AWS VPC, EKS)"
    echo "  ✅ External project integration"
    echo "  ✅ OTEL instrumentation"
    echo "  ✅ Performance benchmarks"
    echo "  ✅ Error handling"
    echo ""
    echo "The Terraform integration can be safely deployed to production environments."
else
    echo "❌ Some cleanroom tests FAILED!"
    echo ""
    echo "Exit code: $TEST_EXIT_CODE"
    echo ""
    echo "Please review the test output above for specific failures."
    echo "Common issues:"
    echo "  - Missing dependencies in clean environment"
    echo "  - Import path problems"
    echo "  - Template generation issues"
    echo "  - Performance regressions"
fi

exit $TEST_EXIT_CODE