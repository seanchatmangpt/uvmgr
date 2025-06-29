"""
Tests for OpenTelemetry integration in DoD operations against Weaver semantic conventions.
Validates that all DoD operations emit proper telemetry with correct semantic conventions.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode
from typing import Dict, Any, List

from uvmgr.ops.dod import (
    create_exoskeleton,
    execute_complete_automation,
    validate_dod_criteria,
    generate_devops_pipeline,
    run_e2e_automation,
    analyze_project_status,
    generate_dod_report
)


class TestOtelWeaverIntegration:
    """Test OpenTelemetry integration with Weaver semantic conventions."""
    
    @pytest.fixture(autouse=True)
    def setup_telemetry(self):
        """Setup OpenTelemetry testing infrastructure."""
        # Store original provider to restore later
        original_provider = trace.get_tracer_provider()
        
        # Create in-memory span exporter for testing
        self.span_exporter = InMemorySpanExporter()
        
        # Setup tracer provider
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(self.span_exporter)
        tracer_provider.add_span_processor(processor)
        
        # Set the tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Clear any existing spans
        self.span_exporter.clear()
        
        yield
        
        # Cleanup after test
        self.span_exporter.clear()
        
        # Restore original provider
        if hasattr(original_provider, '__class__'):
            trace.set_tracer_provider(original_provider)
    
    def get_spans(self) -> List:
        """Get all collected spans."""
        return self.span_exporter.get_finished_spans()
    
    def get_span_by_name(self, name: str):
        """Get span by name."""
        spans = self.get_spans()
        for span in spans:
            if span.name == name:
                return span
        return None
    
    def assert_span_attributes(self, span, expected_attributes: Dict[str, Any]):
        """Assert that span has expected attributes."""
        if span is None:
            pytest.fail("Span not found")
        
        span_attributes = dict(span.attributes) if span.attributes else {}
        
        for key, expected_value in expected_attributes.items():
            assert key in span_attributes, f"Attribute '{key}' not found in span"
            actual_value = span_attributes[key]
            assert actual_value == expected_value, f"Attribute '{key}': expected {expected_value}, got {actual_value}"
    
    def assert_weaver_semantic_conventions(self, span, operation_type: str):
        """Assert that span follows Weaver semantic conventions."""
        assert span is not None
        
        # Check span name format follows Weaver conventions
        assert span.name.startswith("dod."), f"Span name should start with 'dod.': {span.name}"
        
        # Check operation type attribute
        span_attributes = dict(span.attributes) if span.attributes else {}
        
        # Weaver semantic conventions for DoD operations
        weaver_attributes = [
            "project.path",  # Project context
            f"dod.{operation_type}",  # Operation-specific attribute
        ]
        
        for attr in weaver_attributes:
            if attr.startswith("dod."):
                # Check that at least one DoD-specific attribute exists
                dod_attrs = [key for key in span_attributes.keys() if key.startswith("dod.")]
                assert len(dod_attrs) > 0, f"No DoD-specific attributes found in span: {list(span_attributes.keys())}"
                break
    
    def test_create_exoskeleton_telemetry(self):
        """Test that create_exoskeleton emits proper telemetry."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {
                "success": True,
                "files_created": [{"path": ".uvmgr/dod.yaml"}],
                "workflows_created": ["dod-validation"],
                "ai_integrations": ["code-review"]
            }
            
            result = create_exoskeleton(
                project_path,
                template="standard",
                force=True,
                preview=False
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.create_exoskeleton")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "create_exoskeleton")
            
            # Check expected attributes
            expected_attributes = {
                "dod.template": "standard",
                "dod.force": True,
                "dod.preview": False,
                "project.path": str(project_path),
                "dod.files_created": 1,
                "dod.workflows_created": 1,
                "dod.ai_integrations": 1
            }
            self.assert_span_attributes(span, expected_attributes)
            
            # Check span status (successful spans may be UNSET or OK)
            assert span.status.status_code in [StatusCode.UNSET, StatusCode.OK]
    
    def test_create_exoskeleton_telemetry_failure(self):
        """Test telemetry on create_exoskeleton failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.side_effect = Exception("Test error")
            
            result = create_exoskeleton(project_path)
            
            # Verify error telemetry
            span = self.get_span_by_name("dod.create_exoskeleton")
            assert span is not None
            
            # Check that error was recorded
            assert span.status.status_code == StatusCode.ERROR
            
            # Check that exception was recorded
            events = span.events
            error_events = [event for event in events if event.name == "exception"]
            assert len(error_events) > 0, "No exception event recorded"
    
    def test_execute_complete_automation_telemetry(self):
        """Test telemetry for complete automation execution."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "criteria_results": {
                    "testing": {"passed": True, "score": 95.0},
                    "security": {"passed": True, "score": 88.0}
                }
            }
            
            result = execute_complete_automation(
                project_path=project_path,
                environment="production",
                skip_tests=False,
                skip_security=False,
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.execute_complete_automation")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "execute_complete_automation")
            
            # Check expected attributes
            expected_attributes = {
                "dod.environment": "production",
                "dod.skip_tests": False,
                "dod.skip_security": False,
                "dod.auto_fix": True,
                "dod.parallel": True,
                "dod.ai_assist": True,
                "project.path": str(project_path),
                "dod.criteria_count": 7,  # All criteria
                "dod.criteria_passed": 2  # testing and security passed
            }
            self.assert_span_attributes(span, expected_attributes)
            
            # Check that success rate and execution time are recorded
            span_attributes = dict(span.attributes)
            assert "dod.success_rate" in span_attributes
            assert "dod.execution_time" in span_attributes
    
    def test_validate_dod_criteria_telemetry(self):
        """Test telemetry for DoD criteria validation."""
        project_path = Path("/test/project")
        criteria = ["testing", "security", "code_quality"]
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "criteria_scores": {
                    "testing": {"passed": True, "score": 95.0},
                    "security": {"passed": False, "score": 65.0},
                    "code_quality": {"passed": True, "score": 85.0}
                }
            }
            
            result = validate_dod_criteria(
                project_path=project_path,
                criteria=criteria,
                detailed=True,
                fix_suggestions=True
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.validate_dod_criteria")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "validate_dod_criteria")
            
            # Check expected attributes
            expected_attributes = {
                "dod.detailed": True,
                "dod.fix_suggestions": True,
                "project.path": str(project_path),
                "dod.criteria_count": 3
            }
            self.assert_span_attributes(span, expected_attributes)
            
            # Check calculated scores are recorded
            span_attributes = dict(span.attributes)
            assert "dod.overall_score" in span_attributes
            assert "dod.critical_score" in span_attributes
            assert "dod.important_score" in span_attributes
    
    def test_generate_devops_pipeline_telemetry(self):
        """Test telemetry for DevOps pipeline generation."""
        project_path = Path("/test/project")
        environments = ["dev", "staging", "production"]
        features = ["testing", "security", "deployment"]
        
        with patch("uvmgr.ops.dod.generate_pipeline_files") as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "files_created": [".github/workflows/dod.yml"],
                "features_enabled": features,
                "environments_configured": environments
            }
            
            result = generate_devops_pipeline(
                project_path=project_path,
                provider="github-actions",
                environments=environments,
                features=features,
                template="enterprise"
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.generate_devops_pipeline")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "generate_devops_pipeline")
            
            # Check expected attributes
            expected_attributes = {
                "dod.provider": "github-actions",
                "dod.template": "enterprise",
                "dod.environments": str(environments),
                "dod.features": str(features),
                "project.path": str(project_path),
                "dod.files_created": 1,
                "dod.features_enabled": 3,
                "dod.environments_configured": 3
            }
            self.assert_span_attributes(span, expected_attributes)
    
    def test_run_e2e_automation_telemetry(self):
        """Test telemetry for E2E automation."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.run_e2e_tests") as mock_run_tests:
            mock_run_tests.return_value = {
                "success": True,
                "test_suites": {
                    "browser_tests": {"total": 20, "passed": 18, "failed": 2},
                    "api_tests": {"total": 15, "passed": 15, "failed": 0}
                }
            }
            
            result = run_e2e_automation(
                project_path=project_path,
                environment="staging",
                parallel=True,
                headless=True,
                record_video=False,
                generate_report=True
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.run_e2e_automation")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "run_e2e_automation")
            
            # Check expected attributes
            expected_attributes = {
                "dod.environment": "staging",
                "dod.parallel": True,
                "dod.headless": True,
                "dod.record_video": False,
                "dod.generate_report": True,
                "project.path": str(project_path),
                "dod.total_tests": 35,  # 20 + 15
                "dod.passed_tests": 33,  # 18 + 15
            }
            self.assert_span_attributes(span, expected_attributes)
            
            # Check calculated metrics
            span_attributes = dict(span.attributes)
            assert "dod.success_rate" in span_attributes
            assert "dod.execution_time" in span_attributes
            
            # Verify success rate calculation
            expected_success_rate = 33 / 35
            actual_success_rate = span_attributes["dod.success_rate"]
            assert abs(actual_success_rate - expected_success_rate) < 0.01
    
    def test_analyze_project_status_telemetry(self):
        """Test telemetry for project status analysis."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.analyze_project_health") as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "dod_status": {"overall_score": 85.0},
                "automation_health": {"score": 80.0},
                "security_posture": {"score": 90.0},
                "code_quality": {"score": 88.0}
            }
            
            result = analyze_project_status(
                project_path=project_path,
                detailed=True,
                suggestions=True
            )
            
            # Verify telemetry
            span = self.get_span_by_name("dod.analyze_project_status")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "analyze_project_status")
            
            # Check expected attributes
            expected_attributes = {
                "dod.detailed": True,
                "dod.suggestions": True,
                "project.path": str(project_path)
            }
            self.assert_span_attributes(span, expected_attributes)
            
            # Check health score is recorded
            span_attributes = dict(span.attributes)
            assert "dod.health_score" in span_attributes
    
    def test_generate_dod_report_telemetry(self):
        """Test telemetry for DoD report generation."""
        project_path = Path("/test/project")
        automation_result = {
            "overall_success_rate": 85.5,
            "criteria_results": {}
        }
        
        with patch("uvmgr.ops.dod.create_automation_report") as mock_create_report:
            mock_create_report.return_value = {
                "success": True,
                "formats_generated": ["json", "markdown"]
            }
            
            result = generate_dod_report(project_path, automation_result)
            
            # Verify telemetry
            span = self.get_span_by_name("dod.generate_dod_report")
            assert span is not None
            
            # Check Weaver semantic conventions
            self.assert_weaver_semantic_conventions(span, "generate_dod_report")
            
            # Check expected attributes
            expected_attributes = {
                "project.path": str(project_path),
                "dod.success_rate": 85.5,
                "dod.report_generated": True,
                "dod.report_formats": 2
            }
            self.assert_span_attributes(span, expected_attributes)


class TestWeaverSemanticConventions:
    """Test adherence to Weaver semantic conventions."""
    
    def test_span_naming_conventions(self):
        """Test that spans follow Weaver naming conventions."""
        project_path = Path("/test/project")
        
        # Setup telemetry capture
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Execute operations to generate spans
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files"):
            create_exoskeleton(project_path)
        
        with patch("uvmgr.ops.dod.execute_automation_workflow"):
            execute_complete_automation(project_path)
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime"):
            validate_dod_criteria(project_path)
        
        spans = span_exporter.get_finished_spans()
        
        # Verify all spans follow naming convention
        for span in spans:
            assert span.name.startswith("dod."), f"Span name should start with 'dod.': {span.name}"
            
            # Verify span name format: dod.<operation>
            name_parts = span.name.split(".")
            assert len(name_parts) == 2, f"Span name should have format 'dod.<operation>': {span.name}"
            assert name_parts[0] == "dod", f"First part should be 'dod': {span.name}"
            assert len(name_parts[1]) > 0, f"Operation name should not be empty: {span.name}"
    
    def test_attribute_naming_conventions(self):
        """Test that attributes follow Weaver naming conventions."""
        project_path = Path("/test/project")
        
        # Setup telemetry capture
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Execute operation to generate span with attributes
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            
            create_exoskeleton(
                project_path,
                template="standard",
                force=True,
                preview=False
            )
        
        spans = span_exporter.get_finished_spans()
        assert len(spans) > 0, "No spans generated"
        
        span = spans[0]
        span_attributes = dict(span.attributes) if span.attributes else {}
        
        # Check attribute naming conventions
        for attr_name in span_attributes.keys():
            # Should follow dot notation for namespaces
            assert "." in attr_name, f"Attribute should use dot notation: {attr_name}"
            
            # DoD-specific attributes should start with 'dod.'
            # Project attributes should start with 'project.'
            namespace = attr_name.split(".")[0]
            assert namespace in ["dod", "project"], f"Unknown attribute namespace: {namespace}"
    
    def test_span_context_propagation(self):
        """Test that span context is properly propagated."""
        project_path = Path("/test/project")
        
        # Setup telemetry capture
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Create a parent span to test context propagation
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test.parent_operation") as parent_span:
            with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
                mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
                
                # Execute DoD operation within parent span context
                create_exoskeleton(project_path)
        
        spans = span_exporter.get_finished_spans()
        
        # Find parent and child spans
        parent_span = None
        dod_span = None
        
        for span in spans:
            if span.name == "test.parent_operation":
                parent_span = span
            elif span.name == "dod.create_exoskeleton":
                dod_span = span
        
        assert parent_span is not None, "Parent span not found"
        assert dod_span is not None, "DoD span not found"
        
        # Verify span relationship
        assert dod_span.parent is not None, "DoD span should have a parent"
        assert dod_span.parent.span_id == parent_span.context.span_id, "DoD span should be child of parent span"
    
    def test_error_telemetry_conventions(self):
        """Test that error telemetry follows Weaver conventions."""
        project_path = Path("/test/project")
        
        # Setup telemetry capture
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Execute operation that will fail
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.side_effect = Exception("Test error for telemetry")
            
            result = create_exoskeleton(project_path)
        
        spans = span_exporter.get_finished_spans()
        assert len(spans) > 0, "No spans generated"
        
        span = spans[0]
        
        # Check error status
        assert span.status.status_code == StatusCode.ERROR, "Span should have error status"
        
        # Check exception event
        events = span.events
        exception_events = [event for event in events if event.name == "exception"]
        assert len(exception_events) > 0, "Should have exception event"
        
        # Check exception event attributes
        exception_event = exception_events[0]
        event_attributes = dict(exception_event.attributes) if exception_event.attributes else {}
        
        # Should have standard exception attributes
        expected_exception_attrs = ["exception.type", "exception.message"]
        for attr in expected_exception_attrs:
            assert any(attr in key for key in event_attributes.keys()), f"Missing exception attribute: {attr}"


class TestTelemetryPerformanceMetrics:
    """Test telemetry performance and efficiency metrics."""
    
    def test_span_attribute_efficiency(self):
        """Test that spans don't have excessive attributes."""
        project_path = Path("/test/project")
        
        # Setup telemetry capture
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        # Execute operations
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            create_exoskeleton(project_path)
        
        spans = span_exporter.get_finished_spans()
        
        for span in spans:
            span_attributes = dict(span.attributes) if span.attributes else {}
            
            # Should not have excessive attributes (performance consideration)
            assert len(span_attributes) <= 20, f"Span has too many attributes ({len(span_attributes)}): {span.name}"
            
            # Attribute values should not be excessively large
            for key, value in span_attributes.items():
                if isinstance(value, str):
                    assert len(value) <= 1000, f"Attribute value too large: {key}={value[:100]}..."
    
    def test_telemetry_overhead_minimal(self):
        """Test that telemetry overhead is minimal."""
        import time
        project_path = Path("/test/project")
        
        # Measure execution time with telemetry
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            
            start_time = time.time()
            create_exoskeleton(project_path)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
        # Telemetry should add minimal overhead
        assert execution_time < 1.0, f"Execution time too high with telemetry: {execution_time}s"


class TestDodTelemetryIntegration:
    """Integration tests for DoD telemetry across operations."""
    
    @pytest.fixture(autouse=True)
    def setup_telemetry(self):
        """Setup telemetry for integration tests."""
        self.span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        processor = SimpleSpanProcessor(self.span_exporter)
        tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(tracer_provider)
        
        yield
        
        self.span_exporter.clear()
    
    def test_complete_dod_workflow_telemetry(self):
        """Test telemetry across complete DoD workflow."""
        project_path = Path("/test/integration-project")
        
        # Mock all runtime dependencies
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init, \
             patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute, \
             patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            
            # Setup mocks
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            mock_validate.return_value = {"success": True, "criteria_scores": {}}
            
            # Execute complete workflow
            create_exoskeleton(project_path, template="enterprise")
            execute_complete_automation(project_path, environment="production")
            validate_dod_criteria(project_path, criteria=["testing", "security"])
            
        # Verify telemetry spans
        spans = self.span_exporter.get_finished_spans()
        span_names = [span.name for span in spans]
        
        expected_spans = [
            "dod.create_exoskeleton",
            "dod.execute_complete_automation", 
            "dod.validate_dod_criteria"
        ]
        
        for expected_span in expected_spans:
            assert expected_span in span_names, f"Missing expected span: {expected_span}"
        
        # Verify all spans have required attributes
        for span in spans:
            span_attributes = dict(span.attributes) if span.attributes else {}
            
            # All DoD spans should have project.path
            assert "project.path" in span_attributes, f"Missing project.path in span: {span.name}"
            assert span_attributes["project.path"] == str(project_path)
    
    def test_telemetry_trace_correlation(self):
        """Test that related DoD operations can be correlated via traces."""
        project_path = Path("/test/correlation-project")
        
        # Create a correlation ID for the workflow
        correlation_id = "dod-workflow-12345"
        
        # Execute operations with correlation context
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("dod.workflow", attributes={"dod.correlation_id": correlation_id}):
            with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init, \
                 patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
                
                mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
                mock_execute.return_value = {"success": True, "criteria_results": {}}
                
                create_exoskeleton(project_path)
                execute_complete_automation(project_path)
        
        spans = self.span_exporter.get_finished_spans()
        
        # Find workflow span
        workflow_span = None
        child_spans = []
        
        for span in spans:
            if span.name == "dod.workflow":
                workflow_span = span
            elif span.name.startswith("dod."):
                child_spans.append(span)
        
        assert workflow_span is not None, "Workflow span not found"
        assert len(child_spans) >= 2, "Not enough child spans found"
        
        # Verify all child spans have the same trace ID
        for child_span in child_spans:
            assert child_span.context.trace_id == workflow_span.context.trace_id, \
                f"Child span has different trace ID: {child_span.name}"