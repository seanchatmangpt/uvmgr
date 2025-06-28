# Comprehensive Test Workflow

## Usage
`/project:test-workflow [component] [coverage-threshold=80]`

## Purpose
Automated test workflow with coverage analysis, AI-assisted fixing, and comprehensive validation.

## Workflow Phases

### Phase 1: Pre-Test Analysis
1. **Dependency Check**
   - Verify all test dependencies installed
   - Check for missing test fixtures
   - Validate test configuration

2. **Coverage Baseline**
   - Get current coverage metrics
   - Identify untested modules
   - Generate coverage gaps report

### Phase 2: Test Execution
1. **Unit Tests**
   ```bash
   uvmgr tests run --verbose
   uvmgr tests coverage
   ```

2. **Integration Tests**
   - Test command integration
   - Verify ops → runtime flow
   - Check external dependencies

3. **OTEL Validation**
   ```bash
   uvmgr otel validate
   uvmgr otel demo
   ```

### Phase 3: AI-Assisted Fixing
1. **Failure Analysis**
   - Parse test output
   - Identify failure patterns
   - Group related failures

2. **AI Fix Generation**
   ```bash
   uvmgr ai fix-tests
   ```

3. **Fix Validation**
   - Apply fixes incrementally
   - Re-run affected tests
   - Verify no regressions

### Phase 4: Coverage Enhancement
1. **Gap Analysis**
   - Identify low-coverage modules
   - Generate test suggestions
   - Priority ranking by impact

2. **Test Generation**
   - AI-assisted test creation
   - Edge case identification
   - Mock/fixture generation

### Phase 5: Final Validation
1. **Full Test Suite**
   - Run all tests with coverage
   - Generate HTML coverage report
   - Verify threshold met

2. **Performance Validation**
   - Check test execution time
   - Identify slow tests
   - Optimize test suite

## Examples
```bash
# Test search subsystem with 90% coverage target
/project:test-workflow search coverage-threshold=90

# Test all components
/project:test-workflow all

# Quick test for commands layer
/project:test-workflow commands
```

## Output
- Test execution summary
- Coverage report with gaps
- AI fix suggestions applied
- Performance metrics
- OTEL validation results

## Integration
- Uses `uvmgr tests` for execution
- Leverages `uvmgr ai` for fixes
- Integrates with OTEL validation
- Generates comprehensive reports