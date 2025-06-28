# Weaver Forge Complete Blueprint: 100% OTEL Coverage for uvmgr

## Executive Summary

This blueprint consolidates all Weaver Forge generation requirements to achieve 100% OpenTelemetry coverage in uvmgr. Current coverage is ~40% with critical gaps in command instrumentation, metrics usage, and semantic conventions.

## Current State vs Target State

### Current State (40% Coverage)
```
✅ Runtime Layer: 70% traced (subprocess calls)
⚠️  Operations Layer: 50% traced (using @timed decorator)
❌ Command Layer: 0% traced (17 modules uninstrumented)
❌ Metrics: Defined but unused
❌ Semantic Conventions: Not implemented
❌ Error Handling: Basic only
```

### Target State (100% Coverage)
```
✅ All Layers: 100% traced with proper hierarchy
✅ Metrics: Counters, histograms, gauges in active use
✅ Semantic Conventions: Full OTEL compliance
✅ Error Handling: Complete with exception recording
✅ Context Propagation: Distributed tracing support
✅ Performance: <1% overhead with sampling
```

## Generation Requirements

### 1. Command Instrumentation (17 files)

**Files Requiring Generation:**
```
src/uvmgr/commands/agent.py
src/uvmgr/commands/ai.py
src/uvmgr/commands/ap_scheduler.py
src/uvmgr/commands/build.py
src/uvmgr/commands/cache.py
src/uvmgr/commands/deps.py
src/uvmgr/commands/exec.py
src/uvmgr/commands/index.py
src/uvmgr/commands/lint.py
src/uvmgr/commands/project.py
src/uvmgr/commands/release.py
src/uvmgr/commands/remote.py
src/uvmgr/commands/serve.py
src/uvmgr/commands/shell.py
src/uvmgr/commands/tests.py
src/uvmgr/commands/tool.py
```

**Generation Pattern:**
```bash
weaver-forge generate command_telemetry \
  --input-file src/uvmgr/commands/${COMMAND}.py \
  --command-name ${COMMAND} \
  --output-mode inject
```

### 2. Direct Subprocess Fixes

**Critical Files:**
- `src/uvmgr/commands/tests.py` - Uses raw `subprocess.run()`
- `src/uvmgr/commands/lint.py` - Uses raw `subprocess.run()`

**Required Changes:**
- Replace with `run_logged()` from `core.process`
- Or wrap with span context

### 3. Operations Layer Gaps

**Files Missing Telemetry:**
- `src/uvmgr/ops/remote.py`
- `src/uvmgr/ops/aps.py`
- `src/uvmgr/ops/agent.py`

**Generation Pattern:**
```bash
weaver-forge generate operation_telemetry \
  --operation-type ${TYPE} \
  --operations-file src/uvmgr/ops/${TYPE}.py
```

### 4. Metrics Implementation

**Required Metrics:**
```yaml
metrics:
  - cli.command.calls (counter)
  - cli.command.errors (counter)
  - cli.command.duration (histogram)
  - package.operations (counter)
  - package.operation.duration (histogram)
  - build.artifacts (counter)
  - build.size (histogram)
  - build.duration (histogram)
  - test.runs (counter)
  - test.results (counter by status)
  - test.coverage (gauge)
  - process.executions (counter)
  - process.failures (counter)
```

### 5. Semantic Conventions

**Required Conventions:**
```yaml
conventions:
  cli:
    - cli.command (required)
    - cli.subcommand (conditional)
    - cli.args (optional)
    - cli.exit_code (required)
  package:
    - package.name (required)
    - package.version (recommended)
    - package.operation (required)
  build:
    - build.type (required)
    - build.size (recommended)
    - build.duration (recommended)
  test:
    - test.framework (required)
    - test.operation (required)
    - test.count (recommended)
  process:
    - process.command (required)
    - process.executable (recommended)
    - process.exit_code (required)
```

## Weaver Forge Templates

### Template 1: Command Decorator
```python
# weaver-forge/templates/command_decorator.py.j2
from functools import wraps
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes

def instrument_command(name: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = f"cli.command.{name or func.__name__}"
            
            with span(
                span_name,
                span_kind=trace.SpanKind.SERVER,
                attributes={
                    "cli.command": name or func.__name__,
                    "cli.module": "{{ module_name }}",
                    SpanAttributes.CODE_FUNCTION: func.__name__,
                }
            ) as current_span:
                metric_counter(f"cli.command.{name}.calls")
                try:
                    result = func(*args, **kwargs)
                    current_span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    record_exception(e, escaped=True)
                    metric_counter(f"cli.command.{name}.errors")
                    raise
        return wrapper
    return decorator
```

### Template 2: Metrics Class
```python
# weaver-forge/templates/metrics_class.py.j2
class {{ namespace.title() }}Metrics:
    def __init__(self):
        self.namespace = "{{ namespace }}"
        self._meter = metrics.get_meter(f"uvmgr.{self.namespace}")
        
    def record_operation(self, operation: str, result: OperationResult):
        attrs = {
            "operation": operation,
            "namespace": self.namespace,
            "success": str(result.success),
        }
        
        metric_counter(f"{self.namespace}.operations", 1, attrs)
        metric_histogram(f"{self.namespace}.duration", result.duration, attrs)
        
        if not result.success:
            metric_counter(f"{self.namespace}.errors", 1, attrs)
```

## Implementation Roadmap

### Phase 1: Foundation Enhancement (Day 1-2)
```bash
# 1. Upgrade telemetry core
cp weaver-forge/enhanced-telemetry-core.py src/uvmgr/core/telemetry.py

# 2. Add metrics module
cp weaver-forge/metrics-implementation.py src/uvmgr/core/metrics.py

# 3. Generate semantic conventions
weaver-forge generate semantic_conventions \
  --input weaver-forge/semantic-conventions.yaml \
  --output src/uvmgr/core/semconv.py
```

### Phase 2: Command Instrumentation (Day 3-5)
```bash
# Generate instrumentation for all commands
for cmd in agent ai ap_scheduler build cache deps exec index lint project release remote serve shell tests tool; do
  weaver-forge generate command_telemetry \
    --command-name $cmd \
    --input-file src/uvmgr/commands/$cmd.py \
    --output-mode inject
done
```

### Phase 3: Fix Direct Calls (Day 6)
```python
# Before (tests.py)
subprocess.run(["pytest"], check=True)

# After
from uvmgr.core.process import run_logged
with span("test.pytest.run"):
    run_logged(["pytest"])
```

### Phase 4: Metrics Integration (Day 7-8)
```python
# In each operation
from uvmgr.core.metrics import dependency_metrics

result = OperationResult(
    success=True,
    duration=time.time() - start,
    metadata={"package": package_name}
)
dependency_metrics.record_add(package_name, version, dev, result)
```

### Phase 5: Testing & Validation (Day 9-10)
```bash
# Run validation script
python weaver-forge/validate-telemetry-coverage.py

# Test with OTEL collector
docker run -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 uvmgr deps add pytest

# Verify traces in Jaeger
open http://localhost:16686
```

## Validation Checklist

### Coverage Validation
- [ ] All 17 command modules have `@instrument_command` decorators
- [ ] All subprocess calls use `run_logged()` or are wrapped in spans
- [ ] All operations record metrics
- [ ] Exception handling records to spans
- [ ] Semantic conventions used throughout

### Integration Testing
- [ ] Traces appear in Jaeger/Tempo
- [ ] Metrics appear in Prometheus
- [ ] Span hierarchy is correct
- [ ] Context propagation works
- [ ] Performance overhead <1%

### Automated Validation
```python
# Run coverage check
coverage = check_telemetry_coverage("src/uvmgr")
assert coverage["overall"] >= 99.0

# Run performance test
overhead = measure_telemetry_overhead()
assert overhead < 0.01  # 1%
```

## Generated Code Examples

### Example 1: Instrumented deps.py
```python
@deps_app.command()
@instrument_command("deps_add")
def add(
    packages: List[str] = typer.Argument(...),
    dev: bool = typer.Option(False, "--dev"),
):
    """Add package dependencies."""
    # Decorator handles span creation and metrics
    payload = deps_ops.add(packages, dev=dev)
    # ... rest of implementation
```

### Example 2: Instrumented Operation
```python
@timed
def add(pkgs: list[str], *, dev: bool = False) -> dict:
    with span("deps.add", pkgs=" ".join(pkgs), dev=dev) as s:
        s.set_attribute("package.count", len(pkgs))
        s.set_attribute("package.dev", dev)
        
        start = time.time()
        try:
            _rt.add(pkgs, dev=dev)
            result = OperationResult(True, time.time() - start)
            dependency_metrics.record_operation("add", result)
        except Exception as e:
            result = OperationResult(False, time.time() - start, error=e)
            dependency_metrics.record_operation("add", result)
            raise
            
    return {"added": pkgs, "dev": dev}
```

## Success Criteria

### Quantitative Metrics
- 100% function coverage with telemetry
- <1% performance overhead
- 0 uninstrumented subprocess calls
- All 5 metric types in use
- 100% semantic convention compliance

### Qualitative Metrics
- Complete observability of user workflows
- Clear span hierarchies
- Meaningful metric dashboards
- Actionable error tracking
- Easy troubleshooting

## Maintenance Guidelines

### Adding New Commands
1. Use `@instrument_command` decorator
2. Follow semantic conventions
3. Record relevant metrics
4. Handle exceptions properly
5. Test with OTEL collector

### Adding New Operations
1. Wrap with span context
2. Use operation-specific attributes
3. Record operation metrics
4. Follow naming conventions
5. Document span hierarchy

## Resources

- [OTEL Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [Semantic Conventions](https://opentelemetry.io/docs/reference/specification/trace/semantic_conventions/)
- [Weaver Tool](https://github.com/open-telemetry/weaver)
- [Jaeger UI](https://www.jaegertracing.io/docs/1.21/getting-started/)

## Conclusion

This blueprint provides a complete path to 100% OTEL coverage in uvmgr. By following the Weaver Forge generation patterns and implementation roadmap, uvmgr will have enterprise-grade observability with minimal performance impact.