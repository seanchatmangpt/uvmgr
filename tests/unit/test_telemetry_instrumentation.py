"""
Unit tests for telemetry instrumentation across all uvmgr modules.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import telemetry modules
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, metric_gauge
from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event
from uvmgr.core.semconv import (
    CliAttributes, PackageAttributes, SecurityAttributes, WorktreeAttributes,
    GuideAttributes, InfoDesignAttributes, PackageOperations
)
from uvmgr.core.metrics import (
    BaseMetrics, PackageMetrics, BuildMetrics, TestMetrics, AiMetrics,
    ProcessMetrics, OperationResult
)


class TestTelemetryInstrumentation:
    """Test telemetry instrumentation functionality."""

    def test_span_context_manager(self):
        """Test span context manager functionality."""
        with span("test.operation") as current_span:
            # Should create a span (even if no-op)
            assert current_span is not None
            
            # Should be able to add attributes
            if hasattr(current_span, 'set_attribute'):
                current_span.set_attribute("test.key", "test.value")
                current_span.set_attribute("test.number", 42)
                current_span.set_attribute("test.boolean", True)

    def test_span_with_initial_attributes(self):
        """Test span creation with initial attributes."""
        initial_attrs = {
            "operation.type": "test",
            "operation.component": "uvmgr.test",
            "operation.version": "1.0.0"
        }
        
        with span("test.operation", **initial_attrs) as current_span:
            assert current_span is not None

    def test_nested_spans(self):
        """Test nested span creation and hierarchy."""
        with span("parent.operation") as parent_span:
            assert parent_span is not None
            
            with span("child.operation") as child_span:
                assert child_span is not None
                
                with span("grandchild.operation") as grandchild_span:
                    assert grandchild_span is not None

    def test_span_error_handling(self):
        """Test span behavior with exceptions."""
        with pytest.raises(ValueError):
            with span("test.operation") as current_span:
                assert current_span is not None
                raise ValueError("Test exception")

    def test_metrics_creation(self):
        """Test metric creation and basic functionality."""
        # Counter metrics
        counter = metric_counter("test.operations.total")
        assert callable(counter)
        
        # Histogram metrics
        histogram = metric_histogram("test.operation.duration", unit="s")
        assert callable(histogram)
        
        # Gauge metrics
        gauge = metric_gauge("test.active.connections")
        assert callable(gauge)

    def test_metrics_recording(self):
        """Test metric recording with various values."""
        counter = metric_counter("test.counter")
        histogram = metric_histogram("test.histogram")
        gauge = metric_gauge("test.gauge")
        
        # Should handle various value types
        counter(1)
        counter(10)
        counter(0)
        
        histogram(0.001)
        histogram(1.5)
        histogram(60.0)
        
        gauge(100)
        gauge(-50)
        gauge(0)

    def test_instrument_command_decorator(self):
        """Test command instrumentation decorator."""
        call_log = []
        
        @instrument_command("test.command")
        def test_command(arg1: str, arg2: int = 42) -> str:
            call_log.append((arg1, arg2))
            return f"result_{arg1}_{arg2}"
        
        result = test_command("hello", 123)
        
        assert result == "result_hello_123"
        assert call_log == [("hello", 123)]

    def test_instrument_command_with_exception(self):
        """Test command instrumentation with exceptions."""
        @instrument_command("test.failing_command")
        def failing_command():
            raise RuntimeError("Command failed")
        
        with pytest.raises(RuntimeError, match="Command failed"):
            failing_command()

    def test_add_span_attributes_function(self):
        """Test adding attributes to current span."""
        # Should not raise exceptions even without active span
        add_span_attributes(
            test_string="value",
            test_number=42,
            test_float=3.14,
            test_boolean=True
        )
        
        # Test with semantic convention attributes
        add_span_attributes(**{
            CliAttributes.CLI_COMMAND: "test",
            PackageAttributes.PACKAGE_NAME: "test-package",
            SecurityAttributes.OPERATION: "scan"
        })

    def test_add_span_event_function(self):
        """Test adding events to current span."""
        # Should not raise exceptions even without active span
        add_span_event("test.event", {
            "event.data": "test_value",
            "event.timestamp": time.time()
        })
        
        # Test event without data
        add_span_event("simple.event")

    def test_telemetry_no_op_safety(self):
        """Test that telemetry is safe when disabled."""
        # All telemetry operations should work without raising exceptions
        
        with span("safe.operation"):
            counter = metric_counter("safe.counter")
            counter(1)
            
            histogram = metric_histogram("safe.histogram") 
            histogram(0.5)
            
            gauge = metric_gauge("safe.gauge")
            gauge(10)
            
            add_span_attributes(test="value")
            add_span_event("safe.event", {"data": "test"})


class TestSemanticConventionUsage:
    """Test usage of semantic conventions in telemetry."""

    def test_cli_semantic_conventions(self):
        """Test CLI semantic convention usage."""
        with span("cli.command") as current_span:
            if hasattr(current_span, 'set_attribute'):
                current_span.set_attribute(CliAttributes.CLI_COMMAND, "deps")
                current_span.set_attribute(CliAttributes.CLI_SUBCOMMAND, "add")
                current_span.set_attribute(CliAttributes.CLI_EXIT_CODE, 0)
                current_span.set_attribute(CliAttributes.OPTIONS, '{"dev": false}')

    def test_package_semantic_conventions(self):
        """Test package semantic convention usage."""
        with span("package.operation") as current_span:
            if hasattr(current_span, 'set_attribute'):
                current_span.set_attribute(PackageAttributes.PACKAGE_NAME, "requests")
                current_span.set_attribute(PackageAttributes.PACKAGE_VERSION, "2.28.0")
                current_span.set_attribute(PackageAttributes.OPERATION, PackageOperations.ADD)
                current_span.set_attribute(PackageAttributes.DEV_DEPENDENCY, False)

    def test_security_semantic_conventions(self):
        """Test security semantic convention usage."""
        with span("security.scan") as current_span:
            if hasattr(current_span, 'set_attribute'):
                current_span.set_attribute(SecurityAttributes.OPERATION, "scan")
                current_span.set_attribute(SecurityAttributes.PROJECT_PATH, "/path/to/project")
                current_span.set_attribute(SecurityAttributes.SEVERITY_THRESHOLD, "medium")
                current_span.set_attribute(SecurityAttributes.VULNERABILITY_COUNT, 5)

    def test_semantic_convention_validation(self):
        """Test that semantic conventions are properly validated."""
        from uvmgr.core.semconv import validate_attribute
        
        # Valid attributes
        assert validate_attribute(CliAttributes.CLI_COMMAND, "test_command")
        assert validate_attribute(PackageAttributes.PACKAGE_NAME, "test_package")
        assert validate_attribute(SecurityAttributes.OPERATION, "scan")
        
        # Invalid attributes (should return False for unknown attributes)
        assert not validate_attribute("invalid.attribute", "value")
        assert not validate_attribute("unknown.namespace.attribute", "value")


class TestMetricsClasses:
    """Test specialized metrics classes."""

    def test_base_metrics(self):
        """Test BaseMetrics functionality."""
        metrics = BaseMetrics("test")
        
        # Should have basic metrics
        assert hasattr(metrics, 'operation_counter')
        assert hasattr(metrics, 'error_counter')
        assert hasattr(metrics, 'duration_histogram')
        assert hasattr(metrics, 'active_gauge')
        
        # Should be callable
        assert callable(metrics.operation_counter)
        assert callable(metrics.error_counter)
        assert callable(metrics.duration_histogram)
        assert callable(metrics.active_gauge)

    def test_base_metrics_timer(self):
        """Test BaseMetrics timer context manager."""
        metrics = BaseMetrics("test")
        
        with metrics.timer() as get_duration:
            time.sleep(0.01)  # Small delay
            duration = get_duration()
            assert duration > 0

    def test_base_metrics_record_operation(self):
        """Test BaseMetrics record_operation method."""
        metrics = BaseMetrics("test")
        
        # Successful operation
        metrics.record_operation("test_op", 0.5, True, {"key": "value"})
        
        # Failed operation
        metrics.record_operation("test_op", 1.0, False, {"error": "test_error"})

    def test_package_metrics(self):
        """Test PackageMetrics specialized functionality."""
        metrics = PackageMetrics()
        
        # Should have package-specific metrics
        assert hasattr(metrics, 'packages_added')
        assert hasattr(metrics, 'packages_removed')
        assert hasattr(metrics, 'packages_updated')
        assert hasattr(metrics, 'dependency_resolution_time')
        
        # Test record methods
        result = OperationResult(success=True, duration=0.5)
        metrics.record_add("test_package", "1.0.0", False, result)
        metrics.record_remove("test_package", result)

    def test_package_metrics_record_operation(self):
        """Test PackageMetrics record_package_operation method."""
        metrics = PackageMetrics()
        
        # Test different operations
        metrics.record_package_operation("add", "requests", "2.28.0", False, 0.5, True)
        metrics.record_package_operation("remove", "requests", None, False, 0.3, True)
        metrics.record_package_operation("update", "requests", "2.29.0", False, 1.0, True)

    def test_build_metrics(self):
        """Test BuildMetrics functionality."""
        metrics = BuildMetrics()
        
        # Should have build-specific metrics
        assert hasattr(metrics, 'artifact_size')
        assert hasattr(metrics, 'builds_by_type')
        
        # Test build operation recording
        metrics.record_build_operation("wheel", 2.5, True, 1024000, "/path/to/dist")

    def test_operation_result(self):
        """Test OperationResult dataclass."""
        # Successful result
        result = OperationResult(success=True, duration=1.5)
        assert result.success is True
        assert result.duration == 1.5
        assert result.error is None
        assert result.metadata is None
        
        # Failed result with error
        error = RuntimeError("Test error")
        result = OperationResult(
            success=False, 
            duration=0.8, 
            error=error,
            metadata={"attempt": 1}
        )
        assert result.success is False
        assert result.error == error
        assert result.metadata["attempt"] == 1


class TestInstrumentationIntegration:
    """Test integration of instrumentation across uvmgr modules."""

    def test_command_instrumentation_pattern(self):
        """Test that command instrumentation follows consistent pattern."""
        # This tests the pattern used across uvmgr command modules
        
        @instrument_command("deps.add", track_args=True)
        def mock_deps_add(pkgs: list[str], dev: bool = False) -> dict:
            # Simulate the pattern used in actual commands
            with span("deps.add.operation") as current_span:
                if current_span and hasattr(current_span, 'set_attribute'):
                    current_span.set_attribute(PackageAttributes.OPERATION, PackageOperations.ADD)
                    current_span.set_attribute(PackageAttributes.PACKAGE_NAME, " ".join(pkgs))
                    current_span.set_attribute(PackageAttributes.DEV_DEPENDENCY, dev)
                
                add_span_event("deps.add.started", {"packages": pkgs, "dev": dev})
                
                # Simulate operation
                result = {"added": pkgs, "dev": dev}
                
                add_span_event("deps.add.completed", {"result": "success"})
                return result
        
        result = mock_deps_add(["requests", "httpx"], dev=True)
        assert result["added"] == ["requests", "httpx"]
        assert result["dev"] is True

    def test_error_instrumentation_pattern(self):
        """Test error instrumentation pattern."""
        @instrument_command("test.failing_operation")
        def mock_failing_operation():
            with span("test.operation") as current_span:
                try:
                    raise ValueError("Simulated error")
                except Exception as e:
                    # Pattern for error instrumentation
                    if current_span and hasattr(current_span, 'set_attribute'):
                        current_span.set_attribute("operation.success", False)
                        current_span.set_attribute("operation.error", str(e))
                    
                    add_span_event("operation.error", {
                        "error.type": type(e).__name__,
                        "error.message": str(e)
                    })
                    raise
        
        with pytest.raises(ValueError, match="Simulated error"):
            mock_failing_operation()

    def test_metrics_instrumentation_pattern(self):
        """Test metrics instrumentation pattern."""
        # Pattern used for recording metrics in operations
        counter = metric_counter("test.operations")
        histogram = metric_histogram("test.operation.duration")
        
        start_time = time.time()
        
        # Simulate operation
        time.sleep(0.01)
        
        # Record metrics (following uvmgr pattern)
        duration = time.time() - start_time
        counter(1)  # Increment operation count
        histogram(duration)  # Record duration
        
        # Should not raise exceptions
        assert duration > 0

    def test_telemetry_consistency_across_modules(self):
        """Test that telemetry is consistent across different modules."""
        # This tests that the same patterns work for different module types
        
        # CLI module pattern
        with span("cli.command") as cli_span:
            add_span_attributes(**{
                CliAttributes.CLI_COMMAND: "test",
                CliAttributes.CLI_EXIT_CODE: 0
            })
        
        # Operations module pattern  
        with span("ops.operation") as ops_span:
            add_span_attributes(**{
                PackageAttributes.OPERATION: "test",
                PackageAttributes.PACKAGE_NAME: "test-package"
            })
        
        # Runtime module pattern
        with span("runtime.execution") as runtime_span:
            add_span_event("runtime.process.started", {"command": "test"})
            add_span_event("runtime.process.completed", {"exit_code": 0})


class TestTelemetryPerformance:
    """Test telemetry performance characteristics."""

    def test_telemetry_overhead(self):
        """Test that telemetry has minimal performance overhead."""
        # Measure time with and without telemetry
        iterations = 1000
        
        # Without telemetry
        start_time = time.time()
        for _ in range(iterations):
            pass  # No-op
        baseline_time = time.time() - start_time
        
        # With telemetry
        start_time = time.time()
        for i in range(iterations):
            with span(f"test.operation.{i}"):
                counter = metric_counter("test.counter")
                counter(1)
        telemetry_time = time.time() - start_time
        
        # Telemetry should not add significant overhead (factor of 1000x is reasonable for no-op)
        overhead_factor = telemetry_time / baseline_time if baseline_time > 0 else 0
        assert overhead_factor < 1000, f"Telemetry overhead too high: {overhead_factor}x"

    def test_span_creation_performance(self):
        """Test span creation performance."""
        iterations = 100
        
        start_time = time.time()
        for i in range(iterations):
            with span(f"performance.test.{i}"):
                # Minimal work inside span
                pass
        duration = time.time() - start_time
        
        # Should complete quickly
        avg_span_time = duration / iterations
        assert avg_span_time < 0.01, f"Span creation too slow: {avg_span_time}s per span"

    def test_metrics_recording_performance(self):
        """Test metrics recording performance."""
        counter = metric_counter("performance.test.counter")
        histogram = metric_histogram("performance.test.histogram")
        
        iterations = 1000
        
        start_time = time.time()
        for i in range(iterations):
            counter(1)
            histogram(0.001)
        duration = time.time() - start_time
        
        # Should complete quickly
        avg_metric_time = duration / (iterations * 2)  # 2 metrics per iteration
        assert avg_metric_time < 0.001, f"Metrics recording too slow: {avg_metric_time}s per metric"


if __name__ == "__main__":
    pytest.main([__file__])