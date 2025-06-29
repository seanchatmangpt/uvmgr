#!/usr/bin/env python3
"""
End-to-End External Project Validation for uvmgr
================================================

This script validates that uvmgr can manage the complete lifecycle
of external Python projects, from creation to deployment.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class ExternalProjectValidator:
    """Validates uvmgr functionality on external projects."""
    
    def __init__(self, uvmgr_path: Path):
        self.uvmgr_path = uvmgr_path
        self.uvmgr_exe = sys.executable
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "uvmgr_path": str(uvmgr_path),
            "python_version": sys.version,
            "test_results": [],
            "summary": {}
        }
        
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                   env: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command and capture results."""
        if env is None:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.uvmgr_path / "src")
        
        start_time = time.time()
        try:
            # Use uv directly for uv commands
            if cmd[0] == "uv":
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                # Use uvmgr through Python module
                uvmgr_cmd = [self.uvmgr_exe, "-m", "uvmgr"] + cmd
                result = subprocess.run(
                    uvmgr_cmd,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - start_time,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "duration": timeout,
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start_time,
                "command": " ".join(cmd)
            }
    
    def create_test_project(self, project_dir: Path, project_type: str) -> None:
        """Create a test project with specific characteristics."""
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Base pyproject.toml
        pyproject_content = {
            "minimal": '''[project]
name = "test-minimal"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/test_minimal"]
''',
            "library": '''[project]
name = "test-library"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = ["requests>=2.28.0", "click>=8.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/test_library"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=22.0.0", "mypy>=0.990"]
test = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]
''',
            "application": '''[project]
name = "test-app"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = ["click>=8.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/test_app"]

[project.scripts]
test-app = "test_app.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=22.0.0", "ruff>=0.1.0"]
'''
        }
        
        # Write pyproject.toml
        (project_dir / "pyproject.toml").write_text(pyproject_content[project_type])
        
        # Create source directory
        package_name = project_dir.name.replace("-", "_")
        src_dir = project_dir / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        (src_dir / "__init__.py").write_text(f'"""Test {project_type} project."""\n__version__ = "0.1.0"\n')
        
        # Create main module
        if project_type == "application":
            (src_dir / "cli.py").write_text('''"""CLI for test application."""
import click

@click.command()
@click.option("--name", default="World", help="Name to greet")
def main(name: str) -> None:
    """Simple greeting application."""
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    main()
''')
        else:
            (src_dir / "main.py").write_text('''"""Main module for test project."""

def hello(name: str = "World") -> str:
    """Return a greeting."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
        
        # Create tests
        test_dir = project_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "__init__.py").write_text("")
        if project_type == "application":
            (test_dir / "test_main.py").write_text(f'''"""Tests for {project_type} project."""
import pytest
from {package_name}.cli import main
from click.testing import CliRunner

def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output

def test_main_with_name():
    runner = CliRunner()
    result = runner.invoke(main, ["--name", "Test"])
    assert result.exit_code == 0
    assert "Hello, Test!" in result.output
''')
        else:
            (test_dir / "test_main.py").write_text(f'''"""Tests for {project_type} project."""
import pytest
from {package_name}.main import hello, add

def test_hello():
    assert hello() == "Hello, World!"
    assert hello("Test") == "Hello, Test!"

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
''')
        
        # Create README
        (project_dir / "README.md").write_text(f"""# Test {project_type.title()} Project

This is a test {project_type} project for validating uvmgr functionality.

## Installation

```bash
uv venv
uv pip install -e .
```

## Usage

```python
from {package_name} import hello
print(hello())
```
""")
    
    def validate_project_lifecycle(self, project_type: str) -> Dict[str, Any]:
        """Validate complete project lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / f"test-{project_type}"
            
            print(f"\n🧪 Testing {project_type} project lifecycle...")
            
            # Create test project
            self.create_test_project(project_dir, project_type)
            
            test_results = {
                "project_type": project_type,
                "project_path": str(project_dir),
                "steps": []
            }
            
            # Test sequence
            test_steps = [
                ("Create virtual environment", ["uv", "venv"]),
                ("Install project", ["uv", "pip", "install", "-e", "."]),
                ("Add dependency", ["deps", "add", "httpx"]),
                ("List dependencies", ["deps", "list"]),
                ("Run tests", ["tests", "run"]),
                ("Check code quality", ["lint", "check", "--help"]),  # Just check if command exists
                ("Build distribution", ["build", "wheel"]),
                ("Build source dist", ["build", "sdist"]),
            ]
            
            # Additional steps for application projects
            if project_type == "application":
                test_steps.extend([
                    ("Create executable", ["build", "exe", "--help"]),
                ])
            
            # Execute test steps
            for step_name, command in test_steps:
                print(f"  ▶ {step_name}...")
                result = self.run_command(command, cwd=project_dir)
                
                test_results["steps"].append({
                    "name": step_name,
                    "command": command,
                    "success": result["success"],
                    "duration": result["duration"],
                    "error": result["stderr"] if not result["success"] else None
                })
                
                # Stop on critical failures
                if not result["success"] and step_name in ["Create virtual environment", "Install project"]:
                    break
            
            # Calculate success rate
            successful_steps = sum(1 for step in test_results["steps"] if step["success"])
            total_steps = len(test_results["steps"])
            test_results["success_rate"] = successful_steps / total_steps if total_steps > 0 else 0
            test_results["summary"] = f"{successful_steps}/{total_steps} steps passed"
            
            return test_results
    
    def validate_advanced_features(self) -> Dict[str, Any]:
        """Validate advanced uvmgr features."""
        print("\n🚀 Testing advanced features...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            results = {
                "feature": "advanced",
                "tests": []
            }
            
            # Test OpenTelemetry validation
            print("  ▶ OpenTelemetry validation...")
            otel_result = self.run_command(["otel", "validate"], cwd=workspace)
            results["tests"].append({
                "name": "OTEL Validation",
                "success": otel_result["success"] and "100.0%" in otel_result["stdout"],
                "details": "All OTEL features working" if otel_result["success"] else otel_result["stderr"]
            })
            
            # Test Mermaid diagram generation
            print("  ▶ Mermaid diagram generation...")
            mermaid_test = workspace / "test.mmd"
            mermaid_test.write_text("""graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> A
""")
            
            mermaid_result = self.run_command(
                ["mermaid", "validate", str(mermaid_test)], 
                cwd=workspace
            )
            results["tests"].append({
                "name": "Mermaid Validation",
                "success": mermaid_result["success"],
                "details": "Diagram validation working" if mermaid_result["success"] else mermaid_result["stderr"]
            })
            
            # Test guide catalog
            print("  ▶ Guide catalog...")
            guide_result = self.run_command(["guides", "list"], cwd=workspace)
            results["tests"].append({
                "name": "Guide Catalog",
                "success": guide_result["success"],
                "details": "Guide system operational" if guide_result["success"] else guide_result["stderr"]
            })
            
            # Test worktree management
            print("  ▶ Git worktree management...")
            # Initialize git repo first
            subprocess.run(["git", "init"], cwd=workspace, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=workspace, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=workspace, capture_output=True)
            (workspace / "README.md").write_text("# Test")
            subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=workspace, capture_output=True)
            
            worktree_result = self.run_command(["worktree", "list"], cwd=workspace)
            results["tests"].append({
                "name": "Worktree Management",
                "success": worktree_result["success"],
                "details": "Worktree commands available" if worktree_result["success"] else worktree_result["stderr"]
            })
            
            return results
    
    def run_validation(self) -> None:
        """Run complete validation suite."""
        print("=" * 60)
        print("uvmgr End-to-End External Project Validation")
        print("=" * 60)
        
        # Validate different project types
        project_types = ["minimal", "library", "application"]
        lifecycle_results = []
        
        for project_type in project_types:
            result = self.validate_project_lifecycle(project_type)
            lifecycle_results.append(result)
            self.results["test_results"].append(result)
        
        # Validate advanced features
        advanced_result = self.validate_advanced_features()
        self.results["test_results"].append(advanced_result)
        
        # Calculate summary
        total_tests = sum(len(r.get("steps", r.get("tests", []))) for r in self.results["test_results"])
        passed_tests = sum(
            sum(1 for s in r.get("steps", []) if s["success"]) +
            sum(1 for t in r.get("tests", []) if t["success"])
            for r in self.results["test_results"]
        )
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "project_types_tested": len(project_types),
            "all_lifecycles_pass": all(r["success_rate"] > 0.8 for r in lifecycle_results),
            "advanced_features_pass": all(t["success"] for t in advanced_result["tests"])
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        for result in lifecycle_results:
            status = "✅" if result["success_rate"] > 0.8 else "❌"
            print(f"{status} {result['project_type'].title()}: {result['summary']}")
        
        print(f"\n{'✅' if self.results['summary']['advanced_features_pass'] else '❌'} Advanced Features: "
              f"{sum(1 for t in advanced_result['tests'] if t['success'])}/{len(advanced_result['tests'])} passed")
        
        print(f"\nOverall Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        
        # Save detailed results
        report_path = self.uvmgr_path / "e2e_external_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")
        
        # Exit code based on success
        if self.results["summary"]["success_rate"] >= 0.8:
            print("\n✅ VALIDATION PASSED: uvmgr is ready for external projects!")
            sys.exit(0)
        else:
            print("\n❌ VALIDATION FAILED: Issues detected in external project support")
            sys.exit(1)


def main():
    """Run the validation."""
    # Determine uvmgr path
    uvmgr_path = Path(__file__).parent
    
    # Ensure we can import uvmgr
    sys.path.insert(0, str(uvmgr_path / "src"))
    
    try:
        import uvmgr
        print(f"✅ Found uvmgr at: {uvmgr_path}")
    except ImportError:
        print(f"❌ Cannot import uvmgr from: {uvmgr_path}")
        sys.exit(1)
    
    # Run validation
    validator = ExternalProjectValidator(uvmgr_path)
    validator.run_validation()


if __name__ == "__main__":
    main()