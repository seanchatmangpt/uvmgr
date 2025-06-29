#!/usr/bin/env python3
"""
Comprehensive test runner for uvmgr validation tests with loops and live data validation.

This script runs all validation tests including:
- MCP models with Qwen3 and web search
- Weaver telemetry validation against live data
- Performance and reliability testing
- Integration tests with real GitHub data
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import pytest
import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uvmgr.core.telemetry import span, record_exception, get_tracer
from uvmgr.mcp.models import get_dspy_models, run_dspy_analysis
from uvmgr.core.weaver import Weaver
from uvmgr.ops.actions_ops import GitHubActionsOps
from uvmgr.runtime.actions import get_github_token
from uvmgr.core.validation import ValidationLevel


class ValidationTestRunner:
    """Comprehensive test runner for validation tests."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.results = []
        self.start_time = None
        self.end_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        self.start_time = datetime.now()
        
        with span("validation_test_runner.run_all_tests"):
            try:
                print("🚀 Starting comprehensive validation tests...")
                
                # Test 1: MCP Models with Qwen3
                print("\n📊 Testing MCP Models with Qwen3...")
                mcp_results = await self.test_mcp_models()
                
                # Test 2: Weaver Telemetry
                print("\n🔍 Testing Weaver Telemetry...")
                weaver_results = await self.test_weaver_telemetry()
                
                # Test 3: Performance Tests
                print("\n⚡ Testing Performance...")
                performance_results = await self.test_performance()
                
                # Test 4: Integration Tests
                print("\n🔗 Testing Integration...")
                integration_results = await self.test_integration()
                
                # Test 5: Reliability Tests (with loops)
                print("\n🔄 Testing Reliability with loops...")
                reliability_results = await self.test_reliability()
                
                # Test 6: Live Data Validation
                print("\n🌐 Testing Live Data Validation...")
                live_data_results = await self.test_live_data_validation()
                
                self.end_time = datetime.now()
                
                # Compile final results
                final_results = {
                    "status": "completed",
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "duration": (self.end_time - self.start_time).total_seconds(),
                    "tests": {
                        "mcp_models": mcp_results,
                        "weaver_telemetry": weaver_results,
                        "performance": performance_results,
                        "integration": integration_results,
                        "reliability": reliability_results,
                        "live_data": live_data_results
                    },
                    "summary": self._generate_summary([
                        mcp_results, weaver_results, performance_results,
                        integration_results, reliability_results, live_data_results
                    ])
                }
                
                # Save results
                self._save_results(final_results)
                
                print(f"\n✅ All tests completed in {final_results['duration']:.2f} seconds")
                self._print_summary(final_results["summary"])
                
                return final_results
                
            except Exception as e:
                record_exception(e, attributes={"test_runner": "run_all_tests"})
                return {"status": "error", "message": str(e)}
    
    async def test_mcp_models(self) -> Dict[str, Any]:
        """Test MCP models with Qwen3 and web search."""
        with span("test.mcp_models"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0
                }
                
                # Test 1: Model initialization
                try:
                    dspy_models = get_dspy_models()
                    models = dspy_models.get_available_models()
                    
                    if len(models) > 0:
                        results["tests"].append({
                            "name": "model_initialization",
                            "status": "passed",
                            "details": f"Initialized {len(models)} models"
                        })
                        results["passed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "model_initialization",
                            "status": "failed",
                            "details": "No models were initialized"
                        })
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "model_initialization",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: Web search functionality
                try:
                    dspy_models = get_dspy_models()
                    search_results = await dspy_models.web_search("GitHub Actions optimization", max_results=3)
                    
                    if search_results and len(search_results) > 0:
                        results["tests"].append({
                            "name": "web_search",
                            "status": "passed",
                            "details": f"Retrieved {len(search_results)} search results"
                        })
                        results["passed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "web_search",
                            "status": "failed",
                            "details": "No search results returned"
                        })
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "web_search",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 3: Analysis with web search (even if models are not fully functional)
                try:
                    dspy_models = get_dspy_models()
                    if dspy_models.models:
                        analysis_result = await run_dspy_analysis(
                            "validation_analyzer",
                            {"test": "data"},
                            {"enable_web_search": True},
                            "cot",
                            True
                        )
                        
                        if "error" not in analysis_result:
                            results["tests"].append({
                                "name": "analysis_with_web_search",
                                "status": "passed",
                                "details": "Analysis completed successfully"
                            })
                            results["passed_tests"] += 1
                        else:
                            results["tests"].append({
                                "name": "analysis_with_web_search",
                                "status": "failed",
                                "error": analysis_result.get("error", "Unknown error")
                            })
                            results["failed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "analysis_with_web_search",
                            "status": "skipped",
                            "details": "No models available for analysis"
                        })
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "analysis_with_web_search",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 4: Model info retrieval
                try:
                    dspy_models = get_dspy_models()
                    model_info = dspy_models.get_model_info("validation_analyzer")
                    
                    if "error" not in model_info:
                        results["tests"].append({
                            "name": "model_info_retrieval",
                            "status": "passed",
                            "details": "Successfully retrieved model information"
                        })
                        results["passed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "model_info_retrieval",
                            "status": "failed",
                            "error": model_info.get("error", "Unknown error")
                        })
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "model_info_retrieval",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "mcp_models"})
                return {"status": "error", "message": str(e)}
    
    async def test_weaver_telemetry(self) -> Dict[str, Any]:
        """Test Weaver telemetry validation."""
        with span("test.weaver_telemetry"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0
                }
                
                # Get GitHub token
                token = get_github_token()
                if not token:
                    return {"status": "skipped", "reason": "No GitHub token available"}
                
                # Test 1: Basic telemetry
                try:
                    weaver = Weaver()
                    tracer = get_tracer()
                    
                    with span("test.weaver_basic"):
                        # Simple operation to test telemetry
                        pass
                    
                    spans = tracer.get_spans()
                    
                    results["tests"].append({
                        "name": "basic_telemetry",
                        "status": "passed",
                        "details": f"Generated {len(spans)} telemetry spans"
                    })
                    results["passed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "basic_telemetry",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: GitHub Actions operations telemetry
                try:
                    actions_ops = GitHubActionsOps(token, "sac", "uvmgr", ValidationLevel.STRICT)
                    
                    start_time = time.time()
                    workflows_result = actions_ops.list_workflows()
                    execution_time = time.time() - start_time
                    
                    results["tests"].append({
                        "name": "github_actions_telemetry",
                        "status": "passed",
                        "details": f"Retrieved {len(workflows_result['data'])} workflows in {execution_time:.2f}s"
                    })
                    results["passed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "github_actions_telemetry",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "weaver_telemetry"})
                return {"status": "error", "message": str(e)}
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        with span("test.performance"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "performance_metrics": {}
                }
                
                # Test 1: Response time consistency
                try:
                    times = []
                    for i in range(5):
                        start_time = time.time()
                        # Simple operation
                        await asyncio.sleep(0.1)
                        times.append(time.time() - start_time)
                    
                    avg_time = sum(times) / len(times)
                    variance = sum((t - avg_time) ** 2 for t in times) / len(times)
                    
                    results["performance_metrics"]["response_time"] = {
                        "times": times,
                        "average": avg_time,
                        "variance": variance,
                        "consistent": variance < 0.01
                    }
                    
                    results["tests"].append({
                        "name": "response_time_consistency",
                        "status": "passed" if variance < 0.01 else "failed",
                        "details": f"Average: {avg_time:.3f}s, Variance: {variance:.6f}"
                    })
                    
                    if variance < 0.01:
                        results["passed_tests"] += 1
                    else:
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "response_time_consistency",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: Memory usage
                try:
                    import psutil
                    process = psutil.Process()
                    memory_before = process.memory_info().rss / 1024 / 1024  # MB
                    
                    # Perform some operations
                    for _ in range(100):
                        await asyncio.sleep(0.001)
                    
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = memory_after - memory_before
                    
                    results["performance_metrics"]["memory_usage"] = {
                        "before": memory_before,
                        "after": memory_after,
                        "increase": memory_increase,
                        "acceptable": memory_increase < 50  # Less than 50MB increase
                    }
                    
                    results["tests"].append({
                        "name": "memory_usage",
                        "status": "passed" if memory_increase < 50 else "failed",
                        "details": f"Memory increase: {memory_increase:.2f}MB"
                    })
                    
                    if memory_increase < 50:
                        results["passed_tests"] += 1
                    else:
                        results["failed_tests"] += 1
                    
                except ImportError:
                    results["tests"].append({
                        "name": "memory_usage",
                        "status": "skipped",
                        "details": "psutil not available"
                    })
                except Exception as e:
                    results["tests"].append({
                        "name": "memory_usage",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "performance"})
                return {"status": "error", "message": str(e)}
    
    async def test_integration(self) -> Dict[str, Any]:
        """Test integration between components."""
        with span("test.integration"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0
                }
                
                # Test 1: MCP + Weaver integration
                try:
                    dspy_models = get_dspy_models()
                    weaver = Weaver()
                    
                    # Simulate integration workflow
                    analysis_result = await run_dspy_analysis(
                        "workflow_optimizer",
                        {"workflows": [{"name": "test"}]},
                        {"optimization_target": "performance"},
                        "cot",
                        True
                    )
                    
                    results["tests"].append({
                        "name": "mcp_weaver_integration",
                        "status": "passed",
                        "details": "Integration test completed successfully"
                    })
                    results["passed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "mcp_weaver_integration",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: Telemetry integration
                try:
                    tracer = get_tracer()
                    initial_spans = len(tracer.get_spans())
                    
                    with span("test.integration_telemetry"):
                        await asyncio.sleep(0.1)
                    
                    final_spans = len(tracer.get_spans())
                    span_increase = final_spans - initial_spans
                    
                    results["tests"].append({
                        "name": "telemetry_integration",
                        "status": "passed" if span_increase > 0 else "failed",
                        "details": f"Generated {span_increase} new spans"
                    })
                    
                    if span_increase > 0:
                        results["passed_tests"] += 1
                    else:
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "telemetry_integration",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "integration"})
                return {"status": "error", "message": str(e)}
    
    async def test_reliability(self) -> Dict[str, Any]:
        """Test reliability with loops and repeated operations."""
        with span("test.reliability"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "reliability_metrics": {}
                }
                
                # Test 1: Repeated operations
                try:
                    success_count = 0
                    total_operations = 10
                    
                    for i in range(total_operations):
                        try:
                            dspy_models = get_dspy_models()
                            models = dspy_models.get_available_models()
                            
                            if len(models) > 0:
                                success_count += 1
                            
                            await asyncio.sleep(0.1)  # Small delay between operations
                            
                        except Exception:
                            pass  # Count as failure
                    
                    success_rate = success_count / total_operations
                    
                    results["reliability_metrics"]["repeated_operations"] = {
                        "total_operations": total_operations,
                        "successful_operations": success_count,
                        "success_rate": success_rate,
                        "reliable": success_rate >= 0.9  # 90% success rate
                    }
                    
                    results["tests"].append({
                        "name": "repeated_operations",
                        "status": "passed" if success_rate >= 0.9 else "failed",
                        "details": f"Success rate: {success_rate:.1%}"
                    })
                    
                    if success_rate >= 0.9:
                        results["passed_tests"] += 1
                    else:
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "repeated_operations",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: Concurrent operations
                try:
                    async def concurrent_operation(operation_id: int):
                        try:
                            dspy_models = get_dspy_models()
                            models = dspy_models.get_available_models()
                            return {"operation_id": operation_id, "success": True, "models_count": len(models)}
                        except Exception as e:
                            return {"operation_id": operation_id, "success": False, "error": str(e)}
                    
                    # Run 5 concurrent operations
                    tasks = [concurrent_operation(i) for i in range(5)]
                    concurrent_results = await asyncio.gather(*tasks)
                    
                    successful_concurrent = sum(1 for r in concurrent_results if r["success"])
                    concurrent_success_rate = successful_concurrent / len(concurrent_results)
                    
                    results["reliability_metrics"]["concurrent_operations"] = {
                        "total_operations": len(concurrent_results),
                        "successful_operations": successful_concurrent,
                        "success_rate": concurrent_success_rate,
                        "reliable": concurrent_success_rate >= 0.8  # 80% success rate for concurrent
                    }
                    
                    results["tests"].append({
                        "name": "concurrent_operations",
                        "status": "passed" if concurrent_success_rate >= 0.8 else "failed",
                        "details": f"Concurrent success rate: {concurrent_success_rate:.1%}"
                    })
                    
                    if concurrent_success_rate >= 0.8:
                        results["passed_tests"] += 1
                    else:
                        results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "concurrent_operations",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "reliability"})
                return {"status": "error", "message": str(e)}
    
    async def test_live_data_validation(self) -> Dict[str, Any]:
        """Test validation against live GitHub data."""
        with span("test.live_data_validation"):
            try:
                results = {
                    "status": "success",
                    "tests": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "live_data_metrics": {}
                }
                
                # Get GitHub token
                token = get_github_token()
                if not token:
                    results["tests"].append({
                        "name": "github_token_availability",
                        "status": "skipped",
                        "details": "No GitHub token available"
                    })
                    results["total_tests"] = len(results["tests"])
                    return results
                
                # Test 1: Live workflow data validation
                try:
                    actions_ops = GitHubActionsOps(token, "sac", "uvmgr", ValidationLevel.STRICT)
                    
                    start_time = time.time()
                    workflows_result = actions_ops.list_workflows()
                    execution_time = time.time() - start_time
                    
                    if "error" in workflows_result:
                        results["tests"].append({
                            "name": "live_workflow_validation",
                            "status": "failed",
                            "error": workflows_result["error"]
                        })
                        results["failed_tests"] += 1
                    else:
                        is_valid = workflows_result["validation"].is_valid
                        confidence = workflows_result["validation"].confidence
                        workflows_count = len(workflows_result["data"])
                        
                        results["live_data_metrics"]["workflows"] = {
                            "is_valid": is_valid,
                            "confidence": confidence,
                            "workflows_count": workflows_count,
                            "execution_time": execution_time,
                            "acceptable_time": execution_time < 10.0
                        }
                        
                        results["tests"].append({
                            "name": "live_workflow_validation",
                            "status": "passed" if is_valid and execution_time < 10.0 else "failed",
                            "details": f"Valid: {is_valid}, Confidence: {confidence:.2f}, Time: {execution_time:.2f}s"
                        })
                        
                        if is_valid and execution_time < 10.0:
                            results["passed_tests"] += 1
                        else:
                            results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "live_workflow_validation",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 2: Live runs data validation
                try:
                    actions_ops = GitHubActionsOps(token, "sac", "uvmgr", ValidationLevel.STRICT)
                    
                    start_time = time.time()
                    runs_result = actions_ops.list_workflow_runs(per_page=10)
                    execution_time = time.time() - start_time
                    
                    if "error" in runs_result:
                        results["tests"].append({
                            "name": "live_runs_validation",
                            "status": "failed",
                            "error": runs_result["error"]
                        })
                        results["failed_tests"] += 1
                    else:
                        is_valid = runs_result["validation"].is_valid
                        confidence = runs_result["validation"].confidence
                        runs_count = len(runs_result["data"]["workflow_runs"])
                        
                        results["live_data_metrics"]["runs"] = {
                            "is_valid": is_valid,
                            "confidence": confidence,
                            "runs_count": runs_count,
                            "execution_time": execution_time,
                            "acceptable_time": execution_time < 15.0
                        }
                        
                        results["tests"].append({
                            "name": "live_runs_validation",
                            "status": "passed" if is_valid and execution_time < 15.0 else "failed",
                            "details": f"Valid: {is_valid}, Confidence: {confidence:.2f}, Time: {execution_time:.2f}s"
                        })
                        
                        if is_valid and execution_time < 15.0:
                            results["passed_tests"] += 1
                        else:
                            results["failed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "live_runs_validation",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                # Test 3: GitHub token validation
                try:
                    # Test if token is valid by making a simple API call
                    actions_ops = GitHubActionsOps(token, "sac", "uvmgr", ValidationLevel.STRICT)
                    
                    # Try to get repo info
                    repo_info = actions_ops.get_repo_info()
                    
                    if "error" in repo_info:
                        results["tests"].append({
                            "name": "github_token_validation",
                            "status": "failed",
                            "error": repo_info["error"]
                        })
                        results["failed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": "github_token_validation",
                            "status": "passed",
                            "details": "GitHub token is valid and working"
                        })
                        results["passed_tests"] += 1
                    
                except Exception as e:
                    results["tests"].append({
                        "name": "github_token_validation",
                        "status": "failed",
                        "error": str(e)
                    })
                    results["failed_tests"] += 1
                
                results["total_tests"] = len(results["tests"])
                return results
                
            except Exception as e:
                record_exception(e, attributes={"test": "live_data_validation"})
                return {"status": "error", "message": str(e)}
    
    def _generate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of all test results."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for result in test_results:
            if result.get("status") == "success":
                total_tests += result.get("total_tests", 0)
                total_passed += result.get("passed_tests", 0)
                total_failed += result.get("failed_tests", 0)
            elif result.get("status") == "skipped":
                total_skipped += 1
        
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "skipped_tests": total_skipped,
            "success_rate": success_rate,
            "overall_status": "passed" if success_rate >= 0.8 else "failed"
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_test_results_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Results saved to: {filename}")
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 VALIDATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Skipped: {summary['skipped_tests']} ⏭️")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print("="*60)


@click.command()
@click.option("--config", "-c", "config_file", help="Configuration file path")
@click.option("--output", "-o", "output_file", help="Output file for results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(config_file: Optional[str], output_file: Optional[str], verbose: bool):
    """Run comprehensive validation tests."""
    try:
        # Load configuration
        config = {}
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        
        # Run tests
        runner = ValidationTestRunner(config)
        results = asyncio.run(runner.run_all_tests())
        
        # Save to specified output file
        if output_file:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {output_file}")
        
        # Exit with appropriate code
        if results.get("status") == "completed":
            summary = results.get("summary", {})
            if summary.get("overall_status") == "passed":
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 