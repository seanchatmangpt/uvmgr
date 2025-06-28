# Weaver Command Suite Documentation

The `uvmgr weaver` command suite provides comprehensive tools for managing OpenTelemetry semantic conventions using the Weaver tool.

## Overview

Weaver is OpenTelemetry's official tool for:
- Validating semantic convention definitions
- Generating code from conventions
- Managing convention registries
- Ensuring consistency across telemetry implementations

## Installation

Before using any Weaver commands, install it:

```bash
uvmgr weaver install
```

Options:
- `--version VERSION`: Install specific version (default: latest)
- `--force`: Force reinstall even if already installed

## Commands

### `uvmgr weaver check`

Validate semantic convention registry for correctness.

```bash
uvmgr weaver check
```

Options:
- `--registry PATH`: Registry path (default: weaver-forge/registry)
- `--future`: Enable latest validation rules (recommended)
- `--policy PATH`: Apply custom Rego policy file

Example:
```bash
uvmgr weaver check --future --policy security-policy.rego
```

### `uvmgr weaver generate`

Generate code from semantic conventions.

```bash
uvmgr weaver generate python
```

Supported templates:
- `python`: Generate Python constants
- `markdown`: Generate documentation
- `go`: Generate Go constants (planned)
- `java`: Generate Java constants (planned)

Options:
- `--output PATH`: Output directory
- `--registry PATH`: Registry path
- `--config PATH`: Weaver config file

Example:
```bash
uvmgr weaver generate python --output src/telemetry/
uvmgr weaver generate markdown --output docs/semconv/
```

### `uvmgr weaver resolve`

Resolve all references and inheritance in the registry.

```bash
uvmgr weaver resolve
```

Options:
- `--registry PATH`: Registry path
- `--output PATH`: Save resolved output
- `--format FORMAT`: Output format (json, yaml)

Example:
```bash
uvmgr weaver resolve --format json --output resolved.json
```

### `uvmgr weaver search`

Search for attributes, metrics, or conventions.

```bash
uvmgr weaver search "package"
```

Options:
- `--registry PATH`: Registry path
- `--type TYPE`: Filter by type (attribute, metric, span)

Examples:
```bash
uvmgr weaver search "cli\\..*" --type attribute
uvmgr weaver search "error" --type metric
```

### `uvmgr weaver stats`

Display registry statistics.

```bash
uvmgr weaver stats
```

Shows:
- Number of attribute groups
- Total attributes defined
- Metrics count
- Span definitions
- Event definitions

### `uvmgr weaver diff`

Compare two semantic convention registries.

```bash
uvmgr weaver diff registry1/ registry2/
```

Options:
- `--output PATH`: Save diff to file

Example:
```bash
uvmgr weaver diff old-registry/ new-registry/ --output changes.json
```

### `uvmgr weaver init`

Initialize a new semantic convention registry.

```bash
uvmgr weaver init
```

Options:
- `--name NAME`: Registry name (default: myproject)
- `--path PATH`: Where to create registry
- `--force`: Overwrite existing registry

Example:
```bash
uvmgr weaver init --name myapp --path ./telemetry/
```

Creates:
```
telemetry/registry/
├── registry_manifest.yaml
├── models/
│   └── common.yaml
└── .gitignore
```

### `uvmgr weaver docs`

Generate comprehensive documentation from conventions.

```bash
uvmgr weaver docs
```

Options:
- `--registry PATH`: Registry path
- `--output PATH`: Documentation output directory
- `--format FORMAT`: Documentation format (markdown, html)

Example:
```bash
uvmgr weaver docs --output ./docs/telemetry/ --format markdown
```

### `uvmgr weaver version`

Display Weaver version and configuration.

```bash
uvmgr weaver version
```

## Registry Structure

A Weaver registry follows this structure:

```
registry/
├── registry_manifest.yaml    # Registry metadata
├── models/                   # Convention definitions
│   ├── common.yaml          # Common attributes
│   ├── cli.yaml             # CLI-specific conventions
│   └── package.yaml         # Package management conventions
└── templates/               # Custom generation templates (optional)
    ├── python.jinja2
    └── markdown.jinja2
```

### Registry Manifest

```yaml
name: "uvmgr"
description: "Semantic conventions for uvmgr"
version: "1.0.0"
semconv_version: "1.26.0"
schema_base_url: "https://opentelemetry.io/schemas"
models:
  - path: models/common.yaml
    description: "Common attributes"
```

### Convention Definition

```yaml
groups:
  - id: package
    type: attribute_group
    brief: 'Package management attributes'
    attributes:
      - id: name
        type: string
        brief: 'Package name'
        note: 'The name as it appears in the registry'
        examples: ['pytest', 'django']
        requirement_level: required
        stability: stable
```

## Templates

Weaver uses Jinja2 templates for code generation. Custom templates can be added to the `templates/` directory.

### Available Filters

- `pascal_case`: Convert to PascalCase
- `slugify`: Convert to URL-friendly slug
- `format_type`: Format attribute types
- `format_requirement`: Format requirement levels
- `code_format`: Format code examples

### Template Variables

- `registry_name`: Name of the registry
- `registry_version`: Registry version
- `groups`: Attribute groups
- `metrics`: Metric definitions
- `timestamp`: Generation timestamp

## Configuration

The `weaver.toml` file configures generation behavior:

```toml
[general]
registry_path = "registry"
output_path = "generated"

[python]
output_file = "../src/uvmgr/core/semconv.py"
class_suffix = "Attributes"

[markdown]
output_dir = "docs"
include_toc = true
```

## Best Practices

1. **Always validate before generating**:
   ```bash
   uvmgr weaver check --future && uvmgr weaver generate python
   ```

2. **Use semantic versioning** for your registry

3. **Document attributes thoroughly** with notes and examples

4. **Set appropriate stability levels**:
   - `stable`: Won't change
   - `experimental`: May change
   - `deprecated`: Will be removed

5. **Define requirement levels clearly**:
   - `required`: Must be present
   - `recommended`: Should be present
   - `optional`: May be present
   - `conditionally_required`: Required in specific cases

## Integration with uvmgr

The generated semantic conventions integrate with uvmgr's instrumentation:

```python
from uvmgr.core.semconv import PackageAttributes
from uvmgr.core.instrumentation import add_span_attributes

# Use generated constants
add_span_attributes(**{
    PackageAttributes.NAME: "pytest",
    PackageAttributes.VERSION: "7.4.0",
    PackageAttributes.OPERATION: "add"
})
```

## Troubleshooting

### Weaver not found
```bash
uvmgr weaver install
```

### Validation errors
```bash
uvmgr weaver check --future
```

### Generation fails
Check template syntax:
```bash
uvmgr weaver resolve --format json
```

### Platform-specific issues
Weaver supports:
- macOS (x86_64, ARM64)
- Linux (x86_64, ARM64)
- Windows (x86_64)

## Resources

- [OpenTelemetry Weaver](https://github.com/open-telemetry/weaver)
- [Semantic Conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/)
- [Weaver Documentation](https://github.com/open-telemetry/weaver/tree/main/docs)