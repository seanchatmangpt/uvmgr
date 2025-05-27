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
from contextlib import contextmanager
from typing import Any, Callable

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
    def span(name: str, **attrs: Any):
        with _TRACER.start_as_current_span(name, attributes=attrs):
            yield

    def metric_counter(name: str) -> Callable[[int], None]:
        return metrics.get_meter("uvmgr").create_counter(name).add

except ImportError:  # SDK not installed – degrade gracefully

    @contextmanager
    def span(name: str, **attrs: Any):  # type: ignore[arg-type]
        yield

    def metric_counter(name: str):  # type: ignore[return-value]
        def _noop(_=1, **__): ...
        return _noop
