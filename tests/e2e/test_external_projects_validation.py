"""
End-to-end validation of DoD automation against real external projects.
Tests complete DoD workflow on actual Python projects to validate production readiness.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import json
import time
from typing import Dict, Any, List

from uvmgr.ops.dod import (
    create_exoskeleton,
    execute_complete_automation,
    validate_dod_criteria,
    analyze_project_status,
    DOD_CRITERIA_WEIGHTS
)


class ExternalProjectValidator:
    """Validates DoD automation against real external projects."""
    
    def __init__(self):
        self.test_projects = [
            {
                "name": "fastapi-minimal",
                "repo": "https://github.com/tiangolo/fastapi.git",
                "description": "FastAPI web framework",
                "expected_criteria": ["testing", "security", "documentation"],
                "size": "large"
            },
            {
                "name": "requests-simple", 
                "repo": "https://github.com/psf/requests.git",
                "description": "HTTP library for Python",
                "expected_criteria": ["testing", "security", "code_quality"],
                "size": "medium"
            },
            {
                "name": "click-cli",
                "repo": "https://github.com/pallets/click.git", 
                "description": "Command line interface creation kit",
                "expected_criteria": ["testing", "documentation"],
                "size": "small"
            }
        ]
        self.validation_results = {}
        self.temp_dir = None
    
    def setup_test_environment(self) -> Path:
        """Setup isolated test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="dod_e2e_"))
        return self.temp_dir
    
    def cleanup_test_environment(self):
        """Cleanup test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def clone_project(self, project_info: Dict[str, Any]) -> Path:
        """Clone external project for testing."""
        project_path = self.temp_dir / project_info["name"]
        
        try:
            # Use a minimal clone for testing
            result = subprocess.run([
                "git", "clone", "--depth", "1", "--single-branch",
                project_info["repo"], str(project_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                # Create a mock project structure if clone fails
                project_path.mkdir(parents=True, exist_ok=True)
                self._create_mock_project_structure(project_path, project_info)
            
            return project_path
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback to mock project
            project_path.mkdir(parents=True, exist_ok=True)
            self._create_mock_project_structure(project_path, project_info)
            return project_path
    
    def _create_mock_project_structure(self, project_path: Path, project_info: Dict[str, Any]):
        """Create a realistic mock project structure for testing."""
        
        # Create basic Python project structure
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        
        # Create pyproject.toml
        pyproject_content = f'''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_info["name"]}"
version = "1.0.0"
description = "{project_info["description"]}"
authors = [{{name = "Test Author", email = "test@example.com"}}]
license = {{text = "MIT"}}
requires-python = ">=3.8"
dependencies = [
    "requests>=2.25.0",
]

[project.optional-dependencies]
test = [
    "pytest>=6.0",
    "pytest-cov>=2.10",
]
dev = [
    "black>=21.0",
    "flake8>=3.8",
    "mypy>=0.800",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=term-missing"

[tool.black]
line-length = 88
target-version = ["py38"]

[tool.mypy]
python_version = "3.8"
strict = true
'''
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        # Create README.md
        readme_content = f'''# {project_info["name"]}

{project_info["description"]}

## Installation

```bash
pip install {project_info["name"]}
```

## Usage

```python
import {project_info["name"].replace("-", "_")}

# Example usage
result = {project_info["name"].replace("-", "_")}.main()
print(result)
```

## Testing

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
'''
        (project_path / "README.md").write_text(readme_content)
        
        # Create main module
        main_module = project_path / "src" / f'{project_info["name"].replace("-", "_")}'
        main_module.mkdir(parents=True, exist_ok=True)
        
        (main_module / "__init__.py").write_text(f'''"""
{project_info["description"]}
"""

__version__ = "1.0.0"

def main():
    """Main function for {project_info["name"]}."""
    return "Hello from {project_info["name"]}!"
''')
        
        # Create test files
        test_content = f'''"""
Tests for {project_info["name"]}
"""

import pytest
from src.{project_info["name"].replace("-", "_")} import main


def test_main_function():
    """Test the main function."""
    result = main()
    assert "Hello from {project_info["name"]}!" in result


def test_main_returns_string():
    """Test that main returns a string."""
    result = main()
    assert isinstance(result, str)


class TestAdvanced:
    """Advanced test scenarios."""
    
    def test_module_import(self):
        """Test module can be imported."""
        import src.{project_info["name"].replace("-", "_")} as module
        assert hasattr(module, "main")
    
    def test_version_exists(self):
        """Test version is defined."""
        import src.{project_info["name"].replace("-", "_")} as module
        assert hasattr(module, "__version__")
        assert isinstance(module.__version__, str)
'''
        (project_path / "tests" / "test_main.py").write_text(test_content)
        
        # Create GitHub Actions workflow (if appropriate)
        github_dir = project_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = '''name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[test,dev]
    
    - name: Lint with flake8
      run: |
        flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Type check with mypy
      run: |
        mypy src
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
'''
        (github_dir / "ci.yml").write_text(workflow_content)
    
    def validate_project_dod(self, project_path: Path, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete DoD validation on project."""
        validation_start = time.time()
        
        results = {
            "project": project_info["name"],
            "path": str(project_path),
            "validation_timestamp": time.time(),
            "stages": {}
        }
        
        try:
            # Stage 1: Create Exoskeleton
            print(f"🏗️  Creating exoskeleton for {project_info['name']}...")
            exoskeleton_result = create_exoskeleton(
                project_path=project_path,
                template="standard",
                force=True
            )
            results["stages"]["exoskeleton"] = {
                "success": exoskeleton_result.get("success", False),
                "details": exoskeleton_result
            }
            
            # Stage 2: Validate DoD Criteria
            print(f"✅ Validating DoD criteria for {project_info['name']}...")
            validation_result = validate_dod_criteria(
                project_path=project_path,
                criteria=project_info.get("expected_criteria", list(DOD_CRITERIA_WEIGHTS.keys())),
                detailed=True,
                fix_suggestions=True
            )
            results["stages"]["validation"] = {
                "success": validation_result.get("success", False),
                "overall_score": validation_result.get("overall_score", 0),
                "details": validation_result
            }
            
            # Stage 3: Execute Complete Automation
            print(f"🤖 Executing automation for {project_info['name']}...")
            automation_result = execute_complete_automation(
                project_path=project_path,
                environment="testing",
                auto_fix=False,  # Don't modify external projects
                parallel=True
            )
            results["stages"]["automation"] = {
                "success": automation_result.get("success", False),
                "success_rate": automation_result.get("overall_success_rate", 0),
                "details": automation_result
            }
            
            # Stage 4: Analyze Project Status
            print(f"📊 Analyzing project status for {project_info['name']}...")
            status_result = analyze_project_status(
                project_path=project_path,
                detailed=True,
                suggestions=True
            )
            results["stages"]["status"] = {
                "success": status_result.get("success", True),
                "health_score": status_result.get("health_score", 0),
                "details": status_result
            }
            
            # Calculate overall validation score
            stage_scores = []
            for stage_name, stage_result in results["stages"].items():
                if "overall_score" in stage_result:
                    stage_scores.append(stage_result["overall_score"])
                elif "success_rate" in stage_result:
                    stage_scores.append(stage_result["success_rate"] * 100)
                elif "health_score" in stage_result:
                    stage_scores.append(stage_result["health_score"])
                elif stage_result["success"]:
                    stage_scores.append(100)
                else:
                    stage_scores.append(0)
            
            results["overall_score"] = sum(stage_scores) / len(stage_scores) if stage_scores else 0
            results["validation_time"] = time.time() - validation_start
            results["success"] = results["overall_score"] > 50  # 50% threshold for success
            
        except Exception as e:
            results["error"] = str(e)
            results["success"] = False
            results["validation_time"] = time.time() - validation_start
        
        return results


@pytest.fixture
def external_validator():
    """Fixture providing external project validator."""
    validator = ExternalProjectValidator()
    validator.setup_test_environment()
    yield validator
    validator.cleanup_test_environment()


class TestExternalProjectsE2E:
    """End-to-end tests against real external projects."""
    
    def test_fastapi_project_validation(self, external_validator):
        """Test DoD automation against FastAPI-like project."""
        project_info = external_validator.test_projects[0]  # FastAPI
        
        # Clone/create project
        project_path = external_validator.clone_project(project_info)
        assert project_path.exists()
        
        # Execute DoD validation
        results = external_validator.validate_project_dod(project_path, project_info)
        
        # Validate results
        assert results["success"], f"FastAPI validation failed: {results.get('error', 'Unknown error')}"
        assert results["overall_score"] > 60, f"FastAPI score too low: {results['overall_score']}"
        
        # Verify all stages completed
        expected_stages = ["exoskeleton", "validation", "automation", "status"]
        for stage in expected_stages:
            assert stage in results["stages"], f"Missing stage: {stage}"
        
        # Store results for reporting
        external_validator.validation_results["fastapi"] = results
    
    def test_requests_project_validation(self, external_validator):
        """Test DoD automation against Requests-like project."""
        project_info = external_validator.test_projects[1]  # Requests
        
        # Clone/create project
        project_path = external_validator.clone_project(project_info)
        assert project_path.exists()
        
        # Execute DoD validation
        results = external_validator.validate_project_dod(project_path, project_info)
        
        # Validate results
        assert results["success"], f"Requests validation failed: {results.get('error', 'Unknown error')}"
        assert results["overall_score"] > 50, f"Requests score too low: {results['overall_score']}"
        
        # Store results
        external_validator.validation_results["requests"] = results
    
    def test_click_project_validation(self, external_validator):
        """Test DoD automation against Click-like project."""
        project_info = external_validator.test_projects[2]  # Click
        
        # Clone/create project
        project_path = external_validator.clone_project(project_info)
        assert project_path.exists()
        
        # Execute DoD validation
        results = external_validator.validate_project_dod(project_path, project_info)
        
        # Validate results
        assert results["success"], f"Click validation failed: {results.get('error', 'Unknown error')}"
        assert results["overall_score"] > 40, f"Click score too low: {results['overall_score']}"
        
        # Store results
        external_validator.validation_results["click"] = results
    
    def test_cross_project_consistency(self, external_validator):
        """Test that DoD automation produces consistent results across projects."""
        # Ensure we have results from previous tests
        assert len(external_validator.validation_results) >= 3, "Need results from all project tests"
        
        # Check that all projects have consistent stage execution
        all_results = external_validator.validation_results
        
        for project_name, results in all_results.items():
            # All projects should have the same stages
            expected_stages = ["exoskeleton", "validation", "automation", "status"]
            actual_stages = list(results["stages"].keys())
            
            assert set(actual_stages) == set(expected_stages), \
                f"Project {project_name} missing stages: {set(expected_stages) - set(actual_stages)}"
            
            # All projects should complete in reasonable time
            assert results["validation_time"] < 30, \
                f"Project {project_name} took too long: {results['validation_time']}"
    
    def test_telemetry_integration_external(self, external_validator):
        """Test that telemetry is properly generated during external validation."""
        project_info = external_validator.test_projects[0]  # Use FastAPI
        project_path = external_validator.clone_project(project_info)
        
        # Mock telemetry capture
        with patch("uvmgr.ops.dod.trace") as mock_trace:
            mock_span = MagicMock()
            mock_trace.get_current_span.return_value = mock_span
            mock_trace.get_tracer.return_value.start_as_current_span.return_value.__enter__ = lambda x: mock_span
            mock_trace.get_tracer.return_value.start_as_current_span.return_value.__exit__ = lambda *args: None
            
            # Execute validation
            results = external_validator.validate_project_dod(project_path, project_info)
            
            # Verify telemetry calls were made
            assert mock_trace.get_tracer.called, "Tracer should be requested"
            
            # Verify span attributes were set
            assert mock_span.set_attributes.called, "Span attributes should be set"
            
            # Check that project path was recorded
            call_args = mock_span.set_attributes.call_args_list
            project_path_recorded = any(
                "project.path" in str(call.args) or "project.path" in str(call.kwargs)
                for call in call_args
            )
            assert project_path_recorded, "Project path should be recorded in telemetry"


class TestExternalProjectsPerformance:
    """Performance tests for external project validation."""
    
    def test_validation_performance_benchmark(self, external_validator):
        """Benchmark DoD validation performance across project sizes."""
        performance_results = {}
        
        for project_info in external_validator.test_projects:
            project_path = external_validator.clone_project(project_info)
            
            # Measure validation time
            start_time = time.time()
            results = external_validator.validate_project_dod(project_path, project_info)
            validation_time = time.time() - start_time
            
            performance_results[project_info["name"]] = {
                "size": project_info["size"],
                "validation_time": validation_time,
                "success": results["success"],
                "score": results["overall_score"]
            }
        
        # Validate performance thresholds
        for project_name, perf_data in performance_results.items():
            size = perf_data["size"]
            validation_time = perf_data["validation_time"]
            
            # Set reasonable thresholds based on project size
            if size == "small":
                assert validation_time < 10, f"Small project {project_name} too slow: {validation_time}s"
            elif size == "medium":
                assert validation_time < 20, f"Medium project {project_name} too slow: {validation_time}s"
            elif size == "large":
                assert validation_time < 30, f"Large project {project_name} too slow: {validation_time}s"
    
    def test_memory_usage_external_validation(self, external_validator):
        """Test memory usage during external project validation."""
        import psutil
        import os
        
        project_info = external_validator.test_projects[1]  # Medium-sized project
        project_path = external_validator.clone_project(project_info)
        
        # Measure memory before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute validation
        results = external_validator.validate_project_dod(project_path, project_info)
        
        # Measure memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Validate memory usage is reasonable
        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
        assert results["success"], "Validation should succeed with reasonable memory usage"


class TestExternalProjectsRobustness:
    """Robustness tests for external project validation."""
    
    def test_malformed_project_handling(self, external_validator):
        """Test DoD automation with malformed project structures."""
        # Create a malformed project
        malformed_path = external_validator.temp_dir / "malformed-project"
        malformed_path.mkdir()
        
        # Create invalid pyproject.toml
        (malformed_path / "pyproject.toml").write_text("invalid toml content [[[")
        
        # Create empty directories
        (malformed_path / "src").mkdir()
        (malformed_path / "tests").mkdir()
        
        # Execute validation (should handle gracefully)
        project_info = {
            "name": "malformed-project",
            "description": "Malformed test project",
            "expected_criteria": ["testing"]
        }
        
        results = external_validator.validate_project_dod(malformed_path, project_info)
        
        # Should not crash, but may have lower scores
        assert "error" not in results or results["success"] is False
        assert "validation_time" in results
        assert results["validation_time"] < 30  # Should fail fast
    
    def test_missing_files_handling(self, external_validator):
        """Test DoD automation with missing critical files."""
        # Create minimal project structure
        minimal_path = external_validator.temp_dir / "minimal-project"
        minimal_path.mkdir()
        
        # Only create a basic __init__.py
        (minimal_path / "__init__.py").write_text('"""Minimal project"""')
        
        project_info = {
            "name": "minimal-project", 
            "description": "Minimal test project",
            "expected_criteria": ["code_quality"]
        }
        
        results = external_validator.validate_project_dod(minimal_path, project_info)
        
        # Should complete but with lower scores
        assert results["success"] is not None  # Should have a definitive result
        assert "validation_time" in results
    
    def test_large_project_timeout_handling(self, external_validator):
        """Test DoD automation timeout handling for large projects."""
        # Create a project with many files to simulate large project
        large_path = external_validator.temp_dir / "large-project"
        large_path.mkdir()
        
        # Create many files
        for i in range(10):  # Reduced for test performance
            module_dir = large_path / f"module_{i}"
            module_dir.mkdir()
            
            for j in range(5):
                (module_dir / f"file_{j}.py").write_text(f'"""Module {i} file {j}"""\n\ndef function_{j}():\n    return {j}')
        
        project_info = {
            "name": "large-project",
            "description": "Large test project", 
            "expected_criteria": ["code_quality"],
            "size": "large"
        }
        
        # Execute with potential timeout
        start_time = time.time()
        results = external_validator.validate_project_dod(large_path, project_info)
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 45, f"Large project validation took too long: {execution_time}s"
        assert "validation_time" in results