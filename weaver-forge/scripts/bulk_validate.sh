#!/bin/bash
# Bulk validation script for multiple registries

set -e

echo "=== Bulk Semantic Convention Validation ==="
echo

# Find all registry directories
registries=$(find . -name "registry_manifest.yaml" -type f | xargs -I {} dirname {})

total=0
passed=0
failed=0

for registry in $registries; do
    echo "Checking registry: $registry"
    
    if uvmgr weaver check --registry "$registry" --future > /dev/null 2>&1; then
        echo "  ✓ PASSED"
        ((passed++))
    else
        echo "  ✗ FAILED"
        ((failed++))
        # Show error details
        uvmgr weaver check --registry "$registry" --future 2>&1 | grep -E "^  ×" | head -5
    fi
    
    ((total++))
    echo
done

echo "=== Summary ==="
echo "Total registries: $total"
echo "Passed: $passed"
echo "Failed: $failed"

if [ $failed -gt 0 ]; then
    exit 1
fi