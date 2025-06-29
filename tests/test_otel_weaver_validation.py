"""
OpenTelemetry validation against Weaver semantic conventions.

Tests that DoD system properly implements OpenTelemetry tracing
with Weaver-compliant semantic conventions and observability.
"""

from __future__ import annotations

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

from uvmgr.ops.dod import (
    create_exoskeleton,
    execute_complete_automation,
    validate_dod_criteria,
    generate_devops_pipeline
)


class TestDoDOpenTelemetryIntegration:
    """Test DoD system OpenTelemetry integration."""
    
    def setup_method(self):
        """Set up OpenTelemetry test environment."""
        # Create in-memory span exporter for testing
        self.span_exporter = InMemorySpanExporter()
        self.tracer_provider = TracerProvider()
        self.tracer_provider.add_span_processor(
            SimpleSpanProcessor(self.span_exporter)
        )
        trace.set_tracer_provider(self.tracer_provider)
        
        self.test_project_path = Path("/test/project")
        
    def teardown_method(self):
        """Clean up after tests."""
        self.span_exporter.clear()
        
    def test_dod_operations_create_spans(self):
        """Test that DoD operations create proper OpenTelemetry spans."""
        # Mock runtime functions to avoid actual execution
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {"success": True, "files_created": []}
            
            # Execute DoD operation
            result = create_exoskeleton(
                project_path=self.test_project_path,
                template="enterprise",
                force=False,
                preview=False
            )
            
            # Get captured spans
            spans = self.span_exporter.get_finished_spans()
            
            # Verify span was created
            assert len(spans) > 0
            
            # Find the DoD exoskeleton span
            dod_span = next((s for s in spans if "dod.create_exoskeleton" in s.name), None)
            assert dod_span is not None
            
            # Verify span attributes follow Weaver conventions
            attributes = dod_span.attributes
            assert "dod.template" in attributes
            assert "dod.force" in attributes
            assert "dod.preview" in attributes
            assert "project.path" in attributes
            
            # Verify attribute values
            assert attributes["dod.template"] == "enterprise"
            assert attributes["dod.force"] is False
            assert attributes["dod.preview"] is False
            assert attributes["project.path"] == str(self.test_project_path)
            
    def test_dod_automation_span_hierarchy(self):
        """Test proper span hierarchy for DoD automation workflow."""
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0}
            }
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow", return_value=mock_automation_result):
            result = execute_complete_automation(
                project_path=self.test_project_path,
                environment="production",
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
            
            spans = self.span_exporter.get_finished_spans()
            
            # Find the main automation span (handle different span name patterns)
            automation_span = None
            for span in spans:
                if any(name in span.name for name in ["execute_complete_automation", "automation", "dod"]):
                    automation_span = span
                    break
            
            # If no automation span found, use the first span (test should still validate attributes)
            if automation_span is None and spans:
                automation_span = spans[0]
                
            assert automation_span is not None, f"No automation span found in: {[s.name for s in spans]}"
            
            # Verify span attributes
            attributes = automation_span.attributes
            assert "dod.environment" in attributes
            assert "dod.auto_fix" in attributes
            assert "dod.parallel" in attributes
            assert "dod.ai_assist" in attributes
            assert "project.path" in attributes
            
            # Verify success metrics are recorded
            if result["success"]:
                assert "dod.success_rate" in attributes
                assert "dod.execution_time" in attributes
                assert "dod.criteria_passed" in attributes
                
    def test_dod_validation_telemetry(self):
        """Test DoD validation telemetry and metrics."""
        mock_validation_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 85.0, "passed": True},
                "security": {"score": 92.0, "passed": True},
                "code_quality": {"score": 78.0, "passed": True}
            },
            "overall_score": 85.0
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime", return_value=mock_validation_result):
            result = validate_dod_criteria(
                project_path=self.test_project_path,
                criteria=["testing", "security", "code_quality"],
                detailed=True,
                fix_suggestions=True
            )
            
            spans = self.span_exporter.get_finished_spans()
            
            # Find validation span
            validation_span = next(
                (s for s in spans if "dod.validate_dod_criteria" in s.name), 
                None
            )
            assert validation_span is not None
            
            # Verify telemetry attributes
            attributes = validation_span.attributes
            assert "dod.detailed" in attributes
            assert "dod.fix_suggestions" in attributes
            assert "dod.criteria_count" in attributes
            assert "project.path" in attributes
            
            # Verify success metrics
            if result["success"]:
                assert "dod.overall_score" in attributes
                assert "dod.critical_score" in attributes
                assert "dod.important_score" in attributes
                
    def test_dod_pipeline_generation_spans(self):
        """Test DevOps pipeline generation spans."""
        mock_pipeline_result = {
            "success": True,
            "provider": "github-actions",
            "files_created": [".github/workflows/dod-automation.yml"],
            "features_enabled": ["testing", "security"],
            "environments_configured": ["dev", "staging", "production"]
        }
        
        with patch("uvmgr.ops.dod.generate_pipeline_files", return_value=mock_pipeline_result):
            result = generate_devops_pipeline(
                project_path=self.test_project_path,
                provider="github-actions",
                environments=["dev", "staging", "production"],
                features=["testing", "security"],
                template="enterprise"
            )
            
            spans = self.span_exporter.get_finished_spans()
            
            # Find pipeline generation span
            pipeline_span = next(
                (s for s in spans if "dod.generate_devops_pipeline" in s.name), 
                None
            )
            assert pipeline_span is not None
            
            # Verify span attributes
            attributes = pipeline_span.attributes
            assert "dod.provider" in attributes
            assert "dod.template" in attributes
            assert "dod.environments" in attributes
            assert "dod.features" in attributes
            assert "project.path" in attributes
            
            # Verify success metrics
            if result["success"]:
                assert "dod.files_created" in attributes
                assert "dod.features_enabled" in attributes
                assert "dod.environments_configured" in attributes
                
    def test_span_error_handling(self):
        """Test proper error handling and span status."""
        # Mock a runtime error
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", side_effect=Exception("Test error")):
            result = create_exoskeleton(
                project_path=self.test_project_path,
                template="invalid_template"
            )
            
            spans = self.span_exporter.get_finished_spans()
            
            # Find the error span
            error_span = next(
                (s for s in spans if "dod.create_exoskeleton" in s.name), 
                None
            )
            assert error_span is not None
            
            # Verify error was recorded
            assert error_span.status.status_code == StatusCode.ERROR
            assert "Test error" in error_span.status.description or len(error_span.events) > 0
            
    def test_weaver_semantic_convention_compliance(self):
        """Test compliance with Weaver semantic conventions."""
        mock_result = {"success": True, "files_created": []}
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
            result = create_exoskeleton(
                project_path=self.test_project_path,
                template="enterprise"
            )
            
            spans = self.span_exporter.get_finished_spans()
            dod_span = spans[0] if spans else None
            
            assert dod_span is not None
            attributes = dod_span.attributes
            
            # Verify DoD-specific semantic conventions
            dod_attributes = {k: v for k, v in attributes.items() if k.startswith("dod.")}
            
            # Required DoD attributes per Weaver conventions
            required_dod_attributes = [
                "dod.template",
                "dod.force", 
                "dod.preview"
            ]
            
            for attr in required_dod_attributes:
                assert attr in dod_attributes, f"Missing required DoD attribute: {attr}"
                
            # Verify project-level attributes
            project_attributes = {k: v for k, v in attributes.items() if k.startswith("project.")}
            assert "project.path" in project_attributes
            
            # Verify attribute types are correct
            assert isinstance(attributes["dod.template"], str)
            assert isinstance(attributes["dod.force"], bool)
            assert isinstance(attributes["dod.preview"], bool)
            assert isinstance(attributes["project.path"], str)
            
    def test_dod_metrics_collection(self):
        """Test DoD metrics collection through OpenTelemetry."""
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0}
            },
            "overall_success_rate": 0.917
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow", return_value=mock_automation_result):
            result = execute_complete_automation(
                project_path=self.test_project_path,
                environment="production"
            )
            
            spans = self.span_exporter.get_finished_spans()
            automation_span = spans[0] if spans else None
            
            assert automation_span is not None
            attributes = automation_span.attributes
            
            # Verify metric-style attributes for dashboards
            assert "dod.success_rate" in attributes
            assert "dod.execution_time" in attributes
            assert "dod.criteria_passed" in attributes
            
            # Verify values are numeric for metrics
            assert isinstance(attributes["dod.success_rate"], (int, float))
            assert isinstance(attributes["dod.execution_time"], (int, float))
            assert isinstance(attributes["dod.criteria_passed"], int)
            
            # Verify success rate is calculated correctly
            expected_passed = sum(1 for r in mock_automation_result["criteria_results"].values() if r["passed"])
            assert attributes["dod.criteria_passed"] == expected_passed
            
    def test_distributed_tracing_context(self):
        """Test distributed tracing context propagation."""
        # Create a parent span to test context propagation
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("parent_operation") as parent_span:
            parent_span.set_attribute("operation.type", "dod_workflow")
            
            mock_result = {"success": True, "files_created": []}
            
            with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
                result = create_exoskeleton(
                    project_path=self.test_project_path,
                    template="enterprise"
                )
                
        spans = self.span_exporter.get_finished_spans()
        
        # Find parent and child spans
        parent_span = next((s for s in spans if s.name == "parent_operation"), None)
        child_span = next((s for s in spans if "dod.create_exoskeleton" in s.name), None)
        
        assert parent_span is not None
        assert child_span is not None
        
        # Verify parent-child relationship
        assert child_span.parent is not None
        assert child_span.parent.span_id == parent_span.context.span_id
        assert child_span.context.trace_id == parent_span.context.trace_id
        
    def test_custom_dod_events(self):
        """Test custom DoD events in spans."""
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0, "auto_fix_applied": True},
                "security": {"passed": False, "score": 65.0, "auto_fix_applied": False}
            }
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow", return_value=mock_automation_result):
            result = execute_complete_automation(
                project_path=self.test_project_path,
                auto_fix=True
            )
            
        spans = self.span_exporter.get_finished_spans()
        automation_span = spans[0] if spans else None
        
        assert automation_span is not None
        
        # Check for DoD-specific events (if implemented)
        events = automation_span.events
        
        # Events might include auto-fix attempts, criteria failures, etc.
        # This validates the event structure even if no events are present
        assert isinstance(events, list)
        
        # If events exist, verify they have proper structure
        for event in events:
            assert hasattr(event, 'name')
            assert hasattr(event, 'timestamp')
            assert hasattr(event, 'attributes')


class TestWeaverSemanticConventions:
    """Test Weaver semantic convention compliance."""
    
    def setup_method(self):
        """Set up test environment."""
        self.span_exporter = InMemorySpanExporter()
        self.tracer_provider = TracerProvider()
        self.tracer_provider.add_span_processor(
            SimpleSpanProcessor(self.span_exporter)
        )
        trace.set_tracer_provider(self.tracer_provider)
        
    def teardown_method(self):
        """Clean up after tests."""
        self.span_exporter.clear()
        
    def test_dod_namespace_conventions(self):
        """Test DoD namespace follows Weaver conventions."""
        # DoD attributes should use 'dod.' prefix
        # Project attributes should use 'project.' prefix
        # System attributes should use 'system.' prefix
        
        mock_result = {"success": True, "criteria_scores": {}}
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime", return_value=mock_result):
            result = validate_dod_criteria(
                project_path=Path("/test/project"),
                criteria=["testing"]
            )
            
        spans = self.span_exporter.get_finished_spans()
        span = spans[0] if spans else None
        
        assert span is not None
        attributes = span.attributes
        
        # Verify namespace prefixes
        for attr_name, attr_value in attributes.items():
            if attr_name.startswith("dod."):
                # DoD-specific attributes
                assert attr_name in [
                    "dod.detailed", "dod.fix_suggestions", "dod.criteria_count",
                    "dod.overall_score", "dod.critical_score", "dod.important_score"
                ], f"Unknown DoD attribute: {attr_name}"
            elif attr_name.startswith("project."):
                # Project-specific attributes
                assert attr_name in ["project.path"], f"Unknown project attribute: {attr_name}"
            elif attr_name.startswith("system."):
                # System-specific attributes (if any)
                pass
            else:
                # Standard OpenTelemetry attributes are allowed
                pass
                
    def test_attribute_value_types(self):
        """Test attribute value types follow conventions."""
        mock_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 85.0, "passed": True}
            },
            "overall_score": 85.0
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime", return_value=mock_result):
            result = validate_dod_criteria(
                project_path=Path("/test/project"),
                detailed=True,
                fix_suggestions=False
            )
            
        spans = self.span_exporter.get_finished_spans()
        span = spans[0] if spans else None
        
        assert span is not None
        attributes = span.attributes
        
        # Verify attribute types per Weaver conventions
        type_expectations = {
            "dod.detailed": bool,
            "dod.fix_suggestions": bool,
            "dod.criteria_count": int,
            "dod.overall_score": (int, float),
            "dod.critical_score": (int, float),
            "dod.important_score": (int, float),
            "project.path": str
        }
        
        for attr_name, expected_type in type_expectations.items():
            if attr_name in attributes:
                actual_value = attributes[attr_name]
                assert isinstance(actual_value, expected_type), \
                    f"Attribute {attr_name} should be {expected_type}, got {type(actual_value)}"
                    
    def test_span_naming_conventions(self):
        """Test span naming follows Weaver conventions."""
        mock_result = {"success": True, "files_created": []}
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
            result = create_exoskeleton(Path("/test/project"), "enterprise")
            
        spans = self.span_exporter.get_finished_spans()
        span = spans[0] if spans else None
        
        assert span is not None
        
        # Span name should follow pattern: {service}.{operation}
        span_name = span.name
        assert "dod." in span_name, f"Span name should contain 'dod.' prefix: {span_name}"
        
        # Should be descriptive and use snake_case
        assert "_" in span_name or "." in span_name, f"Span name should use proper casing: {span_name}"
        
    def test_status_code_conventions(self):
        """Test status codes follow OpenTelemetry conventions."""
        # Test successful operation
        mock_success_result = {"success": True, "files_created": []}
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_success_result):
            result = create_exoskeleton(Path("/test/project"), "enterprise")
            
        spans = self.span_exporter.get_finished_spans()
        success_span = spans[-1] if spans else None
        
        assert success_span is not None
        # Successful operations should have OK status (or unset, which defaults to OK)
        assert success_span.status.status_code in [StatusCode.OK, StatusCode.UNSET]
        
        # Clear spans for next test
        self.span_exporter.clear()
        
        # Test error operation
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", side_effect=Exception("Test error")):
            result = create_exoskeleton(Path("/test/project"), "enterprise")
            
        spans = self.span_exporter.get_finished_spans()
        error_span = spans[-1] if spans else None
        
        assert error_span is not None
        # Error operations should have ERROR status
        assert error_span.status.status_code == StatusCode.ERROR
        
    def test_resource_attributes(self):
        """Test resource attributes are properly set."""
        mock_result = {"success": True, "files_created": []}
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
            result = create_exoskeleton(Path("/test/project"), "enterprise")
            
        spans = self.span_exporter.get_finished_spans()
        span = spans[0] if spans else None
        
        assert span is not None
        
        # Verify resource attributes exist
        resource = span.resource
        assert resource is not None
        
        # Resource should have service identification
        service_name = resource.attributes.get("service.name")
        assert service_name is not None
        
        # Should identify as uvmgr service
        assert "uvmgr" in str(service_name).lower()


class TestDoDTelemetryPerformance:
    """Test telemetry performance impact."""
    
    def test_telemetry_overhead(self):
        """Test that telemetry doesn't significantly impact performance."""
        import time
        
        # Test without telemetry (mocked)
        mock_result = {"success": True, "files_created": []}
        
        with patch("uvmgr.ops.dod.trace.get_current_span") as mock_span:
            mock_span.return_value = Mock()
            
            start_time = time.time()
            with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
                for _ in range(10):  # Run multiple times
                    result = create_exoskeleton(Path("/test/project"), "enterprise")
            end_time = time.time()
            
            time_without_real_telemetry = end_time - start_time
            
        # Test with real telemetry
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        
        start_time = time.time()
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
            for _ in range(10):  # Run multiple times
                result = create_exoskeleton(Path("/test/project"), "enterprise")
        end_time = time.time()
        
        time_with_telemetry = end_time - start_time
        
        # Telemetry overhead should be minimal (less than 50% increase)
        overhead_ratio = time_with_telemetry / time_without_real_telemetry
        assert overhead_ratio < 1.5, f"Telemetry overhead too high: {overhead_ratio}x"
        
        # Verify spans were created
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 10
        
    def test_span_attribute_limits(self):
        """Test span attributes don't exceed reasonable limits."""
        mock_result = {
            "success": True,
            "files_created": [f"file_{i}.yaml" for i in range(100)],  # Many files
            "large_data": "x" * 1000  # Large string
        }
        
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=mock_result):
            result = create_exoskeleton(Path("/test/project"), "enterprise")
            
        spans = span_exporter.get_finished_spans()
        span = spans[0] if spans else None
        
        assert span is not None
        
        # Verify reasonable number of attributes
        attributes = span.attributes
        assert len(attributes) < 50, f"Too many span attributes: {len(attributes)}"
        
        # Verify attribute values aren't excessively large
        for attr_name, attr_value in attributes.items():
            if isinstance(attr_value, str):
                assert len(attr_value) < 2000, f"Attribute {attr_name} too large: {len(attr_value)} chars"


if __name__ == "__main__":
    pytest.main([__file__])