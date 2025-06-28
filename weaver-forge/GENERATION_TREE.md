# Weaver Forge Generation Tree for uvmgr

## 🌳 Complete Generation Structure

```
weaver-forge/
├── 📁 core-infrastructure/
│   ├── telemetry-enhanced.forge.yaml        # Enhanced telemetry core module
│   ├── instrumentation.forge.yaml           # Command/operation decorators
│   ├── metrics-system.forge.yaml            # Metrics classes and helpers
│   ├── semantic-conventions.forge.yaml      # OTEL semantic conventions
│   └── span-helpers.forge.yaml              # Span utilities and helpers
│
├── 📁 command-instrumentation/
│   ├── base-command.forge.yaml              # Base command instrumentation pattern
│   ├── commands/
│   │   ├── agent.forge.yaml                 # BPMN workflow commands
│   │   ├── ai.forge.yaml                    # AI/LLM commands
│   │   ├── ap_scheduler.forge.yaml          # Scheduler commands
│   │   ├── build.forge.yaml                 # Build/packaging commands
│   │   ├── cache.forge.yaml                 # Cache management commands
│   │   ├── deps.forge.yaml                  # Dependency commands (DONE)
│   │   ├── exec.forge.yaml                  # Script execution commands
│   │   ├── index.forge.yaml                 # Index management commands
│   │   ├── lint.forge.yaml                  # Linting commands (subprocess fix)
│   │   ├── project.forge.yaml               # Project scaffolding commands
│   │   ├── release.forge.yaml               # Release management commands
│   │   ├── remote.forge.yaml                # Remote execution commands
│   │   ├── serve.forge.yaml                 # MCP server commands
│   │   ├── shell.forge.yaml                 # REPL/shell commands
│   │   ├── tests.forge.yaml                 # Test runner commands (subprocess fix)
│   │   └── tool.forge.yaml                  # Tool management commands
│   └── command-aggregator.forge.yaml        # Aggregate all command instrumentations
│
├── 📁 operation-instrumentation/
│   ├── base-operation.forge.yaml            # Base operation pattern
│   ├── operations/
│   │   ├── agent.forge.yaml                 # Agent operations (missing)
│   │   ├── ai.forge.yaml                    # AI operations (partial)
│   │   ├── aps.forge.yaml                   # Scheduler operations (missing)
│   │   ├── build.forge.yaml                 # Build operations (partial)
│   │   ├── cache.forge.yaml                 # Cache operations (has spans)
│   │   ├── deps.forge.yaml                  # Dependency operations (has spans)
│   │   ├── exec.forge.yaml                  # Execution operations (partial)
│   │   ├── indexes.forge.yaml               # Index operations (has spans)
│   │   ├── mcp.forge.yaml                   # MCP operations (has spans)
│   │   ├── project.forge.yaml               # Project operations (partial)
│   │   ├── release.forge.yaml               # Release operations (partial)
│   │   ├── remote.forge.yaml                # Remote operations (missing)
│   │   ├── shell.forge.yaml                 # Shell operations (partial)
│   │   ├── tools.forge.yaml                 # Tool operations (has spans)
│   │   └── uv.forge.yaml                    # UV wrapper operations (partial)
│   └── operation-metrics.forge.yaml         # Metrics integration for operations
│
├── 📁 runtime-instrumentation/
│   ├── subprocess-wrapper.forge.yaml        # Instrumented subprocess calls
│   ├── runtime/
│   │   ├── agent_legacy.forge.yaml          # Legacy agent runtime (missing)
│   │   ├── agent/*.forge.yaml               # Agent subsystem (missing)
│   │   └── remote.forge.yaml                # Remote runtime (missing)
│   └── runtime-aggregator.forge.yaml        # Aggregate runtime instrumentations
│
├── 📁 metrics-implementation/
│   ├── metric-types/
│   │   ├── counters.forge.yaml              # Counter metric patterns
│   │   ├── histograms.forge.yaml            # Histogram metric patterns
│   │   └── gauges.forge.yaml                # Gauge metric patterns
│   ├── domain-metrics/
│   │   ├── cli-metrics.forge.yaml           # CLI command metrics
│   │   ├── package-metrics.forge.yaml       # Package management metrics
│   │   ├── build-metrics.forge.yaml         # Build operation metrics
│   │   ├── test-metrics.forge.yaml          # Test execution metrics
│   │   ├── ai-metrics.forge.yaml            # AI operation metrics
│   │   └── process-metrics.forge.yaml       # Process execution metrics
│   └── metrics-aggregator.forge.yaml        # Aggregate all metrics
│
├── 📁 semantic-conventions/
│   ├── base-conventions.forge.yaml          # Base OTEL conventions
│   ├── domain-conventions/
│   │   ├── cli-conventions.forge.yaml       # CLI-specific conventions
│   │   ├── package-conventions.forge.yaml   # Package management conventions
│   │   ├── build-conventions.forge.yaml     # Build operation conventions
│   │   ├── test-conventions.forge.yaml      # Test execution conventions
│   │   ├── ai-conventions.forge.yaml        # AI operation conventions
│   │   ├── mcp-conventions.forge.yaml       # MCP server conventions
│   │   └── process-conventions.forge.yaml   # Process execution conventions
│   └── convention-constants.forge.yaml      # Generate Python constants
│
├── 📁 testing-infrastructure/
│   ├── telemetry-test-utils.forge.yaml      # Test utilities for telemetry
│   ├── mock-telemetry.forge.yaml            # Mock telemetry for testing
│   ├── span-assertions.forge.yaml           # Span assertion helpers
│   ├── metric-assertions.forge.yaml         # Metric assertion helpers
│   └── coverage-validator.forge.yaml        # Telemetry coverage validation
│
├── 📁 configuration/
│   ├── otel-config.forge.yaml               # OTEL configuration
│   ├── sampling-config.forge.yaml           # Sampling strategies
│   ├── exporter-config.forge.yaml           # Exporter configurations
│   └── environment-vars.forge.yaml          # Environment variable setup
│
├── 📁 monitoring/
│   ├── grafana-dashboards/
│   │   ├── cli-dashboard.forge.yaml         # CLI command dashboard
│   │   ├── package-dashboard.forge.yaml     # Package operations dashboard
│   │   ├── build-dashboard.forge.yaml       # Build operations dashboard
│   │   ├── test-dashboard.forge.yaml        # Test execution dashboard
│   │   └── system-dashboard.forge.yaml      # System overview dashboard
│   ├── prometheus-rules/
│   │   ├── alert-rules.forge.yaml           # Alerting rules
│   │   └── recording-rules.forge.yaml       # Recording rules
│   └── jaeger-config.forge.yaml             # Jaeger UI configuration
│
├── 📁 scripts/
│   ├── generate-all.sh                      # Master generation script
│   ├── validate-coverage.py                 # Coverage validation script
│   ├── performance-test.py                  # Performance testing script
│   └── apply-instrumentation.py             # Apply generated code
│
└── 📁 templates/
    ├── command-decorator.j2                  # Jinja2 template for commands
    ├── operation-wrapper.j2                  # Jinja2 template for operations
    ├── metric-class.j2                       # Jinja2 template for metrics
    └── test-helper.j2                        # Jinja2 template for tests
```

## 🎯 Generation Priority Order

### Phase 1: Core Infrastructure (Critical)
1. `core-infrastructure/instrumentation.forge.yaml` ✅ (partially exists)
2. `core-infrastructure/telemetry-enhanced.forge.yaml`
3. `core-infrastructure/semantic-conventions.forge.yaml`
4. `core-infrastructure/metrics-system.forge.yaml`

### Phase 2: Command Layer (High Priority)
1. `command-instrumentation/base-command.forge.yaml`
2. `command-instrumentation/commands/*.forge.yaml` (except deps.yaml)
3. Special attention to:
   - `tests.forge.yaml` (fix subprocess)
   - `lint.forge.yaml` (fix subprocess)

### Phase 3: Operations Layer (Medium Priority)
1. Missing operations:
   - `operations/agent.forge.yaml`
   - `operations/aps.forge.yaml`
   - `operations/remote.forge.yaml`
2. Enhance partial implementations

### Phase 4: Metrics & Monitoring (Medium Priority)
1. `domain-metrics/*.forge.yaml`
2. `monitoring/grafana-dashboards/*.forge.yaml`

### Phase 5: Testing & Validation (Low Priority)
1. `testing-infrastructure/*.forge.yaml`
2. `scripts/validate-coverage.py`

## 📊 Current Status

### ✅ Already Implemented
- `deps.py` command instrumentation (manual)
- Basic telemetry core with `span()` and `metric_counter()`
- `record_exception()` helper

### 🔄 In Progress
- Command instrumentation pattern established

### ❌ Not Started
- 16/17 commands need instrumentation
- All metrics implementation
- Semantic convention constants
- Testing infrastructure
- Monitoring dashboards

## 🔧 Generation Commands

```bash
# Generate all core infrastructure
weaver-forge generate-batch core-infrastructure/

# Generate all command instrumentations
weaver-forge generate-batch command-instrumentation/commands/

# Generate specific command
weaver-forge generate command-instrumentation/commands/build.forge.yaml

# Apply all generated code
python scripts/apply-instrumentation.py --target ../src/

# Validate coverage
python scripts/validate-coverage.py --min-coverage 99.0
```

## 📝 Notes

1. **Subprocess Fixes**: `tests.py` and `lint.py` need special handling
2. **Metrics Integration**: Should be added alongside span instrumentation
3. **Semantic Conventions**: Must follow OTEL standards
4. **Performance**: Each generation should consider <1% overhead
5. **Backwards Compatibility**: Graceful degradation when OTEL not available