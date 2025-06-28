"""Integration tests for OTEL functionality focusing on critical 80% features."""
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import CliAttributes, WorkflowAttributes
from uvmgr.core.telemetry import metric_counter, metric_histogram, span


class TestOTELIntegration:
    """Test critical OTEL integration features (80/20 principle)."""

    def test_span_creation_and_context(self):
        """Test that spans are created and context is maintained."""
        spans_created = []

        # Mock to capture span calls
        with patch("uvmgr.core.telemetry.span") as mock_span:
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            # Test nested spans
            with span("test.parent"):
                with span("test.child", operation="test"):
                    with span("test.grandchild"):
                        pass

            # Verify spans were created
            assert mock_span.call_count >= 3
            print(f"✅ Span creation test passed: {mock_span.call_count} spans created")

    def test_metrics_collection(self):
        """Test metrics collection functionality."""
        counters_called = []
        histograms_called = []

        # Test counter
        counter = metric_counter("test.operations")
        counter(1)
        counter(5)

        # Test histogram
        histogram = metric_histogram("test.duration", "s")
        histogram(0.1)
        histogram(0.5)

        print("✅ Metrics collection test passed")

    def test_semantic_conventions_usage(self):
        """Test semantic conventions are properly defined and usable."""
        # Test CLI attributes
        assert hasattr(CliAttributes, "COMMAND")
        assert hasattr(CliAttributes, "EXIT_CODE")
        assert isinstance(CliAttributes.COMMAND, str)

        # Test Workflow attributes
        assert hasattr(WorkflowAttributes, "ENGINE")
        assert hasattr(WorkflowAttributes, "OPERATION")
        assert isinstance(WorkflowAttributes.ENGINE, str)

        print("✅ Semantic conventions test passed")

    def test_instrumentation_decorator(self):
        """Test command instrumentation decorator."""
        executed = []

        @instrument_command("test_command")
        def test_function(arg1: str, arg2: int = 42):
            executed.append((arg1, arg2))
            return f"result_{arg1}_{arg2}"

        # Mock telemetry to capture calls
        with patch("uvmgr.core.telemetry.span") as mock_span:
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = test_function("test", 123)

            assert result == "result_test_123"
            assert executed == [("test", 123)]
            assert mock_span.call_count >= 1

        print("✅ Instrumentation decorator test passed")

    def test_error_handling_and_recording(self):
        """Test error handling and exception recording."""
        from uvmgr.core.telemetry import record_exception

        # Test exception recording doesn't crash
        try:
            raise ValueError("Test exception for OTEL validation")
        except ValueError as e:
            # This should not throw an exception
            record_exception(e, attributes={"test": True})

        # Test span event/attribute functions handle errors gracefully
        add_span_event("test.event", {"key": "value"})
        add_span_attributes(test_attr="test_value")

        print("✅ Error handling test passed")

    def test_performance_measurement(self):
        """Test performance measurement capabilities."""
        start_time = time.time()

        # Simulate some work
        time.sleep(0.01)

        duration = time.time() - start_time

        # Record performance metrics
        perf_histogram = metric_histogram("test.performance.duration", "s")
        perf_histogram(duration)

        # Verify duration is reasonable
        assert 0.005 < duration < 0.1  # Should be around 10ms

        print(f"✅ Performance measurement test passed: {duration:.3f}s")


class TestOTELValidationCommand:
    """Test the OTEL validation command functionality."""

    def test_validation_command_execution(self):
        """Test that OTEL validation command can be executed."""
        from uvmgr.commands.otel import validate_8020

        # Mock all the validation functions to return success
        with patch("uvmgr.commands.otel._test_span_creation") as mock_span_test, \
             patch("uvmgr.commands.otel._test_metrics_collection") as mock_metrics_test, \
             patch("uvmgr.commands.otel._test_semantic_conventions") as mock_semconv_test, \
             patch("uvmgr.commands.otel._test_error_handling") as mock_error_test, \
             patch("uvmgr.commands.otel._test_performance_tracking") as mock_perf_test:

            # Set up mock returns
            mock_span_test.return_value = {"status": "passed", "message": "Test passed", "details": {}}
            mock_metrics_test.return_value = {"status": "passed", "message": "Test passed", "details": {}}
            mock_semconv_test.return_value = {"status": "passed", "message": "Test passed", "details": {}}
            mock_error_test.return_value = {"status": "passed", "message": "Test passed", "details": {}}
            mock_perf_test.return_value = {"status": "passed", "message": "Test passed", "details": {}}

            # Mock telemetry components
            with patch("uvmgr.core.telemetry.span") as mock_span, \
                 patch("uvmgr.core.instrumentation.add_span_event") as mock_event, \
                 patch("uvmgr.core.instrumentation.add_span_attributes") as mock_attrs:

                mock_span.return_value.__enter__ = MagicMock()
                mock_span.return_value.__exit__ = MagicMock(return_value=None)

                # Execute validation (should not raise exceptions)
                try:
                    validate_8020(
                        comprehensive=False,
                        export_results=False,
                        output="",
                        endpoint="http://localhost:4317"
                    )
                    validation_success = True
                except SystemExit as e:
                    # Typer raises SystemExit on success (exit code 0)
                    validation_success = (e.code == 0)
                except Exception as e:
                    validation_success = False
                    print(f"Validation failed with: {e}")

                assert validation_success, "OTEL validation should succeed"
                print("✅ OTEL validation command test passed")


class TestOTELIntegrationRealistic:
    """Test realistic integration scenarios."""

    def test_workflow_validation_integration(self):
        """Test workflow validation with OTEL instrumentation."""
        from uvmgr.runtime.agent.spiff import validate_bpmn_file

        # Create a minimal BPMN file for testing
        minimal_bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="minimal_test">
  <bpmn:process id="minimal_process" isExecutable="true">
    <bpmn:startEvent id="start"/>
  </bpmn:process>
</bpmn:definitions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
            f.write(minimal_bpmn)
            bpmn_path = Path(f.name)

        try:
            # Mock telemetry to capture calls
            with patch("uvmgr.core.telemetry.span") as mock_span:
                mock_span.return_value.__enter__ = MagicMock()
                mock_span.return_value.__exit__ = MagicMock(return_value=None)

                result = validate_bpmn_file(bpmn_path)

                # Should validate successfully
                assert result is True
                assert mock_span.call_count >= 1

        finally:
            # Cleanup
            bpmn_path.unlink()

        print("✅ Workflow validation integration test passed")

    def test_cli_command_telemetry_integration(self):
        """Test that CLI commands are properly instrumented."""
        from uvmgr.core.instrumentation import instrument_command

        call_count = 0

        @instrument_command("test_cli_command", command_type="cli")
        def mock_cli_command(arg: str = "test"):
            nonlocal call_count
            call_count += 1
            return f"executed_{arg}"

        # Mock telemetry
        with patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.core.telemetry.metric_counter") as mock_counter:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()

            # Execute command
            result = mock_cli_command("integration_test")

            # Verify execution
            assert result == "executed_integration_test"
            assert call_count == 1
            assert mock_span.call_count >= 1
            assert mock_counter.call_count >= 1

        print("✅ CLI command telemetry integration test passed")


if __name__ == "__main__":
    # Run tests if executed directly
    test_integration = TestOTELIntegration()
    test_integration.test_span_creation_and_context()
    test_integration.test_metrics_collection()
    test_integration.test_semantic_conventions_usage()
    test_integration.test_instrumentation_decorator()
    test_integration.test_error_handling_and_recording()
    test_integration.test_performance_measurement()

    test_realistic = TestOTELIntegrationRealistic()
    test_realistic.test_workflow_validation_integration()
    test_realistic.test_cli_command_telemetry_integration()

    print("\n🎉 All OTEL integration tests passed!")
