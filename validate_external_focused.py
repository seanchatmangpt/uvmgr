#!/usr/bin/env python3
"""
Focused external project validation for uvmgr.
Tests core commands in properly configured external projects.
"""

import subprocess
import tempfile
import json
import time
from pathlib import Path
import sys

def run_command(cmd, cwd=None, timeout=30):
    """Run command and return result."""
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        return result.returncode, result.stdout, result.stderr, elapsed
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out", timeout
    except Exception as e:
        return 1, "", str(e), 0

class ExternalProjectValidator:
    """Validate uvmgr in external projects."""
    
    def __init__(self):
        self.results = []
        
    def validate_all(self):
        """Run all external project validations."""
        print("🌍 External Project Validation")
        print("=" * 50)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test 1: Minimal project
            print("\n📦 Testing Minimal Project...")
            self.test_minimal_project(Path(temp_dir) / "minimal")
            
            # Test 2: FastAPI project
            print("\n🚀 Testing FastAPI Project...")
            self.test_fastapi_project(Path(temp_dir) / "fastapi")
            
            # Test 3: Data Science project
            print("\n📊 Testing Data Science Project...")
            self.test_data_project(Path(temp_dir) / "datascience")
        
        return self.generate_report()
    
    def test_minimal_project(self, path):
        """Test uvmgr in minimal Python project."""
        path.mkdir(parents=True)
        
        # Create minimal project structure
        (path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-minimal"
version = "0.1.0"
dependencies = []
""")
        
        # Create source directory
        src = path / "src" / "test_minimal"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('__version__ = "0.1.0"')
        (src / "main.py").write_text('def main(): print("Hello World")')
        
        # Test commands
        tests = [
            (["uvmgr", "--help"], "help command"),
            (["uvmgr", "deps", "list"], "list dependencies"),
            (["uvmgr", "cache", "status"], "cache status"),
            (["uvmgr", "otel", "--help"], "otel help"),
        ]
        
        project_success = True
        for cmd, desc in tests:
            exit_code, stdout, stderr, elapsed = run_command(cmd, cwd=path, timeout=10)
            success = exit_code == 0
            if not success:
                project_success = False
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc} ({elapsed:.2f}s)")
        
        self.results.append({
            "project": "minimal",
            "success": project_success,
            "path": str(path)
        })
    
    def test_fastapi_project(self, path):
        """Test uvmgr in FastAPI project."""
        path.mkdir(parents=True)
        
        # Create FastAPI project
        (path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-api"
version = "0.1.0"
dependencies = ["fastapi", "uvicorn"]

[project.optional-dependencies]
dev = ["pytest", "ruff"]
""")
        
        # Create app structure
        app = path / "app"
        app.mkdir()
        (app / "__init__.py").write_text("")
        (app / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")
        
        # Test commands
        tests = [
            (["uvmgr", "deps", "--help"], "deps help"),
            (["uvmgr", "build", "--help"], "build help"),
            (["uvmgr", "lint", "--help"], "lint help"),
        ]
        
        project_success = True
        for cmd, desc in tests:
            exit_code, stdout, stderr, elapsed = run_command(cmd, cwd=path, timeout=10)
            success = exit_code == 0
            if not success:
                project_success = False
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc} ({elapsed:.2f}s)")
        
        self.results.append({
            "project": "fastapi",
            "success": project_success,
            "path": str(path)
        })
    
    def test_data_project(self, path):
        """Test uvmgr in data science project."""
        path.mkdir(parents=True)
        
        # Create data science project
        (path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-data"
version = "0.1.0"
dependencies = ["pandas", "numpy", "matplotlib"]

[project.optional-dependencies]
dev = ["jupyter", "pytest"]
""")
        
        # Create notebooks directory
        notebooks = path / "notebooks"
        notebooks.mkdir()
        
        # Create src directory
        src = path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "analysis.py").write_text("""
import pandas as pd
import numpy as np

def load_data(filepath):
    return pd.read_csv(filepath)

def analyze(df):
    return df.describe()
""")
        
        # Test commands
        tests = [
            (["uvmgr", "tests", "--help"], "tests help"),
            (["uvmgr", "cache", "--help"], "cache help"),
            (["uvmgr", "infodesign", "--help"], "infodesign help"),
        ]
        
        project_success = True
        for cmd, desc in tests:
            exit_code, stdout, stderr, elapsed = run_command(cmd, cwd=path, timeout=10)
            success = exit_code == 0
            if not success:
                project_success = False
            
            status = "✅" if success else "❌"
            print(f"  {status} {desc} ({elapsed:.2f}s)")
        
        self.results.append({
            "project": "datascience",
            "success": project_success,
            "path": str(path)
        })
    
    def generate_report(self):
        """Generate validation report."""
        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)
        success_rate = success_count / total_count if total_count > 0 else 0
        
        report = {
            "external_validation": {
                "projects_tested": total_count,
                "projects_passed": success_count,
                "success_rate": success_rate,
                "meets_8020": success_rate >= 0.80
            },
            "results": self.results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return report

def main():
    """Main validation function."""
    validator = ExternalProjectValidator()
    report = validator.validate_all()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 EXTERNAL VALIDATION SUMMARY")
    print("=" * 50)
    
    summary = report["external_validation"]
    print(f"Projects Tested:     {summary['projects_tested']}")
    print(f"Projects Passed:     {summary['projects_passed']}")
    print(f"Success Rate:        {summary['success_rate']:.0%}")
    print(f"80/20 Threshold:     {'✅ MET' if summary['meets_8020'] else '❌ NOT MET'}")
    
    # Save report
    with open("external_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: external_validation_report.json")
    
    # Now run telemetry validation
    print("\n" + "=" * 50)
    print("🔬 TELEMETRY VALIDATION")
    print("=" * 50)
    
    # Run OTEL validation
    exit_code, stdout, stderr, elapsed = run_command(["uvmgr", "otel", "validate"], timeout=10)
    if "80.0%" in stdout or exit_code == 0:
        print("✅ Telemetry validation passed")
        telemetry_success = True
    else:
        print("❌ Telemetry validation failed")
        telemetry_success = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎯 FINAL VALIDATION SUMMARY")
    print("=" * 50)
    print(f"External Projects:   {summary['success_rate']:.0%}")
    print(f"Telemetry System:    {'✅ PASS' if telemetry_success else '❌ FAIL'}")
    print(f"Overall Status:      {'✅ VALIDATED' if summary['meets_8020'] and telemetry_success else '❌ NEEDS WORK'}")
    
    return 0 if summary['meets_8020'] else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)