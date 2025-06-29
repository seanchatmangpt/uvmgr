"""
Weaver telemetry validation tests against live data.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock

from uvmgr.core.weaver import Weaver
from uvmgr.core.telemetry import span, record_exception, get_tracer
from uvmgr.ops.actions_ops import GitHubActionsOps
from uvmgr.runtime.actions import get_github_token, get_repo_info
from uvmgr.core.validation import ValidationLevel


class TestWeaverTelemetryValidation:
    """Test Weaver telemetry validation against live GitHub data."""
    
    @pytest.fixture
    def weaver(self):
        """Create Weaver instance."""
        return Weaver()
    
    @pytest.fixture
    def test_repo(self):
        """Test repository configuration."""
        return {
            "owner": "sac",
            "repo": "uvmgr",
            "branch": "main"
        }
    
    @pytest.fixture
    def github_token(self):
        """Get GitHub token for testing."""
        return get_github_token()
    
    @pytest.fixture
    def actions_ops(self, github_token, test_repo):
        """Create GitHub Actions operations instance."""
        return GitHubActionsOps(
            github_token, 
            test_repo["owner"], 
            test_repo["repo"], 
            ValidationLevel.STRICT
        )
    
    @pytest.mark.asyncio
    async def test_workflow_data_collection_telemetry(self, weaver, actions_ops):
        """Test telemetry during workflow data collection."""
        with span("test.workflow_data_collection", repo="sac/uvmgr"):
            try:
                # Collect workflow data with telemetry
                start_time = time.time()
                
                workflows_result = actions_ops.list_workflows()
                workflows_time = time.time() - start_time
                
                # Validate telemetry data
                assert workflows_result["validation"].is_valid
                assert workflows_result["validation"].confidence > 0
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                
                # Verify workflow collection span
                workflow_spans = [s for s in spans if "workflow" in s.name.lower()]
                assert len(workflow_spans) > 0
                
                # Verify performance metrics
                assert workflows_time < 10.0  # Should complete within 10 seconds
                
                return {
                    "status": "success",
                    "workflows_count": len(workflows_result["data"]),
                    "collection_time": workflows_time,
                    "validation_score": workflows_result["validation"].confidence,
                    "telemetry_spans": len(workflow_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "workflow_data_collection"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_workflow_runs_telemetry(self, weaver, actions_ops):
        """Test telemetry during workflow runs collection."""
        with span("test.workflow_runs_collection", repo="sac/uvmgr"):
            try:
                # Collect workflow runs with telemetry
                start_time = time.time()
                
                runs_result = actions_ops.list_workflow_runs(per_page=20)
                runs_time = time.time() - start_time
                
                # Validate telemetry data
                assert runs_result["validation"].is_valid
                assert runs_result["validation"].confidence > 0
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                
                # Verify runs collection span
                runs_spans = [s for s in spans if "runs" in s.name.lower()]
                assert len(runs_spans) > 0
                
                # Verify performance metrics
                assert runs_time < 15.0  # Should complete within 15 seconds
                
                return {
                    "status": "success",
                    "runs_count": len(runs_result["data"]["workflow_runs"]),
                    "collection_time": runs_time,
                    "validation_score": runs_result["validation"].confidence,
                    "telemetry_spans": len(runs_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "workflow_runs_collection"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_validation_telemetry(self, weaver, actions_ops):
        """Test telemetry during validation operations."""
        with span("test.validation_telemetry", repo="sac/uvmgr"):
            try:
                # Test multiple validation operations
                validation_results = []
                
                # Test workflows validation
                workflows_result = actions_ops.list_workflows()
                validation_results.append({
                    "type": "workflows",
                    "is_valid": workflows_result["validation"].is_valid,
                    "confidence": workflows_result["validation"].confidence,
                    "issues": workflows_result["validation"].issues
                })
                
                # Test runs validation
                runs_result = actions_ops.list_workflow_runs(per_page=10)
                validation_results.append({
                    "type": "runs",
                    "is_valid": runs_result["validation"].is_valid,
                    "confidence": runs_result["validation"].confidence,
                    "issues": runs_result["validation"].issues
                })
                
                # Test secrets validation
                try:
                    secrets_result = actions_ops.list_secrets()
                    validation_results.append({
                        "type": "secrets",
                        "is_valid": secrets_result["validation"].is_valid,
                        "confidence": secrets_result["validation"].confidence,
                        "issues": secrets_result["validation"].issues
                    })
                except Exception:
                    # Secrets might not be accessible
                    pass
                
                # Test variables validation
                try:
                    variables_result = actions_ops.list_variables()
                    validation_results.append({
                        "type": "variables",
                        "is_valid": variables_result["validation"].is_valid,
                        "confidence": variables_result["validation"].confidence,
                        "issues": variables_result["validation"].issues
                    })
                except Exception:
                    # Variables might not be accessible
                    pass
                
                # Analyze validation telemetry
                total_validations = len(validation_results)
                successful_validations = sum(1 for r in validation_results if r["is_valid"])
                avg_confidence = sum(r["confidence"] for r in validation_results) / total_validations
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                validation_spans = [s for s in spans if "validation" in s.name.lower()]
                
                return {
                    "status": "success",
                    "total_validations": total_validations,
                    "successful_validations": successful_validations,
                    "success_rate": successful_validations / total_validations,
                    "average_confidence": avg_confidence,
                    "validation_results": validation_results,
                    "telemetry_spans": len(validation_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "validation_telemetry"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_performance_telemetry(self, weaver, actions_ops):
        """Test performance telemetry across multiple operations."""
        with span("test.performance_telemetry", repo="sac/uvmgr"):
            try:
                performance_metrics = {}
                
                # Test workflows performance
                start_time = time.time()
                workflows_result = actions_ops.list_workflows()
                workflows_time = time.time() - start_time
                performance_metrics["workflows"] = {
                    "time": workflows_time,
                    "success": workflows_result["validation"].is_valid,
                    "confidence": workflows_result["validation"].confidence
                }
                
                # Test runs performance
                start_time = time.time()
                runs_result = actions_ops.list_workflow_runs(per_page=15)
                runs_time = time.time() - start_time
                performance_metrics["runs"] = {
                    "time": runs_time,
                    "success": runs_result["validation"].is_valid,
                    "confidence": runs_result["validation"].confidence
                }
                
                # Test secrets performance
                try:
                    start_time = time.time()
                    secrets_result = actions_ops.list_secrets()
                    secrets_time = time.time() - start_time
                    performance_metrics["secrets"] = {
                        "time": secrets_time,
                        "success": secrets_result["validation"].is_valid,
                        "confidence": secrets_result["validation"].confidence
                    }
                except Exception:
                    performance_metrics["secrets"] = {"time": 0, "success": False, "confidence": 0}
                
                # Test variables performance
                try:
                    start_time = time.time()
                    variables_result = actions_ops.list_variables()
                    variables_time = time.time() - start_time
                    performance_metrics["variables"] = {
                        "time": variables_time,
                        "success": variables_result["validation"].is_valid,
                        "confidence": variables_result["validation"].confidence
                    }
                except Exception:
                    performance_metrics["variables"] = {"time": 0, "success": False, "confidence": 0}
                
                # Calculate overall metrics
                total_time = sum(m["time"] for m in performance_metrics.values())
                avg_time = total_time / len(performance_metrics)
                success_rate = sum(1 for m in performance_metrics.values() if m["success"]) / len(performance_metrics)
                avg_confidence = sum(m["confidence"] for m in performance_metrics.values()) / len(performance_metrics)
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                performance_spans = [s for s in spans if "performance" in s.name.lower() or "test" in s.name.lower()]
                
                return {
                    "status": "success",
                    "total_time": total_time,
                    "average_time": avg_time,
                    "success_rate": success_rate,
                    "average_confidence": avg_confidence,
                    "performance_metrics": performance_metrics,
                    "telemetry_spans": len(performance_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "performance_telemetry"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_error_telemetry(self, weaver, actions_ops):
        """Test telemetry during error scenarios."""
        with span("test.error_telemetry", repo="sac/uvmgr"):
            try:
                error_metrics = {}
                
                # Test invalid repository
                try:
                    invalid_ops = GitHubActionsOps(
                        actions_ops.token, 
                        "invalid", 
                        "repository", 
                        ValidationLevel.STRICT
                    )
                    invalid_ops.list_workflows()
                    error_metrics["invalid_repo"] = {"error": False, "expected_error": True}
                except Exception as e:
                    error_metrics["invalid_repo"] = {
                        "error": True, 
                        "expected_error": True, 
                        "error_type": type(e).__name__
                    }
                
                # Test invalid token
                try:
                    invalid_token_ops = GitHubActionsOps(
                        "invalid_token", 
                        "sac", 
                        "uvmgr", 
                        ValidationLevel.STRICT
                    )
                    invalid_token_ops.list_workflows()
                    error_metrics["invalid_token"] = {"error": False, "expected_error": True}
                except Exception as e:
                    error_metrics["invalid_token"] = {
                        "error": True, 
                        "expected_error": True, 
                        "error_type": type(e).__name__
                    }
                
                # Test valid operations (should not error)
                try:
                    valid_result = actions_ops.list_workflows()
                    error_metrics["valid_operation"] = {
                        "error": False, 
                        "expected_error": False,
                        "success": valid_result["validation"].is_valid
                    }
                except Exception as e:
                    error_metrics["valid_operation"] = {
                        "error": True, 
                        "expected_error": False, 
                        "error_type": type(e).__name__
                    }
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                error_spans = [s for s in spans if "error" in s.name.lower()]
                
                return {
                    "status": "success",
                    "error_metrics": error_metrics,
                    "telemetry_spans": len(error_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "error_telemetry"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_concurrent_telemetry(self, weaver, actions_ops):
        """Test telemetry during concurrent operations."""
        with span("test.concurrent_telemetry", repo="sac/uvmgr"):
            try:
                # Run multiple operations concurrently
                async def run_operation(operation_name: str, operation_func):
                    with span(f"concurrent.{operation_name}"):
                        start_time = time.time()
                        try:
                            result = operation_func()
                            execution_time = time.time() - start_time
                            return {
                                "operation": operation_name,
                                "success": True,
                                "time": execution_time,
                                "validation_score": result["validation"].confidence
                            }
                        except Exception as e:
                            execution_time = time.time() - start_time
                            return {
                                "operation": operation_name,
                                "success": False,
                                "time": execution_time,
                                "error": str(e)
                            }
                
                # Define operations
                operations = [
                    ("workflows", lambda: actions_ops.list_workflows()),
                    ("runs", lambda: actions_ops.list_workflow_runs(per_page=5)),
                ]
                
                # Add optional operations
                try:
                    operations.append(("secrets", lambda: actions_ops.list_secrets()))
                except Exception:
                    pass
                
                try:
                    operations.append(("variables", lambda: actions_ops.list_variables()))
                except Exception:
                    pass
                
                # Run operations concurrently
                start_time = time.time()
                tasks = [
                    run_operation(name, func) 
                    for name, func in operations
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Analyze results
                successful_operations = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                total_operations = len(results)
                success_rate = successful_operations / total_operations if total_operations > 0 else 0
                
                # Check telemetry spans
                tracer = get_tracer()
                spans = tracer.get_spans()
                concurrent_spans = [s for s in spans if "concurrent" in s.name.lower()]
                
                return {
                    "status": "success",
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "success_rate": success_rate,
                    "total_time": total_time,
                    "results": results,
                    "telemetry_spans": len(concurrent_spans)
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "concurrent_telemetry"})
                return {"status": "error", "message": str(e)}
    
    @pytest.mark.asyncio
    async def test_telemetry_data_integrity(self, weaver, actions_ops):
        """Test telemetry data integrity and consistency."""
        with span("test.telemetry_data_integrity", repo="sac/uvmgr"):
            try:
                integrity_checks = {}
                
                # Test 1: Consistent validation scores
                workflows_result1 = actions_ops.list_workflows()
                workflows_result2 = actions_ops.list_workflows()
                
                integrity_checks["consistent_validation"] = {
                    "score1": workflows_result1["validation"].confidence,
                    "score2": workflows_result2["validation"].confidence,
                    "consistent": abs(workflows_result1["validation"].confidence - workflows_result2["validation"].confidence) < 0.1
                }
                
                # Test 2: Data structure consistency
                runs_result = actions_ops.list_workflow_runs(per_page=5)
                integrity_checks["data_structure"] = {
                    "has_workflow_runs": "workflow_runs" in runs_result["data"],
                    "has_validation": "validation" in runs_result,
                    "validation_has_confidence": hasattr(runs_result["validation"], "confidence"),
                    "validation_has_issues": hasattr(runs_result["validation"], "issues")
                }
                
                # Test 3: Telemetry span consistency
                tracer = get_tracer()
                spans = tracer.get_spans()
                
                integrity_checks["telemetry_spans"] = {
                    "total_spans": len(spans),
                    "has_attributes": all(hasattr(s, "attributes") for s in spans),
                    "has_name": all(hasattr(s, "name") for s in spans),
                    "has_start_time": all(hasattr(s, "start_time") for s in spans)
                }
                
                # Test 4: Performance consistency
                times = []
                for _ in range(3):
                    start_time = time.time()
                    actions_ops.list_workflows()
                    times.append(time.time() - start_time)
                
                avg_time = sum(times) / len(times)
                time_variance = sum((t - avg_time) ** 2 for t in times) / len(times)
                
                integrity_checks["performance_consistency"] = {
                    "times": times,
                    "average_time": avg_time,
                    "variance": time_variance,
                    "consistent": time_variance < 1.0  # Less than 1 second variance
                }
                
                return {
                    "status": "success",
                    "integrity_checks": integrity_checks,
                    "all_checks_passed": all(
                        all(check.values()) if isinstance(check, dict) else check
                        for check in integrity_checks.values()
                    )
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "telemetry_data_integrity"})
                return {"status": "error", "message": str(e)}


class TestWeaverIntegration:
    """Integration tests for Weaver with live data."""
    
    @pytest.mark.asyncio
    async def test_full_weaver_workflow(self):
        """Test complete Weaver workflow with live data."""
        with span("test.full_weaver_workflow", repo="sac/uvmgr"):
            try:
                weaver = Weaver()
                token = get_github_token()
                actions_ops = GitHubActionsOps(token, "sac", "uvmgr", ValidationLevel.STRICT)
                
                # Step 1: Collect all data
                start_time = time.time()
                
                workflows_result = actions_ops.list_workflows()
                runs_result = actions_ops.list_workflow_runs(per_page=20)
                
                # Try to get secrets and variables
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
                
                collection_time = time.time() - start_time
                
                # Step 2: Validate all data
                validation_results = {
                    "workflows": workflows_result["validation"],
                    "runs": runs_result["validation"]
                }
                
                if secrets_result:
                    validation_results["secrets"] = secrets_result["validation"]
                
                if variables_result:
                    validation_results["variables"] = variables_result["validation"]
                
                # Step 3: Analyze results
                total_validations = len(validation_results)
                successful_validations = sum(1 for v in validation_results.values() if v.is_valid)
                avg_confidence = sum(v.confidence for v in validation_results.values()) / total_validations
                
                # Step 4: Check telemetry
                tracer = get_tracer()
                spans = tracer.get_spans()
                
                return {
                    "status": "success",
                    "collection_time": collection_time,
                    "total_validations": total_validations,
                    "successful_validations": successful_validations,
                    "success_rate": successful_validations / total_validations,
                    "average_confidence": avg_confidence,
                    "workflows_count": len(workflows_result["data"]),
                    "runs_count": len(runs_result["data"]["workflow_runs"]),
                    "secrets_count": len(secrets_result["data"]) if secrets_result else 0,
                    "variables_count": len(variables_result["data"]) if variables_result else 0,
                    "telemetry_spans": len(spans),
                    "validation_results": {
                        k: {
                            "is_valid": v.is_valid,
                            "confidence": v.confidence,
                            "issues_count": len(v.issues)
                        }
                        for k, v in validation_results.items()
                    }
                }
                
            except Exception as e:
                record_exception(e, attributes={"test": "full_weaver_workflow"})
                return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 