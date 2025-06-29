#!/usr/bin/env python3
"""Final validation report for uvmgr telemetry and external project support."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime


def run_command(cmd, cwd=None):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }


def validate_test_suite():
    """Run test suite to validate fixes."""
    print("🧪 Running test suite...")
    tests = [
        ("CLI Tests", "uv run pytest tests/test_cli.py -v"),
        ("OTEL Integration", "uv run pytest tests/test_otel_integration.py -v"),
        ("Dependency Management", "uv run pytest tests/test_deps.py -v"),
    ]
    
    results = []
    for name, cmd in tests:
        print(f"  Testing {name}...")
        result = run_command(cmd)
        results.append({
            "test": name,
            "success": result["success"],
            "details": result
        })
    
    return results


def validate_telemetry():
    """Validate telemetry functionality."""
    print("\n📊 Validating telemetry...")
    result = run_command("uv run python -m uvmgr otel validate")
    return {
        "success": result["success"] and "100.0%" in result["stdout"],
        "output": result["stdout"],
        "details": result
    }


def validate_external_project():
    """Validate external project support."""
    print("\n🏗️ Validating external project support...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test-project"
        
        # Create a minimal project
        project_dir.mkdir()
        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text("""[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")
        
        src_dir = project_dir / "src" / "test_project"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('"""Test project."""\n__version__ = "0.1.0"')
        (src_dir / "main.py").write_text("""def hello():\n    return "Hello, World!"\n""")
        
        # Test uvmgr commands
        tests = [
            ("Initialize venv", "uv venv"),
            ("Add dependency", "uv run python -m uvmgr deps add requests"),
            ("List dependencies", "uv run python -m uvmgr deps list"),
            ("Run tests", "uv run python -m uvmgr tests run --help"),
            ("Build project", "uv run python -m uvmgr build wheel"),
        ]
        
        results = []
        for name, cmd in tests:
            print(f"  Testing {name}...")
            result = run_command(cmd, cwd=project_dir)
            results.append({
                "operation": name,
                "success": result["success"],
                "details": result
            })
        
        return results


def generate_report(test_results, telemetry_result, external_results):
    """Generate final validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "all_tests_passed": all(r["success"] for r in test_results),
            "telemetry_validated": telemetry_result["success"],
            "external_project_support": all(r["success"] for r in external_results),
        },
        "test_suite": test_results,
        "telemetry_validation": telemetry_result,
        "external_project_validation": external_results
    }
    
    # Calculate overall success
    report["overall_success"] = all([
        report["summary"]["all_tests_passed"],
        report["summary"]["telemetry_validated"],
        report["summary"]["external_project_support"]
    ])
    
    return report


def main():
    """Run final validation."""
    print("🚀 uvmgr Final Validation Report")
    print("=" * 50)
    
    # Run validations
    test_results = validate_test_suite()
    telemetry_result = validate_telemetry()
    external_results = validate_external_project()
    
    # Generate report
    report = generate_report(test_results, telemetry_result, external_results)
    
    # Save report
    report_file = Path("final_validation_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n📋 Summary")
    print("=" * 50)
    print(f"✅ Test Suite: {'PASSED' if report['summary']['all_tests_passed'] else 'FAILED'}")
    print(f"✅ Telemetry: {'VALIDATED' if report['summary']['telemetry_validated'] else 'FAILED'}")
    print(f"✅ External Projects: {'WORKING' if report['summary']['external_project_support'] else 'FAILED'}")
    print(f"\n{'✅ Overall: ALL SYSTEMS OPERATIONAL' if report['overall_success'] else '❌ Overall: FAILURES DETECTED'}")
    print(f"\nReport saved to: {report_file}")
    
    return 0 if report["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())