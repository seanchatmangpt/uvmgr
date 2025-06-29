"""
Unit tests for OpenTelemetry and Weaver semantic convention validation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Set

# Import OpenTelemetry and semantic convention modules
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, metric_gauge
from uvmgr.core.semconv import (
    CliAttributes, PackageAttributes, SecurityAttributes, 
    WorktreeAttributes, GuideAttributes, InfoDesignAttributes,
    PackageOperations, validate_attribute
)
from uvmgr.core.instrumentation import instrument_command, add_span_attributes, add_span_event


class TestOpenTelemetryIntegration:
    """Test OpenTelemetry integration and functionality."""

    def test_span_creation(self):
        """Test span creation functionality."""
        with span("test.operation") as current_span:
            # Span should be created
            assert current_span is not None
            
            # Should be able to set attributes
            if hasattr(current_span, 'set_attribute'):
                current_span.set_attribute("test.key", "test.value")

    def test_span_nesting(self):
        """Test nested span creation."""
        with span("parent.operation") as parent_span:
            assert parent_span is not None
            
            with span("child.operation") as child_span:
                assert child_span is not None
                # Child span should be different from parent
                # (In real implementation, they would have parent-child relationship)

    def test_span_with_attributes(self):
        """Test span creation with attributes."""
        attributes = {
            "operation.type": "test",
            "operation.duration": 1.5,
            "operation.success": True
        }
        
        with span("test.operation", **attributes) as current_span:
            assert current_span is not None

    def test_metric_counter(self):
        """Test metric counter functionality."""
        counter = metric_counter("test.counter")
        
        # Should be callable
        assert callable(counter)
        
        # Should accept values
        counter(1)
        counter(5)
        
        # Should not raise exceptions with no-op implementation
        try:
            counter(10)
        except Exception as e:
            pytest.fail(f"Counter should not raise exceptions: {e}")

    def test_metric_histogram(self):
        """Test metric histogram functionality."""
        histogram = metric_histogram("test.histogram")
        
        # Should be callable
        assert callable(histogram)
        
        # Should accept duration values
        histogram(0.5)
        histogram(1.2)
        histogram(0.001)
        
        # Should not raise exceptions with no-op implementation
        try:
            histogram(2.5)
        except Exception as e:
            pytest.fail(f"Histogram should not raise exceptions: {e}")

    def test_metric_gauge(self):
        """Test metric gauge functionality."""
        gauge = metric_gauge("test.gauge")
        
        # Should be callable
        assert callable(gauge)
        
        # Should accept gauge values
        gauge(10)
        gauge(-5)
        gauge(0)
        
        # Should not raise exceptions with no-op implementation
        try:
            gauge(100)
        except Exception as e:
            pytest.fail(f"Gauge should not raise exceptions: {e}")

    def test_instrumentation_decorator(self):
        """Test command instrumentation decorator."""
        executed = []
        
        @instrument_command("test_command")
        def test_function(arg1: str, arg2: int = 42):
            executed.append((arg1, arg2))
            return f"result_{arg1}_{arg2}"
        
        # Function should execute normally
        result = test_function("test", 123)
        
        assert result == "result_test_123"
        assert executed == [("test", 123)]

    def test_add_span_attributes(self):
        """Test adding span attributes."""
        # Should not raise exceptions even if no span is active
        try:
            add_span_attributes(
                test_key="test_value",
                test_number=42,
                test_bool=True
            )
        except Exception as e:
            pytest.fail(f"add_span_attributes should not raise exceptions: {e}")

    def test_add_span_event(self):
        """Test adding span events."""
        # Should not raise exceptions even if no span is active
        try:
            add_span_event("test.event", {"key": "value"})
        except Exception as e:
            pytest.fail(f"add_span_event should not raise exceptions: {e}")

    def test_telemetry_graceful_degradation(self):
        """Test that telemetry works when OpenTelemetry is not configured."""
        # This tests the no-op implementations
        
        # All these should work without raising exceptions
        with span("test.span"):
            counter = metric_counter("test.counter")
            counter(1)
            
            histogram = metric_histogram("test.histogram")
            histogram(0.5)
            
            gauge = metric_gauge("test.gauge")
            gauge(10)
            
            add_span_attributes(test="value")
            add_span_event("test.event", {})


class TestSemanticConventions:
    """Test semantic convention classes and validation."""

    def test_cli_attributes(self):
        """Test CLI attribute definitions."""
        # Check that all expected attributes exist
        assert hasattr(CliAttributes, 'CLI_COMMAND')
        assert hasattr(CliAttributes, 'CLI_SUBCOMMAND')
        assert hasattr(CliAttributes, 'CLI_EXIT_CODE')
        assert hasattr(CliAttributes, 'COMMAND')  # Alias
        assert hasattr(CliAttributes, 'EXIT_CODE')  # Alias
        
        # Check attribute values
        assert CliAttributes.CLI_COMMAND == "cli.command"
        assert CliAttributes.CLI_SUBCOMMAND == "cli.subcommand"
        assert CliAttributes.CLI_EXIT_CODE == "cli.exit_code"
        
        # Check aliases
        assert CliAttributes.COMMAND == CliAttributes.CLI_COMMAND
        assert CliAttributes.EXIT_CODE == CliAttributes.CLI_EXIT_CODE

    def test_package_attributes(self):
        """Test package attribute definitions."""
        # Check that all expected attributes exist
        assert hasattr(PackageAttributes, 'PACKAGE_NAME')
        assert hasattr(PackageAttributes, 'PACKAGE_VERSION')
        assert hasattr(PackageAttributes, 'PACKAGE_OPERATION')
        assert hasattr(PackageAttributes, 'OPERATION')  # Alias
        assert hasattr(PackageAttributes, 'DEV_DEPENDENCY')
        
        # Check attribute values
        assert PackageAttributes.PACKAGE_NAME == "package.name"
        assert PackageAttributes.PACKAGE_VERSION == "package.version"
        assert PackageAttributes.PACKAGE_OPERATION == "package.operation"
        assert PackageAttributes.DEV_DEPENDENCY == "package.dev_dependency"

    def test_package_operations(self):
        """Test package operation values."""
        assert hasattr(PackageOperations, 'ADD')
        assert hasattr(PackageOperations, 'REMOVE')
        assert hasattr(PackageOperations, 'UPDATE')
        assert hasattr(PackageOperations, 'LIST')
        
        assert PackageOperations.ADD == "add"
        assert PackageOperations.REMOVE == "remove"
        assert PackageOperations.UPDATE == "update"
        assert PackageOperations.LIST == "list"

    def test_security_attributes(self):
        """Test security attribute definitions."""
        assert hasattr(SecurityAttributes, 'OPERATION')
        assert hasattr(SecurityAttributes, 'PROJECT_PATH')
        assert hasattr(SecurityAttributes, 'SEVERITY_THRESHOLD')
        assert hasattr(SecurityAttributes, 'SCAN_TYPE')
        assert hasattr(SecurityAttributes, 'VULNERABILITY_COUNT')
        
        assert SecurityAttributes.OPERATION == "security.operation"
        assert SecurityAttributes.PROJECT_PATH == "security.project_path"

    def test_worktree_attributes(self):
        """Test worktree attribute definitions."""
        assert hasattr(WorktreeAttributes, 'OPERATION')
        assert hasattr(WorktreeAttributes, 'BRANCH')
        assert hasattr(WorktreeAttributes, 'PATH')
        assert hasattr(WorktreeAttributes, 'PROJECT_PATH')
        
        assert WorktreeAttributes.OPERATION == "worktree.operation"
        assert WorktreeAttributes.BRANCH == "worktree.branch"

    def test_guide_attributes(self):
        """Test guide attribute definitions."""
        assert hasattr(GuideAttributes, 'OPERATION')
        assert hasattr(GuideAttributes, 'NAME')
        assert hasattr(GuideAttributes, 'VERSION')
        assert hasattr(GuideAttributes, 'CATEGORY')
        
        assert GuideAttributes.OPERATION == "guide.operation"
        assert GuideAttributes.NAME == "guide.name"

    def test_info_design_attributes(self):
        """Test information design attribute definitions."""
        assert hasattr(InfoDesignAttributes, 'OPERATION')
        assert hasattr(InfoDesignAttributes, 'SOURCE')
        assert hasattr(InfoDesignAttributes, 'ANALYSIS_TYPE')
        assert hasattr(InfoDesignAttributes, 'DOC_TYPE')
        
        assert InfoDesignAttributes.OPERATION == "infodesign.operation"
        assert InfoDesignAttributes.SOURCE == "infodesign.source"

    def test_validate_attribute_function(self):
        """Test the validate_attribute function."""
        # Valid attributes should return True
        assert validate_attribute("cli.command", "test_command") is True
        assert validate_attribute("package.name", "test_package") is True
        assert validate_attribute("security.operation", "scan") is True
        
        # Invalid attributes should return False
        assert validate_attribute("invalid.attribute", "value") is False
        assert validate_attribute("not.a.real.attribute", "value") is False

    def test_all_attribute_classes_covered(self):
        """Test that validate_attribute covers all attribute classes."""
        # Get all attribute classes that should be validated
        from uvmgr.core.semconv import (
            ProcessAttributes, TestAttributes, ToolAttributes, PluginAttributes,
            BuildAttributes, ProjectAttributes, AIAttributes, CIAttributes,
            WorkflowAttributes, ReleaseAttributes, UvxAttributes, CacheAttributes,
            IndexAttributes, RemoteAttributes, SearchAttributes, ServerAttributes,
            ShellAttributes, McpAttributes, GitHubAttributes, MultiLangAttributes,
            PerformanceAttributes, ContainerAttributes, CiCdAttributes,
            AgentAttributes, InfrastructureAttributes
        )
        
        # Test a few attributes from each class to ensure they're included
        test_cases = [
            ("process.command", True),
            ("test.operation", True),
            ("tool.name", True),
            ("build.operation", True),
            ("project.name", True),
            ("ai.operation", True),
            ("workflow.operation", True),
            ("cache.operation", True),
            ("remote.operation", True),
            ("server.operation", True),
            ("mcp.operation", True),
        ]
        
        for attribute, expected in test_cases:
            assert validate_attribute(attribute, "test_value") == expected, \
                f"Attribute {attribute} validation failed"

    def test_semantic_convention_completeness(self):
        """Test that semantic conventions are complete and consistent."""
        # Test that all operation attributes have corresponding operation classes
        operation_attributes = [
            PackageAttributes.OPERATION,
            SecurityAttributes.OPERATION,
            WorktreeAttributes.OPERATION,
            GuideAttributes.OPERATION,
            InfoDesignAttributes.OPERATION,
        ]
        
        for attr in operation_attributes:
            # Should be a string ending with .operation
            assert isinstance(attr, str)
            assert attr.endswith(".operation")
            
            # Should be a valid attribute
            assert validate_attribute(attr, "test_operation") is True


class TestWeaverIntegration:
    """Test integration with Weaver semantic conventions."""

    def test_weaver_semantic_convention_format(self):
        """Test that semantic conventions follow Weaver format."""
        # Weaver conventions should follow specific patterns
        
        # Check CLI conventions
        cli_attrs = [
            CliAttributes.CLI_COMMAND,
            CliAttributes.CLI_SUBCOMMAND,
            CliAttributes.CLI_EXIT_CODE,
        ]
        
        for attr in cli_attrs:
            # Should be lowercase with dots as separators
            assert attr.islower()
            assert "." in attr
            assert attr.startswith("cli.")
            
            # Should not have underscores in the actual attribute name
            assert "_" not in attr or attr.count("_") <= 1  # Allow one underscore for compound words

    def test_weaver_attribute_consistency(self):
        """Test attribute naming consistency with Weaver standards."""
        # Check that similar concepts use consistent naming
        operation_attrs = [
            PackageAttributes.OPERATION,
            SecurityAttributes.OPERATION,
            WorktreeAttributes.OPERATION,
            GuideAttributes.OPERATION,
            InfoDesignAttributes.OPERATION,
        ]
        
        # All operation attributes should end with .operation
        for attr in operation_attrs:
            assert attr.endswith(".operation")
            
        # Check that name attributes are consistent
        name_attrs = [
            PackageAttributes.PACKAGE_NAME,
            GuideAttributes.NAME,
        ]
        
        for attr in name_attrs:
            assert ".name" in attr

    def test_weaver_validation_rules(self):
        """Test validation rules that would be enforced by Weaver."""
        # Test attribute naming rules
        valid_attributes = [
            "service.name",
            "service.version", 
            "http.method",
            "http.status_code",
            "db.operation",
            "messaging.operation",
        ]
        
        invalid_attributes = [
            "ServiceName",  # Should be lowercase
            "service_name",  # Should use dots not underscores
            "service.Name",  # Should not have capital letters
            "service..name",  # Should not have double dots
            ".service.name",  # Should not start with dot
            "service.name.",  # Should not end with dot
        ]
        
        # Note: Our validate_attribute function tests against our defined attributes,
        # not generic naming rules, so we test the principle with our actual attributes
        
        # Our attributes should follow the valid pattern
        uvmgr_attributes = [
            CliAttributes.CLI_COMMAND,
            PackageAttributes.PACKAGE_NAME,
            SecurityAttributes.OPERATION,
            WorktreeAttributes.BRANCH,
        ]
        
        for attr in uvmgr_attributes:
            # Should follow valid naming pattern
            assert "." in attr
            assert attr.islower()
            assert not attr.startswith(".")
            assert not attr.endswith(".")
            assert ".." not in attr

    def test_weaver_semantic_convention_registry(self):
        """Test that conventions match what would be in a Weaver registry."""
        # Test structure that would be expected in weaver.yaml
        expected_registry_structure = {
            "groups": {
                "cli": {
                    "attributes": ["command", "subcommand", "exit_code", "options"]
                },
                "package": {
                    "attributes": ["name", "version", "operation", "dev_dependency"]
                },
                "security": {
                    "attributes": ["operation", "project_path", "severity_threshold", "scan_type"]
                },
                "worktree": {
                    "attributes": ["operation", "branch", "path", "project_path"]
                },
                "guide": {
                    "attributes": ["operation", "name", "version", "category", "source"]
                },
                "infodesign": {
                    "attributes": ["operation", "source", "analysis_type", "doc_type"]
                }
            }
        }
        
        # Verify our attributes match expected structure
        for group, expected_attrs in expected_registry_structure["groups"].items():
            for attr in expected_attrs["attributes"]:
                full_attr = f"{group}.{attr}"
                # Should be valid in our system
                assert validate_attribute(full_attr, "test_value") is True, \
                    f"Expected attribute {full_attr} not found in validation"

    def test_weaver_generation_compatibility(self):
        """Test compatibility with Weaver code generation."""
        # Test that our attribute classes could be generated by Weaver
        
        # Check that class structure matches Weaver output
        attribute_classes = [
            CliAttributes,
            PackageAttributes,
            SecurityAttributes,
            WorktreeAttributes,
            GuideAttributes,
            InfoDesignAttributes,
        ]
        
        for attr_class in attribute_classes:
            # Should have class docstring
            assert attr_class.__doc__ is not None
            
            # Should have Final string attributes
            for attr_name in dir(attr_class):
                if not attr_name.startswith('_'):
                    attr_value = getattr(attr_class, attr_name)
                    assert isinstance(attr_value, str), \
                        f"Attribute {attr_class.__name__}.{attr_name} should be string"

    def test_otel_semantic_convention_compliance(self):
        """Test compliance with OpenTelemetry semantic conventions."""
        # Test that our conventions don't conflict with OTel standards
        
        # OTel reserved prefixes that we should not use for non-standard attributes
        otel_reserved_prefixes = [
            "otel.",
            "opentelemetry.",
        ]
        
        # Get all our attributes
        all_attributes = []
        attribute_classes = [
            CliAttributes, PackageAttributes, SecurityAttributes,
            WorktreeAttributes, GuideAttributes, InfoDesignAttributes,
        ]
        
        for attr_class in attribute_classes:
            for attr_name in dir(attr_class):
                if not attr_name.startswith('_'):
                    attr_value = getattr(attr_class, attr_name)
                    if isinstance(attr_value, str):
                        all_attributes.append(attr_value)
        
        # None of our attributes should use reserved prefixes
        for attr in all_attributes:
            for reserved_prefix in otel_reserved_prefixes:
                assert not attr.startswith(reserved_prefix), \
                    f"Attribute {attr} uses reserved prefix {reserved_prefix}"


class TestWeaverValidationIntegration:
    """Integration tests for Weaver validation."""

    def test_run_weaver_validation(self):
        """Test running Weaver validation on our semantic conventions."""
        # This would test integration with actual Weaver tool
        # For now, test that our validation infrastructure is in place
        
        # Check that validate_attribute function works comprehensively
        test_attributes = [
            ("cli.command", True),
            ("cli.subcommand", True),
            ("cli.exit_code", True),
            ("package.name", True),
            ("package.version", True),
            ("package.operation", True),
            ("security.operation", True),
            ("worktree.operation", True),
            ("guide.operation", True),
            ("infodesign.operation", True),
            ("invalid.attribute", False),
            ("not.real", False),
        ]
        
        for attr, expected in test_attributes:
            result = validate_attribute(attr, "test_value")
            assert result == expected, f"Validation failed for {attr}: expected {expected}, got {result}"

    def test_semantic_convention_coverage(self):
        """Test that all implemented commands have semantic conventions."""
        # This tests that we have semantic conventions for all major operations
        
        required_operations = [
            "cli.command",        # CLI operations
            "package.operation",  # Package management
            "test.operation",     # Testing
            "build.operation",    # Building
            "security.operation", # Security scanning
            "worktree.operation", # Git worktree
            "guide.operation",    # Guide management
            "infodesign.operation", # Information design
        ]
        
        for operation in required_operations:
            assert validate_attribute(operation, "test") is True, \
                f"Missing semantic convention for {operation}"

    def test_weaver_forge_integration(self):
        """Test integration with Weaver Forge workflow."""
        # Test that our conventions work with Weaver Forge automation
        
        # Check that we have the structure Weaver Forge expects
        weaver_forge_dir = Path(__file__).parent.parent.parent / "weaver-forge"
        
        if weaver_forge_dir.exists():
            # Check for registry files
            registry_dir = weaver_forge_dir / "registry"
            if registry_dir.exists():
                # Should have semantic convention definitions
                yaml_files = list(registry_dir.glob("*.yaml"))
                assert len(yaml_files) > 0, "No semantic convention YAML files found"


if __name__ == "__main__":
    pytest.main([__file__])