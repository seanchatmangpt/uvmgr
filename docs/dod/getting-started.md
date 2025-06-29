# Getting Started with DoD Automation

This guide will walk you through setting up and using the Definition of Done (DoD) automation system for your project.

## Prerequisites

- Python 3.11 or higher
- Git repository (local or remote)
- Basic understanding of CI/CD concepts

## Installation

### Option 1: Install from PyPI
```bash
pip install uvmgr
```

### Option 2: Install from Source
```bash
git clone https://github.com/your-org/uvmgr.git
cd uvmgr
pip install -e ".[dev]"
```

### Verify Installation
```bash
uvmgr dod --help
```

You should see the DoD automation commands listed.

## Your First DoD Project

### 1. Project Status Check
Start by checking your project's current DoD status:

```bash
cd your-project
uvmgr dod status
```

**Example Output:**
```
📊 Project DoD Status
╭─────────────────────────── 📊 DoD Status Summary ────────────────────────────╮
│ Overall Health Score: 45.2%                                                  │
│ Status: NEEDS WORK                                                           │
│ DoD Compliance: 42.0%                                                        │
│ Security Score: 38.0%                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯

🔧 Recommendations:
   • Improve test coverage
   • Fix security vulnerabilities
   • Update dependencies
```

### 2. Initialize DoD Exoskeleton
Create the automation framework for your project:

```bash
# For standard projects
uvmgr dod exoskeleton --template standard

# For enterprise projects with governance
uvmgr dod exoskeleton --template enterprise

# For AI-first projects
uvmgr dod exoskeleton --template ai-native
```

**What This Creates:**
- `.uvmgr/` - DoD configuration directory
- `.uvmgr/exoskeleton/config.yaml` - Main configuration
- `.uvmgr/automation/workflows/` - Automation workflows
- CI/CD pipeline templates
- Security and testing configurations

### 3. Validate Specific Criteria
Test individual DoD criteria:

```bash
# Validate testing criteria
uvmgr dod validate --criteria testing --detailed

# Validate security and code quality
uvmgr dod validate --criteria security,code_quality

# Validate all criteria
uvmgr dod validate
```

**Understanding the Output:**
```
✅ Validation Results
┏━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ Criteria      ┃ Score   ┃ Status  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ Testing       │ 92.0%   │ ✅ PASS │
│ Security      │ 78.0%   │ ✅ PASS │
│ Code_Quality  │ 65.0%   │ ❌ FAIL │
└───────────────┴─────────┴─────────┘

📊 Overall Score: 85.3%
```

### 4. Run Complete Automation
Execute the full DoD automation workflow:

```bash
# Development environment
uvmgr dod complete --env development

# Production environment with auto-fix
uvmgr dod complete --env production --auto-fix

# Parallel execution for faster results
uvmgr dod complete --parallel
```

## Understanding DoD Criteria

The DoD system implements the 80/20 principle, focusing on criteria that deliver maximum impact:

### Critical Criteria (70% weight)
- **Testing (25%)**: Unit, integration, and E2E test coverage
- **Security (25%)**: Vulnerability scanning and compliance
- **DevOps (20%)**: CI/CD pipelines and deployment automation

### Important Criteria (20% weight)
- **Code Quality (10%)**: Linting, complexity analysis, maintainability
- **Documentation (10%)**: API docs, user guides, architecture documentation

### Optional Criteria (10% weight)
- **Performance (5%)**: Benchmarks and optimization
- **Compliance (5%)**: Regulatory and governance requirements

## Customizing Your DoD Configuration

### Basic Configuration
Create or edit `.uvmgr/dod.yaml`:

```yaml
# DoD Automation Configuration
automation:
  enabled: true
  level: "supervised"  # autonomous, supervised, manual
  parallel: true
  auto_fix: false

criteria:
  testing:
    enabled: true
    coverage_threshold: 80
    types: ["unit", "integration", "e2e"]
    frameworks: ["pytest", "jest"]
  
  security:
    enabled: true
    scan_dependencies: true
    vulnerability_threshold: "medium"
    tools: ["bandit", "safety", "semgrep"]
  
  devops:
    enabled: true
    provider: "github"  # github, gitlab, azure
    environments: ["dev", "staging", "production"]
    features: ["testing", "security", "deployment"]

  code_quality:
    enabled: true
    linting: true
    complexity_threshold: 10
    tools: ["ruff", "mypy", "black"]

# AI-powered features
ai:
  enabled: true
  insights: true
  auto_optimization: false
  features: ["code_review", "test_generation"]

# OpenTelemetry configuration
telemetry:
  enabled: true
  endpoint: "http://localhost:4317"
  service_name: "my-project-dod"
  attributes:
    environment: "development"
    team: "platform"
```

### Template Customization
Customize exoskeleton templates in `.uvmgr/templates/`:

```yaml
# .uvmgr/templates/custom.yaml
description: "Custom DoD template for microservices"
includes:
  - "microservice_ci"
  - "kubernetes_deployment" 
  - "service_mesh"
  - "distributed_tracing"
ai_features:
  - "architecture_analysis"
  - "performance_optimization"
  - "fault_injection"

structure:
  automation:
    - ".uvmgr/microservice/"
    - ".uvmgr/k8s/"
  ci_cd:
    - ".github/workflows/microservice.yml"
    - "k8s/deployment.yaml"
  monitoring:
    - "monitoring/service-monitor.yaml"
    - "monitoring/alerts/"
```

## Integrating with CI/CD

### GitHub Actions
The exoskeleton creates `.github/workflows/dod-automation.yml`:

```yaml
name: DoD Automation
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  dod-validation:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [development, staging]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install uvmgr
      run: pip install uvmgr
    - name: Run DoD Automation
      run: uvmgr dod complete --env ${{ matrix.environment }}
      env:
        OTEL_EXPORTER_OTLP_ENDPOINT: ${{ secrets.OTEL_ENDPOINT }}
        OTEL_EXPORTER_OTLP_HEADERS: ${{ secrets.OTEL_HEADERS }}
```

### GitLab CI
For GitLab, use `.gitlab-ci.yml`:

```yaml
stages:
  - dod-validation

dod-automation:
  stage: dod-validation
  image: python:3.11
  before_script:
    - pip install uvmgr
  script:
    - uvmgr dod complete --env $CI_ENVIRONMENT_NAME
  parallel:
    matrix:
      - CI_ENVIRONMENT_NAME: [development, staging, production]
  artifacts:
    reports:
      junit: dod-automation-report.xml
```

## Common Workflows

### Daily Development Workflow
```bash
# 1. Check status before starting work
uvmgr dod status

# 2. Make your changes
git add .
git commit -m "feat: add new feature"

# 3. Run validation before pushing
uvmgr dod validate --criteria testing,security

# 4. Fix any issues
uvmgr dod complete --auto-fix

# 5. Push changes
git push
```

### Release Workflow
```bash
# 1. Comprehensive validation
uvmgr dod complete --env production --detailed

# 2. Generate release pipeline
uvmgr dod pipeline --provider github --environments staging,production

# 3. Create release documentation
uvmgr dod testing --generate-report

# 4. Deploy to staging
git tag v1.0.0
git push origin v1.0.0
```

### Project Onboarding Workflow
```bash
# 1. Clone existing project
git clone https://github.com/your-org/existing-project.git
cd existing-project

# 2. Initialize DoD automation
uvmgr dod exoskeleton --template standard

# 3. Assess current state
uvmgr dod status

# 4. Create improvement plan
uvmgr dod validate --detailed --fix-suggestions

# 5. Implement automation
uvmgr dod complete --auto-fix
```

## Monitoring and Observability

### OpenTelemetry Integration
The DoD system automatically instruments all operations with OpenTelemetry:

```bash
# View traces in your observability platform
# Spans include:
# - dod.create_exoskeleton
# - dod.execute_complete_automation  
# - dod.validate_dod_criteria
# - dod.run_e2e_automation

# Key attributes tracked:
# - dod.environment
# - dod.success_rate
# - dod.execution_time
# - project.path
# - automation.strategy
```

### Health Monitoring
Set up continuous monitoring:

```yaml
# monitoring/dod-health-check.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dod-health-check
data:
  check.sh: |
    #!/bin/bash
    uvmgr dod status --json | jq '.health_score > 80'
```

## Next Steps

1. **Explore Advanced Features**: Learn about [AI-powered insights](./ai-features.md)
2. **Customize Templates**: Create [custom exoskeleton templates](./templates.md)
3. **Monitor Performance**: Set up [comprehensive monitoring](./monitoring.md)
4. **Contribute**: Help improve the system with [contributions](./contributing.md)

## Troubleshooting

### Common Issues

**Issue: "DoD command not found"**
```bash
# Solution: Verify uvmgr installation
pip show uvmgr
uvmgr --version
```

**Issue: "Exoskeleton already exists"**
```bash
# Solution: Use --force flag
uvmgr dod exoskeleton --template standard --force
```

**Issue: "Low test coverage score"**
```bash
# Solution: Check coverage configuration
uvmgr dod validate --criteria testing --detailed
# Adjust thresholds in .uvmgr/dod.yaml
```

**Issue: "OTEL traces not appearing"**
```bash
# Solution: Check telemetry configuration
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
uvmgr dod status
```

For more troubleshooting, see the [Troubleshooting Guide](./troubleshooting.md).

---

**Ready to automate your Definition of Done? Start with `uvmgr dod status` in your project directory!**