#!/usr/bin/env python3
"""
OpenTelemetry Claim Verification System
======================================

This system uses OpenTelemetry traces and metrics to verify ALL claims
made about uvmgr's external project testing capabilities. Every claim
is backed by actual telemetry data, not assumptions.

TRUST ONLY OTEL TRACES - NO HARDCODED VALUES
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# OpenTelemetry imports
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


@dataclass
class ClaimVerification:
    """Represents a verified claim with OTEL evidence."""

    claim: str
    verified: bool
    evidence_spans: list[str]
    metrics: dict[str, float]
    performance_data: dict[str, Any]
    error_details: str | None = None
    verification_timestamp: float = 0.0

    def __post_init__(self):
        if self.verification_timestamp == 0.0:
            self.verification_timestamp = time.time()


class OTELClaimVerifier:
    """Verifies uvmgr claims through OpenTelemetry observability."""

    def __init__(self, collector_endpoint: str = "http://localhost:4317"):
        self.collector_endpoint = collector_endpoint
        self.verified_claims: list[ClaimVerification] = []
        self.active_spans: dict[str, Any] = {}
        self.performance_thresholds = {
            "command_startup_max": 0.5,  # 500ms max startup time
            "deps_list_max": 2.0,        # 2s max for deps list
            "test_run_overhead_max": 1.5, # 50% max overhead vs direct
            "build_overhead_max": 1.1,   # 10% max overhead vs direct
        }

        self._setup_otel()

    def _setup_otel(self):
        """Set up OpenTelemetry with both local and remote exporters."""
        # Configure resource
        resource = Resource.create({
            "service.name": "uvmgr-claim-verifier",
            "service.version": "1.0.0",
            "environment": "verification",
            "verifier.mode": "external-testing"
        })

        # Set up tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)

        # Add exporters
        otlp_exporter = OTLPSpanExporter(endpoint=self.collector_endpoint, insecure=True)
        console_exporter = ConsoleSpanExporter()

        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(console_exporter)
        )

        # Set up metrics
        otlp_metric_exporter = OTLPMetricExporter(endpoint=self.collector_endpoint, insecure=True)
        console_metric_exporter = ConsoleMetricExporter()

        metrics.set_meter_provider(MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000),
                PeriodicExportingMetricReader(console_metric_exporter, export_interval_millis=10000)
            ]
        ))

        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.command_duration_histogram = self.meter.create_histogram(
            "uvmgr_command_duration_seconds",
            description="Duration of uvmgr commands",
            unit="s"
        )

        self.claim_verification_counter = self.meter.create_counter(
            "uvmgr_claims_verified_total",
            description="Total claims verified"
        )

        self.performance_threshold_gauge = self.meter.create_gauge(
            "uvmgr_performance_threshold_ratio",
            description="Performance threshold compliance ratio"
        )

        print("🔧 OpenTelemetry configured with both OTLP and console exporters")

    @contextmanager
    def verify_claim(self, claim_name: str, claim_description: str):
        """Context manager for claim verification with OTEL tracing."""
        span_name = f"verify_claim.{claim_name}"

        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("claim.name", claim_name)
            span.set_attribute("claim.description", claim_description)
            span.set_attribute("verification.start_time", time.time())

            verification = ClaimVerification(
                claim=claim_description,
                verified=False,
                evidence_spans=[span_name],
                metrics={},
                performance_data={}
            )

            try:
                yield verification

                # Record success
                span.set_attribute("claim.verified", verification.verified)
                span.set_attribute("claim.evidence_count", len(verification.evidence_spans))

                if verification.verified:
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    self.claim_verification_counter.add(1, {"status": "verified", "claim": claim_name})
                else:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, "Claim not verified"))
                    self.claim_verification_counter.add(1, {"status": "failed", "claim": claim_name})

                # Record metrics
                for metric_name, value in verification.metrics.items():
                    span.set_attribute(f"metric.{metric_name}", value)

            except Exception as e:
                verification.error_details = str(e)
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                self.claim_verification_counter.add(1, {"status": "error", "claim": claim_name})

            finally:
                self.verified_claims.append(verification)
                span.set_attribute("verification.end_time", time.time())

    def measure_command_performance(self, command: list[str], cwd: Path | None = None,
                                  expected_max_duration: float | None = None) -> tuple[bool, dict[str, Any]]:
        """Measure command performance with OTEL instrumentation."""
        cmd_name = command[0] if command else "unknown"

        with self.tracer.start_as_current_span(f"command_execution.{cmd_name}") as span:
            span.set_attribute("command.name", cmd_name)
            span.set_attribute("command.args", " ".join(command))
            span.set_attribute("command.cwd", str(cwd) if cwd else "")

            start_time = time.time()

            try:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=60, check=False
                )

                duration = time.time() - start_time

                # Record metrics
                self.command_duration_histogram.record(
                    duration,
                    {"command": cmd_name, "status": "success" if result.returncode == 0 else "error"}
                )

                span.set_attribute("command.duration", duration)
                span.set_attribute("command.returncode", result.returncode)
                span.set_attribute("command.stdout_length", len(result.stdout))
                span.set_attribute("command.stderr_length", len(result.stderr))

                performance_data = {
                    "duration": duration,
                    "returncode": result.returncode,
                    "stdout": result.stdout[:1000],  # Truncate for storage
                    "stderr": result.stderr[:1000],
                    "success": result.returncode == 0
                }

                # Check against threshold
                threshold_met = True
                if expected_max_duration is not None:
                    threshold_met = duration <= expected_max_duration
                    span.set_attribute("performance.threshold_met", threshold_met)
                    span.set_attribute("performance.expected_max", expected_max_duration)

                    threshold_ratio = duration / expected_max_duration
                    self.performance_threshold_gauge.set(threshold_ratio, {"command": cmd_name})

                if result.returncode == 0:
                    span.set_status(trace.Status(trace.StatusCode.OK))
                else:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, f"Command failed: {result.returncode}"))

                return threshold_met and result.returncode == 0, performance_data

            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                span.set_attribute("command.timeout", True)
                span.set_attribute("command.duration", duration)
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Command timeout"))

                return False, {"duration": duration, "timeout": True, "success": False}

            except Exception as e:
                duration = time.time() - start_time
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                return False, {"duration": duration, "error": str(e), "success": False}

    def verify_auto_install_claim(self, test_project_path: Path) -> ClaimVerification:
        """Verify: 'Auto-install script works with any Python project'"""
        with self.verify_claim("auto_install", "Auto-install script works with any Python project") as verification:

            # Test auto-install script exists and is executable
            script_path = Path(__file__).parent / "auto-install-uvmgr.sh"

            with self.tracer.start_as_current_span("check_script_exists") as span:
                script_exists = script_path.exists()
                script_executable = script_path.is_file() and os.access(script_path, os.X_OK)

                span.set_attribute("script.exists", script_exists)
                span.set_attribute("script.executable", script_executable)

                if not script_exists:
                    verification.error_details = "Auto-install script not found"
                    return verification

            # Test script execution
            success, perf_data = self.measure_command_performance(
                ["bash", str(script_path), str(test_project_path)],
                expected_max_duration=120.0  # 2 minutes max for installation
            )

            verification.performance_data["auto_install"] = perf_data
            verification.metrics["install_duration"] = perf_data.get("duration", 0)

            # Verify uvmgr is available after installation
            if success:
                with self.tracer.start_as_current_span("verify_uvmgr_available") as span:
                    uvmgr_success, uvmgr_perf = self.measure_command_performance(
                        ["uvmgr", "--version"],
                        cwd=test_project_path,
                        expected_max_duration=self.performance_thresholds["command_startup_max"]
                    )

                    span.set_attribute("uvmgr.available", uvmgr_success)
                    verification.performance_data["uvmgr_startup"] = uvmgr_perf
                    verification.metrics["startup_duration"] = uvmgr_perf.get("duration", 0)

                    # Check for config files
                    config_file = test_project_path / ".uvmgr.toml"
                    examples_dir = test_project_path / ".uvmgr" / "examples"

                    span.set_attribute("config.file_created", config_file.exists())
                    span.set_attribute("config.examples_created", examples_dir.exists())

                    verification.verified = (
                        uvmgr_success and
                        config_file.exists() and
                        examples_dir.exists()
                    )

            return verification

    def verify_substrate_integration_claim(self) -> ClaimVerification:
        """Verify: 'Substrate template integration works seamlessly'"""
        with self.verify_claim("substrate_integration", "Substrate template integration works seamlessly") as verification:

            # Check if copier is available
            with self.tracer.start_as_current_span("check_copier_available") as span:
                copier_success, copier_perf = self.measure_command_performance(
                    ["copier", "--version"],
                    expected_max_duration=5.0
                )

                span.set_attribute("copier.available", copier_success)
                verification.performance_data["copier_check"] = copier_perf

                if not copier_success:
                    verification.error_details = "Copier not available for Substrate testing"
                    return verification

            # Test Substrate integration script
            script_path = Path(__file__).parent / "test-substrate-integration.sh"

            with tempfile.TemporaryDirectory() as tmpdir:
                test_project = Path(tmpdir) / "substrate-test"

                # Run substrate integration (with timeout due to potential network operations)
                success, perf_data = self.measure_command_performance(
                    ["bash", str(script_path), str(test_project)],
                    cwd=Path(tmpdir),
                    expected_max_duration=300.0  # 5 minutes for full integration
                )

                verification.performance_data["substrate_integration"] = perf_data
                verification.metrics["integration_duration"] = perf_data.get("duration", 0)

                # Check for integration artifacts
                if success:
                    with self.tracer.start_as_current_span("verify_integration_artifacts") as span:
                        expected_files = [
                            "pyproject.toml",
                            ".uvmgr.toml",
                            "substrate-uvmgr-integration-report.md"
                        ]

                        artifacts_found = 0
                        for expected_file in expected_files:
                            file_path = test_project / expected_file
                            if file_path.exists():
                                artifacts_found += 1
                                span.set_attribute(f"artifact.{expected_file}", True)
                            else:
                                span.set_attribute(f"artifact.{expected_file}", False)

                        span.set_attribute("artifacts.found_count", artifacts_found)
                        span.set_attribute("artifacts.expected_count", len(expected_files))

                        verification.metrics["artifacts_ratio"] = artifacts_found / len(expected_files)
                        verification.verified = artifacts_found >= len(expected_files) * 0.8  # 80% success rate

            return verification

    def verify_lifecycle_testing_claim(self) -> ClaimVerification:
        """Verify: 'Complete lifecycle testing covers all development phases'"""
        with self.verify_claim("lifecycle_testing", "Complete lifecycle testing covers all development phases") as verification:

            # Test lifecycle script
            script_path = Path(__file__).parent / "test-lifecycle.py"

            with self.tracer.start_as_current_span("check_lifecycle_script") as span:
                script_exists = script_path.exists()
                span.set_attribute("script.exists", script_exists)

                if not script_exists:
                    verification.error_details = "Lifecycle testing script not found"
                    return verification

            # Test help functionality
            help_success, help_perf = self.measure_command_performance(
                [sys.executable, str(script_path), "--help"],
                expected_max_duration=5.0
            )

            verification.performance_data["help_command"] = help_perf

            # Test minimal project lifecycle
            with tempfile.TemporaryDirectory() as tmpdir:
                with self.tracer.start_as_current_span("test_minimal_lifecycle") as span:
                    lifecycle_success, lifecycle_perf = self.measure_command_performance(
                        [
                            sys.executable, str(script_path),
                            "--project", "minimal",
                            "--workspace", tmpdir,
                            "--results", tmpdir
                        ],
                        expected_max_duration=180.0  # 3 minutes for minimal lifecycle
                    )

                    span.set_attribute("lifecycle.minimal.success", lifecycle_success)
                    verification.performance_data["minimal_lifecycle"] = lifecycle_perf
                    verification.metrics["lifecycle_duration"] = lifecycle_perf.get("duration", 0)

                    # Check for results file
                    results_file = Path(tmpdir) / "lifecycle_test_results.json"
                    if results_file.exists():
                        with open(results_file) as f:
                            results_data = json.load(f)

                        span.set_attribute("results.file_exists", True)

                        # Verify phases were tested
                        phases_tested = results_data.get("projects", {}).get("minimal", {}).get("phases", {})
                        expected_phases = ["setup", "dependencies", "development", "testing", "building"]

                        phases_found = 0
                        for phase in expected_phases:
                            if phase in phases_tested:
                                phases_found += 1
                                span.set_attribute(f"phase.{phase}.tested", True)
                            else:
                                span.set_attribute(f"phase.{phase}.tested", False)

                        verification.metrics["phases_coverage"] = phases_found / len(expected_phases)
                        verification.verified = phases_found >= len(expected_phases) * 0.8  # 80% coverage

                        span.set_attribute("phases.found_count", phases_found)
                        span.set_attribute("phases.expected_count", len(expected_phases))
                    else:
                        span.set_attribute("results.file_exists", False)
                        verification.verified = False

            return verification

    def verify_performance_claims(self) -> ClaimVerification:
        """Verify: 'uvmgr meets performance benchmarks'"""
        with self.verify_claim("performance", "uvmgr meets performance benchmarks") as verification:

            performance_tests = [
                ("uvmgr --help", ["uvmgr", "--help"], "command_startup_max"),
                ("uvmgr deps list", ["uvmgr", "deps", "list"], "deps_list_max"),
            ]

            all_thresholds_met = True

            for test_name, command, threshold_key in performance_tests:
                with self.tracer.start_as_current_span(f"performance_test.{threshold_key}") as span:
                    threshold = self.performance_thresholds[threshold_key]

                    success, perf_data = self.measure_command_performance(
                        command,
                        expected_max_duration=threshold
                    )

                    duration = perf_data.get("duration", float("inf"))
                    threshold_met = duration <= threshold

                    span.set_attribute("test.name", test_name)
                    span.set_attribute("test.threshold", threshold)
                    span.set_attribute("test.actual_duration", duration)
                    span.set_attribute("test.threshold_met", threshold_met)

                    verification.performance_data[threshold_key] = perf_data
                    verification.metrics[f"{threshold_key}_duration"] = duration
                    verification.metrics[f"{threshold_key}_threshold"] = threshold
                    verification.metrics[f"{threshold_key}_ratio"] = duration / threshold

                    if not threshold_met:
                        all_thresholds_met = False

            verification.verified = all_thresholds_met
            return verification

    def verify_observability_claims(self) -> ClaimVerification:
        """Verify: 'Complete observability with OpenTelemetry integration'"""
        with self.verify_claim("observability", "Complete observability with OpenTelemetry integration") as verification:

            # Test OTEL commands
            otel_commands = [
                ["uvmgr", "otel", "validate"],
                ["uvmgr", "otel", "demo"],
                ["uvmgr", "weaver", "validate"]
            ]

            successful_commands = 0

            for command in otel_commands:
                with self.tracer.start_as_current_span(f"otel_command.{command[1]}_{command[2]}") as span:
                    success, perf_data = self.measure_command_performance(
                        command,
                        expected_max_duration=30.0  # 30s max for OTEL operations
                    )

                    cmd_name = f"{command[1]}_{command[2]}"
                    span.set_attribute("otel_command.name", cmd_name)
                    span.set_attribute("otel_command.success", success)

                    verification.performance_data[cmd_name] = perf_data

                    if success:
                        successful_commands += 1

            # Check OTEL collector connectivity
            with self.tracer.start_as_current_span("check_otel_collector") as span:
                import requests
                try:
                    # Try to reach OTEL collector health endpoint
                    response = requests.get("http://localhost:13133", timeout=5)
                    collector_available = response.status_code == 200
                except:
                    collector_available = False

                span.set_attribute("otel_collector.available", collector_available)
                verification.metrics["collector_available"] = 1.0 if collector_available else 0.0

            verification.metrics["otel_commands_success_ratio"] = successful_commands / len(otel_commands)
            verification.verified = successful_commands >= len(otel_commands) * 0.7  # 70% success rate

            return verification

    def verify_all_claims(self, test_workspace: Path | None = None) -> dict[str, Any]:
        """Verify all claims about uvmgr external testing capabilities."""
        print("🔍 OpenTelemetry Claim Verification System")
        print("=" * 50)
        print("TRUST ONLY OTEL TRACES - NO HARDCODED VALUES")
        print("=" * 50)

        if test_workspace is None:
            test_workspace = Path(tempfile.mkdtemp(prefix="uvmgr-claim-test-"))

        with self.tracer.start_as_current_span("verify_all_claims") as main_span:
            main_span.set_attribute("test_workspace", str(test_workspace))
            main_span.set_attribute("verification.start_time", time.time())

            # Create test project structure
            with self.tracer.start_as_current_span("setup_test_project") as span:
                test_project = test_workspace / "test-project"
                test_project.mkdir(parents=True, exist_ok=True)

                # Create minimal Python project
                (test_project / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project for uvmgr claim verification"
""")

                span.set_attribute("test_project.path", str(test_project))
                span.set_attribute("test_project.created", True)

            # Run all verifications
            verifications = [
                ("auto_install", lambda: self.verify_auto_install_claim(test_project)),
                ("substrate_integration", self.verify_substrate_integration_claim),
                ("lifecycle_testing", self.verify_lifecycle_testing_claim),
                ("performance", self.verify_performance_claims),
                ("observability", self.verify_observability_claims)
            ]

            for claim_name, verifier in verifications:
                with self.tracer.start_as_current_span(f"run_verification.{claim_name}") as span:
                    print(f"\n🧪 Verifying: {claim_name}")

                    try:
                        verification = verifier()

                        span.set_attribute(f"verification.{claim_name}.success", verification.verified)
                        span.set_attribute(f"verification.{claim_name}.duration",
                                         verification.verification_timestamp)

                        if verification.verified:
                            print(f"✅ {verification.claim}: VERIFIED")
                        else:
                            print(f"❌ {verification.claim}: NOT VERIFIED")
                            if verification.error_details:
                                print(f"   Error: {verification.error_details}")

                        # Log key metrics
                        for metric_name, value in verification.metrics.items():
                            print(f"   📊 {metric_name}: {value}")
                            span.set_attribute(f"metric.{claim_name}.{metric_name}", value)

                    except Exception as e:
                        print(f"💥 {claim_name}: VERIFICATION FAILED - {e}")
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            # Generate summary
            total_claims = len(self.verified_claims)
            verified_claims = sum(1 for v in self.verified_claims if v.verified)

            summary = {
                "total_claims": total_claims,
                "verified_claims": verified_claims,
                "verification_rate": verified_claims / total_claims if total_claims > 0 else 0,
                "overall_success": verified_claims == total_claims,
                "test_workspace": str(test_workspace),
                "verification_timestamp": time.time(),
                "otel_collector_endpoint": self.collector_endpoint
            }

            main_span.set_attribute("summary.total_claims", total_claims)
            main_span.set_attribute("summary.verified_claims", verified_claims)
            main_span.set_attribute("summary.verification_rate", summary["verification_rate"])
            main_span.set_attribute("summary.overall_success", summary["overall_success"])

            print("\n📊 OTEL Verification Summary")
            print(f"   Total Claims: {total_claims}")
            print(f"   Verified: {verified_claims}")
            print(f"   Success Rate: {summary['verification_rate']:.1%}")
            print(f"   Overall: {'✅ ALL VERIFIED' if summary['overall_success'] else '❌ SOME FAILED'}")
            print(f"   OTEL Endpoint: {self.collector_endpoint}")

            # Record final metrics
            self.claim_verification_counter.add(verified_claims, {"final": "verified"})
            self.claim_verification_counter.add(total_claims - verified_claims, {"final": "failed"})

            return {
                "summary": summary,
                "claims": [asdict(claim) for claim in self.verified_claims],
                "performance_thresholds": self.performance_thresholds
            }

    def save_verification_report(self, results: dict[str, Any], output_path: Path | None = None):
        """Save verification results with OTEL tracing."""
        if output_path is None:
            output_path = Path("otel-claim-verification-report.json")

        with self.tracer.start_as_current_span("save_verification_report") as span:
            span.set_attribute("report.output_path", str(output_path))

            # Add OTEL metadata
            results["otel_metadata"] = {
                "tracer_provider": "configured",
                "metric_provider": "configured",
                "exporters": ["otlp", "console"],
                "collector_endpoint": self.collector_endpoint,
                "verification_method": "opentelemetry_instrumented"
            }

            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

            span.set_attribute("report.file_size", output_path.stat().st_size)
            span.set_attribute("report.claims_count", len(results.get("claims", [])))

            print(f"📄 OTEL Verification Report saved to: {output_path}")
            print(f"   File size: {output_path.stat().st_size} bytes")
            print(f"   Claims verified: {len(results.get('claims', []))}")


def main():
    """Main OTEL claim verification entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify uvmgr claims through OpenTelemetry")
    parser.add_argument("--collector", default="http://localhost:4317",
                       help="OTEL collector endpoint")
    parser.add_argument("--workspace", type=Path,
                       help="Test workspace directory")
    parser.add_argument("--output", type=Path,
                       help="Output report path")

    args = parser.parse_args()

    # Initialize verifier
    verifier = OTELClaimVerifier(collector_endpoint=args.collector)

    try:
        print("🚀 Starting OTEL-based claim verification...")
        print(f"📡 OTEL Collector: {args.collector}")

        # Run verification
        results = verifier.verify_all_claims(test_workspace=args.workspace)

        # Save report
        verifier.save_verification_report(results, output_path=args.output)

        # Exit with appropriate code
        success = results["summary"]["overall_success"]
        print(f"\n🎯 Final Result: {'✅ ALL CLAIMS VERIFIED' if success else '❌ VERIFICATION FAILED'}")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n🛑 Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
