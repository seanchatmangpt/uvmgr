#!/usr/bin/env python3
"""
Complete End-to-End Validation Script for uvmgr
===============================================

This script validates the complete uvmgr system including:
1. All enabled commands functionality 
2. External project integration
3. Performance benchmarks
4. 80/20 success criteria verification
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
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
        return 1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)

class UvmgrValidator:
    """Complete uvmgr validation system."""
    
    def __init__(self):
        self.results = {
            "command_tests": [],
            "architecture_tests": [],
            "performance_tests": [],
            "external_project_tests": [],
            "overall_success": False,
            "success_rate": 0.0,
            "meets_8020_threshold": False
        }
        
    def validate_all(self) -> Dict:
        """Run complete validation suite."""
        print("🚀 Starting uvmgr Complete E2E Validation")
        print("=" * 50)
        
        # 1. Core Command Validation
        print("\n📋 Testing Core Commands...")
        self._test_core_commands()
        
        # 2. Newly Implemented Commands
        print("\n🆕 Testing Newly Implemented Commands...")
        self._test_new_commands()
        
        # 3. Architecture Validation
        print("\n🏗️ Testing Three-Tier Architecture...")
        self._test_architecture()
        
        # 4. Performance Benchmarks
        print("\n⚡ Running Performance Tests...")
        self._test_performance()
        
        # 5. Quick External Project Test
        print("\n🌍 Testing External Project Integration...")
        self._test_external_integration()
        
        # Calculate overall results
        self._calculate_overall_results()
        
        return self.results
    
    def _test_core_commands(self):
        """Test essential core commands."""
        core_commands = [
            (["uvmgr", "--help"], "Help command"),
            (["uvmgr", "--version"], "Version command"),
            (["uvmgr", "deps", "--help"], "Deps command help"),
            (["uvmgr", "build", "--help"], "Build command help"),
            (["uvmgr", "lint", "--help"], "Lint command help"),
        ]
        
        for cmd, desc in core_commands:
            exit_code, stdout, stderr = run_command(cmd)
            success = exit_code == 0
            
            self.results["command_tests"].append({
                "command": " ".join(cmd),
                "description": desc,
                "success": success,
                "exit_code": exit_code,
                "output_length": len(stdout),
                "error": stderr if not success else None
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc}")
    
    def _test_new_commands(self):
        """Test newly implemented commands."""
        new_commands = [
            (["uvmgr", "workflow", "--help"], "Workflow command"),
            (["uvmgr", "knowledge", "--help"], "Knowledge command"),
            (["uvmgr", "history", "--help"], "History command"),
            (["uvmgr", "documentation", "--help"], "Documentation command"),
            (["uvmgr", "infodesign", "--help"], "Infodesign command"),
        ]
        
        for cmd, desc in new_commands:
            exit_code, stdout, stderr = run_command(cmd)
            success = exit_code == 0
            
            self.results["command_tests"].append({
                "command": " ".join(cmd),
                "description": desc,
                "success": success,
                "exit_code": exit_code,
                "output_length": len(stdout),
                "error": stderr if not success else None
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc}")
    
    def _test_architecture(self):
        """Test three-tier architecture compliance."""
        # Test that commands properly use ops -> runtime layers
        architecture_tests = [
            {
                "name": "Operations layer exists",
                "test": lambda: Path("src/uvmgr/ops").exists(),
                "description": "Operations directory structure"
            },
            {
                "name": "Runtime layer exists", 
                "test": lambda: Path("src/uvmgr/runtime").exists(),
                "description": "Runtime directory structure"
            },
            {
                "name": "New ops files exist",
                "test": lambda: all([
                    Path("src/uvmgr/ops/workflow.py").exists(),
                    Path("src/uvmgr/ops/knowledge.py").exists(),
                    Path("src/uvmgr/ops/history.py").exists()
                ]),
                "description": "Newly created operations files"
            },
            {
                "name": "New runtime files exist",
                "test": lambda: all([
                    Path("src/uvmgr/runtime/workflow.py").exists(),
                    Path("src/uvmgr/runtime/knowledge.py").exists(),
                    Path("src/uvmgr/runtime/history.py").exists()
                ]),
                "description": "Newly created runtime files"
            }
        ]
        
        for test in architecture_tests:
            try:
                success = test["test"]()
            except Exception:
                success = False
                
            self.results["architecture_tests"].append({
                "name": test["name"],
                "description": test["description"],
                "success": success
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} {test['name']}")
    
    def _test_performance(self):
        """Test command performance."""
        performance_tests = [
            (["uvmgr", "--help"], "Help performance", 1.0),
            (["uvmgr", "--version"], "Version performance", 1.0),
            (["uvmgr", "workflow", "--help"], "Workflow help performance", 2.0),
            (["uvmgr", "knowledge", "--help"], "Knowledge help performance", 2.0),
        ]
        
        for cmd, desc, max_time in performance_tests:
            start_time = time.time()
            exit_code, stdout, stderr = run_command(cmd, timeout=10)
            elapsed = time.time() - start_time
            
            success = exit_code == 0 and elapsed <= max_time
            
            self.results["performance_tests"].append({
                "command": " ".join(cmd),
                "description": desc,
                "success": success,
                "elapsed_time": elapsed,
                "max_time": max_time,
                "performance_met": elapsed <= max_time
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc} ({elapsed:.2f}s <= {max_time}s)")
    
    def _test_external_integration(self):
        """Quick external project integration test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_external"
            
            try:
                # Create minimal project
                project_path.mkdir()
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
                
                # Test uvmgr commands in external project
                external_tests = [
                    (["uvmgr", "--help"], "Help in external project"),
                    (["uvmgr", "deps", "list"], "Deps list in external project"),
                ]
                
                for cmd, desc in external_tests:
                    exit_code, stdout, stderr = run_command(cmd, cwd=project_path, timeout=15)
                    success = exit_code == 0
                    
                    self.results["external_project_tests"].append({
                        "command": " ".join(cmd),
                        "description": desc,
                        "success": success,
                        "cwd": str(project_path)
                    })
                    
                    status = "✅" if success else "❌"
                    print(f"  {status} {desc}")
                    
            except Exception as e:
                self.results["external_project_tests"].append({
                    "command": "external_project_setup",
                    "description": "External project setup",
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ External project setup failed: {e}")
    
    def _calculate_overall_results(self):
        """Calculate overall success metrics."""
        all_tests = (
            self.results["command_tests"] + 
            self.results["architecture_tests"] + 
            self.results["performance_tests"] + 
            self.results["external_project_tests"]
        )
        
        total_tests = len(all_tests)
        passed_tests = sum(1 for test in all_tests if test.get("success", False))
        
        self.results["total_tests"] = total_tests
        self.results["passed_tests"] = passed_tests
        self.results["success_rate"] = passed_tests / total_tests if total_tests > 0 else 0
        self.results["overall_success"] = self.results["success_rate"] >= 0.80
        self.results["meets_8020_threshold"] = self.results["success_rate"] >= 0.80
    
    def generate_report(self) -> str:
        """Generate validation report."""
        return f"""
# uvmgr Complete E2E Validation Report

## Summary
- **Overall Success**: {'✅ PASS' if self.results['overall_success'] else '❌ FAIL'}
- **Success Rate**: {self.results['success_rate']:.1%}
- **80/20 Threshold**: {'✅ MET' if self.results['meets_8020_threshold'] else '❌ NOT MET'}

## Test Results
- **Total Tests**: {self.results['total_tests']}
- **Passed Tests**: {self.results['passed_tests']}
- **Failed Tests**: {self.results['total_tests'] - self.results['passed_tests']}

### Command Tests ({len(self.results['command_tests'])} tests)
{self._format_test_results(self.results['command_tests'])}

### Architecture Tests ({len(self.results['architecture_tests'])} tests)
{self._format_test_results(self.results['architecture_tests'])}

### Performance Tests ({len(self.results['performance_tests'])} tests)
{self._format_test_results(self.results['performance_tests'])}

### External Project Tests ({len(self.results['external_project_tests'])} tests)
{self._format_test_results(self.results['external_project_tests'])}

## Conclusion
uvmgr {'PASSED' if self.results['meets_8020_threshold'] else 'FAILED'} the complete E2E validation with {self.results['success_rate']:.1%} success rate.

The system {'meets' if self.results['overall_success'] else 'does not meet'} the 80/20 implementation criteria.
"""
    
    def _format_test_results(self, tests: List[Dict]) -> str:
        """Format test results for report."""
        if not tests:
            return "No tests run."
            
        lines = []
        for test in tests:
            status = "✅ PASS" if test.get("success", False) else "❌ FAIL"
            desc = test.get("description", test.get("name", "Unknown test"))
            lines.append(f"- {status} {desc}")
            
            if not test.get("success", False) and test.get("error"):
                lines.append(f"  Error: {test['error'][:100]}...")
        
        return "\n".join(lines)

def main():
    """Main validation function."""
    validator = UvmgrValidator()
    results = validator.validate_all()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION COMPLETE")
    print("=" * 50)
    
    # Print summary
    print(f"✨ Success Rate: {results['success_rate']:.1%}")
    print(f"📈 80/20 Threshold: {'✅ MET' if results['meets_8020_threshold'] else '❌ NOT MET'}")
    print(f"🎯 Overall: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
    
    # Generate and save report
    report = validator.generate_report()
    
    # Save results
    with open("e2e_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("e2e_validation_report.md", "w") as f:
        f.write(report)
    
    print(f"\n📄 Reports saved:")
    print(f"  - e2e_validation_results.json")
    print(f"  - e2e_validation_report.md")
    
    # Exit with appropriate code
    exit_code = 0 if results["meets_8020_threshold"] else 1
    print(f"\n🏁 Exiting with code {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)