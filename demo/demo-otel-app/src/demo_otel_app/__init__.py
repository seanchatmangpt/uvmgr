"""
demo_otel_app: With built-in OpenTelemetry instrumentation.
"""

from demo_otel_app._telemetry import configure_telemetry, trace_function

# Initialize telemetry on import
tracer, meter = configure_telemetry()

# Create common metrics
request_counter = meter.create_counter(
    "demo_otel_app.requests",
    description="Number of requests processed",
    unit="1",
)

error_counter = meter.create_counter(
    "demo_otel_app.errors",
    description="Number of errors encountered",
    unit="1",
)

duration_histogram = meter.create_histogram(
    "demo_otel_app.duration",
    description="Operation duration",
    unit="ms",
)

__version__ = "0.0.0"
__all__ = [
    "tracer",
    "meter",
    "request_counter",
    "error_counter",
    "duration_histogram",
    "trace_function",
]


