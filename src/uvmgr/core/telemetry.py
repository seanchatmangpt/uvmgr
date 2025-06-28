"""
uvmgr.core.telemetry
--------------------
Logging bootstrap + (optional) OpenTelemetry exporter.

*  Always exports ``setup_logging`` – used by `uvmgr.cli`.
*  Exports context-manager ``span(name, **attrs)`` that becomes a real OTEL
   span **iff** `opentelemetry-sdk` is installed *and* the environment sets
   `OTEL_EXPORTER_OTLP_ENDPOINT`.  Otherwise it degrades to a no-op.
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
    Initialise root logging once, idempotently.  Called by `uvmgr.cli` on
    start-up.
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
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _RESOURCE = Resource.create(
        {
            "service.name": "uvmgr",
            "service.instance.id": os.getenv("HOSTNAME", "localhost"),
            "os.type": platform.system().lower(),
        }
    )
    _PROVIDER = TracerProvider(resource=_RESOURCE)
    _PROVIDER.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(_PROVIDER)
    _TRACER = trace.get_tracer("uvmgr")

    @contextmanager
    def span(name: str, span_kind=None, **attrs: Any):
        kwargs = {"attributes": attrs}
        if span_kind is not None:
            kwargs["kind"] = span_kind
        with _TRACER.start_as_current_span(name, **kwargs):
            yield

    def metric_counter(name: str) -> Callable[[int], None]:
        return metrics.get_meter("uvmgr").create_counter(name).add

    def metric_histogram(name: str, unit: str = "s") -> Callable[[float], None]:
        """Create a histogram metric for recording distributions."""
        return metrics.get_meter("uvmgr").create_histogram(name, unit=unit).record

    def metric_gauge(name: str) -> Callable[[float], None]:
        """Create a gauge metric for recording current values."""
        # Note: OTEL uses UpDownCounter for gauge-like behavior
        return metrics.get_meter("uvmgr").create_up_down_counter(name).add

    def record_exception(e: Exception, escaped: bool = True, attributes: dict[str, Any] | None = None):
        """Record an exception in the current span with semantic conventions."""
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
        """Get the current active span."""
        return trace.get_current_span()

    def set_span_status(status_code, description: str = ""):
        """Set the status of the current span."""
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
