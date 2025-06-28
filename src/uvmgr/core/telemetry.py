"""
uvmgr.core.telemetry
--------------------
OpenTelemetry integration and telemetry utilities for uvmgr.

This module provides comprehensive telemetry capabilities for the uvmgr application:

• **Logging Setup**: Always exports ``setup_logging`` – used by `uvmgr.cli`
• **Span Management**: Context-manager ``span(name, **attrs)`` for distributed tracing
• **Metrics Collection**: Functions for counters, histograms, and gauges
• **Exception Recording**: Utilities for recording exceptions with semantic conventions
• **Graceful Degradation**: No-op implementations when OpenTelemetry is not available

The module automatically initializes OpenTelemetry when the environment variable
`OTEL_EXPORTER_OTLP_ENDPOINT` is set and the `opentelemetry-sdk` package is installed.
Otherwise, it provides no-op implementations that allow the application to run normally.

Example
-------
    # Basic span usage
    with span("my_operation", operation_type="custom"):
        result = perform_operation()
    
    # Metrics collection
    counter = metric_counter("my.operation.calls")
    counter(1, {"operation": "add"})
    
    # Exception recording
    try:
        risky_operation()
    except Exception as e:
        record_exception(e, attributes={"operation": "risky"})
        raise

Environment Variables
--------------------
- OTEL_EXPORTER_OTLP_ENDPOINT : OpenTelemetry collector endpoint
- OTEL_SERVICE_NAME : Service name for telemetry (default: "uvmgr")
- OTEL_SERVICE_VERSION : Service version for telemetry

See Also
--------
- :mod:`uvmgr.core.instrumentation` : Command instrumentation decorators
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

import logging
import os
import platform
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any


# --------------------------------------------------------------------------- #
# Public helper: plain logging                                                #
# --------------------------------------------------------------------------- #
def setup_logging(level: str = "INFO") -> None:
    """
    Initialize root logging configuration once, idempotently.
    
    This function sets up the basic logging configuration for the uvmgr application.
    It's called by `uvmgr.cli` on startup and ensures consistent logging across
    all modules. The function is idempotent - calling it multiple times has no
    additional effect.
    
    Parameters
    ----------
    level : str, optional
        Logging level to use. Must be a valid logging level name
        (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default is "INFO".
    
    Notes
    -----
    The logging configuration includes:
    - Timestamp format: HH:MM:SS
    - Level name with 8-character padding
    - Logger name
    - Message content
    
    Example
    -------
    >>> setup_logging("DEBUG")
    >>> logging.getLogger("uvmgr").info("Application started")
    14:30:25 INFO     uvmgr │ Application started
    """
    if logging.getLogger().handlers:
        return  # already configured

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s │ %(message)s",
        datefmt="%H:%M:%S",
    )


# --------------------------------------------------------------------------- #
# Optional OpenTelemetry                                                      #
# --------------------------------------------------------------------------- #
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Only initialize if OTEL endpoint is configured
    _OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not _OTEL_ENDPOINT:
        raise ImportError("OTEL_EXPORTER_OTLP_ENDPOINT not set")

    _RESOURCE = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "uvmgr"),
            "service.instance.id": os.getenv("HOSTNAME", "localhost"),
            "os.type": platform.system().lower(),
        }
    )

    # Setup Traces
    _TRACE_PROVIDER = TracerProvider(resource=_RESOURCE)
    _TRACE_PROVIDER.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=_OTEL_ENDPOINT)))
    trace.set_tracer_provider(_TRACE_PROVIDER)
    _TRACER = trace.get_tracer("uvmgr")

    # Setup Metrics
    _METRIC_READER = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=_OTEL_ENDPOINT),
        export_interval_millis=5000  # Export every 5 seconds
    )
    _METRIC_PROVIDER = MeterProvider(resource=_RESOURCE, metric_readers=[_METRIC_READER])
    metrics.set_meter_provider(_METRIC_PROVIDER)
    _METER = metrics.get_meter("uvmgr")

    @contextmanager
    def span(name: str, span_kind=None, **attrs: Any):
        kwargs = {"attributes": attrs}
        if span_kind is not None:
            kwargs["kind"] = span_kind
        with _TRACER.start_as_current_span(name, **kwargs):
            yield

    def metric_counter(name: str) -> Callable[[int], None]:
        return _METER.create_counter(name).add

    def metric_histogram(name: str, unit: str = "s") -> Callable[[float], None]:
        """
        Create a histogram metric for recording distributions.
        
        Histograms are used to track the distribution of values, such as
        operation durations, request sizes, or other measurable quantities.
        
        Parameters
        ----------
        name : str
            The name of the histogram metric. Should follow OpenTelemetry
            naming conventions (e.g., "operation.duration").
        unit : str, optional
            The unit of measurement for the histogram values. Common units
            include "s" (seconds), "ms" (milliseconds), "bytes", "count".
            Default is "s".
        
        Returns
        -------
        Callable[[float], None]
            A function that records values in the histogram. The function
            accepts a float value and optional attributes as keyword arguments.
        
        Example
        -------
        >>> duration_histogram = metric_histogram("api.request.duration", unit="ms")
        >>> duration_histogram(150.5, {"endpoint": "/users", "method": "GET"})
        """
        return _METER.create_histogram(name, unit=unit).record

    def metric_gauge(name: str) -> Callable[[float], None]:
        """
        Create a gauge metric for recording current values.
        
        Gauges represent a single numerical value that can arbitrarily go up
        and down. They are typically used for measured values like temperatures
        or current memory usage, or "counts" that can go up and down, like
        the number of concurrent requests.
        
        Parameters
        ----------
        name : str
            The name of the gauge metric. Should follow OpenTelemetry
            naming conventions (e.g., "system.memory.usage").
        
        Returns
        -------
        Callable[[float], None]
            A function that updates the gauge value. The function accepts
            a float value and optional attributes as keyword arguments.
            Positive values increase the gauge, negative values decrease it.
        
        Notes
        -----
        OpenTelemetry uses UpDownCounter for gauge-like behavior, which
        allows both positive and negative increments.
        
        Example
        -------
        >>> memory_gauge = metric_gauge("system.memory.usage")
        >>> memory_gauge(1024.5, {"type": "heap"})  # Set to 1024.5
        >>> memory_gauge(-100.0, {"type": "heap"})  # Decrease by 100
        """
        # Note: OTEL uses UpDownCounter for gauge-like behavior
        return _METER.create_up_down_counter(name).add

    def record_exception(e: Exception, escaped: bool = True, attributes: dict[str, Any] | None = None):
        """
        Record an exception in the current span with semantic conventions.
        
        This function records exception information in the current OpenTelemetry span,
        including the exception type, message, and stack trace. It also sets the
        span status to ERROR and adds semantic convention attributes for common
        exception types.
        
        Parameters
        ----------
        e : Exception
            The exception to record. The exception type, message, and stack trace
            will be extracted and recorded.
        escaped : bool, optional
            Whether the exception escaped the current span. True if the exception
            was not caught and handled within the span. Default is True.
        attributes : dict[str, Any], optional
            Additional attributes to record with the exception. These will be
            merged with the standard semantic convention attributes.
        
        Notes
        -----
        The function automatically adds the following semantic convention attributes:
        - exception.type: The exception class name
        - exception.message: The exception message
        - exception.escaped: Whether the exception escaped
        - exception.stacktrace: The exception stack trace
        
        For specific exception types, additional attributes are added:
        - subprocess.CalledProcessError: process.exit_code, process.command
        - FileNotFoundError/IOError: file.path
        
        Example
        -------
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     record_exception(e, attributes={"operation": "validation"})
        ...     raise
        """
        current_span = trace.get_current_span()
        if current_span.is_recording():
            # Record the exception
            current_span.record_exception(e, escaped=escaped)

            # Add semantic convention attributes
            exc_attrs = {
                "exception.type": type(e).__name__,
                "exception.message": str(e),
                "exception.escaped": str(escaped),
            }

            # Add custom attributes if provided
            if attributes:
                exc_attrs.update(attributes)

            # Add specific attributes for common errors
            if hasattr(e, "returncode"):  # subprocess.CalledProcessError
                exc_attrs["process.exit_code"] = e.returncode
                if hasattr(e, "cmd"):
                    exc_attrs["process.command"] = " ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
            elif hasattr(e, "filename"):  # FileNotFoundError, IOError
                exc_attrs["file.path"] = str(e.filename)

            # Add event with attributes
            current_span.add_event("exception", exc_attrs)

            # Set error status
            from opentelemetry.trace import Status, StatusCode
            current_span.set_status(Status(StatusCode.ERROR, str(e)))

    def get_current_span():
        """
        Get the current active span from the OpenTelemetry context.
        
        Returns
        -------
        opentelemetry.trace.Span
            The current active span. If no span is active, returns a no-op span
            that can be safely used for all span operations.
        
        Example
        -------
        >>> current_span = get_current_span()
        >>> if current_span.is_recording():
        ...     current_span.set_attribute("custom.attr", "value")
        """
        return trace.get_current_span()

    def set_span_status(status_code, description: str = ""):
        """
        Set the status of the current span.
        
        Parameters
        ----------
        status_code : str
            The status code to set. Valid values are:
            - "OK": Operation completed successfully
            - "ERROR": Operation failed with an error
            - "UNSET": Status is not set (default)
        description : str, optional
            A description of the status, particularly useful for ERROR status.
            Default is an empty string.
        
        Example
        -------
        >>> set_span_status("OK")
        >>> set_span_status("ERROR", "Failed to connect to database")
        """
        from opentelemetry.trace import Status, StatusCode
        current_span = trace.get_current_span()
        if current_span.is_recording():
            if status_code == "OK":
                current_span.set_status(Status(StatusCode.OK))
            elif status_code == "ERROR":
                current_span.set_status(Status(StatusCode.ERROR, description))
            else:
                current_span.set_status(Status(StatusCode.UNSET))

except ImportError:  # SDK not installed – degrade gracefully

    @contextmanager
    def span(name: str, span_kind=None, **attrs: Any):  # type: ignore[arg-type]
        yield

    def metric_counter(name: str):  # type: ignore[return-value]
        def _noop(_=1, **__): ...
        return _noop

    def metric_histogram(name: str, unit: str = "s"):  # type: ignore[return-value]
        def _noop(_: float, **__): ...
        return _noop

    def metric_gauge(name: str):  # type: ignore[return-value]
        def _noop(_: float, **__): ...
        return _noop

    def record_exception(e: Exception, escaped: bool = True, attributes: dict[str, Any] | None = None):
        pass

    def get_current_span():  # type: ignore[return-value]
        class _NoopSpan:
            def is_recording(self): return False
            def set_status(self, *args, **kwargs): pass
            def set_attributes(self, *args, **kwargs): pass
            def add_event(self, *args, **kwargs): pass
        return _NoopSpan()

    def set_span_status(status_code, description: str = ""):
        pass
