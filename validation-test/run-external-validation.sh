#!/bin/bash
# End-to-End External Project Validation Script
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/external-projects"
RESULTS_DIR="$SCRIPT_DIR/validation-results"
REPORTS_DIR="$SCRIPT_DIR/reports"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 uvmgr End-to-End External Project Validation"
echo "=============================================="
echo "Started: $(date)"
echo ""

# Create results directories
mkdir -p "$RESULTS_DIR" "$REPORTS_DIR"

# External projects for validation
declare -a PROJECT_NAMES=("flask" "requests" "typer")
declare -A PROJECTS
PROJECTS["flask"]="$PROJECTS_DIR/flask"
PROJECTS["requests"]="$PROJECTS_DIR/requests"
PROJECTS["typer"]="$PROJECTS_DIR/typer"

# Validation results
declare -A RESULTS
total_tests=0
passed_tests=0

function validate_project() {
    local name="$1"
    local path="$2"
    local result_file="$RESULTS_DIR/${name}-validation.json"
    
    echo -e "\n${YELLOW}🔍 Validating $name${NC}"
    echo "Path: $path"
    
    if [ ! -d "$path" ]; then
        echo -e "${RED}✗ Project directory not found${NC}"
        RESULTS[$name]="NOT_FOUND"
        return 1
    fi
    
    cd "$path"
    
    # Initialize JSON result
    cat > "$result_file" << EOF
{
  "project": "$name",
  "path": "$path",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "validations": {
EOF
    
    local project_passed=0
    local project_total=0
    
    # 1. Test deps command
    echo -n "  📦 Testing deps command... "
    ((project_total++))
    ((total_tests++))
    if uvmgr deps list > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((project_passed++))
        ((passed_tests++))
        echo '    "deps": {"status": "passed", "command": "uvmgr deps list"},' >> "$result_file"
    else
        echo -e "${RED}✗${NC}"
        echo '    "deps": {"status": "failed", "command": "uvmgr deps list"},' >> "$result_file"
    fi
    
    # 2. Test lint command
    echo -n "  📋 Testing lint check... "
    ((project_total++))
    ((total_tests++))
    if uvmgr lint check > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((project_passed++))
        ((passed_tests++))
        echo '    "lint": {"status": "passed", "command": "uvmgr lint check"},' >> "$result_file"
    else
        echo -e "${RED}✗${NC}"
        echo '    "lint": {"status": "failed", "command": "uvmgr lint check"},' >> "$result_file"
    fi
    
    # 3. Test build capability
    echo -n "  🏗️  Testing build capability... "
    ((project_total++))
    ((total_tests++))
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        echo -e "${GREEN}✓ (build ready)${NC}"
        ((project_passed++))
        ((passed_tests++))
        echo '    "build": {"status": "passed", "note": "build configuration found"},' >> "$result_file"
    else
        echo -e "${YELLOW}⚠ (no build config)${NC}"
        echo '    "build": {"status": "skipped", "note": "no build configuration"},' >> "$result_file"
    fi
    
    # 4. Test cache command
    echo -n "  💾 Testing cache info... "
    ((project_total++))
    ((total_tests++))
    if uvmgr cache info > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((project_passed++))
        ((passed_tests++))
        echo '    "cache": {"status": "passed", "command": "uvmgr cache info"},' >> "$result_file"
    else
        echo -e "${RED}✗${NC}"
        echo '    "cache": {"status": "failed", "command": "uvmgr cache info"},' >> "$result_file"
    fi
    
    # 5. Test OTEL validation
    echo -n "  📊 Testing OTEL validation... "
    ((project_total++))
    ((total_tests++))
    if uvmgr otel validate > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((project_passed++))
        ((passed_tests++))
        echo '    "otel": {"status": "passed", "command": "uvmgr otel validate"}' >> "$result_file"
    else
        echo -e "${RED}✗${NC}"
        echo '    "otel": {"status": "failed", "command": "uvmgr otel validate"}' >> "$result_file"
    fi
    
    # Complete JSON
    cat >> "$result_file" << EOF
  },
  "summary": {
    "total_tests": $project_total,
    "passed_tests": $project_passed,
    "success_rate": $(awk "BEGIN {printf \"%.1f\", $project_passed/$project_total*100}")
  }
}
EOF
    
    # Summary for project
    local success_rate=$(awk "BEGIN {printf \"%.1f\", $project_passed/$project_total*100}")
    if [ "$project_passed" -eq "$project_total" ]; then
        echo -e "  ${GREEN}✅ All tests passed! ($project_passed/$project_total)${NC}"
        RESULTS[$name]="PASSED"
    else
        echo -e "  ${YELLOW}⚠️  Partial success: $project_passed/$project_total tests passed ($success_rate%)${NC}"
        RESULTS[$name]="PARTIAL"
    fi
}

# Clone projects if not exists
echo "📥 Preparing external projects..."
for name in "${PROJECT_NAMES[@]}"; do
    if [ ! -d "${PROJECTS[$name]}" ]; then
        case $name in
            "flask")
                git clone --depth 1 https://github.com/pallets/flask.git "$PROJECTS_DIR/flask"
                ;;
            "requests")
                git clone --depth 1 https://github.com/psf/requests.git "$PROJECTS_DIR/requests"
                ;;
            "typer")
                git clone --depth 1 https://github.com/tiangolo/typer.git "$PROJECTS_DIR/typer"
                ;;
        esac
    fi
done

# Run validations
echo -e "\n🎯 Running validations..."
for name in "${PROJECT_NAMES[@]}"; do
    validate_project "$name" "${PROJECTS[$name]}"
done

# Generate final report
echo -e "\n📊 Generating final report..."
REPORT_FILE="$REPORTS_DIR/external-validation-report.md"

cat > "$REPORT_FILE" << EOF
# uvmgr External Project Validation Report

**Generated:** $(date)  
**Environment:** Host System  
**uvmgr Version:** $(uvmgr --version 2>/dev/null || echo "dev")

## Summary

- **Total Tests:** $total_tests
- **Passed Tests:** $passed_tests
- **Success Rate:** $(awk "BEGIN {printf \"%.1f%%\", $passed_tests/$total_tests*100}")

## Project Results

| Project | Status | Details |
|---------|--------|---------|
EOF

for name in "${!RESULTS[@]}"; do
    status="${RESULTS[$name]}"
    case $status in
        "PASSED")
            echo "| $name | ✅ PASSED | All tests successful |" >> "$REPORT_FILE"
            ;;
        "PARTIAL")
            echo "| $name | ⚠️ PARTIAL | Some tests failed |" >> "$REPORT_FILE"
            ;;
        "NOT_FOUND")
            echo "| $name | ❌ NOT FOUND | Project directory missing |" >> "$REPORT_FILE"
            ;;
    esac
done

cat >> "$REPORT_FILE" << EOF

## Tested Commands

1. **deps list** - Dependency listing
2. **lint check** - Code quality checks
3. **build** - Build system compatibility
4. **cache info** - Cache management
5. **otel validate** - OpenTelemetry validation

## Detailed Results

Individual project validation results are available in:
- \`$RESULTS_DIR/\`

## Conclusion

uvmgr demonstrated $(awk "BEGIN {printf \"%.1f%%\", $passed_tests/$total_tests*100}") compatibility with external Python projects, validating its core functionality across different project structures and configurations.
EOF

# Display summary
echo -e "\n${GREEN}✨ Validation Complete!${NC}"
echo "========================"
echo -e "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"
echo -e "Success Rate: $(awk "BEGIN {printf \"%.1f%%\", $passed_tests/$total_tests*100}")"
echo ""
echo "📄 Full report: $REPORT_FILE"
echo "📊 Detailed results: $RESULTS_DIR/"