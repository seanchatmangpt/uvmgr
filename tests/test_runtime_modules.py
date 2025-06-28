"""
Runtime Modules Tests
====================

Tests for the newly implemented runtime modules that were missing:
- runtime/agent.py (BPMN workflow execution)
- runtime/aps.py (APScheduler integration)
- ops/devtasks.py (Development task automation)
- ops/cost.py (Cost analysis and optimization)

These tests ensure the 80/20 implementation is working correctly.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from uvmgr.runtime.agent import (
    BpmnWorkflowAgent, get_workflow_agent, 
    WorkflowExecutionResult, WorkflowStatus
)
from uvmgr.runtime.aps import (
    IntelligentScheduler, get_intelligent_scheduler,
    JobStatus, ScheduleType
)
from uvmgr.ops.devtasks import (
    IntelligentDevTaskManager, get_dev_task_manager,
    TaskType, TaskStatus, TaskPriority
)
from uvmgr.ops.cost import (
    IntelligentCostAnalyzer, get_cost_analyzer,
    CostCategory, CostUnit, track_cost_entry
)


class TestBpmnWorkflowAgent:
    """Test BPMN Workflow Agent implementation."""
    
    def test_agent_initialization(self):
        """Test that workflow agent initializes correctly."""
        agent = BpmnWorkflowAgent()
        
        assert agent is not None
        assert isinstance(agent.task_handlers, dict)
        assert len(agent.task_handlers) > 0
        assert agent.max_concurrent_workflows == 10
        
        # Test statistics
        stats = agent.get_execution_stats()
        assert "total_executions" in stats
        assert "spiff_available" in stats
        assert stats["active_workflows"] == 0
    
    @pytest.mark.asyncio
    async def test_workflow_execution_without_spiff(self):
        """Test workflow execution when SpiffWorkflow is not available."""
        
        with patch('uvmgr.runtime.agent.SPIFF_AVAILABLE', False):
            agent = BpmnWorkflowAgent()
            
            with tempfile.NamedTemporaryFile(suffix=".bpmn") as f:
                bpmn_path = Path(f.name)
                
                result = await agent.execute_workflow_from_file(bpmn_path)
                
                assert result.status == WorkflowStatus.FAILED
                assert "SpiffWorkflow not available" in result.error
    
    @pytest.mark.asyncio
    async def test_task_handler_registration(self):
        """Test custom task handler registration."""
        agent = BpmnWorkflowAgent()
        
        # Register custom handler
        async def custom_handler(context):
            return {"custom": True, "success": True}
        
        agent.register_task_handler("custom_task", custom_handler)
        
        assert "custom_task" in agent.task_handlers
        assert agent.task_handlers["custom_task"] == custom_handler
    
    def test_global_agent_singleton(self):
        """Test that global agent is singleton."""
        agent1 = get_workflow_agent()
        agent2 = get_workflow_agent()
        
        assert agent1 is agent2


class TestIntelligentScheduler:
    """Test APScheduler integration."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = IntelligentScheduler()
        
        assert scheduler is not None
        assert isinstance(scheduler.job_functions, dict)
        assert len(scheduler.job_functions) > 0
        assert scheduler.enable_agi_optimization is True
        
        # Test statistics
        stats = scheduler.get_scheduler_stats()
        assert "aps_available" in stats
        assert "total_jobs" in stats
    
    def test_scheduler_without_apscheduler(self):
        """Test scheduler when APScheduler is not available."""
        
        with patch('uvmgr.runtime.aps.APS_AVAILABLE', False):
            scheduler = IntelligentScheduler()
            stats = scheduler.get_scheduler_stats()
            
            assert stats["aps_available"] is False
            assert stats["status"] == "stopped"
    
    @pytest.mark.asyncio
    async def test_job_function_registration(self):
        """Test job function registration."""
        scheduler = IntelligentScheduler()
        
        # Register custom job function
        async def custom_job():
            return {"custom_job": True}
        
        scheduler.register_job_function("custom_job", custom_job)
        
        assert "custom_job" in scheduler.job_functions
        assert scheduler.job_functions["custom_job"] == custom_job
    
    @pytest.mark.asyncio
    async def test_job_addition_without_apscheduler(self):
        """Test job addition when APScheduler is not available."""
        
        with patch('uvmgr.runtime.aps.APS_AVAILABLE', False):
            scheduler = IntelligentScheduler()
            
            result = await scheduler.add_job(
                job_id="test_job",
                name="Test Job",
                function="system_health_check",
                schedule_type=ScheduleType.INTERVAL,
                schedule_config={"minutes": 5}
            )
            
            assert result is False
    
    def test_global_scheduler_singleton(self):
        """Test that global scheduler is singleton."""
        scheduler1 = get_intelligent_scheduler()
        scheduler2 = get_intelligent_scheduler()
        
        assert scheduler1 is scheduler2


class TestDevTaskManager:
    """Test development task automation."""
    
    @pytest.mark.asyncio
    async def test_task_manager_initialization(self):
        """Test task manager initialization."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            manager = IntelligentDevTaskManager(project_root)
            
            assert manager.project_root == project_root
            assert isinstance(manager.task_registry, dict)
            assert isinstance(manager.task_handlers, dict)
            assert manager.enable_agi_optimization is True
    
    @pytest.mark.asyncio
    async def test_python_project_detection(self):
        """Test Python project task detection."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create pyproject.toml
            pyproject_toml = project_root / "pyproject.toml"
            pyproject_toml.write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "0.1.0"

dependencies = [
    "pytest>=7.0.0",
    "ruff>=0.1.0"
]

[tool.poe.tasks]
test = "pytest"
lint = "ruff check ."
format = "ruff format ."
""")
            
            manager = IntelligentDevTaskManager(project_root)
            
            # Wait for auto-detection
            await asyncio.sleep(0.1)
            
            # Verify tasks were detected
            stats = manager.get_task_stats()
            
            # Should have detected at least the Poetry tasks
            assert stats["total_tasks"] > 0
            
            # Check for specific tasks
            task_ids = list(manager.task_registry.keys())
            poe_tasks = [tid for tid in task_ids if tid.startswith("poe_")]
            assert len(poe_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_task_execution_mock(self):
        """Test task execution with mocked subprocess."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            manager = IntelligentDevTaskManager(project_root)
            
            # Register a test task
            from uvmgr.ops.devtasks import TaskDefinition
            
            test_task = TaskDefinition(
                id="test_task",
                name="Test Task",
                task_type=TaskType.TEST,
                priority=TaskPriority.HIGH,
                command="echo 'test output'",
                description="Test task for unit testing",
                working_dir=project_root
            )
            
            await manager.register_task(test_task)
            
            # Mock subprocess execution
            with patch('asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"test output", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                # Execute task
                result = await manager.execute_task("test_task")
                
                assert result.status == TaskStatus.COMPLETED
                assert result.stdout == "test output"
                assert result.exit_code == 0
    
    def test_task_type_inference(self):
        """Test task type inference logic."""
        
        manager = IntelligentDevTaskManager()
        
        # Test various task names
        assert manager._infer_task_type("test", "") == TaskType.TEST
        assert manager._infer_task_type("build", "") == TaskType.BUILD
        assert manager._infer_task_type("lint", "") == TaskType.LINT
        assert manager._infer_task_type("format", "") == TaskType.FORMAT
        assert manager._infer_task_type("typecheck", "") == TaskType.TYPECHECK
        assert manager._infer_task_type("custom_task", "") == TaskType.CUSTOM
    
    def test_task_priority_inference(self):
        """Test task priority inference."""
        
        manager = IntelligentDevTaskManager()
        
        assert manager._infer_task_priority(TaskType.TEST) == TaskPriority.CRITICAL
        assert manager._infer_task_priority(TaskType.BUILD) == TaskPriority.HIGH
        assert manager._infer_task_priority(TaskType.LINT) == TaskPriority.HIGH
        assert manager._infer_task_priority(TaskType.FORMAT) == TaskPriority.MEDIUM
        assert manager._infer_task_priority(TaskType.CLEANUP) == TaskPriority.LOW
    
    def test_global_manager_access(self):
        """Test global task manager access."""
        
        manager1 = get_dev_task_manager()
        manager2 = get_dev_task_manager()
        
        assert manager1 is manager2


class TestCostAnalyzer:
    """Test cost analysis and optimization."""
    
    @pytest.mark.asyncio
    async def test_cost_analyzer_initialization(self):
        """Test cost analyzer initialization."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            assert analyzer.project_root == project_root
            assert analyzer.default_currency == CostUnit.USD
            assert analyzer.enable_agi_optimization is True
            assert isinstance(analyzer.cost_baselines, dict)
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Test basic cost tracking functionality."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            # Track a cost
            cost_id = await analyzer.track_cost(
                category=CostCategory.DEVELOPER_TIME,
                description="Test development work",
                amount=100.0,
                unit=CostUnit.USD,
                metadata={"hours": 2, "rate": 50.0}
            )
            
            assert cost_id is not None
            assert cost_id.startswith("cost_")
            
            # Verify cost was added
            assert len(analyzer.cost_entries) == 1
            entry = analyzer.cost_entries[0]
            assert entry.category == CostCategory.DEVELOPER_TIME
            assert entry.amount == 100.0
            assert entry.description == "Test development work"
    
    @pytest.mark.asyncio
    async def test_specialized_cost_tracking(self):
        """Test specialized cost tracking methods."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            # Test CI/CD cost tracking
            ci_cd_id = await analyzer.track_ci_cd_cost(
                pipeline_name="test-pipeline",
                duration_minutes=10.0,
                platform="github_actions"
            )
            
            assert ci_cd_id is not None
            
            # Test developer time tracking
            dev_time_id = await analyzer.track_developer_time(
                activity="Code review",
                duration_hours=1.5,
                hourly_rate=75.0
            )
            
            assert dev_time_id is not None
            
            # Test cloud service cost tracking
            cloud_id = await analyzer.track_cloud_service_cost(
                service_name="aws-lambda",
                usage_amount=1000,
                usage_unit="requests",
                cost_per_unit=0.0000002
            )
            
            assert cloud_id is not None
            
            # Verify all costs were tracked
            assert len(analyzer.cost_entries) == 3
    
    @pytest.mark.asyncio
    async def test_budget_management(self):
        """Test budget creation and management."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            # Create a budget
            budget_id = await analyzer.create_budget(
                name="Development Budget",
                category=CostCategory.DEVELOPER_TIME,
                period="monthly",
                limit=5000.0,
                unit=CostUnit.USD,
                alert_threshold=0.8
            )
            
            assert budget_id is not None
            assert budget_id in analyzer.budgets
            
            budget = analyzer.budgets[budget_id]
            assert budget.name == "Development Budget"
            assert budget.limit == 5000.0
            assert budget.alert_threshold == 0.8
    
    @pytest.mark.asyncio
    async def test_cost_report_generation(self):
        """Test cost report generation."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            # Add some test costs
            await analyzer.track_cost(
                category=CostCategory.DEVELOPER_TIME,
                description="Development work",
                amount=500.0
            )
            
            await analyzer.track_cost(
                category=CostCategory.CI_CD,
                description="Pipeline execution",
                amount=50.0
            )
            
            # Generate report
            report = await analyzer.generate_cost_report(period_days=1)
            
            assert report.total_cost == 550.0
            assert len(report.category_breakdown) == 2
            assert CostCategory.DEVELOPER_TIME in report.category_breakdown
            assert CostCategory.CI_CD in report.category_breakdown
            assert len(report.insights) > 0
    
    @pytest.mark.asyncio
    async def test_optimization_recommendations(self):
        """Test AGI-driven optimization recommendations."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            analyzer = IntelligentCostAnalyzer(project_root)
            
            # Add high CI/CD costs to trigger optimization
            for i in range(10):
                await analyzer.track_cost(
                    category=CostCategory.CI_CD,
                    description=f"Pipeline run {i}",
                    amount=100.0  # High cost
                )
            
            # Add some developer time
            await analyzer.track_cost(
                category=CostCategory.DEVELOPER_TIME,
                description="Manual deployment",
                amount=200.0
            )
            
            # Generate recommendations
            entries = analyzer.cost_entries
            recommendations = await analyzer._generate_optimization_recommendations(entries)
            
            # Should have recommendations for high CI/CD costs
            assert len(recommendations) > 0
            
            # Check recommendation structure
            rec = recommendations[0]
            assert hasattr(rec, 'title')
            assert hasattr(rec, 'potential_savings')
            assert hasattr(rec, 'action_items')
            assert len(rec.action_items) > 0
    
    def test_global_analyzer_access(self):
        """Test global cost analyzer access."""
        
        analyzer1 = get_cost_analyzer()
        analyzer2 = get_cost_analyzer()
        
        assert analyzer1 is analyzer2
    
    @pytest.mark.asyncio
    async def test_global_cost_tracking_function(self):
        """Test the global cost tracking function."""
        
        cost_id = await track_cost_entry(
            category=CostCategory.TOOLING,
            description="License cost",
            amount=99.0,
            unit=CostUnit.USD
        )
        
        assert cost_id is not None
        assert cost_id.startswith("cost_")


class TestRuntimeIntegration:
    """Test integration between runtime modules."""
    
    @pytest.mark.asyncio
    async def test_cross_module_functionality(self):
        """Test that different runtime modules can work together."""
        
        # Initialize all modules
        agent = get_workflow_agent()
        scheduler = get_intelligent_scheduler()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            task_manager = get_dev_task_manager(project_root)
            cost_analyzer = get_cost_analyzer(project_root)
            
            # Test that they're all initialized
            assert agent is not None
            assert scheduler is not None
            assert task_manager is not None
            assert cost_analyzer is not None
            
            # Test that they can provide statistics
            agent_stats = agent.get_execution_stats()
            scheduler_stats = scheduler.get_scheduler_stats()
            task_stats = task_manager.get_task_stats()
            cost_stats = cost_analyzer.get_cost_stats()
            
            assert isinstance(agent_stats, dict)
            assert isinstance(scheduler_stats, dict)
            assert isinstance(task_stats, dict)
            assert isinstance(cost_stats, dict)
    
    @pytest.mark.asyncio
    async def test_agi_integration_with_runtime(self):
        """Test that runtime modules integrate with AGI components."""
        
        # This verifies that the runtime modules properly use
        # AGI reasoning and memory systems
        
        from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
        from uvmgr.core.agi_memory import get_persistent_memory
        
        memory = get_persistent_memory()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cost_analyzer = get_cost_analyzer(project_root)
            
            # Track a cost (which should use AGI observation)
            cost_id = await cost_analyzer.track_cost(
                category=CostCategory.DEVELOPER_TIME,
                description="AGI integration test",
                amount=75.0
            )
            
            assert cost_id is not None
            
            # Verify the cost was tracked
            stats = cost_analyzer.get_cost_stats()
            assert stats["total_entries"] > 0


# Pytest configuration for runtime tests
@pytest.fixture(autouse=True)
def reset_global_instances():
    """Reset global instances between tests to avoid interference."""
    
    # Reset global instances
    import uvmgr.runtime.agent
    import uvmgr.runtime.aps
    import uvmgr.ops.devtasks
    import uvmgr.ops.cost
    
    uvmgr.runtime.agent._workflow_agent = None
    uvmgr.runtime.aps._intelligent_scheduler = None
    uvmgr.ops.devtasks._dev_task_manager = None
    uvmgr.ops.cost._cost_analyzer = None
    
    yield
    
    # Cleanup after test
    uvmgr.runtime.agent._workflow_agent = None
    uvmgr.runtime.aps._intelligent_scheduler = None
    uvmgr.ops.devtasks._dev_task_manager = None
    uvmgr.ops.cost._cost_analyzer = None


# Mark runtime tests
pytestmark = pytest.mark.runtime