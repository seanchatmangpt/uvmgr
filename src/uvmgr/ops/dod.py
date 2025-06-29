#!/usr/bin/env python3
"""
Definition of Done (DoD) operations layer.

Business logic for complete project automation with 80/20 principles:
- Focus on 20% effort that delivers 80% value
- Critical criteria: Testing, Security, DevOps (80% impact)
- Weaver Forge exoskeleton for structural automation
- AI-powered intelligent decision making and optimization
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from ..runtime.dod import (
    analyze_project_health,
    create_automation_report,
    execute_automation_workflow,
    generate_pipeline_files,
    initialize_exoskeleton_files,
    run_e2e_tests,
    validate_criteria_runtime,
)

tracer = trace.get_tracer(__name__)

# 80/20 DoD Criteria with weights optimized for maximum impact
DOD_CRITERIA_WEIGHTS = {
    "testing": {"weight": 0.25, "priority": "critical"},        # Highest impact
    "security": {"weight": 0.25, "priority": "critical"},       # Highest impact
    "devops": {"weight": 0.20, "priority": "critical"},         # High impact
    "code_quality": {"weight": 0.10, "priority": "important"},  # Medium impact
    "documentation": {"weight": 0.10, "priority": "important"}, # Medium impact
    "performance": {"weight": 0.05, "priority": "optional"},    # Lower impact
    "compliance": {"weight": 0.05, "priority": "optional"}      # Lower impact
}

EXOSKELETON_TEMPLATES = {
    "standard": {
        "description": "Standard DoD automation for typical projects",
        "includes": ["basic_ci", "testing", "security_scan", "docs"],
        "ai_features": ["code_review", "test_generation"]
    },
    "enterprise": {
        "description": "Enterprise-grade automation with governance",
        "includes": ["advanced_ci", "multi_env", "security_hardened", "compliance", "monitoring"],
        "ai_features": ["architecture_analysis", "security_advisory", "performance_optimization"]
    },
    "ai-native": {
        "description": "AI-first automation with cutting-edge capabilities",
        "includes": ["intelligent_ci", "ai_testing", "autonomous_security", "self_healing"],
        "ai_features": ["autonomous_development", "predictive_analysis", "self_optimization"]
    }
}

@tracer.start_as_current_span("dod.create_exoskeleton")
def create_exoskeleton(
    project_path: Path,
    template: str = "standard",
    force: bool = False,
    preview: bool = False
) -> dict[str, Any]:
    """
    Create Weaver Forge exoskeleton for complete project automation.
    
    The exoskeleton provides structural automation framework with:
    - Semantic conventions for consistent automation patterns
    - OTEL integration for complete observability
    - BPMN workflows for complex orchestration
    - AI integration for intelligent automation
    - Template system for reusable blueprints
    
    Args:
        project_path: Path to project root
        template: Exoskeleton template (standard, enterprise, ai-native)
        force: Overwrite existing exoskeleton
        preview: Preview structure without creating files
        
    Returns
    -------
        Dict with creation results and metadata
    """
    span = trace.get_current_span()
    span.set_attributes({
        "dod.template": template,
        "dod.force": force,
        "dod.preview": preview,
        "project.path": str(project_path)
    })

    try:
        # Validate template
        if template not in EXOSKELETON_TEMPLATES:
            return {
                "success": False,
                "error": f"Unknown template: {template}. Available: {list(EXOSKELETON_TEMPLATES.keys())}"
            }

        template_config = EXOSKELETON_TEMPLATES[template]

        if preview:
            # Return structure preview without creating files
            return {
                "success": True,
                "preview": True,
                "template": template,
                "structure": _generate_exoskeleton_structure(template_config),
                "description": template_config["description"]
            }

        # Create exoskeleton files and structure
        result = initialize_exoskeleton_files(
            project_path=project_path,
            template_config=template_config,
            force=force
        )

        if result["success"]:
            span.set_attributes({
                "dod.files_created": len(result.get("files_created", [])),
                "dod.workflows_created": len(result.get("workflows_created", [])),
                "dod.ai_integrations": len(result.get("ai_integrations", []))
            })

        return result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Failed to create exoskeleton: {e!s}"
        }

@tracer.start_as_current_span("dod.execute_complete_automation")
def execute_complete_automation(
    project_path: Path,
    environment: str = "development",
    criteria: list[str] | None = None,
    skip_tests: bool = False,
    skip_security: bool = False,
    auto_fix: bool = False,
    parallel: bool = True,
    ai_assist: bool = True
) -> dict[str, Any]:
    """
    Execute complete Definition of Done automation for entire project.
    
    Implements 80/20 automation strategy:
    - Critical criteria (70% weight): Testing, Security, DevOps
    - Important criteria (25% weight): Code Quality, Documentation  
    - Optional criteria (5% weight): Performance, Compliance
    
    Args:
        project_path: Path to project root
        environment: Target environment (development, staging, production)
        criteria: Specific criteria to validate (None = all)
        skip_tests: Skip automated testing
        skip_security: Skip security validation
        auto_fix: Automatically fix issues where possible
        parallel: Run automation steps in parallel
        ai_assist: Enable AI-powered automation assistance
        
    Returns
    -------
        Dict with automation results and completion status
    """
    span = trace.get_current_span()
    span.set_attributes({
        "dod.environment": environment,
        "dod.skip_tests": skip_tests,
        "dod.skip_security": skip_security,
        "dod.auto_fix": auto_fix,
        "dod.parallel": parallel,
        "dod.ai_assist": ai_assist,
        "project.path": str(project_path)
    })

    start_time = time.time()

    try:
        # Determine criteria to execute (default to all if not specified)
        if criteria is None:
            criteria = list(DOD_CRITERIA_WEIGHTS.keys())

        # Filter out skipped criteria
        if skip_tests and "testing" in criteria:
            criteria.remove("testing")
        if skip_security and "security" in criteria:
            criteria.remove("security")

        span.set_attribute("dod.criteria_count", len(criteria))

        # Execute automation workflow
        automation_result = execute_automation_workflow(
            project_path=project_path,
            criteria=criteria,
            environment=environment,
            auto_fix=auto_fix,
            parallel=parallel,
            ai_assist=ai_assist
        )

        # Calculate weighted success rate using 80/20 principles
        overall_success_rate = _calculate_weighted_success_rate(
            automation_result.get("criteria_results", {}),
            criteria
        )

        automation_result["overall_success_rate"] = overall_success_rate
        automation_result["execution_time"] = time.time() - start_time
        automation_result["criteria_executed"] = criteria
        automation_result["automation_strategy"] = "80/20"

        span.set_attributes({
            "dod.success_rate": overall_success_rate,
            "dod.execution_time": automation_result["execution_time"],
            "dod.criteria_passed": len([c for c, r in automation_result.get("criteria_results", {}).items() if r.get("passed", False)])
        })

        return automation_result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Automation execution failed: {e!s}",
            "execution_time": time.time() - start_time
        }

@tracer.start_as_current_span("dod.validate_dod_criteria")
def validate_dod_criteria(
    project_path: Path,
    criteria: list[str] | None = None,
    detailed: bool = False,
    fix_suggestions: bool = True
) -> dict[str, Any]:
    """
    Validate current Definition of Done criteria with 80/20 scoring.
    
    Analyzes project against DoD criteria with intelligent weighting:
    - Critical criteria have high impact on overall score
    - Provides actionable fix suggestions using AI
    - Detailed analysis with specific improvement recommendations
    
    Args:
        project_path: Path to project root
        criteria: Specific criteria to validate (None = all)
        detailed: Include detailed validation results
        fix_suggestions: Generate AI-powered fix suggestions
        
    Returns
    -------
        Dict with validation results and scores
    """
    span = trace.get_current_span()
    span.set_attributes({
        "dod.detailed": detailed,
        "dod.fix_suggestions": fix_suggestions,
        "project.path": str(project_path)
    })

    try:
        # Default to all criteria if not specified
        if criteria is None:
            criteria = list(DOD_CRITERIA_WEIGHTS.keys())

        span.set_attribute("dod.criteria_count", len(criteria))

        # Validate criteria using runtime layer
        validation_result = validate_criteria_runtime(
            project_path=project_path,
            criteria=criteria,
            detailed=detailed,
            fix_suggestions=fix_suggestions
        )

        # Calculate weighted overall score using 80/20 principles
        criteria_scores = validation_result.get("criteria_scores", {})
        overall_score = _calculate_weighted_success_rate(criteria_scores, criteria)

        # Add 80/20 analysis
        critical_scores = [
            score_data.get("score", 0)
            for criteria_name, score_data in criteria_scores.items()
            if DOD_CRITERIA_WEIGHTS.get(criteria_name, {}).get("priority") == "critical"
        ]
        important_scores = [
            score_data.get("score", 0)
            for criteria_name, score_data in criteria_scores.items()
            if DOD_CRITERIA_WEIGHTS.get(criteria_name, {}).get("priority") == "important"
        ]

        validation_result.update({
            "overall_score": overall_score,
            "critical_score": sum(critical_scores) / len(critical_scores) if critical_scores else 0,
            "important_score": sum(important_scores) / len(important_scores) if important_scores else 0,
            "scoring_strategy": "80/20 weighted",
            "criteria_weights": {
                criteria_name: DOD_CRITERIA_WEIGHTS.get(criteria_name, {})
                for criteria_name in criteria
            }
        })

        span.set_attributes({
            "dod.overall_score": overall_score,
            "dod.critical_score": validation_result["critical_score"],
            "dod.important_score": validation_result["important_score"]
        })

        return validation_result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Validation failed: {e!s}",
            "overall_score": 0.0
        }

@tracer.start_as_current_span("dod.generate_devops_pipeline")
def generate_devops_pipeline(
    project_path: Path,
    provider: str = "github-actions",
    environments: list[str] = None,
    features: list[str] = None,
    template: str = "standard",
    output_path: Path | None = None
) -> dict[str, Any]:
    """
    Generate comprehensive DevOps pipelines with DoD automation.
    
    Creates production-ready CI/CD pipelines with:
    - Multi-environment deployment strategies
    - Complete testing automation (unit, integration, E2E)
    - Security scanning and compliance validation
    - Performance testing and monitoring
    - Container orchestration and Infrastructure as Code
    - Automated rollback and recovery mechanisms
    
    Args:
        project_path: Path to project root
        provider: CI/CD provider (github-actions, gitlab-ci, azure-devops)
        environments: Target environments (default: [dev, staging, production])
        features: Pipeline features to include
        template: Pipeline template (standard, enterprise, security-first)
        output_path: Custom output path for pipeline files
        
    Returns
    -------
        Dict with pipeline generation results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "dod.provider": provider,
        "dod.template": template,
        "dod.environments": str(environments or ["dev", "staging", "production"]),
        "dod.features": str(features or ["testing", "security", "deployment"]),
        "project.path": str(project_path)
    })

    try:
        # Set defaults
        if environments is None:
            environments = ["dev", "staging", "production"]
        if features is None:
            features = ["testing", "security", "deployment", "monitoring"]

        # Generate pipeline files using runtime layer
        pipeline_result = generate_pipeline_files(
            project_path=project_path,
            provider=provider,
            environments=environments,
            features=features,
            template=template,
            output_path=output_path
        )

        if pipeline_result["success"]:
            span.set_attributes({
                "dod.files_created": len(pipeline_result.get("files_created", [])),
                "dod.features_enabled": len(pipeline_result.get("features_enabled", [])),
                "dod.environments_configured": len(environments)
            })

        return pipeline_result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Pipeline generation failed: {e!s}"
        }

@tracer.start_as_current_span("dod.run_e2e_automation")
def run_e2e_automation(
    project_path: Path,
    environment: str = "development",
    parallel: bool = True,
    headless: bool = True,
    record_video: bool = False,
    generate_report: bool = True
) -> dict[str, Any]:
    """
    Execute comprehensive end-to-end automation testing.
    
    Runs complete E2E test automation including:
    - Browser automation (Playwright/Selenium)
    - API testing with full scenario coverage
    - Mobile testing for responsive applications
    - Performance testing under load conditions
    - Security testing with penetration scenarios
    - Accessibility testing for compliance
    
    Args:
        project_path: Path to project root
        environment: Test environment
        parallel: Run tests in parallel
        headless: Run browser tests in headless mode
        record_video: Record test execution videos
        generate_report: Generate detailed test report
        
    Returns
    -------
        Dict with E2E test results and metrics
    """
    span = trace.get_current_span()
    span.set_attributes({
        "dod.environment": environment,
        "dod.parallel": parallel,
        "dod.headless": headless,
        "dod.record_video": record_video,
        "dod.generate_report": generate_report,
        "project.path": str(project_path)
    })

    start_time = time.time()

    try:
        # Execute E2E tests using runtime layer
        e2e_result = run_e2e_tests(
            project_path=project_path,
            environment=environment,
            parallel=parallel,
            headless=headless,
            record_video=record_video,
            generate_report=generate_report
        )

        # Calculate success rate
        test_suites = e2e_result.get("test_suites", {})
        total_tests = sum(suite.get("total", 0) for suite in test_suites.values())
        passed_tests = sum(suite.get("passed", 0) for suite in test_suites.values())
        success_rate = passed_tests / total_tests if total_tests > 0 else 0.0

        e2e_result.update({
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "execution_time": time.time() - start_time
        })

        span.set_attributes({
            "dod.success_rate": success_rate,
            "dod.total_tests": total_tests,
            "dod.passed_tests": passed_tests,
            "dod.execution_time": e2e_result["execution_time"]
        })

        return e2e_result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"E2E testing failed: {e!s}",
            "execution_time": time.time() - start_time,
            "success_rate": 0.0
        }

@tracer.start_as_current_span("dod.analyze_project_status")
def analyze_project_status(
    project_path: Path,
    detailed: bool = False,
    suggestions: bool = True
) -> dict[str, Any]:
    """
    Analyze project Definition of Done status and health.
    
    Provides comprehensive project health assessment including:
    - Overall DoD compliance score
    - Critical criteria status (Testing, Security, DevOps)
    - Automation pipeline health
    - Security posture assessment
    - Code quality metrics
    - Actionable improvement suggestions
    
    Args:
        project_path: Path to project root
        detailed: Include detailed analysis and metrics
        suggestions: Include improvement suggestions
        
    Returns
    -------
        Dict with project health analysis and recommendations
    """
    span = trace.get_current_span()
    span.set_attributes({
        "project.path": str(project_path),
        "dod.detailed": detailed,
        "dod.suggestions": suggestions
    })

    try:
        # Get project health analysis from runtime layer
        health_result = analyze_project_health(
            project_path=project_path,
            detailed=detailed,
            suggestions=suggestions
        )

        if not health_result.get("success", False):
            return health_result

        # Calculate overall health score
        dod_status = health_result.get("dod_status", {})
        overall_score = dod_status.get("overall_score", 0)

        # Determine status level
        if overall_score >= 90:
            status = "EXCELLENT"
        elif overall_score >= 80:
            status = "GOOD"
        elif overall_score >= 70:
            status = "FAIR"
        elif overall_score >= 60:
            status = "NEEDS WORK"
        else:
            status = "CRITICAL"

        span.set_attributes({
            "dod.overall_score": overall_score,
            "dod.status": status
        })

        return {
            "success": True,
            "overall_health_score": overall_score,
            "status": status,
            "dod_compliance": dod_status.get("overall_score", 0),
            "security_score": health_result.get("security_posture", {}).get("score", 0),
            "suggestions": health_result.get("suggestions", [])
        }

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Project status analysis failed: {e!s}"
        }

@tracer.start_as_current_span("dod.generate_dod_report")
def generate_dod_report(project_path: Path, automation_result: dict[str, Any]) -> dict[str, Any]:
    """
    Generate comprehensive Definition of Done completion report.
    
    Creates detailed report with:
    - Executive summary with key metrics
    - Detailed criteria analysis with recommendations
    - Automation performance and efficiency metrics
    - AI-generated insights and next steps
    - Export formats (JSON, Markdown, PDF)
    
    Args:
        project_path: Path to project root
        automation_result: Results from complete automation execution
        
    Returns
    -------
        Dict with generated report and metadata
    """
    span = trace.get_current_span()
    span.set_attributes({
        "project.path": str(project_path),
        "dod.success_rate": automation_result.get("overall_success_rate", 0)
    })

    try:
        # Generate comprehensive report using runtime layer
        report_result = create_automation_report(
            project_path=project_path,
            automation_result=automation_result,
            include_ai_insights=True
        )

        span.set_attributes({
            "dod.report_generated": report_result.get("success", False),
            "dod.report_formats": len(report_result.get("formats_generated", []))
        })

        return report_result

    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Report generation failed: {e!s}"
        }

# Helper functions

def _generate_exoskeleton_structure(template_config: dict[str, Any]) -> dict[str, list[str]]:
    """Generate exoskeleton structure preview for template."""
    base_structure = {
        "automation": [
            ".uvmgr/",
            ".uvmgr/dod.yaml",
            ".uvmgr/exoskeleton.json",
            ".uvmgr/automation/",
            ".uvmgr/automation/workflows/",
            ".uvmgr/automation/templates/"
        ],
        "ci_cd": [
            ".github/workflows/dod-automation.yml",
            ".github/workflows/continuous-validation.yml"
        ],
        "testing": [
            "tests/automation/",
            "tests/e2e/",
            "playwright.config.js",
            "pytest.ini"
        ],
        "security": [
            ".security/",
            ".security/bandit.yml",
            ".security/safety.json"
        ],
        "monitoring": [
            "monitoring/",
            "monitoring/otel-config.yaml",
            "monitoring/grafana/",
            "monitoring/dashboards/"
        ]
    }

    # Add template-specific files
    includes = template_config.get("includes", [])
    if "compliance" in includes:
        base_structure["governance"] = [
            "governance/",
            "governance/policies/",
            "governance/compliance/",
            "governance/audit-trail.json"
        ]

    if "ai_features" in template_config:
        base_structure["ai_integration"] = [
            ".uvmgr/ai/",
            ".uvmgr/ai/prompts/",
            ".uvmgr/ai/models.json",
            ".uvmgr/ai/claude-integration.py"
        ]

    return base_structure

def _calculate_weighted_success_rate(criteria_results: dict[str, Any], criteria: list[str]) -> float:
    """Calculate weighted success rate using 80/20 principles."""
    if not criteria_results:
        return 0.0

    total_weight = 0.0
    weighted_score = 0.0

    for criteria_name in criteria:
        if criteria_name not in criteria_results:
            continue

        criteria_weight = DOD_CRITERIA_WEIGHTS.get(criteria_name, {}).get("weight", 0.05)
        criteria_score = criteria_results[criteria_name].get("score", 0.0)

        # Convert boolean passed to score if needed
        if isinstance(criteria_score, bool):
            criteria_score = 1.0 if criteria_score else 0.0
        elif "passed" in criteria_results[criteria_name]:
            criteria_score = 1.0 if criteria_results[criteria_name]["passed"] else 0.0

        weighted_score += criteria_score * criteria_weight
        total_weight += criteria_weight

    return weighted_score / total_weight if total_weight > 0 else 0.0
