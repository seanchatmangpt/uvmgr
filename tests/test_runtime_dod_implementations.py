"""
Unit tests for DoD runtime implementations.

Tests the actual runtime validation functions to ensure they work correctly
with real project scenarios and edge cases.
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from uvmgr.runtime.dod import (
    run_e2e_tests,
    _execute_testing_validation,
    _execute_security_validation,
    _execute_documentation_validation,
    create_automation_report,
    analyze_project_health,
)


class TestRunE2ETests:
    """Test the run_e2e_tests implementation."""

    def test_run_e2e_tests_with_no_tests(self):
        """Test E2E testing with no test files present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = run_e2e_tests(
                project_path=project_path,
                environment="test",
                parallel=False,
                headless=True,
                record_video=False,
                generate_report=False
            )
            
            assert result["success"] is False
            assert result["total_tests"] == 0
            assert result["test_suites"] == {}
            assert result["frameworks_detected"] == []

    def test_run_e2e_tests_with_mock_test_files(self):
        """Test E2E testing with mock test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create mock test files
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            
            # Create API test file
            api_test = tests_dir / "test_api_endpoints.py"
            api_test.write_text("""
import pytest

def test_get_users():
    assert True

def test_create_user():
    assert True
""")
            
            # Create integration test file
            integration_test = tests_dir / "test_integration_flows.py"
            integration_test.write_text("""
import pytest

def test_user_registration_flow():
    assert True
""")
            
            # Mock subprocess to simulate pytest success
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="3 passed",
                    stderr=""
                )
                
                result = run_e2e_tests(
                    project_path=project_path,
                    environment="test",
                    parallel=False,
                    headless=True,
                    record_video=False,
                    generate_report=True
                )
                
                assert result["success"] is True
                assert result["total_tests"] > 0
                assert "api_tests" in result["test_suites"]
                assert "integration_tests" in result["test_suites"]
                assert result["report_path"] is not None

    def test_run_e2e_tests_with_pytest_failure(self):
        """Test E2E testing when pytest fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            test_file = project_path / "test_general.py"
            test_file.write_text("def test_failure(): assert False")
            
            # Mock subprocess to simulate pytest failure
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="0 passed, 1 FAILED",
                    stderr="AssertionError"
                )
                
                result = run_e2e_tests(
                    project_path=project_path,
                    environment="test",
                    parallel=False,
                    headless=True,
                    record_video=False,
                    generate_report=False
                )
                
                assert result["success"] is False
                assert result["total_tests"] > 0
                assert result["failed_tests"] > 0

    def test_run_e2e_tests_timeout_handling(self):
        """Test E2E testing timeout handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            e2e_dir = project_path / "e2e"
            e2e_dir.mkdir()
            test_file = e2e_dir / "test_browser.py"
            test_file.write_text("def test_long_running(): assert True")
            
            # Mock subprocess to simulate timeout
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)
                
                result = run_e2e_tests(
                    project_path=project_path,
                    environment="test",
                    parallel=False,
                    headless=True,
                    record_video=False,
                    generate_report=False
                )
                
                assert result["success"] is False
                assert "browser_tests" in result["test_suites"]
                assert "error" in result["test_suites"]["browser_tests"]
                assert "timed out" in result["test_suites"]["browser_tests"]["error"]

    def test_run_e2e_tests_report_generation(self):
        """Test report generation functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            test_file = project_path / "test_sample.py"
            test_file.write_text("def test_sample(): assert True")
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="1 passed, 0 failed",
                    stderr=""
                )
                
                result = run_e2e_tests(
                    project_path=project_path,
                    environment="production",
                    parallel=True,
                    headless=False,
                    record_video=True,
                    generate_report=True
                )
                
                # Check report was generated
                assert result["report_path"] is not None
                report_path = Path(result["report_path"])
                assert report_path.exists()
                
                # Validate report content
                with open(report_path) as f:
                    report_data = json.load(f)
                
                assert report_data["environment"] == "production"
                assert report_data["configuration"]["parallel"] is True
                assert report_data["configuration"]["headless"] is False
                assert report_data["configuration"]["record_video"] is True
                assert "summary" in report_data
                assert "test_suites" in report_data


class TestExecuteTestingValidation:
    """Test the _execute_testing_validation implementation."""

    def test_execute_testing_validation_no_tests_no_autofix(self):
        """Test testing validation with no tests and no auto-fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_testing_validation(
                project_path=project_path,
                environment="test",
                auto_fix=False
            )
            
            assert result["success"] is False
            assert result["score"] == 0.0
            assert "No test files found" in result["details"]
            assert "No test files found" in result["errors"]

    def test_execute_testing_validation_no_tests_with_autofix(self):
        """Test testing validation with no tests but auto-fix enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_testing_validation(
                project_path=project_path,
                environment="test",
                auto_fix=True
            )
            
            assert result["success"] is True
            assert result["score"] == 50.0
            assert "Created basic test structure" in result["details"]
            assert "Created tests/ directory" in result["fixes_applied"]
            
            # Verify test structure was created
            tests_dir = project_path / "tests"
            assert tests_dir.exists()
            assert (tests_dir / "test_basic.py").exists()

    def test_execute_testing_validation_with_pytest_available(self):
        """Test testing validation when pytest is available and tests pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            test_file = project_path / "test_example.py"
            test_file.write_text("def test_example(): assert True")
            
            # Mock subprocess calls
            with patch('subprocess.run') as mock_run:
                # First call: pytest --version (success)
                # Second call: pytest --tb=short (success)
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="pytest 7.0.0", stderr=""),
                    MagicMock(returncode=0, stdout="1 passed", stderr="")
                ]
                
                result = _execute_testing_validation(
                    project_path=project_path,
                    environment="test",
                    auto_fix=False
                )
                
                assert result["success"] is True
                assert result["score"] == 90.0
                assert "Tests passed" in result["details"]

    def test_execute_testing_validation_pytest_not_available(self):
        """Test testing validation when pytest is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            test_file = project_path / "test_example.py"
            test_file.write_text("def test_example(): assert True")
            
            # Mock subprocess to simulate pytest not available
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="No module named pytest")
                
                result = _execute_testing_validation(
                    project_path=project_path,
                    environment="test",
                    auto_fix=False
                )
                
                assert result["success"] is False
                assert result["score"] == 20.0
                assert "pytest not available" in result["details"]

    def test_execute_testing_validation_tests_fail(self):
        """Test testing validation when tests fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test file
            test_file = project_path / "test_failing.py"
            test_file.write_text("def test_failing(): assert False")
            
            with patch('subprocess.run') as mock_run:
                # pytest available but tests fail
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="pytest 7.0.0", stderr=""),
                    MagicMock(returncode=1, stdout="0 passed, 1 failed", stderr="FAILED test_failing.py")
                ]
                
                result = _execute_testing_validation(
                    project_path=project_path,
                    environment="test",
                    auto_fix=False
                )
                
                assert result["success"] is False
                assert result["score"] == 30.0
                assert "Tests failed" in result["details"]


class TestExecuteSecurityValidation:
    """Test the _execute_security_validation implementation."""

    def test_execute_security_validation_no_config_no_autofix(self):
        """Test security validation with no security config and no auto-fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_security_validation(
                project_path=project_path,
                environment="test",
                auto_fix=False
            )
            
            assert result["success"] is False
            assert result["score"] < 70.0

    def test_execute_security_validation_with_autofix(self):
        """Test security validation with auto-fix enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_security_validation(
                project_path=project_path,
                environment="test",
                auto_fix=True
            )
            
            assert result["score"] > 0
            assert len(result["fixes_applied"]) > 0
            
            # Verify files were created
            assert (project_path / ".bandit").exists()
            assert (project_path / "requirements.txt").exists()
            assert (project_path / ".env.example").exists()

    def test_execute_security_validation_existing_config(self):
        """Test security validation with existing security configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create existing security files
            (project_path / ".bandit").write_text("[bandit]\nexclude_dirs = tests\n")
            (project_path / "poetry.lock").write_text("# Poetry lock file\n")
            (project_path / ".env.example").write_text("# Environment variables\n")
            
            with patch('subprocess.run') as mock_run:
                # Mock bandit available and successful scan
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="bandit 1.7.0", stderr=""),
                    MagicMock(returncode=0, stdout="No issues identified", stderr="")
                ]
                
                result = _execute_security_validation(
                    project_path=project_path,
                    environment="test",
                    auto_fix=False
                )
                
                assert result["success"] is True
                assert result["score"] >= 70.0

    def test_execute_security_validation_bandit_finds_issues(self):
        """Test security validation when bandit finds security issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create security files
            (project_path / ".bandit").write_text("[bandit]\n")
            
            with patch('subprocess.run') as mock_run:
                # Mock bandit finds issues
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="bandit 1.7.0", stderr=""),
                    MagicMock(returncode=1, stdout="Issues found", stderr="High severity issue found")
                ]
                
                result = _execute_security_validation(
                    project_path=project_path,
                    environment="test",
                    auto_fix=False
                )
                
                assert "Bandit scan found issues" in str(result["errors"])


class TestExecuteDocumentationValidation:
    """Test the _execute_documentation_validation implementation."""

    def test_execute_documentation_validation_basic(self):
        """Test basic documentation validation functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_documentation_validation(
                project_path=project_path,
                environment="test",
                auto_fix=False
            )
            
            # Should not fail completely
            assert "success" in result
            assert "score" in result
            assert "details" in result


class TestCreateAutomationReport:
    """Test the create_automation_report implementation."""

    def test_create_automation_report_without_ai_insights(self):
        """Test automation report creation without AI insights."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            automation_result = {
                "success": True,
                "overall_success_rate": 0.85,
                "execution_time": 45.2,
                "criteria_results": {
                    "testing": {"passed": True, "score": 90.0},
                    "security": {"passed": True, "score": 80.0}
                }
            }
            
            result = create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=False
            )
            
            assert result["success"] is True
            assert "report_file" in result
            
            # Verify report file was created
            report_file = Path(result["report_file"])
            assert report_file.exists()
            
            # Verify report content
            with open(report_file) as f:
                report_data = json.load(f)
            
            assert report_data["automation_summary"]["overall_success"] is True
            assert report_data["automation_summary"]["success_rate"] == 0.85
            assert report_data["automation_summary"]["execution_time"] == 45.2
            assert len(report_data["ai_insights"]) == 0

    def test_create_automation_report_with_ai_insights_raises_error(self):
        """Test automation report creation with AI insights raises NotImplementedError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            automation_result = {"success": True}
            
            with pytest.raises(NotImplementedError, match="AI insights generation is not yet implemented"):
                create_automation_report(
                    project_path=project_path,
                    automation_result=automation_result,
                    include_ai_insights=True
                )


class TestAnalyzeProjectHealth:
    """Test the analyze_project_health implementation."""

    def test_analyze_project_health_basic(self):
        """Test basic project health analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = analyze_project_health(
                project_path=project_path,
                detailed=False,
                suggestions=True
            )
            
            # Should not fail completely and return basic structure
            assert "success" in result
            if result.get("success"):
                assert "overall_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])