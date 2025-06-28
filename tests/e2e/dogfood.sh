#!/bin/bash
# Run the uvmgr dogfooding test loop using uvmgr itself

set -e  # Exit on error

echo "🐕 Starting uvmgr Dogfooding Test Loop"
echo "===================================="
echo ""

# First, ensure uvmgr is available
if ! command -v uvmgr &> /dev/null; then
    echo "❌ Error: uvmgr not found in PATH"
    echo "Please install uvmgr first with: pip install -e ."
    exit 1
fi

echo "✓ uvmgr found: $(which uvmgr)"
echo ""

# Run the dogfooding tests using uvmgr's Python
echo "Running dogfooding tests..."
uvmgr run python tests/e2e/run_dogfood_loop.py "$@"

# If that succeeds, run the full e2e test suite
if [ $? -eq 0 ]; then
    echo ""
    echo "Running full e2e test suite with uvmgr..."
    uvmgr tests run tests/e2e/ -v
fi

echo ""
echo "✨ Dogfooding complete!"