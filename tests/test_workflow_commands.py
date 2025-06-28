"""
Tests for uvmgr workflow commands with Spiff BPMN integration.

This module tests the enhanced agent commands including:
- BPMN workflow execution
- File validation
- OTEL integration testing
- Workflow parsing and statistics
- Comprehensive error handling
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from uvmgr.commands.agent import (
    _display_execution_results,
    _display_test_results,
    _display_validation_details,
    _display_workflow_statistics,
    _get_file_statistics,
    _get_telemetry_statistics,
    _get_workflow_statistics,
    _parse_workflow_structure,
    _test_otel_integration,
    agent_app,
    run_bpmn_workflow,
    test_workflow,
    validate_workflow,
    workflow_stats,
)


class TestWorkflowCommands:
    """Test workflow command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def simple_bpmn(self):
        """Create a simple BPMN workflow for testing."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="simple_workflow"
                  targetNamespace="http://example.com/simple">
  
  <bpmn:process id="simple_process" isExecutable="true">
    <bpmn:startEvent id="start_event" name="Start">
      <bpmn:outgoing>flow1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:sequenceFlow id="flow1" sourceRef="start_event" targetRef="service_task"/>
    
    <bpmn:serviceTask id="service_task" name="Process Data">
      <bpmn:incoming>flow1</bpmn:incoming>
      <bpmn:outgoing>flow2</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="flow2" sourceRef="service_task" targetRef="end_event"/>
    
    <bpmn:endEvent id="end_event" name="End">
      <bpmn:incoming>flow2</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
            f.write(bpmn_content)
            return Path(f.name)

    @pytest.fixture
    def invalid_bpmn(self):
        """Create an invalid BPMN file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
            f.write("invalid xml content")
            return Path(f.name)

    def test_run_bpmn_workflow_success(self, simple_bpmn):
        """Test successful BPMN workflow execution."""
        with patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.core.instrumentation.add_span_event") as mock_event:

            # Setup mocks
            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "duration_seconds": 1.5,
                "steps_executed": 3,
                "total_tasks": 4,
                "completed_tasks": 4,
                "failed_tasks": 0,
                "workflow_name": "test"
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            # Execute command
            result = runner.invoke(agent_app, ["run", str(simple_bpmn)])

            # Verify execution
            assert result.exit_code == 0
            mock_validate.assert_called_once_with(simple_bpmn)
            mock_run.assert_called_once_with(simple_bpmn)
            assert mock_event.call_count >= 2  # started and completed events

    def test_run_bpmn_workflow_validation_failure(self, invalid_bpmn):
        """Test BPMN workflow execution with validation failure."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span:

            mock_validate.return_value = False
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["run", str(invalid_bpmn)])

            assert result.exit_code == 1
            assert "BPMN validation failed" in result.stdout

    def test_run_bpmn_workflow_execution_failure(self, simple_bpmn):
        """Test BPMN workflow execution failure."""
        with patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span:

            mock_validate.return_value = True
            mock_run.side_effect = Exception("Workflow execution failed")
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["run", str(simple_bpmn)])

            assert result.exit_code == 1
            assert "Workflow execution failed" in result.stdout

    def test_validate_workflow_success(self, simple_bpmn):
        """Test successful workflow validation."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.core.instrumentation.add_span_event") as mock_event:

            mock_validate.return_value = True
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["validate", str(simple_bpmn)])

            assert result.exit_code == 0
            assert "BPMN validation passed" in result.stdout
            mock_validate.assert_called_once_with(simple_bpmn)

    def test_validate_workflow_failure(self, invalid_bpmn):
        """Test workflow validation failure."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span:

            mock_validate.return_value = False
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["validate", str(invalid_bpmn)])

            assert result.exit_code == 1
            assert "BPMN validation failed" in result.stdout

    def test_validate_workflow_detailed(self, simple_bpmn):
        """Test detailed workflow validation."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span:

            mock_validate.return_value = True
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["validate", str(simple_bpmn), "--detailed"])

            assert result.exit_code == 0
            assert "Validation Details" in result.stdout

    def test_test_workflow_success(self, simple_bpmn):
        """Test workflow testing command."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._test_otel_integration") as mock_otel:

            # Setup mocks
            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "duration_seconds": 1.0,
                "steps_executed": 2,
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "workflow_name": "test"
            }
            mock_otel.return_value = {"status": "passed", "message": "OTEL working"}
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["test", str(simple_bpmn)])

            assert result.exit_code == 0
            assert "Test Results" in result.stdout
            assert "PASSED" in result.stdout

    def test_test_workflow_with_export(self, simple_bpmn):
        """Test workflow testing with result export."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._test_otel_integration") as mock_otel:

            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "duration_seconds": 1.0,
                "steps_executed": 2,
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "workflow_name": "test"
            }
            mock_otel.return_value = {"status": "passed", "message": "OTEL working"}
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["test", str(simple_bpmn), "--export"])

            assert result.exit_code == 0
            assert "exported to" in result.stdout

            # Check if export file was created
            export_file = simple_bpmn.with_suffix(".test-results.json")
            assert export_file.exists()
            export_file.unlink()  # Cleanup

    def test_parse_workflow_success(self, simple_bpmn):
        """Test workflow parsing command."""
        with patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._parse_workflow_structure") as mock_parse:

            mock_parse.return_value = {
                "file": "test.bpmn",
                "processes": [{"id": "process1", "name": "Test Process", "tasks": 3}],
                "elements": [
                    {"id": "start", "name": "Start", "type": "StartEvent", "process": "process1"},
                    {"id": "task", "name": "Task", "type": "ServiceTask", "process": "process1"},
                    {"id": "end", "name": "End", "type": "EndEvent", "process": "process1"}
                ]
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["parse", str(simple_bpmn)])

            assert result.exit_code == 0
            assert "Workflow Structure" in result.stdout
            mock_parse.assert_called_once_with(simple_bpmn)

    def test_parse_workflow_json_format(self, simple_bpmn):
        """Test workflow parsing with JSON output format."""
        with patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._parse_workflow_structure") as mock_parse:

            mock_parse.return_value = {
                "file": "test.bpmn",
                "processes": [],
                "elements": []
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["parse", str(simple_bpmn), "--format", "json"])

            assert result.exit_code == 0
            # Should output JSON format
            assert '"file": "test.bpmn"' in result.stdout

    def test_workflow_stats_success(self, simple_bpmn):
        """Test workflow statistics command."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._get_file_statistics") as mock_file_stats, \
             patch("uvmgr.commands.agent._get_workflow_statistics") as mock_wf_stats, \
             patch("uvmgr.commands.agent._get_telemetry_statistics") as mock_tel_stats:

            # Setup mocks
            mock_validate.return_value = True
            mock_file_stats.return_value = {
                "name": "test.bpmn",
                "size": 1024,
                "modified": 1234567890,
                "readable": True
            }
            mock_wf_stats.return_value = {
                "processes": [{"id": "process1", "name": "Test", "tasks": 3}],
                "total_tasks": 3,
                "valid": True
            }
            mock_tel_stats.return_value = {
                "otel_enabled": True,
                "spans_created": True,
                "metrics_recorded": True,
                "semantic_conventions": True
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["stats", str(simple_bpmn)])

            assert result.exit_code == 0
            assert "Workflow Statistics" in result.stdout
            assert "File" in result.stdout
            assert "Workflow" in result.stdout
            assert "Telemetry" in result.stdout

    def test_workflow_stats_invalid_workflow(self, invalid_bpmn):
        """Test workflow statistics with invalid workflow."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._get_file_statistics") as mock_file_stats:

            mock_validate.return_value = False
            mock_file_stats.return_value = {
                "name": "invalid.bpmn",
                "size": 100,
                "modified": 1234567890,
                "readable": True
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["stats", str(invalid_bpmn)])

            assert result.exit_code == 0
            assert "Workflow Statistics" in result.stdout
            assert "Valid" in result.stdout
            assert "❌ No" in result.stdout

    def test_workflow_stats_no_telemetry(self, simple_bpmn):
        """Test workflow statistics without telemetry."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._get_file_statistics") as mock_file_stats, \
             patch("uvmgr.commands.agent._get_workflow_statistics") as mock_wf_stats:

            mock_validate.return_value = True
            mock_file_stats.return_value = {
                "name": "test.bpmn",
                "size": 1024,
                "modified": 1234567890,
                "readable": True
            }
            mock_wf_stats.return_value = {
                "processes": [],
                "total_tasks": 0,
                "valid": True
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["stats", str(simple_bpmn), "--no-telemetry"])

            assert result.exit_code == 0
            assert "Workflow Statistics" in result.stdout
            assert "Telemetry" not in result.stdout


class TestWorkflowHelperFunctions:
    """Test workflow helper functions."""

    def test_display_execution_results(self):
        """Test execution results display."""
        stats = {
            "status": "completed",
            "duration_seconds": 1.5,
            "steps_executed": 3,
            "total_tasks": 4,
            "completed_tasks": 4,
            "failed_tasks": 0,
            "workflow_name": "test"
        }
        
        # Should not raise any exceptions
        _display_execution_results(stats, 1.5, False)
        _display_execution_results(stats, 1.5, True)

    def test_display_validation_details(self, tmp_path):
        """Test validation details display."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("test content")
        
        # Should not raise any exceptions
        _display_validation_details(test_file, True, 0.5)
        _display_validation_details(test_file, False, 0.5)

    def test_test_otel_integration(self, tmp_path):
        """Test OTEL integration testing."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("test content")
        
        with patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.core.instrumentation.add_span_event") as mock_event, \
             patch("uvmgr.core.telemetry.metric_counter") as mock_counter, \
             patch("uvmgr.core.telemetry.metric_histogram") as mock_histogram:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_event.return_value = None
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()

            result = _test_otel_integration(test_file)
            
            assert "status" in result
            assert result["status"] == "passed"

    def test_display_test_results(self):
        """Test test results display."""
        results = {
            "workflow": "test.bpmn",
            "iterations": 1,
            "tests": {
                "bpmn_validation": {"status": "passed", "message": "Valid"},
                "execution": {"status": "passed", "message": "Completed"},
                "otel_integration": {"status": "passed", "message": "Working"}
            }
        }
        
        # Should not raise any exceptions
        _display_test_results(results, 1.5)

    def test_get_file_statistics(self, tmp_path):
        """Test file statistics retrieval."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("test content")
        
        stats = _get_file_statistics(test_file)
        
        assert stats["name"] == "test.bpmn"
        assert stats["size"] > 0
        assert stats["readable"] is True
        assert "modified" in stats

    def test_get_workflow_statistics_success(self, tmp_path):
        """Test workflow statistics retrieval."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="test">
  <bpmn:process id="test_process" isExecutable="true">
    <bpmn:startEvent id="start"/>
  </bpmn:process>
</bpmn:definitions>""")
        
        stats = _get_workflow_statistics(test_file)
        
        assert "valid" in stats
        assert stats["valid"] is True

    def test_get_workflow_statistics_invalid(self, tmp_path):
        """Test workflow statistics with invalid file."""
        test_file = tmp_path / "invalid.bpmn"
        test_file.write_text("invalid content")
        
        stats = _get_workflow_statistics(test_file)
        
        assert "valid" in stats
        assert stats["valid"] is False

    def test_get_telemetry_statistics(self):
        """Test telemetry statistics retrieval."""
        stats = _get_telemetry_statistics(Path("test.bpmn"))
        
        assert "otel_enabled" in stats
        assert "spans_created" in stats
        assert "metrics_recorded" in stats
        assert "semantic_conventions" in stats

    def test_display_workflow_statistics(self):
        """Test workflow statistics display."""
        file_stats = {
            "name": "test.bpmn",
            "size": 1024,
            "modified": 1234567890,
            "readable": True
        }
        workflow_stats = {
            "processes": [],
            "total_tasks": 0,
            "valid": True
        }
        telemetry_stats = {
            "otel_enabled": True,
            "spans_created": True,
            "metrics_recorded": True,
            "semantic_conventions": True
        }
        
        # Should not raise any exceptions
        _display_workflow_statistics(file_stats, workflow_stats, telemetry_stats)
        _display_workflow_statistics(file_stats, None, None)
        _display_workflow_statistics(file_stats, workflow_stats, None)

    def test_parse_workflow_structure(self, tmp_path):
        """Test workflow structure parsing."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="test">
  <bpmn:process id="test_process" isExecutable="true">
    <bpmn:startEvent id="start" name="Start"/>
    <bpmn:serviceTask id="task" name="Task"/>
    <bpmn:endEvent id="end" name="End"/>
  </bpmn:process>
</bpmn:definitions>""")
        
        structure = _parse_workflow_structure(test_file)
        
        assert "file" in structure
        assert "processes" in structure
        assert "elements" in structure
        assert len(structure["processes"]) > 0
        assert len(structure["elements"]) > 0


class TestWorkflowErrorHandling:
    """Test workflow error handling scenarios."""

    def test_missing_file(self, runner):
        """Test handling of missing file."""
        result = runner.invoke(agent_app, ["run", "nonexistent.bpmn"])
        assert result.exit_code != 0

    def test_invalid_file_format(self, tmp_path):
        """Test handling of invalid file format."""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not bpmn content")
        
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate:
            mock_validate.return_value = False
            
            result = runner.invoke(agent_app, ["validate", str(invalid_file)])
            assert result.exit_code == 1

    def test_parse_error_handling(self, tmp_path):
        """Test parsing error handling."""
        invalid_file = tmp_path / "invalid.bpmn"
        invalid_file.write_text("invalid xml")
        
        with patch("uvmgr.commands.agent._parse_workflow_structure") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            
            result = runner.invoke(agent_app, ["parse", str(invalid_file)])
            assert result.exit_code == 1

    def test_otel_integration_error(self, tmp_path):
        """Test OTEL integration error handling."""
        test_file = tmp_path / "test.bpmn"
        test_file.write_text("test content")
        
        with patch("uvmgr.core.telemetry.span") as mock_span:
            mock_span.side_effect = Exception("OTEL error")
            
            result = _test_otel_integration(test_file)
            assert result["status"] == "failed"
            assert "OTEL error" in result["message"]


class TestWorkflowIntegration:
    """Integration tests for workflow functionality."""

    def test_end_to_end_workflow_execution(self, simple_bpmn):
        """Test complete end-to-end workflow execution."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.core.instrumentation.add_span_event") as mock_event, \
             patch("uvmgr.core.telemetry.metric_counter") as mock_counter, \
             patch("uvmgr.core.telemetry.metric_histogram") as mock_histogram:

            # Setup comprehensive mocks
            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "duration_seconds": 2.0,
                "steps_executed": 5,
                "total_tasks": 6,
                "completed_tasks": 6,
                "failed_tasks": 0,
                "workflow_name": "integration_test"
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_event.return_value = None
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()

            # Execute workflow
            result = runner.invoke(agent_app, ["run", str(simple_bpmn), "--verbose"])

            # Verify execution
            assert result.exit_code == 0
            assert "Executing workflow" in result.stdout
            assert "completed" in result.stdout

            # Verify telemetry calls
            assert mock_span.call_count >= 1
            assert mock_event.call_count >= 2
            assert mock_counter.call_count >= 1
            assert mock_histogram.call_count >= 1

    def test_workflow_testing_comprehensive(self, simple_bpmn):
        """Test comprehensive workflow testing."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.runtime.agent.spiff.run_bpmn") as mock_run, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._test_otel_integration") as mock_otel:

            # Setup mocks for comprehensive testing
            mock_validate.return_value = True
            mock_run.return_value = {
                "status": "completed",
                "duration_seconds": 1.0,
                "steps_executed": 3,
                "total_tasks": 4,
                "completed_tasks": 4,
                "failed_tasks": 0,
                "workflow_name": "test"
            }
            mock_otel.return_value = {"status": "passed", "message": "OTEL working"}
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            # Test with multiple iterations
            result = runner.invoke(agent_app, ["test", str(simple_bpmn), "--iterations", "3"])

            assert result.exit_code == 0
            assert "Test Results" in result.stdout
            assert "PASSED" in result.stdout

            # Verify multiple execution calls
            assert mock_run.call_count == 3

    def test_workflow_statistics_comprehensive(self, simple_bpmn):
        """Test comprehensive workflow statistics."""
        with patch("uvmgr.runtime.agent.spiff.validate_bpmn_file") as mock_validate, \
             patch("uvmgr.core.telemetry.span") as mock_span, \
             patch("uvmgr.commands.agent._get_file_statistics") as mock_file_stats, \
             patch("uvmgr.commands.agent._get_workflow_statistics") as mock_wf_stats, \
             patch("uvmgr.commands.agent._get_telemetry_statistics") as mock_tel_stats:

            # Setup comprehensive statistics
            mock_validate.return_value = True
            mock_file_stats.return_value = {
                "name": "comprehensive.bpmn",
                "size": 2048,
                "modified": 1234567890,
                "readable": True
            }
            mock_wf_stats.return_value = {
                "processes": [
                    {"id": "process1", "name": "Main Process", "tasks": 5},
                    {"id": "process2", "name": "Sub Process", "tasks": 3}
                ],
                "total_tasks": 8,
                "valid": True
            }
            mock_tel_stats.return_value = {
                "otel_enabled": True,
                "spans_created": True,
                "metrics_recorded": True,
                "semantic_conventions": True
            }
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            result = runner.invoke(agent_app, ["stats", str(simple_bpmn)])

            assert result.exit_code == 0
            assert "Workflow Statistics" in result.stdout
            assert "File" in result.stdout
            assert "Workflow" in result.stdout
            assert "Telemetry" in result.stdout
            assert "Main Process" in result.stdout
            assert "8" in result.stdout  # Total tasks


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"]) 