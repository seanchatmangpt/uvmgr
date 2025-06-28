# Weaver Command Suite

The `uvmgr weaver` command suite provides comprehensive tools for managing OpenTelemetry semantic conventions.

## Quick Start

```bash
# Install Weaver
uvmgr weaver install

# Check version
uvmgr weaver version

# Initialize a new registry
uvmgr weaver init --name myapp

# Validate conventions
uvmgr weaver check

# Generate Python code
uvmgr weaver generate python

# Show statistics
uvmgr weaver stats
```

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `install` | Install/update Weaver binary | `uvmgr weaver install --version latest` |
| `check` | Validate registry | `uvmgr weaver check --future` |
| `generate` | Generate code from conventions | `uvmgr weaver generate python` |
| `resolve` | Resolve references and inheritance | `uvmgr weaver resolve --format json` |
| `search` | Search for conventions | `uvmgr weaver search "package.*"` |
| `stats` | Show registry statistics | `uvmgr weaver stats` |
| `diff` | Compare registries | `uvmgr weaver diff old/ new/` |
| `init` | Initialize new registry | `uvmgr weaver init --name myapp` |
| `docs` | Generate documentation | `uvmgr weaver docs --format markdown` |
| `version` | Show version info | `uvmgr weaver version` |

## Features

### 1. Cross-Platform Installation
- Automatically detects platform (macOS, Linux, Windows)
- Downloads appropriate binary for your architecture
- Supports ARM64 and x86_64

### 2. Registry Management
- Initialize new registries from templates
- Validate against OpenTelemetry standards
- Compare different registry versions

### 3. Code Generation
- Python constants with type hints
- Markdown documentation
- Extensible template system

### 4. Search and Discovery
- Regex-based searching
- Type filtering (attributes, metrics, spans)
- Cross-registry searches

### 5. Quality Assurance
- Comprehensive validation rules
- Policy enforcement with Rego
- Bulk validation for CI/CD

## Examples

### Creating a Custom Registry

```bash
# Initialize
uvmgr weaver init --name ecommerce --path ./telemetry

# Edit conventions
nano telemetry/registry/models/common.yaml

# Validate
uvmgr weaver check --registry ./telemetry/registry

# Generate code
uvmgr weaver generate python --registry ./telemetry/registry
```

### Continuous Integration

```bash
#!/bin/bash
# CI validation script

set -e

echo "Validating semantic conventions..."
uvmgr weaver check --future --policy security.rego

echo "Generating code..."
uvmgr weaver generate python

echo "Running tests..."
pytest tests/test_semconv.py

echo "✓ All checks passed"
```

### Advanced Usage

```bash
# Compare two versions
uvmgr weaver diff v1.0/ v2.0/ --output changes.json

# Search for security-related attributes
uvmgr weaver search "auth|token|key" --type attribute

# Generate docs with custom template
uvmgr weaver docs --format markdown --output ./docs/

# Bulk validate multiple registries
find . -name "registry_manifest.yaml" -exec dirname {} \; | \
  xargs -I {} uvmgr weaver check --registry {}
```

## Integration Points

The Weaver command suite integrates with:

1. **uvmgr CLI**: All commands follow uvmgr patterns
2. **OTEL Commands**: Works with `uvmgr otel` suite
3. **CI/CD**: Exit codes for automation
4. **Code Generation**: Outputs to uvmgr source tree

## Best Practices

1. **Always validate before generating**
2. **Use semantic versioning for registries**
3. **Document all attributes with notes**
4. **Test generated code in CI**
5. **Use policies for consistency**

## Troubleshooting

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| Installation fails | Check internet connection, try `--force` |
| Validation errors | Fix YAML syntax, add required fields |
| Generation fails | Ensure registry is valid first |
| Search returns nothing | Check regex syntax, try broader terms |

## See Also

- [Weaver Documentation](docs/weaver-command-suite.md)
- [OTEL Integration](docs/otel-integration.md)
- [Semantic Conventions](weaver-forge/registry/)