# uvmgr E2E Dogfooding Tests

This directory contains end-to-end tests where uvmgr tests itself - true dogfooding!

## Overview

The dogfooding test loop verifies that uvmgr can:
1. Test its own functionality using its own commands
2. Handle real-world development workflows
3. Maintain performance standards
4. Work correctly across different platforms

## Test Structure

```
tests/e2e/
├── conftest.py              # Shared fixtures and helpers
├── fixtures/                # Test data and sample projects
│   ├── sample_project/      # Complete sample project
│   └── expected_outputs/    # Expected command outputs
├── test_dogfooding.py       # Self-referential tests
├── test_workflows.py        # Real-world workflow tests
├── test_performance.py      # Performance benchmarks
├── run_dogfood_loop.py      # Standalone dogfood runner
└── dogfood.sh              # Shell script runner
```

## Running Tests

### Quick Start

```bash
# Run the complete dogfooding loop
./tests/e2e/dogfood.sh

# Run with verbose output
./tests/e2e/dogfood.sh -v

# Run specific test files
uvmgr tests run tests/e2e/test_dogfooding.py
uvmgr tests run tests/e2e/test_workflows.py
```

### Standalone Dogfood Runner

```bash
# Run the dogfood loop directly
python tests/e2e/run_dogfood_loop.py

# With verbose output
python tests/e2e/run_dogfood_loop.py -v

# Using uvmgr itself
uvmgr run python tests/e2e/run_dogfood_loop.py
```

### Performance Tests

```bash
# Run all performance benchmarks
uvmgr tests run tests/e2e/test_performance.py

# Run specific benchmark
uvmgr tests run tests/e2e/test_performance.py::TestPerformanceBenchmarks::test_command_startup_time
```

## Test Categories

### 1. Dogfooding Tests (`test_dogfooding.py`)

Self-referential tests where uvmgr tests itself:
- `test_uvmgr_tests_itself` - uvmgr runs its own test suite
- `test_uvmgr_lints_itself` - uvmgr checks its own code
- `test_uvmgr_builds_itself` - uvmgr builds its own wheel
- `test_recursive_uvmgr_call` - uvmgr calling uvmgr

### 2. Workflow Tests (`test_workflows.py`)

Real-world development workflows:
- **Project Setup**: Initialize, configure, and set up new projects
- **Development Cycle**: TDD workflow, CI/CD simulation
- **Dependency Management**: Add, remove, update dependencies
- **Release Process**: Version bumping, building, checking
- **AI Integration**: AI-assisted development (requires API keys)

### 3. Performance Tests (`test_performance.py`)

Benchmarks and scalability tests:
- **Command Performance**: Startup time, response time
- **Dependency Operations**: Add/remove/list speed
- **Build Performance**: Wheel/sdist creation time
- **Scalability**: Large dependency trees, many test files
- **Cache Effectiveness**: Cold vs warm cache performance

## CI/CD Integration

The `.github/workflows/dogfood-e2e.yml` workflow runs:
1. **Multi-platform tests**: Linux, macOS, Windows
2. **Multi-Python version**: 3.8, 3.11, 3.12
3. **Performance tracking**: Automated benchmarking
4. **Integration scenarios**: Monorepo, AI features, MCP server
5. **Executable building**: Self-contained uvmgr binaries

## Writing New E2E Tests

### Use the Fixtures

```python
def test_my_workflow(uvmgr_runner, temp_project):
    """Test a specific workflow."""
    # Use uvmgr_runner to execute commands
    result = uvmgr_runner("deps", "add", "pytest", cwd=temp_project)
    assert_command_success(result)
    
    # Verify outputs
    assert_output_contains(result, "pytest")
```

### Add Performance Benchmarks

```python
def test_new_operation_performance(uvmgr_runner, benchmark_project):
    """Benchmark a new operation."""
    with timer() as t:
        result = uvmgr_runner("new-command", cwd=benchmark_project)
        assert_command_success(result)
    
    # Assert performance requirements
    assert t.elapsed < 5.0, f"Operation too slow: {t.elapsed}s"
```

### Test Error Scenarios

```python
def test_error_handling(uvmgr_runner, temp_project):
    """Test error scenarios."""
    # Intentionally cause an error
    result = uvmgr_runner("invalid-command", check=False)
    
    # Verify graceful failure
    assert result.returncode != 0
    assert "error" in result.stderr.lower()
```

## Performance Goals

- **Startup**: < 0.5s for help/version
- **Deps list**: < 2s for typical project
- **Single test**: < 3s overhead
- **Build wheel**: < 5s for simple project
- **Cache speedup**: > 10% improvement

## Debugging Tips

1. **Use verbose mode**: Add `-v` to see detailed command output
2. **Check isolated environment**: Tests use temporary directories
3. **Review fixtures**: See `conftest.py` for available helpers
4. **Examine reports**: `dogfood_report.json` has detailed results

## Known Issues

- Network-dependent tests may be flaky
- Cache effectiveness varies by network speed
- Windows path handling may differ
- AI tests require API keys in environment

## Future Improvements

- [ ] Add telemetry collection and validation
- [ ] Implement parallel test execution
- [ ] Add cross-version compatibility tests
- [ ] Create visual performance dashboards
- [ ] Add stress testing scenarios