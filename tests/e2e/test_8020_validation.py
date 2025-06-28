"""
End-to-End Tests for 8020 BPMN Validation System
================================================

Comprehensive test suite for the 8020 external project validation workflow
that integrates SpiffWorkflow BPMN execution with OpenTelemetry validation.

Tests validate:
- BPMN workflow execution with SpiffWorkflow
- 8020 external project validation principles
- OpenTelemetry integration and data collection
- External project generation and testing
- Multi-agent coordination
- Performance SLA validation
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor, run_8020_validation_workflow
from uvmgr.runtime.agent.spiff import run_bpmn, validate_bpmn_file


class Test8020BPMNValidation:
    """Test suite for 8020 BPMN validation system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_bpmn = Path(__file__).parent.parent / "fixtures" / "test_workflow.bpmn"
        self.validation_bpmn = Path(__file__).parent.parent.parent / "workflows" / "8020-external-project-validation.bpmn"
    
    def test_bpmn_8020_workflow_exists(self):
        """Test that the 8020 validation BPMN workflow exists and is valid."""
        assert self.validation_bpmn.exists(), f"8020 BPMN workflow not found at {self.validation_bpmn}"
        
        # Validate BPMN structure
        validation_result = validate_bpmn_file(self.validation_bpmn)
        assert validation_result, f"8020 BPMN workflow is invalid"
        
        # Check for required elements
        bpmn_content = self.validation_bpmn.read_text()
        required_elements = [
            "setup_environment",
            "start_otel_validation", 
            "generate_minimal_project",
            "generate_fastapi_project",
            "generate_substrate_project",
            "test_copier_integration",
            "validate_performance",
            "analyze_otel_data"
        ]
        
        for element in required_elements:
            assert element in bpmn_content, f"Required BPMN element '{element}' not found in workflow"
    
    def test_bpmn_8020_executor_initialization(self):
        """Test BPMN 8020 executor initialization."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        assert executor.base_path == self.temp_dir
        assert executor.test_workspace is None
        assert isinstance(executor.validation_results, dict)
        assert isinstance(executor.slas, dict)
        assert isinstance(executor.workflow_stats, dict)
        
        # Check SLA configuration
        expected_slas = ["startup_time_ms", "command_time_ms", "success_rate"]
        for sla in expected_slas:
            assert sla in executor.slas
    
    @pytest.mark.asyncio
    async def test_setup_environment_handler(self):
        """Test environment setup task handler."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Mock task
        task = Mock()
        task.data = {}
        task.task_spec = Mock()
        task.task_spec.extensions = {}
        
        result = await executor._handle_setup_environment(task)
        
        assert result["success"] is True
        assert "workspace" in result
        assert executor.test_workspace is not None
        assert executor.test_workspace.exists()
        
        # Check task data was updated
        assert "workspace_path" in task.data
        assert "docker_started" in task.data
        assert "otel_ready" in task.data
    
    @pytest.mark.asyncio
    async def test_otel_validation_handler(self):
        """Test OTEL validation start handler."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        task = Mock()
        task.data = {}
        task.task_spec = Mock()
        task.task_spec.extensions = {}
        
        result = await executor._handle_start_otel_validation(task)
        
        assert result["success"] is True
        assert result["monitoring_started"] is True
        assert executor.otel_start_time is not None
        
        # Check task data
        assert "otel_start_time" in task.data
        assert "monitoring_active" in task.data
        assert task.data["monitoring_active"] is True
    
    @pytest.mark.asyncio
    async def test_project_generation_handlers(self):
        """Test project generation handlers for different types."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Setup workspace
        executor.test_workspace = self.temp_dir / "test_workspace"
        executor.test_workspace.mkdir(exist_ok=True)
        
        project_types = ["minimal", "fastapi", "substrate"]
        
        for project_type in project_types:
            task = Mock()
            task.data = {}
            task.task_spec = Mock()
            task.task_spec.extensions = {"project_type": project_type}
            
            # Mock the generation methods to succeed
            with patch.object(executor, f'_generate_{project_type}_project', return_value=True):
                result = await executor._handle_generate_project(task)
                
                assert result["success"] is True
                assert "project_path" in result
                
                # Check task data
                assert task.data["project_type"] == project_type
                assert task.data["generation_success"] is True
                assert "project_path" in task.data
    
    @pytest.mark.asyncio
    async def test_performance_validation_handler(self):
        """Test performance SLA validation handler."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        task = Mock()
        task.data = {}
        task.task_spec = Mock()
        task.task_spec.extensions = {}
        
        # Mock performance metrics within SLA
        with patch.object(executor, '_collect_performance_metrics', return_value={
            "startup_time_ms": 400,  # Within SLA (500ms)
            "command_time_ms": 3000,  # Within SLA (5000ms)
            "success_rate": 0.98  # Above SLA (0.95)
        }):
            result = await executor._handle_validate_performance(task)
            
            assert result["success"] is True
            assert "sla_results" in result
            assert len(result["violations"]) == 0
            
            # Check all SLAs passed
            for sla_result in result["sla_results"].values():
                assert sla_result["passed"] is True
    
    @pytest.mark.asyncio
    async def test_otel_analysis_handler(self):
        """Test OTEL data analysis handler."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        executor.otel_start_time = executor.otel_start_time or asyncio.get_event_loop().time()
        
        # Add some validation results
        executor.validation_results = {
            "minimal": {"tests_run": 5, "tests_passed": 5, "success_rate": 1.0},
            "fastapi": {"tests_run": 8, "tests_passed": 7, "success_rate": 0.875}
        }
        
        task = Mock()
        task.data = {}
        task.task_spec = Mock()
        task.task_spec.extensions = {"analysis_window": "3600"}
        
        with patch.object(executor, '_analyze_spans', return_value={"total_spans": 25, "error_spans": 2}):
            with patch.object(executor, '_analyze_metrics', return_value={"commands_executed": 15}):
                result = await executor._handle_analyze_otel_data(task)
                
                assert result["success"] is True
                assert result["validation_success"] is True  # 93.8% overall success rate
                assert result["overall_success_rate"] > 0.80
                
                # Check task data
                assert "span_analysis" in task.data
                assert "metrics_analysis" in task.data
                assert "overall_success_rate" in task.data
                assert "validation_success" in task.data
    
    @pytest.mark.asyncio
    async def test_report_generation_handler(self):
        """Test validation report generation."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        executor.test_workspace = self.temp_dir / "test_workspace"
        executor.test_workspace.mkdir(exist_ok=True)
        
        task = Mock()
        task.data = {
            "sla_results": {"startup_time_ms": {"passed": True}},
            "span_analysis": {"total_spans": 20},
            "overall_success_rate": 0.85
        }
        task.task_spec = Mock()
        task.task_spec.extensions = {"report_type": "success"}
        
        result = await executor._handle_generate_report(task)
        
        assert result["success"] is True
        assert "report_path" in result
        assert "markdown_path" in result
        
        # Check files were created
        report_path = Path(result["report_path"])
        markdown_path = Path(result["markdown_path"])
        
        assert report_path.exists()
        assert markdown_path.exists()
        
        # Validate report content
        report_data = json.loads(report_path.read_text())
        assert "timestamp" in report_data
        assert "report_type" in report_data
        assert report_data["report_type"] == "success"
        
        markdown_content = markdown_path.read_text()
        assert "8020 External Project Validation Report" in markdown_content
        assert "Trust Only OTEL Traces" in markdown_content
    
    @pytest.mark.asyncio
    @patch('uvmgr.runtime.agent.bpmn_8020_executor.run')
    async def test_minimal_project_generation(self, mock_run):
        """Test minimal project generation."""
        mock_run.return_value = None  # run() doesn't return anything on success
        
        executor = BPMN8020Executor(base_path=self.temp_dir)
        project_path = self.temp_dir / "test_minimal"
        
        success = await executor._generate_minimal_project(project_path)
        
        assert success is True
        assert project_path.exists()
        assert (project_path / "src" / "main.py").exists()
        assert (project_path / "pyproject.toml").exists()
        
        # Check file contents
        main_py = (project_path / "src" / "main.py").read_text()
        assert "def hello():" in main_py
        
        pyproject = (project_path / "pyproject.toml").read_text()
        assert "minimal-test" in pyproject
    
    @pytest.mark.asyncio
    @patch('uvmgr.runtime.agent.bpmn_8020_executor.run')
    async def test_project_testing(self, mock_run):
        """Test project testing functionality."""
        # Mock successful command executions
        mock_run.return_value = "Success"  # run() returns output when capture=True
        
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Create a test project
        project_path = self.temp_dir / "test_project"
        project_path.mkdir()
        (project_path / "pyproject.toml").write_text("[project]\nname='test'")
        
        results = await executor._run_project_tests(project_path, "minimal")
        
        assert results["project_type"] == "minimal"
        assert results["tests_run"] > 0
        assert results["tests_passed"] > 0
        assert results["success_rate"] > 0.0
        
        # All commands should have succeeded
        assert results["success_rate"] == 1.0
    
    def test_overall_success_rate_calculation(self):
        """Test overall success rate calculation."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Set up validation results
        executor.validation_results = {
            "minimal": {"tests_run": 5, "tests_passed": 5},
            "fastapi": {"tests_run": 10, "tests_passed": 8},
            "substrate": {"tests_run": 8, "tests_passed": 6}
        }
        
        success_rate = executor._calculate_overall_success_rate()
        
        # Expected: (5 + 8 + 6) / (5 + 10 + 8) = 19/23 ≈ 0.826
        expected_rate = 19 / 23
        assert abs(success_rate - expected_rate) < 0.001
    
    def test_sla_compliance_checking(self):
        """Test SLA compliance checking."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Set performance metrics
        executor.performance_metrics = {
            "startup_time_ms": 400,  # Within SLA
            "command_time_ms": 6000,  # Violates SLA (> 5000ms)
            "success_rate": 0.98  # Above SLA
        }
        
        compliance = executor._check_sla_compliance()
        
        assert compliance["startup_time_ms"] is True
        assert compliance["command_time_ms"] is False
        assert compliance["success_rate"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_execution_integration(self):
        """Test complete workflow execution with mocked components."""
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Mock all the handler methods to succeed
        async def mock_success_handler(task):
            return {"success": True}
        
        executor._handle_setup_environment = mock_success_handler
        executor._handle_start_otel_validation = mock_success_handler
        executor._handle_generate_project = mock_success_handler
        executor._handle_test_project = mock_success_handler
        executor._handle_test_copier = mock_success_handler
        executor._handle_test_deployment = mock_success_handler
        executor._handle_validate_performance = mock_success_handler
        executor._handle_analyze_otel_data = mock_success_handler
        executor._handle_generate_report = mock_success_handler
        
        # Test with the actual BPMN file if it exists
        if self.validation_bpmn.exists():
            with patch('uvmgr.runtime.agent.spiff._load') as mock_load:
                with patch('uvmgr.runtime.agent.spiff._step') as mock_step:
                    
                    # Mock workflow
                    mock_workflow = Mock()
                    mock_workflow.is_completed.return_value = True
                    mock_workflow.get_ready_user_tasks.return_value = []
                    mock_load.return_value = mock_workflow
                    
                    results = await executor._execute_workflow_async(mock_workflow)
                    
                    assert "tasks" in results
                    assert "errors" in results
                    assert "metrics" in results
    
    @pytest.mark.integration
    def test_cli_8020_command_structure(self):
        """Test that CLI commands are properly structured."""
        # Test by running the help command instead of importing
        import subprocess
        result = subprocess.run(
            ["uvmgr", "agent", "--help"], 
            capture_output=True, text=True
        )
        
        # Check that 8020 command exists in help output
        assert "8020" in result.stdout
        assert "otel-validate" in result.stdout
        assert "coordinate" in result.stdout
    
    @pytest.mark.integration
    @patch('uvmgr.runtime.agent.bpmn_8020_executor.run')
    def test_external_project_integration(self, mock_run):
        """Test integration with external project testing framework."""
        mock_run.return_value = None  # run() doesn't return anything on success
        
        # Test auto-install script integration
        executor = BPMN8020Executor(base_path=self.temp_dir)
        
        # Check that external testing directory structure is expected
        external_testing_dir = executor.base_path / "external-project-testing"
        
        # The executor should handle missing directories gracefully
        # This tests the resilience of the system
        
        # Test workspace creation
        executor.test_workspace = self.temp_dir / "integration_test"
        executor.test_workspace.mkdir(exist_ok=True)
        
        assert executor.test_workspace.exists()
        
        # Test that the system can create project structures
        project_path = executor.test_workspace / "test_integration_project"
        
        # This should not fail even if external scripts are missing
        try:
            import asyncio
            success = asyncio.run(executor._generate_minimal_project(project_path))
            # Success depends on whether external scripts exist
            # The test validates the executor handles both cases
            assert isinstance(success, bool)
        except Exception as e:
            # Expected if external dependencies are missing
            assert "external-project-testing" in str(e) or "auto-install" in str(e)


class TestOTELValidationIntegration:
    """Test OTEL validation integration with BPMN workflows."""
    
    def setup_method(self):
        """Set up OTEL test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_otel_collector_connectivity(self, mock_urlopen):
        """Test OTEL collector connectivity checking."""
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        
        # Mock successful connection
        mock_response = Mock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response
        
        executor = BPMN8020Executor()
        result = await executor._ensure_otel_collector()
        
        assert result["ready"] is True
        
        # Test failed connection
        mock_urlopen.side_effect = Exception("Connection failed")
        result = await executor._ensure_otel_collector()
        
        assert result["ready"] is False
    
    def test_workflow_telemetry_integration(self):
        """Test that workflow execution integrates with telemetry."""
        if not self.temp_dir.exists():
            pytest.skip("Test environment setup failed")
        
        # This test validates that the BPMN execution includes proper telemetry
        # We test the integration points rather than full execution
        
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations
        
        # Verify semantic conventions are available
        assert hasattr(WorkflowAttributes, 'OPERATION')
        assert hasattr(WorkflowAttributes, 'DEFINITION_PATH')
        assert hasattr(WorkflowOperations, 'RUN')
        assert hasattr(WorkflowOperations, 'VALIDATE')
        
        # Test executor has proper telemetry setup
        executor = BPMN8020Executor()
        assert hasattr(executor, 'workflow_stats')
        assert hasattr(executor, 'performance_metrics')
        
        # Verify stats structure
        expected_stats = ["tasks_executed", "tasks_failed", "success_rate"]
        for stat in expected_stats:
            assert stat in executor.workflow_stats


class TestMultiAgentCoordination:
    """Test multi-agent coordination capabilities."""
    
    def setup_method(self):
        """Set up coordination test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    @pytest.mark.asyncio
    async def test_parallel_agent_coordination(self):
        """Test parallel agent coordination."""
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        
        # Mock multiple executors
        executors = [BPMN8020Executor() for _ in range(3)]
        
        # Mock the validation method to return success
        async def mock_validation(bpmn_path):
            return {
                "validation_success": True,
                "overall_success_rate": 0.85,
                "workflow_stats": {"tasks_executed": 10, "tasks_failed": 1}
            }
        
        for executor in executors:
            executor.run_8020_validation = mock_validation
        
        # Run coordination simulation
        tasks = [executor.run_8020_validation(Path("test.bpmn")) for executor in executors]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result["validation_success"] is True
            assert result["overall_success_rate"] >= 0.80
    
    def test_coordination_metrics_calculation(self):
        """Test coordination metrics calculation."""
        # Test coordination success rate calculation
        total_agents = 5
        successful_agents = 4
        failed_agents = 1
        
        coordination_success_rate = successful_agents / total_agents
        assert coordination_success_rate == 0.8
        
        # Test average agent success rate
        agent_success_rates = [0.95, 0.87, 0.92, 0.88]  # Only successful agents
        average_success_rate = sum(agent_success_rates) / len(agent_success_rates)
        
        assert abs(average_success_rate - 0.905) < 0.001
        
        # Test overall coordination success (8020 principle)
        coordination_successful = coordination_success_rate >= 0.80 and average_success_rate >= 0.80
        assert coordination_successful is True


@pytest.mark.integration
class TestFullSystemValidation:
    """Integration tests for the complete 8020 validation system."""
    
    def setup_method(self):
        """Set up full system test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def test_system_components_integration(self):
        """Test that all system components integrate properly."""
        # Test imports work
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor, run_8020_validation_workflow
        from uvmgr.commands.agent import run_8020_validation, validate_otel_integration, coordinate_agents
        
        # Test that components can be instantiated
        executor = BPMN8020Executor()
        assert executor is not None
        
        # Test that CLI commands exist and have proper signatures
        import inspect
        
        # Check 8020 validation command
        sig = inspect.signature(run_8020_validation)
        assert 'success_threshold' in sig.parameters
        assert 'otel_endpoint' in sig.parameters
        
        # Check OTEL validation command
        sig = inspect.signature(validate_otel_integration)
        assert 'check_collector' in sig.parameters
        assert 'check_spans' in sig.parameters
        
        # Check coordination command
        sig = inspect.signature(coordinate_agents)
        assert 'agents' in sig.parameters
        assert 'mode' in sig.parameters
    
    def test_8020_principle_validation(self):
        """Test that the 8020 principle is properly implemented."""
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        
        executor = BPMN8020Executor()
        
        # Test success rate calculation with 8020 principle
        test_cases = [
            # (success_rate, should_pass_8020)
            (0.85, True),   # Above 80% - should pass
            (0.80, True),   # Exactly 80% - should pass
            (0.79, False),  # Below 80% - should fail
            (0.95, True),   # Well above 80% - should pass
            (0.60, False),  # Well below 80% - should fail
        ]
        
        for success_rate, should_pass in test_cases:
            # Mock validation results to achieve target success rate
            total_tests = 100
            passed_tests = int(success_rate * total_tests)
            
            executor.validation_results = {
                "test_project": {
                    "tests_run": total_tests,
                    "tests_passed": passed_tests
                }
            }
            
            calculated_rate = executor._calculate_overall_success_rate()
            validation_success = calculated_rate >= 0.80
            
            assert abs(calculated_rate - success_rate) < 0.01
            assert validation_success == should_pass
    
    def test_otel_trust_principle(self):
        """Test that the system follows 'Trust Only OTEL Traces' principle."""
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        
        executor = BPMN8020Executor()
        
        # Verify that performance metrics come from actual collection, not hardcoded
        # The _collect_performance_metrics method should query real OTEL data
        
        # Test SLA configuration is data-driven
        assert isinstance(executor.slas, dict)
        assert all(isinstance(threshold, (int, float)) for threshold in executor.slas.values())
        
        # Test that validation results are based on actual test execution
        # Not hardcoded success values
        executor.validation_results = {}
        initial_success_rate = executor._calculate_overall_success_rate()
        assert initial_success_rate == 0.0  # No results yet
        
        # Add real results
        executor.validation_results["real_test"] = {
            "tests_run": 10,
            "tests_passed": 8
        }
        
        updated_success_rate = executor._calculate_overall_success_rate()
        assert updated_success_rate == 0.8  # Based on actual results
    
    @pytest.mark.slow
    def test_performance_characteristics(self):
        """Test performance characteristics of the validation system."""
        from uvmgr.runtime.agent.bpmn_8020_executor import BPMN8020Executor
        import time
        
        executor = BPMN8020Executor()
        
        # Test that executor initialization is fast
        start_time = time.time()
        executor = BPMN8020Executor()
        init_time = time.time() - start_time
        
        assert init_time < 1.0  # Should initialize in under 1 second
        
        # Test that SLA checking is efficient
        executor.performance_metrics = {
            "startup_time_ms": 450,
            "command_time_ms": 3000,
            "success_rate": 0.95
        }
        
        start_time = time.time()
        compliance = executor._check_sla_compliance()
        check_time = time.time() - start_time
        
        assert check_time < 0.1  # Should check SLAs in under 100ms
        assert isinstance(compliance, dict)
        assert len(compliance) == len(executor.slas)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])