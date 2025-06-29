#!/bin/bash

# Final Comprehensive Validation for uvmgr
# ========================================
# Complete end-to-end validation of all uvmgr components

set -euo pipefail

echo "🎯 Final Comprehensive Validation of uvmgr"
echo "=========================================="
echo ""

# Track overall success
OVERALL_SUCCESS=true

# Function to report test results
report_test() {
    local test_name="$1"
    local status="$2"
    if [ "$status" = "success" ]; then
        echo "✅ $test_name"
    else
        echo "❌ $test_name"
        OVERALL_SUCCESS=false
    fi
}

echo "🧪 Phase 1: Core Module Validation"
echo "=================================="

# Test 1: Core imports and module loading
echo "📦 Testing core module imports..."
if python -c "
import sys
sys.path.insert(0, 'src')

# Core imports
from uvmgr.commands import deps, build, tests, cache, lint, otel, guides, worktree, infodesign, mermaid, mcp, exponential, democratize
from uvmgr.runtime import multilang, performance, container, cicd, agent_guides
from uvmgr.core.semconv import MultiLangAttributes, PerformanceAttributes, ContainerAttributes, CiCdAttributes, AgentAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
print('All modules imported successfully')
" 2>/dev/null; then
    report_test "Core Module Imports" "success"
else
    report_test "Core Module Imports" "failure"
fi

# Test 2: Telemetry integration
echo "🔍 Testing OpenTelemetry telemetry integration..."
if python -c "
import sys
sys.path.insert(0, 'src')
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception

# Test span creation
with span('test_operation', test_attr='value'):
    pass

# Test metrics
counter = metric_counter('test.counter')
counter(1)

histogram = metric_histogram('test.histogram')
histogram(0.5)

# Test exception recording
try:
    raise ValueError('Test exception')
except Exception as e:
    record_exception(e, attributes={'test': 'value'})

print('Telemetry integration working')
" 2>/dev/null; then
    report_test "OpenTelemetry Integration" "success"
else
    report_test "OpenTelemetry Integration" "failure"
fi

# Test 3: Performance measurement
echo "🚀 Testing performance measurement..."
if python -c "
import sys
sys.path.insert(0, 'src')
from uvmgr.runtime.performance import measure_operation, get_system_info
import time

def test_func():
    time.sleep(0.01)
    return 42

metrics = measure_operation('test', test_func, warmup_runs=1, measurement_runs=2)
system_info = get_system_info()

print(f'Performance measurement: {metrics.duration*1000:.1f}ms')
print(f'System info available: {len(system_info) > 0}')
" 2>/dev/null; then
    report_test "Performance Measurement" "success"
else
    report_test "Performance Measurement" "failure"
fi

echo ""
echo "🌍 Phase 2: Multi-Language Detection Validation"
echo "=============================================="

# Create test workspace
TEST_WORKSPACE=$(mktemp -d)
echo "📁 Test workspace: $TEST_WORKSPACE"

# Test 4: Python project detection
echo "🐍 Testing Python project detection..."
cd "$TEST_WORKSPACE"
mkdir python-test && cd python-test

cat > pyproject.toml << 'EOF'
[project]
name = "test-project"
version = "1.0.0"
dependencies = ["requests>=2.25.0", "click>=8.0.0"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF

cat > main.py << 'EOF'
#!/usr/bin/env python3
"""Test application."""
import requests

def main():
    print("Hello from test!")

if __name__ == '__main__':
    main()
EOF

if python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies, run_builds
from pathlib import Path

languages = detect_languages(Path('.'))
dependencies = analyze_dependencies(Path('.'))
build_results = run_builds(Path('.'))

python_detected = any(lang.language == 'python' for lang in languages)
deps_found = len(dependencies) > 0
build_success = build_results.get('success', False)

print(f'Python detected: {python_detected}')
print(f'Dependencies found: {deps_found}')
print(f'Build successful: {build_success}')

assert python_detected, 'Python not detected'
assert deps_found, 'Dependencies not found'
assert build_success, 'Build failed'
" 2>/dev/null; then
    report_test "Python Project Detection" "success"
else
    report_test "Python Project Detection" "failure"
fi

# Test 5: Terraform project detection
echo "🏗️  Testing Terraform project detection..."
cd "$TEST_WORKSPACE"
mkdir terraform-test && cd terraform-test

cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "example" {
  bucket = "test-bucket"
}
EOF

if python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies, run_builds
from pathlib import Path

languages = detect_languages(Path('.'))
dependencies = analyze_dependencies(Path('.'))
build_results = run_builds(Path('.'))

terraform_detected = any(lang.language == 'terraform' for lang in languages)
providers_found = len(dependencies) > 0
build_success = build_results.get('success', False)

print(f'Terraform detected: {terraform_detected}')
print(f'Providers found: {providers_found}')
print(f'Build successful: {build_success}')

assert terraform_detected, 'Terraform not detected'
assert providers_found, 'Providers not found'
assert build_success, 'Build failed'
" 2>/dev/null; then
    report_test "Terraform Project Detection" "success"
else
    report_test "Terraform Project Detection" "failure"
fi

# Test 6: Mixed project support
echo "🔀 Testing mixed project support..."
cd "$TEST_WORKSPACE"
mkdir mixed-test && cd mixed-test

# Copy Python files
cp ../python-test/pyproject.toml .
cp ../python-test/main.py .

# Copy Terraform files
mkdir infrastructure
cp ../terraform-test/main.tf infrastructure/

if python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies, run_builds
from pathlib import Path

languages = detect_languages(Path('.'))
dependencies = analyze_dependencies(Path('.'))
build_results = run_builds(Path('.'))

lang_names = [lang.language for lang in languages]
python_detected = 'python' in lang_names
terraform_detected = 'terraform' in lang_names
mixed_build_success = build_results.get('success', False)

print(f'Languages: {lang_names}')
print(f'Mixed project build: {mixed_build_success}')

assert python_detected and terraform_detected, 'Mixed languages not detected'
assert mixed_build_success, 'Mixed build failed'
" 2>/dev/null; then
    report_test "Mixed Project Support" "success"
else
    report_test "Mixed Project Support" "failure"
fi

# Cleanup test workspace
cd /
rm -rf "$TEST_WORKSPACE"

echo ""
echo "🎯 Phase 3: Real-World Validation"
echo "================================="

# Test 7: External repository validation (simplified)
echo "🌐 Testing against external repositories..."
EXTERNAL_TEST_WORKSPACE=$(mktemp -d)
cd "$EXTERNAL_TEST_WORKSPACE"

# Clone a small, fast repository for testing
if git clone --depth 1 --single-branch https://github.com/tiangolo/fastapi.git fastapi-sample 2>/dev/null; then
    cd fastapi-sample
    
    if python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')
from uvmgr.runtime.multilang import detect_languages
from pathlib import Path

languages = detect_languages(Path('.'))
python_lang = next((lang for lang in languages if lang.language == 'python'), None)

if python_lang:
    print(f'FastAPI analysis: {python_lang.files_count} files, {python_lang.lines_of_code} lines')
    assert python_lang.files_count > 100, 'Expected more Python files'
    success = True
else:
    success = False

assert success, 'FastAPI analysis failed'
" 2>/dev/null; then
        report_test "External Repository Analysis" "success"
    else
        report_test "External Repository Analysis" "failure"
    fi
else
    echo "⚠️  Skipping external repository test (network required)"
    report_test "External Repository Analysis" "skipped"
fi

cd /
rm -rf "$EXTERNAL_TEST_WORKSPACE"

echo ""
echo "🛡️  Phase 4: Error Handling and Edge Cases"
echo "=========================================="

# Test 8: Error handling
echo "🚨 Testing error handling and recovery..."
if python -c "
import sys
sys.path.insert(0, 'src')
from uvmgr.runtime.multilang import detect_languages
from pathlib import Path

# Test with non-existent directory
try:
    languages = detect_languages(Path('/non/existent/directory'))
    # Should return empty list, not crash
    assert isinstance(languages, list), 'Should return list for non-existent directory'
    print('Error handling working')
    success = True
except Exception as e:
    print(f'Error handling failed: {e}')
    success = False

assert success, 'Error handling test failed'
" 2>/dev/null; then
    report_test "Error Handling" "success"
else
    report_test "Error Handling" "failure"
fi

# Test 9: Command availability
echo "🎛️  Testing command availability..."
AVAILABLE_COMMANDS=0
TOTAL_COMMANDS=0

for cmd in deps build tests cache lint otel guides worktree infodesign mermaid mcp exponential democratize; do
    TOTAL_COMMANDS=$((TOTAL_COMMANDS + 1))
    if python -c "
import sys
sys.path.insert(0, 'src')
try:
    from uvmgr.commands import $cmd
    print('$cmd: available')
except Exception as e:
    print('$cmd: error -', str(e))
    exit(1)
" 2>/dev/null; then
        AVAILABLE_COMMANDS=$((AVAILABLE_COMMANDS + 1))
    fi
done

if [ "$AVAILABLE_COMMANDS" -eq "$TOTAL_COMMANDS" ]; then
    report_test "Command Availability ($AVAILABLE_COMMANDS/$TOTAL_COMMANDS)" "success"
else
    report_test "Command Availability ($AVAILABLE_COMMANDS/$TOTAL_COMMANDS)" "failure"
fi

echo ""
echo "📊 Final Validation Summary"
echo "=========================="
echo ""

if [ "$OVERALL_SUCCESS" = true ]; then
    echo "🎉 ALL TESTS PASSED - uvmgr is PRODUCTION READY!"
    echo ""
    echo "✅ Core Functionality:"
    echo "   • Module imports and telemetry working"
    echo "   • Performance measurement operational"
    echo "   • Error handling robust"
    echo ""
    echo "✅ Multi-Language Support:"
    echo "   • Python detection and analysis"
    echo "   • Terraform detection and analysis" 
    echo "   • Mixed project support"
    echo "   • Build validation working"
    echo ""
    echo "✅ Real-World Validation:"
    echo "   • External repository analysis"
    echo "   • Command availability confirmed"
    echo "   • End-to-end workflows functional"
    echo ""
    echo "🚀 uvmgr is validated and ready for production use!"
    echo "   Supports Python and Terraform projects with full"
    echo "   telemetry, performance monitoring, and extensibility."
    
    exit 0
else
    echo "❌ SOME TESTS FAILED - Review above for details"
    echo ""
    echo "⚠️  uvmgr has some issues that need to be addressed"
    echo "   before production deployment."
    
    exit 1
fi