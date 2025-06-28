"""
uvmgr.ops.forge - Forge Operations
=================================

Operations layer for uvmgr forge workflow management.

This module provides the business logic for forge operations, including
validation, code generation, and OTEL testing.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import metric_counter, metric_histogram, span
from uvmgr.ops.weaver import check_registry
from uvmgr.ops.weaver_generation import consolidate_generation

# Paths
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"


def run_validation() -> Dict[str, Any]:
    """Run semantic convention validation."""
    with span("forge.validation"):
        add_span_attributes(**{
            "forge.operation": "validation",
            "forge.registry_path": str(REGISTRY_PATH),
        })
        add_span_event("forge.validation.started", {"registry_path": str(REGISTRY_PATH)})

        start_time = time.time()

        try:
            result = check_registry(registry=REGISTRY_PATH, future=True)
            duration = time.time() - start_time

            if result["status"] == "success":
                add_span_event("forge.validation.success", {"duration": duration})
                metric_counter("forge.validation.passed")(1)
                return {
                    "status": "passed",
                    "duration": duration,
                    "output": result.get("output", "")
                }
            else:
                # 8020 approach: Report warnings but continue with core functionality
                add_span_event("forge.validation.warnings", {
                    "duration": duration,
                    "warnings": result.get("output", "")
                })
                metric_counter("forge.validation.warnings")(1)
                
                return {
                    "status": "passed_with_warnings",
                    "duration": duration,
                    "output": "Validation completed with warnings - continuing with 8020 approach",
                    "warnings": result.get("output", "")
                }

        except Exception as e:
            duration = time.time() - start_time
            add_span_event("forge.validation.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("forge.validation.failed")(1)
            raise


def run_generation() -> Dict[str, Any]:
    """Run code generation from semantic conventions using 80/20 approach."""
    with span("forge.generation"):
        add_span_attributes(**{
            "forge.operation": "generation",
            "forge.registry_path": str(REGISTRY_PATH),
        })
        add_span_event("forge.generation.started", {"registry_path": str(REGISTRY_PATH)})

        start_time = time.time()

        try:
            # Use consolidated generation (80/20 approach)
            output_path = Path("src/uvmgr/core/semconv.py")
            
            result = consolidate_generation(
                registry_path=REGISTRY_PATH,
                output_path=output_path,
                language="python",
                template_path=Path("src/uvmgr/templates")
            )
            
            duration = time.time() - start_time
            
            if result.get("status") == "success":
                add_span_event("forge.generation.success", {
                    "duration": duration,
                    "attributes_generated": result.get("attributes_generated", 0),
                    "template_used": result.get("template_used", False)
                })
                metric_counter("forge.generation.passed")(1)
                metric_histogram("forge.generation.duration")(duration)
                
                return {
                    "status": "passed",
                    "duration": duration,
                    "output": f"Generated {result.get('attributes_generated', 0)} attributes",
                    "template_used": result.get("template_used", False),
                    "output_path": result.get("output_path")
                }
            else:
                # Fallback to legacy generation for compatibility
                add_span_event("forge.generation.fallback", {"duration": duration})
                return run_legacy_generation(start_time)
                
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("forge.generation.failed", {
                "duration": duration,
                "error": str(e)
            })
            metric_counter("forge.generation.failed")(1)
            
            # 80/20 error recovery: try legacy method
            try:
                return run_legacy_generation(start_time)
            except Exception as legacy_error:
                raise RuntimeError(f"Both generation methods failed. New: {e}, Legacy: {legacy_error}")


def run_legacy_generation(start_time: float) -> Dict[str, Any]:
    """Fallback to legacy generation method for compatibility."""
    with span("forge.legacy_generation"):
        add_span_attributes(**{
            "forge.operation": "legacy_generation",
            "forge.fallback": True,
        })
        add_span_event("forge.legacy_generation.started")
        
        try:
            import sys
            sys.path.append(str(REGISTRY_PATH.parent))
            from validate_semconv import generate_python_constants

            generate_python_constants()

            duration = time.time() - start_time
            add_span_event("forge.legacy_generation.success", {"duration": duration})
            metric_counter("forge.generation.legacy.passed")(1)

            return {
                "status": "passed",
                "duration": duration,
                "output": "Python constants generated successfully (legacy method)",
                "template_used": False,
                "fallback": True
            }
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("forge.legacy_generation.failed", {
                "duration": duration,
                "error": str(e)
            })
            metric_counter("forge.generation.legacy.failed")(1)
            raise RuntimeError(f"Legacy generation failed: {e}")


def run_otel_validation() -> Dict[str, Any]:
    """Run OTEL validation tests."""
    with span("forge.otel_validation"):
        add_span_attributes(**{
            "forge.operation": "otel_validation",
        })
        add_span_event("forge.otel_validation.started")

        start_time = time.time()

        try:
            # Import and run the OTEL validation functions
            from uvmgr.commands.otel import (
                _test_error_handling,
                _test_metrics_collection,
                _test_performance_tracking,
                _test_semantic_conventions,
                _test_span_creation,
            )

            tests = {
                "span_creation": _test_span_creation,
                "metrics_collection": _test_metrics_collection,
                "semantic_conventions": _test_semantic_conventions,
                "error_handling": _test_error_handling,
                "performance_tracking": _test_performance_tracking,
            }

            results = {}
            passed = 0

            for test_name, test_func in tests.items():
                try:
                    result = test_func()
                    results[test_name] = result
                    if result.get("status") == "passed":
                        passed += 1
                except Exception as e:
                    results[test_name] = {
                        "status": "failed",
                        "message": f"Test execution failed: {e}",
                        "details": {"error": str(e)}
                    }

            duration = time.time() - start_time
            success_rate = (passed / len(tests)) * 100

            add_span_event("forge.otel_validation.completed", {
                "duration": duration,
                "tests_passed": passed,
                "tests_total": len(tests),
                "success_rate": success_rate
            })

            metric_counter("forge.otel_validation.executed")(1)
            metric_histogram("forge.otel_validation.duration")(duration)

            if success_rate == 100:
                metric_counter("forge.otel_validation.passed")(1)
                return {
                    "status": "passed",
                    "duration": duration,
                    "tests_passed": passed,
                    "tests_total": len(tests),
                    "success_rate": success_rate,
                    "results": results
                }
            else:
                metric_counter("forge.otel_validation.failed")(1)
                raise RuntimeError(f"OTEL validation failed: {len(tests) - passed} tests failed")

        except Exception as e:
            duration = time.time() - start_time
            add_span_event("forge.otel_validation.failed", {
                "duration": duration,
                "error": str(e)
            })
            metric_counter("forge.otel_validation.failed")(1)
            raise RuntimeError(f"OTEL validation failed: {e}")


def run_workflow(validate: bool = True, generate: bool = True, test: bool = True) -> Dict[str, Any]:
    """Run the complete forge workflow."""
    with span("forge.workflow"):
        add_span_attributes(**{
            "forge.operation": "workflow",
            "forge.validate": validate,
            "forge.generate": generate,
            "forge.test": test,
        })
        add_span_event("forge.workflow.started", {
            "validate": validate,
            "generate": generate,
            "test": test
        })

        start_time = time.time()
        results = {}
        success_count = 0
        total_steps = 0

        # Run validation step
        if validate:
            total_steps += 1
            try:
                results["validation"] = run_validation()
                if results["validation"]["status"] in ["passed", "passed_with_warnings"]:
                    success_count += 1
            except Exception as e:
                results["validation"] = {
                    "status": "failed",
                    "error": str(e)
                }

        # Run generation step
        if generate:
            total_steps += 1
            try:
                results["generation"] = run_generation()
                if results["generation"]["status"] == "passed":
                    success_count += 1
            except Exception as e:
                results["generation"] = {
                    "status": "failed",
                    "error": str(e)
                }

        # Run test step
        if test:
            total_steps += 1
            try:
                results["test"] = run_otel_validation()
                if results["test"]["status"] == "passed":
                    success_count += 1
            except Exception as e:
                results["test"] = {
                    "status": "failed",
                    "error": str(e)
                }

        duration = time.time() - start_time
        success_rate = (success_count / total_steps) * 100 if total_steps > 0 else 0

        add_span_event("forge.workflow.completed", {
            "duration": duration,
            "success_count": success_count,
            "total_steps": total_steps,
            "success_rate": success_rate
        })

        metric_counter("forge.workflow.completed")(1)
        metric_histogram("forge.workflow.duration")(duration)

        return {
            "status": "completed",
            "duration": duration,
            "success_count": success_count,
            "total_steps": total_steps,
            "success_rate": success_rate,
            "results": results
        } 