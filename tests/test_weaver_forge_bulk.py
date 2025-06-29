"""
Unit tests for Weaver Forge bulk generation functionality.

This module provides comprehensive testing for Weaver Forge's bulk generation
capabilities, including telemetry validation to ensure it matches Weaver standards.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import pytest
import yaml
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from uvmgr.ops.weaver_forge import (
    generate_bulk_from_templates,
    generate_bulk_scaffolds,
    generate_from_batch_file,
    create_bulk_template,
    validate_bulk_templates,
    WeaverForgeError,
    TemplateNotFoundError
)
from uvmgr.core.telemetry import span, metric_counter, metric_histogram


class TestWeaverForgeBulkGeneration:
    """Test suite for Weaver Forge bulk generation functionality."""

    @pytest.fixture(autouse=True)
    def setup_telemetry(self):
        """Setup telemetry for testing."""
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
                "name": "UserProfile",
                "parameters": {
                    "style": "styled-components",
                    "typescript": True,
                    "props": ["name", "email", "avatar"]
                },
                "subdir": "components"
            },
            {
                "template": "component",
                "name": "ProductCard",
                "parameters": {
                    "style": "css-modules",
                    "typescript": True,
                    "props": ["title", "price", "image"]
                },
                "subdir": "components"
            },
            {
                "template": "api",
                "name": "users",
                "parameters": {
                    "framework": "express",
                    "validation": True,
                    "authentication": True
                },
                "subdir": "api"
            }
        ]

    @pytest.fixture
    def sample_scaffold_specs(self) -> List[Dict[str, Any]]:
        """Sample scaffold specifications for testing."""
        return [
            {
                "type": "react-app",
                "name": "frontend",
                "parameters": {
                    "typescript": True,
                    "testing": "jest",
                    "styling": "styled-components"
                },
                "subdir": "apps"
            },
            {
                "type": "node-api",
                "name": "backend",
                "parameters": {
                    "framework": "express",
                    "database": "postgres",
                    "authentication": "jwt"
                },
                "subdir": "apps"
            }
        ]

    @pytest.fixture
    def sample_batch_file(self) -> Dict[str, Any]:
        """Sample batch file content for testing."""
        return {
            "description": "Test batch specification",
            "version": "1.0.0",
            "generations": [
                {
                    "template": "component",
                    "name": "TestComponent",
                    "parameters": {
                        "style": "styled-components",
                        "typescript": True
                    }
                }
            ],
            "scaffolds": [
                {
                    "type": "react-app",
                    "name": "test-app",
                    "parameters": {
                        "typescript": True,
                        "testing": "jest"
                    }
                }
            ]
        }

    def test_generate_bulk_from_templates_success(self, sample_generation_specs):
        """Test successful bulk generation from templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["total_specs"] == 3
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert result["success_rate"] == 100.0
                assert result["total_files"] == 3
                assert result["duration"] > 0
                assert result["parallel"] is False
                assert result["dry_run"] is False
                assert len(result["results"]) == 3
                assert len(result["errors"]) == 0
                
                # Verify generate_from_template was called for each spec
                assert mock_generate.call_count == 3

    def test_generate_bulk_from_templates_with_errors(self, sample_generation_specs):
        """Test bulk generation with some errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function to simulate errors
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                # First call succeeds, second fails, third succeeds
                mock_generate.side_effect = [
                    {"success": True, "files": [{"path": "test1.tsx", "size": 100, "type": "created"}], "duration": 0.1},
                    Exception("Template not found"),
                    {"success": True, "files": [{"path": "test3.tsx", "size": 100, "type": "created"}], "duration": 0.1}
                ]
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["total_specs"] == 3
                assert result["successful"] == 2
                assert result["failed"] == 1
                assert result["success_rate"] == 66.7
                assert result["total_files"] == 2
                assert len(result["results"]) == 2
                assert len(result["errors"]) == 1
                assert "Template not found" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_generate_bulk_from_templates_parallel(self, sample_generation_specs):
        """Test parallel bulk generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=True,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["total_specs"] == 3
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert result["success_rate"] == 100.0
                assert result["total_files"] == 3
                assert result["parallel"] is True
                assert len(result["results"]) == 3
                assert len(result["errors"]) == 0

    def test_generate_bulk_from_templates_dry_run(self, sample_generation_specs):
        """Test bulk generation in dry run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "would_create"}],
                    "duration": 0.1
                }
                
                result = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=True
                )
                
                # Validate result structure
                assert result["total_specs"] == 3
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert result["success_rate"] == 100.0
                assert result["total_files"] == 3
                assert result["dry_run"] is True
                assert len(result["results"]) == 3
                assert len(result["errors"]) == 0

    def test_generate_bulk_scaffolds_success(self, sample_scaffold_specs):
        """Test successful bulk scaffold generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the create_scaffold function
            with patch('uvmgr.ops.weaver_forge.create_scaffold') as mock_scaffold:
                mock_scaffold.return_value = {
                    "success": True,
                    "files": [{"path": "package.json", "size": 200, "type": "created"}],
                    "duration": 0.2
                }
                
                result = generate_bulk_scaffolds(
                    scaffold_specs=sample_scaffold_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["total_scaffolds"] == 2
                assert result["successful"] == 2
                assert result["failed"] == 0
                assert result["success_rate"] == 100.0
                assert result["total_files"] == 2
                assert result["duration"] > 0
                assert result["parallel"] is False
                assert result["dry_run"] is False
                assert len(result["results"]) == 2
                assert len(result["errors"]) == 0
                
                # Verify create_scaffold was called for each spec
                assert mock_scaffold.call_count == 2

    def test_generate_from_batch_file_success(self, sample_batch_file):
        """Test successful batch file processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create temporary batch file
            batch_file = Path(temp_dir) / "batch-spec.json"
            with open(batch_file, 'w') as f:
                json.dump(sample_batch_file, f)
            
            # Mock the bulk generation functions
            with patch('uvmgr.ops.weaver_forge.generate_bulk_from_templates') as mock_generate, \
                 patch('uvmgr.ops.weaver_forge.generate_bulk_scaffolds') as mock_scaffold:
                
                mock_generate.return_value = {
                    "total_specs": 1,
                    "successful": 1,
                    "failed": 0,
                    "total_files": 1,
                    "duration": 0.1
                }
                
                mock_scaffold.return_value = {
                    "total_scaffolds": 1,
                    "successful": 1,
                    "failed": 0,
                    "total_files": 1,
                    "duration": 0.2
                }
                
                result = generate_from_batch_file(
                    batch_file=batch_file,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["batch_file"] == str(batch_file)
                assert result["generations"] == mock_generate.return_value
                assert result["scaffolds"] == mock_scaffold.return_value
                assert result["total_files"] == 2
                assert result["total_errors"] == 0
                assert result["total_duration"] > 0

    def test_generate_from_batch_file_yaml(self, sample_batch_file):
        """Test batch file processing with YAML format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create temporary batch file in YAML format
            batch_file = Path(temp_dir) / "batch-spec.yaml"
            with open(batch_file, 'w') as f:
                yaml.dump(sample_batch_file, f)
            
            # Mock the bulk generation functions
            with patch('uvmgr.ops.weaver_forge.generate_bulk_from_templates') as mock_generate, \
                 patch('uvmgr.ops.weaver_forge.generate_bulk_scaffolds') as mock_scaffold:
                
                mock_generate.return_value = {
                    "total_specs": 1,
                    "successful": 1,
                    "failed": 0,
                    "total_files": 1,
                    "duration": 0.1
                }
                
                mock_scaffold.return_value = {
                    "total_scaffolds": 1,
                    "successful": 1,
                    "failed": 0,
                    "total_files": 1,
                    "duration": 0.2
                }
                
                result = generate_from_batch_file(
                    batch_file=batch_file,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                
                # Validate result structure
                assert result["batch_file"] == str(batch_file)
                assert result["generations"] == mock_generate.return_value
                assert result["scaffolds"] == mock_scaffold.return_value

    def test_generate_from_batch_file_not_found(self):
        """Test batch file processing with non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            batch_file = Path(temp_dir) / "non-existent.json"
            
            with pytest.raises(WeaverForgeError, match="Batch file not found"):
                generate_from_batch_file(
                    batch_file=batch_file,
                    output_path=output_path
                )

    def test_generate_from_batch_file_invalid_json(self):
        """Test batch file processing with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create temporary batch file with invalid JSON
            batch_file = Path(temp_dir) / "invalid-batch.json"
            with open(batch_file, 'w') as f:
                f.write('{"invalid": json}')
            
            with pytest.raises(WeaverForgeError, match="Failed to load batch file"):
                generate_from_batch_file(
                    batch_file=batch_file,
                    output_path=output_path
                )

    def test_create_bulk_template_success(self):
        """Test successful bulk template creation."""
        template_specs = [
            {
                "name": "test-template-1",
                "type": "component",
                "description": "Test template 1"
            },
            {
                "name": "test-template-2",
                "type": "api",
                "description": "Test template 2"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Mock the create_template function
            with patch('uvmgr.ops.weaver_forge.create_template') as mock_create:
                mock_create.return_value = {
                    "name": "test-template",
                    "type": "component",
                    "description": "Test template",
                    "output_path": output_dir / "test-template",
                    "files": [{"path": "template.ejs.t", "size": 100, "type": "template"}],
                    "duration": 0.1
                }
                
                result = create_bulk_template(
                    template_specs=template_specs,
                    output_dir=output_dir,
                    interactive=False
                )
                
                # Validate result structure
                assert result["total_templates"] == 2
                assert result["successful"] == 2
                assert result["failed"] == 0
                assert result["success_rate"] == 100.0
                assert result["duration"] > 0
                assert len(result["results"]) == 2
                assert len(result["errors"]) == 0
                
                # Verify create_template was called for each spec
                assert mock_create.call_count == 2

    def test_validate_bulk_templates_success(self):
        """Test successful bulk template validation."""
        template_names = ["component", "api", "workflow"]
        
        # Mock the validation functions
        with patch('uvmgr.ops.weaver_forge._find_weaver_forge_path') as mock_find_path, \
             patch('uvmgr.ops.weaver_forge._validate_single_template') as mock_validate, \
             patch('uvmgr.ops.weaver_forge._apply_template_fixes') as mock_fix:
            
            # Mock weaver forge path
            mock_find_path.return_value = Path("/tmp/.weaver-forge")
            
            # Mock template validation
            mock_validate.return_value = [
                {"severity": "warning", "description": "Minor issue"}
            ]
            
            # Mock template fixes
            mock_fix.return_value = [{"fixed": True}]
            
            result = validate_bulk_templates(
                template_names=template_names,
                fix_issues=True,
                output_report=None
            )
            
            # Validate result structure
            assert result["total_templates"] == 3
            assert result["templates_with_issues"] == 3
            assert result["total_issues"] == 3
            assert result["fixed_issues"] == 3
            assert result["success_rate"] == 100.0
            assert result["duration"] > 0
            assert len(result["results"]) == 3

    def test_validate_bulk_templates_with_report(self):
        """Test bulk template validation with report generation."""
        template_names = ["component"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_report = Path(temp_dir) / "validation-report.json"
            
            # Mock the validation functions
            with patch('uvmgr.ops.weaver_forge._find_weaver_forge_path') as mock_find_path, \
                 patch('uvmgr.ops.weaver_forge._validate_single_template') as mock_validate:
                
                # Mock weaver forge path
                mock_find_path.return_value = Path("/tmp/.weaver-forge")
                
                # Mock template validation
                mock_validate.return_value = []
                
                result = validate_bulk_templates(
                    template_names=template_names,
                    fix_issues=False,
                    output_report=output_report
                )
                
                # Validate result structure
                assert result["total_templates"] == 1
                assert result["templates_with_issues"] == 0
                assert result["total_issues"] == 0
                assert result["fixed_issues"] == 0
                assert result["success_rate"] == 100.0
                
                # Verify report file was created
                assert output_report.exists()
                
                # Verify report content
                with open(output_report, 'r') as f:
                    report_data = json.load(f)
                    assert report_data["total_templates"] == 1
                    assert report_data["success_rate"] == 100.0

    def test_telemetry_span_creation(self, sample_generation_specs):
        """Test that telemetry spans are created correctly."""
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
                
                # Find the bulk generation span
                bulk_span = None
                for span in spans:
                    if span.name == "weaver_forge.bulk_generate":
                        bulk_span = span
                        break
                
                assert bulk_span is not None
                assert bulk_span.attributes["specs_count"] == 3
                assert bulk_span.attributes["parallel"] is False
                assert bulk_span.attributes["dry_run"] is False

    def test_telemetry_events_creation(self, sample_generation_specs):
        """Test that telemetry events are created correctly."""
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
                
                # Verify spans and events were created
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0
                
                # Check for events in spans
                events_found = False
                for span in spans:
                    if span.events:
                        events_found = True
                        for event in span.events:
                            if event.name == "weaver_forge.bulk_generated":
                                assert event.attributes["total_specs"] == 3
                                assert event.attributes["successful"] == 3
                                assert event.attributes["failed"] == 0
                                assert event.attributes["total_files"] == 3
                                break
                
                assert events_found

    def test_telemetry_metrics_collection(self, sample_generation_specs):
        """Test that metrics are collected correctly."""
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
                metrics = self.metric_reader.collect()
                
                # Verify metrics were collected
                assert len(metrics) > 0
                
                # Check for specific metric names
                metric_names = []
                for metric in metrics:
                    for point in metric.data.points:
                        metric_names.append(metric.name)
                
                # Note: Actual metric names depend on the implementation
                # This test verifies that metrics are being collected

    def test_error_handling_and_telemetry(self, sample_generation_specs):
        """Test error handling with telemetry integration."""
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
                assert result["total_specs"] == 3
                assert result["successful"] == 0
                assert result["failed"] == 3
                assert result["success_rate"] == 0.0
                assert len(result["errors"]) == 3
                assert all("Test error" in error for error in result["errors"])
                
                # Verify telemetry captured the errors
                spans = self.span_exporter.get_finished_spans()
                assert len(spans) > 0

    def test_performance_benchmarking(self, sample_generation_specs):
        """Test performance benchmarking capabilities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Mock the generate_from_template function
            with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "files": [{"path": "test.tsx", "size": 100, "type": "created"}],
                    "duration": 0.1
                }
                
                # Test sequential generation
                start_time = time.time()
                result_seq = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=False,
                    dry_run=False
                )
                seq_duration = time.time() - start_time
                
                # Test parallel generation
                start_time = time.time()
                result_par = generate_bulk_from_templates(
                    generation_specs=sample_generation_specs,
                    output_path=output_path,
                    parallel=True,
                    dry_run=False
                )
                par_duration = time.time() - start_time
                
                # Verify both approaches work
                assert result_seq["successful"] == 3
                assert result_par["successful"] == 3
                assert result_seq["success_rate"] == 100.0
                assert result_par["success_rate"] == 100.0
                
                # Performance metrics are captured in the result
                assert result_seq["duration"] > 0
                assert result_par["duration"] > 0

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with empty generation specs
        result = generate_bulk_from_templates(
            generation_specs=[],
            output_path=Path.cwd(),
            parallel=False,
            dry_run=False
        )
        
        assert result["total_specs"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0
        assert result["success_rate"] == 0.0
        assert result["total_files"] == 0
        
        # Test with None output path
        with patch('uvmgr.ops.weaver_forge.generate_from_template') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "files": [],
                "duration": 0.1
            }
            
            result = generate_bulk_from_templates(
                generation_specs=[{"template": "test", "name": "test"}],
                output_path=None,
                parallel=False,
                dry_run=False
            )
            
            assert result["total_specs"] == 1
            assert result["successful"] == 1

    def test_weaver_compatibility(self, sample_generation_specs):
        """Test compatibility with Weaver telemetry standards."""
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
                
                # Verify Weaver-compatible telemetry
                spans = self.span_exporter.get_finished_spans()
                
                # Check for Weaver-style span attributes
                weaver_attributes = [
                    "specs_count",
                    "parallel",
                    "dry_run",
                    "total_specs",
                    "successful",
                    "failed",
                    "total_files"
                ]
                
                for span in spans:
                    if span.name == "weaver_forge.bulk_generate":
                        for attr in weaver_attributes:
                            assert attr in span.attributes or f"weaver_forge.{attr}" in span.attributes
                
                # Verify result structure matches Weaver patterns
                assert "total_specs" in result
                assert "successful" in result
                assert "failed" in result
                assert "success_rate" in result
                assert "total_files" in result
                assert "duration" in result
                assert "results" in result
                assert "errors" in result


if __name__ == "__main__":
    pytest.main([__file__]) 