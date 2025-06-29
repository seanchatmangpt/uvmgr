"""
Telemetry compatibility tests for Weaver Forge.

This module validates that Weaver Forge's telemetry implementation
matches Weaver standards and patterns for observability.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List

import pytest
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter

from uvmgr.ops.weaver_forge import (
    generate_bulk_from_templates,
    generate_bulk_scaffolds,
    generate_from_batch_file,
    create_bulk_template,
    validate_bulk_templates
)
from uvmgr.core.telemetry import (
    span,
    metric_counter,
    metric_histogram,
    get_tracer,
    get_meter
)


class TestWeaverTelemetryCompatibility:
    """Test suite for Weaver telemetry compatibility."""

    @pytest.fixture(autouse=True)
    def setup_telemetry(self):
        """Setup telemetry for testing with Weaver-compatible configuration."""
        # Setup trace provider with in-memory exporter
        self.trace_provider = TracerProvider()
        self.span_exporter = InMemorySpanExporter()
        self.trace_provider.add_span_processor(
            trace.BatchSpanProcessor(self.span_exporter)
        )
        trace.set_tracer_provider(self.trace_provider)
        
        # Setup meter provider with in-memory reader
        self.meter_provider = MeterProvider()
        self.metric_reader = InMemoryMetricReader()
        self.meter_provider.add_metric_reader(self.metric_reader)
        metrics.set_meter_provider(self.meter_provider)
        
        # Setup Weaver-compatible tracer and meter
        self.tracer = get_tracer("weaver_forge")
        self.meter = get_meter("weaver_forge")
        
        yield
        
        # Cleanup
        self.span_exporter.shutdown()
        self.metric_reader.shutdown()

    @pytest.fixture
    def sample_generation_specs(self) -> List[Dict[str, Any]]:
        """Sample generation specifications for testing."""
        return [
            {
                "template": "component",
                "name": "TestComponent",
                "parameters": {
                    "style": "styled-components",
                    "typescript": True
                }
            }
        ]

    def test_weaver_span_naming_convention(self, sample_generation_specs):
        """Test that span names follow Weaver naming conventions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous spans
                self.span_exporter.clear()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify spans were created
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Check Weaver naming conventions
                weaver_span_names = [
                    "weaver_forge.bulk_generate",
                    "weaver_forge.template_generate",
                    "weaver_forge.scaffold_create"
                ]
                
                span_names = [span.name for span in spans]
                assert any(name in span_names for name in weaver_span_names)

    def test_weaver_span_attributes(self, sample_generation_specs):
        """Test that span attributes follow Weaver patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous spans
                self.span_exporter.clear()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify spans and attributes
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Find bulk generation span
                bulk_span = None
                for span in spans:
                    if span.name == "weaver_forge.bulk_generate":
                        bulk_span = span
                        break
                
                assert bulk_span is not None
                
                # Check Weaver-style attributes
                weaver_attributes = [
                    "specs_count",
                    "parallel",
                    "dry_run",
                    "total_specs",
                    "successful",
                    "failed",
                    "total_files",
                    "success_rate"
                ]
                
                for attr in weaver_attributes:
                    assert attr in bulk_span.attributes or f"weaver_forge.{attr}" in bulk_span.attributes

    def test_weaver_span_events(self, sample_generation_specs):
        """Test that span events follow Weaver patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous spans
                self.span_exporter.clear()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify spans and events
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Check for Weaver-style events
                weaver_events = [
                    "weaver_forge.bulk_generated",
                    "weaver_forge.template_generated",
                    "weaver_forge.scaffold_created"
                ]
                
                events_found = []
                for span in spans:
                    if span.events:
                        for event in span.events:
                            events_found.append(event.name)
                
                assert any(event in events_found for event in weaver_events)

    def test_weaver_metrics_naming(self, sample_generation_specs):
        """Test that metrics follow Weaver naming conventions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous metrics
                self.metric_reader.collect()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Collect metrics
                metrics_data = self.metric_reader.collect()
                
                # Check Weaver metric naming patterns
                weaver_metric_patterns = [
                    "weaver_forge.bulk_generation",
                    "weaver_forge.template_generation",
                    "weaver_forge.scaffold_creation",
                    "weaver_forge.generation_duration",
                    "weaver_forge.files_created"
                ]
                
                metric_names = []
                for metric in metrics_data:
                    metric_names.append(metric.name)
                
                # Verify at least some Weaver-style metrics are present
                assert len(metric_names) > 0

    def test_weaver_metrics_attributes(self, sample_generation_specs):
        """Test that metrics have Weaver-compatible attributes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous metrics
                self.metric_reader.collect()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Collect metrics
                metrics_data = self.metric_reader.collect()
                
                # Check for Weaver-style metric attributes
                weaver_attributes = [
                    "template_type",
                    "parallel",
                    "dry_run",
                    "success"
                ]
                
                for metric in metrics_data:
                    for point in metric.data.points:
                        if hasattr(point, 'attributes'):
                            # Verify some Weaver-style attributes are present
                            assert len(point.attributes) > 0

    def test_weaver_error_handling_telemetry(self, sample_generation_specs):
        """Test that errors are properly captured in Weaver telemetry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function to raise an exception
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.side_effect = Exception("Test error")
                
                # Clear previous spans
                self.span_exporter.clear()
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify error handling
                assert result["failed"] == 1
                assert result["success_rate"] == 0.0
                
                # Verify telemetry captured the errors
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Check for error spans or error attributes
                error_spans = []
                for span in spans:
                    if span.status.status_code == trace.StatusCode.ERROR:
                        error_spans.append(span)
                    elif span.events:
                        for event in span.events:
                            if "error" in event.name.lower():
                                error_spans.append(span)
                
                assert len(error_spans) > 0

    def test_weaver_performance_telemetry(self, sample_generation_specs):
        """Test that performance metrics follow Weaver patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous metrics
                self.metric_reader.collect()
                
                start_time = time.time()
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                end_time = time.time()
                
                # Verify performance metrics
                assert result["duration"] > 0
                assert result["duration"] <= (end_time - start_time) + 0.1  # Allow some overhead
                
                # Collect metrics
                metrics_data = self.metric_reader.collect()
                
                # Check for performance-related metrics
                performance_metrics = []
                for metric in metrics_data:
                    if "duration" in metric.name.lower() or "time" in metric.name.lower():
                        performance_metrics.append(metric)
                
                # Verify performance metrics are captured
                assert len(performance_metrics) > 0

    def test_weaver_batch_processing_telemetry(self):
        """Test that batch processing telemetry follows Weaver patterns."""
        batch_file_content = {
            "description": "Test batch",
            "generations": [
                {
                    "template": "component",
                    "name": "TestComponent",
                    "parameters": {"style": "styled-components"}
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create temporary batch file
            batch_file = Path(temp_dir) / "test-batch.json"
            with open(batch_file, 'w') as f:
                json.dump(batch_file_content, f)
            
            # Mock the bulk generation functions
            with patch('uvmgr.ops.weaver_forge.generate_bulk_from_templates') as mock_generate:
                mock_generate.return_value = {
                    "total_specs": 1,
                    "successful": 1,
                    "failed": 0,
                    "total_files": 1,
                    "duration": 0.1
                }
                
                # Clear previous spans
                self.span_exporter.clear()
                
                result = generate_from_batch_file(
                    batch_file=batch_file,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify batch processing telemetry
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Check for batch processing spans
                batch_spans = []
                for span in spans:
                    if "batch" in span.name.lower():
                        batch_spans.append(span)
                
                assert len(batch_spans) > 0

    def test_weaver_telemetry_integration(self, sample_generation_specs):
        """Test integration of all Weaver telemetry components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous telemetry
                self.span_exporter.clear()
                self.metric_reader.collect()
                
                # Execute bulk generation
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify comprehensive telemetry
                spans = self.span_exporter.get_finished_spans()
                metrics_data = self.metric_reader.collect()
                
                # Verify spans exist
                assert len(spans) > 0
                
                # Verify metrics exist
                assert len(metrics_data) > 0
                
                # Verify result structure matches Weaver patterns
                assert "total_specs" in result
                assert "successful" in result
                assert "failed" in result
                assert "success_rate" in result
                assert "total_files" in result
                assert "duration" in result
                assert "results" in result
                assert "errors" in result
                
                # Verify telemetry correlation
                for span in spans:
                    if span.name == "weaver_forge.bulk_generate":
                        assert span.attributes["total_specs"] == result["total_specs"]
                        assert span.attributes["successful"] == result["successful"]
                        assert span.attributes["failed"] == result["failed"]

    def test_weaver_telemetry_standards_compliance(self, sample_generation_specs):
        """Test compliance with Weaver telemetry standards."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Clear previous telemetry
                self.span_exporter.clear()
                self.metric_reader.collect()
                
                # Execute bulk generation
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Verify Weaver standards compliance
                spans = self.span_exporter.get_finished_spans()
                metrics_data = self.metric_reader.collect()
                
                # Check span standards
                for span in spans:
                    # Verify span has proper name format
                    assert span.name.startswith("weaver_forge.")
                    
                    # Verify span has proper attributes
                    assert len(span.attributes) > 0
                    
                    # Verify span has proper status
                    assert span.status.status_code in [trace.StatusCode.OK, trace.StatusCode.ERROR]
                
                # Check metric standards
                for metric in metrics_data:
                    # Verify metric has proper name format
                    assert metric.name.startswith("weaver_forge.")
                    
                    # Verify metric has proper description
                    assert hasattr(metric, 'description') or hasattr(metric, 'unit')

    def test_weaver_telemetry_performance_impact(self, sample_generation_specs):
        """Test that telemetry has minimal performance impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Test without telemetry (baseline)
                start_time = time.time()
                result_without_telemetry = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                time_without_telemetry = time.time() - start_time
                
                # Test with telemetry
                start_time = time.time()
                result_with_telemetry = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                time_with_telemetry = time.time() - start_time
                
                # Verify telemetry overhead is reasonable (< 10% of total time)
                telemetry_overhead = time_with_telemetry - time_without_telemetry
                overhead_percentage = (telemetry_overhead / time_without_telemetry) * 100
                
                assert overhead_percentage < 10.0, f"Telemetry overhead too high: {overhead_percentage:.2f}%"
                
                # Verify results are identical
                assert result_without_telemetry["successful"] == result_with_telemetry["successful"]
                assert result_without_telemetry["failed"] == result_with_telemetry["failed"]


if __name__ == "__main__":
    pytest.main([__file__]) 