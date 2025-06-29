# uvmgr v2: Weaver Forge Configuration

This directory contains the Weaver Forge configuration for scaffolding **uvmgr v2** - a modular, observability-first Python package manager with **complete Weaver ecosystem integration**.

## 🎯 Overview

The Weaver Forge configuration converts the current uvmgr command structure into a declarative, scaffolded system that:

- **Maintains 3-layer architecture** (CLI → Operations → Runtime)
- **Ensures 100% telemetry coverage** with Weaver semantic conventions
- **Enables safe regeneration** of CLI wrappers
- **Preserves business logic** in operations layer
- **Provides enterprise-grade observability**
- **🆕 Complete Weaver ecosystem abstraction** - users never manually call `weaver` or `weaver forge`

## 🚫 **No Manual Weaver Calls**

**Key Goal**: Users should **never** need to manually call:
- ❌ `weaver registry check`
- ❌ `weaver forge generate`
- ❌ `weaver registry resolve`
- ❌ `weaver --help`

**Instead, users call**:
- ✅ `uvmgr otel status` (wraps weaver registry check)
- ✅ `uvmgr forge generate` (wraps weaver forge generate)
- ✅ `uvmgr otel registry` (wraps weaver registry commands)
- ✅ `uvmgr weaver status` (shows Weaver ecosystem status)

## 📁 Files

- **`weaver-forge-uvmgr-v2.yaml`** - Main Weaver Forge configuration
- **`uvmgr-semantic-conventions.yaml`** - Custom semantic conventions for uvmgr
- **`README-uvmgr-v2-weaver-forge.md`** - This documentation

## 🏗️ Architecture

### Current Structure → Weaver Forge Structure

```
Current uvmgr v1:
src/uvmgr/
├── commands/           # Mixed CLI + business logic
│   ├── deps.py        # 339 lines (CLI + ops mixed)
│   ├── tests.py       # 884 lines (CLI + ops mixed)
│   └── ...
├── ops/               # Some operations
└── runtime/           # Runtime utilities

Weaver Forge uvmgr v2:
src/uvmgr/
├── commands/          # Pure CLI layer (regenerated)
│   ├── deps/
│   │   ├── __init__.py
│   │   ├── add.py     # CLI wrapper only
│   │   ├── remove.py  # CLI wrapper only
│   │   └── ...
│   ├── otel/          # Complete Weaver wrapper
│   │   ├── status.py  # Wraps weaver registry check
│   │   ├── coverage.py # Wraps weaver registry validate
│   │   ├── weaver.py  # Wraps weaver registry resolve
│   │   └── registry.py # Wraps all weaver registry commands
│   ├── forge/         # Complete Weaver Forge wrapper
│   │   ├── generate.py # Wraps weaver forge generate
│   │   ├── validate.py # Wraps weaver forge validate
│   │   ├── scaffold.py # Wraps weaver forge scaffold
│   │   └── registry.py # Wraps weaver forge registry
│   └── weaver/        # Weaver ecosystem management
│       ├── install.py # Install Weaver tools
│       ├── update.py  # Update Weaver tools
│       ├── status.py  # Show Weaver status
│       └── config.py  # Manage Weaver config
├── operations/        # Business logic (preserved)
│   ├── deps/
│   │   ├── __init__.py
│   │   ├── add.py     # Pure business logic
│   │   └── ...
│   ├── otel/          # Weaver integration logic
│   │   ├── status.py  # Calls weaver registry check
│   │   ├── coverage.py # Calls weaver registry validate
│   │   └── ...
│   ├── forge/         # Weaver Forge integration logic
│   │   ├── generate.py # Calls weaver forge generate
│   │   └── ...
│   └── weaver/        # Weaver ecosystem management logic
│       ├── install.py # Manages Weaver installation
│       └── ...
└── runtime/           # Runtime utilities (preserved)
```

## 🚀 Usage

### 1. Generate uvmgr v2 Structure

```bash
# Using Weaver Forge to scaffold the new structure
uvmgr forge generate \
  --template cli-init \
  --output ./uvmgr-v2
```

### 2. Generate Command Groups

```bash
# Generate each command group
for group in deps tests build lint otel ai docs worktree security forge weaver; do
  uvmgr forge generate \
    --template cli-group \
    --output ./uvmgr-v2 \
    -D group=$group
done
```

### 3. Generate Individual Commands

```bash
# Example: Generate deps commands
uvmgr forge generate \
  --template cli-command \
  --output ./uvmgr-v2 \
  -D group=deps \
  -D command=add

uvmgr forge generate \
  --template cli-command \
  --output ./uvmgr-v2 \
  -D group=deps \
  -D command=remove
```

## 📊 Command Groups

The configuration defines **11 command groups** with **58 total commands**:

| Group | Commands | Description | Weaver Integration |
|-------|----------|-------------|-------------------|
| **deps** | 5 | Dependency management (add, remove, upgrade, list, lock) | - |
| **tests** | 4 | Testing and coverage (run, coverage, discover, generate) | - |
| **build** | 2 | Package building (build, clean) | - |
| **lint** | 1 | Code quality (run) | - |
| **otel** | 4 | OpenTelemetry (status, coverage, weaver, registry) | ✅ Complete Weaver wrapper |
| **ai** | 2 | AI assistance (analyze, suggest) | - |
| **docs** | 2 | Documentation (generate, serve) | - |
| **worktree** | 3 | Git worktrees (create, list, remove) | - |
| **security** | 2 | Security scanning (scan, audit) | - |
| **forge** | 4 | Weaver Forge (generate, validate, scaffold, registry) | ✅ Complete Weaver Forge wrapper |
| **weaver** | 4 | Weaver ecosystem (install, update, status, config) | ✅ Complete Weaver ecosystem management |

## 🔧 Semantic Conventions

The configuration includes comprehensive semantic conventions:

### Core Attributes
- `uvmgr.operation` - Operation type (add, remove, run, build, etc.)
- `uvmgr.command_group` - Command group (deps, tests, build, etc.)
- `uvmgr.subcommand` - Specific subcommand

### Domain-Specific Attributes
- **Package Management**: `uvmgr.package.*` (count, names, dev_dependency)
- **Testing**: `uvmgr.test.*` (framework, parallel, coverage, types)
- **Build**: `uvmgr.build.*` (type, operation)
- **Linting**: `uvmgr.lint.*` (tools, auto_fix)
- **OpenTelemetry**: `uvmgr.otel.*` (coverage.threshold, coverage.detailed, registry.action)
- **Weaver**: `uvmgr.weaver.*` (validate, test_semconv)
- **🆕 Weaver Ecosystem**: `uvmgr.weaver_ecosystem.*` (version, components, config.action)
- **AI**: `uvmgr.ai.*` (model, target)
- **Documentation**: `uvmgr.docs.*` (format, ai_enhance, port)
- **Worktree**: `uvmgr.worktree.*` (branch, path, isolated)
- **Security**: `uvmgr.security.*` (severity, auto_fix)
- **Forge**: `uvmgr.forge.*` (template, output, project_type, project_name, registry.action)

## 🎯 Key Benefits

### 1. **100% Telemetry Coverage**
- Every command automatically instrumented
- Weaver semantic convention compliance
- Structured observability data

### 2. **Safe Regeneration**
- CLI layer can be regenerated without losing business logic
- Operations layer preserved during regeneration
- Deterministic output structure

### 3. **Three-Layer Architecture**
- **CLI Layer**: Pure command-line interface (regenerated)
- **Operations Layer**: Business logic (preserved)
- **Runtime Layer**: Utilities and core functionality (preserved)

### 4. **Enterprise Observability**
- OpenTelemetry integration out-of-the-box
- Weaver semantic convention compliance
- Comprehensive metrics and tracing

### 5. **Modular Design**
- One command per file
- Clear separation of concerns
- Easy to extend and maintain

### 6. **🆕 Complete Weaver Abstraction**
- **No manual weaver calls** - everything wrapped in uvmgr
- **Unified interface** - single CLI for all Weaver functionality
- **Automatic management** - Weaver ecosystem self-managing
- **Simplified UX** - users don't need to learn weaver/forge commands

## 🔄 Migration Strategy

### Phase 1: Generate New Structure
```bash
# Generate the new v2 structure
uvmgr forge generate --template cli-init --output ./uvmgr-v2
```

### Phase 2: Migrate Business Logic
```bash
# Extract business logic from current commands to operations
# This is a manual process to preserve existing functionality
```

### Phase 3: Validate and Test
```bash
# Run telemetry coverage validation
uvmgr otel coverage --threshold 100

# Run Weaver validation
uvmgr otel weaver --validate --test-semconv

# Check Weaver ecosystem status
uvmgr weaver status
```

### Phase 4: Deploy
```bash
# Replace current structure with new v2 structure
# All existing functionality preserved with improved architecture
```

## 🧪 Validation Rules

The configuration includes strict validation rules:

- **Telemetry Coverage**: 100% function instrumentation required
- **Weaver Compatibility**: 100% semantic convention usage required
- **Three-Layer Architecture**: Layer separation enforced
- **Generation Rules**: Operations preserved, CLI regenerated
- **🆕 Weaver Abstraction**: No manual weaver calls allowed

## 📈 Metrics and Observability

With this configuration, uvmgr v2 will provide:

- **Structured telemetry** for all operations
- **Weaver semantic convention compliance**
- **Comprehensive metrics collection**
- **Distributed tracing support**
- **Enterprise-grade observability**
- **🆕 Weaver ecosystem monitoring**

## 🔗 Integration

### OpenTelemetry Weaver
- Semantic convention validation
- Code generation with telemetry
- Policy enforcement
- **🆕 Complete registry management**

### Weaver Forge
- Template-driven code generation
- Declarative configuration
- Safe regeneration workflows
- **🆕 Complete project scaffolding**

### Weaver Ecosystem Management
- **🆕 Automatic installation and updates**
- **🆕 Configuration management**
- **🆕 Status monitoring**
- **🆕 Component management**

### Enterprise Observability
- Jaeger/Zipkin integration
- Prometheus metrics
- Grafana dashboards
- ELK stack support

## 🚀 Next Steps

1. **Review Configuration**: Validate the Weaver Forge configuration
2. **Generate Structure**: Use Weaver Forge to scaffold uvmgr v2
3. **Migrate Logic**: Extract business logic to operations layer
4. **Validate Telemetry**: Ensure 100% coverage and Weaver compliance
5. **Deploy**: Replace current structure with improved v2 architecture
6. **🆕 Test Weaver Abstraction**: Verify no manual weaver calls needed

## 🎯 **User Experience Transformation**

### Before (Manual Weaver Calls)
```bash
# Users had to learn and manually call weaver commands
weaver registry check
weaver registry resolve --output-dir /tmp/resolved
weaver forge generate --config my-config.yaml
weaver --help
```

### After (Complete uvmgr Abstraction)
```bash
# Users only need to know uvmgr commands
uvmgr otel status
uvmgr otel registry --action resolve --output /tmp/resolved
uvmgr forge generate --template my-template --config my-config.yaml
uvmgr weaver status
```

This configuration provides a solid foundation for uvmgr v2 with enterprise-grade observability, maintainable architecture, and **complete Weaver ecosystem abstraction**. 