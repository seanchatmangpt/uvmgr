"""Unit tests for core SpiffWorkflow functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from uvmgr.runtime.agent.spiff import (
    _load,
    _step,
    _process_task,
    run_bpmn,
    get_workflow_stats,
    validate_bpmn_file
)


class TestSpiffCoreFunctions:
    """Test core SpiffWorkflow functions."""

    @pytest.fixture
    def valid_bpmn_content(self):
        """Valid BPMN content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="test_workflow"
                  targetNamespace="http://example.com/test">
  <bpmn:process id="test_process" isExecutable="true">
    <bpmn:startEvent id="start" name="Start">
      <bpmn:outgoing>flow1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="flow1" sourceRef="start" targetRef="task1"/>
    <bpmn:serviceTask id="task1" name="Test Task">
      <bpmn:incoming>flow1</bpmn:incoming>
      <bpmn:outgoing>flow2</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="flow2" sourceRef="task1" targetRef="end"/>
    <bpmn:endEvent id="end" name="End">
      <bpmn:incoming>flow2</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""

    @pytest.fixture
    def mock_workflow(self):
        """Mock BPMN workflow for testing."""
        workflow = MagicMock()
        workflow.spec.name = "test_workflow"
        workflow.is_completed.return_value = False
        workflow.get_next_task.return_value = None
        return workflow

    @pytest.fixture
    def mock_task(self):
        """Mock workflow task for testing."""
        task = MagicMock()
        task.id = "task_1"
        task.task_spec.name = "Test Task"
        task.task_spec.script = None
        task.state = "READY"
        return task

    def test_load_valid_bpmn(self, valid_bpmn_content):
        """Test loading valid BPMN workflow."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.add_span_attributes") as mock_attrs, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write(valid_bpmn_content)
                bpmn_path = Path(f.name)

            try:
                workflow = _load(bpmn_path)
                
                # Verify workflow was created
                assert workflow is not None
                assert hasattr(workflow, 'spec')
                
                # Verify OTEL instrumentation was called
                mock_span.assert_called_with("workflow.load", definition_path=str(bpmn_path))
                mock_event.assert_called()
                mock_attrs.assert_called()
                mock_counter.assert_called_with("workflow.instances.created")
                
            finally:
                bpmn_path.unlink()

    def test_load_invalid_bpmn(self):
        """Test loading invalid BPMN workflow."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write("invalid xml content")
                bpmn_path = Path(f.name)

            try:
                with pytest.raises(Exception):
                    _load(bpmn_path)
                    
                # Verify error event was recorded
                mock_event.assert_called()
                
            finally:
                bpmn_path.unlink()

    def test_step_with_ready_task(self, mock_workflow, mock_task):
        """Test workflow step with ready task."""
        mock_workflow.get_next_task.return_value = mock_task
        
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.add_span_attributes") as mock_attrs, \
             patch("uvmgr.runtime.agent.spiff.metric_histogram") as mock_histogram, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter, \
             patch("uvmgr.runtime.agent.spiff._process_task") as mock_process:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_histogram.return_value = MagicMock()
            mock_counter.return_value = MagicMock()

            _step(mock_workflow)

            # Verify task was processed
            mock_process.assert_called_once_with(mock_workflow, mock_task, "service")
            
            # Verify OTEL instrumentation
            mock_span.assert_called_with("workflow.step")
            mock_event.assert_called()
            mock_attrs.assert_called()
            mock_histogram.assert_called()
            mock_counter.assert_called()

    def test_step_with_no_ready_task(self, mock_workflow):
        """Test workflow step with no ready task."""
        mock_workflow.get_next_task.return_value = None
        
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.add_span_attributes") as mock_attrs, \
             patch("uvmgr.runtime.agent.spiff.metric_histogram") as mock_histogram, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_histogram.return_value = MagicMock()
            mock_counter.return_value = MagicMock()

            _step(mock_workflow)

            # Verify no task processing occurred
            mock_event.assert_called_with("workflow.step.no_tasks", {"workflow_completed": False})
            
            # Verify metrics were still recorded
            mock_attrs.assert_called()
            mock_histogram.assert_called()
            mock_counter.assert_called()

    def test_process_task_service(self, mock_workflow, mock_task):
        """Test processing service task."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.metric_histogram") as mock_histogram, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter, \
             patch("uvmgr.runtime.agent.spiff.colour") as mock_colour:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_histogram.return_value = MagicMock()
            mock_counter.return_value = MagicMock()

            _process_task(mock_workflow, mock_task, "service")

            # Verify task was completed
            mock_task.complete.assert_called_once()
            
            # Verify OTEL instrumentation
            mock_span.assert_called_with(
                "workflow.task.service",
                task_name="Test Task",
                task_type="service",
                task_id="task_1"
            )
            mock_event.assert_called()
            mock_histogram.assert_called()
            mock_counter.assert_called()
            mock_colour.assert_called()

    def test_process_task_script(self, mock_workflow, mock_task):
        """Test processing script task."""
        mock_task.task_spec.script = "print('hello')"
        
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.metric_histogram") as mock_histogram, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter, \
             patch("uvmgr.runtime.agent.spiff.colour") as mock_colour:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_histogram.return_value = MagicMock()
            mock_counter.return_value = MagicMock()

            _process_task(mock_workflow, mock_task, "script")

            # Verify task was completed
            mock_task.complete.assert_called_once()
            
            # Verify script task handling
            mock_span.assert_called_with(
                "workflow.task.script",
                task_name="Test Task",
                task_type="script",
                task_id="task_1"
            )

    def test_process_task_error(self, mock_workflow, mock_task):
        """Test processing task with error."""
        mock_task.complete.side_effect = Exception("Task failed")
        
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()

            with pytest.raises(Exception, match="Task failed"):
                _process_task(mock_workflow, mock_task, "service")

            # Verify error was recorded
            mock_event.assert_called_with("task.failed", {
                "task_name": "Test Task",
                "error": "Task failed"
            })
            mock_counter.assert_called_with("workflow.task.service.failed")

    def test_run_bpmn_success(self, valid_bpmn_content):
        """Test successful BPMN workflow execution."""
        with patch("uvmgr.runtime.agent.spiff._load") as mock_load, \
             patch("uvmgr.runtime.agent.spiff._step") as mock_step, \
             patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event, \
             patch("uvmgr.runtime.agent.spiff.metric_counter") as mock_counter, \
             patch("uvmgr.runtime.agent.spiff.metric_histogram") as mock_histogram:

            mock_workflow = MagicMock()
            mock_workflow.is_completed.side_effect = [False, False, True]
            mock_workflow.get_next_task.return_value = MagicMock()
            mock_load.return_value = mock_workflow

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write(valid_bpmn_content)
                bpmn_path = Path(f.name)

            try:
                result = run_bpmn(bpmn_path)

                # Verify workflow was executed
                assert result["status"] == "completed"
                assert result["steps_executed"] > 0
                assert result["duration_seconds"] > 0
                
                # Verify OTEL instrumentation
                mock_span.assert_called()
                mock_event.assert_called()
                mock_counter.assert_called()
                mock_histogram.assert_called()
                
            finally:
                bpmn_path.unlink()

    def test_run_bpmn_infinite_loop_detection(self, valid_bpmn_content):
        """Test infinite loop detection in workflow execution."""
        with patch("uvmgr.runtime.agent.spiff._load") as mock_load, \
             patch("uvmgr.runtime.agent.spiff._step") as mock_step, \
             patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event:

            mock_workflow = MagicMock()
            mock_workflow.is_completed.return_value = False
            mock_workflow.get_next_task.return_value = MagicMock()
            mock_workflow.get_tasks.return_value = [MagicMock()]
            mock_load.return_value = mock_workflow

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write(valid_bpmn_content)
                bpmn_path = Path(f.name)

            try:
                result = run_bpmn(bpmn_path)

                # Verify infinite loop was detected
                assert result["status"] == "stopped"
                assert "infinite_loop" in result.get("reason", "")
                
                # Verify loop detection event was recorded
                mock_event.assert_called()
                
            finally:
                bpmn_path.unlink()

    def test_get_workflow_stats(self, mock_workflow):
        """Test workflow statistics collection."""
        mock_workflow.spec.name = "test_workflow"
        mock_workflow.is_completed.return_value = True
        
        mock_task1 = MagicMock()
        mock_task1.state = "COMPLETED"
        mock_task2 = MagicMock()
        mock_task2.state = "FAILED"
        
        mock_workflow.get_tasks.return_value = [mock_task1, mock_task2]

        stats = get_workflow_stats(mock_workflow)

        # Verify statistics
        assert stats["workflow_name"] == "test_workflow"
        assert stats["is_completed"] is True
        assert stats["total_tasks"] == 2
        assert stats["completed_tasks"] == 1
        assert stats["failed_tasks"] == 1

    def test_validate_bpmn_file_valid(self, valid_bpmn_content):
        """Test validation of valid BPMN file."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write(valid_bpmn_content)
                bpmn_path = Path(f.name)

            try:
                result = validate_bpmn_file(bpmn_path)
                assert result is True
                
                # Verify success event was recorded
                mock_event.assert_called_with("workflow.validation.success", {
                    "workflow_name": bpmn_path.stem,
                    "task_specs": 4  # start, service, end, plus implicit
                })
                
            finally:
                bpmn_path.unlink()

    def test_validate_bpmn_file_invalid(self):
        """Test validation of invalid BPMN file."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".bpmn", delete=False) as f:
                f.write("invalid xml content")
                bpmn_path = Path(f.name)

            try:
                result = validate_bpmn_file(bpmn_path)
                assert result is False
                
                # Verify failure event was recorded
                mock_event.assert_called_with("workflow.validation.failed", {
                    "error": mock_event.call_args[0][1]["error"],
                    "file_path": str(bpmn_path),
                })
                
            finally:
                bpmn_path.unlink()

    def test_validate_bpmn_file_nonexistent(self):
        """Test validation of nonexistent BPMN file."""
        with patch("uvmgr.runtime.agent.spiff.span") as mock_span, \
             patch("uvmgr.runtime.agent.spiff.add_span_event") as mock_event:

            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)

            nonexistent_path = Path("/nonexistent/file.bpmn")
            result = validate_bpmn_file(nonexistent_path)
            
            assert result is False
            
            # Verify failure event was recorded
            mock_event.assert_called_with("workflow.validation.failed", {
                "error": mock_event.call_args[0][1]["error"],
                "file_path": str(nonexistent_path),
            }) 