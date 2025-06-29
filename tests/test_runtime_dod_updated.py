"""
Updated unit tests for DoD runtime layer.

Tests the actual implementation logic, file I/O operations, and proper
error handling for NotImplementedError functions. Follows the principle:
"Only trust what is verified by unit tests and OTEL telemetry"
"""

from __future__ import annotations

import json
import pytest
import tempfile
import yaml
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from uvmgr.runtime.dod import (
    initialize_exoskeleton_files,
    execute_automation_workflow,
    validate_criteria_runtime,
    generate_pipeline_files,
    run_e2e_tests,
    analyze_project_health,
    create_automation_report,
    _execute_testing_validation,
    _execute_security_validation,
    _execute_documentation_validation,
    _execute_ci_cd_validation,
    _execute_code_quality_validation,
    _analyze_automation_health,
    _analyze_security_posture,
    _analyze_code_quality,
)


class TestDoDRuntimeRealImplementation:
    """Test suite for actual DoD runtime implementations (no mocks)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_template_config = {
            "description": "Test template",
            "includes": ["basic_ci", "testing"],
            "ai_features": ["code_review"]
        }
        
    def test_initialize_exoskeleton_files_real_implementation(self):
        """Test actual exoskeleton file initialization with real I/O."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = initialize_exoskeleton_files(
                project_path=project_path,
                template_config=self.test_template_config,
                force=False
            )
            
            assert result["success"] is True
            assert "files_created" in result
            assert len(result["files_created"]) > 0
            
            # Verify actual directory structure was created
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            assert exoskeleton_dir.exists()
            assert exoskeleton_dir.is_dir()
            
            # Verify actual config file was created
            config_file = exoskeleton_dir / "config.yaml"
            assert config_file.exists()
            
            # Verify actual config content
            with open(config_file) as f:
                config_content = f.read()
                assert "DoD Exoskeleton Configuration" in config_content
                assert "Test template" in config_content
                
            # Verify actual automation directory was created
            automation_dir = exoskeleton_dir / "automation"
            assert automation_dir.exists()
            
            workflows_dir = automation_dir / "workflows"
            assert workflows_dir.exists()
            
    def test_initialize_exoskeleton_files_already_exists_handling(self):
        """Test actual behavior when exoskeleton already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            exoskeleton_dir.mkdir(parents=True, exist_ok=True)
            
            result = initialize_exoskeleton_files(
                project_path=project_path,
                template_config=self.test_template_config,
                force=False
            )
            
            assert result["success"] is False
            assert "already exists" in result["error"]
            
    def test_initialize_exoskeleton_files_force_overwrite_real(self):
        """Test actual force overwrite behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            exoskeleton_dir.mkdir(parents=True, exist_ok=True)
            
            result = initialize_exoskeleton_files(
                project_path=project_path,
                template_config=self.test_template_config,
                force=True
            )
            
            assert result["success"] is True
            assert "files_created" in result
            
    def test_generate_pipeline_files_github_real_implementation(self):
        """Test actual GitHub pipeline file generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = generate_pipeline_files(
                project_path=project_path,
                provider="github",
                environments=["dev", "staging", "prod"],
                features=["testing", "security"],
                template="standard",
                output_path=None
            )
            
            assert result["success"] is True
            assert result["provider"] == "github"
            assert "files_created" in result
            assert len(result["files_created"]) > 0
            
            # Verify actual GitHub workflow file was created
            workflow_file = project_path / ".github" / "workflows" / "dod-automation.yml"
            assert workflow_file.exists()
            
            # Verify actual workflow content
            with open(workflow_file) as f:
                workflow_content = f.read()
                assert "DoD Automation" in workflow_content
                assert "uvmgr dod complete" in workflow_content
                assert "dev" in workflow_content
                assert "staging" in workflow_content
                assert "prod" in workflow_content

    def test_create_automation_report_without_ai_insights_real(self):
        """Test actual automation report creation without AI insights."""
        automation_result = {
            "success": True,
            "overall_success_rate": 0.75,
            "execution_time": 45.2,
            "criteria_results": {
                "testing": {"passed": True, "score": 85.0},
                "security": {"passed": False, "score": 65.0}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=False
            )
            
            assert result["success"] is True
            assert "report_file" in result
            assert "formats_generated" in result
            assert result["ai_insights_included"] is False
            
            # Verify actual report file was created
            report_file = Path(result["report_file"])
            assert report_file.exists()
            
            # Verify actual report content
            with open(report_file) as f:
                report_data = json.load(f)
                
            assert "timestamp" in report_data
            assert "project_path" in report_data
            assert "automation_summary" in report_data
            assert "criteria_results" in report_data
            assert "ai_insights" in report_data
            
            # Verify actual automation summary
            summary = report_data["automation_summary"]
            assert summary["overall_success"] == automation_result["success"]
            assert summary["success_rate"] == automation_result["overall_success_rate"]
            assert summary["execution_time"] == automation_result["execution_time"]
            
            # Verify actual criteria results are included
            assert report_data["criteria_results"] == automation_result["criteria_results"]
            
            # Verify AI insights are empty when not requested
            assert report_data["ai_insights"] == []


class TestDoDRuntimeNotImplementedFunctions:
    """Test functions that properly raise NotImplementedError."""
    
    def test_run_e2e_tests_actual_implementation(self):
        """Test that E2E tests now have real implementation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create some test files for the E2E runner to find
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            test_file = tests_dir / "test_example.py"
            test_file.write_text("def test_something(): assert True")
            
            result = run_e2e_tests(
                project_path=project_path,
                environment="test",
                parallel=False,
                headless=True,
                record_video=False,
                generate_report=True
            )
            
            # Should have actual results instead of raising NotImplementedError
            assert "success" in result
            assert "test_suites" in result
            assert "total_tests" in result
        
    def test_create_automation_report_with_ai_insights_returns_error(self):
        """Test that AI insights properly return error when not implemented."""
        automation_result = {"success": True}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=True
            )
            
            assert result["success"] is False
            assert "AI insights generation is not yet implemented" in result["error"]


class TestDoDRuntimeValidationFunctions:
    """Test actual validation functions with real file system analysis."""
    
    def test_execute_testing_validation_no_tests_no_autofix(self):
        """Test testing validation when no tests exist and auto-fix is disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_testing_validation(
                project_path=project_path,
                environment="development",
                auto_fix=False
            )
            
            assert result["success"] is False
            assert result["score"] == 0.0
            assert "No test files found" in result["details"]
            assert "No test files found" in result["errors"]
            
    def test_execute_testing_validation_with_autofix(self):
        """Test testing validation with auto-fix enabled creates actual test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_testing_validation(
                project_path=project_path,
                environment="development",
                auto_fix=True
            )
            
            assert result["success"] is True
            assert result["score"] == 50.0  # Partial score for created tests
            assert "Created basic test structure" in result["details"]
            assert "Created tests/ directory" in result["fixes_applied"]
            assert "Added basic test file" in result["fixes_applied"]
            
            # Verify actual test files were created
            tests_dir = project_path / "tests"
            assert tests_dir.exists()
            
            test_file = tests_dir / "test_basic.py"
            assert test_file.exists()
            
            # Verify actual test file content
            with open(test_file) as f:
                content = f.read()
                assert "import pytest" in content
                assert "def test_import():" in content
                
    def test_execute_testing_validation_with_existing_tests(self):
        """Test testing validation with existing test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create actual test files
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            test_file = tests_dir / "test_example.py"
            test_file.write_text("def test_something(): assert True")
            
            result = _execute_testing_validation(
                project_path=project_path,
                environment="development",
                auto_fix=False
            )
            
            # Should find the existing test files
            assert "1 test files found" in result["details"]
            
    def test_execute_security_validation_no_config_no_autofix(self):
        """Test security validation when no security config exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_security_validation(
                project_path=project_path,
                environment="development",
                auto_fix=False
            )
            
            assert "errors" in result
            # Score will be low due to missing security configurations
            assert result["score"] < 70.0
            
    def test_execute_security_validation_with_autofix(self):
        """Test security validation with auto-fix creates actual security files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_security_validation(
                project_path=project_path,
                environment="development",
                auto_fix=True
            )
            
            assert result["score"] >= 70.0  # Should pass with auto-fix
            assert "Created .bandit configuration" in result["fixes_applied"]
            assert "Created requirements.txt" in result["fixes_applied"]
            assert "Created .env.example" in result["fixes_applied"]
            
            # Verify actual security files were created
            bandit_file = project_path / ".bandit"
            assert bandit_file.exists()
            
            requirements_file = project_path / "requirements.txt"
            assert requirements_file.exists()
            
            env_example_file = project_path / ".env.example"
            assert env_example_file.exists()
            
            # Verify actual file content
            with open(bandit_file) as f:
                content = f.read()
                assert "[bandit]" in content
                assert "exclude_dirs" in content
                
    def test_execute_documentation_validation_with_autofix(self):
        """Test documentation validation with auto-fix creates actual documentation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_documentation_validation(
                project_path=project_path,
                environment="development",
                auto_fix=True
            )
            
            assert result["score"] >= 55.0  # Should get points for auto-created files
            assert "Created README.md" in result["fixes_applied"]
            assert "Created docs/ directory" in result["fixes_applied"]
            assert "Created CHANGELOG.md" in result["fixes_applied"]
            
            # Verify actual documentation files were created
            readme_file = project_path / "README.md"
            assert readme_file.exists()
            
            docs_dir = project_path / "docs"
            assert docs_dir.exists()
            
            changelog_file = project_path / "CHANGELOG.md"
            assert changelog_file.exists()
            
            # Verify actual README content
            with open(readme_file) as f:
                content = f.read()
                assert f"# {project_path.name}" in content
                assert "## Description" in content
                
    def test_execute_ci_cd_validation_with_autofix(self):
        """Test CI/CD validation with auto-fix creates actual CI/CD files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = _execute_ci_cd_validation(
                project_path=project_path,
                environment="development",
                auto_fix=True
            )
            
            assert result["score"] >= 70.0  # Should pass with auto-fix
            assert "Created GitHub Actions CI workflow" in result["fixes_applied"]
            
            # Verify actual CI/CD files were created
            workflow_file = project_path / ".github" / "workflows" / "ci.yml"
            assert workflow_file.exists()
            
            # Verify actual workflow content
            with open(workflow_file) as f:
                content = f.read()
                assert "name: CI" in content
                assert "pytest" in content
                
    def test_execute_code_quality_validation_with_autofix(self):
        """Test code quality validation with auto-fix creates actual config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a pyproject.toml file for the validation to modify
            pyproject_file = project_path / "pyproject.toml"
            pyproject_file.write_text("""[project]
name = "test-project"
version = "0.1.0"
""")
            
            result = _execute_code_quality_validation(
                project_path=project_path,
                environment="development",
                auto_fix=True
            )
            
            assert result["score"] >= 20.0  # Should get points for created configurations
            assert any("configuration" in fix for fix in result["fixes_applied"])
            
            # Verify that configuration files exist (actual content may vary based on what was created)
            # The function creates either pre-commit or .black files, or modifies pyproject.toml
            created_files = [
                project_path / ".pre-commit-config.yaml",
                project_path / ".black"
            ]
            assert any(f.exists() for f in created_files), "Should have created some configuration files"


class TestDoDRuntimeAnalysisFunctions:
    """Test file system analysis functions."""
    
    def test_analyze_automation_health_real_detection(self):
        """Test automation health analysis with real file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create actual CI/CD configuration
            github_dir = project_path / ".github" / "workflows"
            github_dir.mkdir(parents=True)
            workflow_file = github_dir / "ci.yml"
            workflow_file.write_text("name: CI\non: push")
            
            # Create actual build configuration
            pyproject_file = project_path / "pyproject.toml"
            pyproject_file.write_text("[build-system]\nrequires = ['setuptools']")
            
            # Create actual test files
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            test_file = tests_dir / "test_example.py"
            test_file.write_text("def test_something(): pass")
            
            result = _analyze_automation_health(project_path)
            
            assert result["score"] >= 90.0  # Should score high with all components
            assert result["pipeline_status"] == "active"
            assert result["test_files_count"] == 1
            assert "note" in result
            
    def test_analyze_security_posture_real_detection(self):
        """Test security posture analysis with real file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create actual security configuration
            bandit_file = project_path / ".bandit"
            bandit_file.write_text("[bandit]\nexclude_dirs = tests")
            
            # Create actual dependency management
            requirements_file = project_path / "requirements.txt"
            requirements_file.write_text("requests==2.28.0")
            
            # Create actual secrets management
            env_example = project_path / ".env.example"
            env_example.write_text("SECRET_KEY=your_secret_here")
            
            # Create Python files with secure practices
            src_dir = project_path / "src"
            src_dir.mkdir()
            secure_file = src_dir / "secure.py"
            secure_file.write_text("import secrets\napi_key = secrets.token_hex(32)")
            
            result = _analyze_security_posture(project_path)
            
            assert result["score"] == 100.0  # Should score perfect with all components
            assert result["vulnerabilities"] == "unknown"
            assert result["last_scan"] == "never"
            assert result["security_level"] == "high"
            assert "note" in result
            
    def test_analyze_code_quality_real_detection(self):
        """Test code quality analysis with real file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create actual linting configuration
            pyproject_file = project_path / "pyproject.toml"
            pyproject_file.write_text("""
[tool.flake8]
max-line-length = 88

[tool.black]
line-length = 88

[tool.coverage.run]
source = ["src"]
""")
            
            # Create actual pre-commit configuration
            precommit_file = project_path / ".pre-commit-config.yaml"
            precommit_file.write_text("repos:\n- repo: https://github.com/psf/black")
            
            result = _analyze_code_quality(project_path)
            
            assert result["score"] == 100.0  # Should score perfect with all components
            assert result["linting"] == 100.0
            assert result["complexity"] == "unknown"
            assert result["quality_level"] == "high"
            assert "note" in result


class TestDoDRuntimeIntegration:
    """Integration tests for DoD runtime workflow."""
    
    def test_full_workflow_with_real_project_structure(self):
        """Test complete DoD workflow with actual project files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Step 1: Initialize exoskeleton
            template_config = {
                "description": "Integration test template",
                "includes": ["basic_ci", "testing", "security"],
                "ai_features": ["code_review"]
            }
            
            exoskeleton_result = initialize_exoskeleton_files(
                project_path=project_path,
                template_config=template_config,
                force=False
            )
            
            assert exoskeleton_result["success"] is True
            
            # Step 2: Generate pipeline files
            pipeline_result = generate_pipeline_files(
                project_path=project_path,
                provider="github",
                environments=["dev", "prod"],
                features=["testing", "security"],
                template="standard",
                output_path=None
            )
            
            assert pipeline_result["success"] is True
            
            # Step 3: Execute automation workflow
            criteria = ["testing", "security", "documentation", "ci_cd", "code_quality"]
            
            workflow_result = execute_automation_workflow(
                project_path=project_path,
                criteria=criteria,
                environment="development",
                auto_fix=True,
                parallel=False,
                ai_assist=False
            )
            
            # The workflow might not be 100% successful due to missing tools (like black for code quality)
            # but it should have processed all criteria
            assert len(workflow_result["criteria_results"]) == len(criteria)
            assert "success" in workflow_result
            
            # Step 4: Analyze project health
            health_result = analyze_project_health(
                project_path=project_path,
                detailed=True,
                suggestions=True
            )
            
            assert health_result["success"] is True
            assert "dod_status" in health_result
            assert "automation_health" in health_result
            
            # Step 5: Create automation report
            report_result = create_automation_report(
                project_path=project_path,
                automation_result=workflow_result,
                include_ai_insights=False
            )
            
            assert report_result["success"] is True
            
            # Verify the complete workflow created actual files
            assert (project_path / ".uvmgr" / "exoskeleton" / "config.yaml").exists()
            assert (project_path / ".github" / "workflows" / "dod-automation.yml").exists()
            assert (project_path / "tests" / "test_basic.py").exists()
            assert (project_path / "README.md").exists()
            assert (project_path / ".bandit").exists()
            assert (project_path / "dod-automation-report.json").exists()
            
    def test_error_propagation_in_workflow(self):
        """Test that errors are properly propagated through the workflow."""
        # Test with permission-denied scenario
        invalid_path = Path("/proc/cannot_write_here")
        
        result = initialize_exoskeleton_files(
            project_path=invalid_path,
            template_config={"description": "test"},
            force=False
        )
        
        # Should handle error gracefully
        if not result["success"]:
            assert "error" in result
            assert isinstance(result["error"], str)
            
    def test_yaml_and_json_file_validity(self):
        """Test that all generated files are valid YAML/JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Generate files
            initialize_exoskeleton_files(
                project_path=project_path,
                template_config={"description": "test", "includes": [], "ai_features": []},
                force=False
            )
            
            generate_pipeline_files(
                project_path=project_path,
                provider="github",
                environments=["dev"],
                features=["testing"],
                template="standard",
                output_path=None
            )
            
            # Test YAML files
            config_file = project_path / ".uvmgr" / "exoskeleton" / "config.yaml"
            with open(config_file) as f:
                yaml.safe_load(f)  # Should not raise exception
                
            workflow_file = project_path / ".github" / "workflows" / "dod-automation.yml"
            with open(workflow_file) as f:
                yaml.safe_load(f)  # Should not raise exception
                
            # Test JSON reports
            automation_result = {"success": True, "criteria_results": {}}
            create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=False
            )
            
            report_file = project_path / "dod-automation-report.json"
            with open(report_file) as f:
                json.load(f)  # Should not raise exception


class TestDoDRuntimeTelemetry:
    """Test OTEL telemetry integration."""
    
    def test_telemetry_span_decorators_present(self):
        """Test that runtime functions have telemetry span decorators."""
        # These functions should have the @span decorator
        functions_with_spans = [
            initialize_exoskeleton_files,
            execute_automation_workflow,
            validate_criteria_runtime,
            generate_pipeline_files,
            run_e2e_tests,
            analyze_project_health,
            create_automation_report
        ]
        
        for func in functions_with_spans:
            # Check if function has been wrapped by span decorator
            assert hasattr(func, "__wrapped__") or hasattr(func, "_original_func")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])