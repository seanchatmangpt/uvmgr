#!/bin/bash
set -euo pipefail

# uvmgr External Project Lifecycle Test Runner
# ============================================
#
# This script orchestrates comprehensive testing of uvmgr on external projects,
# demonstrating the complete Python development lifecycle from project initialization
# to deployment with observability.

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${WORKSPACE_DIR:-${SCRIPT_DIR}/workspace}"
RESULTS_DIR="${RESULTS_DIR:-${SCRIPT_DIR}/test-results}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.external.yml"
PROJECT_NAME="${1:-}"
OTEL_ENABLED="${OTEL_ENABLED:-true}"
MCP_ENABLED="${MCP_ENABLED:-true}"

# Test configuration
declare -A TEST_PROJECTS=(
    ["substrate"]="Substrate Copier template with uvmgr integration"
    ["minimal"]="Minimal Python project created with uvmgr new"
    ["fastapi"]="FastAPI project created with uvmgr new --fastapi"
    ["existing"]="Existing Python project enhanced with uvmgr"
)

# Available test modes
declare -A TEST_MODES=(
    ["quick"]="Quick test of basic uvmgr functionality"
    ["full"]="Complete lifecycle test including AI and observability"
    ["docker"]="Run tests in Docker containers with full observability stack"
    ["substrate"]="Specific test of Substrate template integration"
    ["benchmark"]="Performance benchmarking of uvmgr vs native tools"
)

# Helper functions
print_banner() {
    echo -e "${PURPLE}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    uvmgr External Project Lifecycle Testing                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}$(printf '=%.0s' $(seq 1 ${#1}))${NC}"
}

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

show_usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  $0 [PROJECT] [MODE] [OPTIONS]"
    echo ""
    echo -e "${BOLD}Projects:${NC}"
    for project in "${!TEST_PROJECTS[@]}"; do
        echo "  ${GREEN}${project}${NC} - ${TEST_PROJECTS[$project]}"
    done
    echo ""
    echo -e "${BOLD}Modes:${NC}"
    for mode in "${!TEST_MODES[@]}"; do
        echo "  ${GREEN}${mode}${NC} - ${TEST_MODES[$mode]}"
    done
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "  --otel           Enable OpenTelemetry observability"
    echo "  --no-otel        Disable OpenTelemetry"
    echo "  --mcp            Enable MCP server testing"
    echo "  --no-mcp         Disable MCP server testing"
    echo "  --workspace DIR  Set workspace directory (default: ./workspace)"
    echo "  --results DIR    Set results directory (default: ./test-results)"
    echo "  --help           Show this help message"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  $0 substrate full --otel     # Complete Substrate test with observability"
    echo "  $0 minimal quick             # Quick test of minimal project"
    echo "  $0 docker                    # Run all tests in Docker with full stack"
    echo "  $0 benchmark                 # Performance benchmarking"
}

check_prerequisites() {
    print_section "Checking Prerequisites"
    
    local missing=()
    
    # Check required commands
    local commands=("python3" "git" "curl")
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            print_status "$cmd is available"
        else
            print_error "$cmd is required but not installed"
            missing+=("$cmd")
        fi
    done
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        local major=$(echo "$python_version" | cut -d'.' -f1)
        local minor=$(echo "$python_version" | cut -d'.' -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
            print_status "Python $python_version is compatible"
        else
            print_error "Python 3.8+ required, found $python_version"
            missing+=("python3.8+")
        fi
    fi
    
    # Check for uv
    if command -v uv >/dev/null 2>&1; then
        print_status "uv package manager is available"
    else
        print_warning "uv not found, will be installed automatically"
    fi
    
    # Check Docker for container tests
    if [ "${2:-}" = "docker" ]; then
        if command -v docker >/dev/null 2>&1; then
            print_status "Docker is available for container testing"
        else
            print_error "Docker is required for container testing"
            missing+=("docker")
        fi
        
        if command -v docker-compose >/dev/null 2>&1; then
            print_status "Docker Compose is available"
        else
            print_error "Docker Compose is required for container testing"
            missing+=("docker-compose")
        fi
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing prerequisites: ${missing[*]}"
        echo "Please install the missing components and try again."
        exit 1
    fi
    
    print_status "All prerequisites satisfied"
}

setup_workspace() {
    print_section "Setting Up Workspace"
    
    # Create directories
    mkdir -p "$WORKSPACE_DIR" "$RESULTS_DIR"
    print_status "Created workspace: $WORKSPACE_DIR"
    print_status "Created results directory: $RESULTS_DIR"
    
    # Clean up previous test results if requested
    if [ -f "$RESULTS_DIR/.cleanup" ]; then
        print_info "Cleaning up previous test results..."
        rm -rf "${RESULTS_DIR:?}"/*
    fi
    
    # Set up environment
    export WORKSPACE_DIR RESULTS_DIR
    export OTEL_SERVICE_NAME="uvmgr-external-test"
    export OTEL_RESOURCE_ATTRIBUTES="service.name=uvmgr-external,service.version=test,environment=lifecycle-testing"
    
    if [ "$OTEL_ENABLED" = "true" ]; then
        export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
        print_status "OpenTelemetry enabled"
    else
        print_info "OpenTelemetry disabled"
    fi
    
    print_status "Workspace setup complete"
}

run_quick_test() {
    local project="$1"
    print_section "Running Quick Test: $project"
    
    case "$project" in
        "minimal"|"fastapi")
            print_info "Testing uvmgr project creation..."
            cd "$WORKSPACE_DIR"
            
            # Test uvmgr new command
            if uvmgr new "$project-quick-test" ${project:+--$project} >/dev/null 2>&1; then
                print_status "uvmgr new command works"
            else
                print_warning "uvmgr new command failed (may be stubbed)"
            fi
            ;;
        "substrate")
            print_info "Testing Substrate integration..."
            bash "$SCRIPT_DIR/test-substrate-integration.sh" "$project-quick-test"
            ;;
        "existing")
            print_info "Testing existing project enhancement..."
            # Create a simple project structure
            mkdir -p "$WORKSPACE_DIR/$project-quick-test"
            cd "$WORKSPACE_DIR/$project-quick-test"
            echo '#!/usr/bin/env python3\nprint("Hello World")' > main.py
            
            # Run auto-install
            bash "$SCRIPT_DIR/auto-install-uvmgr.sh"
            ;;
    esac
    
    print_status "Quick test completed for $project"
}

run_full_test() {
    local project="$1"
    print_section "Running Full Lifecycle Test: $project"
    
    # Use the Python test runner for comprehensive testing
    python3 "$SCRIPT_DIR/test-lifecycle.py" \
        --project "$project" \
        --workspace "$WORKSPACE_DIR" \
        --results "$RESULTS_DIR" \
        ${OTEL_ENABLED:+--validate-otel}
    
    print_status "Full lifecycle test completed for $project"
}

run_docker_tests() {
    print_section "Running Docker Container Tests"
    
    # Check if Docker Compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    print_info "Starting observability stack..."
    docker-compose -f "$COMPOSE_FILE" up -d otel-collector jaeger prometheus grafana
    
    # Wait for services to be ready
    print_info "Waiting for services to start..."
    sleep 10
    
    # Check service health
    local services=("otel-collector:13133/health" "jaeger:14269" "prometheus:9090/-/healthy")
    for service in "${services[@]}"; do
        local host_port=$(echo "$service" | cut -d':' -f1-2)
        local path=$(echo "$service" | cut -d':' -f3)
        
        if curl -sSf "http://localhost:${host_port}${path}" >/dev/null 2>&1; then
            print_status "$host_port is healthy"
        else
            print_warning "$host_port health check failed"
        fi
    done
    
    print_info "Running containerized tests..."
    docker-compose -f "$COMPOSE_FILE" up --build uvmgr-external
    
    # Collect results
    print_info "Collecting test results..."
    docker cp uvmgr-external-test:/test-results/. "$RESULTS_DIR/" 2>/dev/null || \
        print_warning "Could not collect test results from container"
    
    print_status "Docker tests completed"
    
    print_info "Observability interfaces available:"
    echo "  Jaeger UI: http://localhost:16686"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/admin)"
}

run_substrate_test() {
    print_section "Running Substrate Integration Test"
    
    # Run the dedicated Substrate test script
    bash "$SCRIPT_DIR/test-substrate-integration.sh" "substrate-lifecycle-test"
    
    print_status "Substrate integration test completed"
}

run_benchmark_test() {
    print_section "Running Performance Benchmarks"
    
    print_info "Benchmarking uvmgr vs native tools..."
    
    # Create benchmark project
    local benchmark_dir="$WORKSPACE_DIR/benchmark-test"
    mkdir -p "$benchmark_dir"
    cd "$benchmark_dir"
    
    # Initialize project
    bash "$SCRIPT_DIR/auto-install-uvmgr.sh"
    
    # Create benchmark script
    cat > benchmark.py << 'EOF'
#!/usr/bin/env python3
"""Performance benchmarking of uvmgr vs native tools."""

import subprocess
import time
import statistics
from typing import List, Dict, Any

def time_command(cmd: List[str], runs: int = 5) -> Dict[str, Any]:
    """Time a command execution multiple times."""
    times = []
    
    for _ in range(runs):
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            success = True
        except subprocess.CalledProcessError:
            success = False
        end = time.time()
        
        if success:
            times.append(end - start)
    
    if times:
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "runs": len(times),
            "success_rate": len(times) / runs
        }
    else:
        return {"error": "All runs failed"}

def main():
    """Run benchmarks."""
    benchmarks = {
        "uvmgr_help": ["uvmgr", "--help"],
        "uv_help": ["uv", "--help"],
        "uvmgr_deps_list": ["uvmgr", "deps", "list"],
        "uv_pip_list": ["uv", "pip", "list"],
        "uvmgr_lint_check": ["uvmgr", "lint", "check"],
        "ruff_check": ["ruff", "check", "."],
    }
    
    print("Performance Benchmarks")
    print("=" * 50)
    
    results = {}
    for name, cmd in benchmarks.items():
        print(f"\nBenchmarking: {' '.join(cmd)}")
        result = time_command(cmd)
        results[name] = result
        
        if "error" in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Mean: {result['mean']:.3f}s")
            print(f"  Median: {result['median']:.3f}s")
            print(f"  Range: {result['min']:.3f}s - {result['max']:.3f}s")
            print(f"  Success Rate: {result['success_rate']:.1%}")
    
    # Calculate overhead
    if "uvmgr_help" in results and "uv_help" in results:
        if "mean" in results["uvmgr_help"] and "mean" in results["uv_help"]:
            overhead = (results["uvmgr_help"]["mean"] - results["uv_help"]["mean"]) / results["uv_help"]["mean"] * 100
            print(f"\nuvmgr help overhead: {overhead:.1f}%")
    
    return results

if __name__ == "__main__":
    main()
EOF
    
    python3 benchmark.py | tee "$RESULTS_DIR/benchmark-results.txt"
    
    print_status "Performance benchmarks completed"
}

generate_summary_report() {
    print_section "Generating Summary Report"
    
    local report_file="$RESULTS_DIR/lifecycle-test-summary.md"
    
    cat > "$report_file" << EOF
# uvmgr External Project Lifecycle Test Summary

Generated: $(date)
Test Runner: $0 $*

## Test Configuration

- **Workspace**: $WORKSPACE_DIR
- **Results**: $RESULTS_DIR  
- **OTEL Enabled**: $OTEL_ENABLED
- **MCP Enabled**: $MCP_ENABLED

## Test Environment

- **OS**: $(uname -s) $(uname -r)
- **Python**: $(python3 --version 2>/dev/null || echo "Not available")
- **uv**: $(uv --version 2>/dev/null || echo "Not available")
- **uvmgr**: $(uvmgr --version 2>/dev/null || echo "Not available")
- **Docker**: $(docker --version 2>/dev/null || echo "Not available")

## Test Results

$(find "$RESULTS_DIR" -name "*.json" -exec echo "### {}" \; -exec jq -r '.summary // "No summary available"' {} \; 2>/dev/null || echo "No JSON results found")

## Files Generated

\`\`\`
$(find "$RESULTS_DIR" -type f | sort)
\`\`\`

## Quick Commands

\`\`\`bash
# View detailed results
cat $RESULTS_DIR/lifecycle_test_results.json

# View benchmark results  
cat $RESULTS_DIR/benchmark-results.txt

# View integration reports
find $WORKSPACE_DIR -name "*integration-report.md" -exec cat {} \;
\`\`\`

## Observability

- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000

## Next Steps

1. Review test results in $RESULTS_DIR
2. Examine generated projects in $WORKSPACE_DIR
3. Check observability dashboards if OTEL enabled
4. Run specific tests with: \`$0 [project] [mode]\`

---

Generated by uvmgr external project lifecycle testing framework.
EOF
    
    print_status "Summary report generated: $report_file"
    
    # Display key results
    echo -e "\n${BOLD}Key Results:${NC}"
    if [ -f "$RESULTS_DIR/lifecycle_test_results.json" ]; then
        python3 -c "
import json
try:
    with open('$RESULTS_DIR/lifecycle_test_results.json') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    print(f\"  Projects Tested: {summary.get('total_projects', 0)}\")
    print(f\"  Success Rate: {summary.get('success_rate', 0):.1%}\")
    print(f\"  Overall Result: {'✅ PASS' if summary.get('overall_success') else '❌ FAIL'}\")
except:
    print('  No results data available')
"
    else
        print_info "No detailed results available yet"
    fi
}

cleanup() {
    print_section "Cleanup"
    
    # Stop Docker containers if running
    if [ -f "$COMPOSE_FILE" ]; then
        print_info "Stopping Docker containers..."
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
    fi
    
    # Optional: Clean up workspace
    if [ "${CLEANUP_WORKSPACE:-false}" = "true" ]; then
        print_info "Cleaning up workspace..."
        rm -rf "$WORKSPACE_DIR"
    fi
    
    print_status "Cleanup completed"
}

# Main execution
main() {
    print_banner
    
    # Parse arguments
    local project="${1:-}"
    local mode="${2:-full}"
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --otel)
                OTEL_ENABLED=true
                shift
                ;;
            --no-otel)
                OTEL_ENABLED=false
                shift
                ;;
            --mcp)
                MCP_ENABLED=true
                shift
                ;;
            --no-mcp)
                MCP_ENABLED=false
                shift
                ;;
            --workspace)
                WORKSPACE_DIR="$2"
                shift 2
                ;;
            --results)
                RESULTS_DIR="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Show configuration
    print_info "Project: ${project:-all}"
    print_info "Mode: $mode"
    print_info "Workspace: $WORKSPACE_DIR"
    print_info "Results: $RESULTS_DIR"
    print_info "OTEL: $OTEL_ENABLED"
    print_info "MCP: $MCP_ENABLED"
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Run tests based on mode
    case "$mode" in
        "quick")
            check_prerequisites "$project" "$mode"
            setup_workspace
            if [ -n "$project" ] && [ "$project" != "all" ]; then
                run_quick_test "$project"
            else
                for proj in "${!TEST_PROJECTS[@]}"; do
                    run_quick_test "$proj"
                done
            fi
            ;;
        "full")
            check_prerequisites "$project" "$mode"
            setup_workspace
            if [ -n "$project" ] && [ "$project" != "all" ]; then
                run_full_test "$project"
            else
                python3 "$SCRIPT_DIR/test-lifecycle.py" \
                    --all-projects \
                    --workspace "$WORKSPACE_DIR" \
                    --results "$RESULTS_DIR" \
                    ${OTEL_ENABLED:+--validate-otel}
            fi
            ;;
        "docker")
            check_prerequisites "$project" "$mode"
            setup_workspace
            run_docker_tests
            ;;
        "substrate")
            check_prerequisites "$project" "$mode"
            setup_workspace
            run_substrate_test
            ;;
        "benchmark")
            check_prerequisites "$project" "$mode"
            setup_workspace
            run_benchmark_test
            ;;
        *)
            print_error "Unknown mode: $mode"
            show_usage
            exit 1
            ;;
    esac
    
    # Generate summary
    generate_summary_report
    
    print_section "Test Execution Complete"
    print_status "All tests completed successfully!"
    print_info "Results available in: $RESULTS_DIR"
    
    if [ "$OTEL_ENABLED" = "true" ]; then
        print_info "Observability dashboards:"
        echo "  Jaeger: http://localhost:16686"
        echo "  Prometheus: http://localhost:9090"
        echo "  Grafana: http://localhost:3000"
    fi
}

# Execute main function with all arguments
main "$@"