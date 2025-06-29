# uvmgr Cookbook 🍳

*A comprehensive guide to all uvmgr commands with practical examples*

## 📚 Table of Contents

1. [🚀 Quick Start](#-quick-start)
2. [📦 Package Management (deps)](#-package-management-deps)
3. [🏗️ Building & Distribution (build)](#-building--distribution-build)
4. [🧪 Testing & Coverage (tests)](#-testing--coverage-tests)
5. [🎨 Code Quality & Linting (lint)](#-code-quality--linting-lint)
6. [📊 OpenTelemetry & Monitoring (otel)](#-opentelemetry--monitoring-otel)
7. [📖 Documentation & Guides (guides)](#-documentation--guides-guides)
8. [🌿 Git Worktree Management (worktree)](#-git-worktree-management-worktree)
9. [🎨 Information Design (infodesign)](#-information-design-infodesign)
10. [📈 Diagram Generation (mermaid)](#-diagram-generation-mermaid)
11. [🎯 Definition of Done (dod)](#-definition-of-done-dod)
12. [🏗️ Infrastructure & Terraform (terraform)](#-infrastructure--terraform-terraform)
13. [💾 Cache Management (cache)](#-cache-management-cache)
14. [🔬 Validation & Testing Recipes](#-validation--testing-recipes)
15. [⚡ Advanced Workflows](#-advanced-workflows)

---

## 🚀 Quick Start

### Get Help Anywhere
```bash
# Main help
uvmgr --help

# Command-specific help
uvmgr deps --help
uvmgr build --help
uvmgr tests --help

# Get version info
uvmgr --version
```

### Essential First Commands
```bash
# Initialize a new project
uvmgr deps init

# Add dependencies
uvmgr deps add requests fastapi

# Run tests
uvmgr tests run

# Build package
uvmgr build wheel
```

---

## 📦 Package Management (deps)

### Basic Dependency Operations

```bash
# Add production dependencies
uvmgr deps add requests httpx pydantic
uvmgr deps add "fastapi>=0.100.0"

# Add development dependencies
uvmgr deps add pytest pytest-cov --dev
uvmgr deps add black ruff mypy --group dev

# Add optional dependencies
uvmgr deps add jupyter pandas --optional data
uvmgr deps add streamlit plotly --optional viz

# Remove dependencies
uvmgr deps remove old-package
uvmgr deps remove dev-tool --dev
```

### Advanced Dependency Management

```bash
# Upgrade dependencies
uvmgr deps upgrade requests
uvmgr deps upgrade --all

# Sync dependencies (install from lockfile)
uvmgr deps sync
uvmgr deps sync --dev

# Show dependency tree
uvmgr deps tree
uvmgr deps tree --depth 2

# Check for outdated packages
uvmgr deps outdated
uvmgr deps outdated --json

# Export requirements
uvmgr deps export > requirements.txt
uvmgr deps export --dev > requirements-dev.txt
```

### Dependency Groups and Extras

```bash
# Work with dependency groups
uvmgr deps add --group testing pytest pytest-mock
uvmgr deps add --group docs sphinx mkdocs
uvmgr deps add --group security bandit safety

# Install specific groups
uvmgr deps sync --group testing
uvmgr deps sync --group docs,testing

# List installed packages
uvmgr deps list
uvmgr deps list --group dev
uvmgr deps list --json
```

---

## 🏗️ Building & Distribution (build)

### Basic Building

```bash
# Build wheel distribution
uvmgr build wheel

# Build source distribution
uvmgr build sdist

# Build both wheel and sdist
uvmgr build wheel sdist

# Build to specific directory
uvmgr build wheel --outdir custom-dist/
```

### Advanced Build Options

```bash
# Clean build (remove existing dist)
uvmgr build wheel --clean

# Build with specific Python version
uvmgr build wheel --python 3.11

# Verbose build output
uvmgr build wheel --verbose

# Build and upload to PyPI
uvmgr build wheel --upload
uvmgr build wheel --upload --repository testpypi
```

### Build Verification

```bash
# Check built distributions
uvmgr build check
uvmgr build check --strict

# Validate metadata
uvmgr build validate

# Test installation from built wheel
uvmgr build test-install

# Build performance analysis
uvmgr build profile
```

---

## 🧪 Testing & Coverage (tests)

### Running Tests

```bash
# Run all tests
uvmgr tests run

# Run specific test files
uvmgr tests run tests/test_api.py
uvmgr tests run tests/test_api.py tests/test_db.py

# Run tests with pattern matching
uvmgr tests run -k "test_user"
uvmgr tests run -k "not slow"

# Run tests in parallel
uvmgr tests run --parallel
uvmgr tests run -n 4  # Use 4 workers
```

### Test Configuration

```bash
# Run with different verbosity
uvmgr tests run --verbose
uvmgr tests run --quiet

# Stop on first failure
uvmgr tests run --fail-fast

# Run last failed tests only
uvmgr tests run --last-failed

# Run tests that failed in last run
uvmgr tests run --failed-first
```

### Coverage Analysis

```bash
# Run tests with coverage
uvmgr tests coverage

# Generate HTML coverage report
uvmgr tests coverage --html

# Generate XML coverage report (for CI)
uvmgr tests coverage --xml

# Set coverage threshold
uvmgr tests coverage --min-coverage 90

# Coverage for specific modules
uvmgr tests coverage --source src/mypackage
```

### Advanced Testing

```bash
# Run performance/benchmark tests
uvmgr tests benchmark
uvmgr tests benchmark --compare baseline

# Run security tests
uvmgr tests security

# Run integration tests
uvmgr tests integration

# Run tests with profiling
uvmgr tests profile

# Generate test reports
uvmgr tests report --format json
uvmgr tests report --format html
```

---

## 🎨 Code Quality & Linting (lint)

### Basic Linting

```bash
# Check code quality
uvmgr lint check

# Fix automatically fixable issues
uvmgr lint fix

# Run specific linters only
uvmgr lint check --ruff-only
uvmgr lint check --mypy-only
```

### Formatting

```bash
# Format code with Ruff
uvmgr lint format

# Check if formatting is needed
uvmgr lint format --check

# Format specific files
uvmgr lint format src/mypackage/api.py

# Format with different line length
uvmgr lint format --line-length 100
```

### Type Checking

```bash
# Run MyPy type checking
uvmgr lint mypy

# Type check specific modules
uvmgr lint mypy src/mypackage/

# Generate type coverage report
uvmgr lint mypy --coverage

# Show type checking errors only
uvmgr lint mypy --errors-only
```

### Advanced Quality Checks

```bash
# Security scanning
uvmgr lint security
uvmgr lint security --confidence high

# Import sorting
uvmgr lint imports

# Docstring checking
uvmgr lint docstrings

# Complexity analysis
uvmgr lint complexity

# Generate quality report
uvmgr lint report
uvmgr lint report --format json
```

---

## 📊 OpenTelemetry & Monitoring (otel)

### Validation & Testing

```bash
# Validate OpenTelemetry implementation
uvmgr otel validate

# Run Weaver semantic convention validation
uvmgr otel validate weaver

# Check telemetry performance
uvmgr otel validate performance

# Generate validation report
uvmgr otel validate --report validation-report.json
```

### Configuration & Setup

```bash
# Initialize OTEL configuration
uvmgr otel init

# Configure OTEL exporters
uvmgr otel config --exporter jaeger
uvmgr otel config --exporter prometheus
uvmgr otel config --endpoint http://localhost:4317

# Show current OTEL configuration
uvmgr otel status
```

### Monitoring & Analysis

```bash
# Start OTEL collector
uvmgr otel start

# Stop OTEL collector
uvmgr otel stop

# View telemetry data
uvmgr otel traces
uvmgr otel metrics

# Export telemetry data
uvmgr otel export --format json
uvmgr otel export --start "2023-01-01" --end "2023-01-31"
```

### Instrumentation

```bash
# Add instrumentation to project
uvmgr otel instrument

# Validate instrumentation
uvmgr otel validate instrumentation

# Generate instrumentation report
uvmgr otel instrument --report
```

---

## 📖 Documentation & Guides (guides)

### Guide Management

```bash
# List available guides
uvmgr guides list

# Show guide details
uvmgr guides show getting-started
uvmgr guides show api-reference

# Search guides
uvmgr guides search "testing"
uvmgr guides search --tag python
```

### Creating & Editing Guides

```bash
# Create new guide
uvmgr guides create "My New Guide" --category tutorial

# Edit existing guide
uvmgr guides edit getting-started

# Copy guide template
uvmgr guides template --type tutorial
uvmgr guides template --type reference
```

### Publishing & Sharing

```bash
# Publish guide
uvmgr guides publish my-guide

# Export guides
uvmgr guides export --format markdown
uvmgr guides export --format html

# Import guides
uvmgr guides import guides.zip
```

### Guide Validation

```bash
# Validate guide content
uvmgr guides validate my-guide

# Check links in guides
uvmgr guides check-links

# Generate guide metrics
uvmgr guides metrics
```

---

## 🌿 Git Worktree Management (worktree)

### Basic Worktree Operations

```bash
# Create new worktree
uvmgr worktree create feature-branch
uvmgr worktree create hotfix-123 --branch hotfix/bug-123

# List worktrees
uvmgr worktree list
uvmgr worktree list --verbose

# Switch to worktree
uvmgr worktree switch feature-branch

# Remove worktree
uvmgr worktree remove feature-branch
```

### Advanced Worktree Management

```bash
# Create worktree from specific commit
uvmgr worktree create release --commit v1.2.3

# Create worktree with fresh branch
uvmgr worktree create experiment --new-branch experiment/ai

# Sync worktree with remote
uvmgr worktree sync feature-branch

# Clean up stale worktrees
uvmgr worktree cleanup
```

### Worktree Utilities

```bash
# Show worktree status
uvmgr worktree status

# Archive worktree
uvmgr worktree archive old-feature

# Restore archived worktree
uvmgr worktree restore old-feature

# Move worktree
uvmgr worktree move old-path new-path
```

---

## 🎨 Information Design (infodesign)

### Content Analysis

```bash
# Analyze content structure
uvmgr infodesign analyze README.md
uvmgr infodesign analyze docs/ --recursive

# Generate content report
uvmgr infodesign report --source docs/
uvmgr infodesign report --format json

# Check content quality
uvmgr infodesign quality docs/api.md
```

### Content Generation

```bash
# Generate documentation
uvmgr infodesign generate --type api-docs
uvmgr infodesign generate --type user-guide

# Create content templates
uvmgr infodesign template --type tutorial
uvmgr infodesign template --type reference

# Improve existing content
uvmgr infodesign improve README.md
uvmgr infodesign improve --suggestions
```

### Content Organization

```bash
# Organize content structure
uvmgr infodesign organize docs/

# Validate content hierarchy
uvmgr infodesign validate structure

# Generate content index
uvmgr infodesign index
uvmgr infodesign index --format json
```

---

## 📈 Diagram Generation (mermaid)

### Basic Diagram Creation

```bash
# Generate flowchart
uvmgr mermaid generate --type flowchart --title "User Flow"
uvmgr mermaid flowchart "Login Process"

# Generate sequence diagram
uvmgr mermaid sequence "API Interaction"
uvmgr mermaid generate --type sequence --source api-docs.md

# Generate class diagram
uvmgr mermaid class "System Architecture"
```

### Advanced Diagram Features

```bash
# Generate from code analysis
uvmgr mermaid from-code src/mypackage/
uvmgr mermaid from-code --language python

# Create Git graph
uvmgr mermaid git-graph
uvmgr mermaid git-graph --branch-filter "main,develop"

# Generate ER diagram
uvmgr mermaid er "Database Schema"
```

### Diagram Management

```bash
# List available diagrams
uvmgr mermaid list

# Validate diagram syntax
uvmgr mermaid validate diagram.mmd

# Export diagrams
uvmgr mermaid export --format png
uvmgr mermaid export --format svg

# Update existing diagrams
uvmgr mermaid update diagram.mmd
```

### Interactive Features

```bash
# Live preview diagrams
uvmgr mermaid preview diagram.mmd

# Watch for changes
uvmgr mermaid watch src/ --auto-generate

# Batch process diagrams
uvmgr mermaid batch diagrams/
```

---

## 🎯 Definition of Done (dod)

### DoD Setup & Configuration

```bash
# Initialize DoD for project
uvmgr dod init
uvmgr dod init --template enterprise

# Create exoskeleton
uvmgr dod exoskeleton
uvmgr dod exoskeleton --template standard

# Show DoD status
uvmgr dod status
uvmgr dod status --detailed
```

### DoD Validation & Checking

```bash
# Validate DoD criteria
uvmgr dod validate
uvmgr dod validate --criteria security,testing

# Check specific criteria
uvmgr dod check tests
uvmgr dod check documentation
uvmgr dod check security

# Generate DoD report
uvmgr dod report
uvmgr dod report --format json
```

### Automation & CI/CD

```bash
# Complete automation workflow
uvmgr dod automate
uvmgr dod automate --skip-optional

# Generate CI/CD pipeline
uvmgr dod pipeline --provider github
uvmgr dod pipeline --provider gitlab

# Run comprehensive testing
uvmgr dod test-all
uvmgr dod test-all --parallel
```

### DoD Templates & Customization

```bash
# List available templates
uvmgr dod templates

# Customize DoD criteria
uvmgr dod customize
uvmgr dod customize --add-criteria performance

# Export DoD configuration
uvmgr dod export config.yaml
uvmgr dod import config.yaml
```

---

## 🏗️ Infrastructure & Terraform (terraform)

### Terraform Operations

```bash
# Initialize Terraform project
uvmgr terraform init
uvmgr terraform init --backend s3

# Plan infrastructure changes
uvmgr terraform plan
uvmgr terraform plan --var-file prod.tfvars

# Apply infrastructure
uvmgr terraform apply
uvmgr terraform apply --auto-approve

# Destroy infrastructure
uvmgr terraform destroy
uvmgr terraform destroy --target resource.name
```

### State Management

```bash
# Show Terraform state
uvmgr terraform state list
uvmgr terraform state show resource.name

# Import existing resource
uvmgr terraform import resource.name existing-id

# Move state resources
uvmgr terraform state mv old.name new.name

# Remove from state
uvmgr terraform state rm resource.name
```

### Terraform Validation & Quality

```bash
# Validate Terraform configuration
uvmgr terraform validate

# Format Terraform files
uvmgr terraform format
uvmgr terraform format --check

# Security scanning
uvmgr terraform security-scan

# Generate documentation
uvmgr terraform docs
```

### Advanced Terraform Features

```bash
# Workspace management
uvmgr terraform workspace list
uvmgr terraform workspace new prod
uvmgr terraform workspace select dev

# Output management
uvmgr terraform output
uvmgr terraform output --json

# Graph generation
uvmgr terraform graph
uvmgr terraform graph --type plan
```

---

## 💾 Cache Management (cache)

### Basic Cache Operations

```bash
# Show cache info
uvmgr cache info
uvmgr cache info --size

# Clear all caches
uvmgr cache clear
uvmgr cache clear --confirm

# Clear specific cache types
uvmgr cache clear uv
uvmgr cache clear pip
```

### Cache Analysis

```bash
# Analyze cache usage
uvmgr cache analyze
uvmgr cache analyze --verbose

# Show cache statistics
uvmgr cache stats
uvmgr cache stats --json

# Find large cache entries
uvmgr cache large-entries
uvmgr cache large-entries --size 100MB
```

### Cache Optimization

```bash
# Optimize cache
uvmgr cache optimize

# Vacuum cache (remove orphaned entries)
uvmgr cache vacuum

# Rebuild cache indexes
uvmgr cache rebuild-index

# Set cache limits
uvmgr cache limit --size 5GB
uvmgr cache limit --age 30d
```

---

## 🔬 Validation & Testing Recipes

### Complete Validation Suite

```bash
# Run full validation (recommended for CI/CD)
python validate_weaver_telemetry.py
python e2e_external_validation.py
python -m pytest tests/unit/test_*_validation.py -v

# Quick validation check
uvmgr tests run tests/test_validation.py
uvmgr otel validate
uvmgr dod validate
```

### Performance Testing

```bash
# Test telemetry performance
python -m pytest tests/unit/test_telemetry_instrumentation.py::TestTelemetryPerformance -v

# External project performance
python e2e_external_validation.py --performance

# Build performance
uvmgr build profile
```

### Security & Quality Validation

```bash
# Security validation
uvmgr lint security
uvmgr dod check security
uvmgr terraform security-scan

# Quality validation
uvmgr lint check
uvmgr tests coverage --min-coverage 95
uvmgr otel validate weaver
```

### Continuous Validation Script

```bash
#!/bin/bash
# complete-validation.sh

echo "🔍 Starting Complete uvmgr Validation"

# 1. Weaver telemetry validation
echo "📊 Weaver Telemetry Validation"
python validate_weaver_telemetry.py

# 2. Unit tests
echo "🧪 Unit Tests"
uvmgr tests coverage --min-coverage 90

# 3. Code quality
echo "🎨 Code Quality"
uvmgr lint check

# 4. Security checks
echo "🔒 Security Validation"
uvmgr lint security

# 5. DoD validation
echo "🎯 Definition of Done"
uvmgr dod validate

# 6. External project validation
echo "🌍 External Projects"
python e2e_external_validation.py

# 7. Build validation
echo "🏗️ Build Validation"
uvmgr build wheel --verify

echo "✅ Complete validation finished!"
```

---

## ⚡ Advanced Workflows

### CI/CD Pipeline Recipe

```yaml
# .github/workflows/uvmgr-validation.yml
name: uvmgr Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uvmgr
        run: pip install -e .
      
      - name: Run Weaver validation
        run: python validate_weaver_telemetry.py
      
      - name: Run tests with coverage
        run: uvmgr tests coverage --min-coverage 95
      
      - name: Lint and format check
        run: uvmgr lint check
      
      - name: DoD validation
        run: uvmgr dod validate
      
      - name: Build validation
        run: uvmgr build wheel --verify
```

### Development Workflow

```bash
# Daily development workflow
function uvmgr-dev-cycle() {
    echo "🚀 Starting development cycle"
    
    # 1. Update dependencies
    uvmgr deps upgrade --check
    
    # 2. Run tests
    uvmgr tests run --fail-fast
    
    # 3. Check code quality
    uvmgr lint fix
    uvmgr lint check
    
    # 4. Validate changes
    uvmgr otel validate
    
    # 5. Update documentation if needed
    uvmgr guides validate
    
    echo "✅ Development cycle complete"
}

# Release workflow
function uvmgr-release() {
    echo "🎉 Starting release workflow"
    
    # 1. Complete validation
    python validate_weaver_telemetry.py
    python e2e_external_validation.py
    
    # 2. DoD validation
    uvmgr dod validate
    
    # 3. Build and test
    uvmgr build wheel sdist
    uvmgr build test-install
    
    # 4. Generate documentation
    uvmgr guides export --format html
    
    echo "✅ Release workflow complete"
}
```

### Project Initialization Recipe

```bash
# Complete project setup
function setup-uvmgr-project() {
    local project_name=$1
    
    echo "🏗️ Setting up $project_name with uvmgr"
    
    # 1. Initialize project structure
    mkdir $project_name && cd $project_name
    
    # 2. Initialize uvmgr
    uvmgr deps init
    
    # 3. Add essential dependencies
    uvmgr deps add --dev pytest pytest-cov black ruff mypy
    uvmgr deps add --dev pre-commit commitizen
    
    # 4. Initialize DoD
    uvmgr dod init --template standard
    
    # 5. Create exoskeleton
    uvmgr dod exoskeleton
    
    # 6. Initialize documentation
    uvmgr guides create "Getting Started" --category tutorial
    
    # 7. Setup CI/CD
    uvmgr dod pipeline --provider github
    
    # 8. Initial validation
    uvmgr tests run
    uvmgr lint check
    uvmgr dod validate
    
    echo "✅ Project $project_name initialized successfully!"
}
```

### Monitoring & Observability Setup

```bash
# Setup complete observability
function setup-observability() {
    echo "📊 Setting up observability"
    
    # 1. Initialize OTEL
    uvmgr otel init
    
    # 2. Configure exporters
    uvmgr otel config --exporter jaeger --endpoint http://localhost:14268
    uvmgr otel config --exporter prometheus --endpoint http://localhost:9090
    
    # 3. Add instrumentation
    uvmgr otel instrument
    
    # 4. Validate setup
    uvmgr otel validate
    uvmgr otel validate weaver
    uvmgr otel validate performance
    
    # 5. Generate monitoring dashboard
    uvmgr mermaid generate --type flowchart --title "Observability Architecture"
    
    echo "✅ Observability setup complete"
}
```

### Troubleshooting Commands

```bash
# Debug common issues
function uvmgr-debug() {
    echo "🔍 uvmgr Debug Information"
    
    # System info
    uvmgr --version
    python --version
    
    # Check configuration
    uvmgr cache info
    uvmgr otel status
    uvmgr dod status
    
    # Validate setup
    uvmgr deps check
    uvmgr tests run --collect-only
    uvmgr lint check --no-fix
    
    # Performance check
    python validate_weaver_telemetry.py | grep "Success Rate"
    
    echo "✅ Debug information collected"
}

# Clean and reset
function uvmgr-reset() {
    echo "🧹 Resetting uvmgr environment"
    
    # Clear caches
    uvmgr cache clear --confirm
    
    # Reset dependencies
    uvmgr deps sync --clean
    
    # Clean build artifacts
    uvmgr build clean
    
    # Validate clean state
    uvmgr tests run
    uvmgr lint check
    
    echo "✅ Environment reset complete"
}
```

---

## 🎓 Best Practices & Tips

### Daily Usage Patterns

1. **Morning Routine**: `uvmgr deps sync && uvmgr tests run --fail-fast`
2. **Before Commit**: `uvmgr lint fix && uvmgr tests coverage`
3. **Before Push**: `uvmgr dod validate && python validate_weaver_telemetry.py`
4. **Release Prep**: `uvmgr build wheel && uvmgr dod test-all`

### Performance Optimization

```bash
# Use parallel execution where possible
uvmgr tests run --parallel
uvmgr dod test-all --parallel

# Cache optimization
uvmgr cache optimize

# Use specific targets
uvmgr lint check src/mypackage/  # Instead of entire project
uvmgr tests run tests/unit/      # Instead of all tests
```

### Configuration Tips

```bash
# Set up aliases for common commands
alias ut="uvmgr tests run"
alias ul="uvmgr lint check"
alias ub="uvmgr build wheel"
alias uv="python validate_weaver_telemetry.py"

# Environment variables for consistency
export UVMGR_DEFAULT_COVERAGE_MIN=95
export UVMGR_DEFAULT_LINT_LINE_LENGTH=88
export OTEL_SERVICE_NAME="my-project"
```

---

*This cookbook covers all major uvmgr commands and workflows. For specific command options and advanced usage, use `uvmgr COMMAND --help` or refer to the detailed documentation.*

**Happy cooking with uvmgr! 🍳✨**