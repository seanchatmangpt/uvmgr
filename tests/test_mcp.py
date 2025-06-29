"""
Tests for uvmgr MCP functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from uvmgr.mcp.server import UvmgrMCPServer
from uvmgr.mcp.client import UvmgrMCPClient
from uvmgr.mcp.config import MCPConfig, MCPConfigManager, validate_mcp_config
from uvmgr.mcp.models import UvmgrDSPyModels, run_dspy_analysis


class TestMCPConfig:
    """Test MCP configuration management."""
    
    def test_mcp_config_defaults(self):
        """Test MCP config default values."""
        config = MCPConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.server_url == "http://localhost:8000"
        assert config.dspy_enabled is True
        assert config.default_validation_level == "strict"
    
    def test_mcp_config_validation(self):
        """Test MCP config validation."""
        config = MCPConfig()
        config.port = 99999  # Invalid port
        
        manager = MCPConfigManager()
        manager.config = config
        
        result = manager.validate_config()
        assert result["is_valid"] is False
        assert "Invalid port" in result["issues"]
    
    def test_mcp_config_update(self):
        """Test MCP config updates."""
        manager = MCPConfigManager()
        
        manager.update_config(port=9000, dspy_enabled=False)
        
        assert manager.config.port == 9000
        assert manager.config.dspy_enabled is False


class TestMCPDSPyModels:
    """Test DSPy models integration."""
    
    def test_dspy_models_initialization(self):
        """Test DSPy models initialization."""
        models = UvmgrDSPyModels()
        
        expected_models = [
            "validation_analyzer", "workflow_optimizer", "issue_diagnoser",
            "config_recommender", "performance_analyzer", "security_analyzer",
            "trend_analyzer", "query_optimizer", "result_interpreter", "error_analyzer"
        ]
        
        for model_name in expected_models:
            assert model_name in models.get_available_models()
    
    def test_dspy_models_info(self):
        """Test getting model information."""
        models = UvmgrDSPyModels()
        
        info = models.get_model_info("validation_analyzer")
        assert info["name"] == "validation_analyzer"
        assert "input_fields" in info
        assert "output_fields" in info
        assert "available_strategies" in info
    
    @pytest.mark.asyncio
    async def test_dspy_analysis_run(self):
        """Test running DSPy analysis."""
        models = UvmgrDSPyModels()
        
        # Mock the predictor to avoid actual LLM calls
        with patch.object(models, 'predictors', {}):
            models.predictors["validation_analyzer_simple"] = Mock()
            models.predictors["validation_analyzer_simple"].return_value = Mock(
                analysis="Test analysis",
                confidence_score=0.8,
                key_insights="Test insights"
            )
            
            result = await models.run_analysis(
                "validation_analyzer",
                {"test": "data"},
                {"context": "test"},
                "simple"
            )
            
            assert "analysis" in result
            assert "confidence_score" in result


class TestMCPServer:
    """Test MCP server functionality."""
    
    def test_mcp_server_initialization(self):
        """Test MCP server initialization."""
        server = UvmgrMCPServer()
        
        assert server.validation_orchestrator is not None
        assert server.dspy_models is not None
    
    def test_mcp_server_routes(self):
        """Test MCP server route registration."""
        server = UvmgrMCPServer()
        
        # Check that routes are registered
        assert hasattr(server, 'app')
        
        # Check that tools are available
        tools = [route.name for route in server.app.routes if hasattr(route, 'name')]
        expected_tools = [
            "get_github_actions_status", "list_workflows", "get_workflow_runs",
            "validate_data", "get_validation_dashboard", "optimize_workflows",
            "diagnose_validation_issues", "get_recommendations"
        ]
        
        for tool in expected_tools:
            assert any(tool in str(route) for route in server.app.routes)


class TestMCPClient:
    """Test MCP client functionality."""
    
    @pytest.mark.asyncio
    async def test_mcp_client_initialization(self):
        """Test MCP client initialization."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        assert client.server_url == "http://test-server:8000"
        assert client.dspy_models is not None
    
    @pytest.mark.asyncio
    async def test_mcp_client_health_check(self):
        """Test MCP client health check."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await client.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_mcp_client_get_status(self):
        """Test MCP client get status."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        # Mock the client call
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.return_value = {
                "status": "success",
                "data": {"workflow_runs": []},
                "validation": {"is_valid": True, "confidence": 0.9, "issues": []}
            }
            
            # Mock DSPy analysis
            with patch.object(client, '_run_dspy_analysis') as mock_dspy:
                mock_dspy.return_value = {"interpretation": "Test interpretation"}
                
                result = await client.get_github_actions_status("test-org", "test-repo")
                
                assert result["status"] == "success"
                assert "interpretation" in result


class TestMCPIntegration:
    """Test MCP integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_analysis(self):
        """Test full workflow analysis through MCP."""
        # Mock server response
        mock_server_response = {
            "status": "success",
            "data": {
                "workflow_runs": [
                    {
                        "id": 1,
                        "name": "Test Workflow",
                        "status": "completed",
                        "conclusion": "success"
                    }
                ]
            },
            "validation": {
                "is_valid": True,
                "confidence": 0.95,
                "issues": []
            },
            "optimization": {
                "optimization_suggestions": "Test suggestions",
                "expected_improvement": "10%"
            }
        }
        
        client = UvmgrMCPClient("http://test-server:8000")
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.return_value = mock_server_response
            
            with patch.object(client, '_run_dspy_analysis') as mock_dspy:
                mock_dspy.return_value = {
                    "interpretation": "Workflow is performing well",
                    "key_insights": "No major issues detected",
                    "next_actions": "Continue monitoring"
                }
                
                result = await client.get_workflow_runs("test-org", "test-repo")
                
                assert result["status"] == "success"
                assert "interpretation" in result
                assert len(result["data"]["data"]["workflow_runs"]) == 1
    
    @pytest.mark.asyncio
    async def test_validation_with_dspy(self):
        """Test validation with DSPy analysis."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        test_data = {
            "workflow_runs": [],
            "total_count": 0
        }
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.return_value = {
                "status": "success",
                "validation": {
                    "is_valid": True,
                    "confidence": 0.9,
                    "issues": []
                }
            }
            
            with patch.object(client, '_run_dspy_analysis') as mock_dspy:
                mock_dspy.return_value = {
                    "interpretation": "Data validation successful",
                    "key_insights": "All data is valid",
                    "next_actions": "Proceed with confidence"
                }
                
                result = await client.validate_data(test_data)
                
                assert result["status"] == "success"
                assert result["data"]["validation"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in MCP client."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.side_effect = Exception("Test error")
            
            with patch.object(client, '_run_dspy_analysis') as mock_dspy:
                mock_dspy.return_value = {
                    "analysis": "Error occurred during request",
                    "solutions": "Check server connectivity"
                }
                
                result = await client.get_github_actions_status("test-org", "test-repo")
                
                assert result["status"] == "error"
                assert "Test error" in result["message"]
                assert "analysis" in result


class TestMCPCommands:
    """Test MCP CLI commands."""
    
    def test_mcp_commands_registration(self):
        """Test MCP commands are properly registered."""
        from uvmgr.mcp.commands import mcp_group
        
        assert mcp_group.name == "mcp"
        assert len(mcp_group.commands) > 0
        
        # Check for expected commands
        command_names = [cmd.name for cmd in mcp_group.commands]
        expected_commands = [
            "server", "status", "workflows", "runs", 
            "dashboard", "optimize", "validate"
        ]
        
        for cmd in expected_commands:
            assert cmd in command_names


class TestMCPPerformance:
    """Test MCP performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.return_value = {"status": "success", "data": {}}
            
            # Make multiple concurrent requests
            tasks = [
                client.get_github_actions_status("org1", "repo1"),
                client.get_github_actions_status("org2", "repo2"),
                client.list_workflows("org3", "repo3")
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result["status"] == "success" for result in results)
    
    @pytest.mark.asyncio
    async def test_dspy_analysis_performance(self):
        """Test DSPy analysis performance."""
        models = UvmgrDSPyModels()
        
        # Mock predictors for performance testing
        with patch.object(models, 'predictors', {}):
            mock_predictor = Mock()
            mock_predictor.return_value = Mock(
                analysis="Test analysis",
                confidence_score=0.8
            )
            models.predictors["validation_analyzer_simple"] = mock_predictor
            
            # Run multiple analyses
            tasks = [
                models.run_analysis("validation_analyzer", {"data": i}, {})
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all("analysis" in result for result in results)


class TestMCPValidation:
    """Test MCP validation integration."""
    
    @pytest.mark.asyncio
    async def test_validation_with_different_levels(self):
        """Test validation with different levels."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        test_data = {"test": "data"}
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.return_value = {
                "status": "success",
                "validation": {
                    "is_valid": True,
                    "confidence": 0.9,
                    "issues": []
                }
            }
            
            # Test different validation levels
            levels = ["strict", "moderate", "lenient"]
            
            for level in levels:
                result = await client.validate_data(test_data, level)
                assert result["status"] == "success"
                assert result["data"]["validation"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation error handling."""
        client = UvmgrMCPClient("http://test-server:8000")
        
        with patch.object(client.client, 'call_tool') as mock_call:
            mock_call.side_effect = Exception("Validation failed")
            
            result = await client.validate_data({"test": "data"})
            
            assert result["status"] == "error"
            assert "Validation failed" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__]) 