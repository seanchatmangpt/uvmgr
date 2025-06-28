#!/bin/bash
# Master generation script for Weaver Forge instrumentation

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$FORGE_DIR")"

echo "🔨 Weaver Forge: Generating all instrumentation for uvmgr"
echo "========================================================="
echo ""

# Function to apply a forge template
apply_forge() {
    local forge_file=$1
    local description=$2
    
    echo "📝 $description"
    echo "   Template: $forge_file"
    
    # For this example, we'll just copy the generated files
    # In a real implementation, this would use the weaver-forge CLI
    
    # Extract output path and content from forge file
    # This is a simplified version - real implementation would parse YAML
    
    echo "   ✅ Applied successfully"
    echo ""
}

# Phase 1: Core Infrastructure
echo "🏗️  Phase 1: Core Infrastructure"
echo "--------------------------------"

# Check if instrumentation.py already exists
if [ ! -f "$PROJECT_ROOT/src/uvmgr/core/instrumentation.py" ]; then
    echo "📝 Creating instrumentation.py"
    # Extract and apply the template from the forge file
    # For now, we'll indicate what would happen
    echo "   Would create: src/uvmgr/core/instrumentation.py"
    echo "   ✅ Ready to apply"
else
    echo "   ✅ instrumentation.py already exists"
fi

# Check if semantic conventions exist
if [ ! -f "$PROJECT_ROOT/src/uvmgr/core/semconv.py" ]; then
    echo "📝 Creating semantic conventions"
    echo "   Would create: src/uvmgr/core/semconv.py"
    echo "   ✅ Ready to apply"
else
    echo "   ✅ semconv.py already exists"
fi

echo ""

# Phase 2: Command Instrumentation
echo "🎯 Phase 2: Command Instrumentation"
echo "-----------------------------------"

# List of commands that need instrumentation (excluding deps which is done)
COMMANDS=(
    "agent"
    "ai"
    "ap_scheduler"
    "build"
    "cache"
    "exec"
    "index"
    "lint"
    "project"
    "release"
    "remote"
    "serve"
    "shell"
    "tests"
    "tool"
)

echo "Commands to instrument: ${#COMMANDS[@]}"
echo ""

for cmd in "${COMMANDS[@]}"; do
    cmd_file="$PROJECT_ROOT/src/uvmgr/commands/${cmd}.py"
    
    if [ -f "$cmd_file" ]; then
        # Check if already instrumented
        if grep -q "instrument_command" "$cmd_file"; then
            echo "✅ $cmd - already instrumented"
        else
            echo "📝 $cmd - needs instrumentation"
            forge_file="$FORGE_DIR/command-instrumentation/commands/${cmd}.forge.yaml"
            
            if [ -f "$forge_file" ]; then
                echo "   Found forge template: $forge_file"
            else
                echo "   ⚠️  No forge template yet, needs creation"
            fi
        fi
    else
        echo "❌ $cmd - command file not found!"
    fi
done

echo ""

# Phase 3: Special Cases
echo "🔧 Phase 3: Special Cases"
echo "------------------------"

# Check for direct subprocess usage
echo "Checking for direct subprocess calls..."

for file in "$PROJECT_ROOT/src/uvmgr/commands/tests.py" "$PROJECT_ROOT/src/uvmgr/commands/lint.py"; do
    if [ -f "$file" ]; then
        if grep -q "subprocess.run" "$file"; then
            echo "⚠️  $(basename $file) - uses direct subprocess calls, needs fixing"
        else
            echo "✅ $(basename $file) - subprocess calls OK"
        fi
    fi
done

echo ""

# Phase 4: Summary
echo "📊 Summary"
echo "----------"

# Count instrumented files
instrumented_count=$(grep -l "instrument_command" "$PROJECT_ROOT"/src/uvmgr/commands/*.py 2>/dev/null | wc -l || echo 0)
total_commands=$(ls "$PROJECT_ROOT"/src/uvmgr/commands/*.py 2>/dev/null | wc -l || echo 0)

echo "Instrumented commands: $instrumented_count / $total_commands"
echo "Coverage: $(( instrumented_count * 100 / total_commands ))%"

echo ""
echo "🚀 Next Steps:"
echo "1. Review the forge templates in weaver-forge/"
echo "2. Run: weaver-forge apply <template.forge.yaml>"
echo "3. Test with: OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 uvmgr <command>"
echo "4. Validate with: python scripts/validate-coverage.py"

# Make executable
chmod +x "$0"