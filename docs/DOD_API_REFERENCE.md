# 📚 DoD Automation API Reference

## Table of Contents
- [Overview](#overview)
- [Commands Layer API](#commands-layer-api)
- [Operations Layer API](#operations-layer-api)  
- [Runtime Layer API](#runtime-layer-api)
- [Core Components](#core-components)
- [Data Models](#data-models)
- [Extension APIs](#extension-apis)
- [Error Handling](#error-handling)

## Overview

The DoD Automation API provides programmatic access to the complete Definition of Done automation system. The API follows a three-tier architecture with clear separation between CLI commands, business logic operations, and infrastructure runtime.

### API Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        DoD Automation API                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Commands Layer (CLI Interface)                                 │
│  ├── dod.py - CLI command definitions                          │
│  └── Typer-based command interface                             │
│                                                                 │
│  Operations Layer (Business Logic)                              │
│  ├── ops/dod.py - Core business logic and 80/20 optimization  │
│  └── Pure functions, no side effects                           │
│                                                                 │
│  Runtime Layer (Infrastructure)                                 │
│  ├── runtime/dod.py - File I/O and external tool execution    │
│  └── Subprocess calls, file operations, CI/CD integration      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Import Structure
```python
# Commands Layer
from uvmgr.commands.dod import app as dod_commands

# Operations Layer  
from uvmgr.ops.dod import (
    complete_dod_automation,
    validate_dod_criteria,
    generate_exoskeleton_config,
    calculate_weighted_score
)

# Runtime Layer
from uvmgr.runtime.dod import (
    initialize_exoskeleton_files,
    execute_automation_workflow,
    run_e2e_tests,
    generate_pipeline_files
)

# Data Models
from uvmgr.models.dod import (
    AutomationResult,
    CriteriaResult,
    ExoskeletonConfig,
    ValidationResult
)
```

## Commands Layer API

### Module: `uvmgr.commands.dod`

The commands layer provides the CLI interface for DoD automation.

#### `app: typer.Typer`
Main Typer application for DoD commands.

```python
import typer
from uvmgr.commands.dod import app

# Access the Typer app directly
dod_app = app
```

#### Command Functions

##### `exoskeleton()`
Initialize Weaver Forge exoskeleton structure.

```python
@app.command("exoskeleton")
def exoskeleton(
    template: str = typer.Option("standard", "--template", "-t", 
                                help="Template type: standard, enterprise, ai-native"),
    force: bool = typer.Option(False, "--force", 
                              help="Overwrite existing exoskeleton"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", 
                                            help="Custom output directory")
) -> None:
    """🏗️ Initialize Weaver Forge exoskeleton."""
```

**Usage:**
```python
from uvmgr.commands.dod import exoskeleton

# Initialize standard exoskeleton
exoskeleton(template="standard", force=False)

# Initialize enterprise exoskeleton with force
exoskeleton(template="enterprise", force=True, output_dir=Path("./custom"))
```

##### `complete()`
Execute complete Definition of Done automation.

```python
@app.command("complete")
def complete(
    environment: str = typer.Option("development", "--env", "-e",
                                   help="Target environment"),
    auto_fix: bool = typer.Option(False, "--auto-fix",
                                 help="Automatically fix detected issues"),
    parallel: bool = typer.Option(True, "--parallel/--sequential",
                                 help="Enable parallel execution"),
    criteria: Optional[str] = typer.Option(None, "--criteria",
                                         help="Specific criteria (comma-separated)"),
    ai_assist: bool = typer.Option(False, "--ai-assist",
                                  help="Enable AI-powered optimization")
) -> None:
    """🎯 Execute complete Definition of Done automation."""
```

**Usage:**
```python
from uvmgr.commands.dod import complete

# Basic development automation
complete(environment="development")

# Production automation with AI assistance
complete(environment="production", auto_fix=True, ai_assist=True)

# Specific criteria only
complete(criteria="testing,security", parallel=True)
```

##### `validate()`
Validate Definition of Done criteria.

```python
@app.command("validate")
def validate(
    detailed: bool = typer.Option(False, "--detailed",
                                 help="Show detailed validation results"),
    criteria: Optional[str] = typer.Option(None, "--criteria",
                                         help="Specific criteria to validate"),
    format: str = typer.Option("table", "--format",
                              help="Output format: table, json, yaml"),
    fix_suggestions: bool = typer.Option(False, "--fix-suggestions",
                                        help="Include fix suggestions")
) -> None:
    """✅ Validate Definition of Done criteria."""
```

##### `pipeline()`
Generate DevOps pipeline configurations.

```python
@app.command("pipeline")
def pipeline(
    provider: str = typer.Option("github", "--provider",
                                help="CI/CD provider: github, gitlab-ci, azure-devops"),
    environments: str = typer.Option("dev,staging,prod", "--environments",
                                   help="Target environments (comma-separated)"),
    template: str = typer.Option("basic", "--template",
                                help="Pipeline template: basic, enterprise, security-focused"),
    features: Optional[str] = typer.Option(None, "--features",
                                         help="Additional features to include"),
    output_path: Optional[Path] = typer.Option(None, "--output-path",
                                             help="Custom output location")
) -> None:
    """🚀 Generate DevOps pipeline configurations."""
```

##### `testing()`
Execute comprehensive end-to-end testing.

```python
@app.command("testing")
def testing(
    strategy: str = typer.Option("comprehensive", "--strategy",
                                help="Testing strategy: quick, comprehensive, security-focused"),
    parallel: bool = typer.Option(True, "--parallel",
                                 help="Run tests in parallel"),
    headless: bool = typer.Option(True, "--headless/--headed",
                                 help="Browser mode for E2E tests"),
    record_video: bool = typer.Option(False, "--record-video",
                                     help="Record test execution videos"),
    coverage: int = typer.Option(80, "--coverage",
                                help="Minimum coverage threshold")
) -> None:
    """🧪 Execute comprehensive end-to-end testing."""
```

##### `status()`
Analyze project health and DoD status.

```python
@app.command("status")  
def status(
    detailed: bool = typer.Option(False, "--detailed",
                                 help="Show detailed health analysis"),
    format: str = typer.Option("summary", "--format",
                              help="Output format: summary, detailed, json"),
    suggestions: bool = typer.Option(False, "--suggestions",
                                    help="Include improvement suggestions")
) -> None:
    """📊 Analyze project health and DoD status."""
```

## Operations Layer API

### Module: `uvmgr.ops.dod`

The operations layer contains pure business logic functions with no side effects.

#### Core Functions

##### `complete_dod_automation()`
Execute complete DoD automation with 80/20 optimization.

```python
def complete_dod_automation(
    project_path: Path,
    environment: str = "development",
    auto_fix: bool = False,
    parallel: bool = True,
    criteria: Optional[List[str]] = None,
    ai_assist: bool = False
) -> AutomationResult:
    """
    Execute complete Definition of Done automation.
    
    Args:
        project_path: Path to the project directory
        environment: Target environment (development, staging, production)
        auto_fix: Whether to automatically fix detected issues
        parallel: Whether to run criteria in parallel
        criteria: Specific criteria to run (None for all)
        ai_assist: Whether to enable AI-powered optimization
        
    Returns:
        AutomationResult containing execution results and metrics
        
    Example:
        >>> result = complete_dod_automation(
        ...     project_path=Path("."),
        ...     environment="production",
        ...     auto_fix=True,
        ...     ai_assist=True
        ... )
        >>> print(f"Success: {result.success}, Score: {result.overall_score}")
    """
```

##### `validate_dod_criteria()`
Validate specific DoD criteria with weighted scoring.

```python
def validate_dod_criteria(
    project_path: Path,
    criteria: Optional[List[str]] = None,
    detailed: bool = False,
    fix_suggestions: bool = False
) -> ValidationResult:
    """
    Validate Definition of Done criteria.
    
    Args:
        project_path: Path to the project directory
        criteria: Specific criteria to validate (None for all)
        detailed: Whether to include detailed validation information
        fix_suggestions: Whether to include fix suggestions
        
    Returns:
        ValidationResult containing validation scores and details
        
    Example:
        >>> result = validate_dod_criteria(
        ...     project_path=Path("."),
        ...     criteria=["testing", "security"],
        ...     detailed=True
        ... )
        >>> for criterion, score in result.criteria_scores.items():
        ...     print(f"{criterion}: {score.score}%")
    """
```

##### `generate_exoskeleton_config()`
Generate exoskeleton configuration based on template.

```python
def generate_exoskeleton_config(
    template: str = "standard",
    project_path: Optional[Path] = None,
    custom_options: Optional[Dict[str, Any]] = None
) -> ExoskeletonConfig:
    """
    Generate Weaver Forge exoskeleton configuration.
    
    Args:
        template: Template type (standard, enterprise, ai-native)
        project_path: Path to the project (for context analysis)
        custom_options: Custom configuration options
        
    Returns:
        ExoskeletonConfig containing complete configuration
        
    Example:
        >>> config = generate_exoskeleton_config(
        ...     template="enterprise",
        ...     project_path=Path("."),
        ...     custom_options={"ai_features": ["optimization", "prediction"]}
        ... )
        >>> print(config.automation.criteria["testing"].weight)
    """
```

##### `calculate_weighted_score()`
Calculate 80/20 weighted score for criteria results.

```python
def calculate_weighted_score(
    criteria_results: Dict[str, CriteriaResult],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate weighted score using 80/20 optimization principles.
    
    Args:
        criteria_results: Results for each criterion
        weights: Custom weights (None for default 80/20 weights)
        
    Returns:
        Weighted score (0-100)
        
    Example:
        >>> results = {
        ...     "testing": CriteriaResult(score=85.0, passed=True),
        ...     "security": CriteriaResult(score=92.0, passed=True),
        ...     "devops": CriteriaResult(score=78.0, passed=True)
        ... }
        >>> score = calculate_weighted_score(results)
        >>> print(f"Weighted score: {score}%")
    """
```

##### `optimize_execution_plan()`
Create optimized execution plan using 80/20 principles.

```python
def optimize_execution_plan(
    criteria: List[str],
    parallel: bool = True,
    project_context: Optional[ProjectContext] = None
) -> ExecutionPlan:
    """
    Create optimized execution plan for DoD criteria.
    
    Args:
        criteria: List of criteria to execute
        parallel: Whether to enable parallel execution
        project_context: Project context for optimization
        
    Returns:
        ExecutionPlan with optimized order and resource allocation
        
    Example:
        >>> plan = optimize_execution_plan(
        ...     criteria=["testing", "security", "devops"],
        ...     parallel=True
        ... )
        >>> print(f"Execution phases: {len(plan.phases)}")
    """
```

#### Helper Functions

##### `get_default_criteria_weights()`
Get default 80/20 criteria weights.

```python
def get_default_criteria_weights() -> Dict[str, CriteriaWeight]:
    """
    Get default weighted criteria configuration.
    
    Returns:
        Dictionary of criteria weights following 80/20 principles
        
    Example:
        >>> weights = get_default_criteria_weights()
        >>> print(weights["testing"].weight)  # 0.25
        >>> print(weights["testing"].priority)  # "critical"
    """
```

##### `analyze_project_context()`
Analyze project context for optimization.

```python
def analyze_project_context(project_path: Path) -> ProjectContext:
    """
    Analyze project to determine optimal automation strategy.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        ProjectContext containing analysis results
        
    Example:
        >>> context = analyze_project_context(Path("."))
        >>> print(f"Complexity: {context.complexity_score}")
        >>> print(f"Recommended criteria: {context.recommended_criteria}")
    """
```

## Runtime Layer API

### Module: `uvmgr.runtime.dod`

The runtime layer handles infrastructure operations and external tool integration.

#### Core Functions

##### `initialize_exoskeleton_files()`
Initialize exoskeleton files and directory structure.

```python
@span("dod.runtime.initialize_exoskeleton_files")
def initialize_exoskeleton_files(
    project_path: Path,
    template_config: Dict[str, Any],
    force: bool = False
) -> Dict[str, Any]:
    """
    Initialize exoskeleton files and structure.
    
    Args:
        project_path: Path to the project directory
        template_config: Template configuration
        force: Whether to overwrite existing files
        
    Returns:
        Dictionary containing initialization results
        
    Example:
        >>> result = initialize_exoskeleton_files(
        ...     project_path=Path("."),
        ...     template_config={"template": "enterprise", "ai_features": []},
        ...     force=True
        ... )
        >>> print(f"Success: {result['success']}")
        >>> print(f"Files created: {len(result['files_created'])}")
    """
```

##### `execute_automation_workflow()`
Execute complete automation workflow with infrastructure operations.

```python
@span("dod.runtime.execute_automation_workflow")
def execute_automation_workflow(
    project_path: Path,
    criteria: List[str],
    environment: str,
    auto_fix: bool,
    parallel: bool,
    ai_assist: bool
) -> Dict[str, Any]:
    """
    Execute complete automation workflow.
    
    Args:
        project_path: Path to the project directory
        criteria: List of criteria to execute
        environment: Target environment
        auto_fix: Whether to automatically fix issues
        parallel: Whether to run in parallel
        ai_assist: Whether to enable AI assistance
        
    Returns:
        Dictionary containing execution results and metrics
        
    Example:
        >>> result = execute_automation_workflow(
        ...     project_path=Path("."),
        ...     criteria=["testing", "security"],
        ...     environment="production",
        ...     auto_fix=True,
        ...     parallel=True,
        ...     ai_assist=True
        ... )
        >>> print(f"Overall success: {result['success']}")
    """
```

##### `validate_criteria_runtime()`
Runtime validation of DoD criteria.

```python
@span("dod.runtime.validate_criteria_runtime")
def validate_criteria_runtime(
    project_path: Path,
    criteria: List[str],
    detailed: bool,
    fix_suggestions: bool
) -> Dict[str, Any]:
    """
    Runtime validation of DoD criteria.
    
    Args:
        project_path: Path to the project directory
        criteria: List of criteria to validate
        detailed: Whether to include detailed results
        fix_suggestions: Whether to include fix suggestions
        
    Returns:
        Dictionary containing validation results
        
    Example:
        >>> result = validate_criteria_runtime(
        ...     project_path=Path("."),
        ...     criteria=["testing", "security"],
        ...     detailed=True,
        ...     fix_suggestions=True
        ... )
        >>> for criterion, score in result["criteria_scores"].items():
        ...     print(f"{criterion}: {score['score']}%")
    """
```

##### `generate_pipeline_files()`
Generate DevOps pipeline files for various providers.

```python
@span("dod.runtime.generate_pipeline_files")
def generate_pipeline_files(
    project_path: Path,
    provider: str,
    environments: List[str],
    features: List[str],
    template: str,
    output_path: Optional[Path]
) -> Dict[str, Any]:
    """
    Generate DevOps pipeline files.
    
    Args:
        project_path: Path to the project directory
        provider: CI/CD provider (github, gitlab-ci, azure-devops)
        environments: List of target environments
        features: List of features to include
        template: Pipeline template type
        output_path: Custom output path
        
    Returns:
        Dictionary containing generation results
        
    Example:
        >>> result = generate_pipeline_files(
        ...     project_path=Path("."),
        ...     provider="github",
        ...     environments=["dev", "prod"],
        ...     features=["testing", "security"],
        ...     template="enterprise",
        ...     output_path=None
        ... )
        >>> print(f"Files created: {result['files_created']}")
    """
```

##### `run_e2e_tests()`
Execute end-to-end testing with various strategies.

```python
@span("dod.runtime.run_e2e_tests")
def run_e2e_tests(
    project_path: Path,
    environment: str,
    parallel: bool,
    headless: bool,
    record_video: bool,
    generate_report: bool
) -> Dict[str, Any]:
    """
    Run end-to-end tests.
    
    Args:
        project_path: Path to the project directory
        environment: Target environment
        parallel: Whether to run in parallel
        headless: Whether to run headless browser tests
        record_video: Whether to record test videos
        generate_report: Whether to generate test reports
        
    Returns:
        Dictionary containing test results
        
    Example:
        >>> result = run_e2e_tests(
        ...     project_path=Path("."),
        ...     environment="staging",
        ...     parallel=True,
        ...     headless=True,
        ...     record_video=True,
        ...     generate_report=True
        ... )
        >>> for suite, results in result["test_suites"].items():
        ...     print(f"{suite}: {results['passed']}/{results['total']} passed")
    """
```

##### `analyze_project_health()`
Analyze project health and generate status report.

```python
@span("dod.runtime.analyze_project_health")
def analyze_project_health(
    project_path: Path,
    detailed: bool,
    suggestions: bool
) -> Dict[str, Any]:
    """
    Analyze project health and status.
    
    Args:
        project_path: Path to the project directory
        detailed: Whether to include detailed analysis
        suggestions: Whether to include improvement suggestions
        
    Returns:
        Dictionary containing health analysis results
        
    Example:
        >>> result = analyze_project_health(
        ...     project_path=Path("."),
        ...     detailed=True,
        ...     suggestions=True
        ... )
        >>> print(f"Overall score: {result['dod_status']['overall_score']}")
        >>> print(f"Suggestions: {result['suggestions']}")
    """
```

## Core Components

### Telemetry Integration

All API functions are instrumented with OpenTelemetry for observability.

```python
from uvmgr.core.telemetry import span, metric_counter, metric_histogram

# Example usage in custom functions
@span("custom.operation")
def custom_dod_operation(project_path: Path) -> Result:
    """Custom DoD operation with telemetry."""
    metric_counter("custom.operations.started")(1)
    
    start_time = time.time()
    try:
        # Your operation logic here
        result = perform_operation(project_path)
        
        # Record success metrics
        metric_counter("custom.operations.success")(1)
        duration = time.time() - start_time
        metric_histogram("custom.operations.duration")(duration)
        
        return result
    except Exception as e:
        metric_counter("custom.operations.failed")(1)
        raise
```

### Configuration Management

```python
from uvmgr.core.config import Config

# Access DoD configuration
config = Config.load()
dod_config = config.dod

# Customize criteria weights
custom_weights = {
    "testing": 0.30,    # Increase testing weight
    "security": 0.25,   # Keep security weight
    "devops": 0.15      # Decrease devops weight
}

config.dod.criteria_weights = custom_weights
```

## Data Models

### `AutomationResult`
Result of complete DoD automation execution.

```python
@dataclass
class AutomationResult:
    """Result of DoD automation execution."""
    
    success: bool                                    # Overall success
    overall_score: float                            # Weighted score (0-100)
    criteria_results: Dict[str, CriteriaResult]     # Individual criterion results
    execution_time: float                           # Total execution time
    environment: str                                # Target environment
    auto_fix_applied: bool                          # Whether auto-fix was used
    parallel_execution: bool                        # Whether parallel execution was used
    ai_insights: Optional[List[str]] = None         # AI-generated insights
    
    def get_critical_score(self) -> float:
        """Get score for critical criteria only."""
        critical_criteria = ["testing", "security", "devops"]
        critical_results = {
            k: v for k, v in self.criteria_results.items() 
            if k in critical_criteria
        }
        return calculate_weighted_score(critical_results)
    
    def get_failed_criteria(self) -> List[str]:
        """Get list of failed criteria."""
        return [
            criterion for criterion, result in self.criteria_results.items()
            if not result.passed
        ]
```

### `CriteriaResult`
Result of individual DoD criterion validation.

```python
@dataclass
class CriteriaResult:
    """Result of individual criterion validation."""
    
    criterion: str              # Criterion name
    passed: bool               # Whether criterion passed
    score: float               # Score (0-100)
    weight: float              # Criterion weight in 80/20 system
    execution_time: float      # Time taken to execute
    details: Optional[str]     # Detailed results
    fix_suggestions: Optional[List[str]] = None  # Suggested fixes
    
    @property
    def weighted_score(self) -> float:
        """Get weighted score contribution."""
        return self.score * self.weight
```

### `ExoskeletonConfig`
Configuration for Weaver Forge exoskeleton.

```python
@dataclass
class ExoskeletonConfig:
    """Weaver Forge exoskeleton configuration."""
    
    version: str                           # Configuration version
    template: str                          # Template type
    created: datetime                      # Creation timestamp
    automation: AutomationConfig          # Automation configuration
    ai: AIConfig                          # AI configuration
    telemetry: TelemetryConfig            # Telemetry configuration
    
    @classmethod
    def load(cls, project_path: Path) -> 'ExoskeletonConfig':
        """Load configuration from project."""
        config_file = project_path / ".uvmgr" / "exoskeleton" / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        else:
            return cls.default()
    
    def save(self, project_path: Path) -> None:
        """Save configuration to project."""
        config_file = project_path / ".uvmgr" / "exoskeleton" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
```

### `ValidationResult`
Result of DoD criteria validation.

```python
@dataclass
class ValidationResult:
    """Result of DoD criteria validation."""
    
    success: bool                                # Overall validation success
    criteria_scores: Dict[str, CriteriaResult]  # Individual criterion scores
    overall_score: float                        # Weighted overall score
    validation_strategy: str                    # Validation strategy used
    timestamp: datetime                         # Validation timestamp
    
    def get_passing_criteria(self) -> List[str]:
        """Get list of passing criteria."""
        return [
            criterion for criterion, result in self.criteria_scores.items()
            if result.passed
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "total_criteria": len(self.criteria_scores),
            "passing_criteria": len(self.get_passing_criteria()),
            "overall_score": self.overall_score,
            "success": self.success
        }
```

## Extension APIs

### Custom Criteria Extension

```python
from uvmgr.extensions.criteria import CriteriaExtension, CriteriaValidator

class CustomCriteriaValidator(CriteriaValidator):
    """Custom DoD criteria validator."""
    
    def validate(self, project_path: Path) -> CriteriaResult:
        """Validate custom criterion."""
        # Your validation logic here
        score = self.calculate_custom_score(project_path)
        passed = score >= 80.0
        
        return CriteriaResult(
            criterion="custom_criterion",
            passed=passed,
            score=score,
            weight=0.10,
            execution_time=time.time() - start_time,
            details=f"Custom validation score: {score}%"
        )

# Register custom criterion
CriteriaExtension.register(
    name="custom_criterion",
    validator=CustomCriteriaValidator(),
    weight=0.10,
    priority="important"
)
```

### AI Model Extension

```python
from uvmgr.extensions.ai import AIModelExtension
import dspy

class CustomAnalysisModel(dspy.Module):
    """Custom AI model for DoD analysis."""
    
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(
            "project_context: str -> optimization_suggestions: List[str], confidence: float"
        )
    
    def forward(self, project_context: str):
        return self.predictor(project_context=project_context)

# Register custom AI model
AIModelExtension.register(
    name="custom_optimizer",
    model=CustomAnalysisModel(),
    use_cases=["optimization", "analysis"]
)
```

### Workflow Extension

```python
from uvmgr.extensions.workflow import WorkflowExtension

def custom_workflow_step(context: WorkflowContext) -> StepResult:
    """Custom workflow step."""
    # Your workflow logic here
    return StepResult(
        success=True,
        output={"processed": True},
        duration=1.5
    )

# Register custom workflow
WorkflowExtension.register_step(
    name="custom_processing",
    function=custom_workflow_step,
    dependencies=["validation"],
    parallel_safe=True
)
```

## Error Handling

### Exception Hierarchy

```python
# Base exceptions
class DoDError(Exception):
    """Base exception for DoD automation."""
    pass

class ExoskeletonError(DoDError):
    """Exoskeleton initialization or configuration error."""
    pass

class CriteriaValidationError(DoDError):
    """Error during criteria validation."""
    pass

class AutomationExecutionError(DoDError):
    """Error during automation execution."""
    pass

class PipelineGenerationError(DoDError):
    """Error during pipeline generation."""
    pass

# Specific exceptions
class InvalidCriteriaError(CriteriaValidationError):
    """Invalid or unknown criteria specified."""
    pass

class InsufficientResourcesError(AutomationExecutionError):
    """Insufficient resources for automation execution."""
    pass

class UnsupportedProviderError(PipelineGenerationError):
    """Unsupported CI/CD provider specified."""
    pass
```

### Error Handling Patterns

```python
from uvmgr.exceptions import DoDError, CriteriaValidationError

try:
    result = complete_dod_automation(
        project_path=Path("."),
        environment="production"
    )
except CriteriaValidationError as e:
    print(f"Validation error: {e}")
    # Handle validation-specific error
except DoDError as e:
    print(f"DoD automation error: {e}")
    # Handle general DoD error
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected errors
```

### Retry and Resilience

```python
from uvmgr.core.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def resilient_automation_execution(project_path: Path) -> AutomationResult:
    """Execute automation with automatic retry on transient failures."""
    return complete_dod_automation(project_path)

# Usage
try:
    result = resilient_automation_execution(Path("."))
except Exception as e:
    print(f"Automation failed after retries: {e}")
```

---

**Generated by uvmgr DoD API Documentation Team**  
*Complete technical reference for DoD automation system*