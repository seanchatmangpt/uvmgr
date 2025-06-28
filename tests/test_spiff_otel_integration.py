"""
Tests for SpiffWorkflow OTEL Integration
=======================================

Tests validating the integration between SpiffWorkflow and OpenTelemetry
instrumentation, ensuring workflows can validate OTEL functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import json

from uvmgr.ops.spiff_otel_validation import (
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
    OTELValidationResult
)


class TestSpiffOTELIntegration:
    """Test SpiffWorkflow OTEL validation integration."""

    def test_create_otel_validation_workflow(self, tmp_path):
        """Test creating OTEL validation BPMN workflow."""
        test_commands = [
            "uvmgr otel status",
            "uvmgr tests run tests/test_instrumentation.py"
        ]
        
        workflow_path = tmp_path / "test_validation.bpmn"
        
        # Create workflow
        result_path = create_otel_validation_workflow(workflow_path, test_commands)
        
        # Verify workflow was created
        assert result_path.exists()
        assert result_path == workflow_path
        
        # Verify BPMN content
        content = workflow_path.read_text()
        assert "otel_validation_workflow" in content
        assert "Start OTEL Validation" in content
        assert "Setup Validation Environment" in content
        assert "Validate OTEL Results" in content
        assert "OTEL Validation Complete" in content
        
        # Verify test commands are included
        for cmd in test_commands:
            # Should find shortened version of command in task names
            assert cmd[:20] in content or "Execute Test" in content

    def test_execute_otel_validation_workflow_success(self, tmp_path):
        """Test successful execution of OTEL validation workflow."""
        test_commands = ["echo 'test command'"]
        workflow_path = tmp_path / "test.bpmn"
        
        # Create minimal workflow
        create_otel_validation_workflow(workflow_path, test_commands)
        
        # Mock successful execution
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run_bpmn, \
             patch("subprocess.run") as mock_subprocess:
            
            # Mock workflow execution
            mock_run_bpmn.return_value = {
                "status": "completed",
                "steps_executed": 3,
                "duration_seconds": 1.5
            }
            
            # Mock test command execution
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Success output",
                stderr=""
            )
            
            # Execute validation
            result = execute_otel_validation_workflow(
                workflow_path, test_commands, timeout_seconds=60
            )
            
            # Verify successful result
            assert isinstance(result, OTELValidationResult)
            assert result.success is True
            assert result.workflow_name == "test"
            assert len(result.validation_steps) >= 3  # BPMN, workflow, test command
            assert result.duration_seconds > 0
            assert len(result.errors) == 0

    def test_execute_otel_validation_workflow_failure(self, tmp_path):
        """Test OTEL validation workflow with failures."""
        test_commands = ["false"]  # Command that always fails
        workflow_path = tmp_path / "test_fail.bpmn"
        
        create_otel_validation_workflow(workflow_path, test_commands)
        
        # Mock failure scenarios
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file", return_value=False), \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run_bpmn:
            
            mock_run_bpmn.return_value = {
                "status": "failed",
                "steps_executed": 1,
                "duration_seconds": 0.5
            }
            
            result = execute_otel_validation_workflow(
                workflow_path, test_commands, timeout_seconds=60
            )
            
            # Verify failure is captured
            assert result.success is False
            assert len(result.errors) > 0
            assert "BPMN validation failed" in result.errors

    def test_8020_otel_validation(self):
        """Test 80/20 OTEL validation approach."""
        with patch("uvmgr.ops.spiff_otel_validation.create_otel_validation_workflow") as mock_create, \
             patch("uvmgr.ops.spiff_otel_validation.execute_otel_validation_workflow") as mock_execute:
            
            # Mock workflow creation
            mock_workflow_path = Path("/tmp/8020_otel_validation.bpmn")
            mock_create.return_value = mock_workflow_path
            
            # Mock successful execution
            mock_result = OTELValidationResult(
                success=True,
                workflow_name="8020_otel_validation",
                validation_steps=["Core instrumentation", "Critical spans", "Essential metrics"],
                metrics_validated=10,
                spans_validated=15,
                errors=[],
                performance_data={"total_duration": 2.5},
                duration_seconds=2.5
            )
            mock_execute.return_value = mock_result
            
            # Execute 80/20 validation
            result = run_8020_otel_validation()
            
            # Verify critical tests were used
            assert mock_create.called
            create_args = mock_create.call_args[0]
            test_commands = create_args[1]
            
            # Should include critical OTEL tests
            assert any("otel status" in cmd for cmd in test_commands)
            assert any("test_instrumentation" in cmd for cmd in test_commands)
            assert any("otel validate" in cmd for cmd in test_commands)
            
            # Verify successful result
            assert result.success is True
            assert result.metrics_validated > 0
            assert result.spans_validated > 0

    def test_validation_step_creation(self):
        """Test individual validation step execution and monitoring."""
        from uvmgr.ops.spiff_otel_validation import _execute_test_command_with_validation
        
        with patch("subprocess.run") as mock_subprocess:
            # Mock successful test execution with OTEL output
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Test output with span data and metric counts",
                stderr=""
            )
            
            # Execute test step
            step = _execute_test_command_with_validation(
                "uvmgr otel status", None, 1
            )
            
            # Verify step details
            assert step.name == "Test Step 1"
            assert step.type == "test"
            assert step.success is True
            assert step.duration > 0
            assert "command" in step.details
            assert "metrics_count" in step.details
            assert "spans_count" in step.details

    def test_otel_system_health_validation(self):
        """Test OTEL system health validation."""
        from uvmgr.ops.spiff_otel_validation import _validate_otel_system_health
        
        # Mock healthy OTEL system
        with patch("uvmgr.ops.spiff_otel_validation._check_telemetry_import", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation._check_span_creation", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation._check_metric_creation", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation._check_instrumentation_registry", return_value=True):
            
            step = _validate_otel_system_health()
            
            assert step.success is True
            assert step.type == "system"
            assert step.details["telemetry_import"] is True
            assert step.details["span_creation"] is True
            assert step.details["metric_creation"] is True
            assert step.details["instrumentation_registry"] is True

    def test_bpmn_workflow_generation(self):
        """Test BPMN workflow content generation."""
        from uvmgr.ops.spiff_otel_validation import _generate_otel_validation_bpmn
        
        test_commands = [
            "uvmgr tests run",
            "uvmgr otel validate spans",
            "uvmgr otel validate metrics"
        ]
        
        bpmn_content = _generate_otel_validation_bpmn(test_commands)
        
        # Verify BPMN structure
        assert "<?xml version=" in bpmn_content
        assert "bpmn:definitions" in bpmn_content
        assert "otel_validation_workflow" in bpmn_content
        assert "otel_validation_process" in bpmn_content
        
        # Verify workflow elements
        assert "start_validation" in bpmn_content
        assert "setup_validation" in bpmn_content
        assert "validate_results" in bpmn_content
        assert "end_validation" in bpmn_content
        
        # Verify test tasks are included
        for i in range(1, len(test_commands) + 1):
            assert f"test_task_{i}" in bpmn_content
        
        # Verify flows between tasks
        assert "to_test_1" in bpmn_content
        assert "to_validate" in bpmn_content

    def test_workflow_timeout_handling(self, tmp_path):
        """Test workflow execution with timeout scenarios."""
        test_commands = ["sleep 10"]  # Long running command
        workflow_path = tmp_path / "timeout_test.bpmn"
        
        create_otel_validation_workflow(workflow_path, test_commands)
        
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run_bpmn, \
             patch("subprocess.run") as mock_subprocess:
            
            # Mock timeout
            from subprocess import TimeoutExpired
            mock_subprocess.side_effect = TimeoutExpired("sleep", 1)
            
            mock_run_bpmn.return_value = {
                "status": "completed",
                "steps_executed": 1,
                "duration_seconds": 1.0
            }
            
            result = execute_otel_validation_workflow(
                workflow_path, test_commands, timeout_seconds=1
            )
            
            # Should handle timeout gracefully
            assert result.success is False
            assert any("timeout" in error.lower() for error in result.errors)

    def test_metrics_and_spans_counting(self):
        """Test counting of metrics and spans in command output."""
        from uvmgr.ops.spiff_otel_validation import _count_metrics_in_output, _count_spans_in_output
        
        # Test output with OTEL data
        output = """
        Starting test execution...
        Creating span: test.execution
        Recording metric: test.counter_total
        Processing with trace context
        Histogram metric: test.duration_seconds
        Span completed: test.execution
        Test completed successfully
        """
        
        metrics_count = _count_metrics_in_output(output)
        spans_count = _count_spans_in_output(output)
        
        # Should find metric and span references
        assert metrics_count >= 2  # counter_total, duration_seconds
        assert spans_count >= 2   # span creation and trace references


class TestSpiffOTELWorkflowE2E:
    """End-to-end tests for Spiff OTEL workflow integration."""

    def test_complete_validation_workflow(self, tmp_path):
        """Test complete validation workflow from creation to execution."""
        # Create test project structure
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        
        # Create mock test file
        test_file = project_path / "test_otel.py"
        test_file.write_text("""
def test_telemetry_works():
    from uvmgr.core.telemetry import span
    with span("test"):
        assert True
""")
        
        test_commands = [
            f"python -m pytest {test_file} -v",
            "echo 'OTEL validation complete'"
        ]
        
        workflow_path = tmp_path / "complete_validation.bpmn"
        
        # Mock all external dependencies
        with patch("uvmgr.ops.spiff_otel_validation.validate_bpmn_file", return_value=True), \
             patch("uvmgr.ops.spiff_otel_validation.run_bpmn") as mock_run_bpmn, \
             patch("subprocess.run") as mock_subprocess:
            
            # Mock successful workflow execution
            mock_run_bpmn.return_value = {
                "status": "completed",
                "steps_executed": 4,
                "total_tasks": 6,
                "completed_tasks": 6,
                "failed_tasks": 0,
                "duration_seconds": 3.2
            }
            
            # Mock successful test commands
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Test passed\nspan: test.execution\nmetric: test.counter",
                stderr=""
            )
            
            # Create and execute workflow
            create_otel_validation_workflow(workflow_path, test_commands)
            result = execute_otel_validation_workflow(
                workflow_path, test_commands, project_path
            )
            
            # Verify complete execution
            assert result.success is True
            assert result.workflow_name == "complete_validation"
            assert len(result.validation_steps) >= 4
            assert result.metrics_validated > 0
            assert result.spans_validated > 0
            assert result.duration_seconds > 0
            assert len(result.errors) == 0
            
            # Verify workflow was actually called
            mock_run_bpmn.assert_called_once_with(workflow_path)
            
            # Verify test commands were executed
            assert mock_subprocess.call_count >= len(test_commands)

    def test_integration_with_real_spiff_engine(self, tmp_path):
        """Test integration with actual SpiffWorkflow engine."""
        # Create minimal but valid BPMN workflow
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="test_workflow"
                  targetNamespace="http://test.com">
  <bpmn:process id="test_process" isExecutable="true">
    <bpmn:startEvent id="start">
      <bpmn:outgoing>to_end</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="to_end" sourceRef="start" targetRef="end"/>
    <bpmn:endEvent id="end">
      <bpmn:incoming>to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""
        
        workflow_file = tmp_path / "minimal.bpmn"
        workflow_file.write_text(bpmn_content)
        
        # Test with actual SpiffWorkflow engine
        from uvmgr.runtime.agent.spiff import validate_bpmn_file, run_bpmn
        
        # Validate BPMN file
        is_valid = validate_bpmn_file(workflow_file)
        assert is_valid is True
        
        # Execute workflow (should complete quickly)
        stats = run_bpmn(workflow_file)
        assert stats["status"] == "completed"
        assert stats["completed_tasks"] >= 1