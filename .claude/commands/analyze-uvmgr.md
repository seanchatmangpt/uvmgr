# Analyze uvmgr Components

## Usage
`/project:analyze-uvmgr [component] [depth=deep]`

## Purpose
Deep analysis of uvmgr components with multi-perspective insights using the three-layer architecture pattern.

## Components
- **commands**: CLI command implementations
- **ops**: Business logic operations
- **runtime**: Execution layer
- **core**: Infrastructure utilities
- **telemetry**: OpenTelemetry instrumentation
- **search**: Advanced search capabilities
- **project**: Project scaffolding system

## Analysis Approach

### Phase 1: Component Discovery
1. Identify all modules in the specified component
2. Map dependencies and relationships
3. Analyze telemetry instrumentation coverage
4. Review test coverage

### Phase 2: Deep Analysis
1. **Architecture Perspective**
   - Three-layer compliance (Commands → Ops → Runtime)
   - Dependency injection patterns
   - Error handling strategies
   
2. **Telemetry Perspective**
   - OpenTelemetry instrumentation completeness
   - Metric collection patterns
   - Span and attribute usage
   
3. **Code Quality Perspective**
   - Type safety and annotations
   - Documentation coverage
   - Test coverage analysis
   
4. **Performance Perspective**
   - Async operation usage
   - Cache utilization
   - Subprocess optimization

### Phase 3: Synthesis
- Generate comprehensive component report
- Identify improvement opportunities
- Suggest refactoring patterns
- Recommend test additions

## Examples

```bash
# Analyze search subsystem
/project:analyze-uvmgr search

# Deep analysis of project generation
/project:analyze-uvmgr project depth=deep

# Analyze telemetry implementation
/project:analyze-uvmgr telemetry
```

## Output Format
- Component overview
- Dependency graph
- Telemetry coverage report
- Code quality metrics
- Improvement recommendations
- Test coverage gaps

## Integration Points
- Uses `uvmgr search` commands for code analysis
- Leverages OpenTelemetry data for runtime insights
- Integrates with test coverage reports
- Cross-references with CLAUDE.md documentation