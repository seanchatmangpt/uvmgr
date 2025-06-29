#!/bin/bash
# Project Preparation Script for DoD Validation
# ==============================================
#
# This script prepares external projects for DoD validation by
# ensuring they have the necessary structure and dependencies.

set -euo pipefail

PROJECTS_DIR="/workdir/external-projects"

# Popular Python projects for comprehensive validation
declare -A PROJECTS=(
    ["flask"]="https://github.com/pallets/flask.git"
    ["requests"]="https://github.com/psf/requests.git"
    ["fastapi"]="https://github.com/fastapi/fastapi.git"
    ["pandas"]="https://github.com/pandas-dev/pandas.git"
    ["numpy"]="https://github.com/numpy/numpy.git"
    ["django"]="https://github.com/django/django.git"
    ["pytest"]="https://github.com/pytest-dev/pytest.git"
    ["rich"]="https://github.com/Textualize/rich.git"
    ["typer"]="https://github.com/tiangolo/typer.git"
    ["pydantic"]="https://github.com/pydantic/pydantic.git"
)

function prepare_project() {
    local name="$1"
    local url="$2"
    local project_dir="$PROJECTS_DIR/$name"
    
    echo "📦 Preparing $name..."
    
    # Clone if not exists
    if [ ! -d "$project_dir" ]; then
        echo "   Cloning $name from $url"
        git clone --depth 1 "$url" "$project_dir"
    else
        echo "   Project $name already exists, updating..."
        cd "$project_dir"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    fi
    
    cd "$project_dir"
    
    # Analyze project structure
    echo "   📋 Analyzing project structure..."
    
    # Check for Python files
    python_files=$(find . -name "*.py" | wc -l)
    echo "      Python files: $python_files"
    
    # Check for configuration files
    config_files=""
    [ -f "pyproject.toml" ] && config_files+="pyproject.toml "
    [ -f "setup.py" ] && config_files+="setup.py "
    [ -f "requirements.txt" ] && config_files+="requirements.txt "
    [ -f "Pipfile" ] && config_files+="Pipfile "
    [ -f "poetry.lock" ] && config_files+="poetry.lock "
    echo "      Config files: $config_files"
    
    # Check for test directories
    test_dirs=""
    [ -d "tests" ] && test_dirs+="tests/ "
    [ -d "test" ] && test_dirs+="test/ "
    echo "      Test directories: $test_dirs"
    
    # Check for CI/CD
    ci_files=""
    [ -d ".github/workflows" ] && ci_files+=".github/workflows/ "
    [ -f ".gitlab-ci.yml" ] && ci_files+=".gitlab-ci.yml "
    [ -f ".travis.yml" ] && ci_files+=".travis.yml "
    echo "      CI/CD files: $ci_files"
    
    # Create validation metadata
    cat > ".uvmgr-validation-metadata.json" << EOF
{
  "project_name": "$name",
  "repository_url": "$url",
  "analysis_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "structure": {
    "python_files": $python_files,
    "config_files": "$config_files",
    "test_directories": "$test_dirs",
    "ci_cd_files": "$ci_files"
  },
  "validation_ready": true
}
EOF
    
    echo "✅ $name prepared for validation"
}

function main() {
    echo "🎯 Preparing External Projects for DoD Validation"
    echo "================================================="
    
    mkdir -p "$PROJECTS_DIR"
    
    for project_name in "${!PROJECTS[@]}"; do
        prepare_project "$project_name" "${PROJECTS[$project_name]}"
        echo ""
    done
    
    echo "🎉 All projects prepared for validation!"
    echo "Projects available in: $PROJECTS_DIR"
    
    # List prepared projects
    echo ""
    echo "📋 Prepared Projects:"
    for project_dir in "$PROJECTS_DIR"/*/; do
        if [ -d "$project_dir" ]; then
            project_name=$(basename "$project_dir")
            echo "   • $project_name"
        fi
    done
}

main "$@"