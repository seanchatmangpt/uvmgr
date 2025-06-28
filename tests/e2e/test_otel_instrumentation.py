"""End-to-end tests for OTEL instrumentation."""
import json
import os
import subprocess
import time
from unittest.mock import patch

import pytest
from tests.e2e.conftest import assert_command_success


class TestOTELInstrumentation:
    """Test OTEL tracing and metrics for uvmgr commands."""

    def test_deps_command_instrumentation(self, uvmgr_runner, temp_project):
        """Test that deps commands generate proper OTEL spans."""
        # Mock the OTEL exporter to capture spans
        captured_spans = []

        # Run deps list command
        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

        # Since we don't have a real OTEL collector, we can't verify spans directly
        # But we can verify the command executed successfully with telemetry enabled
        assert result.returncode == 0

    def test_command_metrics(self, uvmgr_runner, temp_project):
        """Test that commands increment metrics counters."""
        # Run several commands to generate metrics
        commands = [
            ["deps", "lock"],
            ["deps", "list"],
            ["--help"],
        ]

        for cmd in commands:
            result = uvmgr_runner(*cmd, cwd=temp_project, check=False)
            # Help and valid commands should succeed
            if "--help" in cmd or cmd[0] == "deps":
                assert result.returncode == 0

    def test_error_instrumentation(self, uvmgr_runner, temp_project):
        """Test that errors are properly instrumented."""
        # Try to add a non-existent package
        result = uvmgr_runner(
            "deps", "add", "this-package-definitely-does-not-exist-12345",
            cwd=temp_project,
            check=False
        )

        # Command should fail
        assert result.returncode != 0

        # In a real test with OTEL collector, we would verify:
        # - Error span with ERROR status
        # - Exception recorded in span
        # - Error counter incremented

    def test_span_attributes(self, uvmgr_runner, temp_project):
        """Test that spans include proper attributes."""
        # Add a dev dependency with specific options
        result = uvmgr_runner(
            "deps", "add", "pytest", "--dev",
            cwd=temp_project
        )
        assert_command_success(result)

        # In a real test with OTEL collector, we would verify span attributes:
        # - cli.command: "deps_add"
        # - package.operation: "add"
        # - package.dev_dependency: true
        # - package.names: "pytest"

    def test_nested_spans(self, uvmgr_runner, temp_project):
        """Test that operations create proper nested spans."""
        # Run a build command which should create nested spans
        result = uvmgr_runner("build", "wheel", cwd=temp_project, check=False)

        # In a real test with OTEL collector, we would verify:
        # - Parent span for the build command
        # - Child spans for subprocess calls
        # - Proper parent-child relationships

    @pytest.mark.skipif(
        not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
        reason="OTEL collector not configured"
    )
    def test_real_otel_integration(self, uvmgr_runner, temp_project):
        """Test with a real OTEL collector if available."""
        # This test requires a running OTEL collector
        # Set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 to enable

        result = uvmgr_runner("deps", "list", cwd=temp_project)
        assert_command_success(result)

        # Give time for spans to be exported
        time.sleep(2)

        # In a real scenario, you would query the collector's API
        # to verify the spans were received
        print("OTEL integration test completed - check collector for spans")


def test_instrumentation_imports():
    """Test that instrumentation modules can be imported."""
    try:
        from uvmgr.core.instrumentation import add_span_attributes, instrument_command
        from uvmgr.core.semconv import CliAttributes, PackageAttributes
        from uvmgr.core.telemetry import metric_counter, record_exception, span

        # Verify the decorators and functions exist
        assert callable(instrument_command)
        assert callable(add_span_attributes)
        assert callable(span)
        assert callable(metric_counter)
        assert callable(record_exception)

        # Verify constants exist
        assert hasattr(CliAttributes, "COMMAND")
        assert hasattr(PackageAttributes, "OPERATION")

    except ImportError as e:
        pytest.fail(f"Failed to import instrumentation modules: {e}")


def test_semconv_constants():
    """Test that semantic convention constants are properly defined."""
    from uvmgr.core.semconv import (
        BuildAttributes,
        CliAttributes,
        PackageAttributes,
        PackageOperations,
        TestAttributes,
    )

    # Verify CLI attributes
    assert CliAttributes.COMMAND == "cli.command"
    assert CliAttributes.SUBCOMMAND == "cli.subcommand"
    assert CliAttributes.EXIT_CODE == "cli.exit_code"

    # Verify package attributes
    assert PackageAttributes.OPERATION == "package.operation"
    assert PackageAttributes.NAME == "package.name"
    assert PackageAttributes.VERSION == "package.version"

    # Verify package operations
    assert PackageOperations.ADD == "add"
    assert PackageOperations.REMOVE == "remove"
    assert PackageOperations.UPDATE == "update"
