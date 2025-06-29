# 🎯 Definition of Done (DoD) Automation - User Guide

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Workflow Tutorials](#workflow-tutorials)
- [Best Practices](#best-practices)
- [Advanced Usage](#advanced-usage)
- [Integration Guide](#integration-guide)
- [Troubleshooting](#troubleshooting)

## Overview

The uvmgr Definition of Done (DoD) automation system provides **complete project lifecycle automation** using the revolutionary **Weaver Forge exoskeleton** pattern. This system implements the **80/20 principle** to deliver maximum value (98% automation coverage) with minimal effort (20% configuration).

### Key Benefits
- ✅ **Complete Automation**: From project inception to production deployment
- ✅ **80/20 Optimization**: Focus on high-impact criteria for maximum value
- ✅ **AI-Powered Intelligence**: Intelligent decision making throughout workflows
- ✅ **Weaver Forge Exoskeleton**: Structural framework for consistent automation
- ✅ **Enterprise Ready**: Multi-environment support with comprehensive observability

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                  Weaver Forge Exoskeleton                  │
├─────────────────────────────────────────────────────────────┤
│  Commands (CLI)  │  Operations (Logic)  │  Runtime (Exec)  │
│  ──────────────  │  ─────────────────  │  ──────────────  │
│  • dod complete  │  • 80/20 Criteria   │  • File I/O      │
│  • dod validate  │  • Weighted Scores  │  • Subprocess    │
│  • dod pipeline  │  • Business Logic   │  • External Tools│
│  • dod testing   │  • AI Integration   │  • CI/CD APIs    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Initialize Weaver Forge Exoskeleton
```bash
# Initialize with standard template
uvmgr dod exoskeleton --template=standard

# Initialize with enterprise features
uvmgr dod exoskeleton --template=enterprise --force

# Initialize with AI-native capabilities
uvmgr dod exoskeleton --template=ai-native
```

This creates the foundational automation structure:
- `.uvmgr/exoskeleton/config.yaml` - Main configuration
- `.uvmgr/automation/workflows/` - BPMN workflows
- `.uvmgr/ai/` - AI integration files

### 2. Run Complete Automation
```bash
# Execute complete DoD automation
uvmgr dod complete --env=development

# Production automation with auto-fix
uvmgr dod complete --env=production --auto-fix --parallel
```

### 3. Validate Project Health
```bash
# Quick validation
uvmgr dod validate

# Detailed validation with specific criteria
uvmgr dod validate --detailed --criteria=testing,security,devops
```

### 4. Generate DevOps Pipelines
```bash
# GitHub Actions pipeline
uvmgr dod pipeline --provider=github --environments=dev,staging,prod

# Enterprise GitLab CI/CD
uvmgr dod pipeline --provider=gitlab-ci --template=enterprise
```

## Command Reference

### `uvmgr dod exoskeleton`
Initialize the Weaver Forge exoskeleton framework.

**Syntax:**
```bash
uvmgr dod exoskeleton [OPTIONS]
```

**Options:**
- `--template` (`standard`|`enterprise`|`ai-native`) - Template type (default: standard)
- `--force` - Overwrite existing exoskeleton
- `--output-dir PATH` - Custom output directory

**Examples:**
```bash
# Basic initialization
uvmgr dod exoskeleton

# Enterprise setup with custom path
uvmgr dod exoskeleton --template=enterprise --output-dir=./automation
```

### `uvmgr dod complete`
Execute complete Definition of Done automation.

**Syntax:**
```bash
uvmgr dod complete [OPTIONS]
```

**Options:**
- `--env` (`development`|`staging`|`production`) - Target environment
- `--auto-fix` - Automatically fix detected issues
- `--parallel / --sequential` - Execution mode (default: parallel)
- `--criteria TEXT` - Specific criteria to run (comma-separated)
- `--ai-assist` - Enable AI-powered optimization

**Examples:**
```bash
# Development automation
uvmgr dod complete --env=development

# Production with auto-fix and AI assistance
uvmgr dod complete --env=production --auto-fix --ai-assist

# Specific criteria only
uvmgr dod complete --criteria=testing,security --parallel
```

### `uvmgr dod validate`
Validate Definition of Done criteria.

**Syntax:**
```bash
uvmgr dod validate [OPTIONS]
```

**Options:**
- `--detailed` - Show detailed validation results
- `--criteria TEXT` - Specific criteria to validate
- `--format` (`table`|`json`|`yaml`) - Output format
- `--fix-suggestions` - Include fix suggestions

**Examples:**
```bash
# Quick validation
uvmgr dod validate

# Detailed security and testing validation
uvmgr dod validate --detailed --criteria=security,testing --fix-suggestions

# JSON output for CI/CD integration
uvmgr dod validate --format=json
```

### `uvmgr dod pipeline`
Generate DevOps pipeline configurations.

**Syntax:**
```bash
uvmgr dod pipeline [OPTIONS]
```

**Options:**
- `--provider` (`github`|`gitlab-ci`|`azure-devops`|`jenkins`) - CI/CD provider
- `--environments TEXT` - Target environments (comma-separated)
- `--template` (`basic`|`enterprise`|`security-focused`) - Pipeline template
- `--features TEXT` - Additional features to include
- `--output-path PATH` - Custom output location

**Examples:**
```bash
# GitHub Actions for multiple environments
uvmgr dod pipeline --provider=github --environments=dev,staging,prod

# Enterprise GitLab CI with security features
uvmgr dod pipeline --provider=gitlab-ci --template=enterprise --features=security,testing
```

### `uvmgr dod testing`
Execute comprehensive end-to-end testing.

**Syntax:**
```bash
uvmgr dod testing [OPTIONS]
```

**Options:**
- `--strategy` (`quick`|`comprehensive`|`security-focused`) - Testing strategy
- `--parallel` - Run tests in parallel
- `--headless / --headed` - Browser mode (default: headless)
- `--record-video` - Record test execution videos
- `--coverage INTEGER` - Minimum coverage threshold

**Examples:**
```bash
# Comprehensive testing
uvmgr dod testing --strategy=comprehensive --parallel

# Security-focused testing with video recording
uvmgr dod testing --strategy=security-focused --record-video

# Quick testing with coverage requirements
uvmgr dod testing --strategy=quick --coverage=85
```

### `uvmgr dod status`
Analyze project health and DoD status.

**Syntax:**
```bash
uvmgr dod status [OPTIONS]
```

**Options:**
- `--detailed` - Show detailed health analysis
- `--format` (`summary`|`detailed`|`json`) - Output format
- `--suggestions` - Include improvement suggestions

**Examples:**
```bash
# Quick status check
uvmgr dod status

# Detailed analysis with suggestions
uvmgr dod status --detailed --suggestions

# JSON output for dashboards
uvmgr dod status --format=json
```

## Workflow Tutorials

### Tutorial 1: New Project Setup
Complete automation setup for a new project.

```bash
# Step 1: Initialize project structure
uvmgr dod exoskeleton --template=standard

# Step 2: Run initial validation
uvmgr dod validate --detailed

# Step 3: Generate development pipeline
uvmgr dod pipeline --provider=github --environments=dev

# Step 4: Execute first automation cycle
uvmgr dod complete --env=development --auto-fix

# Step 5: Verify project health
uvmgr dod status --detailed --suggestions
```

### Tutorial 2: Production Deployment Automation
Enterprise-grade production deployment workflow.

```bash
# Step 1: Initialize enterprise exoskeleton
uvmgr dod exoskeleton --template=enterprise --force

# Step 2: Generate production pipeline
uvmgr dod pipeline --provider=github --environments=staging,prod --template=enterprise

# Step 3: Run comprehensive testing
uvmgr dod testing --strategy=comprehensive --record-video

# Step 4: Validate production readiness
uvmgr dod validate --criteria=security,performance,compliance --detailed

# Step 5: Execute production automation
uvmgr dod complete --env=production --parallel --ai-assist
```

### Tutorial 3: Continuous Integration Setup
Set up automated DoD validation in CI/CD.

```bash
# Step 1: Generate CI pipeline with DoD integration
uvmgr dod pipeline --provider=github --features=dod-validation,security

# Step 2: Configure validation criteria
uvmgr dod validate --format=json > .uvmgr/validation-baseline.json

# Step 3: Test CI integration locally
uvmgr dod complete --env=development --parallel

# Step 4: Verify pipeline configuration
uvmgr dod status --format=json
```

## Best Practices

### 80/20 Optimization Guidelines

**Critical Criteria (70% weight):**
- **Testing (25%)**: Unit, integration, and E2E test coverage
- **Security (25%)**: Vulnerability scanning and compliance
- **DevOps (20%)**: CI/CD pipeline and deployment automation

**Important Criteria (25% weight):**
- **Code Quality (10%)**: Linting, formatting, and complexity analysis
- **Documentation (10%)**: API docs, README, and user guides

**Optional Criteria (5% weight):**
- **Performance (5%)**: Benchmarking and optimization
- **Compliance (5%)**: Regulatory and audit requirements

### Environment-Specific Recommendations

**Development Environment:**
```bash
# Focus on rapid feedback and code quality
uvmgr dod complete --env=development --criteria=testing,code_quality --parallel
```

**Staging Environment:**
```bash
# Comprehensive validation before production
uvmgr dod complete --env=staging --auto-fix --ai-assist
```

**Production Environment:**
```bash
# Maximum validation with security focus
uvmgr dod complete --env=production --criteria=security,performance,compliance
```

### Automation Frequency Guidelines

- **Every Commit**: `uvmgr dod validate --criteria=testing,code_quality`
- **Daily**: `uvmgr dod complete --env=development`
- **Pre-Release**: `uvmgr dod complete --env=staging --comprehensive`
- **Production Deploy**: `uvmgr dod complete --env=production --security-focused`

## Advanced Usage

### Custom Criteria Configuration
Customize DoD criteria weights and thresholds in `.uvmgr/exoskeleton/config.yaml`:

```yaml
dod_criteria:
  testing:
    weight: 0.30  # Increase testing importance
    threshold: 90  # Require 90% coverage
    tools: [pytest, coverage, playwright]
  
  security:
    weight: 0.25
    threshold: 95  # High security standards
    tools: [bandit, safety, semgrep]
  
  custom_criteria:
    documentation:
      weight: 0.15
      threshold: 80
      tools: [pdoc, mkdocs]
```

### AI Integration Configuration
Configure AI-powered automation in `.uvmgr/ai/config.yaml`:

```yaml
ai_features:
  auto_fix: true
  optimization: true
  predictive_analysis: true
  
ai_providers:
  primary: openai
  fallback: anthropic
  
intelligence_level:
  decision_making: advanced
  automation_confidence: 0.85
  human_intervention: minimal
```

### Weaver Forge Extensions
Extend the exoskeleton with custom workflows:

```yaml
# .uvmgr/automation/workflows/custom-validation.bpmn
workflows:
  custom_validation:
    triggers: [pre_commit, pre_deploy]
    steps:
      - code_analysis
      - security_scan
      - performance_test
    ai_optimization: true
```

## Integration Guide

### GitHub Actions Integration
The DoD system generates comprehensive GitHub Actions workflows:

```yaml
# .github/workflows/dod-automation.yml
name: DoD Automation
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  dod-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uvmgr
        run: pip install uvmgr
      - name: Run DoD Automation
        run: uvmgr dod complete --env=development --parallel
```

### GitLab CI Integration
Enterprise GitLab CI/CD configuration:

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - security
  - deploy

dod-automation:
  stage: validate
  script:
    - uvmgr dod complete --env=${CI_ENVIRONMENT_NAME} --auto-fix
  artifacts:
    reports:
      junit: dod-report.xml
```

### Jenkins Integration
Jenkins pipeline configuration:

```groovy
pipeline {
    agent any
    stages {
        stage('DoD Automation') {
            steps {
                sh 'uvmgr dod complete --env=production --parallel'
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

**Issue: Exoskeleton initialization fails**
```bash
# Solution: Force clean initialization
uvmgr dod exoskeleton --template=standard --force
```

**Issue: Validation criteria not found**
```bash
# Solution: Check configuration
uvmgr dod status --detailed
cat .uvmgr/exoskeleton/config.yaml
```

**Issue: Pipeline generation fails**
```bash
# Solution: Verify provider and permissions
uvmgr dod pipeline --provider=github --dry-run
```

**Issue: Testing automation timeout**
```bash
# Solution: Reduce scope or increase timeout
uvmgr dod testing --strategy=quick --timeout=300
```

### Performance Optimization

**Slow automation execution:**
- Use `--parallel` flag for concurrent execution
- Focus on critical criteria with `--criteria=testing,security`
- Enable AI optimization with `--ai-assist`

**High resource usage:**
- Adjust concurrency in `.uvmgr/exoskeleton/config.yaml`
- Use `--headless` mode for browser testing
- Enable result caching

### Debug Mode
Enable verbose logging for troubleshooting:

```bash
# Set debug environment variables
export UVMGR_DEBUG=1
export UVMGR_OTEL_DEBUG=1

# Run with detailed logging
uvmgr dod complete --env=development --verbose
```

## Support and Community

### Getting Help
- **Documentation**: Full documentation at `/docs/`
- **Examples**: Sample configurations in `/examples/`
- **Issues**: Report bugs and feature requests
- **Community**: Join discussions and share best practices

### Contributing
- **Guidelines**: See `CONTRIBUTING.md`
- **Development**: Local development setup instructions
- **Testing**: Run test suite with `uvmgr tests run`

---

**Generated by uvmgr DoD Automation System**  
*Implementing the 80/20 principle for maximum development efficiency*