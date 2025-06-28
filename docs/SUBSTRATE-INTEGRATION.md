# Using Substrate Projects with uvmgr OTEL Validation

## Overview

[Substrate](https://github.com/superlinear-ai/substrate) is a modern Python project scaffolding template that creates standardized, production-ready Python projects. This document explains how to use uvmgr's SpiffWorkflow OTEL validation system to validate and monitor Substrate-based projects.

Substrate provides an excellent test case for uvmgr's external project validation because:
- It uses `uv` for dependency management (same as uvmgr)
- It follows modern Python best practices
- It includes comprehensive testing infrastructure
- It has a standardized project structure

## Quick Start

### 1. Create a Substrate Project

```bash
# Create a new Substrate-based project
uvx copier copy gh:superlinear-ai/substrate my-substrate-project

# Navigate to the project
cd my-substrate-project

# Set up the development environment
make install
```

### 2. Validate with uvmgr

```bash
# Validate the Substrate project with uvmgr's OTEL system
uvmgr spiff-otel external-validate ./my-substrate-project --mode 8020

# Run comprehensive validation
uvmgr spiff-otel external-validate ./my-substrate-project --mode comprehensive --save
```

### 3. Batch Validation for Multiple Substrate Projects

```bash
# Discover all Substrate projects in your workspace
uvmgr spiff-otel discover-projects --path ~/dev --details

# Run 80/20 validation across all discovered projects
uvmgr spiff-otel 8020-external --path ~/dev --type library --save
```

## Integration Architecture

### How uvmgr Validates Substrate Projects

1. **Project Discovery**
   - Detects `pyproject.toml` with Substrate markers
   - Identifies `uv` as the package manager
   - Recognizes the standardized directory structure

2. **OTEL Instrumentation Analysis**
   - Validates project structure compatibility
   - Checks test framework integration (pytest)
   - Analyzes dependency management setup

3. **SpiffWorkflow Orchestration**
   - Creates BPMN workflows for validation
   - Executes test validation sequences
   - Monitors telemetry generation

## Substrate-Specific Features

### 1. Package Manager Compatibility

Substrate uses `uv` for dependency management, which aligns perfectly with uvmgr:

```python
# uvmgr automatically detects uv-based projects
if (project_path / "uv.lock").exists():
    package_manager = "uv"
```

### 2. Standardized Project Structure

Substrate projects follow a consistent structure that uvmgr can reliably analyze:

```
my-substrate-project/
├── pyproject.toml      # Project metadata (detected by uvmgr)
├── uv.lock            # Lock file (uv compatibility)
├── src/               # Source code
│   └── my_package/
├── tests/             # Test suite (pytest)
├── .github/           # CI/CD workflows
└── Makefile          # Development tasks
```

### 3. Testing Infrastructure

Substrate includes comprehensive testing setup that uvmgr validates:

```bash
# uvmgr validates test framework availability
uvmgr spiff-otel external-validate ./my-substrate-project \
  --mode comprehensive \
  --timeout 300
```

## Validation Workflow

### 1. Basic Validation (80/20 Mode)

The 80/20 mode focuses on critical validation paths:

```yaml
# Generated BPMN workflow for Substrate validation
- Check Python version compatibility
- Verify uv package manager
- Validate project structure
- Test framework detection (pytest)
- Basic OTEL instrumentation check
```

### 2. Comprehensive Validation

Full validation includes:

```yaml
# Extended validation workflow
- All basic validation steps
- Dependency resolution check
- Test suite execution
- Coverage analysis
- Linting and formatting validation
- CI/CD workflow analysis
```

### 3. Custom Validation

Create custom validation for Substrate projects:

```bash
# Create custom BPMN workflow
uvmgr spiff-otel create-workflow substrate-validation.bpmn \
  --test "make test" \
  --test "make lint" \
  --test "make coverage"

# Execute custom workflow
uvmgr spiff-otel run-workflow substrate-validation.bpmn \
  --project ./my-substrate-project
```

## OTEL Integration Points

### 1. Development Workflow Instrumentation

Add OTEL instrumentation to Substrate's Makefile targets:

```makefile
# Enhanced Makefile with OTEL tracking
test:
	@uvmgr otel validate spans
	@$(UV) run pytest
	@uvmgr otel validate metrics

lint:
	@uvmgr otel validate --pre-check
	@$(UV) run ruff check .
	@uvmgr otel validate --post-check
```

### 2. CI/CD Integration

Integrate uvmgr validation into Substrate's GitHub Actions:

```yaml
# .github/workflows/ci.yml enhancement
- name: Validate OTEL Integration
  run: |
    pip install uvmgr
    uvmgr spiff-otel external-validate . --mode 8020
    uvmgr otel export --format json > otel-validation.json
```

### 3. Development Environment

Add uvmgr to Substrate's development dependencies:

```toml
# pyproject.toml
[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "coverage[toml]>=7.4.1",
    "uvmgr>=0.1.0",  # Add uvmgr for OTEL validation
]
```

## Best Practices

### 1. Regular Validation

Set up automated validation:

```bash
# Create validation script
cat > validate-otel.sh << 'EOF'
#!/bin/bash
uvmgr spiff-otel external-validate . --mode 8020
if [ $? -eq 0 ]; then
    echo "✅ OTEL validation passed"
else
    echo "❌ OTEL validation failed"
    exit 1
fi
EOF

chmod +x validate-otel.sh
```

### 2. Batch Processing Multiple Projects

For organizations with multiple Substrate projects:

```bash
# Discover all Substrate projects
uvmgr spiff-otel discover-projects \
  --path ~/projects \
  --type library \
  --details > substrate-projects.txt

# Batch validate
uvmgr spiff-otel batch-validate \
  --auto-discover \
  --mode comprehensive \
  --workers 4 \
  --save
```

### 3. Custom Telemetry

Add project-specific telemetry:

```python
# src/my_package/telemetry.py
from uvmgr.core.telemetry import span, metric_counter

@span("substrate.operation")
def critical_operation():
    metric_counter("substrate.operations.executed")(1)
    # Your code here
```

## Troubleshooting

### Common Issues

1. **Package Manager Detection**
   ```bash
   # Ensure uv.lock exists
   uv lock
   ```

2. **Test Framework Issues**
   ```bash
   # Verify pytest is available
   uv run pytest --version
   ```

3. **OTEL Validation Failures**
   ```bash
   # Run with verbose output
   uvmgr spiff-otel external-validate . --mode 8020 --verbose
   ```

## Example Output

Successful Substrate project validation:

```
🔍 External Project OTEL Validation
📁 Project: my-substrate-project
🎯 Mode: 8020
⏱️ Timeout: 600s

╭──────────────────── Project Information ────────────────────╮
│ Project: my-substrate-project                               │
│ Path: /Users/dev/my-substrate-project                      │
│ Type: library                                               │
│ Package Manager: uv                                         │
│ Has Tests: Yes                                              │
│ Test Framework: pytest                                      │
│ Has pyproject.toml: Yes                                     │
╰─────────────────────────────────────────────────────────────╯

✅ Installation: SUCCESS (0.5s)
✅ OTEL Validation: PASSED
✅ uvmgr Integration: SUCCESS

Metrics Validated: 15
Spans Validated: 42
Performance: 2.3s total

✅ External Project OTEL Validation PASSED
✓ uvmgr successfully integrated with my-substrate-project
```

## Advanced Integration

### 1. Continuous Monitoring

Set up continuous OTEL monitoring for Substrate projects:

```python
# monitoring/substrate_monitor.py
from pathlib import Path
from uvmgr.ops.external_project_spiff import run_8020_external_project_validation

def monitor_substrate_projects():
    """Monitor all Substrate projects in workspace."""
    results = run_8020_external_project_validation(
        search_paths=[Path.home() / "projects"],
        project_filters={"project_type": "library"}
    )
    
    if results["success"]:
        print(f"✅ All {results['successful_projects']} Substrate projects validated")
    else:
        print(f"❌ {results['failed_projects']} projects failed validation")
```

### 2. Custom Validation Workflows

Create Substrate-specific validation workflows:

```xml
<!-- substrate-validation.bpmn -->
<bpmn:process id="substrate_validation">
  <bpmn:startEvent id="start" name="Start Substrate Validation"/>
  
  <bpmn:serviceTask id="check_uv" name="Validate uv Setup">
    <bpmn:script>uv --version</bpmn:script>
  </bpmn:serviceTask>
  
  <bpmn:serviceTask id="run_tests" name="Execute Test Suite">
    <bpmn:script>make test</bpmn:script>
  </bpmn:serviceTask>
  
  <bpmn:serviceTask id="check_coverage" name="Validate Coverage">
    <bpmn:script>make coverage</bpmn:script>
  </bpmn:serviceTask>
  
  <bpmn:endEvent id="end" name="Validation Complete"/>
</bpmn:process>
```

### 3. Integration with Substrate's Copier Updates

Validate projects after Copier updates:

```bash
# Update Substrate template
uvx copier update --exclude src/ --exclude tests/

# Immediately validate changes
uvmgr spiff-otel external-validate . --mode comprehensive

# Check for breaking changes
uvmgr otel workflow-validate --mode 8020 --save
```

## Conclusion

Substrate projects are ideal candidates for uvmgr's external project validation because they:
- Use modern Python tooling (uv, ruff, pytest)
- Follow standardized project structures
- Include comprehensive testing infrastructure
- Support continuous integration workflows

By integrating uvmgr's SpiffWorkflow OTEL validation with Substrate projects, teams can:
- Ensure consistent telemetry across all projects
- Validate project health automatically
- Monitor external dependencies effectively
- Maintain high code quality standards

The combination of Substrate's standardized approach and uvmgr's validation capabilities creates a powerful foundation for managing Python projects at scale.