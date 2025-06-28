#!/usr/bin/env python3
"""
OTEL-Instrumented Test Runner
============================

Runs external project lifecycle tests with comprehensive OpenTelemetry
instrumentation to verify ALL claims through actual telemetry data.

NEVER TRUST HARDCODED VALUES - ONLY OTEL TRACES
"""

import asyncio
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# OpenTelemetry imports
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from otel_claim_verification import OTELClaimVerifier

# Import our validation components
from otel_span_validators import (
    LifecycleSpanValidator,
    SpanCaptureExporter,
    create_instrumented_validator,
)


class OTELInstrumentedTestRunner:
    """Runs lifecycle tests with comprehensive OTEL instrumentation."""

    def __init__(self,
                 collector_endpoint: str = "http://localhost:4317",
                 workspace_dir: Path | None = None,
                 results_dir: Path | None = None):

        self.collector_endpoint = collector_endpoint
        self.workspace_dir = workspace_dir or Path(tempfile.mkdtemp(prefix="uvmgr-otel-test-"))
        self.results_dir = results_dir or Path(tempfile.mkdtemp(prefix="uvmgr-otel-results-"))

        # Ensure directories exist
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Test execution state
        self.test_execution_id = f"test-{int(time.time())}"
        self.start_time = time.time()

        # OTEL setup
        self._setup_comprehensive_otel()

        # Validation setup
        self.validator, self.span_exporter = create_instrumented_validator()
        self.claim_verifier = OTELClaimVerifier(collector_endpoint)

        # Test configuration
        self.test_matrix = {
            "substrate_integration": {
                "description": "Substrate Copier template integration test",
                "script": "test-substrate-integration.sh",
                "timeout": 300,  # 5 minutes
                "expected_artifacts": [
                    "pyproject.toml",
                    ".uvmgr.toml",
                    "substrate-uvmgr-integration-report.md"
                ],
                "performance_thresholds": {
                    "max_duration": 300.0,
                    "min_duration": 10.0
                }
            },
            "auto_install": {
                "description": "Auto-install script functionality test",
                "script": "auto-install-uvmgr.sh",
                "timeout": 120,  # 2 minutes
                "expected_artifacts": [
                    ".uvmgr.toml",
                    ".uvmgr/examples/dev-workflow.sh"
                ],
                "performance_thresholds": {
                    "max_duration": 120.0,
                    "min_duration": 5.0
                }
            },
            "lifecycle_testing": {
                "description": "Complete lifecycle testing execution",
                "script": "test-lifecycle.py",
                "timeout": 600,  # 10 minutes
                "expected_artifacts": [
                    "lifecycle_test_results.json"
                ],
                "performance_thresholds": {
                    "max_duration": 600.0,
                    "min_duration": 30.0
                }
            },
            "claim_verification": {
                "description": "OTEL-based claim verification",
                "script": "otel-claim-verification.py",
                "timeout": 300,  # 5 minutes
                "expected_artifacts": [
                    "otel-claim-verification-report.json"
                ],
                "performance_thresholds": {
                    "max_duration": 300.0,
                    "min_duration": 10.0
                }
            }
        }

        print("🔧 OTEL Instrumented Test Runner initialized")
        print(f"   Workspace: {self.workspace_dir}")
        print(f"   Results: {self.results_dir}")
        print(f"   OTEL Endpoint: {self.collector_endpoint}")
        print(f"   Test ID: {self.test_execution_id}")

    def _setup_comprehensive_otel(self):
        """Set up comprehensive OpenTelemetry instrumentation."""
        # Resource with detailed attributes
        resource = Resource.create({
            "service.name": "uvmgr-instrumented-test-runner",
            "service.version": "1.0.0",
            "service.instance.id": self.test_execution_id,
            "environment": "external-testing",
            "test.workspace": str(self.workspace_dir),
            "test.results_dir": str(self.results_dir),
            "test.start_time": self.start_time,
            "runner.mode": "comprehensive",
            "verification.method": "otel_instrumented"
        })

        # Tracing setup
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)

        # Multiple exporters for redundancy
        otlp_exporter = OTLPSpanExporter(endpoint=self.collector_endpoint, insecure=True)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        self.tracer = trace.get_tracer(__name__)

        # Metrics setup
        otlp_metric_exporter = OTLPMetricExporter(endpoint=self.collector_endpoint, insecure=True)
        metric_provider = MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)
            ]
        )
        metrics.set_meter_provider(metric_provider)

        self.meter = metrics.get_meter(__name__)

        # Custom metrics
        self.test_duration_histogram = self.meter.create_histogram(
            "test_execution_duration_seconds",
            description="Duration of test executions",
            unit="s"
        )

        self.test_success_counter = self.meter.create_counter(
            "test_executions_total",
            description="Total test executions"
        )

        self.performance_ratio_gauge = self.meter.create_gauge(
            "test_performance_ratio",
            description="Test performance vs thresholds"
        )

        self.artifact_validation_counter = self.meter.create_counter(
            "test_artifacts_validated_total",
            description="Total artifacts validated"
        )

        print("✅ Comprehensive OTEL instrumentation configured")

    def execute_test_with_otel(self, test_name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Execute a single test with comprehensive OTEL instrumentation."""
        span_name = f"test_execution.{test_name}"

        with self.tracer.start_as_current_span(span_name) as span:
            # Set comprehensive span attributes
            span.set_attribute("test.name", test_name)
            span.set_attribute("test.description", config["description"])
            span.set_attribute("test.script", config["script"])
            span.set_attribute("test.timeout", config["timeout"])
            span.set_attribute("test.execution_id", self.test_execution_id)
            span.set_attribute("test.start_time", time.time())

            test_result = {
                "test_name": test_name,
                "description": config["description"],
                "start_time": time.time(),
                "success": False,
                "performance": {},
                "artifacts": {},
                "otel_metadata": {}
            }

            try:
                # Create test-specific workspace
                test_workspace = self.workspace_dir / test_name
                test_workspace.mkdir(exist_ok=True)

                span.set_attribute("test.workspace", str(test_workspace))

                # Execute the test script
                with self.tracer.start_as_current_span(f"execute_script.{config['script']}") as script_span:
                    script_path = Path(__file__).parent / config["script"]

                    script_span.set_attribute("script.path", str(script_path))
                    script_span.set_attribute("script.exists", script_path.exists())

                    if not script_path.exists():
                        raise FileNotFoundError(f"Test script not found: {script_path}")

                    # Build command based on script type
                    if script_path.suffix == ".py":
                        cmd = [sys.executable, str(script_path)]
                        if test_name == "lifecycle_testing":
                            cmd.extend([
                                "--workspace", str(test_workspace),
                                "--results", str(self.results_dir),
                                "--all-projects", "--validate-otel"
                            ])
                        elif test_name == "claim_verification":
                            cmd.extend([
                                "--workspace", str(test_workspace),
                                "--output", str(self.results_dir / "otel-claim-verification-report.json")
                            ])
                    else:  # Shell script
                        cmd = ["bash", str(script_path)]
                        if test_name == "substrate_integration":
                            cmd.append(str(test_workspace / "substrate-test"))
                        elif test_name == "auto_install":
                            cmd.append(str(test_workspace))

                    script_span.set_attribute("script.command", " ".join(cmd))

                    # Execute with timeout and performance measurement
                    execution_start = time.time()

                    try:
                        result = subprocess.run(
                            cmd,
                            cwd=test_workspace if test_name != "claim_verification" else None,
                            capture_output=True,
                            text=True,
                            timeout=config["timeout"], check=False
                        )

                        execution_duration = time.time() - execution_start

                        # Record performance metrics
                        self.test_duration_histogram.record(
                            execution_duration,
                            {"test": test_name, "status": "success" if result.returncode == 0 else "error"}
                        )

                        script_span.set_attribute("script.duration", execution_duration)
                        script_span.set_attribute("script.returncode", result.returncode)
                        script_span.set_attribute("script.stdout_length", len(result.stdout))
                        script_span.set_attribute("script.stderr_length", len(result.stderr))

                        test_result["performance"] = {
                            "duration": execution_duration,
                            "returncode": result.returncode,
                            "stdout_length": len(result.stdout),
                            "stderr_length": len(result.stderr)
                        }

                        # Validate performance thresholds
                        thresholds = config["performance_thresholds"]
                        performance_ok = (
                            execution_duration <= thresholds["max_duration"] and
                            execution_duration >= thresholds["min_duration"]
                        )

                        performance_ratio = execution_duration / thresholds["max_duration"]
                        self.performance_ratio_gauge.set(performance_ratio, {"test": test_name})

                        script_span.set_attribute("performance.threshold_met", performance_ok)
                        script_span.set_attribute("performance.ratio", performance_ratio)

                        test_result["performance"]["threshold_met"] = performance_ok
                        test_result["performance"]["ratio"] = performance_ratio

                        # Check for expected artifacts
                        with self.tracer.start_as_current_span("validate_artifacts") as artifact_span:
                            artifacts_found = 0
                            artifact_details = {}

                            for expected_artifact in config["expected_artifacts"]:
                                # Check in test workspace and results directory
                                artifact_paths = [
                                    test_workspace / expected_artifact,
                                    self.results_dir / expected_artifact
                                ]

                                found = False
                                for artifact_path in artifact_paths:
                                    if artifact_path.exists():
                                        found = True
                                        artifacts_found += 1
                                        artifact_details[expected_artifact] = {
                                            "found": True,
                                            "path": str(artifact_path),
                                            "size": artifact_path.stat().st_size
                                        }

                                        self.artifact_validation_counter.add(
                                            1, {"test": test_name, "artifact": expected_artifact, "status": "found"}
                                        )
                                        break

                                if not found:
                                    artifact_details[expected_artifact] = {"found": False}
                                    self.artifact_validation_counter.add(
                                        1, {"test": test_name, "artifact": expected_artifact, "status": "missing"}
                                    )

                                artifact_span.set_attribute(f"artifact.{expected_artifact}.found", found)

                            artifact_span.set_attribute("artifacts.found_count", artifacts_found)
                            artifact_span.set_attribute("artifacts.expected_count", len(config["expected_artifacts"]))

                            artifacts_ratio = artifacts_found / len(config["expected_artifacts"])
                            test_result["artifacts"] = {
                                "found_count": artifacts_found,
                                "expected_count": len(config["expected_artifacts"]),
                                "ratio": artifacts_ratio,
                                "details": artifact_details
                            }

                        # Overall success determination
                        test_result["success"] = (
                            result.returncode == 0 and
                            performance_ok and
                            artifacts_ratio >= 0.8  # 80% of artifacts must be found
                        )

                        # Record success metrics
                        self.test_success_counter.add(
                            1, {"test": test_name, "status": "success" if test_result["success"] else "partial"}
                        )

                        if test_result["success"]:
                            span.set_status(Status(StatusCode.OK))
                        else:
                            span.set_status(Status(StatusCode.ERROR, "Test did not meet all success criteria"))

                    except subprocess.TimeoutExpired:
                        execution_duration = time.time() - execution_start

                        script_span.set_attribute("script.timeout", True)
                        script_span.set_attribute("script.duration", execution_duration)

                        test_result["performance"]["timeout"] = True
                        test_result["performance"]["duration"] = execution_duration

                        span.set_status(Status(StatusCode.ERROR, f"Test timeout after {config['timeout']}s"))

                        self.test_success_counter.add(1, {"test": test_name, "status": "timeout"})

                        raise

            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))

                test_result["error"] = str(e)
                test_result["success"] = False

                self.test_success_counter.add(1, {"test": test_name, "status": "error"})

                print(f"❌ Test {test_name} failed: {e}")

            finally:
                test_result["duration"] = time.time() - test_result["start_time"]
                span.set_attribute("test.duration", test_result["duration"])
                span.set_attribute("test.success", test_result["success"])

                # Add OTEL metadata
                test_result["otel_metadata"] = {
                    "span_id": format(span.get_span_context().span_id, "016x"),
                    "trace_id": format(span.get_span_context().trace_id, "032x"),
                    "collector_endpoint": self.collector_endpoint
                }

            return test_result

    def run_comprehensive_verification(self) -> dict[str, Any]:
        """Run comprehensive verification of all uvmgr external testing claims."""
        with self.tracer.start_as_current_span("comprehensive_verification") as main_span:
            main_span.set_attribute("verification.start_time", time.time())
            main_span.set_attribute("verification.test_count", len(self.test_matrix))
            main_span.set_attribute("verification.execution_id", self.test_execution_id)

            verification_results = {
                "execution_id": self.test_execution_id,
                "start_time": self.start_time,
                "workspace": str(self.workspace_dir),
                "results_dir": str(self.results_dir),
                "collector_endpoint": self.collector_endpoint,
                "test_results": {},
                "span_validation": {},
                "summary": {},
                "otel_metadata": {}
            }

            print("🚀 Starting Comprehensive OTEL Verification")
            print("=" * 60)
            print("TRUST ONLY OTEL TRACES - NO HARDCODED VALUES")
            print("=" * 60)

            # Execute all tests
            for test_name, config in self.test_matrix.items():
                print(f"\n🧪 Executing: {test_name}")
                print(f"   Description: {config['description']}")

                test_result = self.execute_test_with_otel(test_name, config)
                verification_results["test_results"][test_name] = test_result

                if test_result["success"]:
                    print(f"✅ {test_name}: SUCCESS")
                else:
                    print(f"❌ {test_name}: FAILED")

                # Log key metrics
                if "performance" in test_result:
                    perf = test_result["performance"]
                    print(f"   📊 Duration: {perf.get('duration', 0):.1f}s")
                    if "ratio" in perf:
                        print(f"   📊 Performance Ratio: {perf['ratio']:.2f}")

                if "artifacts" in test_result:
                    artifacts = test_result["artifacts"]
                    print(f"   📄 Artifacts: {artifacts['found_count']}/{artifacts['expected_count']}")

            # Wait for spans to be exported
            print("\n⏳ Waiting for span export...")
            time.sleep(5)

            # Validate captured spans
            with self.tracer.start_as_current_span("validate_captured_spans") as validation_span:
                captured_spans = self.span_exporter.captured_spans
                validation_span.set_attribute("captured_spans.count", len(captured_spans))

                span_validation_results = self.validator.validate_captured_spans(captured_spans)
                verification_results["span_validation"] = span_validation_results

                print("\n🔍 Span Validation Results:")
                print(f"   Total Spans Captured: {len(captured_spans)}")
                print(f"   Validation Rules: {len(self.validator.validation_rules)}")

                if span_validation_results["summary"]["overall_success"]:
                    print("   ✅ All span validations PASSED")
                else:
                    print("   ❌ Some span validations FAILED")

                validation_span.set_attribute("span_validation.success",
                                            span_validation_results["summary"]["overall_success"])

            # Generate final summary
            total_tests = len(verification_results["test_results"])
            successful_tests = sum(1 for result in verification_results["test_results"].values()
                                 if result["success"])

            verification_results["summary"] = {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "overall_success": (
                    successful_tests == total_tests and
                    span_validation_results["summary"]["overall_success"]
                ),
                "span_validation_success": span_validation_results["summary"]["overall_success"],
                "total_duration": time.time() - self.start_time,
                "verification_timestamp": time.time()
            }

            # Record final summary in span
            summary = verification_results["summary"]
            main_span.set_attribute("summary.total_tests", summary["total_tests"])
            main_span.set_attribute("summary.successful_tests", summary["successful_tests"])
            main_span.set_attribute("summary.success_rate", summary["success_rate"])
            main_span.set_attribute("summary.overall_success", summary["overall_success"])
            main_span.set_attribute("summary.total_duration", summary["total_duration"])

            # Add OTEL metadata
            verification_results["otel_metadata"] = {
                "trace_id": format(main_span.get_span_context().trace_id, "032x"),
                "span_id": format(main_span.get_span_context().span_id, "016x"),
                "tracer_provider": "configured",
                "metric_provider": "configured",
                "span_validator": "enabled",
                "total_spans_captured": len(captured_spans)
            }

            if summary["overall_success"]:
                main_span.set_status(Status(StatusCode.OK))
                print("\n🎉 COMPREHENSIVE VERIFICATION: ✅ ALL CLAIMS VERIFIED")
            else:
                main_span.set_status(Status(StatusCode.ERROR, "Some verifications failed"))
                print("\n💥 COMPREHENSIVE VERIFICATION: ❌ SOME CLAIMS NOT VERIFIED")

            return verification_results

    def save_comprehensive_report(self, results: dict[str, Any]):
        """Save comprehensive verification report."""
        with self.tracer.start_as_current_span("save_comprehensive_report") as span:
            report_path = self.results_dir / "comprehensive-otel-verification-report.json"

            with open(report_path, "w") as f:
                json.dump(results, f, indent=2)

            span.set_attribute("report.path", str(report_path))
            span.set_attribute("report.size", report_path.stat().st_size)

            print(f"\n📄 Comprehensive report saved: {report_path}")
            print(f"   Size: {report_path.stat().st_size} bytes")

            # Also save a summary report
            summary_path = self.results_dir / "verification-summary.txt"
            with open(summary_path, "w") as f:
                f.write("UVMGR EXTERNAL TESTING VERIFICATION SUMMARY\n")
                f.write("=" * 50 + "\n")
                f.write("TRUST ONLY OTEL TRACES - NO HARDCODED VALUES\n")
                f.write("=" * 50 + "\n\n")

                summary = results["summary"]
                f.write(f"Execution ID: {results['execution_id']}\n")
                f.write(f"Total Tests: {summary['total_tests']}\n")
                f.write(f"Successful: {summary['successful_tests']}\n")
                f.write(f"Success Rate: {summary['success_rate']:.1%}\n")
                f.write(f"Overall Success: {'✅ VERIFIED' if summary['overall_success'] else '❌ NOT VERIFIED'}\n")
                f.write(f"Total Duration: {summary['total_duration']:.1f}s\n")
                f.write(f"OTEL Collector: {results['collector_endpoint']}\n\n")

                f.write("TEST RESULTS:\n")
                for test_name, test_result in results["test_results"].items():
                    status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                    duration = test_result.get("duration", 0)
                    f.write(f"  {test_name}: {status} ({duration:.1f}s)\n")

                span_validation = results["span_validation"]["summary"]
                f.write("\nSPAN VALIDATION:\n")
                f.write(f"  Total Validations: {span_validation['total_validations']}\n")
                f.write(f"  Passed: {span_validation['passed']}\n")
                f.write(f"  Failed: {span_validation['failed']}\n")
                f.write(f"  Success Rate: {span_validation['success_rate']:.1%}\n")

            print(f"📄 Summary report saved: {summary_path}")


def main():
    """Main entry point for OTEL-instrumented testing."""
    import argparse

    parser = argparse.ArgumentParser(description="OTEL-Instrumented uvmgr External Testing")
    parser.add_argument("--collector", default="http://localhost:4317",
                       help="OTEL collector endpoint")
    parser.add_argument("--workspace", type=Path,
                       help="Test workspace directory")
    parser.add_argument("--results", type=Path,
                       help="Results output directory")

    args = parser.parse_args()

    try:
        # Initialize runner
        runner = OTELInstrumentedTestRunner(
            collector_endpoint=args.collector,
            workspace_dir=args.workspace,
            results_dir=args.results
        )

        # Run comprehensive verification
        results = runner.run_comprehensive_verification()

        # Save results
        runner.save_comprehensive_report(results)

        # Exit with appropriate code
        success = results["summary"]["overall_success"]
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n🛑 Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
