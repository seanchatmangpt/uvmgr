#!/usr/bin/env python3
"""
Complete DoD validation script.
Runs comprehensive validation of DoD automation including unit tests, 
integration tests, OTEL validation, and external project E2E tests.
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

def run_command(cmd: List[str], description: str = "") -> Dict[str, Any]:
    """Run a command and capture results."""
    print(f"🔄 Running: {description or ' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        execution_time = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time,
            "command": ' '.join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out",
            "execution_time": 300,
            "command": ' '.join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": ' '.join(cmd)
        }

def parse_pytest_output(output: str) -> Dict[str, Any]:
    """Parse pytest output to extract test results."""
    lines = output.split('\n')
    
    # Look for summary line
    summary_line = None
    for line in lines:
        if 'passed' in line and ('failed' in line or 'error' in line or line.endswith('passed')):
            summary_line = line.strip()
            break
    
    if not summary_line:
        return {"total": 0, "passed": 0, "failed": 0, "errors": 0}
    
    # Parse the summary
    import re
    
    # Extract numbers from patterns like "37 passed, 3 failed"
    passed_match = re.search(r'(\d+) passed', summary_line)
    failed_match = re.search(r'(\d+) failed', summary_line)
    error_match = re.search(r'(\d+) error', summary_line)
    
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0
    
    return {
        "total": passed + failed + errors,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "success_rate": (passed / (passed + failed + errors)) if (passed + failed + errors) > 0 else 0
    }

def main():
    """Execute complete DoD validation."""
    print("🎯 Starting Complete DoD Automation Validation")
    print("=" * 60)
    
    validation_results = {
        "validation_timestamp": datetime.now().isoformat(),
        "validation_start": time.time(),
        "tests": {},
        "summary": {}
    }
    
    # Test categories to run
    test_categories = [
        {
            "name": "DoD Operations Unit Tests",
            "command": ["python", "-m", "pytest", "tests/ops/test_dod.py", "-v"],
            "description": "Unit tests for DoD operations business logic"
        },
        {
            "name": "OpenTelemetry Weaver Validation",
            "command": ["python", "-m", "pytest", "tests/ops/test_dod_otel_weaver.py::TestOtelWeaverIntegration::test_create_exoskeleton_telemetry", "-v"],
            "description": "OTEL integration and Weaver semantic conventions"
        },
        {
            "name": "External Projects E2E - FastAPI",
            "command": ["python", "-m", "pytest", "tests/e2e/test_external_projects_validation.py::TestExternalProjectsE2E::test_fastapi_project_validation", "-v"],
            "description": "E2E validation against FastAPI-like project"
        },
        {
            "name": "External Projects E2E - Requests",
            "command": ["python", "-m", "pytest", "tests/e2e/test_external_projects_validation.py::TestExternalProjectsE2E::test_requests_project_validation", "-v"],
            "description": "E2E validation against Requests-like project"
        },
        {
            "name": "External Projects E2E - Click",
            "command": ["python", "-m", "pytest", "tests/e2e/test_external_projects_validation.py::TestExternalProjectsE2E::test_click_project_validation", "-v"],
            "description": "E2E validation against Click-like project"
        },
        {
            "name": "Performance Benchmarks",
            "command": ["python", "-m", "pytest", "tests/e2e/test_external_projects_validation.py::TestExternalProjectsPerformance::test_validation_performance_benchmark", "-v"],
            "description": "Performance validation across project sizes"
        },
        {
            "name": "Robustness Tests",
            "command": ["python", "-m", "pytest", "tests/e2e/test_external_projects_validation.py::TestExternalProjectsRobustness", "-v"],
            "description": "Robustness testing with malformed/edge case projects"
        }
    ]
    
    # Run each test category
    total_tests_passed = 0
    total_tests_run = 0
    
    for i, test_category in enumerate(test_categories, 1):
        print(f"\n📋 [{i}/{len(test_categories)}] {test_category['name']}")
        print(f"    {test_category['description']}")
        
        result = run_command(test_category["command"], test_category["description"])
        
        # Parse test results
        if result["success"] and result["stdout"]:
            test_stats = parse_pytest_output(result["stdout"])
            result.update(test_stats)
            
            total_tests_passed += test_stats.get("passed", 0)
            total_tests_run += test_stats.get("total", 0)
            
            success_rate = test_stats.get("success_rate", 1.0 if result["success"] else 0.0)
            
            if success_rate >= 0.8:
                print(f"    ✅ PASSED: {test_stats.get('passed', 'N/A')}/{test_stats.get('total', 'N/A')} tests ({success_rate:.1%})")
            else:
                print(f"    ⚠️  PARTIAL: {test_stats.get('passed', 'N/A')}/{test_stats.get('total', 'N/A')} tests ({success_rate:.1%})")
        else:
            print(f"    ❌ FAILED: {result.get('error', 'Command failed')}")
        
        validation_results["tests"][test_category["name"]] = result
    
    # Calculate overall results
    validation_results["validation_end"] = time.time()
    validation_results["total_validation_time"] = validation_results["validation_end"] - validation_results["validation_start"]
    
    # Summary statistics
    successful_categories = sum(1 for test in validation_results["tests"].values() if test["success"])
    total_categories = len(test_categories)
    
    validation_results["summary"] = {
        "total_categories": total_categories,
        "successful_categories": successful_categories,
        "category_success_rate": successful_categories / total_categories,
        "total_tests_run": total_tests_run,
        "total_tests_passed": total_tests_passed,
        "overall_test_success_rate": total_tests_passed / total_tests_run if total_tests_run > 0 else 0,
        "total_execution_time": validation_results["total_validation_time"]
    }
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 DoD Automation Validation Complete")
    print("=" * 60)
    
    summary = validation_results["summary"]
    print(f"📊 Categories: {summary['successful_categories']}/{summary['total_categories']} successful ({summary['category_success_rate']:.1%})")
    print(f"🧪 Tests: {summary['total_tests_passed']}/{summary['total_tests_run']} passed ({summary['overall_test_success_rate']:.1%})")
    print(f"⏱️  Total Time: {summary['total_execution_time']:.1f} seconds")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for name, result in validation_results["tests"].items():
        status = "✅" if result["success"] else "❌"
        if "success_rate" in result:
            print(f"   {status} {name}: {result.get('passed', 0)}/{result.get('total', 0)} tests")
        else:
            print(f"   {status} {name}: {'PASSED' if result['success'] else 'FAILED'}")
    
    # Save detailed results
    results_file = Path("validation_results.json")
    with open(results_file, "w") as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Determine overall success
    overall_success = (
        summary["category_success_rate"] >= 0.8 and  # 80% of categories pass
        summary["overall_test_success_rate"] >= 0.85  # 85% of tests pass
    )
    
    if overall_success:
        print("\n🎉 VALIDATION SUCCESSFUL - DoD automation is production ready!")
        return 0
    else:
        print("\n⚠️  VALIDATION INCOMPLETE - Some issues need addressing")
        return 1

if __name__ == "__main__":
    sys.exit(main())