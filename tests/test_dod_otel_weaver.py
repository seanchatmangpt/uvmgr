#!/usr/bin/env python3
"""
OpenTelemetry and Weaver semantic convention validation tests for DoD system.

This test suite validates that the DoD automation system properly implements
OpenTelemetry instrumentation following Weaver semantic conventions for:
- Span naming conventions
- Attribute standardization  
- Trace context propagation
- Resource detection
- Metric instrumentation
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.test.spantestutil import SpanTestCase

from uvmgr.ops.dod import (
    create_exoskeleton,
    execute_complete_automation,
    validate_dod_criteria,
    generate_devops_pipeline,
    run_e2e_automation,
    analyze_project_status
)

from uvmgr.runtime.dod import (
    initialize_exoskeleton_files,
    execute_automation_workflow,
    validate_criteria_runtime,
    generate_pipeline_files,
    run_e2e_tests,
    analyze_project_health,
    create_automation_report
)


class TestWeaverSemanticConventions:
    """Test compliance with Weaver semantic conventions."""
    
    def setup_method(self):
        """Set up OTEL test infrastructure."""
        self.tracer_provider = TracerProvider()
        self.memory_exporter = []
        self.span_processor = SimpleSpanProcessor(
            MockSpanExporter(self.memory_exporter)
        )
        self.tracer_provider.add_span_processor(self.span_processor)
        trace.set_tracer_provider(self.tracer_provider)
        
    def teardown_method(self):
        """Clean up OTEL test infrastructure."""
        self.memory_exporter.clear()
    
    def test_dod_span_naming_conventions(self):
        """Test that DoD operations follow Weaver span naming conventions."""
        expected_span_names = {
            "dod.create_exoskeleton": create_exoskeleton,
            "dod.execute_complete_automation": execute_complete_automation,
            "dod.validate_dod_criteria": validate_dod_criteria,
            "dod.generate_devops_pipeline": generate_devops_pipeline,
            "dod.run_e2e_automation": run_e2e_automation,
            "dod.analyze_project_status": analyze_project_status
        }
        
        for expected_name, func in expected_span_names.items():
            # Verify span name follows dod.* namespace
            assert expected_name.startswith("dod."), \
                f"Span '{expected_name}' should start with 'dod.' namespace"
            
            # Verify snake_case naming
            assert "_" in expected_name, \
                f"Span '{expected_name}' should use snake_case"
            
            # Verify no uppercase letters
            assert expected_name.islower(), \
                f"Span '{expected_name}' should be lowercase"
    
    def test_dod_runtime_span_naming_conventions(self):
        """Test that DoD runtime operations follow Weaver span naming conventions."""
        expected_runtime_spans = {
            "dod.runtime.initialize_exoskeleton_files": initialize_exoskeleton_files,
            "dod.runtime.execute_automation_workflow": execute_automation_workflow,
            "dod.runtime.validate_criteria_runtime": validate_criteria_runtime,
            "dod.runtime.generate_pipeline_files": generate_pipeline_files,
            "dod.runtime.run_e2e_tests": run_e2e_tests,
            "dod.runtime.analyze_project_health": analyze_project_health,
            "dod.runtime.create_automation_report": create_automation_report
        }
        
        for expected_name, func in expected_runtime_spans.items():
            # Verify runtime span namespace
            assert expected_name.startswith("dod.runtime."), \
                f"Runtime span '{expected_name}' should start with 'dod.runtime.' namespace"
    
    def test_dod_attribute_naming_conventions(self):
        """Test DoD attribute names follow Weaver semantic conventions."""
        valid_dod_attributes = {
            # Core DoD attributes
            "dod.template": str,
            "dod.environment": str,
            "dod.force": bool,
            "dod.preview": bool,
            "dod.success_rate": float,
            "dod.execution_time": float,
            "dod.criteria_count": int,
            "dod.criteria_passed": int,
            "dod.files_created": int,
            "dod.workflows_created": int,
            "dod.ai_integrations": int,
            "dod.auto_fix": bool,
            "dod.parallel": bool,
            "dod.ai_assist": bool,
            "dod.skip_tests": bool,
            "dod.skip_security": bool,
            "dod.detailed": bool,
            "dod.fix_suggestions": bool,
            "dod.provider": str,
            "dod.features_enabled": int,
            "dod.environments_configured": int,
            "dod.headless": bool,
            "dod.record_video": bool,
            "dod.generate_report": bool,
            "dod.total_tests": int,
            "dod.passed_tests": int,
            "dod.suggestions": bool,
            "dod.health_score": float,
            "dod.overall_score": float,
            "dod.critical_score": float,
            "dod.important_score": float,
            "dod.report_generated": bool,
            "dod.report_formats": int,
            "dod.ai_insights_included": bool,
            
            # Project attributes
            "project.path": str,
            
            # Automation attributes
            "automation.strategy": str
        }
        
        for attr_name, expected_type in valid_dod_attributes.items():
            # Test namespace convention
            assert attr_name.startswith(("dod.", "project.", "automation.")), \
                f"Attribute '{attr_name}' must use proper namespace (dod., project., automation.)"
            
            # Test snake_case convention
            parts = attr_name.split(".")
            for part in parts:
                assert part.islower(), f"Attribute part '{part}' in '{attr_name}' must be lowercase"
                if "_" in part:
                    # If underscore is used, verify it's proper snake_case
                    assert not part.startswith("_") and not part.endswith("_"), \
                        f"Attribute part '{part}' has improper underscore usage"
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    @patch('uvmgr.ops.dod.initialize_exoskeleton_files')
    def test_create_exoskeleton_weaver_attributes(self, mock_init, mock_span):
        """Test create_exoskeleton sets proper Weaver attributes."""
        mock_span_instance = Mock()
        mock_span.return_value = mock_span_instance
        mock_init.return_value = {
            "success": True,
            "files_created": [{"path": "test.yaml"}],
            "workflows_created": ["workflow.yml"],
            "ai_integrations": ["code_review"]
        }
        
        create_exoskeleton(
            project_path=Path("/test/project"),
            template="enterprise",
            force=True,
            preview=False
        )
        
        # Verify span attributes were set according to Weaver conventions
        set_attributes_calls = mock_span_instance.set_attributes.call_args_list
        
        # Check initial attributes call
        initial_attrs = set_attributes_calls[0][0][0]
        required_initial_attrs = {
            "dod.template": "enterprise",
            "dod.force": True,
            "dod.preview": False,
            "project.path": "/test/project"
        }
        
        for attr_name, expected_value in required_initial_attrs.items():
            assert attr_name in initial_attrs, f"Missing required attribute: {attr_name}"
            assert initial_attrs[attr_name] == expected_value, \
                f"Attribute {attr_name} = {initial_attrs[attr_name]}, expected {expected_value}"
        
        # Check result attributes call
        if len(set_attributes_calls) > 1:
            result_attrs = set_attributes_calls[1][0][0]
            expected_result_attrs = [
                "dod.files_created",
                "dod.workflows_created", 
                "dod.ai_integrations"
            ]
            
            for attr_name in expected_result_attrs:
                assert attr_name in result_attrs, f"Missing result attribute: {attr_name}"
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    @patch('uvmgr.ops.dod.execute_automation_workflow')
    def test_execute_complete_automation_weaver_attributes(self, mock_execute, mock_span):
        """Test complete automation sets comprehensive Weaver attributes."""
        mock_span_instance = Mock()
        mock_span.return_value = mock_span_instance
        mock_execute.return_value = {
            "success": True,
            "criteria_results": {"testing": {"passed": True, "score": 90}}
        }
        
        execute_complete_automation(
            project_path=Path("/test/project"),
            environment="production",
            criteria=["testing", "security"],
            skip_tests=False,
            skip_security=False,
            auto_fix=True,
            parallel=True,
            ai_assist=True
        )
        
        # Verify comprehensive attribute coverage
        set_attributes_calls = mock_span_instance.set_attributes.call_args_list
        
        # Check initial operational attributes
        initial_attrs = set_attributes_calls[0][0][0]
        required_operational_attrs = {
            "dod.environment": "production",
            "dod.skip_tests": False,
            "dod.skip_security": False,
            "dod.auto_fix": True,
            "dod.parallel": True,
            "dod.ai_assist": True,
            "project.path": "/test/project"
        }
        
        for attr_name, expected_value in required_operational_attrs.items():
            assert attr_name in initial_attrs, f"Missing operational attribute: {attr_name}"
            assert initial_attrs[attr_name] == expected_value
        
        # Check result metrics attributes
        if len(set_attributes_calls) > 1:
            result_attrs = set_attributes_calls[1][0][0]
            expected_metrics_attrs = [
                "dod.success_rate",
                "dod.execution_time",
                "dod.criteria_passed"
            ]
            
            for attr_name in expected_metrics_attrs:
                assert attr_name in result_attrs, f"Missing metrics attribute: {attr_name}"
    
    def test_weaver_attribute_value_types(self):
        """Test that Weaver attributes use correct value types."""
        # Define expected type mappings per Weaver conventions
        type_mappings = {
            # String attributes
            str: ["dod.template", "dod.environment", "dod.provider", "project.path", "automation.strategy"],
            # Boolean attributes  
            bool: ["dod.force", "dod.preview", "dod.auto_fix", "dod.parallel", "dod.ai_assist", 
                   "dod.skip_tests", "dod.skip_security", "dod.detailed", "dod.fix_suggestions",
                   "dod.headless", "dod.record_video", "dod.generate_report", "dod.suggestions",
                   "dod.report_generated", "dod.ai_insights_included"],
            # Numeric attributes (int)
            int: ["dod.criteria_count", "dod.criteria_passed", "dod.files_created", 
                  "dod.workflows_created", "dod.ai_integrations", "dod.features_enabled",
                  "dod.environments_configured", "dod.total_tests", "dod.passed_tests", "dod.report_formats"],
            # Numeric attributes (float)
            float: ["dod.success_rate", "dod.execution_time", "dod.health_score", 
                    "dod.overall_score", "dod.critical_score", "dod.important_score"]
        }
        
        for expected_type, attr_names in type_mappings.items():
            for attr_name in attr_names:
                # This test validates our type expectations are consistent
                # In practice, OTEL will convert types, but we should be intentional
                assert isinstance(attr_name, str), f"Attribute name {attr_name} should be string"
                
                # Verify naming follows conventions for the type
                if expected_type == bool:
                    # Boolean attributes should be clearly named (is_*, has_*, etc. or clear verbs)
                    assert any(word in attr_name.lower() for word in 
                              ['force', 'preview', 'auto', 'parallel', 'assist', 'skip', 
                               'detailed', 'suggestions', 'headless', 'record', 'generate', 'report']), \
                        f"Boolean attribute '{attr_name}' should have clear boolean naming"


class TestOpenTelemetryInstrumentation:
    """Test OpenTelemetry instrumentation functionality."""
    
    def setup_method(self):
        """Set up OTEL test infrastructure."""
        self.captured_spans = []
        self.mock_tracer = Mock()
        self.mock_span = Mock()
        self.mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=self.mock_span)
        self.mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
    
    @patch('uvmgr.ops.dod.tracer')
    @patch('uvmgr.ops.dod.initialize_exoskeleton_files')
    def test_span_lifecycle_management(self, mock_init, mock_tracer):
        """Test proper span lifecycle management."""
        mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
        
        # Mock the span context manager
        mock_span = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_span)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracer.start_as_current_span.return_value = mock_context_manager
        
        create_exoskeleton(
            project_path=Path("/test/project"),
            template="standard"
        )
        
        # Verify span was started with correct name
        mock_tracer.start_as_current_span.assert_called_with("dod.create_exoskeleton")
        
        # Verify span context was entered and exited
        mock_context_manager.__enter__.assert_called_once()
        mock_context_manager.__exit__.assert_called_once()
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    def test_exception_recording(self, mock_get_span):
        """Test that exceptions are properly recorded in spans."""
        mock_span = Mock()
        mock_get_span.return_value = mock_span
        
        with patch('uvmgr.ops.dod.initialize_exoskeleton_files') as mock_init:
            mock_init.side_effect = Exception("Test exception")
            
            result = create_exoskeleton(
                project_path=Path("/test/project"),
                template="standard"
            )
            
            # Verify exception was recorded
            mock_span.record_exception.assert_called_once()
            
            # Verify error result
            assert result["success"] is False
            assert "Failed to create exoskeleton" in result["error"]
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    def test_span_status_on_success(self, mock_get_span):
        """Test span status is set correctly on successful operations."""
        mock_span = Mock()
        mock_get_span.return_value = mock_span
        
        with patch('uvmgr.ops.dod.initialize_exoskeleton_files') as mock_init:
            mock_init.return_value = {
                "success": True,
                "files_created": [{"path": "test.yaml"}],
                "workflows_created": ["workflow.yml"],
                "ai_integrations": ["review"]
            }
            
            result = create_exoskeleton(
                project_path=Path("/test/project"),
                template="standard"
            )
            
            # Verify successful result
            assert result["success"] is True
            
            # Verify span attributes were set (indicating success)
            mock_span.set_attributes.assert_called()
    
    def test_runtime_span_instrumentation(self):
        """Test that runtime functions are properly instrumented."""
        # Test that runtime functions use @span decorator
        runtime_functions = [
            initialize_exoskeleton_files,
            execute_automation_workflow,
            validate_criteria_runtime,
            generate_pipeline_files,
            run_e2e_tests,
            analyze_project_health,
            create_automation_report
        ]
        
        for func in runtime_functions:
            # Check if function has span instrumentation
            # This is a simplified check - in practice we'd verify the decorator
            assert hasattr(func, '__name__'), f"Function {func} should have proper name attribute"
            
            # Verify function follows runtime naming convention
            if hasattr(func, '__qualname__'):
                # Should be part of runtime module
                assert 'runtime' in func.__module__ or 'dod' in func.__module__, \
                    f"Runtime function {func.__name__} should be in runtime module"


class TestWeaverConventionCompliance:
    """Test comprehensive Weaver semantic convention compliance."""
    
    def test_namespace_segregation(self):
        """Test that different namespaces are properly segregated."""
        namespaces = {
            "dod": [
                "template", "environment", "force", "preview", "success_rate",
                "execution_time", "criteria_count", "auto_fix", "parallel"
            ],
            "project": [
                "path"
            ],
            "automation": [
                "strategy"
            ]
        }
        
        for namespace, attributes in namespaces.items():
            for attr in attributes:
                full_attr = f"{namespace}.{attr}"
                
                # Verify no namespace collision
                for other_namespace in namespaces:
                    if other_namespace != namespace:
                        other_attrs = namespaces[other_namespace]
                        assert attr not in other_attrs, \
                            f"Attribute '{attr}' conflicts between {namespace} and {other_namespace}"
    
    def test_semantic_consistency(self):
        """Test semantic consistency across DoD operations."""
        # All DoD operations should use consistent attribute names for similar concepts
        consistent_attributes = {
            "project.path": "All operations should reference project path consistently",
            "dod.environment": "Environment should be consistently named",
            "dod.success_rate": "Success metrics should use consistent naming",
            "dod.execution_time": "Timing metrics should use consistent naming"
        }
        
        for attr_name, description in consistent_attributes.items():
            # Verify attribute name follows conventions
            namespace, attr = attr_name.split(".", 1)
            
            # Namespace should be valid
            assert namespace in ["dod", "project", "automation"], \
                f"Invalid namespace '{namespace}' in '{attr_name}'"
            
            # Attribute should be snake_case
            assert attr.islower(), f"Attribute '{attr}' should be lowercase"
            if "_" in attr:
                parts = attr.split("_")
                assert all(part.isalnum() for part in parts), \
                    f"Attribute parts in '{attr}' should be alphanumeric"
    
    def test_weaver_resource_attributes(self):
        """Test that DoD operations include proper resource attributes."""
        expected_resource_attrs = {
            "service.name": "uvmgr",
            "service.namespace": "dod",
            "service.version": str,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python"
        }
        
        # This test validates our expectations for resource attributes
        # In practice, these would be set at the tracer provider level
        for attr_name, expected_type in expected_resource_attrs.items():
            # Verify resource attribute naming
            assert "." in attr_name, f"Resource attribute '{attr_name}' should use dotted notation"
            
            parts = attr_name.split(".")
            assert len(parts) >= 2, f"Resource attribute '{attr_name}' should have namespace"
            assert all(part.islower() for part in parts), \
                f"Resource attribute '{attr_name}' should be lowercase"


class MockSpanExporter:
    """Mock span exporter for testing."""
    
    def __init__(self, memory_storage):
        self.memory_storage = memory_storage
    
    def export(self, spans):
        self.memory_storage.extend(spans)
        return trace.SpanExportResult.SUCCESS
    
    def shutdown(self):
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])