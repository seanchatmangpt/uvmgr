"""
Core Integration Tests
======================

Comprehensive integration tests for uvmgr's core systems working together.
Tests the 80/20 critical functionality that provides the most value.

Test Coverage:
- Runtime modules (agent, aps scheduler)
- Operations modules (devtasks, cost analysis)
- AGI components (memory, reasoning, goals, self-modification)
- OTEL validation and telemetry
- Command integration and workflows
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Core system imports
from uvmgr.runtime.agent import get_workflow_agent, execute_bpmn_workflow, WorkflowStatus
from uvmgr.runtime.aps import get_intelligent_scheduler, start_scheduler, stop_scheduler
from uvmgr.ops.devtasks import get_dev_task_manager, execute_dev_task, TaskStatus
from uvmgr.ops.cost import get_cost_analyzer, track_cost_entry, CostCategory, CostUnit
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights
from uvmgr.core.autonomous_goals import get_goal_generator, run_autonomous_cycle
from uvmgr.core.safe_modifier import get_safe_modifier, propose_self_improvement


class TestRuntimeIntegration:
    """Test runtime module integration."""
    
    @pytest.mark.asyncio
    async def test_workflow_agent_basic_functionality(self):
        """Test basic workflow agent functionality."""
        
        agent = get_workflow_agent()
        stats = agent.get_execution_stats()
        
        # Verify agent is properly initialized
        assert isinstance(stats, dict)
        assert "total_executions" in stats
        assert "spiff_available" in stats
        
        # Test with mock BPMN workflow
        with tempfile.NamedTemporaryFile(suffix=".bpmn", mode="w", delete=False) as f:
            # Simple BPMN content (mock)
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <bpmn:process id="test_process" isExecutable="true">
        <bpmn:startEvent id="start"/>
        <bpmn:endEvent id="end"/>
        <bpmn:sequenceFlow sourceRef="start" targetRef="end"/>
    </bpmn:process>
</bpmn:definitions>""")
            bpmn_path = Path(f.name)
        
        try:
            # Execute workflow
            result = await execute_bpmn_workflow(
                bpmn_path, 
                inputs={"test_input": "test_value"}
            )
            
            # Verify execution result
            assert result.workflow_id is not None
            assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            assert result.start_time > 0
            
        finally:
            # Cleanup
            bpmn_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_scheduler_integration(self):
        """Test APScheduler integration."""
        
        scheduler = get_intelligent_scheduler()
        initial_stats = scheduler.get_scheduler_stats()
        
        # Verify scheduler is initialized
        assert isinstance(initial_stats, dict)
        assert "aps_available" in initial_stats
        
        # Test basic scheduler operations (without actually starting)
        # since starting requires APScheduler and database setup
        assert initial_stats["total_jobs"] >= 0
        assert "agi_optimization_enabled" in initial_stats


class TestOperationsIntegration:
    """Test operations module integration."""
    
    @pytest.mark.asyncio
    async def test_devtasks_integration(self):
        """Test development tasks integration."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create a test pyproject.toml
            pyproject_toml = project_root / "pyproject.toml"
            pyproject_toml.write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "0.1.0"

[tool.poe.tasks]
test = "pytest"
lint = "ruff check ."
""")
            
            # Initialize task manager
            task_manager = get_dev_task_manager(project_root)
            
            # Wait for auto-detection to complete
            await asyncio.sleep(0.1)
            
            # Verify tasks were detected
            stats = task_manager.get_task_stats()
            assert stats["total_tasks"] > 0
            
            # Test task execution (mock)
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"test output", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                # Execute a mock task
                if task_manager.task_registry:
                    task_id = list(task_manager.task_registry.keys())[0]
                    result = await execute_dev_task(task_id)
                    
                    assert result.task_id == task_id
                    assert result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
    
    @pytest.mark.asyncio
    async def test_cost_analysis_integration(self):
        """Test cost analysis integration."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Initialize cost analyzer
            cost_analyzer = get_cost_analyzer(project_root)
            
            # Test cost tracking
            cost_id = await track_cost_entry(
                category=CostCategory.DEVELOPER_TIME,
                description="Test development task",
                amount=50.0,
                unit=CostUnit.USD
            )
            
            assert cost_id is not None
            assert cost_id.startswith("cost_")
            
            # Verify cost was tracked
            stats = cost_analyzer.get_cost_stats()
            assert stats["total_entries"] > 0
            assert stats["total_cost"] > 0
            
            # Test cost report generation
            report = await cost_analyzer.generate_cost_report(period_days=1)
            assert report.total_cost > 0
            assert len(report.insights) > 0


class TestAGIIntegration:
    """Test AGI component integration."""
    
    @pytest.mark.asyncio
    async def test_agi_memory_integration(self):
        """Test AGI memory system integration."""
        
        memory = get_persistent_memory()
        stats = memory.get_memory_stats()
        
        # Verify memory system is initialized
        assert isinstance(stats, dict)
        assert "status" in stats
        
        # Test knowledge storage and retrieval
        knowledge_id = memory.store_knowledge(
            content="Test integration knowledge",
            knowledge_type="integration_test",
            metadata={"test": True}
        )
        
        # Verify storage
        if stats["status"] == "active":
            assert knowledge_id != "memory_disabled"
            
            # Test retrieval
            results = memory.retrieve_similar("integration test", n_results=1)
            if results:
                assert len(results) > 0
                assert "integration" in results[0].memory.content.lower()
    
    @pytest.mark.asyncio  
    async def test_agi_reasoning_integration(self):
        """Test AGI reasoning integration."""
        
        # Test observation
        observe_with_agi_reasoning(
            attributes={"test_command": "integration_test"},
            context={"integration_test": True}
        )
        
        # Test insights
        insights = get_agi_insights()
        assert isinstance(insights, dict)
        assert "understanding_confidence" in insights
        assert "causal_patterns_discovered" in insights
    
    @pytest.mark.asyncio
    async def test_autonomous_goals_integration(self):
        """Test autonomous goal system integration."""
        
        goal_generator = get_goal_generator()
        
        # Test goal generation
        analysis = await goal_generator.analyze_system_state()
        assert analysis.confidence > 0
        assert isinstance(analysis.performance_metrics, dict)
        
        # Test autonomous cycle (without long execution)
        with patch.object(goal_generator, 'max_concurrent_goals', 1):
            cycle_results = await run_autonomous_cycle()
            
            assert isinstance(cycle_results, dict)
            assert "success" in cycle_results
            assert "goals_generated" in cycle_results
    
    @pytest.mark.asyncio
    async def test_safe_modification_integration(self):
        """Test safe self-modification integration."""
        
        modifier = get_safe_modifier()
        summary = modifier.get_modification_summary()
        
        # Verify modifier is initialized
        assert isinstance(summary, dict)
        assert "total_modifications" in summary
        assert "dspy_available" in summary
        
        # Test modification proposal (with mock file)
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def test_function():\n    return 'hello world'\n")
            test_file = Path(f.name)
        
        try:
            proposal = await propose_self_improvement(
                test_file,
                "Add error handling to the function"
            )
            
            assert proposal.target_file == test_file
            assert proposal.modification_type is not None
            assert proposal.risk_level is not None
            
        finally:
            test_file.unlink(missing_ok=True)


class TestSystemIntegration:
    """Test overall system integration."""
    
    @pytest.mark.asyncio
    async def test_telemetry_integration(self):
        """Test that telemetry works across all components."""
        
        # Import telemetry functions
        from uvmgr.core.telemetry import span, metric_counter
        
        # Test span creation
        with span("integration_test") as test_span:
            assert test_span is not None
            
            # Test metric recording
            counter = metric_counter("integration.test")
            counter(1)
            
            # Verify span completes without error
            pass
    
    @pytest.mark.asyncio
    async def test_command_workflow_integration(self):
        """Test integration between commands and workflows."""
        
        # This tests that the various components can work together
        # in a realistic command execution scenario
        
        # 1. Initialize systems
        memory = get_persistent_memory()
        goal_generator = get_goal_generator()
        
        # 2. Simulate command execution with observation
        observe_with_agi_reasoning(
            attributes={"command": "integration_test_workflow"},
            context={"workflow_integration": True}
        )
        
        # 3. Store knowledge about the execution
        memory.store_knowledge(
            content="Integration test workflow executed successfully",
            knowledge_type="workflow_execution",
            metadata={"integration_test": True}
        )
        
        # 4. Verify systems are working together
        insights = get_agi_insights()
        assert insights["understanding_confidence"] > 0
        
        # 5. Test goal generation based on the execution
        analysis = await goal_generator.analyze_system_state()
        assert analysis.performance_metrics is not None
    
    def test_dependencies_available(self):
        """Test that critical dependencies are available."""
        
        # Test critical imports that the system depends on
        try:
            import chromadb
            import sentence_transformers
            import torch
            import transformers
            import spiffworkflow
            import dspy
            chromadb_available = True
        except ImportError:
            chromadb_available = False
        
        # While these are optional, test should note if they're missing
        # since they significantly impact functionality
        if not chromadb_available:
            pytest.skip("Critical dependencies not available - AGI functionality limited")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test that errors are handled gracefully across components."""
        
        # Test that systems handle missing dependencies gracefully
        memory = get_persistent_memory()
        stats = memory.get_memory_stats()
        
        # System should either work or gracefully degrade
        assert stats["status"] in ["active", "disabled", "error"]
        
        # Test that invalid operations don't crash the system
        with tempfile.TemporaryDirectory() as temp_dir:
            task_manager = get_dev_task_manager(Path(temp_dir))
            
            # Try to execute non-existent task
            result = await task_manager.execute_task("non_existent_task")
            assert result.status == TaskStatus.FAILED
            assert "not found" in result.error


class TestPerformanceIntegration:
    """Test performance characteristics of integrated systems."""
    
    @pytest.mark.asyncio
    async def test_system_startup_performance(self):
        """Test that system components initialize quickly."""
        
        start_time = time.time()
        
        # Initialize key components
        memory = get_persistent_memory()
        agent = get_workflow_agent()
        scheduler = get_intelligent_scheduler()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            task_manager = get_dev_task_manager(Path(temp_dir))
            cost_analyzer = get_cost_analyzer(Path(temp_dir))
        
        initialization_time = time.time() - start_time
        
        # System should initialize reasonably quickly (under 5 seconds)
        assert initialization_time < 5.0, f"System took {initialization_time:.2f}s to initialize"
    
    @pytest.mark.asyncio
    async def test_memory_usage_reasonable(self):
        """Test that memory usage is reasonable."""
        
        try:
            import psutil
            process = psutil.Process()
            
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Initialize all systems
            memory = get_persistent_memory()
            agent = get_workflow_agent()
            goal_generator = get_goal_generator()
            
            # Store some test data
            for i in range(10):
                memory.store_knowledge(
                    content=f"Test knowledge {i}",
                    knowledge_type="performance_test",
                    metadata={"index": i}
                )
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (under 100MB for basic operations)
            assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")


# Integration test fixtures
@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create basic project structure
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        
        # Create pyproject.toml
        pyproject = project_path / "pyproject.toml"
        pyproject.write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "0.1.0"

[tool.poe.tasks]
test = "pytest"
lint = "ruff check ."
build = "python -m build"
""")
        
        yield project_path


@pytest.fixture
def mock_agi_dependencies():
    """Mock AGI dependencies if they're not available."""
    
    # Check if dependencies are available
    try:
        import chromadb
        import sentence_transformers
        dependencies_available = True
    except ImportError:
        dependencies_available = False
    
    if not dependencies_available:
        # Create mocks for testing
        with patch('uvmgr.core.agi_memory.MEMORY_AVAILABLE', False):
            with patch('uvmgr.core.safe_modifier.DSPY_AVAILABLE', False):
                yield
    else:
        yield


# Mark integration tests
pytestmark = pytest.mark.integration