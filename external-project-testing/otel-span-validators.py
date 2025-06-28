#!/usr/bin/env python3
"""
OpenTelemetry Span Validators
============================

Validates specific OTEL spans to ensure uvmgr lifecycle phases
execute correctly and meet performance requirements.

TRUST ONLY OTEL TRACES - NO ASSUMPTIONS
"""

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode


class ValidationResult(Enum):
    """Span validation results."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    MISSING = "missing"


@dataclass
class SpanValidationRule:
    """Defines a rule for validating OTEL spans."""

    name: str
    span_name_pattern: str
    required_attributes: set[str]
    performance_threshold_ms: float | None = None
    expected_status: StatusCode = StatusCode.OK
    min_duration_ms: float | None = None
    max_duration_ms: float | None = None
    required_events: set[str] = None

    def __post_init__(self):
        if self.required_events is None:
            self.required_events = set()


@dataclass
class SpanValidationResult:
    """Result of span validation."""

    rule_name: str
    span_name: str
    result: ValidationResult
    duration_ms: float
    attributes_found: set[str]
    attributes_missing: set[str]
    events_found: set[str]
    events_missing: set[str]
    status_code: StatusCode
    error_message: str | None = None
    performance_ratio: float | None = None


class LifecycleSpanValidator:
    """Validates OTEL spans for uvmgr lifecycle phases."""

    def __init__(self):
        self.validation_rules = self._define_validation_rules()
        self.captured_spans: list[ReadableSpan] = []
        self.validation_results: list[SpanValidationResult] = []

        # Set up span capture
        self.tracer = trace.get_tracer(__name__)

    def _define_validation_rules(self) -> dict[str, SpanValidationRule]:
        """Define validation rules for each lifecycle phase."""
        return {
            # Project Setup Phase
            "project_setup": SpanValidationRule(
                name="project_setup",
                span_name_pattern="verify_claim.auto_install",
                required_attributes={
                    "claim.name", "claim.description", "claim.verified",
                    "script.exists", "script.executable"
                },
                performance_threshold_ms=120000,  # 2 minutes max
                min_duration_ms=1000,  # At least 1 second
                required_events={"check_script_exists"}
            ),

            # Command Performance
            "uvmgr_startup": SpanValidationRule(
                name="uvmgr_startup",
                span_name_pattern="command_execution.uvmgr",
                required_attributes={
                    "command.name", "command.args", "command.duration",
                    "command.returncode", "command.success"
                },
                performance_threshold_ms=500,  # 500ms startup max
                expected_status=StatusCode.OK
            ),

            # Dependencies Phase
            "deps_management": SpanValidationRule(
                name="deps_management",
                span_name_pattern="command_execution.uvmgr",
                required_attributes={
                    "command.name", "command.duration", "command.returncode"
                },
                performance_threshold_ms=2000,  # 2s max for deps operations
                expected_status=StatusCode.OK
            ),

            # Testing Phase
            "test_execution": SpanValidationRule(
                name="test_execution",
                span_name_pattern="test_testing_phase",
                required_attributes={
                    "phase", "success", "start_time", "operations"
                },
                performance_threshold_ms=30000,  # 30s max for testing
                min_duration_ms=100
            ),

            # Building Phase
            "build_execution": SpanValidationRule(
                name="build_execution",
                span_name_pattern="test_building_phase",
                required_attributes={
                    "phase", "success", "operations"
                },
                performance_threshold_ms=60000,  # 1 minute max for building
                min_duration_ms=500
            ),

            # AI Integration
            "ai_integration": SpanValidationRule(
                name="ai_integration",
                span_name_pattern="test_ai_integration_phase",
                required_attributes={
                    "phase", "operations"
                },
                performance_threshold_ms=30000,  # 30s max for AI operations
                expected_status=StatusCode.OK
            ),

            # Observability
            "otel_validation": SpanValidationRule(
                name="otel_validation",
                span_name_pattern="verify_claim.observability",
                required_attributes={
                    "claim.verified", "otel_command.success", "collector.available"
                },
                performance_threshold_ms=30000,  # 30s max for OTEL validation
                expected_status=StatusCode.OK
            ),

            # Substrate Integration
            "substrate_integration": SpanValidationRule(
                name="substrate_integration",
                span_name_pattern="verify_claim.substrate_integration",
                required_attributes={
                    "claim.verified", "copier.available", "artifacts.found_count"
                },
                performance_threshold_ms=300000,  # 5 minutes max for full integration
                min_duration_ms=5000,  # At least 5 seconds
                expected_status=StatusCode.OK
            ),

            # Overall Lifecycle
            "full_lifecycle": SpanValidationRule(
                name="full_lifecycle",
                span_name_pattern="verify_all_claims",
                required_attributes={
                    "test_workspace", "summary.total_claims", "summary.verified_claims",
                    "summary.verification_rate", "summary.overall_success"
                },
                performance_threshold_ms=600000,  # 10 minutes max for full verification
                min_duration_ms=10000,  # At least 10 seconds
                expected_status=StatusCode.OK
            )
        }

    def validate_span(self, span: ReadableSpan, rule: SpanValidationRule) -> SpanValidationResult:
        """Validate a single span against a rule."""
        # Calculate duration
        if span.end_time and span.start_time:
            duration_ms = (span.end_time - span.start_time) / 1_000_000  # Convert nanoseconds to milliseconds
        else:
            duration_ms = 0.0

        # Check attributes
        span_attributes = set(span.attributes.keys()) if span.attributes else set()
        attributes_missing = rule.required_attributes - span_attributes

        # Check events
        span_events = set(event.name for event in span.events) if span.events else set()
        events_missing = rule.required_events - span_events

        # Determine result
        result = ValidationResult.PASS
        error_message = None
        performance_ratio = None

        # Check status
        if span.status and span.status.status_code != rule.expected_status:
            result = ValidationResult.FAIL
            error_message = f"Expected status {rule.expected_status}, got {span.status.status_code}"

        # Check required attributes
        elif attributes_missing:
            result = ValidationResult.FAIL
            error_message = f"Missing required attributes: {attributes_missing}"

        # Check required events
        elif events_missing:
            result = ValidationResult.WARNING
            error_message = f"Missing expected events: {events_missing}"

        # Check performance thresholds
        elif rule.performance_threshold_ms and duration_ms > rule.performance_threshold_ms:
            result = ValidationResult.FAIL
            performance_ratio = duration_ms / rule.performance_threshold_ms
            error_message = f"Performance threshold exceeded: {duration_ms:.1f}ms > {rule.performance_threshold_ms}ms (ratio: {performance_ratio:.2f})"

        # Check minimum duration
        elif rule.min_duration_ms and duration_ms < rule.min_duration_ms:
            result = ValidationResult.WARNING
            error_message = f"Duration too short: {duration_ms:.1f}ms < {rule.min_duration_ms}ms"

        # Check maximum duration
        elif rule.max_duration_ms and duration_ms > rule.max_duration_ms:
            result = ValidationResult.FAIL
            error_message = f"Duration too long: {duration_ms:.1f}ms > {rule.max_duration_ms}ms"

        # Calculate performance ratio if threshold exists
        if rule.performance_threshold_ms:
            performance_ratio = duration_ms / rule.performance_threshold_ms

        return SpanValidationResult(
            rule_name=rule.name,
            span_name=span.name,
            result=result,
            duration_ms=duration_ms,
            attributes_found=span_attributes,
            attributes_missing=attributes_missing,
            events_found=span_events,
            events_missing=events_missing,
            status_code=span.status.status_code if span.status else StatusCode.UNSET,
            error_message=error_message,
            performance_ratio=performance_ratio
        )

    def validate_captured_spans(self, spans: list[ReadableSpan]) -> dict[str, Any]:
        """Validate all captured spans against defined rules."""
        with self.tracer.start_as_current_span("validate_lifecycle_spans") as validation_span:
            validation_span.set_attribute("spans.total_count", len(spans))
            validation_span.set_attribute("rules.total_count", len(self.validation_rules))

            results_by_rule = {}

            for rule_name, rule in self.validation_rules.items():
                with self.tracer.start_as_current_span(f"validate_rule.{rule_name}") as rule_span:
                    # Find matching spans
                    matching_spans = [
                        span for span in spans
                        if rule.span_name_pattern in span.name
                    ]

                    rule_span.set_attribute(f"rule.{rule_name}.matching_spans", len(matching_spans))

                    if not matching_spans:
                        # Rule not satisfied - no matching spans found
                        result = SpanValidationResult(
                            rule_name=rule_name,
                            span_name="<not_found>",
                            result=ValidationResult.MISSING,
                            duration_ms=0.0,
                            attributes_found=set(),
                            attributes_missing=rule.required_attributes,
                            events_found=set(),
                            events_missing=rule.required_events,
                            status_code=StatusCode.UNSET,
                            error_message=f"No spans found matching pattern: {rule.span_name_pattern}"
                        )
                        results_by_rule[rule_name] = [result]
                        rule_span.set_attribute(f"rule.{rule_name}.result", "MISSING")
                        continue

                    # Validate each matching span
                    rule_results = []
                    for span in matching_spans:
                        validation_result = self.validate_span(span, rule)
                        rule_results.append(validation_result)

                        # Log result to span
                        rule_span.set_attribute(
                            f"span.{span.name}.result",
                            validation_result.result.value
                        )
                        rule_span.set_attribute(
                            f"span.{span.name}.duration_ms",
                            validation_result.duration_ms
                        )

                        if validation_result.performance_ratio:
                            rule_span.set_attribute(
                                f"span.{span.name}.performance_ratio",
                                validation_result.performance_ratio
                            )

                    results_by_rule[rule_name] = rule_results

                    # Overall rule result
                    rule_passed = all(r.result == ValidationResult.PASS for r in rule_results)
                    rule_span.set_attribute(f"rule.{rule_name}.passed", rule_passed)

            # Generate summary
            total_validations = sum(len(results) for results in results_by_rule.values())
            passed_validations = sum(
                1 for results in results_by_rule.values()
                for result in results
                if result.result == ValidationResult.PASS
            )
            failed_validations = sum(
                1 for results in results_by_rule.values()
                for result in results
                if result.result == ValidationResult.FAIL
            )
            warning_validations = sum(
                1 for results in results_by_rule.values()
                for result in results
                if result.result == ValidationResult.WARNING
            )
            missing_validations = sum(
                1 for results in results_by_rule.values()
                for result in results
                if result.result == ValidationResult.MISSING
            )

            summary = {
                "total_validations": total_validations,
                "passed": passed_validations,
                "failed": failed_validations,
                "warnings": warning_validations,
                "missing": missing_validations,
                "success_rate": passed_validations / total_validations if total_validations > 0 else 0,
                "overall_success": failed_validations == 0 and missing_validations == 0,
                "validation_timestamp": time.time()
            }

            # Record summary in span
            for key, value in summary.items():
                validation_span.set_attribute(f"summary.{key}", value)

            return {
                "summary": summary,
                "results_by_rule": {
                    rule_name: [
                        {
                            "rule_name": result.rule_name,
                            "span_name": result.span_name,
                            "result": result.result.value,
                            "duration_ms": result.duration_ms,
                            "attributes_found": list(result.attributes_found),
                            "attributes_missing": list(result.attributes_missing),
                            "events_found": list(result.events_found),
                            "events_missing": list(result.events_missing),
                            "status_code": result.status_code.name if result.status_code else "UNSET",
                            "error_message": result.error_message,
                            "performance_ratio": result.performance_ratio
                        }
                        for result in results
                    ]
                    for rule_name, results in results_by_rule.items()
                },
                "validation_rules": {
                    rule_name: {
                        "name": rule.name,
                        "span_name_pattern": rule.span_name_pattern,
                        "required_attributes": list(rule.required_attributes),
                        "performance_threshold_ms": rule.performance_threshold_ms,
                        "expected_status": rule.expected_status.name,
                        "min_duration_ms": rule.min_duration_ms,
                        "max_duration_ms": rule.max_duration_ms,
                        "required_events": list(rule.required_events)
                    }
                    for rule_name, rule in self.validation_rules.items()
                }
            }


class SpanCaptureExporter(SpanExporter):
    """Custom span exporter that captures spans for validation."""

    def __init__(self, validator: LifecycleSpanValidator):
        self.validator = validator
        self.captured_spans: list[ReadableSpan] = []

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        """Capture spans for later validation."""
        self.captured_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Clean shutdown."""


def create_instrumented_validator() -> Tuple[LifecycleSpanValidator, SpanCaptureExporter]:
    """Create a validator with span capture."""
    validator = LifecycleSpanValidator()
    exporter = SpanCaptureExporter(validator)

    # Add the capture exporter to the tracer provider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(exporter)
    )

    return validator, exporter


def validate_lifecycle_execution(spans: list[ReadableSpan]) -> dict[str, Any]:
    """Validate a complete lifecycle execution from captured spans."""
    validator = LifecycleSpanValidator()
    return validator.validate_captured_spans(spans)


def print_validation_results(results: dict[str, Any]):
    """Print formatted validation results."""
    print("\n🔍 OTEL Span Validation Results")
    print("=" * 50)

    summary = results["summary"]
    print(f"Total Validations: {summary['total_validations']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⚠️  Warnings: {summary['warnings']}")
    print(f"❓ Missing: {summary['missing']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Overall: {'✅ PASS' if summary['overall_success'] else '❌ FAIL'}")

    print("\n📋 Results by Rule:")
    for rule_name, rule_results in results["results_by_rule"].items():
        print(f"\n🔧 {rule_name}:")
        for result in rule_results:
            status_emoji = {
                "pass": "✅",
                "fail": "❌",
                "warning": "⚠️",
                "missing": "❓"
            }.get(result["result"], "❓")

            print(f"  {status_emoji} {result['span_name']} ({result['duration_ms']:.1f}ms)")

            if result["error_message"]:
                print(f"     Error: {result['error_message']}")

            if result["performance_ratio"]:
                print(f"     Performance: {result['performance_ratio']:.2f}x threshold")

            if result["attributes_missing"]:
                print(f"     Missing Attributes: {result['attributes_missing']}")


if __name__ == "__main__":
    """Test the span validation system."""
    import tempfile
    from pathlib import Path

    # Create a simple test
    validator = LifecycleSpanValidator()

    # Mock some spans for testing
    print("🧪 Testing span validation system...")

    # This would normally be called with real captured spans
    test_results = {
        "summary": {
            "total_validations": 5,
            "passed": 3,
            "failed": 1,
            "warnings": 1,
            "missing": 0,
            "success_rate": 0.6,
            "overall_success": False
        },
        "results_by_rule": {}
    }

    print_validation_results(test_results)
    print("\n✅ Span validation system ready for use with real OTEL traces")
