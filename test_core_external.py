#!/usr/bin/env python3
"""
Focused external project testing for core working commands.
"""

import subprocess
import tempfile
import json
from pathlib import Path
import sys

def run_command(cmd, cwd=None, timeout=30):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def test_core_commands():
    """Test core working commands."""
    print("🧪 Testing Core Working Commands")
    print("=" * 40)
    
    core_commands = [
        (["uvmgr", "deps", "--help"], "deps help"),
        (["uvmgr", "build", "--help"], "build help"),
        (["uvmgr", "tests", "--help"], "tests help"),
        (["uvmgr", "lint", "--help"], "lint help"),
        (["uvmgr", "otel", "--help"], "otel help"),
        (["uvmgr", "infodesign", "--help"], "infodesign help"),
    ]
    
    results = []
    for cmd, desc in core_commands:
        exit_code, stdout, stderr = run_command(cmd)
        success = exit_code == 0
        results.append({
            "command": " ".join(cmd),
            "description": desc,
            "success": success,
            "exit_code": exit_code
        })
        
        status = "✅" if success else "❌"
        print(f"  {status} {desc}")
    
    return results

def test_external_project():
    """Test commands in external project."""
    print("\n🌍 Testing External Project Integration")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Create minimal project
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-external"
version = "0.1.0"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["pytest"]
""")
        
        src_dir = project_path / "src" / "test_external"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("def hello(): return 'Hello World'")
        
        # Test core commands in external project
        external_tests = [
            (["uvmgr", "deps", "list"], "deps list in external project"),
            (["uvmgr", "lint", "check", "--"], "lint check in external project"),
        ]
        
        results = []
        for cmd, desc in external_tests:
            exit_code, stdout, stderr = run_command(cmd, cwd=project_path, timeout=15)
            success = exit_code == 0
            results.append({
                "command": " ".join(cmd),
                "description": desc,
                "success": success,
                "working_directory": str(project_path)
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc}")
        
        return results

def main():
    """Main testing function."""
    print("🚀 uvmgr Core Commands E2E Testing")
    print("=" * 50)
    
    # Test core commands
    core_results = test_core_commands()
    
    # Test external project integration
    external_results = test_external_project()
    
    # Calculate results
    all_results = core_results + external_results
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get("success", False))
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"80/20 Threshold: {'✅ MET' if success_rate >= 0.80 else '❌ NOT MET'}")
    
    # Save results
    results = {
        "core_command_tests": core_results,
        "external_project_tests": external_results,
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "meets_8020_threshold": success_rate >= 0.80
        }
    }
    
    with open("core_external_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: core_external_test_results.json")
    
    # Exit with appropriate code
    return 0 if success_rate >= 0.80 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)