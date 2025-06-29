"""
Unit tests for runtime module implementations.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from uvmgr.runtime.agent import execute_bpmn_workflow, get_agent_status
from uvmgr.runtime.agent_guides import search_conversations, install_guide
from uvmgr.runtime.guides import get_guide_catalog, fetch_guide
from uvmgr.runtime.dod import execute_automation_workflow, validate_criteria_runtime


class TestAgentRuntime:
    """Test agent runtime functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_bpmn_workflow(self):
        """Test BPMN workflow execution."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False) as f:
            # Create a simple BPMN file
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="test_process">
    <bpmn:task id="test_task" name="Test Task" />
  </bpmn:process>
</bpmn:definitions>""")
            bpmn_file = Path(f.name)
        
        try:
            result = await execute_bpmn_workflow(bpmn_file)
            
            assert result.workflow_id is not None
            assert result.status is not None
            assert result.duration is not None
            assert result.tasks_executed >= 0
            
        finally:
            bpmn_file.unlink()
    
    def test_get_agent_status(self):
        """Test agent status retrieval."""
        status = get_agent_status()
        
        assert "total_executions" in status
        assert "success_rate" in status
        assert "average_duration" in status
        assert "active_workflows" in status


class TestAgentGuides:
    """Test agent guides runtime functionality."""
    
    def test_search_conversations_empty(self):
        """Test conversation search with no results."""
        results = search_conversations("nonexistent_query_12345")
        
        assert isinstance(results, list)
        # Should return empty list since no conversation files exist
        assert len(results) == 0
    
    def test_install_guide_local(self):
        """Test guide installation from local source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "test_guide"
            source_dir.mkdir()
            
            # Create a simple guide structure
            (source_dir / "README.md").write_text("# Test Guide")
            (source_dir / "guide.json").write_text('{"name": "test", "version": "1.0"}')
            
            target_dir = Path(temp_dir) / "target"
            
            guide_info = install_guide(str(source_dir), target_dir)
            
            assert guide_info.name == "test"
            assert guide_info.status == "installed"


class TestGuides:
    """Test guides runtime functionality."""
    
    def test_get_guide_catalog(self):
        """Test guide catalog retrieval."""
        catalog = get_guide_catalog()
        
        assert "guides" in catalog
        assert "categories" in catalog
        assert "total" in catalog
        assert isinstance(catalog["guides"], list)
    
    def test_fetch_guide(self):
        """Test guide fetching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the cache directory
            with patch('uvmgr.runtime.guides._get_cache_dir', return_value=Path(temp_dir)):
                # This should create a simulated guide
                result = fetch_guide("python-best-practices", force=True)
                
                assert "name" in result
                assert "version" in result
                assert "path" in result
                assert result["name"] == "python-best-practices"


class TestDoD:
    """Test Definition of Done runtime functionality."""
    
    @pytest.mark.asyncio 
    async def test_execute_automation_workflow(self):
        """Test DoD automation workflow execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a simple project structure
            (project_path / "README.md").write_text("# Test Project")
            
            result = execute_automation_workflow(
                project_path=project_path,
                criteria=["documentation"],
                environment="test",
                auto_fix=False,
                parallel=False,
                ai_assist=False
            )
            
            assert "success" in result
            assert "criteria_results" in result
            assert "execution_time" in result
    
    def test_validate_criteria_runtime(self):
        """Test criteria validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a simple project structure
            (project_path / "README.md").write_text("# Test Project")
            
            result = validate_criteria_runtime(
                project_path=project_path,
                criteria=["documentation"],
                detailed=True,
                fix_suggestions=True
            )
            
            assert "success" in result
            assert "criteria_scores" in result
            if result["success"]:
                assert "documentation" in result["criteria_scores"]


if __name__ == "__main__":
    pytest.main([__file__])