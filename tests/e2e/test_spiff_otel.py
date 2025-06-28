"""E2E tests for SpiffWorkflow with OTEL instrumentation."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file, get_workflow_stats


class TestSpiffWorkflowOTEL:
    """Test SpiffWorkflow execution with OTEL instrumentation."""
    
    @pytest.fixture
    def simple_bpmn(self):
        """Create a simple BPMN workflow for testing."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False) as f:
            f.write(bpmn_content)
            return Path(f.name)
    
    @pytest.fixture
    def complex_bpmn(self):
        """Create a more complex BPMN workflow with user tasks."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="complex_workflow"
                  targetNamespace="http://example.com/complex">
  
  <bpmn:process id="complex_process" isExecutable="true">
    <bpmn:startEvent id="start" name="Start">
      <bpmn:outgoing>flow1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:sequenceFlow id="flow1" sourceRef="start" targetRef="validate"/>
    
    <bpmn:serviceTask id="validate" name="Validate Input">
      <bpmn:incoming>flow1</bpmn:incoming>
      <bpmn:outgoing>flow2</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="flow2" sourceRef="validate" targetRef="review"/>
    
    <bpmn:userTask id="review" name="Manual Review">
      <bpmn:incoming>flow2</bpmn:incoming>
      <bpmn:outgoing>flow3</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:sequenceFlow id="flow3" sourceRef="review" targetRef="process"/>
    
    <bpmn:serviceTask id="process" name="Process Request">
      <bpmn:incoming>flow3</bpmn:incoming>
      <bpmn:outgoing>flow4</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="flow4" sourceRef="process" targetRef="end"/>
    
    <bpmn:endEvent id="end" name="End">
      <bpmn:incoming>flow4</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False) as f:
            f.write(bpmn_content)
            return Path(f.name)

    def test_simple_workflow_execution(self, simple_bpmn):
        """Test simple workflow execution with OTEL instrumentation."""
        
        # Mock telemetry components to capture calls
        with patch('uvmgr.core.telemetry.span') as mock_span, \
             patch('uvmgr.core.telemetry.metric_counter') as mock_counter, \
             patch('uvmgr.core.telemetry.metric_histogram') as mock_histogram:
            
            # Mock span context manager
            mock_span_instance = MagicMock()
            mock_span.return_value.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            
            # Mock metric functions
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()
            
            # Execute workflow
            stats = run_bpmn(simple_bpmn)
            
            # Verify execution results
            assert stats["status"] == "completed"
            assert stats["workflow_name"] == simple_bpmn.stem
            assert stats["completed_tasks"] > 0
            assert stats["duration_seconds"] > 0
            
            # Verify OTEL instrumentation was called
            assert mock_span.call_count >= 3  # workflow.execute, workflow.load, workflow.step
            assert mock_counter.call_count >= 2  # instance created, execution completed
            assert mock_histogram.call_count >= 1  # execution duration
    
    @patch('builtins.input', return_value='')  # Auto-complete user tasks
    def test_complex_workflow_with_user_tasks(self, mock_input, complex_bpmn):
        """Test complex workflow with user tasks and OTEL instrumentation."""
        
        with patch('uvmgr.core.telemetry.span') as mock_span, \
             patch('uvmgr.core.instrumentation.add_span_event') as mock_event, \
             patch('uvmgr.core.instrumentation.add_span_attributes') as mock_attrs:
            
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            
            stats = run_bpmn(complex_bpmn)
            
            # Verify workflow completion
            assert stats["status"] == "completed"
            assert stats["steps_executed"] >= 3  # At least validate, review, process
            
            # Verify user task instrumentation
            mock_event.assert_any_call("workflow.user_tasks.found", {"count": 1})
            mock_event.assert_any_call("task.started", {
                "task_name": "Manual Review",
                "task_type": "user",
                "task_state": "Task.READY"
            })
    
    def test_workflow_validation(self, simple_bpmn):
        """Test BPMN file validation with telemetry."""
        
        with patch('uvmgr.core.telemetry.span') as mock_span, \
             patch('uvmgr.core.instrumentation.add_span_event') as mock_event:
            
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            
            # Test valid file
            result = validate_bpmn_file(simple_bpmn)
            assert result is True
            
            mock_event.assert_called_with("workflow.validation.success", {
                "workflow_name": simple_bpmn.stem,
                "task_specs": 4  # start, service, end, plus implicit
            })
    
    def test_invalid_bpmn_validation(self):
        """Test validation of invalid BPMN file."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False) as f:
            f.write("invalid xml content")
            invalid_file = Path(f.name)
        
        with patch('uvmgr.core.instrumentation.add_span_event') as mock_event:
            result = validate_bpmn_file(invalid_file)
            assert result is False
            
            # Verify failure event
            mock_event.assert_called_with("workflow.validation.failed", {
                "error": mock_event.call_args[0][1]["error"],
                "file_path": str(invalid_file),
            })
    
    def test_workflow_metrics_collection(self, simple_bpmn):
        """Test that workflow metrics are properly collected."""
        
        metrics_captured = []
        
        def capture_metric(name):
            def metric_func(value):
                metrics_captured.append((name, value))
            return metric_func
        
        with patch('uvmgr.core.telemetry.metric_counter', side_effect=capture_metric), \
             patch('uvmgr.core.telemetry.metric_histogram', side_effect=capture_metric):
            
            run_bpmn(simple_bpmn)
            
            # Verify expected metrics were recorded
            metric_names = [name for name, _ in metrics_captured]
            assert "workflow.instances.created" in metric_names
            assert "workflow.executions.completed" in metric_names
            assert "workflow.execution.duration" in metric_names
    
    def test_workflow_error_handling(self):
        """Test workflow execution error handling with telemetry."""
        
        # Create an invalid workflow file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False) as f:
            f.write("<?xml version='1.0'?><invalid>content</invalid>")
            invalid_file = Path(f.name)
        
        with patch('uvmgr.core.instrumentation.add_span_event') as mock_event:
            with pytest.raises(Exception):
                run_bpmn(invalid_file)
            
            # Verify error event was recorded
            error_events = [call for call in mock_event.call_args_list 
                          if 'failed' in str(call)]
            assert len(error_events) > 0
    
    def test_workflow_statistics_accuracy(self, simple_bpmn):
        """Test workflow statistics are accurate."""
        
        # Mock input for any user tasks
        with patch('builtins.input', return_value=''):
            stats = run_bpmn(simple_bpmn)
        
        # Verify all required statistics are present
        required_keys = [
            "status", "duration_seconds", "steps_executed", 
            "total_tasks", "completed_tasks", "failed_tasks", "workflow_name"
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing statistic: {key}"
        
        # Verify statistics make sense
        assert stats["duration_seconds"] > 0
        assert stats["completed_tasks"] >= 0
        assert stats["failed_tasks"] >= 0
        assert stats["total_tasks"] >= stats["completed_tasks"]


class TestSpiffWorkflowE2E:
    """End-to-end tests for complete workflow scenarios."""
    
    def test_ci_validation_workflow(self, tmp_path):
        """Test a CI validation workflow with full OTEL tracing."""
        # Create a CI validation BPMN workflow
        ci_bpmn = tmp_path / "ci_validation.bpmn"
        ci_bpmn.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="ci_validation"
                  targetNamespace="http://uvmgr.com/ci">
  
  <bpmn:process id="ci_process" isExecutable="true">
    <bpmn:startEvent id="start" name="Code Push">
      <bpmn:outgoing>to_lint</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:sequenceFlow id="to_lint" sourceRef="start" targetRef="lint"/>
    
    <bpmn:serviceTask id="lint" name="Code Linting">
      <bpmn:incoming>to_lint</bpmn:incoming>
      <bpmn:outgoing>to_test</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="to_test" sourceRef="lint" targetRef="test"/>
    
    <bpmn:serviceTask id="test" name="Run Tests">
      <bpmn:incoming>to_test</bpmn:incoming>
      <bpmn:outgoing>to_build</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="to_build" sourceRef="test" targetRef="build"/>
    
    <bpmn:serviceTask id="build" name="Build Package">
      <bpmn:incoming>to_build</bpmn:incoming>
      <bpmn:outgoing>to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:sequenceFlow id="to_end" sourceRef="build" targetRef="end"/>
    
    <bpmn:endEvent id="end" name="CI Complete">
      <bpmn:incoming>to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
""")
        
        
        # Capture all span and event calls
        spans_created = []
        events_recorded = []
        
        def capture_span(name, **kwargs):
            spans_created.append((name, kwargs))
            mock = MagicMock()
            mock.__enter__ = MagicMock(return_value=mock)
            mock.__exit__ = MagicMock(return_value=None)
            return mock
        
        def capture_event(name, attrs=None):
            events_recorded.append((name, attrs or {}))
        
        with patch('uvmgr.core.telemetry.span', side_effect=capture_span), \
             patch('uvmgr.core.instrumentation.add_span_event', side_effect=capture_event):
            
            stats = run_bpmn(ci_bpmn)
            
            # Verify workflow completed successfully
            assert stats["status"] == "completed"
            assert stats["workflow_name"] == "ci_validation"
            assert stats["completed_tasks"] >= 4  # lint, test, build, end
            
            # Verify comprehensive tracing
            span_names = [name for name, _ in spans_created]
            assert "workflow.execute" in span_names
            assert "workflow.load" in span_names
            assert "workflow.step" in span_names
            
            # Verify workflow events
            event_names = [name for name, _ in events_recorded]
            assert "workflow.execution.started" in event_names
            assert "workflow.execution.completed" in event_names
            assert "task.started" in event_names
            assert "task.completed" in event_names
    
    def test_8020_otel_validation(self, simple_bpmn):
        """Test 80/20 principle: validate the most critical OTEL features."""
        
        # Critical OTEL features to validate (80% of value)
        critical_features = {
            "spans_created": False,
            "metrics_recorded": False, 
            "semantic_conventions": False,
            "error_handling": False,
            "performance_tracking": False
        }
        
        with patch('uvmgr.core.telemetry.span') as mock_span, \
             patch('uvmgr.core.telemetry.metric_counter') as mock_counter, \
             patch('uvmgr.core.telemetry.metric_histogram') as mock_histogram, \
             patch('uvmgr.core.instrumentation.add_span_attributes') as mock_attrs:
            
            # Setup mocks
            mock_span.return_value.__enter__ = MagicMock()
            mock_span.return_value.__exit__ = MagicMock(return_value=None)
            mock_counter.return_value = MagicMock()
            mock_histogram.return_value = MagicMock()
            
            # Execute workflow
            stats = run_bpmn(simple_bpmn)
            
            # Validate critical features
            if mock_span.call_count > 0:
                critical_features["spans_created"] = True
            
            if mock_counter.call_count > 0 or mock_histogram.call_count > 0:
                critical_features["metrics_recorded"] = True
            
            # Check semantic conventions usage
            span_calls = [call for call in mock_span.call_args_list]
            for call in span_calls:
                if "workflow.execute" in str(call):
                    critical_features["semantic_conventions"] = True
                    break
            
            # Check performance tracking
            if mock_histogram.call_count > 0:
                critical_features["performance_tracking"] = True
            
            # Verify error handling capability
            try:
                # This should work without throwing unexpected errors
                validate_bpmn_file(simple_bpmn)
                critical_features["error_handling"] = True
            except Exception:
                pass
            
            # Assert all critical features are working (80/20 validation)
            failed_features = [k for k, v in critical_features.items() if not v]
            assert len(failed_features) == 0, f"Critical OTEL features failed: {failed_features}"
            
            # Verify workflow execution was successful
            assert stats["status"] == "completed"
            
            print(f"✓ 8020 OTEL Validation PASSED")
            print(f"  - Spans created: {mock_span.call_count}")
            print(f"  - Counters: {mock_counter.call_count}")
            print(f"  - Histograms: {mock_histogram.call_count}")
            print(f"  - Attributes set: {mock_attrs.call_count}")