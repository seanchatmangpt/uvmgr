# Project Migration to uvmgr/Substrate

## Usage
`/project:migrate-project [path] [features=auto]`

## Purpose
Migrate existing Python projects to use uvmgr and adopt Substrate-inspired modern development practices.

## Migration Phases

### Phase 1: Project Analysis
1. **Current State Assessment**
   - Detect project type (setuptools, poetry, pipenv, etc.)
   - Analyze existing dependencies
   - Check test framework
   - Review CI/CD configuration

2. **Compatibility Check**
   - Python version requirements
   - Dependency conflicts
   - Build system compatibility
   - Test framework support

### Phase 2: uvmgr Integration
1. **Auto-Install uvmgr**
   ```bash
   cd external-project-testing/
   bash auto-install-uvmgr.sh [project-path]
   ```

2. **Dependency Migration**
   - Convert requirements.txt/Pipfile/poetry.lock
   - Preserve version constraints
   - Handle dev dependencies
   - Create pyproject.toml

3. **Virtual Environment Setup**
   ```bash
   uvmgr python pin 3.11
   uvmgr venv create
   uvmgr deps sync
   ```

### Phase 3: Substrate Features Addition
1. **DevContainer Configuration**
   - Generate .devcontainer/devcontainer.json
   - Add VS Code extensions
   - Configure development environment

2. **GitHub Actions**
   - Create .github/workflows/ci.yml
   - Add test, lint, and build jobs
   - Configure matrix testing

3. **Pre-commit Hooks**
   - Generate .pre-commit-config.yaml
   - Add Ruff, MyPy, Black
   - Configure commit message validation

4. **Task Automation**
   - Create Taskfile.yml or poe tasks
   - Define common workflows
   - Add development shortcuts

### Phase 4: Code Quality Enhancement
1. **Linting Configuration**
   ```bash
   uvmgr lint fix
   ```
   - Apply Ruff formatting
   - Fix common issues
   - Update import sorting

2. **Type Hints**
   - Add basic type annotations
   - Configure MyPy
   - Generate type stubs

3. **Test Coverage**
   ```bash
   uvmgr tests coverage
   ```
   - Add pytest configuration
   - Generate coverage reports
   - Identify test gaps

### Phase 5: OTEL Integration
1. **Instrumentation**
   - Add OpenTelemetry to key modules
   - Configure telemetry export
   - Set up metrics collection

2. **Validation**
   ```bash
   uvmgr otel validate
   ```
   - Verify instrumentation
   - Check trace collection
   - Test metric export

## Migration Options

### Minimal Migration
- Basic uvmgr integration
- Dependency management only
- Preserve existing structure

### Standard Migration
- uvmgr + modern tooling
- Linting and formatting
- Basic CI/CD

### Full Substrate Migration
- All Substrate features
- Complete modernization
- OTEL integration
- Advanced CI/CD

## Examples
```bash
# Auto-detect and migrate with all features
/project:migrate-project ./my-legacy-project

# Minimal migration for compatibility
/project:migrate-project ./my-app features=minimal

# Full Substrate transformation
/project:migrate-project ./my-service features=substrate
```

## Safety Features
- **Backup Creation**: Automatic backup before changes
- **Incremental Migration**: Step-by-step with validation
- **Rollback Support**: Undo migrations if needed
- **Dry Run Mode**: Preview changes without applying

## Output
- Migration report
- Changed files list
- New features added
- Test results
- OTEL validation status
- Next steps guide