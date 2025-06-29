#!/usr/bin/env python3
"""
End-to-End External Project Validation for uvmgr
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Colors for terminal output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


def run_command(cmd: List[str], cwd: Path = None) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def validate_project(name: str, path: Path) -> Dict:
    """Validate uvmgr commands on a project."""
    print(f"\n{YELLOW}🔍 Validating {name}{NC}")
    print(f"Path: {path}")
    
    if not path.exists():
        print(f"{RED}✗ Project directory not found{NC}")
        return {"status": "NOT_FOUND", "tests": {}}
    
    results = {
        "project": name,
        "path": str(path),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tests": {}
    }
    
    # Test commands
    tests = [
        ("deps", ["uvmgr", "deps", "list"]),
        ("lint", ["uvmgr", "lint", "check"]),
        ("cache", ["uvmgr", "cache", "info"]),
        ("otel", ["uvmgr", "otel", "validate"]),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, cmd in tests:
        print(f"  📦 Testing {test_name}... ", end="", flush=True)
        success, output = run_command(cmd, cwd=path)
        
        if success:
            print(f"{GREEN}✓{NC}")
            passed += 1
            results["tests"][test_name] = {
                "status": "passed",
                "command": " ".join(cmd)
            }
        else:
            print(f"{RED}✗{NC}")
            results["tests"][test_name] = {
                "status": "failed",
                "command": " ".join(cmd),
                "error": output[:200]  # First 200 chars of error
            }
    
    # Check for build configuration
    print(f"  🏗️  Checking build capability... ", end="", flush=True)
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
        print(f"{GREEN}✓ (build ready){NC}")
        results["tests"]["build"] = {"status": "ready", "note": "build config found"}
    else:
        print(f"{YELLOW}⚠ (no build config){NC}")
        results["tests"]["build"] = {"status": "skipped", "note": "no build config"}
    
    results["summary"] = {
        "total_tests": total,
        "passed_tests": passed,
        "success_rate": round(passed / total * 100, 1) if total > 0 else 0
    }
    
    if passed == total:
        print(f"  {GREEN}✅ All tests passed! ({passed}/{total}){NC}")
        results["status"] = "PASSED"
    else:
        print(f"  {YELLOW}⚠️  Partial success: {passed}/{total} tests passed{NC}")
        results["status"] = "PARTIAL"
    
    return results


def main():
    """Main validation function."""
    print("🚀 uvmgr End-to-End External Project Validation")
    print("==============================================")
    print(f"Started: {datetime.now()}")
    
    # Get uvmgr version
    success, version_output = run_command(["uvmgr", "--version"])
    uvmgr_version = version_output.strip() if success else "unknown"
    print(f"uvmgr version: {uvmgr_version}")
    
    # Test on uvmgr itself first
    uvmgr_path = Path.cwd()
    print(f"\n📍 Testing on uvmgr project itself")
    uvmgr_results = validate_project("uvmgr", uvmgr_path)
    
    # Test on Flask project in src/flask
    flask_path = uvmgr_path / "src" / "flask"
    flask_results = {}
    if flask_path.exists():
        flask_results = validate_project("flask", flask_path)
    else:
        print(f"\n{YELLOW}⚠️  Flask project not found at {flask_path}{NC}")
        flask_results = {"status": "NOT_FOUND", "project": "flask"}
    
    # Generate summary report
    all_results = {
        "validation_type": "end_to_end_external",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uvmgr_version": uvmgr_version,
        "projects": [uvmgr_results, flask_results] if flask_results else [uvmgr_results],
        "summary": {
            "total_projects": 2 if flask_results else 1,
            "passed_projects": sum(1 for r in [uvmgr_results, flask_results] if r.get("status") == "PASSED"),
            "partial_projects": sum(1 for r in [uvmgr_results, flask_results] if r.get("status") == "PARTIAL"),
            "failed_projects": sum(1 for r in [uvmgr_results, flask_results] if r.get("status") not in ["PASSED", "PARTIAL"])
        }
    }
    
    # Save results
    results_file = Path("e2e_external_validation_results.json")
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    # Generate markdown report
    report_file = Path("e2e_external_validation_report.md")
    with open(report_file, "w") as f:
        f.write("# uvmgr End-to-End External Project Validation Report\n\n")
        f.write(f"**Generated:** {datetime.now()}\n")
        f.write(f"**uvmgr Version:** {uvmgr_version}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Projects Tested:** {all_results['summary']['total_projects']}\n")
        f.write(f"- **Passed:** {all_results['summary']['passed_projects']}\n")
        f.write(f"- **Partial:** {all_results['summary']['partial_projects']}\n")
        f.write(f"- **Failed:** {all_results['summary']['failed_projects']}\n\n")
        f.write("## Project Results\n\n")
        
        for project in all_results["projects"]:
            if project.get("status") == "NOT_FOUND":
                f.write(f"### {project.get('project', 'Unknown')}\n")
                f.write("- **Status:** ❌ NOT FOUND\n\n")
                continue
                
            f.write(f"### {project['project']}\n")
            f.write(f"- **Status:** ")
            if project["status"] == "PASSED":
                f.write("✅ PASSED\n")
            elif project["status"] == "PARTIAL":
                f.write("⚠️ PARTIAL\n")
            else:
                f.write("❌ FAILED\n")
            
            if "summary" in project:
                f.write(f"- **Success Rate:** {project['summary']['success_rate']}%\n")
                f.write(f"- **Tests:** {project['summary']['passed_tests']}/{project['summary']['total_tests']}\n")
            
            f.write("\n**Test Results:**\n")
            for test_name, test_result in project.get("tests", {}).items():
                status_icon = "✅" if test_result["status"] == "passed" else "❌"
                f.write(f"- {test_name}: {status_icon} {test_result['status']}\n")
            f.write("\n")
    
    # Display summary
    print(f"\n{GREEN}✨ Validation Complete!{NC}")
    print("========================")
    print(f"Projects Tested: {all_results['summary']['total_projects']}")
    print(f"Passed: {GREEN}{all_results['summary']['passed_projects']}{NC}")
    print(f"Partial: {YELLOW}{all_results['summary']['partial_projects']}{NC}")
    print(f"Failed: {RED}{all_results['summary']['failed_projects']}{NC}")
    print(f"\n📄 Full report: {report_file}")
    print(f"📊 Detailed results: {results_file}")
    
    # Exit with appropriate code
    if all_results['summary']['failed_projects'] > 0:
        sys.exit(1)
    elif all_results['summary']['partial_projects'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()