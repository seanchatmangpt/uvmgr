# External Project Testing with uvmgr

This directory contains comprehensive testing infrastructure to validate uvmgr's capabilities on external Python projects. It demonstrates uvmgr's ability to handle the complete Python development lifecycle outside of its own codebase.

## Overview

The external project testing framework validates uvmgr across:

1. **Project Setup & Initialization**
2. **Dependency Management** 
3. **Development Workflow** (TDD, linting, formatting)
4. **Testing & Coverage**
5. **Building & Distribution**
6. **AI Integration & MCP Server**
7. **Observability & Telemetry**
8. **Release & Deployment**

## Test Projects

### Primary Test Targets
- **copier**: Template engine for project scaffolding
- **fastapi**: Modern web framework (simulates web projects)
- **pytest**: Testing framework (simulates tool/library projects)
- **custom-sample**: Minimal project from scratch

### Lifecycle Coverage Matrix

| Phase | copier | fastapi | pytest | custom |
|-------|--------|---------|--------|--------|
| Init/Clone | ✓ | ✓ | ✓ | ✓ |
| Dependencies | ✓ | ✓ | ✓ | ✓ |
| Dev Setup | ✓ | ✓ | ✓ | ✓ |
| Testing | ✓ | ✓ | ✓ | ✓ |
| Linting | ✓ | ✓ | ✓ | ✓ |
| Building | ✓ | ✓ | ✓ | ✓ |
| AI Features | ✓ | ✓ | ✓ | ✓ |
| OTEL/Telemetry | ✓ | ✓ | ✓ | ✓ |

## Infrastructure

### Docker Compose Services
- **uvmgr-external**: Clean environment with uvmgr installed
- **otel-collector**: OpenTelemetry collection and validation
- **jaeger**: Distributed tracing visualization
- **prometheus**: Metrics collection and monitoring
- **grafana**: Observability dashboards

### Test Environments
- **Isolated**: Each project tested in separate containers
- **Networked**: Services can communicate for integration testing
- **Instrumented**: Full OTEL instrumentation enabled
- **Clean State**: Fresh environment for each test run

## Usage

### Quick Start
```bash
# Run full external project lifecycle tests
./external-project-testing/run-lifecycle-tests.sh

# Test specific project
./external-project-testing/run-lifecycle-tests.sh copier

# Test with observability
docker-compose -f external-project-testing/docker-compose.external.yml up --build
```

### Detailed Testing
```bash
# Individual lifecycle phases
./external-project-testing/test-lifecycle.py --project copier --phase setup
./external-project-testing/test-lifecycle.py --project copier --phase development
./external-project-testing/test-lifecycle.py --project copier --phase build

# With telemetry validation
./external-project-testing/test-lifecycle.py --project copier --validate-otel
```

### Observability
- **Jaeger UI**: http://localhost:16686 (traces)
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3000 (dashboards)

## Test Scenarios

### 1. Project Bootstrap
- Clone/download external project
- Initialize uvmgr in project directory
- Set up virtual environment
- Validate uvmgr recognizes project structure

### 2. Dependency Management
```bash
uvmgr deps list                    # Analyze existing dependencies
uvmgr deps add pytest --dev       # Add development dependencies
uvmgr deps add requests           # Add production dependencies
uvmgr deps update                 # Update all dependencies
uvmgr deps remove unused-package  # Clean up dependencies
```

### 3. Development Workflow
```bash
uvmgr tests run                   # Run existing test suite
uvmgr tests coverage              # Generate coverage reports
uvmgr lint check                  # Check code quality
uvmgr lint fix                    # Auto-fix linting issues
```

### 4. Build & Distribution
```bash
uvmgr build dist                  # Build wheel/sdist
uvmgr build exe                   # Create standalone executable
uvmgr build spec                  # Generate PyInstaller spec
uvmgr release version patch       # Bump version
```

### 5. AI Integration
```bash
uvmgr ai assist "Add async support to this function"
uvmgr ai fix-tests                # Fix failing tests with AI
uvmgr ai plan "Add caching layer" # Plan implementation
uvmgr serve start                 # Start MCP server
```

### 6. Advanced Features
```bash
uvmgr agent coordinate            # Multi-agent workflows
uvmgr otel validate              # OTEL instrumentation
uvmgr weaver generate            # Code generation
uvmgr remote execute             # Distributed execution
```

## Validation Criteria

### Performance Benchmarks
- **Command Startup**: < 0.5s for basic commands
- **Dependency Resolution**: < 30s for complex projects
- **Test Execution**: < 50% overhead vs direct pytest
- **Build Time**: < 10% overhead vs direct build

### Functional Requirements
- **Compatibility**: Works with existing project structures
- **Non-destructive**: Doesn't break existing workflows
- **Incremental**: Can be adopted gradually
- **Portable**: Works across different project types

### Quality Metrics
- **Test Coverage**: > 95% for uvmgr commands
- **Error Handling**: Graceful failure with helpful messages
- **Telemetry**: Complete OTEL traces for all operations
- **Documentation**: Auto-generated from successful runs

## Real-World Simulation

### Copier Project Testing
```bash
# 1. Clone copier (template engine)
git clone https://github.com/copier-org/copier.git /tmp/test-copier
cd /tmp/test-copier

# 2. Initialize uvmgr
uvmgr project init

# 3. Analyze existing setup
uvmgr deps list
uvmgr tests run --dry-run

# 4. Enhance with uvmgr
uvmgr deps add pytest-benchmark --dev
uvmgr lint check
uvmgr build dist

# 5. AI-enhanced development
uvmgr ai assist "Optimize template rendering performance"
uvmgr ai fix-tests

# 6. Advanced workflows
uvmgr agent coordinate
uvmgr otel validate
```

## Expected Outcomes

### Success Criteria
1. **Zero Breaking Changes**: Original project functionality intact
2. **Enhanced Capabilities**: Additional uvmgr features work seamlessly
3. **Performance**: No significant performance degradation
4. **Observability**: Complete telemetry for all operations
5. **AI Integration**: MCP server enables AI-assisted development

### Deliverables
- **Test Reports**: Detailed results for each project/phase
- **Performance Metrics**: Benchmark comparisons
- **OTEL Traces**: Complete observability validation
- **Documentation**: Auto-generated usage guides
- **Container Images**: Pre-configured test environments

## Integration with CI/CD

### GitHub Actions Integration
```yaml
- name: Test uvmgr on External Projects
  run: |
    ./external-project-testing/run-lifecycle-tests.sh
    ./external-project-testing/validate-telemetry.sh
```

### Multi-Platform Testing
- **Linux**: Ubuntu 22.04, Python 3.9-3.12
- **macOS**: Latest, Python 3.9-3.12  
- **Windows**: Latest, Python 3.9-3.12

This comprehensive testing framework ensures uvmgr works reliably across diverse Python project ecosystems while maintaining observability and performance standards.