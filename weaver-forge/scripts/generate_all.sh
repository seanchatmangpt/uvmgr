#!/bin/bash
# Generate all outputs from semantic conventions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY_PATH="$PROJECT_ROOT/weaver-forge/registry"

echo "=== Generating from Semantic Conventions ==="
echo "Registry: $REGISTRY_PATH"
echo

# Validate first
echo "1. Validating registry..."
if ! uvmgr weaver check --registry "$REGISTRY_PATH" --future; then
    echo "✗ Validation failed. Fix errors before generating."
    exit 1
fi

echo
echo "2. Generating Python constants..."
uvmgr weaver generate python --registry "$REGISTRY_PATH"

echo
echo "3. Generating Markdown documentation..."
uvmgr weaver docs --registry "$REGISTRY_PATH" --output "$PROJECT_ROOT/weaver-forge/docs"

echo
echo "4. Generating registry statistics..."
uvmgr weaver stats --registry "$REGISTRY_PATH"

echo
echo "5. Resolving full registry..."
uvmgr weaver resolve --registry "$REGISTRY_PATH" --output "$PROJECT_ROOT/weaver-forge/resolved.json" --format json

echo
echo "=== Generation Complete ==="
echo
echo "Generated files:"
echo "  - Python: src/uvmgr/core/semconv.py"
echo "  - Docs: weaver-forge/docs/"
echo "  - Resolved: weaver-forge/resolved.json"
echo
echo "To use in code:"
echo "  from uvmgr.core.semconv import CliAttributes, PackageAttributes"