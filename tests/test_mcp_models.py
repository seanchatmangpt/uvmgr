"""
Unit tests for uvmgr MCP models with Qwen3 and web search.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from uvmgr.mcp.models import (
    UvmgrDSPyModels, 
    WebSearchTool, 
    get_dspy_models, 
    run_dspy_analysis
)


class TestWebSearchTool:
    """Test web search tool functionality."""
    
    @pytest.fixture
    def web_search_tool(self):
        """Create web search tool instance."""
        return WebSearchTool()
    
    @pytest.mark.asyncio
    async def test_web_search_success(self, web_search_tool):
        """Test successful web search."""
        query = "GitHub Actions optimization"
        results = await web_search_tool.search(query, max_results=3)
        
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)
        assert all("title" in result for result in results)
        assert all("url" in result for result in results)
        assert all("snippet" in result for result in results)
        assert all("source" in result for result in results)
        assert all(result["source"] == "web_search" for result in results)
    
    @pytest.mark.asyncio
    async def test_web_search_caching(self, web_search_tool):
        """Test web search result caching."""
        query = "test query"
        
        # First search
        results1 = await web_search_tool.search(query)
        assert query in web_search_tool.search_results
        
        # Second search should return cached results
        results2 = await web_search_tool.search(query)
        assert results1 == results2
    
    @pytest.mark.asyncio
    async def test_web_search_error_handling(self, web_search_tool):
        """Test web search error handling."""
        with patch.object(web_search_tool, 'search', side_effect=Exception("Search failed")):
            results = await web_search_tool.search("test")
            assert results == []


class TestUvmgrDSPyModels:
    """Test DSPy models functionality."""
    
    @pytest.fixture
    def dspy_models(self):
        """Create DSPy models instance."""
        return UvmgrDSPyModels()
    
    def test_initialization(self, dspy_models):
        """Test DSPy models initialization."""
        assert hasattr(dspy_models, 'models')
        assert hasattr(dspy_models, 'predictors')
        assert hasattr(dspy_models, 'web_search')
        assert isinstance(dspy_models.web_search, WebSearchTool)
    
    def test_available_models(self, dspy_models):
        """Test getting available models."""
        models = dspy_models.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        
        expected_models = [
            "validation_analyzer",
            "workflow_optimizer", 
            "issue_diagnoser",
            "config_recommender",
            "performance_analyzer",
            "security_analyzer",
            "trend_analyzer",
            "query_optimizer",
            "result_interpreter",
            "error_analyzer",
            "web_search_analyzer"
        ]
        
        for model in expected_models:
            assert model in models
    
    def test_available_strategies(self, dspy_models):
        """Test getting available strategies."""
        strategies = dspy_models.get_available_strategies()
        assert isinstance(strategies, list)
        assert "simple" in strategies
        assert "cot" in strategies
        assert "react" in strategies
        assert "multi" in strategies
    
    def test_model_info(self, dspy_models):
        """Test getting model information."""
        model_info = dspy_models.get_model_info("validation_analyzer")
        assert isinstance(model_info, dict)
        assert "name" in model_info
        assert "description" in model_info
        assert "input_fields" in model_info
        assert "output_fields" in model_info
        assert "available_strategies" in model_info
        assert model_info["name"] == "validation_analyzer"
    
    def test_model_info_not_found(self, dspy_models):
        """Test getting info for non-existent model."""
        model_info = dspy_models.get_model_info("non_existent_model")
        assert "error" in model_info
    
    def test_generate_search_query(self, dspy_models):
        """Test search query generation."""
        # Test validation analyzer
        query = dspy_models._generate_search_query(
            "validation_analyzer", 
            {}, 
            {"data_type": "workflow"}
        )
        assert "validation best practices workflow" in query
        
        # Test workflow optimizer
        query = dspy_models._generate_search_query(
            "workflow_optimizer",
            {},
            {"optimization_target": "speed"}
        )
        assert "GitHub Actions workflow optimization speed" in query
        
        # Test issue diagnoser
        query = dspy_models._generate_search_query(
            "issue_diagnoser",
            "workflow failed",
            {}
        )
        assert "GitHub Actions troubleshooting" in query
    
    @pytest.mark.asyncio
    async def test_web_search_method(self, dspy_models):
        """Test web search method."""
        results = await dspy_models.web_search("test query", max_results=2)
        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)


class TestDSPyAnalysis:
    """Test DSPy analysis functionality."""
    
    @pytest.fixture
    def mock_dspy_models(self):
        """Create mock DSPy models."""
        models = UvmgrDSPyModels()
        # Mock the models to avoid actual DSPy calls
        models.models = {}
        models.predictors = {}
        return models
    
    @pytest.mark.asyncio
    async def test_run_analysis_no_models(self, mock_dspy_models):
        """Test running analysis with no models."""
        result = await mock_dspy_models.run_analysis(
            "validation_analyzer",
            {"test": "data"},
            {"context": "test"}
        )
        assert "error" in result
        assert "DSPy models not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_analysis_with_web_search(self):
        """Test running analysis with web search enabled."""
        with patch('uvmgr.mcp.models.UvmgrDSPyModels') as mock_class:
            mock_instance = Mock()
            mock_instance.models = {"validation_analyzer": Mock()}
            mock_instance.predictors = {"validation_analyzer_cot": Mock()}
            mock_instance.web_search = AsyncMock()
            mock_instance.web_search.search.return_value = [
                {"title": "Test", "url": "http://test.com", "snippet": "Test snippet"}
            ]
            mock_instance._generate_search_query.return_value = "test query"
            
            mock_class.return_value = mock_instance
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                {"test": "data"},
                {"enable_web_search": True},
                "cot",
                True
            )
            
            # Verify web search was called
            mock_instance.web_search.search.assert_called_once_with("test query")
    
    @pytest.mark.asyncio
    async def test_run_analysis_without_web_search(self):
        """Test running analysis without web search."""
        with patch('uvmgr.mcp.models.UvmgrDSPyModels') as mock_class:
            mock_instance = Mock()
            mock_instance.models = {"validation_analyzer": Mock()}
            mock_instance.predictors = {"validation_analyzer_cot": Mock()}
            mock_instance.web_search = AsyncMock()
            
            mock_class.return_value = mock_instance
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                {"test": "data"},
                {"enable_web_search": False},
                "cot",
                False
            )
            
            # Verify web search was not called
            mock_instance.web_search.search.assert_not_called()


class TestModelSpecificAnalysis:
    """Test specific model analysis scenarios."""
    
    @pytest.mark.asyncio
    async def test_validation_analyzer_analysis(self):
        """Test validation analyzer with specific data."""
        validation_data = {
            "workflow_runs": [
                {"status": "success", "duration": 120},
                {"status": "failure", "duration": 300}
            ],
            "validation_score": 0.85
        }
        
        context = {
            "data_type": "workflow_validation",
            "repository": "test/repo",
            "time_period": "1d"
        }
        
        with patch('uvmgr.mcp.models.run_dspy_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "analysis": "Validation analysis result",
                "confidence_score": 0.9,
                "key_insights": ["Good performance", "Some failures"],
                "recommendations": ["Optimize slow workflows"],
                "web_insights": ["Industry best practices"]
            }
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                validation_data,
                context,
                "cot",
                True
            )
            
            assert "analysis" in result
            assert "confidence_score" in result
            assert "key_insights" in result
            assert "recommendations" in result
            assert "web_insights" in result
    
    @pytest.mark.asyncio
    async def test_workflow_optimizer_analysis(self):
        """Test workflow optimizer with specific data."""
        workflow_data = {
            "workflows": [
                {"name": "CI", "runs": 100, "avg_duration": 300},
                {"name": "CD", "runs": 50, "avg_duration": 600}
            ],
            "performance_metrics": {
                "total_runs": 150,
                "success_rate": 0.95,
                "avg_duration": 400
            }
        }
        
        context = {
            "optimization_target": "performance",
            "constraints": {"max_duration": 500},
            "performance_metrics": {"current_avg": 400, "target_avg": 200}
        }
        
        with patch('uvmgr.mcp.models.run_dspy_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "optimization_plan": "Detailed optimization plan",
                "expected_improvements": "50% faster execution",
                "implementation_steps": ["Step 1", "Step 2"],
                "web_best_practices": ["Use caching", "Parallel jobs"]
            }
            
            result = await run_dspy_analysis(
                "workflow_optimizer",
                workflow_data,
                context,
                "react",
                True
            )
            
            assert "optimization_plan" in result
            assert "expected_improvements" in result
            assert "implementation_steps" in result
            assert "web_best_practices" in result
    
    @pytest.mark.asyncio
    async def test_issue_diagnoser_analysis(self):
        """Test issue diagnoser with specific data."""
        issues = [
            "Workflow timeout after 6 hours",
            "Dependency resolution failed",
            "Permission denied for secrets"
        ]
        
        context = {
            "system_state": {
                "python_version": "3.12",
                "platform": "ubuntu-latest",
                "runner_type": "github-hosted"
            },
            "recent_changes": ["Updated dependencies", "Modified workflow"]
        }
        
        with patch('uvmgr.mcp.models.run_dspy_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "root_cause_analysis": "Timeout due to large dependency tree",
                "issue_prioritization": ["High", "Medium", "Low"],
                "solution_strategies": ["Use dependency caching", "Split workflow"],
                "web_solutions": ["GitHub timeout solutions", "Dependency optimization"]
            }
            
            result = await run_dspy_analysis(
                "issue_diagnoser",
                issues,
                context,
                "react",
                True
            )
            
            assert "root_cause_analysis" in result
            assert "issue_prioritization" in result
            assert "solution_strategies" in result
            assert "web_solutions" in result


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_analysis_with_exception(self):
        """Test analysis when DSPy raises an exception."""
        with patch('uvmgr.mcp.models.UvmgrDSPyModels') as mock_class:
            mock_instance = Mock()
            mock_instance.models = {"validation_analyzer": Mock()}
            mock_instance.predictors = {"validation_analyzer_cot": Mock()}
            mock_instance.predictors["validation_analyzer_cot"].side_effect = Exception("DSPy error")
            
            mock_class.return_value = mock_instance
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                {"test": "data"},
                {},
                "cot"
            )
            
            assert "error" in result
            assert "DSPy error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_web_search_with_exception(self):
        """Test web search when it raises an exception."""
        with patch('uvmgr.mcp.models.UvmgrDSPyModels') as mock_class:
            mock_instance = Mock()
            mock_instance.models = {"validation_analyzer": Mock()}
            mock_instance.predictors = {"validation_analyzer_cot": Mock()}
            mock_instance.web_search = AsyncMock()
            mock_instance.web_search.search.side_effect = Exception("Search failed")
            
            mock_class.return_value = mock_instance
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                {"test": "data"},
                {"enable_web_search": True},
                "cot",
                True
            )
            
            # Should still work even if web search fails
            assert "error" not in result or "Search failed" not in str(result)


class TestIntegration:
    """Integration tests for the complete flow."""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self):
        """Test complete analysis flow from data to insights."""
        # Test data
        test_data = {
            "workflow_runs": [
                {"id": 1, "status": "success", "duration": 120},
                {"id": 2, "status": "failure", "duration": 300},
                {"id": 3, "status": "success", "duration": 180}
            ],
            "validation_metrics": {
                "success_rate": 0.67,
                "avg_duration": 200,
                "failure_count": 1
            }
        }
        
        context = {
            "data_type": "workflow_analysis",
            "repository": "test/repo",
            "time_period": "1d",
            "enable_web_search": True
        }
        
        # Mock the complete flow
        with patch('uvmgr.mcp.models.run_dspy_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "analysis": "Comprehensive workflow analysis",
                "confidence_score": 0.92,
                "key_insights": [
                    "67% success rate needs improvement",
                    "Average duration is acceptable",
                    "One failure needs investigation"
                ],
                "recommendations": [
                    "Investigate the failed workflow run",
                    "Consider adding retry logic",
                    "Monitor duration trends"
                ],
                "web_insights": [
                    "Industry average success rate is 85%",
                    "Best practices for workflow reliability"
                ],
                "risk_assessment": "Medium risk due to failure rate"
            }
            
            result = await run_dspy_analysis(
                "validation_analyzer",
                test_data,
                context,
                "cot",
                True
            )
            
            # Verify comprehensive result
            assert "analysis" in result
            assert "confidence_score" in result
            assert "key_insights" in result
            assert "recommendations" in result
            assert "web_insights" in result
            assert "risk_assessment" in result
            
            # Verify data integrity
            assert result["confidence_score"] == 0.92
            assert len(result["key_insights"]) == 3
            assert len(result["recommendations"]) == 3
            assert len(result["web_insights"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 