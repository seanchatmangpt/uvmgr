"""Unit tests for SpiffWorkflow OTEL validation operations."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from uvmgr.ops.spiff_otel_validation import (
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
    OTELValidationResult,
    TestValidationStep,
    _generate_otel_validation_bpmn,
    _execute_test_command_with_validation,
    _validate_otel_system_health,
    _check_telemetry_import,
    _check_span_creation,
    _check_metric_creation,
    _check_instrumentation_registry,
    _count_metrics_in_output,
    _count_spans_in_output
)


class TestSpiffOTELValidation:
    """Test SpiffWorkflow OTEL validation operations."""

    @pytest.fixture
    def sample_test_commands(self):
        """Sample test commands for validation."""
        return [
            "uvmgr otel status",
            "uvmgr otel validate",
            "python -c 'import opentelemetry'"
        ]

    @pytest.fixture
    def mock_validation_result(self):
        """Mock validation result for testing."""
        return OTELValidationResult(
            success=True,
            workflow_name="test_workflow",
            validation_steps=[
                TestValidationStep(
                    name="Test Step 1",
                    type="test",
                    success=True,
                    duration=1.0,
                    details={"metrics_count": 5, "spans_count": 3}
                ),
                TestValidationStep(
                    name="Test Step 2",
                    type="metric",
                    success=True,
                    duration=0.5,
                    details={"metrics_count": 2, "spans_count": 1}
                )
            ],
            metrics_validated=7,
            spans_validated=4,
            errors=[],
            performance_data={"total_duration": 1.5},
            duration_seconds=1.5
        )

    def test_create_otel_validation_workflow(self, sample_test_commands, tmp_path):
        """Test creating OTEL validation workflow."""
        workflow_path = tmp_path / "test_validation.bpmn"
        
        with patch("uvmgr.ops.spiff_otel_validation.span") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event, \
             patch("uvmgr.ops.spiff_otel_validation.metric_counter") as mock_counter:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()

            result_path = create_otel_validation_workflow(workflow_path, sample_test_commands)

            # Verify workflow file was created
            assert result_path == workflow_path
            assert workflow_path.exists()
            
            # Verify BPMN content
            content = workflow_path.read_text()
            assert "<?xml version=" in content
            assert "bpmn:definitions" in content
            assert "otel_validation" in content
            
            # Verify OTEL instrumentation
            mock_span.assert_called_with("spiff.create_otel_workflow", workflow_path=str(workflow_path))
            mock_event.assert_called_with("otel_workflow_created", {
                "workflow_path": str(workflow_path),
                "test_commands_count": len(sample_test_commands),
            })
            mock_counter.assert_called_with("spiff.otel_workflows.created")

    def test_generate_otel_validation_bpmn(self, sample_test_commands):
        """Test BPMN generation for OTEL validation."""
        bpmn_content = _generate_otel_validation_bpmn(sample_test_commands)
        
        # Verify BPMN structure
        assert "<?xml version=" in bpmn_content
        assert "bpmn:definitions" in bpmn_content
        assert "otel_validation" in bpmn_content
        assert "startEvent" in bpmn_content
        assert "endEvent" in bpmn_content
        
        # Verify test commands are included
        for cmd in sample_test_commands:
            assert cmd in bpmn_content

    def test_execute_otel_validation_workflow_success(self, sample_test_commands, tmp_path):
        """Test successful OTEL validation workflow execution."""
        workflow_path = tmp_path / "test_workflow.bpmn"
        workflow_path.write_text("<?xml version='1.0'?><bpmn:definitions></bpmn:definitions>")
        
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run, \
             patch("uvmgr.ops.spiff_otel_validation._execute_test_command_with_validation") as mock_execute, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_attributes") as mock_attrs, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event:

            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "steps_executed": 3,
                "completed_tasks": 3,
                "failed_tasks": 0
            }
            mock_execute.return_value = TestValidationStep(
                name="Test Command",
                type="test",
                success=True,
                duration=1.0,
                details={"metrics_count": 5, "spans_count": 3}
            )

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = execute_otel_validation_workflow(workflow_path, sample_test_commands)

            # Verify result structure
            assert isinstance(result, OTELValidationResult)
            assert result.success is True
            assert result.workflow_name == workflow_path.stem
            assert len(result.validation_steps) == 2 + len(sample_test_commands)  # BPMN + workflow + test commands
            assert result.metrics_validated > 0
            assert result.spans_validated > 0
            assert result.errors == []
            assert result.duration_seconds > 0

            # Verify OTEL instrumentation
            mock_span.assert_called_with("spiff.execute_otel_validation", 
                                        workflow=str(workflow_path), 
                                        test_count=len(sample_test_commands))
            mock_attrs.assert_called()
            mock_event.assert_called()

    def test_execute_otel_validation_workflow_bpmn_failure(self, sample_test_commands, tmp_path):
        """Test OTEL validation workflow with BPMN validation failure."""
        workflow_path = tmp_path / "test_workflow.bpmn"
        workflow_path.write_text("invalid content")
        
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span:

            mock_validate.return_value = False
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = execute_otel_validation_workflow(workflow_path, sample_test_commands)

            # Verify failure result
            assert result.success is False
            assert "BPMN workflow validation failed" in result.errors
            assert len(result.validation_steps) == 1  # Only BPMN validation step

    def test_execute_otel_validation_workflow_execution_failure(self, sample_test_commands, tmp_path):
        """Test OTEL validation workflow with execution failure."""
        workflow_path = tmp_path / "test_workflow.bpmn"
        workflow_path.write_text("<?xml version='1.0'?><bpmn:definitions></bpmn:definitions>")
        
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span:

            mock_validate.return_value = True
            mock_run.side_effect = Exception("Workflow execution failed")
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = execute_otel_validation_workflow(workflow_path, sample_test_commands)

            # Verify failure result
            assert result.success is False
            assert "Workflow execution error: Workflow execution failed" in result.errors
            assert len(result.validation_steps) == 2  # BPMN validation + workflow execution

    def test_run_8020_otel_validation(self, tmp_path):
        """Test 80/20 OTEL validation."""
        with patch("uvmgr.ops.spiff_otel_validation._validate_otel_system_health") as mock_health, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_attributes") as mock_attrs, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event, \
             patch("uvmgr.ops.spiff_otel_validation.metric_counter") as mock_counter, \
             patch("uvmgr.ops.spiff_otel_validation.metric_histogram") as mock_histogram:

            mock_health.return_value = TestValidationStep(
                name="System Health Check",
                type="health",
                success=True,
                duration=0.5,
                details={"otel_available": True, "metrics_count": 10, "spans_count": 5}
            )

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()

            result = run_8020_otel_validation(tmp_path)

            # Verify result structure
            assert isinstance(result, OTELValidationResult)
            assert result.success is True
            assert result.workflow_name == "8020_otel_validation"
            assert len(result.validation_steps) == 1
            assert result.metrics_validated == 10
            assert result.spans_validated == 5
            assert result.errors == []
            assert result.duration_seconds > 0

            # Verify OTEL instrumentation
            mock_span.assert_called_with("spiff.8020_otel_validation", project_path=str(tmp_path))
            mock_attrs.assert_called()
            mock_event.assert_called()
            mock_counter.assert_called()
            mock_histogram.assert_called()

    def test_execute_test_command_with_validation_success(self, tmp_path):
        """Test successful test command execution with validation."""
        with patch("uvmgr.ops.spiff_otel_validation.subprocess.run") as mock_run, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event:

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "otel metrics: 5, spans: 3"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = _execute_test_command_with_validation("test command", tmp_path, 1)

            # Verify result
            assert result.name == "Test Command 1"
            assert result.type == "test"
            assert result.success is True
            assert result.duration > 0
            assert result.details["metrics_count"] == 5
            assert result.details["spans_count"] == 3
            assert result.error is None

            # Verify subprocess was called
            mock_run.assert_called_once()
            mock_span.assert_called()
            mock_event.assert_called()

    def test_execute_test_command_with_validation_failure(self, tmp_path):
        """Test test command execution with failure."""
        with patch("uvmgr.ops.spiff_otel_validation.subprocess.run") as mock_run, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event:

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Command failed"
            mock_run.return_value = mock_result

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = _execute_test_command_with_validation("test command", tmp_path, 1)

            # Verify failure result
            assert result.success is False
            assert "Command failed" in result.error
            assert result.details["returncode"] == 1

    def test_validate_otel_system_health_success(self):
        """Test successful OTEL system health validation."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import, \
             patch("uvmgr.ops.spiff_otel_validation._check_span_creation") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation._check_metric_creation") as mock_metric, \
             patch("uvmgr.ops.spiff_otel_validation._check_instrumentation_registry") as mock_registry, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span_wrapper, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event:

            mock_import.return_value = True
            mock_span.return_value = True
            mock_metric.return_value = True
            mock_registry.return_value = True

            mock_span_wrapper.return_value.__enter__ = MagicMock()
            mock_span_wrapper.return_value.__exit__ = MagicMock(return_value=None)

            result = _validate_otel_system_health()

            # Verify success result
            assert result.success is True
            assert result.name == "OTEL System Health Check"
            assert result.type == "health"
            assert result.duration > 0
            assert result.details["otel_available"] is True
            assert result.error is None

            # Verify all checks were called
            mock_import.assert_called_once()
            mock_span.assert_called_once()
            mock_metric.assert_called_once()
            mock_registry.assert_called_once()

    def test_validate_otel_system_health_failure(self):
        """Test OTEL system health validation with failure."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import, \
             patch("uvmgr.ops.spiff_otel_validation._check_span_creation") as mock_span, \
             patch("uvmgr.ops.spiff_otel_validation._check_metric_creation") as mock_metric, \
             patch("uvmgr.ops.spiff_otel_validation._check_instrumentation_registry") as mock_registry, \
             patch("uvmgr.ops.spiff_otel_validation.span") as mock_span_wrapper, \
             patch("uvmgr.ops.spiff_otel_validation.add_span_event") as mock_event:

            mock_import.return_value = False
            mock_span.return_value = True
            mock_metric.return_value = True
            mock_registry.return_value = True

            mock_span_wrapper.return_value.__enter__ = MagicMock()
            mock_span_wrapper.return_value.__exit__ = MagicMock(return_value=None)

            result = _validate_otel_system_health()

            # Verify failure result
            assert result.success is False
            assert "OTEL telemetry import failed" in result.error
            assert result.details["otel_available"] is False

    def test_check_telemetry_import_success(self):
        """Test successful telemetry import check."""
        with patch("builtins.__import__") as mock_import:
            result = _check_telemetry_import()
            assert result is True
            mock_import.assert_called_with("opentelemetry")

    def test_check_telemetry_import_failure(self):
        """Test telemetry import check with failure."""
        with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
            result = _check_telemetry_import()
            assert result is False

    def test_check_span_creation_success(self):
        """Test successful span creation check."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = True
            result = _check_span_creation()
            assert result is True

    def test_check_span_creation_failure(self):
        """Test span creation check with failure."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = False
            result = _check_span_creation()
            assert result is False

    def test_check_metric_creation_success(self):
        """Test successful metric creation check."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = True
            result = _check_metric_creation()
            assert result is True
            mock_import.assert_called_with("opentelemetry")

    def test_check_metric_creation_failure(self):
        """Test metric creation check with failure."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = False
            result = _check_metric_creation()
            assert result is False

    def test_check_instrumentation_registry_success(self):
        """Test successful instrumentation registry check."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = True
            result = _check_instrumentation_registry()
            assert result is True

    def test_check_instrumentation_registry_failure(self):
        """Test instrumentation registry check with failure."""
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import") as mock_import:
            mock_import.return_value = False
            result = _check_instrumentation_registry()
            assert result is False

    def test_count_metrics_in_output(self):
        """Test counting metrics in output."""
        output = "otel metrics: 5, spans: 3, other metrics: 2"
        count = _count_metrics_in_output(output)
        assert count == 7  # 5 + 2

    def test_count_metrics_in_output_no_metrics(self):
        """Test counting metrics in output with no metrics."""
        output = "no metrics here"
        count = _count_metrics_in_output(output)
        assert count == 0

    def test_count_spans_in_output(self):
        """Test counting spans in output."""
        output = "otel spans: 3, other spans: 2, metrics: 5"
        count = _count_spans_in_output(output)
        assert count == 5  # 3 + 2

    def test_count_spans_in_output_no_spans(self):
        """Test counting spans in output with no spans."""
        output = "no spans here"
        count = _count_spans_in_output(output)
        assert count == 0

    def test_otel_validation_result_serialization(self, mock_validation_result):
        """Test OTEL validation result serialization."""
        # Test JSON serialization
        json_str = json.dumps(mock_validation_result.__dict__, default=str)
        assert json_str is not None
        
        # Test that all fields are included
        data = json.loads(json_str)
        assert "success" in data
        assert "workflow_name" in data
        assert "validation_steps" in data
        assert "metrics_validated" in data
        assert "spans_validated" in data
        assert "errors" in data
        assert "performance_data" in data
        assert "duration_seconds" in data

    def test_test_validation_step_serialization(self):
        """Test test validation step serialization."""
        step = TestValidationStep(
            name="Test Step",
            type="test",
            success=True,
            duration=1.0,
            details={"key": "value"},
            error=None
        )
        
        # Test JSON serialization
        json_str = json.dumps(step.__dict__, default=str)
        assert json_str is not None
        
        # Test that all fields are included
        data = json.loads(json_str)
        assert "name" in data
        assert "type" in data
        assert "success" in data
        assert "duration" in data
        assert "details" in data
        assert "error" in data 