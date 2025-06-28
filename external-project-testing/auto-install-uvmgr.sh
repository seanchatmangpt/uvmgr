#!/bin/bash
# Auto-install uvmgr script for external project testing
# This script installs uvmgr into an external project for 8020 validation

set -euo pipefail

PROJECT_PATH="${1:-}"
UVMGR_SOURCE="${UVMGR_SOURCE:-/Users/sac/dev/uvmgr}"

if [[ -z "$PROJECT_PATH" ]]; then
    echo "Usage: $0 <project_path>"
    echo "Example: $0 /tmp/test_project"
    exit 1
fi

if [[ ! -d "$PROJECT_PATH" ]]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

echo "🔧 Installing uvmgr into external project: $PROJECT_PATH"

# Change to project directory
cd "$PROJECT_PATH"

# Check if uv is available, install if not
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Initialize uv project if no pyproject.toml exists
if [[ ! -f "pyproject.toml" ]]; then
    echo "📋 Initializing uv project..."
    uv init --no-readme --name "$(basename "$PROJECT_PATH")"
fi

# Install uvmgr from local source in development mode
echo "🚀 Installing uvmgr from source..."
if [[ -d "$UVMGR_SOURCE" ]]; then
    uv add --editable "$UVMGR_SOURCE"
else
    echo "Warning: uvmgr source not found at $UVMGR_SOURCE, installing from PyPI"
    uv add uvmgr
fi

# Install common development dependencies for testing
echo "🔨 Installing development dependencies..."
uv add --dev pytest pytest-cov pytest-mock

# Verify installation
echo "✅ Verifying uvmgr installation..."
if uv run uvmgr --version; then
    echo "✅ uvmgr successfully installed in $PROJECT_PATH"
    
    # Create basic test to verify uvmgr works
    mkdir -p tests
    cat > tests/test_uvmgr_integration.py << 'EOF'
"""Test uvmgr integration in external project."""
import subprocess
import sys

def test_uvmgr_version():
    """Test that uvmgr is available and returns version."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "--version"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "uvmgr" in result.stdout

def test_uvmgr_help():
    """Test that uvmgr help works."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "--help"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_uvmgr_deps_list():
    """Test that uvmgr deps list works."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "deps", "list"], 
                          capture_output=True, text=True)
    # Should work even if no dependencies installed
    assert result.returncode == 0
EOF
    
    echo "📝 Created integration test: tests/test_uvmgr_integration.py"
    echo "🎉 Setup complete! uvmgr is ready for external project testing."
    
    # Run a quick test to verify everything works
    echo "🧪 Running quick integration test..."
    if uv run pytest tests/test_uvmgr_integration.py -v; then
        echo "✅ Integration test passed!"
    else
        echo "⚠️ Integration test failed, but uvmgr is installed"
    fi
    
else
    echo "❌ uvmgr installation failed"
    exit 1
fi