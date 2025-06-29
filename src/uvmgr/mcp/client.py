"""
MCP Client for uvmgr with DSPy integration.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import aiohttp
from fastmcp import Client

import dspy
from dspy import Predict, Signature, InputField, OutputField
from dspy.teleprompt import BootstrapFewShot

from uvmgr.core.telemetry import span, record_exception

logger = logging.getLogger(__name__)


class UvmgrMCPClient:
    """MCP Client for uvmgr with DSPy integration."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = Client(server_url)
        self.dspy_models = self._initialize_dspy_models()
    
    def _initialize_dspy_models(self) -> Dict[str, Any]:
        """Initialize DSPy models for client-side operations."""
        models = {}
        
        # Query optimizer
        class QueryOptimizer(dspy.Signature):
            """Optimize queries for better results."""
            user_query = InputField(desc="User's original query")
            context = InputField(desc="Context and constraints")
            optimized_query = OutputField(desc="Optimized query parameters")
            reasoning = OutputField(desc="Reasoning for optimization")
        
        models["query_optimizer"] = QueryOptimizer()
        
        # Result interpreter
        class ResultInterpreter(dspy.Signature):
            """Interpret and explain results."""
            raw_result = InputField(desc="Raw result from server")
            user_context = InputField(desc="User's context and needs")
            interpretation = OutputField(desc="Human-readable interpretation")
            key_insights = OutputField(desc="Key insights and takeaways")
            next_actions = OutputField(desc="Recommended next actions")
        
        models["result_interpreter"] = ResultInterpreter()
        
        # Error analyzer
        class ErrorAnalyzer(dspy.Signature):
            """Analyze errors and suggest solutions."""
            error_message = InputField(desc="Error message from server")
            context = InputField(desc="Context when error occurred")
            analysis = OutputField(desc="Error analysis and root cause")
            solutions = OutputField(desc="Suggested solutions")
            prevention = OutputField(desc="Prevention strategies")
        
        models["error_analyzer"] = ErrorAnalyzer()
        
        return models
    
    async def get_github_actions_status(
        self, 
        owner: str, 
        repo: str, 
        validation_level: str = "strict",
        optimize_query: bool = True
    ) -> Dict[str, Any]:
        """Get GitHub Actions status with optional query optimization."""
        with span("mcp_client.github_actions_status", owner=owner, repo=repo):
            try:
                # Optimize query if requested
                if optimize_query:
                    optimizer = self.dspy_models["query_optimizer"]
                    optimization = await self._run_dspy_analysis(
                        optimizer,
                        f"Get GitHub Actions status for {owner}/{repo}",
                        {"validation_level": validation_level}
                    )
                    # Use optimized parameters if available
                    if optimization.get("optimized_query"):
                        # Apply optimizations
                        pass
                
                # Make request to server
                result = await self.client.call_tool(
                    "get_github_actions_status",
                    {
                        "owner": owner,
                        "repo": repo,
                        "validation_level": validation_level,
                        "show_validation": True
                    }
                )
                
                # Interpret results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": f"Checking status for {owner}/{repo}"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                
                # Analyze error
                analyzer = self.dspy_models["error_analyzer"]
                error_analysis = await self._run_dspy_analysis(
                    analyzer,
                    str(e),
                    {"context": f"Getting status for {owner}/{repo}"}
                )
                
                return {
                    "status": "error",
                    "message": str(e),
                    "analysis": error_analysis
                }
    
    async def list_workflows(
        self, 
        owner: str, 
        repo: str, 
        validation_level: str = "strict"
    ) -> Dict[str, Any]:
        """List workflows with intelligent result interpretation."""
        with span("mcp_client.list_workflows", owner=owner, repo=repo):
            try:
                result = await self.client.call_tool(
                    "list_workflows",
                    {
                        "owner": owner,
                        "repo": repo,
                        "validation_level": validation_level
                    }
                )
                
                # Interpret results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": f"Listing workflows for {owner}/{repo}"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                return {"status": "error", "message": str(e)}
    
    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 30,
        validation_level: str = "strict"
    ) -> Dict[str, Any]:
        """Get workflow runs with optimization and interpretation."""
        with span("mcp_client.get_workflow_runs", owner=owner, repo=repo):
            try:
                # Optimize query parameters
                optimizer = self.dspy_models["query_optimizer"]
                optimization = await self._run_dspy_analysis(
                    optimizer,
                    f"Get workflow runs for {owner}/{repo}",
                    {
                        "workflow_id": workflow_id,
                        "status": status,
                        "per_page": per_page
                    }
                )
                
                result = await self.client.call_tool(
                    "get_workflow_runs",
                    {
                        "owner": owner,
                        "repo": repo,
                        "workflow_id": workflow_id,
                        "status": status,
                        "per_page": per_page,
                        "validation_level": validation_level
                    }
                )
                
                # Interpret results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": f"Analyzing workflow runs for {owner}/{repo}"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "optimization": optimization,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                return {"status": "error", "message": str(e)}
    
    async def validate_data(
        self,
        data: Dict[str, Any],
        validation_level: str = "strict",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate data with intelligent analysis."""
        with span("mcp_client.validate_data"):
            try:
                result = await self.client.call_tool(
                    "validate_data",
                    {
                        "data": data,
                        "validation_level": validation_level,
                        "context": context or {}
                    }
                )
                
                # Interpret validation results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": "Data validation analysis"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e)
                return {"status": "error", "message": str(e)}
    
    async def get_validation_dashboard(
        self,
        owner: str,
        repo: str,
        time_window: str = "1h",
        validation_level: str = "strict"
    ) -> Dict[str, Any]:
        """Get validation dashboard with insights."""
        with span("mcp_client.validation_dashboard", owner=owner, repo=repo):
            try:
                result = await self.client.call_tool(
                    "get_validation_dashboard",
                    {
                        "owner": owner,
                        "repo": repo,
                        "time_window": time_window,
                        "validation_level": validation_level
                    }
                )
                
                # Interpret dashboard results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": f"Validation dashboard for {owner}/{repo}"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                return {"status": "error", "message": str(e)}
    
    async def optimize_workflows(
        self,
        owner: str,
        repo: str,
        optimization_target: str = "performance"
    ) -> Dict[str, Any]:
        """Optimize workflows with intelligent analysis."""
        with span("mcp_client.optimize_workflows", owner=owner, repo=repo):
            try:
                result = await self.client.call_tool(
                    "optimize_workflows",
                    {
                        "owner": owner,
                        "repo": repo,
                        "optimization_target": optimization_target
                    }
                )
                
                # Interpret optimization results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": f"Workflow optimization for {owner}/{repo}"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                return {"status": "error", "message": str(e)}
    
    async def diagnose_validation_issues(
        self,
        issues: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Diagnose validation issues with intelligent analysis."""
        with span("mcp_client.diagnose_issues"):
            try:
                result = await self.client.call_tool(
                    "diagnose_validation_issues",
                    {
                        "issues": issues,
                        "context": context
                    }
                )
                
                # Interpret diagnosis results
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": "Validation issue diagnosis"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e)
                return {"status": "error", "message": str(e)}
    
    async def get_recommendations(
        self,
        current_config: Dict[str, Any],
        usage_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get intelligent recommendations."""
        with span("mcp_client.get_recommendations"):
            try:
                result = await self.client.call_tool(
                    "get_recommendations",
                    {
                        "current_config": current_config,
                        "usage_patterns": usage_patterns
                    }
                )
                
                # Interpret recommendations
                interpreter = self.dspy_models["result_interpreter"]
                interpretation = await self._run_dspy_analysis(
                    interpreter,
                    result,
                    {"user_context": "Configuration recommendations"}
                )
                
                return {
                    "status": "success",
                    "data": result,
                    "interpretation": interpretation
                }
                
            except Exception as e:
                record_exception(e)
                return {"status": "error", "message": str(e)}
    
    async def _run_dspy_analysis(self, model: dspy.Signature, data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run DSPy analysis with error handling."""
        try:
            # Configure DSPy with a simple predictor
            predictor = dspy.Predict(model)
            
            # Run prediction
            result = predictor(data=data, context=context)
            
            return {
                "optimized_query": getattr(result, 'optimized_query', None),
                "reasoning": getattr(result, 'reasoning', None),
                "interpretation": getattr(result, 'interpretation', None),
                "key_insights": getattr(result, 'key_insights', None),
                "next_actions": getattr(result, 'next_actions', None),
                "analysis": getattr(result, 'analysis', None),
                "solutions": getattr(result, 'solutions', None),
                "prevention": getattr(result, 'prevention', None)
            }
        except Exception as e:
            logger.warning(f"DSPy analysis failed: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False


# Example usage
async def main():
    """Example usage of the MCP client."""
    client = UvmgrMCPClient()
    
    # Check server health
    if not await client.health_check():
        print("❌ MCP server is not available")
        return
    
    # Get GitHub Actions status
    result = await client.get_github_actions_status("your-org", "your-repo")
    print(json.dumps(result, indent=2))
    
    # Get validation dashboard
    dashboard = await client.get_validation_dashboard("your-org", "your-repo")
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 