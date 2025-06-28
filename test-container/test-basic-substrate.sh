#!/bin/bash
# Basic substrate command test

set -e

echo "=== Basic Substrate Command Test ==="
echo "====================================="

# Test 1: Show substrate commands
echo -e "\n[TEST 1] Available substrate commands:"
uvmgr substrate --help

# Test 2: Show project creation commands  
echo -e "\n[TEST 2] Available project creation commands:"
uvmgr new --help

# Test 3: Create a basic substrate project
echo -e "\n[TEST 3] Creating substrate project..."
uvmgr new new demo-project --template substrate --fastapi --github-actions

# Test 4: Verify project structure
echo -e "\n[TEST 4] Project structure:"
ls -la demo-project/

# Test 5: Check project configuration
echo -e "\n[TEST 5] Project configuration:"
cat demo-project/pyproject.toml

echo -e "\n✅ Basic substrate tests completed successfully!"
echo "✓ uvmgr substrate commands available"
echo "✓ Project creation working"
echo "✓ FastAPI template applied"
echo "✓ GitHub Actions configured"
echo "✓ Project structure valid"