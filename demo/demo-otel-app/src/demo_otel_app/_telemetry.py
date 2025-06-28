"""
OpenTelemetry configuration for demo_otel_app.

This module provides centralized telemetry configuration including
tracing, metrics, and logging instrumentation.
"""

from __future__ import annotations

import os
from typing import Tuple

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


def configure_telemetry(
    service_name: str = "demo_otel_app",
    service_version: str = "0.0.0",
    deployment_environment: str = "development"
) -> Tuple[trace.Tracer, metrics.Meter]:
    """
    Configure OpenTelemetry for the project.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        deployment_environment: Deployment environment (development, staging, production)
        
    Returns:
        Tuple of (tracer, meter) for instrumentation
    """
    # Create resource
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_environment,
    })
    
    # Configure tracing
    tracer_provider = TracerProvider(resource=resource)
    
    # Add exporters based on environment
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # Use OTLP exporter if endpoint is configured
        otlp_exporter = OTLPSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    else:
        # Default to console exporter
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    trace.set_tracer_provider(tracer_provider)
    
    # Configure metrics
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        metric_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(),
            export_interval_millis=10000,
        )
    else:
        metric_reader = PeriodicExportingMetricReader(
            exporter=ConsoleMetricExporter(),
            export_interval_millis=10000,
        )
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)
    
    # Configure logging instrumentation
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    # Return configured instances
    tracer = trace.get_tracer(service_name, service_version)
    meter = metrics.get_meter(service_name, service_version)
    
    return tracer, meter


# Convenience decorators
def trace_function(name: str = None):
    """Decorator to trace function execution."""
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer("demo_otel_app")
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator
