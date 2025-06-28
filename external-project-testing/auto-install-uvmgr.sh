#!/bin/bash
set -euo pipefail

# uvmgr Auto-Install Script
# =========================
# 
# This script automatically installs and configures uvmgr in any Python project,
# making it ready to enhance the existing development workflow.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/yourusername/uvmgr/main/external-project-testing/auto-install-uvmgr.sh | bash
#   OR
#   ./auto-install-uvmgr.sh [project-directory]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory (default to current directory)
PROJECT_DIR="${1:-$(pwd)}"
UVMGR_VERSION="${UVMGR_VERSION:-latest}"

echo -e "${BLUE}🚀 uvmgr Auto-Install & Integration${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "Project Directory: ${PROJECT_DIR}"
echo -e "uvmgr Version: ${UVMGR_VERSION}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if directory exists and navigate to it
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Directory $PROJECT_DIR does not exist"
    exit 1
fi

cd "$PROJECT_DIR"
print_status "Working in: $(pwd)"

# Detect existing Python project structure
detect_project_type() {
    local project_type="unknown"
    local build_system="unknown"
    local package_manager="unknown"
    
    if [ -f "pyproject.toml" ]; then
        project_type="python"
        if grep -q "uv" pyproject.toml 2>/dev/null; then
            package_manager="uv"
        elif grep -q "poetry" pyproject.toml 2>/dev/null; then
            package_manager="poetry"
        elif grep -q "setuptools" pyproject.toml 2>/dev/null; then
            package_manager="pip"
        fi
        
        if grep -q "hatchling" pyproject.toml 2>/dev/null; then
            build_system="hatch"
        elif grep -q "poetry" pyproject.toml 2>/dev/null; then
            build_system="poetry"
        elif grep -q "setuptools" pyproject.toml 2>/dev/null; then
            build_system="setuptools"
        fi
    elif [ -f "setup.py" ] || [ -f "setup.cfg" ]; then
        project_type="python"
        package_manager="pip"
        build_system="setuptools"
    elif [ -f "requirements.txt" ]; then
        project_type="python"
        package_manager="pip"
        build_system="setuptools"
    fi
    
    echo "$project_type|$build_system|$package_manager"
}

# Detect project configuration
PROJECT_INFO=$(detect_project_type)
PROJECT_TYPE=$(echo "$PROJECT_INFO" | cut -d'|' -f1)
BUILD_SYSTEM=$(echo "$PROJECT_INFO" | cut -d'|' -f2)
PACKAGE_MANAGER=$(echo "$PROJECT_INFO" | cut -d'|' -f3)

echo -e "${BLUE}Project Analysis:${NC}"
echo -e "  Type: $PROJECT_TYPE"
echo -e "  Build System: $BUILD_SYSTEM"
echo -e "  Package Manager: $PACKAGE_MANAGER"
echo ""

if [ "$PROJECT_TYPE" != "python" ]; then
    print_warning "This doesn't appear to be a Python project"
    print_warning "uvmgr is designed for Python projects but will continue..."
fi

# Check if uv is installed
check_uv_installation() {
    if command -v uv >/dev/null 2>&1; then
        print_status "uv package manager is already installed"
        UV_VERSION=$(uv --version | cut -d' ' -f2)
        echo -e "  Version: $UV_VERSION"
    else
        print_status "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command -v uv >/dev/null 2>&1; then
            print_status "uv installation successful"
        else
            print_error "Failed to install uv"
            exit 1
        fi
    fi
}

# Install uvmgr
install_uvmgr() {
    print_status "Installing uvmgr..."
    
    # Create or activate virtual environment
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment with uv..."
        uv venv
    else
        print_status "Using existing virtual environment"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install uvmgr with all features
    if [ "$UVMGR_VERSION" = "latest" ]; then
        print_status "Installing latest uvmgr from git..."
        uv pip install "git+https://github.com/yourusername/uvmgr.git[mcp,ai,otel,build]"
    else
        print_status "Installing uvmgr version $UVMGR_VERSION..."
        uv pip install "uvmgr[mcp,ai,otel,build]==$UVMGR_VERSION"
    fi
    
    # Verify installation
    if command -v uvmgr >/dev/null 2>&1; then
        print_status "uvmgr installation successful"
        UVMGR_INSTALLED_VERSION=$(uvmgr --version 2>/dev/null || echo "unknown")
        echo -e "  Version: $UVMGR_INSTALLED_VERSION"
    else
        print_error "Failed to install uvmgr"
        exit 1
    fi
}

# Configure uvmgr for the project
configure_uvmgr() {
    print_status "Configuring uvmgr for this project..."
    
    # Create uvmgr configuration if it doesn't exist
    if [ ! -f ".uvmgr.toml" ]; then
        print_status "Creating .uvmgr.toml configuration..."
        cat > .uvmgr.toml << EOF
[project]
name = "$(basename "$PWD")"
description = "Python project enhanced with uvmgr"

[build]
backend = "$BUILD_SYSTEM"
package_manager = "$PACKAGE_MANAGER"

[ai]
enabled = true
provider = "openai"  # or "groq"

[otel]
enabled = true
service_name = "$(basename "$PWD")"
export_endpoint = "http://localhost:4317"

[mcp]
enabled = true
port = 3001

[cache]
enabled = true
directory = ".uvmgr_cache"
EOF
        print_status "Created .uvmgr.toml configuration"
    else
        print_status "Using existing .uvmgr.toml configuration"
    fi
    
    # Add uvmgr to .gitignore if it exists
    if [ -f ".gitignore" ]; then
        if ! grep -q ".uvmgr_cache" .gitignore; then
            echo -e "\n# uvmgr cache\n.uvmgr_cache/" >> .gitignore
            print_status "Added uvmgr cache to .gitignore"
        fi
    fi
    
    # Create directory structure if minimal
    if [ ! -d "src" ] && [ ! -d "tests" ]; then
        print_status "Creating basic project structure..."
        mkdir -p src tests docs
        
        if [ ! -f "tests/__init__.py" ]; then
            touch tests/__init__.py
        fi
        
        if [ ! -f "README.md" ]; then
            cat > README.md << EOF
# $(basename "$PWD")

Python project enhanced with uvmgr.

## Quick Start

\`\`\`bash
# Install dependencies
uvmgr deps add <package>

# Run tests
uvmgr tests run

# Lint code
uvmgr lint check
uvmgr lint fix

# Build package
uvmgr build dist

# AI assistance
uvmgr ai assist "Help me with this code"

# Start MCP server for AI integration
uvmgr serve start
\`\`\`

## Development

This project uses uvmgr for unified Python workflow management.

- **Dependencies**: \`uvmgr deps\`
- **Testing**: \`uvmgr tests\`
- **Linting**: \`uvmgr lint\`
- **Building**: \`uvmgr build\`
- **AI Features**: \`uvmgr ai\`
- **Observability**: \`uvmgr otel\`
EOF
            print_status "Created README.md with uvmgr usage"
        fi
    fi
}

# Enhance existing project configuration
enhance_existing_project() {
    print_status "Enhancing existing project configuration..."
    
    # If pyproject.toml exists, add uvmgr as dev dependency
    if [ -f "pyproject.toml" ]; then
        if ! grep -q "uvmgr" pyproject.toml; then
            print_status "Adding uvmgr to pyproject.toml dev dependencies..."
            
            # Create backup
            cp pyproject.toml pyproject.toml.backup
            
            # Add uvmgr to dev dependencies
            if grep -q "\[project.optional-dependencies\]" pyproject.toml; then
                # Add to existing optional-dependencies
                sed -i '/\[project\.optional-dependencies\]/,/^\[/ s/dev = \[/dev = [\n    "uvmgr[mcp,ai,otel,build]",/' pyproject.toml
            elif grep -q "dev = \[" pyproject.toml; then
                # Add to existing dev array
                sed -i '/dev = \[/a\    "uvmgr[mcp,ai,otel,build]",' pyproject.toml
            else
                # Add new optional-dependencies section
                echo "" >> pyproject.toml
                echo "[project.optional-dependencies]" >> pyproject.toml
                echo 'dev = ["uvmgr[mcp,ai,otel,build]"]' >> pyproject.toml
            fi
            
            print_status "Added uvmgr to pyproject.toml"
        else
            print_status "uvmgr already present in pyproject.toml"
        fi
    fi
    
    # Add Poe tasks for uvmgr integration
    if command -v poe >/dev/null 2>&1 || grep -q "poethepoet" pyproject.toml 2>/dev/null; then
        print_status "Adding Poe the Poet tasks for uvmgr..."
        
        if ! grep -q "\[tool.poe.tasks\]" pyproject.toml; then
            cat >> pyproject.toml << EOF

[tool.poe.tasks]
# uvmgr integration tasks
uvmgr-test = "uvmgr tests run"
uvmgr-lint = "uvmgr lint check"
uvmgr-lint-fix = "uvmgr lint fix"
uvmgr-build = "uvmgr build dist"
uvmgr-ai = "uvmgr ai assist"
uvmgr-serve = "uvmgr serve start"
uvmgr-otel = "uvmgr otel validate"
EOF
            print_status "Added uvmgr Poe tasks"
        else
            print_status "Poe tasks section already exists"
        fi
    fi
}

# Test uvmgr installation
test_uvmgr() {
    print_status "Testing uvmgr installation..."
    
    # Test basic commands
    echo -e "${BLUE}Testing uvmgr commands:${NC}"
    
    # Test help
    if uvmgr --help > /dev/null 2>&1; then
        print_status "uvmgr --help works"
    else
        print_error "uvmgr --help failed"
    fi
    
    # Test deps list
    if uvmgr deps list > /dev/null 2>&1; then
        print_status "uvmgr deps list works"
    else
        print_warning "uvmgr deps list failed (may be expected for new projects)"
    fi
    
    # Test other commands
    commands=("tests --help" "lint --help" "build --help" "ai --help" "serve --help")
    for cmd in "${commands[@]}"; do
        if uvmgr $cmd > /dev/null 2>&1; then
            print_status "uvmgr $cmd works"
        else
            print_warning "uvmgr $cmd failed"
        fi
    done
}

# Create development workflow examples
create_workflow_examples() {
    print_status "Creating workflow examples..."
    
    mkdir -p .uvmgr/examples
    
    # Create development workflow script
    cat > .uvmgr/examples/dev-workflow.sh << 'EOF'
#!/bin/bash
# Development Workflow with uvmgr
# ==============================

set -e

echo "🚀 Starting development workflow with uvmgr..."

# 1. Install/update dependencies
echo "📦 Managing dependencies..."
uvmgr deps list
uvmgr deps add pytest --dev
uvmgr deps add requests

# 2. Code quality checks
echo "🔍 Running code quality checks..."
uvmgr lint check
uvmgr lint fix

# 3. Run tests
echo "🧪 Running tests..."
uvmgr tests run
uvmgr tests coverage

# 4. Build package
echo "📦 Building package..."
uvmgr build dist

# 5. AI assistance (optional, requires API keys)
echo "🤖 AI assistance available:"
echo "  uvmgr ai assist 'Help me optimize this code'"
echo "  uvmgr ai fix-tests"
echo "  uvmgr ai plan 'Add authentication'"

# 6. Observability (optional)
echo "📊 Observability features:"
echo "  uvmgr otel validate"
echo "  uvmgr otel demo"

# 7. MCP server for AI integration
echo "🔗 MCP server for AI agents:"
echo "  uvmgr serve start"

echo "✅ Development workflow complete!"
EOF
    
    chmod +x .uvmgr/examples/dev-workflow.sh
    
    # Create project enhancement script
    cat > .uvmgr/examples/enhance-project.py << 'EOF'
#!/usr/bin/env python3
"""
Project Enhancement with uvmgr
=============================

This script demonstrates how to programmatically enhance
a Python project with uvmgr capabilities.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}: {e}")
        return False


def enhance_project():
    """Enhance the current project with uvmgr."""
    print("🚀 Enhancing project with uvmgr...")
    
    # Add common dev dependencies
    dev_deps = ["pytest", "pytest-cov", "ruff", "mypy", "black"]
    for dep in dev_deps:
        run_command(f"uvmgr deps add {dep} --dev")
    
    # Add production dependencies based on project type
    if Path("src").exists():
        # Assume it's a package
        run_command("uvmgr deps add click")  # CLI framework
    
    # Set up code quality
    run_command("uvmgr lint check")
    
    # Create basic test if none exist
    if not any(Path("tests").glob("test_*.py")):
        print("📝 Creating basic test file...")
        test_content = '''"""Basic test file."""

def test_basic():
    """Basic test to ensure testing works."""
    assert True


def test_import():
    """Test that the main module can be imported."""
    try:
        # Try to import the main module
        # Adjust this based on your project structure
        pass
    except ImportError:
        pass  # It's okay if no main module exists yet
'''
        Path("tests/test_basic.py").write_text(test_content)
    
    # Run tests
    run_command("uvmgr tests run")
    
    # Build package
    run_command("uvmgr build dist")
    
    print("✅ Project enhancement complete!")
    print("\n🎯 Next steps:")
    print("  1. Configure AI provider: export OPENAI_API_KEY=your_key")
    print("  2. Start MCP server: uvmgr serve start")
    print("  3. Enable OTEL: uvmgr otel validate")
    print("  4. Use AI assistance: uvmgr ai assist 'help me with this project'")


if __name__ == "__main__":
    enhance_project()
EOF
    
    chmod +x .uvmgr/examples/enhance-project.py
    
    print_status "Created workflow examples in .uvmgr/examples/"
}

# Main execution
main() {
    echo -e "${BLUE}Starting uvmgr auto-installation process...${NC}"
    echo ""
    
    # Install prerequisites
    check_uv_installation
    
    # Install uvmgr
    install_uvmgr
    
    # Configure for this project
    configure_uvmgr
    
    # Enhance existing project
    enhance_existing_project
    
    # Test installation
    test_uvmgr
    
    # Create examples
    create_workflow_examples
    
    echo ""
    echo -e "${GREEN}🎉 uvmgr auto-installation complete!${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo -e "  ${GREEN}uvmgr --help${NC}                 # Show all commands"
    echo -e "  ${GREEN}uvmgr deps list${NC}              # List dependencies"
    echo -e "  ${GREEN}uvmgr tests run${NC}              # Run tests"
    echo -e "  ${GREEN}uvmgr lint check${NC}             # Check code quality"
    echo -e "  ${GREEN}uvmgr build dist${NC}             # Build package"
    echo -e "  ${GREEN}uvmgr ai assist 'help'${NC}       # AI assistance"
    echo -e "  ${GREEN}uvmgr serve start${NC}            # Start MCP server"
    echo ""
    echo -e "${BLUE}Workflow Examples:${NC}"
    echo -e "  ${GREEN}./.uvmgr/examples/dev-workflow.sh${NC}     # Complete dev workflow"
    echo -e "  ${GREEN}python .uvmgr/examples/enhance-project.py${NC}  # Programmatic enhancement"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  Project config: ${GREEN}.uvmgr.toml${NC}"
    echo -e "  Cache directory: ${GREEN}.uvmgr_cache/${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} For AI features, set OPENAI_API_KEY or GROQ_API_KEY environment variable"
}

# Execute main function
main "$@"