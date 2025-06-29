# DoD API Reference

Complete API reference for the Definition of Done automation system, including Python APIs, configuration schemas, and integration interfaces.

## Table of Contents
- [Python API](#python-api)
- [Configuration Schema](#configuration-schema)
- [Extension APIs](#extension-apis)
- [REST API](#rest-api)
- [CLI Integration](#cli-integration)
- [Error Handling](#error-handling)

## Python API

### Core Operations Module (`uvmgr.ops.dod`)

#### `create_exoskeleton()`

Create Weaver Forge exoskeleton for project automation.

```python
def create_exoskeleton(
    project_path: Path,
    template: str = "standard",
    force: bool = False,
    preview: bool = False
) -> Dict[str, Any]:
    """
    Create Weaver Forge exoskeleton for complete project automation.
    
    Args:
        project_path: Path to project root directory
        template: Exoskeleton template ('standard', 'enterprise', 'ai-native')
        force: Overwrite existing exoskeleton if present
        preview: Preview structure without creating files
        
    Returns:
        Dict containing:
        - success (bool): Operation success status
        - files_created (List[Dict]): Created files with metadata
        - workflows_created (List[str]): Created workflow names
        - ai_integrations (List[str]): Enabled AI features
        - error (str): Error message if success=False
        
    Raises:
        ValueError: Invalid template name
        PermissionError: Insufficient permissions for file creation
        
    Example:
        >>> from uvmgr.ops.dod import create_exoskeleton
        >>> from pathlib import Path
        >>> 
        >>> result = create_exoskeleton(
        ...     project_path=Path("/project"),
        ...     template="enterprise",
        ...     force=True
        ... )
        >>> if result["success"]:
        ...     print(f"Created {len(result['files_created'])} files")
    """
```

#### `execute_complete_automation()`

Execute complete DoD automation workflow.

```python
def execute_complete_automation(
    project_path: Path,
    environment: str = "development",
    criteria: Optional[List[str]] = None,
    skip_tests: bool = False,
    skip_security: bool = False,
    auto_fix: bool = False,
    parallel: bool = True,
    ai_assist: bool = True
) -> Dict[str, Any]:
    """
    Execute complete Definition of Done automation for entire project.
    
    Args:
        project_path: Path to project root
        environment: Target environment ('development', 'staging', 'production')
        criteria: Specific criteria to validate (None = all)
        skip_tests: Skip automated testing
        skip_security: Skip security validation
        auto_fix: Automatically fix issues where possible
        parallel: Run automation steps in parallel
        ai_assist: Enable AI-powered automation assistance
        
    Returns:
        Dict containing:
        - success (bool): Overall operation success
        - overall_success_rate (float): Weighted success rate (0.0-1.0)
        - execution_time (float): Execution duration in seconds
        - criteria_results (Dict[str, Dict]): Per-criterion results
        - criteria_executed (List[str]): List of executed criteria
        - automation_strategy (str): Strategy used ("80/20")
        - error (str): Error message if success=False
        
    Example:
        >>> result = execute_complete_automation(
        ...     project_path=Path("/project"),
        ...     environment="production",
        ...     auto_fix=True,
        ...     parallel=True
        ... )
        >>> print(f"Success rate: {result['overall_success_rate']:.1%}")
    """
```

#### `validate_dod_criteria()`

Validate specific DoD criteria with detailed analysis.

```python
def validate_dod_criteria(
    project_path: Path,
    criteria: Optional[List[str]] = None,
    detailed: bool = False,
    fix_suggestions: bool = True
) -> Dict[str, Any]:
    """
    Validate current Definition of Done criteria with 80/20 scoring.
    
    Args:
        project_path: Path to project root
        criteria: Specific criteria to validate (None = all)
        detailed: Include detailed validation results
        fix_suggestions: Generate AI-powered fix suggestions
        
    Returns:
        Dict containing:
        - success (bool): Validation operation success
        - overall_score (float): Weighted overall score (0.0-100.0)
        - critical_score (float): Average score of critical criteria
        - important_score (float): Average score of important criteria
        - criteria_scores (Dict[str, Dict]): Per-criterion scores and details
        - scoring_strategy (str): Scoring method ("80/20 weighted")
        - criteria_weights (Dict): Applied weights per criterion
        
    Example:
        >>> result = validate_dod_criteria(
        ...     project_path=Path("/project"),
        ...     criteria=["testing", "security"],
        ...     detailed=True
        ... )
        >>> for criterion, details in result["criteria_scores"].items():
        ...     print(f"{criterion}: {details['score']:.1f}%")
    """
```

#### `generate_devops_pipeline()`

Generate comprehensive DevOps pipelines with DoD automation.

```python
def generate_devops_pipeline(
    project_path: Path,
    provider: str = "github-actions",
    environments: List[str] = None,
    features: List[str] = None,
    template: str = "standard",
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive DevOps pipelines with DoD automation.
    
    Args:
        project_path: Path to project root
        provider: CI/CD provider ('github-actions', 'gitlab-ci', 'azure-devops')
        environments: Target environments (default: ['dev', 'staging', 'production'])
        features: Pipeline features (default: ['testing', 'security', 'deployment'])
        template: Pipeline template ('standard', 'enterprise', 'security-first')
        output_path: Custom output path for pipeline files
        
    Returns:
        Dict containing:
        - success (bool): Generation success status
        - provider (str): CI/CD provider used
        - files_created (List[str]): Created pipeline files
        - features_enabled (List[str]): Enabled pipeline features
        - environments_configured (List[str]): Configured environments
        
    Example:
        >>> result = generate_devops_pipeline(
        ...     project_path=Path("/project"),
        ...     provider="github-actions",
        ...     environments=["staging", "production"],
        ...     features=["testing", "security", "deployment"]
        ... )
    """
```

#### `analyze_project_status()`

Analyze complete project status and automation health.

```python
def analyze_project_status(
    project_path: Path,
    detailed: bool = False,
    suggestions: bool = True
) -> Dict[str, Any]:
    """
    Analyze complete project status and automation health.
    
    Args:
        project_path: Path to project root
        detailed: Include detailed project analysis
        suggestions: Generate AI-powered improvement suggestions
        
    Returns:
        Dict containing:
        - success (bool): Analysis success status
        - health_score (float): Overall project health (0.0-100.0)
        - dod_status (Dict): DoD compliance metrics
        - automation_health (Dict): Automation system health
        - security_posture (Dict): Security assessment
        - code_quality (Dict): Code quality metrics
        - suggestions (List[str]): Improvement recommendations
        - health_components (Dict): Weighted health components
        
    Example:
        >>> status = analyze_project_status(
        ...     project_path=Path("/project"),
        ...     detailed=True
        ... )
        >>> print(f"Health: {status['health_score']:.1f}%")
        >>> for suggestion in status['suggestions']:
        ...     print(f"- {suggestion}")
    """
```

### Runtime Module (`uvmgr.runtime.dod`)

#### `execute_automation_workflow()`

Execute automation workflow with infrastructure operations.

```python
def execute_automation_workflow(
    project_path: Path,
    criteria: List[str],
    environment: str,
    auto_fix: bool,
    parallel: bool,
    ai_assist: bool
) -> Dict[str, Any]:
    """
    Execute complete automation workflow with real infrastructure.
    
    Args:
        project_path: Path to project root
        criteria: List of criteria to execute
        environment: Target environment
        auto_fix: Enable automatic issue fixing
        parallel: Execute criteria in parallel
        ai_assist: Enable AI assistance
        
    Returns:
        Dict containing execution results for each criterion
        
    Example:
        >>> result = execute_automation_workflow(
        ...     project_path=Path("/project"),
        ...     criteria=["testing", "security"],
        ...     environment="development",
        ...     auto_fix=False,
        ...     parallel=True,
        ...     ai_assist=True
        ... )
    """
```

### Constants and Enums

#### DoD Criteria Weights

```python
from uvmgr.ops.dod import DOD_CRITERIA_WEIGHTS

# Access criteria configuration
DOD_CRITERIA_WEIGHTS = {
    "testing": {"weight": 0.25, "priority": "critical"},
    "security": {"weight": 0.25, "priority": "critical"},
    "devops": {"weight": 0.20, "priority": "critical"},
    "code_quality": {"weight": 0.10, "priority": "important"},
    "documentation": {"weight": 0.10, "priority": "important"},
    "performance": {"weight": 0.05, "priority": "optional"},
    "compliance": {"weight": 0.05, "priority": "optional"}
}

# Example usage
critical_criteria = [
    name for name, config in DOD_CRITERIA_WEIGHTS.items()
    if config["priority"] == "critical"
]
```

#### Exoskeleton Templates

```python
from uvmgr.ops.dod import EXOSKELETON_TEMPLATES

# Available templates
EXOSKELETON_TEMPLATES = {
    "standard": {
        "description": "Standard DoD automation for typical projects",
        "includes": ["basic_ci", "testing", "security_scan", "docs"],
        "ai_features": ["code_review", "test_generation"]
    },
    "enterprise": {
        "description": "Enterprise-grade automation with governance",
        "includes": ["advanced_ci", "multi_env", "security_hardened", "compliance"],
        "ai_features": ["architecture_analysis", "security_advisory"]
    },
    "ai-native": {
        "description": "AI-first automation with cutting-edge capabilities",
        "includes": ["intelligent_ci", "ai_testing", "autonomous_security"],
        "ai_features": ["autonomous_development", "predictive_analysis"]
    }
}
```

## Configuration Schema

### DoD Configuration (`dod.yaml`)

```yaml
# Complete configuration schema with types and defaults
automation:
  enabled: true                    # bool: Enable DoD automation
  level: "supervised"              # str: "autonomous" | "supervised" | "manual"
  parallel: true                   # bool: Parallel execution
  auto_fix: false                  # bool: Automatic issue fixing
  timeout: 3600                    # int: Global timeout in seconds

criteria:
  testing:
    enabled: true                  # bool: Enable testing criteria
    coverage_threshold: 80         # int: Minimum coverage percentage
    types:                         # List[str]: Test types to run
      - "unit"
      - "integration" 
      - "e2e"
    frameworks:                    # List[str]: Testing frameworks
      - "pytest"
      - "jest"
    parallel: true                 # bool: Parallel test execution
    
  security:
    enabled: true                  # bool: Enable security criteria
    scan_dependencies: true        # bool: Scan dependencies
    vulnerability_threshold: "medium"  # str: "low" | "medium" | "high" | "critical"
    tools:                         # List[str]: Security tools
      - "bandit"
      - "safety"
      - "semgrep"
    auto_fix: false               # bool: Auto-fix security issues
    
  devops:
    enabled: true                  # bool: Enable DevOps criteria
    provider: "github"             # str: "github" | "gitlab" | "azure"
    environments:                  # List[str]: Target environments
      - "development"
      - "staging"
      - "production"
    features:                      # List[str]: Pipeline features
      - "testing"
      - "security"
      - "deployment"
      - "monitoring"
    
  code_quality:
    enabled: true                  # bool: Enable code quality criteria
    linting: true                  # bool: Enable linting
    formatting: true               # bool: Enable formatting
    complexity_threshold: 10       # int: Maximum complexity
    tools:                         # List[str]: Quality tools
      - "ruff"
      - "mypy"
      - "black"
    
  documentation:
    enabled: true                  # bool: Enable documentation criteria
    formats:                       # List[str]: Documentation formats
      - "markdown"
      - "sphinx"
    coverage_threshold: 70         # int: Documentation coverage percentage
    auto_generate: false           # bool: Auto-generate docs
    
  performance:
    enabled: false                 # bool: Enable performance criteria
    benchmarks: true               # bool: Run benchmarks
    load_testing: false            # bool: Run load tests
    threshold_degradation: 0.1     # float: Max performance degradation
    
  compliance:
    enabled: false                 # bool: Enable compliance criteria
    standards:                     # List[str]: Compliance standards
      - "sox"
      - "pci"
      - "gdpr"
    audit_trail: true              # bool: Generate audit trail

# AI configuration
ai:
  enabled: true                    # bool: Enable AI features
  insights: true                   # bool: Generate AI insights
  auto_optimization: false         # bool: Autonomous optimization
  features:                        # List[str]: AI features
    - "code_review"
    - "test_generation"
    - "security_advisory"
  model:
    provider: "openai"             # str: AI provider
    model_name: "gpt-4"            # str: Model name
    temperature: 0.1               # float: Model temperature
    max_tokens: 2048               # int: Max response tokens

# OpenTelemetry configuration
telemetry:
  enabled: true                    # bool: Enable telemetry
  endpoint: "http://localhost:4317"  # str: OTLP endpoint
  protocol: "grpc"                 # str: "grpc" | "http"
  service_name: "uvmgr-dod"        # str: Service name
  service_version: "2.1.0"         # str: Service version
  service_namespace: "automation"   # str: Service namespace
  compression: "gzip"              # str: Compression type
  timeout: 30                      # int: Export timeout
  attributes:                      # Dict[str, str]: Resource attributes
    environment: "development"
    team: "platform"
    component: "dod-automation"

# Template configuration
templates:
  default: "standard"              # str: Default template
  custom_templates_dir: ".uvmgr/templates"  # str: Custom templates directory
  template_registry: "local"       # str: "local" | "remote"

# Notification configuration
notifications:
  enabled: false                   # bool: Enable notifications
  channels:                        # List[str]: Notification channels
    - "slack"
    - "email"
  slack:
    webhook_url: ""                # str: Slack webhook URL
    channel: "#automation"         # str: Slack channel
  email:
    smtp_server: ""                # str: SMTP server
    recipients: []                 # List[str]: Email recipients

# Environment overrides
environments:
  development:
    criteria:
      testing:
        coverage_threshold: 70     # Lower threshold for dev
      security:
        vulnerability_threshold: "high"  # Less strict for dev
        
  staging:
    criteria:
      testing:
        coverage_threshold: 85     # Higher for staging
      performance:
        enabled: true              # Enable performance testing
        
  production:
    criteria:
      testing:
        coverage_threshold: 90     # Highest for production
      security:
        vulnerability_threshold: "low"  # Most strict
      compliance:
        enabled: true              # Enable compliance
    ai:
      auto_optimization: false     # Disable auto-optimization
```

## Extension APIs

### Custom Criteria Registration

```python
from uvmgr.ops.dod import register_criterion
from typing import Dict, Any
from pathlib import Path

@register_criterion("accessibility", weight=0.05, priority="optional")
def validate_accessibility(
    project_path: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Custom accessibility validation criterion.
    
    Args:
        project_path: Project root directory
        config: Criterion-specific configuration
        
    Returns:
        Dict containing:
        - score (float): Accessibility score (0.0-100.0)
        - passed (bool): Whether criterion passed
        - details (str): Detailed results
        - recommendations (List[str]): Improvement suggestions
    """
    
    # Run accessibility tools (axe-core, lighthouse, etc.)
    # This is where you'd implement actual validation logic
    
    return {
        "score": 85.0,
        "passed": True,
        "details": "WCAG 2.1 AA compliance validated",
        "recommendations": [
            "Add alt text to remaining images",
            "Improve color contrast ratios"
        ]
    }

# Usage
from uvmgr.ops.dod import validate_dod_criteria

result = validate_dod_criteria(
    project_path=Path("/project"),
    criteria=["accessibility"],  # Will use custom criterion
    detailed=True
)
```

### Custom Template Registration

```python
from uvmgr.ops.dod import register_template

@register_template("microservice")
def microservice_template() -> Dict[str, Any]:
    """Custom microservice template with service mesh."""
    
    return {
        "description": "Microservice template with Kubernetes and Istio",
        "includes": [
            "kubernetes_deployment",
            "istio_service_mesh",
            "distributed_tracing",
            "chaos_engineering"
        ],
        "ai_features": [
            "traffic_analysis", 
            "fault_injection",
            "capacity_planning"
        ],
        "structure": {
            "deployment": [
                "k8s/deployment.yaml",
                "k8s/service.yaml", 
                "istio/virtual-service.yaml",
                "istio/destination-rule.yaml"
            ],
            "monitoring": [
                "monitoring/service-monitor.yaml",
                "monitoring/dashboards/service-dashboard.json"
            ],
            "testing": [
                "tests/load/",
                "tests/chaos/"
            ]
        },
        "configuration": {
            "criteria": {
                "performance": {
                    "enabled": True,
                    "load_testing": True
                },
                "devops": {
                    "features": ["testing", "security", "deployment", "monitoring", "chaos"]
                }
            }
        }
    }
```

### AI Integration API

```python
from uvmgr.ai import register_ai_analyzer
import asyncio

@register_ai_analyzer("code_complexity")
async def analyze_code_complexity(
    project_path: Path,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    AI-powered code complexity analysis.
    
    Args:
        project_path: Project root directory
        context: Analysis context and configuration
        
    Returns:
        Dict containing AI analysis results
    """
    
    # Example AI analysis implementation
    files_analyzed = 0
    complexity_hotspots = []
    
    for file_path in project_path.rglob("*.py"):
        # Analyze file complexity with AI
        analysis = await analyze_file_with_ai(file_path)
        files_analyzed += 1
        
        if analysis.complexity_score > 8:
            complexity_hotspots.append({
                "file": str(file_path.relative_to(project_path)),
                "complexity": analysis.complexity_score,
                "suggestions": analysis.suggestions
            })
    
    overall_score = 100 - min(len(complexity_hotspots) * 10, 50)
    
    return {
        "score": overall_score,
        "files_analyzed": files_analyzed,
        "complexity_hotspots": complexity_hotspots,
        "recommendations": generate_complexity_recommendations(complexity_hotspots)
    }

async def analyze_file_with_ai(file_path: Path):
    """Mock AI analysis - replace with actual AI service call."""
    # This would call your LLM service
    await asyncio.sleep(0.1)  # Simulate AI processing
    
    class MockAnalysis:
        complexity_score = 6.5
        suggestions = ["Consider breaking down large functions"]
    
    return MockAnalysis()
```

## REST API

### Authentication

```python
# API key authentication
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
```

### Execute DoD Automation

```http
POST /api/v1/dod/automation
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "project_path": "/path/to/project",
  "environment": "production",
  "criteria": ["testing", "security", "devops"],
  "auto_fix": false,
  "parallel": true,
  "ai_assist": true
}
```

**Response:**
```json
{
  "success": true,
  "overall_success_rate": 0.92,
  "execution_time": 45.2,
  "criteria_results": {
    "testing": {
      "score": 95.0,
      "passed": true,
      "execution_time": 12.3
    },
    "security": {
      "score": 88.0, 
      "passed": true,
      "execution_time": 18.7
    },
    "devops": {
      "score": 94.0,
      "passed": true,
      "execution_time": 14.2
    }
  }
}
```

### Project Status

```http
GET /api/v1/dod/status?project_path=/path/to/project&detailed=true
Authorization: Bearer your-api-key
```

**Response:**
```json
{
  "success": true,
  "health_score": 87.5,
  "dod_status": {
    "overall_score": 85.0,
    "critical_score": 90.0,
    "important_score": 80.0
  },
  "suggestions": [
    "Improve integration test coverage",
    "Add performance benchmarks"
  ]
}
```

### Create Exoskeleton

```http
POST /api/v1/dod/exoskeleton
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "project_path": "/path/to/project",
  "template": "enterprise",
  "force": false,
  "preview": false
}
```

## CLI Integration

### Python Script Integration

```python
#!/usr/bin/env python3
"""
Example script integrating DoD automation into existing workflows.
"""

import subprocess
import json
import sys
from pathlib import Path

def run_dod_automation(project_path: str, environment: str = "development") -> dict:
    """Run DoD automation and return structured results."""
    
    try:
        result = subprocess.run([
            "uvmgr", "dod", "complete",
            "--env", environment,
            "--json"
        ], 
        cwd=project_path,
        capture_output=True,
        text=True,
        check=True
        )
        
        return json.loads(result.stdout)
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": e.stderr,
            "exit_code": e.returncode
        }

def main():
    """Main automation workflow."""
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"Running DoD automation for {project_path}")
    
    # Run automation
    result = run_dod_automation(project_path, "production")
    
    if result["success"]:
        success_rate = result["overall_success_rate"]
        print(f"✅ Automation completed successfully! Success rate: {success_rate:.1%}")
        
        # Print criteria results
        for criterion, details in result["criteria_results"].items():
            status = "✅" if details["passed"] else "❌"
            print(f"  {status} {criterion}: {details['score']:.1f}%")
            
    else:
        print(f"❌ Automation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Makefile Integration

```makefile
# Makefile with DoD automation integration

.PHONY: dod-status dod-validate dod-complete dod-setup

# Check DoD status
dod-status:
	@echo "🔍 Checking DoD status..."
	uvmgr dod status

# Validate specific criteria
dod-validate:
	@echo "✅ Validating DoD criteria..."
	uvmgr dod validate --criteria testing,security,code_quality --detailed

# Run complete automation
dod-complete:
	@echo "🎯 Running complete DoD automation..."
	uvmgr dod complete --env production --auto-fix

# Setup DoD exoskeleton
dod-setup:
	@echo "🏗️ Setting up DoD exoskeleton..."
	uvmgr dod exoskeleton --template enterprise

# CI/CD integration
ci: dod-validate
	@echo "🚀 CI pipeline with DoD validation completed"

# Release preparation
release: dod-complete
	@echo "📦 Release preparation with DoD automation completed"
```

## Error Handling

### Exception Types

```python
from uvmgr.exceptions import (
    DoDError,
    ExoskeletonError,
    CriteriaValidationError,
    PipelineGenerationError,
    ConfigurationError
)

# Base exception
class DoDError(Exception):
    """Base exception for DoD automation errors."""
    pass

# Specific exceptions
class ExoskeletonError(DoDError):
    """Exoskeleton creation or management error."""
    pass

class CriteriaValidationError(DoDError):
    """Criteria validation error."""
    
    def __init__(self, criterion: str, message: str, score: float = 0.0):
        self.criterion = criterion
        self.score = score
        super().__init__(f"Criterion '{criterion}' failed: {message}")

class PipelineGenerationError(DoDError):
    """Pipeline generation error."""
    pass

class ConfigurationError(DoDError):
    """Configuration validation error."""
    pass
```

### Error Response Format

```python
# Standard error response format
{
    "success": false,
    "error": {
        "type": "CriteriaValidationError",
        "message": "Security criterion failed: 3 high-severity vulnerabilities found",
        "code": "SECURITY_VALIDATION_FAILED", 
        "details": {
            "criterion": "security",
            "score": 45.0,
            "vulnerabilities": [
                {
                    "severity": "high",
                    "cve": "CVE-2023-1234",
                    "package": "requests",
                    "version": "2.25.1"
                }
            ]
        },
        "suggestions": [
            "Update requests package to version 2.31.0 or later",
            "Run 'pip install --upgrade requests'",
            "Review security advisory for additional mitigation steps"
        ]
    },
    "execution_time": 23.5,
    "timestamp": "2024-06-29T10:30:00Z"
}
```

### Exception Handling Best Practices

```python
from uvmgr.ops.dod import execute_complete_automation
from uvmgr.exceptions import DoDError, CriteriaValidationError
from pathlib import Path

def safe_dod_automation(project_path: str) -> dict:
    """Safely execute DoD automation with comprehensive error handling."""
    
    try:
        result = execute_complete_automation(
            project_path=Path(project_path),
            environment="production",
            auto_fix=False
        )
        
        return result
        
    except CriteriaValidationError as e:
        # Handle specific criteria failures
        return {
            "success": False,
            "error": {
                "type": "criteria_validation",
                "criterion": e.criterion,
                "message": str(e),
                "score": e.score
            }
        }
        
    except ExoskeletonError as e:
        # Handle exoskeleton issues
        return {
            "success": False,
            "error": {
                "type": "exoskeleton",
                "message": str(e)
            }
        }
        
    except DoDError as e:
        # Handle general DoD errors
        return {
            "success": False,
            "error": {
                "type": "dod_general",
                "message": str(e)
            }
        }
        
    except Exception as e:
        # Handle unexpected errors
        return {
            "success": False,
            "error": {
                "type": "unexpected",
                "message": f"Unexpected error: {str(e)}"
            }
        }
```

This comprehensive API reference provides complete documentation for integrating with and extending the DoD automation system.