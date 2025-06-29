"""
Test execution operations for uvmgr.

This module provides the business logic layer for test execution,
coordinating between commands and runtime execution. It follows the
80/20 principle by focusing on the most impactful testing operations.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.core.semconv import TestAttributes, TestCoverageAttributes, CIAttributes, CIOperations
from uvmgr.runtime import tests as tests_runtime


def run_test_suite(
    verbose: bool = False,
    parallel: bool = True,
    coverage: bool = True,
    fail_fast: bool = False,
    test_types: Optional[List[str]] = None,
    markers: Optional[List[str]] = None,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Run the complete test suite.
    
    Parameters
    ----------
    verbose : bool
        Whether to run tests verbosely
    parallel : bool
        Whether to run tests in parallel
    coverage : bool
        Whether to collect coverage data
    fail_fast : bool
        Whether to stop on first failure
    test_types : Optional[List[str]]
        Test types to run (unit, integration, e2e)
    markers : Optional[List[str]]
        Test markers to run
    generate_report : bool
        Whether to generate comprehensive test report
        
    Returns
    -------
    Dict[str, Any]
        Test execution results including metrics and coverage
    """
    with span("tests.run_suite") as current_span:
        start_time = time.time()
        
        add_span_attributes(**{
            TestAttributes.OPERATION: "run",
            TestAttributes.FRAMEWORK: "pytest",
            "test.verbose": verbose,
            "test.parallel": parallel,
            "test.coverage": coverage,
            "test.fail_fast": fail_fast,
        })
        
        # Delegate to runtime
        result = tests_runtime.execute_pytest(
            verbose=verbose,
            parallel=parallel,
            coverage=coverage,
            fail_fast=fail_fast,
            test_types=test_types or [],
            markers=markers or [],
            generate_report=generate_report
        )
        
        # Add result attributes
        execution_time = time.time() - start_time
        add_span_attributes(**{
            TestAttributes.TEST_COUNT: result.get("total_tests", 0),
            TestAttributes.PASSED: result.get("passed", 0),
            TestAttributes.FAILED: result.get("failed", 0),
            TestAttributes.SKIPPED: result.get("skipped", 0),
            "test.execution_time": execution_time,
            "test.success": result.get("success", False),
        })
        
        if coverage and result.get("coverage"):
            add_span_attributes(**{
                TestCoverageAttributes.COVERAGE_PERCENTAGE: result["coverage"]["percentage"]
            })
        
        return result


def generate_coverage_report(
    format_type: str = "html",
    min_coverage: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate coverage reports.
    
    Parameters
    ----------
    format_type : str
        Format type (html, xml, term)
    min_coverage : Optional[float]
        Minimum coverage threshold
        
    Returns
    -------
    Dict[str, Any]
        Coverage report results
    """
    with span("tests.coverage_report") as current_span:
        add_span_attributes(**{
            TestAttributes.OPERATION: "coverage",
            "coverage.format": format_type,
            "coverage.min_threshold": min_coverage,
        })
        
        # Delegate to runtime
        result = tests_runtime.generate_coverage_report(
            format_type=format_type,
            min_coverage=min_coverage
        )
        
        add_span_attributes(**{
            TestCoverageAttributes.COVERAGE_PERCENTAGE: result.get("percentage", 0),
            "coverage.success": result.get("success", False),
        })
        
        return result


def run_ci_verification(
    quick: bool = False,
    comprehensive: bool = True
) -> Dict[str, Any]:
    """
    Run CI verification pipeline.
    
    Parameters
    ----------
    quick : bool
        Whether to run quick checks only
    comprehensive : bool
        Whether to run comprehensive verification
        
    Returns
    -------
    Dict[str, Any]
        CI verification results
    """
    with span("tests.ci_verification") as current_span:
        start_time = time.time()
        
        operation = CIOperations.QUICK_TEST if quick else CIOperations.VERIFY
        add_span_attributes(**{
            CIAttributes.OPERATION: operation,
            CIAttributes.RUNNER: "uvmgr",
            "ci.quick": quick,
            "ci.comprehensive": comprehensive,
        })
        
        # Delegate to runtime
        result = tests_runtime.run_ci_pipeline(
            quick=quick,
            comprehensive=comprehensive
        )
        
        # Calculate metrics
        execution_time = time.time() - start_time
        total_tests = result.get("test_results", {}).get("total_tests", 0)
        passed_tests = result.get("test_results", {}).get("passed", 0)
        failed_tests = result.get("test_results", {}).get("failed", 0)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        add_span_attributes(**{
            CIAttributes.TEST_COUNT: total_tests,
            CIAttributes.PASSED: passed_tests,
            CIAttributes.FAILED: failed_tests,
            CIAttributes.DURATION: execution_time,
            CIAttributes.SUCCESS_RATE: success_rate,
        })
        
        return result


def discover_tests(
    path: Optional[Path] = None,
    pattern: str = "test_*.py"
) -> Dict[str, Any]:
    """
    Discover available tests in the project.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to search for tests
    pattern : str
        Test file pattern
        
    Returns
    -------
    Dict[str, Any]
        Test discovery results
    """
    with span("tests.discover"):
        add_span_attributes(**{
            TestAttributes.OPERATION: "discover",
            "test.path": str(path) if path else ".",
            "test.pattern": pattern,
        })
        
        # Delegate to runtime
        result = tests_runtime.discover_test_files(
            path=path,
            pattern=pattern
        )
        
        add_span_attributes(**{
            "test.files_found": len(result.get("test_files", [])),
            "test.types_found": len(result.get("test_types", [])),
        })
        
        return result


def validate_test_environment() -> Dict[str, Any]:
    """
    Validate that the test environment is properly configured.
    
    Returns
    -------
    Dict[str, Any]
        Environment validation results
    """
    with span("tests.validate_environment"):
        add_span_attributes(**{
            TestAttributes.OPERATION: "validate",
        })
        
        # Delegate to runtime
        result = tests_runtime.validate_test_environment()
        
        add_span_attributes(**{
            "test.environment_valid": result.get("valid", False),
            "test.dependencies_available": result.get("dependencies_available", False),
        })
        
        return result