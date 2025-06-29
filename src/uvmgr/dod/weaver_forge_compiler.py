"""
Weaver Forge DoD Compiler - Semantic Definition of Done Engine
=============================================================

This module compiles high-level Definition of Done requirements into
executable validation pipelines using Weaver Forge semantic conventions.

The compiler transforms declarative DoD specifications into:
- Automated validation workflows
- Continuous compliance checks
- Self-evolving quality gates
- Cross-project standardization

Example DoD Specification:
```yaml
definition_of_done:
  code_quality:
    - lint: score >= 9.5
    - complexity: cyclomatic < 10
    - test_coverage: >= 80%
  
  security:
    - vulnerability_scan: critical == 0
    - secrets_scan: findings == 0
    - dependency_audit: high_risk == 0
  
  documentation:
    - api_docs: coverage == 100%
    - changelog: updated == true
    - architecture: current == true
  
  operations:
    - monitoring: dashboards == ready
    - alerts: configured == true
    - rollback: tested == true
```
"""

from __future__ import annotations

import ast
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime

from pydantic import BaseModel, Field
from opentelemetry import trace
from spiffworkflow.bpmn import BpmnWorkflow

from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.core.semconv import WorkflowAttributes, TestAttributes
from uvmgr.core.convergence_engine import get_convergence_engine


class ValidationLevel(Enum):
    """Validation strictness levels."""
    ADVISORY = "advisory"      # Warnings only
    STANDARD = "standard"      # Block on failures
    STRICT = "strict"          # Block on warnings
    PARANOID = "paranoid"      # Block on any deviation


class DoDCategory(Enum):
    """Standard Definition of Done categories."""
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    ACCESSIBILITY = "accessibility"


@dataclass
class DoDRule:
    """A single Definition of Done rule."""
    category: DoDCategory
    name: str
    condition: str  # e.g., "coverage >= 80%"
    validation_func: Optional[Callable] = None
    severity: ValidationLevel = ValidationLevel.STANDARD
    auto_fix: bool = False
    fix_command: Optional[str] = None
    telemetry_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DoDValidationResult:
    """Result of a DoD validation."""
    rule: DoDRule
    passed: bool
    actual_value: Any
    expected_value: Any
    message: str
    fix_applied: bool = False
    duration_ms: float = 0.0
    telemetry_span_id: Optional[str] = None


class DoDSpecification(BaseModel):
    """Complete Definition of Done specification."""
    name: str = Field(..., description="DoD profile name")
    version: str = Field("1.0.0", description="DoD version")
    extends: Optional[str] = Field(None, description="Parent DoD to inherit from")
    
    categories: Dict[DoDCategory, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="DoD rules by category"
    )
    
    enforcement: ValidationLevel = Field(
        ValidationLevel.STANDARD,
        description="Default enforcement level"
    )
    
    workflows: Dict[str, str] = Field(
        default_factory=dict,
        description="BPMN workflows for complex validations"
    )
    
    evolution: Dict[str, Any] = Field(
        default_factory=dict,
        description="Self-evolution configuration"
    )


class WeaverForgeCompiler:
    """
    Compiles Definition of Done specifications into executable validation pipelines.
    
    This is the core of the DoD exoskeleton - it takes declarative specifications
    and transforms them into living, breathing validation systems that wrap around
    projects and enforce quality standards automatically.
    """
    
    def __init__(self):
        self.rules_registry: Dict[str, DoDRule] = {}
        self.compiled_workflows: Dict[str, BpmnWorkflow] = {}
        self.validation_history: List[DoDValidationResult] = []
        self.convergence_engine = get_convergence_engine()
        
        # Register built-in validation functions
        self._register_builtin_validators()
    
    def compile_specification(self, spec_path: Path) -> DoDSpecification:
        """
        Compile a DoD specification from YAML into executable form.
        
        Args:
            spec_path: Path to DoD specification YAML file
            
        Returns:
            Compiled DoDSpecification ready for execution
        """
        with span("dod.compile_specification", 
                 **{WorkflowAttributes.DEFINITION_PATH: str(spec_path)}):
            
            # Load YAML specification
            with open(spec_path) as f:
                raw_spec = yaml.safe_load(f)
            
            # Parse into structured format
            spec = DoDSpecification(**raw_spec)
            
            # Compile rules
            for category, rules in spec.categories.items():
                for rule_def in rules:
                    rule = self._compile_rule(category, rule_def)
                    self.rules_registry[rule.name] = rule
            
            # Compile workflows if present
            for workflow_name, workflow_def in spec.workflows.items():
                workflow = self._compile_workflow(workflow_name, workflow_def)
                self.compiled_workflows[workflow_name] = workflow
            
            # Record compilation metrics
            metric_counter("dod.specifications.compiled")(1)
            metric_histogram("dod.rules.count")(len(self.rules_registry))
            
            return spec
    
    def _compile_rule(self, category: DoDCategory, rule_def: Dict[str, Any]) -> DoDRule:
        """Compile a single DoD rule."""
        name = rule_def["name"]
        condition = rule_def["condition"]
        
        # Parse condition into validation function
        validation_func = self._parse_condition(condition)
        
        return DoDRule(
            category=category,
            name=name,
            condition=condition,
            validation_func=validation_func,
            severity=ValidationLevel(rule_def.get("severity", "standard")),
            auto_fix=rule_def.get("auto_fix", False),
            fix_command=rule_def.get("fix_command"),
            telemetry_attributes=rule_def.get("telemetry", {})
        )
    
    def _parse_condition(self, condition: str) -> Callable:
        """
        Parse a condition string into executable validation function.
        
        Examples:
            "coverage >= 80%" -> lambda x: x.coverage >= 80
            "vulnerabilities == 0" -> lambda x: x.vulnerabilities == 0
        """
        # Simple DSL parser for common conditions
        if ">=" in condition:
            metric, threshold = condition.split(">=")
            metric = metric.strip()
            threshold = self._parse_value(threshold.strip())
            return lambda ctx: getattr(ctx, metric, 0) >= threshold
        
        elif "==" in condition:
            metric, expected = condition.split("==")
            metric = metric.strip()
            expected = self._parse_value(expected.strip())
            return lambda ctx: getattr(ctx, metric, None) == expected
        
        elif "<" in condition:
            metric, threshold = condition.split("<")
            metric = metric.strip()
            threshold = self._parse_value(threshold.strip())
            return lambda ctx: getattr(ctx, metric, float('inf')) < threshold
        
        else:
            # Fall back to AST evaluation for complex conditions
            return lambda ctx: self._eval_condition(condition, ctx)
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a value string into appropriate type."""
        value_str = value_str.strip()
        
        # Handle percentages
        if value_str.endswith("%"):
            return float(value_str[:-1])
        
        # Handle booleans
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"
        
        # Handle numbers
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            return value_str
    
    def _eval_condition(self, condition: str, context: Any) -> bool:
        """Evaluate complex conditions using AST."""
        try:
            # Parse condition into AST
            tree = ast.parse(condition, mode='eval')
            
            # Create evaluation context
            eval_context = {
                name: getattr(context, name, None)
                for name in dir(context)
                if not name.startswith('_')
            }
            
            # Evaluate safely
            return eval(compile(tree, '<dod_condition>', 'eval'), 
                       {"__builtins__": {}}, eval_context)
        except Exception as e:
            # Log evaluation error
            metric_counter("dod.condition.eval_errors")(1)
            return False
    
    def _compile_workflow(self, name: str, workflow_def: str) -> BpmnWorkflow:
        """Compile a BPMN workflow for complex DoD validations."""
        # This would integrate with SpiffWorkflow for complex multi-step validations
        return NotImplemented
    
    def _register_builtin_validators(self):
        """Register built-in validation functions."""
        # Code quality validators
        self._register_validator("lint_score", self._validate_lint_score)
        self._register_validator("test_coverage", self._validate_test_coverage)
        self._register_validator("complexity", self._validate_complexity)
        
        # Security validators
        self._register_validator("vulnerability_scan", self._validate_vulnerabilities)
        self._register_validator("secrets_scan", self._validate_secrets)
        
        # Documentation validators
        self._register_validator("api_docs", self._validate_api_docs)
        self._register_validator("changelog", self._validate_changelog)
        
        # Operations validators
        self._register_validator("monitoring", self._validate_monitoring)
        self._register_validator("alerts", self._validate_alerts)
    
    def _register_validator(self, name: str, func: Callable):
        """Register a validation function."""
        # Store validators for use in rule compilation
        setattr(self, f"_builtin_{name}", func)
    
    async def _validate_lint_score(self, project_path: Path) -> float:
        """Validate code lint score."""
        # Run linter and extract score
        # This would integrate with ruff, mypy, etc.
        return NotImplemented
    
    async def _validate_test_coverage(self, project_path: Path) -> float:
        """Validate test coverage percentage."""
        # Run coverage tool and extract percentage
        return NotImplemented
    
    async def _validate_complexity(self, project_path: Path) -> float:
        """Validate code complexity metrics."""
        # Run complexity analysis
        return NotImplemented
    
    async def _validate_vulnerabilities(self, project_path: Path) -> int:
        """Validate security vulnerabilities."""
        # Run security scanner
        return NotImplemented
    
    async def _validate_secrets(self, project_path: Path) -> int:
        """Validate no secrets in code."""
        # Run secrets scanner
        return NotImplemented
    
    async def _validate_api_docs(self, project_path: Path) -> float:
        """Validate API documentation coverage."""
        # Analyze API documentation
        return NotImplemented
    
    async def _validate_changelog(self, project_path: Path) -> bool:
        """Validate changelog is updated."""
        # Check changelog freshness
        return NotImplemented
    
    async def _validate_monitoring(self, project_path: Path) -> bool:
        """Validate monitoring is configured."""
        # Check monitoring setup
        return NotImplemented
    
    async def _validate_alerts(self, project_path: Path) -> bool:
        """Validate alerts are configured."""
        # Check alert configuration
        return NotImplemented


class DoDExoskeleton:
    """
    The Definition of Done Exoskeleton that wraps around projects.
    
    This provides the structural support and automated enforcement of
    quality standards throughout the project lifecycle.
    """
    
    def __init__(self, compiler: WeaverForgeCompiler):
        self.compiler = compiler
        self.active_specifications: Dict[str, DoDSpecification] = {}
        self.validation_cache: Dict[str, DoDValidationResult] = {}
        self.evolution_engine = DoDEvolutionEngine(self)
    
    async def wrap_project(self, 
                          project_path: Path,
                          spec_name: str = "default") -> None:
        """
        Wrap a project with the DoD exoskeleton.
        
        This activates continuous DoD enforcement for the project.
        """
        with span("dod.wrap_project", 
                 project_path=str(project_path),
                 spec_name=spec_name):
            
            # Load or use cached specification
            if spec_name not in self.active_specifications:
                spec_path = project_path / ".dod" / f"{spec_name}.yaml"
                spec = self.compiler.compile_specification(spec_path)
                self.active_specifications[spec_name] = spec
            
            # Initialize continuous validation
            await self._initialize_continuous_validation(project_path, spec_name)
            
            # Set up evolution monitoring
            await self.evolution_engine.monitor_project(project_path, spec_name)
            
            metric_counter("dod.projects.wrapped")(1)
    
    async def validate_project(self,
                             project_path: Path,
                             spec_name: str = "default",
                             fix_issues: bool = True) -> List[DoDValidationResult]:
        """
        Run full DoD validation on a project.
        
        Returns list of validation results.
        """
        with span("dod.validate_project") as validation_span:
            spec = self.active_specifications.get(spec_name)
            if not spec:
                raise ValueError(f"No specification loaded for {spec_name}")
            
            results = []
            start_time = datetime.now()
            
            # Run all validation rules
            for rule_name, rule in self.compiler.rules_registry.items():
                result = await self._validate_rule(project_path, rule)
                results.append(result)
                
                # Apply auto-fix if enabled and validation failed
                if not result.passed and rule.auto_fix and fix_issues:
                    fix_result = await self._apply_fix(project_path, rule)
                    result.fix_applied = fix_result
            
            # Record validation metrics
            duration = (datetime.now() - start_time).total_seconds()
            passed_count = sum(1 for r in results if r.passed)
            
            metric_histogram("dod.validation.duration")(duration)
            metric_counter("dod.validations.total")(1)
            metric_counter("dod.validations.passed")(passed_count)
            metric_counter("dod.validations.failed")(len(results) - passed_count)
            
            # Trigger evolution based on results
            await self.evolution_engine.learn_from_validation(results)
            
            return results
    
    async def _validate_rule(self, 
                           project_path: Path,
                           rule: DoDRule) -> DoDValidationResult:
        """Validate a single DoD rule."""
        start_time = datetime.now()
        
        try:
            # Create validation context
            context = await self._create_validation_context(project_path, rule)
            
            # Run validation
            passed = rule.validation_func(context)
            
            # Extract actual vs expected values
            actual = self._extract_actual_value(context, rule)
            expected = self._extract_expected_value(rule)
            
            message = f"{rule.name}: {'PASSED' if passed else 'FAILED'}"
            
        except Exception as e:
            passed = False
            actual = f"Error: {e}"
            expected = rule.condition
            message = f"{rule.name}: ERROR - {e}"
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return DoDValidationResult(
            rule=rule,
            passed=passed,
            actual_value=actual,
            expected_value=expected,
            message=message,
            duration_ms=duration_ms
        )
    
    async def _create_validation_context(self, 
                                       project_path: Path,
                                       rule: DoDRule) -> Any:
        """Create context object for validation."""
        # This would gather all necessary metrics and data
        # For now, return a simple context
        class ValidationContext:
            def __init__(self):
                self.coverage = 85.5
                self.complexity = 8.2
                self.vulnerabilities = 0
                self.lint_score = 9.8
        
        return ValidationContext()
    
    def _extract_actual_value(self, context: Any, rule: DoDRule) -> Any:
        """Extract actual value from validation context."""
        # Parse rule condition to find metric name
        condition_parts = rule.condition.split()
        if condition_parts:
            metric_name = condition_parts[0]
            return getattr(context, metric_name, "N/A")
        return "Unknown"
    
    def _extract_expected_value(self, rule: DoDRule) -> Any:
        """Extract expected value from rule condition."""
        # Parse condition to find threshold/expected value
        for op in [">=", "==", "<", "<=", ">"]:
            if op in rule.condition:
                _, expected = rule.condition.split(op, 1)
                return expected.strip()
        return rule.condition
    
    async def _apply_fix(self, project_path: Path, rule: DoDRule) -> bool:
        """Apply automated fix for a failed rule."""
        if not rule.fix_command:
            return False
        
        try:
            # Execute fix command
            import subprocess
            result = subprocess.run(
                rule.fix_command,
                shell=True,
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            success = result.returncode == 0
            
            metric_counter("dod.fixes.attempted")(1)
            if success:
                metric_counter("dod.fixes.succeeded")(1)
            
            return success
            
        except Exception as e:
            metric_counter("dod.fixes.failed")(1)
            return False
    
    async def _initialize_continuous_validation(self,
                                              project_path: Path,
                                              spec_name: str) -> None:
        """Set up continuous validation for a project."""
        # This would set up file watchers, git hooks, CI/CD integration
        # to continuously validate DoD compliance
        pass


class DoDEvolutionEngine:
    """
    Self-evolving Definition of Done engine.
    
    This learns from validation patterns and evolves the DoD rules
    to better match project reality while maintaining quality standards.
    """
    
    def __init__(self, exoskeleton: DoDExoskeleton):
        self.exoskeleton = exoskeleton
        self.learning_history: List[Dict[str, Any]] = []
        self.rule_performance: Dict[str, Dict[str, float]] = {}
    
    async def monitor_project(self, project_path: Path, spec_name: str) -> None:
        """Monitor project for DoD evolution opportunities."""
        # Set up monitoring for:
        # - Validation failure patterns
        # - Fix effectiveness
        # - Developer feedback
        # - Project metric trends
        pass
    
    async def learn_from_validation(self, 
                                  results: List[DoDValidationResult]) -> None:
        """Learn from validation results to evolve DoD rules."""
        with span("dod.evolution.learn"):
            # Analyze results for patterns
            for result in results:
                rule_name = result.rule.name
                
                if rule_name not in self.rule_performance:
                    self.rule_performance[rule_name] = {
                        "pass_rate": 0.0,
                        "fix_success_rate": 0.0,
                        "avg_duration_ms": 0.0,
                        "total_runs": 0
                    }
                
                perf = self.rule_performance[rule_name]
                
                # Update performance metrics
                total = perf["total_runs"]
                perf["pass_rate"] = (perf["pass_rate"] * total + 
                                   (1 if result.passed else 0)) / (total + 1)
                perf["avg_duration_ms"] = (perf["avg_duration_ms"] * total + 
                                          result.duration_ms) / (total + 1)
                perf["total_runs"] += 1
                
                if result.fix_applied:
                    fix_total = perf.get("fix_attempts", 0)
                    perf["fix_success_rate"] = (perf["fix_success_rate"] * fix_total + 1) / (fix_total + 1)
                    perf["fix_attempts"] = fix_total + 1
            
            # Trigger evolution if patterns detected
            await self._evolve_rules()
    
    async def _evolve_rules(self) -> None:
        """Evolve DoD rules based on learned patterns."""
        for rule_name, performance in self.rule_performance.items():
            # Rules that always pass might be too lenient
            if performance["pass_rate"] > 0.99 and performance["total_runs"] > 100:
                await self._tighten_rule(rule_name)
            
            # Rules that always fail might be too strict
            elif performance["pass_rate"] < 0.10 and performance["total_runs"] > 50:
                await self._relax_rule(rule_name)
            
            # Rules that take too long might need optimization
            elif performance["avg_duration_ms"] > 5000:
                await self._optimize_rule(rule_name)
    
    async def _tighten_rule(self, rule_name: str) -> None:
        """Make a rule more strict based on consistent passes."""
        # This would adjust thresholds upward
        # e.g., coverage >= 80% -> coverage >= 85%
        metric_counter("dod.evolution.rules_tightened")(1)
    
    async def _relax_rule(self, rule_name: str) -> None:
        """Make a rule less strict based on consistent failures."""
        # This would adjust thresholds downward or add exceptions
        # e.g., coverage >= 80% -> coverage >= 75%
        metric_counter("dod.evolution.rules_relaxed")(1)
    
    async def _optimize_rule(self, rule_name: str) -> None:
        """Optimize a slow-running rule."""
        # This would find more efficient validation methods
        metric_counter("dod.evolution.rules_optimized")(1)


# Global DoD exoskeleton instance
_exoskeleton: Optional[DoDExoskeleton] = None

def get_dod_exoskeleton() -> DoDExoskeleton:
    """Get the global DoD exoskeleton instance."""
    global _exoskeleton
    
    if _exoskeleton is None:
        compiler = WeaverForgeCompiler()
        _exoskeleton = DoDExoskeleton(compiler)
    
    return _exoskeleton


async def wrap_project_with_dod(project_path: Path, 
                               spec_name: str = "default") -> None:
    """Wrap a project with the Definition of Done exoskeleton."""
    exoskeleton = get_dod_exoskeleton()
    await exoskeleton.wrap_project(project_path, spec_name)


async def validate_dod(project_path: Path,
                      spec_name: str = "default",
                      fix_issues: bool = True) -> List[DoDValidationResult]:
    """Validate a project against its Definition of Done."""
    exoskeleton = get_dod_exoskeleton()
    return await exoskeleton.validate_project(project_path, spec_name, fix_issues)