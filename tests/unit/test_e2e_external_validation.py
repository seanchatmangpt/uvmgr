"""
Unit tests for end-to-end external project validation functionality.
"""

import pytest
import tempfile
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the validation classes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from e2e_external_validation import ExternalProjectValidator


class TestExternalProjectValidator:
    """Test suite for ExternalProjectValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        uvmgr_path = Path(__file__).parent.parent.parent
        return ExternalProjectValidator(uvmgr_path)

    @pytest.fixture
    def mock_subprocess_result(self):
        """Mock subprocess result."""
        return {
            "success": True,
            "returncode": 0,
            "stdout": "Success output",
            "stderr": "",
            "duration": 0.5,
            "command": "test command"
        }

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.uvmgr_path.exists()
        assert validator.uvmgr_exe == sys.executable
        assert "timestamp" in validator.results
        assert "test_results" in validator.results

    def test_run_command_success(self, validator, mock_subprocess_result):
        """Test successful command execution."""
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Success"
            mock_process.stderr = ""
            mock_run.return_value = mock_process
            
            result = validator.run_command(["echo", "test"])
            
            assert result["success"] is True
            assert result["returncode"] == 0
            assert "duration" in result

    def test_run_command_failure(self, validator):
        """Test failed command execution."""
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.stdout = ""
            mock_process.stderr = "Error occurred"
            mock_run.return_value = mock_process
            
            result = validator.run_command(["false"])
            
            assert result["success"] is False
            assert result["returncode"] == 1
            assert "Error occurred" in result["stderr"]

    def test_run_command_timeout(self, validator):
        """Test command timeout handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["sleep", "10"], 1)
            
            result = validator.run_command(["sleep", "10"], timeout=1)
            
            assert result["success"] is False
            assert "timed out" in result["stderr"]

    def test_create_test_project_minimal(self, validator):
        """Test minimal project creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-minimal"
            
            validator.create_test_project(project_dir, "minimal")
            
            # Verify project structure
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "src" / "test_minimal" / "__init__.py").exists()
            assert (project_dir / "src" / "test_minimal" / "main.py").exists()
            assert (project_dir / "tests" / "test_main.py").exists()
            assert (project_dir / "README.md").exists()
            
            # Verify pyproject.toml content
            pyproject_content = (project_dir / "pyproject.toml").read_text()
            assert "test-minimal" in pyproject_content
            assert "hatchling" in pyproject_content
            assert "src/test_minimal" in pyproject_content

    def test_create_test_project_library(self, validator):
        """Test library project creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-library"
            
            validator.create_test_project(project_dir, "library")
            
            # Verify project structure
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "src" / "test_library" / "__init__.py").exists()
            assert (project_dir / "src" / "test_library" / "main.py").exists()
            
            # Verify dependencies
            pyproject_content = (project_dir / "pyproject.toml").read_text()
            assert "requests>=2.28.0" in pyproject_content
            assert "click>=8.0.0" in pyproject_content
            assert "optional-dependencies" in pyproject_content

    def test_create_test_project_application(self, validator):
        """Test application project creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-app"
            
            validator.create_test_project(project_dir, "application")
            
            # Verify project structure
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "src" / "test_app" / "__init__.py").exists()
            assert (project_dir / "src" / "test_app" / "cli.py").exists()
            
            # Verify CLI structure
            cli_content = (project_dir / "src" / "test_app" / "cli.py").read_text()
            assert "click" in cli_content
            assert "def main" in cli_content
            
            # Verify entry point
            pyproject_content = (project_dir / "pyproject.toml").read_text()
            assert "project.scripts" in pyproject_content
            assert "test_app.cli:main" in pyproject_content

    def test_validate_project_lifecycle_success(self, validator):
        """Test successful project lifecycle validation."""
        with patch.object(validator, 'run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "returncode": 0,
                "stdout": "Success",
                "stderr": "",
                "duration": 0.5
            }
            
            with patch.object(validator, 'create_test_project'):
                result = validator.validate_project_lifecycle("minimal")
                
                assert result["project_type"] == "minimal"
                assert result["success_rate"] == 1.0
                assert "8/8 steps passed" in result["summary"]
                assert len(result["steps"]) == 8

    def test_validate_project_lifecycle_partial_failure(self, validator):
        """Test project lifecycle with some failures."""
        def mock_run_command(cmd, **kwargs):
            # Simulate failure for lint check
            if "lint" in cmd:
                return {
                    "success": False,
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "Lint error",
                    "duration": 0.3
                }
            return {
                "success": True,
                "returncode": 0,
                "stdout": "Success",
                "stderr": "",
                "duration": 0.5
            }
        
        with patch.object(validator, 'run_command', side_effect=mock_run_command):
            with patch.object(validator, 'create_test_project'):
                result = validator.validate_project_lifecycle("library")
                
                assert result["project_type"] == "library"
                assert result["success_rate"] < 1.0
                # Should have one failed step
                failed_steps = [s for s in result["steps"] if not s["success"]]
                assert len(failed_steps) > 0

    def test_validate_advanced_features_success(self, validator):
        """Test successful advanced features validation."""
        with patch.object(validator, 'run_command') as mock_run:
            def mock_command(cmd, **kwargs):
                if "otel" in cmd and "validate" in cmd:
                    return {
                        "success": True,
                        "stdout": "100.0% success",
                        "stderr": "",
                        "returncode": 0,
                        "duration": 0.5
                    }
                return {
                    "success": True,
                    "stdout": "Success",
                    "stderr": "",
                    "returncode": 0,
                    "duration": 0.5
                }
            
            mock_run.side_effect = mock_command
            
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                
                result = validator.validate_advanced_features()
                
                assert result["feature"] == "advanced"
                assert len(result["tests"]) == 4
                
                # Check OTEL validation specifically
                otel_test = next(t for t in result["tests"] if t["name"] == "OTEL Validation")
                assert otel_test["success"] is True

    def test_validate_advanced_features_otel_failure(self, validator):
        """Test advanced features with OTEL failure."""
        with patch.object(validator, 'run_command') as mock_run:
            def mock_command(cmd, **kwargs):
                if "otel" in cmd and "validate" in cmd:
                    return {
                        "success": False,
                        "stdout": "50.0% success",
                        "stderr": "OTEL validation failed",
                        "returncode": 1,
                        "duration": 0.5
                    }
                return {
                    "success": True,
                    "stdout": "Success",
                    "stderr": "",
                    "returncode": 0,
                    "duration": 0.5
                }
            
            mock_run.side_effect = mock_command
            
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                
                result = validator.validate_advanced_features()
                
                # Check OTEL validation specifically
                otel_test = next(t for t in result["tests"] if t["name"] == "OTEL Validation")
                assert otel_test["success"] is False

    @patch('sys.exit')
    def test_run_validation_success(self, mock_exit, validator):
        """Test full validation run with success."""
        with patch.object(validator, 'validate_project_lifecycle') as mock_lifecycle:
            mock_lifecycle.return_value = {
                "project_type": "test",
                "success_rate": 1.0,
                "steps": [{"success": True}] * 8,
                "summary": "8/8 steps passed"
            }
            
            with patch.object(validator, 'validate_advanced_features') as mock_advanced:
                mock_advanced.return_value = {
                    "tests": [{"success": True}] * 4
                }
                
                with patch('builtins.print'):  # Suppress print output
                    validator.run_validation()
                
                # Should exit with success
                mock_exit.assert_called_with(0)
                
                # Check summary
                assert validator.results["summary"]["success_rate"] >= 0.8

    @patch('sys.exit')
    def test_run_validation_failure(self, mock_exit, validator):
        """Test full validation run with failure."""
        with patch.object(validator, 'validate_project_lifecycle') as mock_lifecycle:
            mock_lifecycle.return_value = {
                "project_type": "test",
                "success_rate": 0.5,  # Below threshold
                "steps": [{"success": False}] * 4 + [{"success": True}] * 4,
                "summary": {}  # Patch: add summary key to match code under test
            }
            
            with patch.object(validator, 'validate_advanced_features') as mock_advanced:
                mock_advanced.return_value = {
                    "tests": [{"success": False}] * 4,
                    "summary": {}  # Patch: add summary key
                }
                
                with patch('builtins.print'):
                    validator.run_validation()
                
                # Should exit with failure
                mock_exit.assert_called_with(1)
                
                # Check summary
                assert validator.results["summary"]["success_rate"] < 0.8

    def test_results_json_serializable(self, validator):
        """Test that results can be serialized to JSON."""
        # Add some test data
        validator.results["test_results"] = [{
            "project_type": "test",
            "success_rate": 1.0,
            "steps": [{"name": "test", "success": True, "duration": 0.5}]
        }]
        
        # Should not raise an exception
        json_str = json.dumps(validator.results)
        
        # Should be able to load back
        loaded_results = json.loads(json_str)
        assert loaded_results["test_results"][0]["project_type"] == "test"

    def test_project_types_coverage(self, validator):
        """Test that all expected project types are covered."""
        expected_types = ["minimal", "library", "application"]
        
        with patch.object(validator, 'validate_project_lifecycle') as mock_lifecycle:
            mock_lifecycle.return_value = {
                "project_type": "test",
                "success_rate": 1.0,
                "steps": [],
                "summary": {}  # Patch: add summary key
            }
            
            with patch.object(validator, 'validate_advanced_features') as mock_advanced:
                mock_advanced.return_value = {"tests": [], "summary": {}}  # Patch: add summary key
                
                with patch('builtins.print'), patch('sys.exit'):
                    validator.run_validation()
        
        # Should have been called for each project type
        assert mock_lifecycle.call_count == len(expected_types)
        
        called_types = [call[0][0] for call in mock_lifecycle.call_args_list]
        for expected_type in expected_types:
            assert expected_type in called_types


@pytest.mark.integration
class TestExternalProjectValidatorIntegration:
    """Integration tests for external project validator."""

    def test_real_project_creation(self):
        """Test creating a real project structure."""
        uvmgr_path = Path(__file__).parent.parent.parent
        validator = ExternalProjectValidator(uvmgr_path)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "integration-test"
            
            validator.create_test_project(project_dir, "minimal")
            
            # Verify all files exist and have content
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "src").exists()
            assert (project_dir / "tests").exists()
            
            # Verify pyproject.toml is valid TOML
            import tomllib
            with open(project_dir / "pyproject.toml", "rb") as f:
                toml_data = tomllib.load(f)
                assert "project" in toml_data
                assert "build-system" in toml_data

    def test_command_timeout_handling(self):
        """Test real timeout handling."""
        uvmgr_path = Path(__file__).parent.parent.parent
        validator = ExternalProjectValidator(uvmgr_path)
        
        # Use a command that will timeout
        result = validator.run_command(["sleep", "5"], timeout=1)
        
        assert result["success"] is False
        assert "timed out" in result["stderr"]
        assert result["duration"] >= 1.0  # Should be at least timeout duration


if __name__ == "__main__":
    pytest.main([__file__])