"""
Weaver module for uvmgr telemetry and data collection.

This module provides the Weaver class that handles data collection,
telemetry, and integration between different components of uvmgr.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from uvmgr.core.telemetry import span, record_exception, get_tracer
from uvmgr.ops.actions_ops import GitHubActionsOps
from uvmgr.runtime.actions import get_github_token
from uvmgr.core.validation import ValidationLevel

logger = logging.getLogger(__name__)


class Weaver:
    """
    Weaver class for data collection and telemetry.
    
    The Weaver class provides a unified interface for collecting data
    from various sources, managing telemetry, and integrating different
    components of the uvmgr system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Weaver instance."""
        self.config = config or {}
        self.tracer = get_tracer()
        self.data_cache = {}
        self.telemetry_spans = []
        
    async def get_workflow_data(self, workflow_path: str) -> Dict[str, Any]:
        """Get workflow data with telemetry."""
        with span("weaver.get_workflow_data", workflow_path=workflow_path):
            try:
                # Simulate workflow data collection
                workflow_data = {
                    "path": workflow_path,
                    "name": workflow_path.split("/")[-1],
                    "last_modified": datetime.now().isoformat(),
                    "size": 1024,
                    "content": "# Workflow content would be here"
                }
                
                # Cache the data
                self.data_cache[workflow_path] = workflow_data
                
                return workflow_data
                
            except Exception as e:
                record_exception(e, attributes={"workflow_path": workflow_path})
                raise
    
    async def collect_github_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Collect GitHub data with telemetry."""
        with span("weaver.collect_github_data", owner=owner, repo=repo):
            try:
                token = get_github_token()
                if not token:
                    return {"error": "No GitHub token available"}
                
                actions_ops = GitHubActionsOps(token, owner, repo, ValidationLevel.STRICT)
                
                # Collect workflows
                workflows_result = actions_ops.list_workflows()
                
                # Collect workflow runs
                runs_result = actions_ops.list_workflow_runs(per_page=20)
                
                # Try to collect secrets and variables
                secrets_result = None
                variables_result = None
                
                try:
                    secrets_result = actions_ops.list_secrets()
                except Exception:
                    pass
                
                try:
                    variables_result = actions_ops.list_variables()
                except Exception:
                    pass
                
                return {
                    "workflows": workflows_result,
                    "runs": runs_result,
                    "secrets": secrets_result,
                    "variables": variables_result,
                    "collection_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                record_exception(e, attributes={"owner": owner, "repo": repo})
                return {"error": str(e)}
    
    async def analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance data with telemetry."""
        with span("weaver.analyze_performance"):
            try:
                # Simulate performance analysis
                analysis = {
                    "total_workflows": len(data.get("workflows", {}).get("data", [])),
                    "total_runs": len(data.get("runs", {}).get("data", {}).get("workflow_runs", [])),
                    "success_rate": 0.95,
                    "average_duration": 300,
                    "performance_score": 85,
                    "recommendations": [
                        "Consider caching dependencies",
                        "Use parallel jobs where possible",
                        "Optimize workflow triggers"
                    ]
                }
                
                return analysis
                
            except Exception as e:
                record_exception(e)
                return {"error": str(e)}
    
    async def collect_telemetry_metrics(self) -> Dict[str, Any]:
        """Collect telemetry metrics."""
        with span("weaver.collect_telemetry_metrics"):
            try:
                metrics = {
                    "spans_generated": len(self.telemetry_spans),
                    "data_cache_size": len(self.data_cache),
                    "collection_time": datetime.now().isoformat(),
                    "system_info": {
                        "python_version": "3.12.0",
                        "platform": "darwin",
                        "uvmgr_version": "0.1.0"
                    }
                }
                
                return metrics
                
            except Exception as e:
                record_exception(e)
                return {"error": str(e)}
    
    def add_telemetry_span(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add a telemetry span to the collection."""
        span_info = {
            "name": span_name,
            "attributes": attributes or {},
            "timestamp": datetime.now().isoformat()
        }
        self.telemetry_spans.append(span_info)
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get a summary of telemetry data."""
        return {
            "total_spans": len(self.telemetry_spans),
            "span_types": list(set(span["name"] for span in self.telemetry_spans)),
            "data_cache_entries": len(self.data_cache),
            "last_activity": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Clean up resources."""
        with span("weaver.cleanup"):
            try:
                # Clear caches
                self.data_cache.clear()
                self.telemetry_spans.clear()
                
                logger.info("Weaver cleanup completed")
                
            except Exception as e:
                record_exception(e)
                logger.error(f"Weaver cleanup failed: {e}")


# Global Weaver instance
weaver_instance = Weaver()


def get_weaver() -> Weaver:
    """Get the global Weaver instance."""
    return weaver_instance 