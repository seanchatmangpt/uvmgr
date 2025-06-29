# DoD Command Reference

Complete reference for all Definition of Done automation commands.

## Command Overview

| Command | Purpose | Usage |
|---------|---------|--------|
| `dod status` | Show project DoD status overview | Daily status checks |
| `dod complete` | Execute complete DoD automation | Full validation runs |
| `dod validate` | Validate specific DoD criteria | Targeted validation |
| `dod exoskeleton` | Initialize Weaver Forge exoskeleton | Project setup |
| `dod pipeline` | Create DevOps pipeline automation | CI/CD generation |
| `dod testing` | Execute comprehensive testing strategy | Test automation |

---

## `uvmgr dod status`

Show project Definition of Done status overview with health metrics and recommendations.

### Usage
```bash
uvmgr dod status [OPTIONS]
```

### Options
None. This command runs with default settings.

### Output
```
📊 Project DoD Status
╭─────────────────────────── 📊 DoD Status Summary ────────────────────────────╮
│ Overall Health Score: 85.8%                                                  │
│ Status: EXCELLENT                                                            │
│ DoD Compliance: 82.5%                                                        │
│ Security Score: 90.0%                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯

🔧 Recommendations:
   • Improve integration test coverage
   • Add performance benchmarks
   • Update security scanning frequency

Run uvmgr dod complete --auto-fix to address issues
```

### Exit Codes
- `0`: Success
- `1`: Non-critical issues found

### Examples
```bash
# Basic status check
uvmgr dod status

# Use in scripts
if uvmgr dod status; then
  echo "Project health is good"
else
  echo "Project needs attention"
fi
```

---

## `uvmgr dod complete`

Execute complete Definition of Done automation for the entire project using 80/20 principles.

### Usage
```bash
uvmgr dod complete [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--env`, `-e` | TEXT | `development` | Target environment (development, staging, production) |
| `--auto-fix` | FLAG | `False` | Automatically fix issues where possible |
| `--parallel/--sequential` | FLAG | `True` | Run automation steps in parallel |

### Examples
```bash
# Basic complete automation
uvmgr dod complete

# Production environment with auto-fix
uvmgr dod complete --env production --auto-fix

# Sequential execution for debugging
uvmgr dod complete --sequential

# Development environment (explicit)
uvmgr dod complete --env development
```

### Output
```
🎯 Definition of Done Automation
            DoD Results            
┏━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ Criteria      ┃ Status  ┃ Score ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ Testing       │ ✅ PASS │ 97.0% │
│ Security      │ ✅ PASS │ 94.0% │
│ Devops        │ ✅ PASS │ 97.0% │
│ Code_Quality  │ ✅ PASS │ 85.0% │
│ Documentation │ ✅ PASS │ 87.0% │
│ Performance   │ ✅ PASS │ 85.0% │
│ Compliance    │ ✅ PASS │ 89.0% │
└───────────────┴─────────┴───────┘

✅ DoD automation completed successfully!
```

### Exit Codes
- `0`: All criteria passed
- `1`: One or more criteria failed

### Environment-Specific Behavior
- **development**: Lenient thresholds, detailed feedback
- **staging**: Production-like validation, comprehensive testing  
- **production**: Strict thresholds, complete security scanning

---

## `uvmgr dod validate`

Validate specific Definition of Done criteria with detailed analysis and recommendations.

### Usage
```bash
uvmgr dod validate [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--criteria`, `-c` | TEXT | All criteria | Specific criteria to validate (can be used multiple times) |
| `--detailed` | FLAG | `False` | Include detailed validation results |

### Available Criteria
- `testing` - Unit, integration, and E2E test coverage
- `security` - Vulnerability scanning and compliance
- `devops` - CI/CD pipelines and deployment automation
- `code_quality` - Linting, complexity, maintainability
- `documentation` - API docs, user guides, architecture
- `performance` - Benchmarks and optimization
- `compliance` - Regulatory and governance

### Examples
```bash
# Validate all criteria
uvmgr dod validate

# Validate specific criteria
uvmgr dod validate --criteria testing

# Multiple criteria with details
uvmgr dod validate --criteria testing,security --detailed

# Validate critical criteria only
uvmgr dod validate --criteria testing,security,devops
```

### Output
```
✅ DoD Criteria Validation
           Validation Results           
┏━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ Criteria      ┃ Score   ┃ Status  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ Testing       │ 92.0%   │ ✅ PASS │
│ Security      │ 88.0%   │ ✅ PASS │
│ Code_Quality  │ 76.0%   │ ✅ PASS │
└───────────────┴─────────┴─────────┘

📊 Overall Score: 85.3%
✅ All validations passed!
```

### Exit Codes
- `0`: Validation completed (check output for pass/fail status)

---

## `uvmgr dod exoskeleton`

Initialize Weaver Forge exoskeleton for complete project automation framework.

### Usage
```bash
uvmgr dod exoskeleton [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--template`, `-t` | TEXT | `standard` | Exoskeleton template (standard, enterprise, ai-native) |
| `--force` | FLAG | `False` | Overwrite existing exoskeleton |

### Templates

#### Standard Template
Basic automation for typical projects:
- Basic CI/CD workflows
- Standard testing framework
- Security scanning
- Documentation generation

#### Enterprise Template  
Advanced governance and compliance:
- Multi-environment pipelines
- Comprehensive security hardening
- Governance and audit trails
- Compliance automation
- Advanced monitoring

#### AI-Native Template
Cutting-edge AI integration:
- Intelligent CI/CD workflows
- AI-powered testing
- Autonomous security
- Self-healing capabilities
- Predictive analysis

### Examples
```bash
# Initialize with standard template
uvmgr dod exoskeleton

# Enterprise template for production systems
uvmgr dod exoskeleton --template enterprise

# Force overwrite existing exoskeleton
uvmgr dod exoskeleton --template ai-native --force
```

### Output
```
🏗️ Initializing Weaver Forge Exoskeleton
✅ Exoskeleton initialized successfully!
📁 Created 12 files:
   📄 .uvmgr/exoskeleton/config.yaml
   📄 .uvmgr/automation/workflows/dod-automation.yaml
   📄 .github/workflows/dod-automation.yml
   📄 tests/automation/
   📄 monitoring/otel-config.yaml
```

### Files Created
```
.uvmgr/
├── exoskeleton/
│   ├── config.yaml              # Main configuration
│   └── templates/               # Custom templates
├── automation/
│   ├── workflows/               # BPMN workflows
│   └── scripts/                 # Automation scripts
.github/workflows/               # CI/CD pipelines
tests/automation/                # Test automation
monitoring/                      # Observability config
```

### Exit Codes
- `0`: Exoskeleton created successfully
- `1`: Creation failed (check error message)

---

## `uvmgr dod pipeline`

Create comprehensive DevOps pipelines with DoD automation integration.

### Usage
```bash
uvmgr dod pipeline [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--provider`, `-p` | TEXT | `github` | CI/CD provider (github, gitlab, azure) |
| `--environments`, `-e` | TEXT | `dev,staging,prod` | Target environments (comma-separated) |

### Supported Providers
- **github** - GitHub Actions workflows
- **gitlab** - GitLab CI/CD pipelines  
- **azure** - Azure DevOps pipelines

### Examples
```bash
# GitHub Actions pipeline
uvmgr dod pipeline --provider github

# GitLab CI with custom environments
uvmgr dod pipeline --provider gitlab --environments dev,staging,production

# Azure DevOps pipeline
uvmgr dod pipeline --provider azure --environments development,production
```

### Output
```
🚀 DevOps Pipeline Creation
✅ Pipeline created successfully!
📁 Provider: github
🌍 Environments: dev, staging, prod
📄 Files created:
   .github/workflows/dod-automation.yml
   .github/workflows/continuous-validation.yml
```

### Generated Pipeline Features
- Multi-environment deployment
- Automated testing (unit, integration, E2E)
- Security scanning and compliance
- Performance testing
- Automated rollback mechanisms
- OpenTelemetry instrumentation

### Exit Codes
- `0`: Pipeline created successfully
- `1`: Creation failed

---

## `uvmgr dod testing`

Execute comprehensive testing strategy with E2E automation.

### Usage
```bash
uvmgr dod testing [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy`, `-s` | TEXT | `comprehensive` | Testing strategy (comprehensive, smoke, regression) |
| `--coverage`, `-c` | INTEGER | `80` | Minimum coverage threshold |
| `--parallel/--sequential` | FLAG | `True` | Run tests in parallel |

### Testing Strategies
- **comprehensive** - Full test suite (unit, integration, E2E, performance)
- **smoke** - Basic functionality tests
- **regression** - Changed areas only

### Examples
```bash
# Comprehensive testing
uvmgr dod testing

# Smoke tests with lower coverage
uvmgr dod testing --strategy smoke --coverage 60

# Sequential execution for debugging
uvmgr dod testing --sequential

# High coverage threshold
uvmgr dod testing --coverage 95
```

### Output
```
🧪 Comprehensive Testing
            Test Results            
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Test Type       ┃ Coverage ┃ Status  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ Browser_Tests   │ 23/25    │ ✅ PASS │
│ Api_Tests       │ 15/15    │ ✅ PASS │
│ Integration     │ 7/8      │ ❌ FAIL │
└─────────────────┴──────────┴─────────┘

✅ All tests passed!
```

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed

---

## Global Options

These options apply to all DoD commands:

| Option | Description |
|--------|-------------|
| `--help` | Show command help |
| `--json` | Output results in JSON format |
| `--debug` | Enable debug logging |
| `--config` | Specify custom config file |

### Examples
```bash
# Get help for any command
uvmgr dod complete --help

# JSON output for scripting
uvmgr dod status --json

# Debug mode for troubleshooting
uvmgr dod complete --debug

# Custom configuration
uvmgr dod validate --config /path/to/custom-dod.yaml
```

---

## Configuration File Reference

The DoD system uses `.uvmgr/dod.yaml` for configuration:

```yaml
# DoD Configuration Schema
automation:
  enabled: true                    # Enable/disable automation
  level: "supervised"              # autonomous, supervised, manual
  parallel: true                   # Run operations in parallel
  auto_fix: false                  # Automatically fix issues

criteria:
  testing:
    enabled: true
    coverage_threshold: 80
    types: ["unit", "integration", "e2e"]
    frameworks: ["pytest", "jest"]
    
  security:
    enabled: true
    scan_dependencies: true
    vulnerability_threshold: "medium"  # low, medium, high, critical
    tools: ["bandit", "safety", "semgrep"]
    
  devops:
    enabled: true
    provider: "github"              # github, gitlab, azure
    environments: ["dev", "staging", "production"]
    features: ["testing", "security", "deployment"]
    
  code_quality:
    enabled: true
    linting: true
    complexity_threshold: 10
    tools: ["ruff", "mypy", "black"]
    
  documentation:
    enabled: true
    formats: ["markdown", "sphinx"]
    coverage_threshold: 70
    
  performance:
    enabled: false
    benchmarks: true
    load_testing: false
    
  compliance:
    enabled: false
    standards: ["sox", "pci", "gdpr"]

# AI-powered features
ai:
  enabled: true
  insights: true
  auto_optimization: false
  features: ["code_review", "test_generation", "security_advisory"]

# OpenTelemetry configuration  
telemetry:
  enabled: true
  endpoint: "http://localhost:4317"
  service_name: "my-project-dod"
  attributes:
    environment: "development"
    team: "platform"
    version: "1.0.0"

# Template configuration
templates:
  default: "standard"
  custom_templates_dir: ".uvmgr/templates"
  
# Notification configuration
notifications:
  enabled: false
  slack_webhook: ""
  email_recipients: []
```

---

## Scripting and Automation

### Bash Scripting
```bash
#!/bin/bash
# DoD automation script

set -e

echo "Running DoD automation..."

# Check current status
if ! uvmgr dod status --json | jq -e '.health_score > 80'; then
  echo "Health score too low, running complete automation..."
  uvmgr dod complete --auto-fix
fi

# Validate critical criteria
uvmgr dod validate --criteria testing,security,devops

echo "DoD automation completed successfully!"
```

### Python Integration
```python
import subprocess
import json

def run_dod_automation():
    """Run DoD automation and return results."""
    result = subprocess.run(
        ['uvmgr', 'dod', 'status', '--json'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        status = json.loads(result.stdout)
        return status['health_score']
    else:
        raise Exception(f"DoD automation failed: {result.stderr}")

# Usage
health_score = run_dod_automation()
print(f"Project health: {health_score}%")
```

### CI/CD Integration
```yaml
# Example GitHub Actions step
- name: Run DoD Automation
  run: |
    uvmgr dod complete --env ${{ github.ref_name == 'main' && 'production' || 'staging' }}
    uvmgr dod status --json > dod-report.json
  env:
    OTEL_EXPORTER_OTLP_ENDPOINT: ${{ secrets.OTEL_ENDPOINT }}
    
- name: Upload DoD Report
  uses: actions/upload-artifact@v3
  with:
    name: dod-report
    path: dod-report.json
```

---

## Exit Codes Summary

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success - all operations completed successfully |
| `1` | Failure - one or more criteria failed or issues found |
| `2` | Error - command execution error or invalid arguments |

---

For more detailed information, see:
- [Configuration Guide](./configuration.md)
- [Architecture Overview](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)