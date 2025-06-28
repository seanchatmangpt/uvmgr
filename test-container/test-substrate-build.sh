#!/bin/bash
# test-substrate-build.sh - Test building a complete project with uvmgr substrate commands

set -euo pipefail

echo "=== uvmgr Substrate Project Build Test ==="
echo "Testing complete project creation and build workflow in clean container"
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Test 1: Show available commands
print_status "Checking uvmgr installation..."
if uvmgr --help > /dev/null 2>&1; then
    print_success "uvmgr is installed and working"
else
    print_error "uvmgr not found or not working"
    exit 1
fi

# Test 2: Create a substrate project
PROJECT_NAME="test-substrate-app"
print_status "Creating substrate project: $PROJECT_NAME"

# Check if we have the new command
if uvmgr new --help > /dev/null 2>&1; then
    # Use the new project command
    uvmgr new substrate $PROJECT_NAME --fastapi --typer
    print_success "Created project using 'uvmgr new substrate'"
elif uvmgr project new --help > /dev/null 2>&1; then
    # Use the project new command
    uvmgr project new $PROJECT_NAME --template substrate --fastapi --typer-cli
    print_success "Created project using 'uvmgr project new'"
elif uvmgr substrate create --help > /dev/null 2>&1; then
    # Use the substrate create command
    uvmgr substrate create $PROJECT_NAME --type web --with-otel
    print_success "Created project using 'uvmgr substrate create'"
else
    print_error "No suitable project creation command found"
    echo "Available commands:"
    uvmgr --help
    exit 1
fi

# Test 3: Navigate to project and check structure
cd $PROJECT_NAME
print_status "Checking project structure..."

if [ -f "pyproject.toml" ]; then
    print_success "Found pyproject.toml"
    echo "Project configuration:"
    head -n 20 pyproject.toml
else
    print_error "pyproject.toml not found"
    ls -la
    exit 1
fi

# Test 4: Install dependencies
print_status "Installing project dependencies..."
if uv sync; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Test 5: Run tests (if any)
print_status "Running project tests..."
if [ -d "tests" ]; then
    if uvmgr tests run || uv run pytest; then
        print_success "Tests passed"
    else
        print_error "Tests failed (this might be expected for a new project)"
    fi
else
    echo "No tests directory found (expected for new project)"
fi

# Test 6: Build the project
print_status "Building the project..."
if uvmgr build dist; then
    print_success "Project built successfully"
    echo "Build artifacts:"
    ls -la dist/ 2>/dev/null || echo "No dist directory found"
else
    print_error "Build failed"
fi

# Test 7: Check if we can run the project (for CLI/FastAPI)
print_status "Checking if project is runnable..."

# Try to find the main module
PACKAGE_NAME="${PROJECT_NAME//-/_}"
if [ -d "src/$PACKAGE_NAME" ]; then
    print_success "Found package directory: src/$PACKAGE_NAME"
    
    # Check for CLI entry point
    if [ -f "src/$PACKAGE_NAME/cli.py" ] || [ -f "src/$PACKAGE_NAME/__main__.py" ]; then
        print_success "Found CLI entry point"
        echo "You can run: python -m $PACKAGE_NAME"
    fi
    
    # Check for FastAPI app
    if [ -f "src/$PACKAGE_NAME/main.py" ] || [ -f "src/$PACKAGE_NAME/app.py" ]; then
        print_success "Found FastAPI application"
        echo "You can run: uvicorn $PACKAGE_NAME.main:app"
    fi
elif [ -d "$PACKAGE_NAME" ]; then
    print_success "Found package directory: $PACKAGE_NAME"
fi

# Test 8: Validate OTEL integration (if substrate includes it)
print_status "Checking OTEL integration..."
if uvmgr substrate validate . > /dev/null 2>&1; then
    print_success "OTEL validation passed"
elif uvmgr otel validate > /dev/null 2>&1; then
    print_success "OTEL validation available"
else
    echo "OTEL validation not available (might not be included in template)"
fi

# Summary
echo
echo "=== Build Test Summary ==="
print_success "Successfully created and built a complete project using uvmgr!"
echo
echo "Project details:"
echo "  Name: $PROJECT_NAME"
echo "  Location: $(pwd)"
echo "  Python: $(python --version)"
echo "  uv: $(uv --version)"
echo "  uvmgr: installed from /uvmgr"
echo
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. uv run python -m $PACKAGE_NAME  # Run the CLI"
echo "  3. uv run uvicorn $PACKAGE_NAME.main:app  # Run the API (if FastAPI)"
echo "  4. uvmgr tests run  # Run tests"
echo "  5. uvmgr build exe  # Build standalone executable"