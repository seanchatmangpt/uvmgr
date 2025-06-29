# OpenTelemetry Integration & Weaver Semantic Conventions

This document details the OpenTelemetry integration in the DoD automation system and how it implements Weaver semantic conventions for consistent observability.

## Table of Contents
- [Overview](#overview)
- [Weaver Semantic Conventions](#weaver-semantic-conventions)
- [Span Instrumentation](#span-instrumentation)
- [Attributes Schema](#attributes-schema)
- [Trace Context Propagation](#trace-context-propagation)
- [Metrics Collection](#metrics-collection)
- [Configuration](#configuration)
- [Monitoring Setup](#monitoring-setup)

## Overview

The DoD automation system is **observable by design**, with comprehensive OpenTelemetry instrumentation that provides:

- **Distributed Tracing**: Full request tracing across all DoD operations
- **Semantic Conventions**: Consistent naming and attributes following Weaver standards
- **Performance Monitoring**: Execution time, success rates, and resource utilization
- **Error Tracking**: Automatic exception capture and error correlation
- **Business Metrics**: DoD compliance scores, criteria success rates, automation efficiency

### Key Benefits

✅ **Operational Visibility**: Real-time insights into DoD automation performance  
✅ **Debugging Capability**: Trace-based debugging for complex automation workflows  
✅ **Performance Analysis**: Identify bottlenecks and optimization opportunities  
✅ **Compliance Monitoring**: Track DoD compliance trends over time  
✅ **Integration Health**: Monitor external tool integration status  

## Weaver Semantic Conventions

The DoD system follows [Weaver semantic conventions](https://github.com/open-telemetry/weaver) for consistent, interoperable observability data.

### Namespace Structure

```
dod.*                    # DoD-specific operations
├── dod.operation        # High-level operation type
├── dod.template         # Template name (standard, enterprise, ai-native)
├── dod.environment      # Target environment (development, staging, production)
├── dod.criteria.*       # Criteria-specific attributes
├── dod.execution.*      # Execution-related metrics
└── dod.result.*         # Result attributes

project.*                # Project-specific attributes
├── project.path         # Project directory path
├── project.name         # Project name
└── project.version      # Project version

automation.*             # Automation-specific attributes
├── automation.strategy  # Strategy used (80/20, comprehensive)
├── automation.version   # DoD system version
└── automation.mode      # Execution mode (autonomous, supervised, manual)
```

### Naming Conventions

#### Span Names
- **Format**: `{namespace}.{operation}` in snake_case
- **Examples**: `dod.create_exoskeleton`, `dod.execute_complete_automation`
- **Hierarchy**: Use consistent prefixes for related operations

#### Attribute Names
- **Format**: `{namespace}.{attribute}` in snake_case
- **Types**: Use appropriate types (string, int, float, bool)
- **Consistency**: Same concept = same attribute name across spans

## Span Instrumentation

### 1. Operations Layer Spans

All operations layer functions are instrumented with comprehensive spans:

```python
from opentelemetry import trace
from uvmgr.core.telemetry import span

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("dod.execute_complete_automation")
def execute_complete_automation(
    project_path: Path,
    environment: str = "development",
    criteria: Optional[List[str]] = None,
    auto_fix: bool = False,
    parallel: bool = True,
    ai_assist: bool = True
) -> Dict[str, Any]:
    """Execute complete DoD automation with full tracing."""
    
    span = trace.get_current_span()
    
    # Set initial operational attributes
    span.set_attributes({
        "dod.operation": "complete_automation",
        "dod.environment": environment,
        "dod.auto_fix": auto_fix,
        "dod.parallel": parallel,
        "dod.ai_assist": ai_assist,
        "dod.criteria_count": len(criteria or []),
        "project.path": str(project_path),
        "automation.strategy": "80/20"
    })
    
    try:
        start_time = time.time()
        
        # Execute automation workflow
        automation_result = execute_automation_workflow(
            project_path=project_path,
            criteria=criteria,
            environment=environment,
            auto_fix=auto_fix,
            parallel=parallel,
            ai_assist=ai_assist
        )
        
        # Calculate metrics
        success_rate = _calculate_weighted_success_rate(
            automation_result.get("criteria_results", {}),
            criteria
        )
        execution_time = time.time() - start_time
        
        # Set result attributes
        span.set_attributes({
            "dod.success_rate": success_rate,
            "dod.execution_time": execution_time,
            "dod.criteria_passed": len([
                c for c, r in automation_result.get("criteria_results", {}).items()
                if r.get("passed", False)
            ]),
            "dod.result.success": automation_result.get("success", False)
        })
        
        return automation_result
        
    except Exception as e:
        # Record exception with context
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        
        return {
            "success": False,
            "error": f"Automation execution failed: {str(e)}",
            "execution_time": time.time() - start_time
        }
```

### 2. Runtime Layer Spans

Runtime functions use the `@span` decorator for consistent instrumentation:

```python
from uvmgr.core.telemetry import span

@span("dod.runtime.execute_automation_workflow")
def execute_automation_workflow(
    project_path: Path,
    criteria: List[str],
    environment: str,
    auto_fix: bool,
    parallel: bool,
    ai_assist: bool
) -> Dict[str, Any]:
    """Execute automation workflow with runtime tracing."""
    
    current_span = trace.get_current_span()
    
    # Set runtime-specific attributes
    current_span.set_attributes({
        "dod.runtime.operation": "automation_workflow",
        "dod.runtime.criteria": json.dumps(criteria),
        "dod.runtime.parallel": parallel,
        "dod.runtime.auto_fix": auto_fix
    })
    
    try:
        criteria_results = {}
        
        if parallel:
            # Parallel execution with child spans
            criteria_results = _execute_criteria_parallel(criteria, current_span)
        else:
            # Sequential execution
            criteria_results = _execute_criteria_sequential(criteria, current_span)
        
        # Set success metrics
        total_criteria = len(criteria)
        passed_criteria = sum(1 for r in criteria_results.values() if r.get("passed", False))
        
        current_span.set_attributes({
            "dod.runtime.total_criteria": total_criteria,
            "dod.runtime.passed_criteria": passed_criteria,
            "dod.runtime.success_rate": passed_criteria / total_criteria if total_criteria > 0 else 0
        })
        
        return {
            "success": passed_criteria == total_criteria,
            "criteria_results": criteria_results
        }
        
    except Exception as e:
        current_span.record_exception(e)
        raise
```

### 3. Criteria-Level Spans

Individual criteria validation creates detailed child spans:

```python
def _execute_criteria_parallel(criteria: List[str], parent_span) -> Dict[str, Any]:
    """Execute criteria in parallel with individual tracing."""
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Create futures with span context
        futures = {}
        
        for criterion in criteria:
            # Create child span for each criterion
            child_span = tracer.start_span(
                f"dod.criterion.{criterion}",
                context=trace.set_span_in_context(parent_span)
            )
            
            child_span.set_attributes({
                "dod.criterion.name": criterion,
                "dod.criterion.weight": DOD_CRITERIA_WEIGHTS[criterion]["weight"],
                "dod.criterion.priority": DOD_CRITERIA_WEIGHTS[criterion]["priority"]
            })
            
            # Submit with span context
            future = executor.submit(
                _execute_single_criterion_with_span,
                criterion, child_span
            )
            futures[future] = (criterion, child_span)
        
        # Collect results
        for future in as_completed(futures):
            criterion, child_span = futures[future]
            try:
                result = future.result()
                results[criterion] = result
                
                # Set result attributes
                child_span.set_attributes({
                    "dod.criterion.score": result.get("score", 0),
                    "dod.criterion.passed": result.get("passed", False),
                    "dod.criterion.execution_time": result.get("execution_time", 0)
                })
                
            except Exception as e:
                child_span.record_exception(e)
                results[criterion] = {"passed": False, "error": str(e)}
            finally:
                child_span.end()
    
    return results
```

## Attributes Schema

### Core DoD Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `dod.operation` | string | DoD operation type | `complete_automation` |
| `dod.template` | string | Exoskeleton template | `enterprise` |
| `dod.environment` | string | Target environment | `production` |
| `dod.criteria_count` | int | Number of criteria evaluated | `7` |
| `dod.success_rate` | float | Overall success rate (0.0-1.0) | `0.92` |
| `dod.execution_time` | float | Execution time in seconds | `45.2` |
| `dod.auto_fix` | bool | Auto-fix enabled | `true` |
| `dod.parallel` | bool | Parallel execution | `true` |
| `dod.ai_assist` | bool | AI assistance enabled | `true` |

### Criterion-Specific Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `dod.criterion.name` | string | Criterion identifier | `testing` |
| `dod.criterion.weight` | float | Criterion weight in scoring | `0.25` |
| `dod.criterion.priority` | string | Criterion priority level | `critical` |
| `dod.criterion.score` | float | Criterion score (0.0-100.0) | `92.5` |
| `dod.criterion.passed` | bool | Whether criterion passed | `true` |
| `dod.criterion.execution_time` | float | Criterion execution time | `12.3` |

### Project Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `project.path` | string | Project directory path | `/home/user/myproject` |
| `project.name` | string | Project name | `my-microservice` |
| `project.version` | string | Project version | `1.2.3` |
| `project.language` | string | Primary language | `python` |
| `project.type` | string | Project type | `microservice` |

### Automation Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `automation.strategy` | string | Automation strategy | `80/20` |
| `automation.version` | string | DoD system version | `2.1.0` |
| `automation.mode` | string | Execution mode | `supervised` |
| `automation.pipeline.provider` | string | CI/CD provider | `github` |
| `automation.pipeline.environments` | string | Target environments | `dev,staging,prod` |

### Result Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `dod.result.success` | bool | Overall operation success | `true` |
| `dod.result.criteria_passed` | int | Number of criteria passed | `6` |
| `dod.result.criteria_failed` | int | Number of criteria failed | `1` |
| `dod.result.health_score` | float | Overall health score | `87.5` |
| `dod.result.recommendation_count` | int | Number of recommendations | `3` |

## Trace Context Propagation

### 1. Synchronous Operations

```python
def create_exoskeleton_with_tracing(project_path: Path, template: str) -> Dict[str, Any]:
    """Create exoskeleton with proper trace context."""
    
    with tracer.start_as_current_span("dod.create_exoskeleton") as span:
        span.set_attributes({
            "dod.operation": "create_exoskeleton",
            "dod.template": template,
            "project.path": str(project_path)
        })
        
        # Child operations inherit context automatically
        result = initialize_exoskeleton_files(project_path, template_config)
        
        if result["success"]:
            span.set_attributes({
                "dod.files_created": len(result.get("files_created", [])),
                "dod.workflows_created": len(result.get("workflows_created", []))
            })
        
        return result
```

### 2. Asynchronous Operations

```python
import asyncio
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor

# Initialize asyncio instrumentation
AsyncioInstrumentor().instrument()

async def execute_async_validation(criteria: List[str]) -> Dict[str, Any]:
    """Execute validation with async trace propagation."""
    
    current_span = trace.get_current_span()
    
    # Create tasks with trace context
    tasks = []
    for criterion in criteria:
        # Context is automatically propagated to async tasks
        task = asyncio.create_task(
            validate_criterion_async(criterion),
            name=f"validate_{criterion}"
        )
        tasks.append(task)
    
    # Wait for all validations
    results = await asyncio.gather(*tasks)
    
    return dict(zip(criteria, results))

async def validate_criterion_async(criterion: str) -> Dict[str, Any]:
    """Validate single criterion asynchronously."""
    
    with tracer.start_as_current_span(f"dod.criterion.{criterion}") as span:
        span.set_attributes({
            "dod.criterion.name": criterion,
            "dod.criterion.async": True
        })
        
        # Simulate async validation
        await asyncio.sleep(1)
        
        return {"passed": True, "score": 85.0}
```

### 3. External Tool Integration

```python
def run_external_tool_with_tracing(
    tool_name: str, 
    command: List[str], 
    project_path: Path
) -> Dict[str, Any]:
    """Run external tool with trace context injection."""
    
    with tracer.start_as_current_span(f"dod.external_tool.{tool_name}") as span:
        span.set_attributes({
            "dod.external_tool.name": tool_name,
            "dod.external_tool.command": " ".join(command),
            "project.path": str(project_path)
        })
        
        try:
            # Inject trace context into environment
            env = os.environ.copy()
            
            # Add OpenTelemetry trace headers
            trace_context = trace.get_current_span().get_span_context()
            if trace_context.is_valid:
                env["TRACEPARENT"] = format_trace_parent(trace_context)
            
            # Execute tool
            start_time = time.time()
            result = subprocess.run(
                command,
                cwd=project_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            execution_time = time.time() - start_time
            
            # Record results
            span.set_attributes({
                "dod.external_tool.exit_code": result.returncode,
                "dod.external_tool.execution_time": execution_time,
                "dod.external_tool.success": result.returncode == 0
            })
            
            if result.returncode != 0:
                span.record_exception(
                    subprocess.CalledProcessError(result.returncode, command, result.stderr)
                )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            span.record_exception(subprocess.TimeoutExpired(command, 300))
            return {"success": False, "error": "Tool execution timeout"}
```

## Metrics Collection

### 1. Business Metrics

```python
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, UpDownCounter

# Create meter
meter = metrics.get_meter(__name__)

# DoD automation metrics
dod_automations_total = meter.create_counter(
    "dod_automations_total",
    description="Total number of DoD automation runs",
    unit="1"
)

dod_automation_duration = meter.create_histogram(
    "dod_automation_duration_seconds", 
    description="DoD automation execution duration",
    unit="s"
)

dod_criteria_score = meter.create_histogram(
    "dod_criteria_score",
    description="DoD criteria scores",
    unit="1"
)

dod_health_score = meter.create_histogram(
    "dod_health_score",
    description="Project health scores",
    unit="1"
)

# Record metrics during operations
def record_automation_metrics(result: Dict[str, Any], environment: str):
    """Record metrics from automation result."""
    
    # Count automation runs
    dod_automations_total.add(1, {
        "environment": environment,
        "success": str(result.get("success", False)).lower(),
        "strategy": "80/20"
    })
    
    # Record execution time
    if "execution_time" in result:
        dod_automation_duration.record(
            result["execution_time"],
            {"environment": environment}
        )
    
    # Record criteria scores
    for criterion, details in result.get("criteria_results", {}).items():
        if "score" in details:
            dod_criteria_score.record(
                details["score"] / 100.0,  # Normalize to 0-1
                {
                    "criterion": criterion,
                    "environment": environment,
                    "passed": str(details.get("passed", False)).lower()
                }
            )
    
    # Record overall health score
    if "health_score" in result:
        dod_health_score.record(
            result["health_score"] / 100.0,  # Normalize to 0-1
            {"environment": environment}
        )
```

### 2. Performance Metrics

```python
# Infrastructure metrics
external_tool_duration = meter.create_histogram(
    "dod_external_tool_duration_seconds",
    description="External tool execution duration", 
    unit="s"
)

external_tool_errors = meter.create_counter(
    "dod_external_tool_errors_total",
    description="External tool execution errors",
    unit="1"
)

file_operations_total = meter.create_counter(
    "dod_file_operations_total",
    description="File operations performed",
    unit="1"
)

# Record during runtime operations
def record_external_tool_metrics(tool_name: str, result: Dict[str, Any]):
    """Record external tool metrics."""
    
    if "execution_time" in result:
        external_tool_duration.record(
            result["execution_time"],
            {"tool": tool_name}
        )
    
    if not result.get("success", True):
        external_tool_errors.add(1, {
            "tool": tool_name,
            "error_type": "execution_failure"
        })
```

## Configuration

### 1. Basic Configuration

```yaml
# .uvmgr/dod.yaml
telemetry:
  enabled: true
  
  # OpenTelemetry configuration
  otel:
    # OTLP exporter configuration
    exporter:
      endpoint: "http://localhost:4317"
      protocol: "grpc"  # grpc or http
      timeout: 30
      compression: "gzip"
      headers:
        api-key: "${OTEL_API_KEY}"
    
    # Service identification
    service:
      name: "uvmgr-dod"
      version: "2.1.0"
      namespace: "automation"
    
    # Resource attributes
    resource:
      environment: "production"
      team: "platform"
      component: "dod-automation"
    
    # Sampling configuration
    sampling:
      traces: 1.0  # Sample all traces
      metrics: 1.0
    
    # Batch configuration
    batch:
      max_export_batch_size: 512
      max_queue_size: 2048
      export_timeout: 30
      schedule_delay: 5
```

### 2. Environment-Specific Configuration

```yaml
# Development environment
environments:
  development:
    telemetry:
      otel:
        exporter:
          endpoint: "http://localhost:4317"
        sampling:
          traces: 1.0  # Full sampling for dev
        resource:
          environment: "development"

# Staging environment  
  staging:
    telemetry:
      otel:
        exporter:
          endpoint: "https://otel-staging.company.com"
        sampling:
          traces: 0.1  # 10% sampling
        resource:
          environment: "staging"

# Production environment
  production:
    telemetry:
      otel:
        exporter:
          endpoint: "https://otel.company.com"
        sampling:
          traces: 0.01  # 1% sampling
        resource:
          environment: "production"
```

### 3. Environment Variables

```bash
# OpenTelemetry environment variables
export OTEL_SERVICE_NAME="uvmgr-dod"
export OTEL_SERVICE_VERSION="2.1.0"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_EXPORTER_OTLP_COMPRESSION="gzip"
export OTEL_EXPORTER_OTLP_TIMEOUT="30"

# Authentication
export OTEL_EXPORTER_OTLP_HEADERS="api-key=${API_KEY}"

# Sampling
export OTEL_TRACES_SAMPLER="traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"

# Resource attributes
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=automation,deployment.environment=production"

# DoD-specific configuration
export DOD_TELEMETRY_ENABLED="true"
export DOD_METRICS_ENABLED="true"
export DOD_TRACE_DEBUG="false"
```

## Monitoring Setup

### 1. Jaeger Setup

```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # gRPC
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - LOG_LEVEL=debug
    volumes:
      - jaeger-data:/tmp
    
  # DoD automation with Jaeger
  uvmgr-dod:
    build: .
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - OTEL_SERVICE_NAME=uvmgr-dod
    depends_on:
      - jaeger
    volumes:
      - ./project:/workspace
    working_dir: /workspace
    command: uvmgr dod complete --env development

volumes:
  jaeger-data:
```

### 2. Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'uvmgr-dod'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'otel-collector'
    static_configs:
      - targets: ['localhost:8888']
```

```yaml
# grafana dashboard for DoD metrics
{
  "dashboard": {
    "title": "DoD Automation Dashboard",
    "panels": [
      {
        "title": "Automation Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dod_automations_total{success=\"true\"}[5m]) / rate(dod_automations_total[5m])",
            "legendFormat": "Success Rate"
          }
        ]
      },
      {
        "title": "Criteria Scores",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, dod_criteria_score)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Execution Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, dod_automation_duration_seconds)",
            "legendFormat": "Median"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules

```yaml
# prometheus alerts
groups:
  - name: dod_automation
    rules:
      - alert: DoD_Automation_High_Failure_Rate
        expr: (rate(dod_automations_total{success="false"}[5m]) / rate(dod_automations_total[5m])) > 0.2
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "DoD automation failure rate is high"
          description: "DoD automation failure rate is {{ $value | humanizePercentage }} over the last 5 minutes"
      
      - alert: DoD_Health_Score_Low
        expr: histogram_quantile(0.50, dod_health_score) < 0.7
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Project health scores are consistently low"
          description: "Median health score is {{ $value | humanizePercentage }} which is below the 70% threshold"
      
      - alert: DoD_External_Tool_Errors
        expr: rate(dod_external_tool_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High rate of external tool errors"
          description: "External tool error rate is {{ $value }} errors per second"
```

## Best Practices

### 1. Span Management
- Always use span context managers or decorators
- Set meaningful attributes early in the span lifecycle
- Record exceptions with full context
- End spans explicitly in error conditions

### 2. Attribute Optimization
- Use consistent attribute names across operations
- Avoid high-cardinality attributes (e.g., file paths, timestamps)
- Normalize values to standard ranges (0-1 for percentages)
- Use enums for categorical attributes

### 3. Performance Considerations
- Configure appropriate sampling rates for different environments
- Use batch exporters to reduce overhead
- Monitor collector resource usage
- Implement circuit breakers for external exporters

### 4. Security
- Never include sensitive data in span attributes
- Use secure transport (TLS) for trace export
- Implement proper authentication for OTLP endpoints
- Sanitize command-line arguments and environment variables

This comprehensive OpenTelemetry integration ensures the DoD automation system provides enterprise-grade observability while following industry-standard semantic conventions.