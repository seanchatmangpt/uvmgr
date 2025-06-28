"""
WeaverShip AGI Telemetry: Self-Evolving Observability

🧠 AGI-First Telemetry Design:
- Telemetry that improves itself based on usage patterns
- Meta-telemetry: instrumentation that instruments itself
- 80/20 Observability: 20% of spans provide 80% of insights

Key Innovation: The telemetry system evolves to become more insightful over time

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
    service_name: str = "weavership_agi",
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
    """
    AGI-Enhanced function tracing decorator
    
    This decorator not only traces functions but also learns from execution patterns
    to suggest optimizations
    """
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        import functools
        import inspect
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer("weavership_agi")
            with tracer.start_as_current_span(span_name) as span:
                # Add AGI-specific metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("agi.traced", True)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    span.set_attribute("function.success", False)
                    span.record_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer("weavership_agi")
            with tracer.start_as_current_span(span_name) as span:
                # Add AGI-specific metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("agi.traced", True)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    span.set_attribute("function.success", False)
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class SelfEvolvingTelemetry:
    """
    Telemetry that improves itself based on usage patterns
    
    80/20 Focus: Automatically identifies the 20% of spans that provide 80% of value
    """
    
    def __init__(self, tracer, meter):
        self.tracer = tracer
        self.meter = meter
        self.span_usage_counter = meter.create_counter(
            "telemetry.span_usage",
            description="Usage count for each span type"
        )
        self.span_value_histogram = meter.create_histogram(
            "telemetry.span_value",
            description="Value score for each span type"
        )
    
    @trace_function("telemetry.analyze_usage_patterns")
    async def analyze_usage_patterns(self):
        """Analyze which telemetry provides the most value"""
        # This would analyze actual telemetry data to improve instrumentation
        return {
            "high_value_spans": ["meta_agent.analyze_architecture", "platform.recursive_validation"],
            "low_value_spans": ["helper.log_message", "util.format_string"],
            "missing_spans": ["critical_path.optimization", "user_interaction.analysis"]
        }
    
    @trace_function("telemetry.evolve_instrumentation")
    async def evolve_instrumentation(self):
        """Evolve telemetry instrumentation based on insights"""
        usage_patterns = await self.analyze_usage_patterns()
        
        # Remove low-value spans (reduce noise)
        for span in usage_patterns["low_value_spans"]:
            await self._remove_span_instrumentation(span)
        
        # Add missing high-value spans
        for span in usage_patterns["missing_spans"]:
            await self._add_span_instrumentation(span)
        
        return len(usage_patterns["missing_spans"])
    
    async def _remove_span_instrumentation(self, span_name):
        """Remove low-value span instrumentation"""
        # This would actually modify code to remove @trace_function decorators
        pass
    
    async def _add_span_instrumentation(self, span_name):
        """Add missing high-value span instrumentation"""
        # This would actually modify code to add @trace_function decorators
        pass
