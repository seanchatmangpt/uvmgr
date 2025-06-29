"""
Unit tests for uvmgr.runtime.tests module.

Tests test execution runtime functionality including pytest execution,
coverage reporting, CI pipeline, and test discovery.
"""

import pytest
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, mock_open, call
from pathlib import Path

from uvmgr.runtime.tests import (
    execute_pytest, generate_coverage_report, run_ci_pipeline,
    discover_test_files, validate_test_environment,
    _parse_pytest_json_report, _parse_coverage_report, 
    _extract_coverage_percentage, _run_ci_step
)


class TestExecutePytest:
    """Test pytest execution functionality."""
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests._parse_pytest_json_report')
    @patch('uvmgr.runtime.tests._parse_coverage_report')
    @patch('uvmgr.runtime.tests.span')
    @patch('tempfile.NamedTemporaryFile')
    @patch('pathlib.Path.unlink')
    def test_execute_pytest_basic(self, mock_unlink, mock_tempfile, mock_span, 
                                 mock_parse_coverage, mock_parse_json, mock_subprocess):
        """Test basic pytest execution."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock temporary file context manager
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/report.json"
        mock_temp_file.__enter__ = Mock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = Mock(return_value=None)
        mock_tempfile.return_value = mock_temp_file
        
        # Mock subprocess result for pytest execution
        mock_pytest_result = Mock()
        mock_pytest_result.returncode = 0
        mock_pytest_result.stdout = "10 passed"
        mock_pytest_result.stderr = ""
        
        mock_subprocess.return_value = mock_pytest_result
        
        # Mock parsers
        mock_parse_json.return_value = {"total": 10, "passed": 10, "failed": 0, "skipped": 0}
        mock_parse_coverage.return_value = {"percentage": 95.0}
        
        result = execute_pytest(parallel=False)
        
        # Should only have 1 call since parallel=False
        assert mock_subprocess.call_count == 1
        pytest_call_args = mock_subprocess.call_args[0][0]
        assert "python" in pytest_call_args
        assert "-m" in pytest_call_args  
        assert "pytest" in pytest_call_args
        assert "-q" in pytest_call_args  # quiet by default
        assert "--cov=src" in pytest_call_args  # coverage enabled by default
        assert "--json-report" in pytest_call_args
        
        # Verify result
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["total_tests"] == 10
        assert result["passed"] == 10
        assert result["failed"] == 0
        assert result["coverage"]["percentage"] == 95.0
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    @patch('tempfile.NamedTemporaryFile')
    @patch('pathlib.Path.unlink')
    def test_execute_pytest_verbose_parallel(self, mock_unlink, mock_tempfile, 
                                           mock_span, mock_subprocess):
        """Test pytest execution with verbose and parallel options."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/report.json"
        mock_tempfile.return_value = mock_temp_file
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock xdist availability
        with patch('uvmgr.runtime.tests.subprocess.run') as mock_xdist_check:
            mock_xdist_check.return_value = Mock()  # Success means xdist available
            
            execute_pytest(verbose=True, parallel=True, coverage=False)
        
        # Get the actual pytest call (not the xdist check)
        pytest_call = mock_subprocess.call_args
        args = pytest_call[0][0]
        
        assert "-v" in args  # verbose
        assert "-n" in args and "auto" in args  # parallel
        assert "--cov=src" not in args  # coverage disabled
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    @patch('tempfile.NamedTemporaryFile')
    def test_execute_pytest_with_markers(self, mock_tempfile, mock_span, mock_subprocess):
        """Test pytest execution with markers."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/report.json"
        mock_tempfile.return_value = mock_temp_file
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        execute_pytest(markers=["unit", "slow"], fail_fast=True)
        
        args = mock_subprocess.call_args[0][0]
        assert "-m" in args
        marker_indices = [i for i, arg in enumerate(args) if arg == "-m"]
        markers = [args[i + 1] for i in marker_indices]
        assert "unit" in markers
        assert "slow" in markers
        assert "-x" in args  # fail fast
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    @patch('tempfile.NamedTemporaryFile')
    def test_execute_pytest_failure(self, mock_tempfile, mock_span, mock_subprocess):
        """Test pytest execution with test failures."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/report.json"
        mock_tempfile.return_value = mock_temp_file
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "5 passed, 2 failed"
        mock_result.stderr = "Some tests failed"
        mock_subprocess.return_value = mock_result
        
        with patch('uvmgr.runtime.tests._parse_pytest_json_report') as mock_parse:
            mock_parse.return_value = {"total": 7, "passed": 5, "failed": 2, "skipped": 0}
            
            result = execute_pytest()
        
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["failed"] == 2
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    @patch('tempfile.NamedTemporaryFile')
    def test_execute_pytest_timeout(self, mock_tempfile, mock_span, mock_subprocess):
        """Test pytest execution timeout handling."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/report.json"
        mock_tempfile.return_value = mock_temp_file
        
        mock_subprocess.side_effect = subprocess.TimeoutExpired("pytest", 300)
        
        result = execute_pytest()
        
        assert result["success"] is False
        assert "timed out" in result["error"]
        assert result["timeout"] is True


class TestGenerateCoverageReport:
    """Test coverage report generation."""
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests._extract_coverage_percentage')
    @patch('uvmgr.runtime.tests.span')
    def test_generate_coverage_html(self, mock_span, mock_extract, mock_subprocess):
        """Test HTML coverage report generation."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_result = Mock()
        mock_result.stdout = "Total coverage: 85%"
        mock_subprocess.return_value = mock_result
        mock_extract.return_value = 85.0
        
        result = generate_coverage_report(format_type="html")
        
        args = mock_subprocess.call_args[0][0]
        assert "python" in args
        assert "-m" in args
        assert "coverage" in args
        assert "html" in args
        assert "--directory=reports/htmlcov" in args
        
        assert result["success"] is True
        assert result["format"] == "html"
        assert result["percentage"] == 85.0
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    def test_generate_coverage_xml(self, mock_span, mock_subprocess):
        """Test XML coverage report generation."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_result = Mock()
        mock_result.stdout = "Coverage XML generated"
        mock_subprocess.return_value = mock_result
        
        with patch('uvmgr.runtime.tests._extract_coverage_percentage') as mock_extract:
            mock_extract.return_value = 90.0
            
            result = generate_coverage_report(format_type="xml", min_coverage=80.0)
        
        args = mock_subprocess.call_args[0][0]
        assert "xml" in args
        assert "-o" in args
        assert "reports/coverage.xml" in args
        assert "--fail-under" in args
        assert "80.0" in args
        
        assert result["meets_threshold"] is True
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests.span')
    def test_generate_coverage_failure(self, mock_span, mock_subprocess):
        """Test coverage report generation failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "coverage", "No data to report")
        error.stdout = ""
        error.stderr = "No data to report"
        mock_subprocess.side_effect = error
        
        result = generate_coverage_report()
        
        assert result["success"] is False
        assert result["error"] == str(error)


class TestRunCiPipeline:
    """Test CI pipeline execution."""
    
    @patch('uvmgr.runtime.tests._run_ci_step')
    @patch('uvmgr.runtime.tests.execute_pytest')
    @patch('uvmgr.runtime.tests.span')
    def test_run_ci_pipeline_comprehensive(self, mock_span, mock_execute_pytest, mock_run_ci_step):
        """Test comprehensive CI pipeline execution."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock successful CI steps
        mock_run_ci_step.return_value = {"name": "test_step", "success": True}
        
        # Mock successful test execution
        mock_execute_pytest.return_value = {
            "success": True,
            "total_tests": 50,
            "passed": 48,
            "failed": 2
        }
        
        result = run_ci_pipeline(comprehensive=True)
        
        assert result["comprehensive"] is True
        assert result["overall_success"] is True
        assert len(result["steps"]) >= 3  # lint, type_check, test_suite
        assert "test_results" in result
        
        # Verify CI steps were called
        assert mock_run_ci_step.call_count >= 2  # At least lint and type check
        mock_execute_pytest.assert_called_once_with(coverage=True)
    
    @patch('uvmgr.runtime.tests._run_ci_step')
    @patch('uvmgr.runtime.tests.span')
    def test_run_ci_pipeline_quick(self, mock_span, mock_run_ci_step):
        """Test quick CI pipeline execution."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_run_ci_step.return_value = {"name": "test_step", "success": True}
        
        result = run_ci_pipeline(quick=True)
        
        assert result["quick"] is True
        assert "test_results" not in result  # No full test suite in quick mode
        assert len(result["steps"]) == 2  # Only lint and type check
    
    @patch('uvmgr.runtime.tests._run_ci_step')
    @patch('uvmgr.runtime.tests.span')
    def test_run_ci_pipeline_with_failures(self, mock_span, mock_run_ci_step):
        """Test CI pipeline with step failures."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock lint failure
        def side_effect(name, cmd):
            if "lint" in name:
                return {"name": name, "success": False, "error": "Lint errors found"}
            return {"name": name, "success": True}
        
        mock_run_ci_step.side_effect = side_effect
        
        result = run_ci_pipeline(quick=True)
        
        assert result["overall_success"] is False
        failed_steps = [step for step in result["steps"] if not step["success"]]
        assert len(failed_steps) == 1
        assert "lint" in failed_steps[0]["name"]


class TestDiscoverTestFiles:
    """Test test file discovery."""
    
    @patch('pathlib.Path.rglob')
    @patch('uvmgr.runtime.tests.span')
    def test_discover_test_files_basic(self, mock_span, mock_rglob):
        """Test basic test file discovery."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock test files
        test_files = [
            Path("tests/unit/test_module.py"),
            Path("tests/integration/test_api.py"),
            Path("tests/e2e/test_browser.py")
        ]
        mock_rglob.return_value = test_files
        
        result = discover_test_files()
        
        assert result["total_files"] == 3
        assert len(result["test_files"]) == 3
        
        # Check categorization
        assert len(result["test_types"]["unit"]) == 1
        assert len(result["test_types"]["integration"]) == 1
        assert len(result["test_types"]["e2e"]) == 1
    
    @patch('pathlib.Path.rglob')
    @patch('uvmgr.runtime.tests.span')
    def test_discover_test_files_with_path(self, mock_span, mock_rglob):
        """Test test file discovery with custom path."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        test_files = [Path("custom/test_custom.py")]
        mock_rglob.return_value = test_files
        
        custom_path = Path("/custom/path")
        result = discover_test_files(path=custom_path, pattern="test_*.py")
        
        mock_rglob.assert_called_with("test_*.py")
        assert result["total_files"] == 1
    
    @patch('pathlib.Path.rglob')
    @patch('uvmgr.runtime.tests.span')
    def test_discover_test_files_categorization(self, mock_span, mock_rglob):
        """Test test file categorization logic."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        test_files = [
            Path("tests/test_unit_module.py"),      # unit (default)
            Path("integration/test_database.py"),   # integration
            Path("e2e/test_frontend.py"),          # e2e
            Path("tests/integration_test.py"),      # integration
            Path("tests/e2e_test_workflow.py")     # e2e
        ]
        mock_rglob.return_value = test_files
        
        result = discover_test_files()
        
        assert len(result["test_types"]["unit"]) == 1
        assert len(result["test_types"]["integration"]) == 2
        assert len(result["test_types"]["e2e"]) == 2


class TestValidateTestEnvironment:
    """Test test environment validation."""
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('uvmgr.runtime.tests.span')
    def test_validate_test_environment_success(self, mock_span, mock_exists, mock_subprocess):
        """Test successful test environment validation."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock successful subprocess calls for pytest and coverage
        mock_subprocess.return_value = Mock()
        mock_exists.return_value = True  # tests directory exists
        
        result = validate_test_environment()
        
        assert result["valid"] is True
        assert result["dependencies_available"] is True
        assert len(result["issues"]) == 0
        
        # Verify pytest and coverage checks
        assert mock_subprocess.call_count == 2
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('uvmgr.runtime.tests.span')
    def test_validate_test_environment_missing_deps(self, mock_span, mock_exists, mock_subprocess):
        """Test test environment validation with missing dependencies."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock failed subprocess calls
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "pytest")
        mock_exists.return_value = False  # tests directory missing
        
        result = validate_test_environment()
        
        assert result["valid"] is False
        assert result["dependencies_available"] is False
        assert "pytest not available" in result["issues"]
        assert "tests directory not found" in result["issues"]


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_parse_pytest_json_report_success(self):
        """Test parsing successful pytest JSON report."""
        report_data = {
            "summary": {
                "total": 10,
                "passed": 8,
                "failed": 1,
                "skipped": 1,
                "error": 0
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(report_data))):
            result = _parse_pytest_json_report("/tmp/report.json")
        
        assert result["total"] == 10
        assert result["passed"] == 8
        assert result["failed"] == 1
        assert result["skipped"] == 1
        assert result["errors"] == 0
    
    def test_parse_pytest_json_report_missing_file(self):
        """Test parsing pytest JSON report with missing file."""
        result = _parse_pytest_json_report("/nonexistent/report.json")
        
        assert result["total"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["skipped"] == 0
    
    @patch('pathlib.Path.exists')
    @patch('xml.etree.ElementTree.parse')
    def test_parse_coverage_report_success(self, mock_parse, mock_exists):
        """Test parsing successful coverage XML report."""
        mock_exists.return_value = True
        
        # Mock XML tree
        mock_root = Mock()
        mock_root.get.return_value = "0.85"  # 85% coverage
        mock_tree = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _parse_coverage_report()
        
        assert result["percentage"] == 85.0
        assert result["format"] == "xml"
    
    @patch('pathlib.Path.exists')
    def test_parse_coverage_report_missing_file(self, mock_exists):
        """Test parsing coverage report with missing file."""
        mock_exists.return_value = False
        
        result = _parse_coverage_report()
        
        assert result == {}
    
    def test_extract_coverage_percentage_total_format(self):
        """Test extracting coverage percentage from TOTAL format."""
        output = """
        src/module.py    100%
        TOTAL            95%
        """
        
        result = _extract_coverage_percentage(output)
        assert result == 95.0
    
    def test_extract_coverage_percentage_verbose_format(self):
        """Test extracting coverage percentage from verbose format."""
        output = "Total coverage: 87.5%"
        
        result = _extract_coverage_percentage(output)
        assert result == 87.5
    
    def test_extract_coverage_percentage_no_match(self):
        """Test extracting coverage percentage with no match."""
        output = "No coverage information found"
        
        result = _extract_coverage_percentage(output)
        assert result == 0.0
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    def test_run_ci_step_success(self, mock_subprocess):
        """Test successful CI step execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "All checks passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = _run_ci_step("lint", ["ruff", "check", "."])
        
        assert result["name"] == "lint"
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["output"] == "All checks passed"
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    def test_run_ci_step_failure(self, mock_subprocess):
        """Test failed CI step execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Lint errors found"
        mock_subprocess.return_value = mock_result
        
        result = _run_ci_step("lint", ["ruff", "check", "."])
        
        assert result["name"] == "lint"
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["stderr"] == "Lint errors found"
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    def test_run_ci_step_timeout(self, mock_subprocess):
        """Test CI step timeout handling."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ruff", 60)
        
        result = _run_ci_step("lint", ["ruff", "check", "."])
        
        assert result["name"] == "lint"
        assert result["success"] is False
        assert "timed out" in result["error"]


class TestIntegration:
    """Integration tests for test runtime module."""
    
    @patch('uvmgr.runtime.tests.subprocess.run')
    @patch('uvmgr.runtime.tests._run_ci_step')
    def test_complete_test_workflow(self, mock_run_ci_step, mock_subprocess):
        """Test complete test workflow from discovery to CI."""
        with patch('uvmgr.runtime.tests.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            # 1. Validate environment
            with patch('pathlib.Path.exists', return_value=True):
                mock_subprocess.return_value = Mock()  # pytest/coverage available
                env_result = validate_test_environment()
                assert env_result["valid"] is True
            
            # 2. Discover test files
            with patch('pathlib.Path.rglob') as mock_rglob:
                mock_rglob.return_value = [Path("tests/test_module.py")]
                discover_result = discover_test_files()
                assert discover_result["total_files"] == 1
            
            # 3. Execute tests
            with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
                with patch('pathlib.Path.unlink'):
                    mock_temp_file = Mock()
                    mock_temp_file.name = "/tmp/report.json"
                    mock_tempfile.return_value = mock_temp_file
                    
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_subprocess.return_value = mock_result
                    
                    with patch('uvmgr.runtime.tests._parse_pytest_json_report') as mock_parse:
                        mock_parse.return_value = {"total": 5, "passed": 5, "failed": 0, "skipped": 0}
                        
                        test_result = execute_pytest()
                        assert test_result["success"] is True
            
            # 4. Run CI pipeline
            mock_run_ci_step.return_value = {"name": "lint", "success": True}
            ci_result = run_ci_pipeline(quick=True)
            assert ci_result["overall_success"] is True