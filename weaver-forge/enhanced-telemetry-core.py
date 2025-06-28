"""
Enhanced telemetry core module for 100% OTEL coverage.
This is an example of what the upgraded telemetry.py would look like.
"""

import functools
import os
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union
from uuid import uuid4

# Graceful degradation if OTEL not installed
try:
    from opentelemetry import baggage, context, metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID, SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.semconv.trace import SpanAttributes
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    trace = None
    metrics = None


# Singleton telemetry instance
_telemetry: Optional["Telemetry"] = None


class Telemetry:
    """Enhanced telemetry system with full OTEL support."""

    def __init__(self):
        """Initialize telemetry with OTEL providers."""
        self.enabled = HAS_OTEL and os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        self.tracer = None
        self.meter = None
        self.logger_instrumentor = None

        # Metric instruments cache
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}

        if self.enabled:
            self._setup_otel()

    def _setup_otel(self):
        """Configure OpenTelemetry with all components."""
        # Create resource with rich metadata
        resource = Resource.create({
            SERVICE_NAME: "uvmgr",
            SERVICE_INSTANCE_ID: str(uuid4()),
            ResourceAttributes.SERVICE_VERSION: self._get_version(),
            ResourceAttributes.OS_TYPE: sys.platform,
            ResourceAttributes.OS_DESCRIPTION: self._get_os_description(),
            ResourceAttributes.PROCESS_PID: os.getpid(),
            ResourceAttributes.PROCESS_EXECUTABLE_NAME: "uvmgr",
            ResourceAttributes.PROCESS_COMMAND: " ".join(sys.argv),
            ResourceAttributes.PROCESS_RUNTIME_NAME: "python",
            ResourceAttributes.PROCESS_RUNTIME_VERSION: sys.version.split()[0],
            "uvmgr.cache_dir": os.environ.get("UVMGR_CACHE_DIR", "~/.uvmgr_cache"),
        })

        # Setup tracing
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        trace_provider = TracerProvider(resource=resource)
        trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(trace_provider)

        # Setup metrics
        metric_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
            export_interval_millis=10000,  # 10 seconds
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        # Setup propagation (for distributed tracing)
        set_global_textmap(TraceContextTextMapPropagator())

        # Setup logging instrumentation
        LoggingInstrumentor().instrument(set_logging_format=True)
        self.logger_instrumentor = LoggingInstrumentor()

        # Get tracer and meter instances
        self.tracer = trace.get_tracer("uvmgr", self._get_version())
        self.meter = metrics.get_meter("uvmgr", self._get_version())

    def _get_version(self) -> str:
        """Get uvmgr version."""
        try:
            from importlib.metadata import version
            return version("uvmgr")
        except:
            return "unknown"

    def _get_os_description(self) -> str:
        """Get OS description."""
        import platform
        return f"{platform.system()} {platform.release()}"

    @contextmanager
    def span(
        self,
        name: str,
        kind: trace.SpanKind | None = None,
        attributes: dict[str, Any] | None = None,
        links: list | None = None,
        record_exception: bool = True,
    ):
        """
        Create a span with automatic exception handling.
        
        Args:
            name: Span name
            kind: Span kind (SERVER, CLIENT, INTERNAL, PRODUCER, CONSUMER)
            attributes: Initial span attributes
            links: Links to other spans
            record_exception: Whether to automatically record exceptions
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        # Start span with attributes
        with self.tracer.start_as_current_span(
            name,
            kind=kind or trace.SpanKind.INTERNAL,
            attributes=attributes,
            links=links,
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                if record_exception:
                    self.record_exception(e, escaped=True)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def record_exception(
        self,
        exception: Exception,
        escaped: bool = False,
        attributes: dict[str, Any] | None = None,
    ):
        """
        Record an exception in the current span.
        
        Args:
            exception: The exception to record
            escaped: Whether the exception escaped the span
            attributes: Additional attributes for the exception event
        """
        if not self.enabled:
            return

        span = trace.get_current_span()
        if not span or not span.is_recording():
            return

        # Build exception attributes following semantic conventions
        exc_type = type(exception).__name__
        exc_message = str(exception)

        event_attributes = {
            "exception.type": exc_type,
            "exception.message": exc_message,
            "exception.escaped": str(escaped),
        }

        # Add traceback if available
        if sys.exc_info()[0] is not None:
            import traceback
            event_attributes["exception.stacktrace"] = "".join(
                traceback.format_exception(*sys.exc_info())
            )

        # Add custom attributes
        if attributes:
            event_attributes.update(attributes)

        # Record the exception event
        span.add_event("exception", event_attributes)

        # Add specific attributes for known exception types
        if hasattr(exception, "returncode"):  # CalledProcessError
            span.set_attribute("process.exit_code", exception.returncode)
        if hasattr(exception, "filename"):  # FileNotFoundError
            span.set_attribute("file.path", str(exception.filename))

    def counter(self, name: str, unit: str = "1", description: str = "") -> Any:
        """Get or create a counter metric."""
        if not self.enabled or not self.meter:
            return None

        if name not in self._counters:
            self._counters[name] = self.meter.create_counter(
                name=name,
                unit=unit,
                description=description or f"Counter for {name}",
            )
        return self._counters[name]

    def histogram(self, name: str, unit: str = "1", description: str = "") -> Any:
        """Get or create a histogram metric."""
        if not self.enabled or not self.meter:
            return None

        if name not in self._histograms:
            self._histograms[name] = self.meter.create_histogram(
                name=name,
                unit=unit,
                description=description or f"Histogram for {name}",
            )
        return self._histograms[name]

    def gauge(self, name: str, unit: str = "1", description: str = "") -> Any:
        """Get or create a gauge metric."""
        if not self.enabled or not self.meter:
            return None

        if name not in self._gauges:
            # Note: Gauges in OTEL are typically observable
            self._gauges[name] = self.meter.create_up_down_counter(
                name=name,
                unit=unit,
                description=description or f"Gauge for {name}",
            )
        return self._gauges[name]

    def add_span_event(self, name: str, attributes: dict[str, Any] | None = None):
        """Add an event to the current span."""
        if not self.enabled:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(name, attributes or {})

    def set_span_attributes(self, attributes: dict[str, Any]):
        """Set attributes on the current span."""
        if not self.enabled:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                # Ensure attribute values are valid types
                if isinstance(value, (str, bool, int, float)):
                    span.set_attribute(key, value)
                elif isinstance(value, (list, tuple)):
                    # Convert to string for lists
                    span.set_attribute(key, str(value))
                else:
                    # Convert everything else to string
                    span.set_attribute(key, str(value))

    def get_trace_context(self) -> dict[str, str] | None:
        """Get current trace context for propagation."""
        if not self.enabled:
            return None

        from opentelemetry import propagate

        carrier = {}
        propagate.inject(carrier)
        return carrier

    def set_trace_context(self, carrier: dict[str, str]):
        """Set trace context from propagation headers."""
        if not self.enabled or not carrier:
            return

        from opentelemetry import propagate

        ctx = propagate.extract(carrier)
        context.attach(ctx)


# Global functions for easy access

def get_telemetry() -> Telemetry:
    """Get the global telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = Telemetry()
    return _telemetry


@contextmanager
def span(name: str, **kwargs):
    """Create a span (convenience function)."""
    telemetry = get_telemetry()
    with telemetry.span(name, **kwargs) as s:
        yield s


def metric_counter(name: str, value: int | float = 1, attributes: dict[str, Any] | None = None):
    """Increment a counter metric."""
    telemetry = get_telemetry()
    counter = telemetry.counter(name)
    if counter:
        counter.add(value, attributes or {})


def metric_histogram(name: str, value: int | float, attributes: dict[str, Any] | None = None):
    """Record a histogram metric."""
    telemetry = get_telemetry()
    histogram = telemetry.histogram(name)
    if histogram:
        histogram.record(value, attributes or {})


def metric_gauge(name: str, value: int | float, attributes: dict[str, Any] | None = None):
    """Set a gauge metric."""
    telemetry = get_telemetry()
    gauge = telemetry.gauge(name)
    if gauge:
        # For up-down counter, we add the delta
        gauge.add(value, attributes or {})


def record_exception(exception: Exception, **kwargs):
    """Record an exception in the current span."""
    telemetry = get_telemetry()
    telemetry.record_exception(exception, **kwargs)


def add_event(name: str, attributes: dict[str, Any] | None = None):
    """Add an event to the current span."""
    telemetry = get_telemetry()
    telemetry.add_span_event(name, attributes)


def set_attributes(**attributes):
    """Set attributes on the current span."""
    telemetry = get_telemetry()
    telemetry.set_span_attributes(attributes)


# Enhanced decorators

def timed(func: Callable) -> Callable:
    """
    Enhanced @timed decorator that creates spans and records metrics.
    
    This replaces the simple timing decorator with full OTEL integration.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create span name from function
        span_name = f"{func.__module__}.{func.__name__}"

        # Start timing
        start_time = time.time()

        with span(
            span_name,
            attributes={
                SpanAttributes.CODE_FUNCTION: func.__name__,
                SpanAttributes.CODE_NAMESPACE: func.__module__,
            }
        ) as current_span:
            try:
                result = func(*args, **kwargs)

                # Record success metrics
                duration = time.time() - start_time
                metric_histogram(
                    "function.duration",
                    duration,
                    {"function": func.__name__, "module": func.__module__, "status": "success"}
                )
                metric_counter(
                    "function.calls",
                    1,
                    {"function": func.__name__, "module": func.__module__, "status": "success"}
                )

                return result

            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                metric_histogram(
                    "function.duration",
                    duration,
                    {"function": func.__name__, "module": func.__module__, "status": "error"}
                )
                metric_counter(
                    "function.calls",
                    1,
                    {"function": func.__name__, "module": func.__module__, "status": "error"}
                )
                metric_counter(
                    "function.errors",
                    1,
                    {"function": func.__name__, "module": func.__module__, "error_type": type(e).__name__}
                )
                raise

    return wrapper


def trace_method(method: Callable) -> Callable:
    """
    Decorator for tracing class methods with semantic conventions.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Create span name from class and method
        class_name = self.__class__.__name__
        span_name = f"{class_name}.{method.__name__}"

        with span(
            span_name,
            attributes={
                SpanAttributes.CODE_FUNCTION: method.__name__,
                SpanAttributes.CODE_NAMESPACE: f"{self.__class__.__module__}.{class_name}",
                "uvmgr.class": class_name,
            }
        ):
            return method(self, *args, **kwargs)

    return wrapper


# Context manager for batch operations

@contextmanager
def batch_operation(operation_name: str, items: list):
    """
    Context manager for batch operations with progress tracking.
    """
    with span(f"batch.{operation_name}") as batch_span:
        if batch_span:
            batch_span.set_attribute("batch.size", len(items))
            batch_span.set_attribute("batch.operation", operation_name)

        completed = 0
        failed = 0
        start_time = time.time()

        try:
            yield
        finally:
            # Record batch metrics
            duration = time.time() - start_time

            if batch_span:
                batch_span.set_attribute("batch.completed", completed)
                batch_span.set_attribute("batch.failed", failed)
                batch_span.set_attribute("batch.duration", duration)

            metric_histogram(
                "batch.duration",
                duration,
                {"operation": operation_name, "size": len(items)}
            )
            metric_counter(
                "batch.operations",
                1,
                {"operation": operation_name, "status": "failed" if failed > 0 else "success"}
            )


# Initialize telemetry on import
_telemetry = Telemetry()
