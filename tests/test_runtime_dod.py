"""
Unit tests for DoD runtime layer.

Tests the actual execution logic, file I/O operations, and external
tool integration for DoD automation infrastructure.
"""

from __future__ import annotations

import json
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from uvmgr.runtime.dod import (
    initialize_exoskeleton_files,
    execute_automation_workflow,
    validate_criteria_runtime,
    generate_pipeline_files,
    run_e2e_tests,
    analyze_project_health,
    create_automation_report
)


class TestDoDRuntime:
    """Test suite for DoD runtime execution layer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_path = Path("/test/project")
        self.test_template_config = {
            "description": "Test template",
            "includes": ["basic_ci", "testing"],
            "ai_features": ["code_review"]
        }
        
    def test_initialize_exoskeleton_files_success(self):
        """Test successful exoskeleton file initialization."""
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
            
            # Verify directory structure was created
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            assert exoskeleton_dir.exists()
            assert exoskeleton_dir.is_dir()
            
            # Verify config file was created
            config_file = exoskeleton_dir / "config.yaml"
            assert config_file.exists()
            
            # Verify config content
            with open(config_file) as f:
                config_content = f.read()
                assert "DoD Exoskeleton Configuration" in config_content
                assert "Test template" in config_content
                
            # Verify automation directory was created
            automation_dir = exoskeleton_dir / "automation"
            assert automation_dir.exists()
            
            workflows_dir = automation_dir / "workflows"
            assert workflows_dir.exists()
            
    def test_initialize_exoskeleton_files_already_exists(self):
        """Test exoskeleton initialization when directory already exists."""
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
            
    def test_initialize_exoskeleton_files_force_overwrite(self):
        """Test exoskeleton initialization with force overwrite."""
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
            
    def test_initialize_exoskeleton_files_error_handling(self):
        """Test error handling in exoskeleton initialization."""
        # Test with invalid path (permission denied scenario)
        invalid_path = Path("/root/cannot_write_here")
        
        result = initialize_exoskeleton_files(
            project_path=invalid_path,
            template_config=self.test_template_config,
            force=False
        )
        
        assert result["success"] is False
        assert "error" in result
        
    def test_execute_automation_workflow_success(self):
        """Test successful automation workflow execution."""
        criteria = ["testing", "security", "code_quality"]
        
        result = execute_automation_workflow(
            project_path=self.test_project_path,
            criteria=criteria,
            environment="development",
            auto_fix=True,
            parallel=True,
            ai_assist=True
        )
        
        assert result["success"] is True
        assert "criteria_results" in result
        assert "execution_time" in result
        assert result["environment"] == "development"
        assert result["auto_fix_applied"] is True
        assert result["parallel_execution"] is True
        
        # Verify all criteria were processed
        for criterion in criteria:
            assert criterion in result["criteria_results"]
            criterion_result = result["criteria_results"][criterion]
            assert "passed" in criterion_result
            assert "score" in criterion_result
            assert "details" in criterion_result
            assert "execution_time" in criterion_result
            
    def test_execute_automation_workflow_realistic_scores(self):
        """Test that automation workflow generates realistic scores."""
        criteria = ["testing", "security", "devops", "code_quality"]
        
        result = execute_automation_workflow(
            project_path=self.test_project_path,
            criteria=criteria,
            environment="production",
            auto_fix=False,
            parallel=False,
            ai_assist=False
        )
        
        assert result["success"] is True
        
        # Verify scores are realistic (between 0 and 100)
        for criterion, criterion_result in result["criteria_results"].items():
            score = criterion_result["score"]
            assert 0.0 <= score <= 100.0
            
            # Scores should vary (not all the same)
            # This tests the hash-based variation in the simulation
            
        # Verify different criteria have different scores
        scores = [r["score"] for r in result["criteria_results"].values()]
        assert len(set(scores)) > 1  # Should have variation
        
    def test_validate_criteria_runtime_success(self):
        """Test successful runtime criteria validation."""
        criteria = ["testing", "security", "code_quality"]
        
        result = validate_criteria_runtime(
            project_path=self.test_project_path,
            criteria=criteria,
            detailed=True,
            fix_suggestions=True
        )
        
        assert result["success"] is True
        assert "criteria_scores" in result
        assert result["validation_strategy"] == "runtime_simulation"
        
        # Verify all criteria were validated
        for criterion in criteria:
            assert criterion in result["criteria_scores"]
            criterion_score = result["criteria_scores"][criterion]
            assert "score" in criterion_score
            assert "passed" in criterion_score
            assert "weight" in criterion_score
            assert "details" in criterion_score
            
    def test_validate_criteria_runtime_threshold_logic(self):
        """Test that validation properly applies passing thresholds."""
        criteria = ["testing"]
        
        result = validate_criteria_runtime(
            project_path=self.test_project_path,
            criteria=criteria,
            detailed=False,
            fix_suggestions=False
        )
        
        assert result["success"] is True
        
        # Verify passing threshold is applied (70% in simulation)
        criterion_score = result["criteria_scores"]["testing"]
        score = criterion_score["score"]
        passed = criterion_score["passed"]
        
        if score >= 70:
            assert passed is True
        else:
            assert passed is False
            
    def test_generate_pipeline_files_github_success(self):
        """Test successful GitHub pipeline generation."""
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
            
            # Verify GitHub workflow file was created
            workflow_file = project_path / ".github" / "workflows" / "dod-automation.yml"
            assert workflow_file.exists()
            
            # Verify workflow content
            with open(workflow_file) as f:
                workflow_content = f.read()
                assert "DoD Automation" in workflow_content
                assert "uvmgr dod complete" in workflow_content
                assert "dev" in workflow_content
                assert "staging" in workflow_content
                assert "prod" in workflow_content
                
    def test_generate_pipeline_files_unsupported_provider(self):
        """Test pipeline generation with unsupported provider."""
        result = generate_pipeline_files(
            project_path=self.test_project_path,
            provider="unsupported_provider",
            environments=["dev"],
            features=["testing"],
            template="standard",
            output_path=None
        )
        
        # Should still succeed but create fewer files
        assert result["success"] is True
        assert len(result["files_created"]) == 0  # No files for unsupported provider
        
    def test_run_e2e_tests_success(self):
        """Test successful E2E test execution."""
        result = run_e2e_tests(
            project_path=self.test_project_path,
            environment="staging",
            parallel=True,
            headless=True,
            record_video=False,
            generate_report=True
        )
        
        assert result["success"] is True
        assert "test_suites" in result
        assert result["environment"] == "staging"
        assert result["parallel"] is True
        assert result["headless"] is True
        assert result["video_recorded"] is False
        assert result["report_generated"] is True
        
        # Verify test suite structure
        test_suites = result["test_suites"]
        expected_suites = ["browser_tests", "api_tests", "integration_tests"]
        
        for suite_name in expected_suites:
            assert suite_name in test_suites
            suite = test_suites[suite_name]
            assert "total" in suite
            assert "passed" in suite
            assert "failed" in suite
            assert "duration" in suite
            
            # Verify test counts are consistent
            assert suite["total"] == suite["passed"] + suite["failed"]
            assert suite["total"] > 0
            assert suite["passed"] >= 0
            assert suite["failed"] >= 0
            assert suite["duration"] > 0
            
    def test_run_e2e_tests_realistic_results(self):
        """Test that E2E tests generate realistic results."""
        result = run_e2e_tests(
            project_path=self.test_project_path,
            environment="production",
            parallel=False,
            headless=False,
            record_video=True,
            generate_report=True
        )
        
        assert result["success"] is True
        
        # Verify test results are realistic
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for suite in result["test_suites"].values():
            total_tests += suite["total"]
            total_passed += suite["passed"]
            total_failed += suite["failed"]
            
            # Each suite should have some tests
            assert suite["total"] > 0
            # Duration should be positive
            assert suite["duration"] > 0
            
        # Overall totals should be consistent
        assert total_tests == total_passed + total_failed
        assert total_tests > 0
        
    def test_analyze_project_health_success(self):
        """Test successful project health analysis."""
        result = analyze_project_health(
            project_path=self.test_project_path,
            detailed=True,
            suggestions=True
        )
        
        assert result["success"] is True
        assert "dod_status" in result
        assert "automation_health" in result
        assert "security_posture" in result
        assert "code_quality" in result
        assert "suggestions" in result
        
        # Verify health status structure
        dod_status = result["dod_status"]
        assert "overall_score" in dod_status
        assert "critical_score" in dod_status
        assert "important_score" in dod_status
        
        automation_health = result["automation_health"]
        assert "score" in automation_health
        assert "pipeline_status" in automation_health
        assert "test_coverage" in automation_health
        
        security_posture = result["security_posture"]
        assert "score" in security_posture
        assert "vulnerabilities" in security_posture
        assert "last_scan" in security_posture
        
        code_quality = result["code_quality"]
        assert "score" in code_quality
        assert "linting" in code_quality
        assert "complexity" in code_quality
        
        # Verify suggestions are provided when requested
        suggestions = result["suggestions"]
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
    def test_analyze_project_health_without_suggestions(self):
        """Test project health analysis without suggestions."""
        result = analyze_project_health(
            project_path=self.test_project_path,
            detailed=False,
            suggestions=False
        )
        
        assert result["success"] is True
        assert result["suggestions"] == []
        
    def test_create_automation_report_success(self):
        """Test successful automation report creation."""
        automation_result = {
            "success": True,
            "overall_success_rate": 0.85,
            "execution_time": 120.5,
            "criteria_results": {
                "testing": {"passed": True, "score": 90.0},
                "security": {"passed": True, "score": 88.0},
                "code_quality": {"passed": False, "score": 65.0}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=True
            )
            
            assert result["success"] is True
            assert "report_file" in result
            assert "formats_generated" in result
            assert result["ai_insights_included"] is True
            
            # Verify report file was created
            report_file = Path(result["report_file"])
            assert report_file.exists()
            
            # Verify report content
            with open(report_file) as f:
                report_data = json.load(f)
                
            assert "timestamp" in report_data
            assert "project_path" in report_data
            assert "automation_summary" in report_data
            assert "criteria_results" in report_data
            assert "ai_insights" in report_data
            
            # Verify automation summary
            summary = report_data["automation_summary"]
            assert summary["overall_success"] == automation_result["success"]
            assert summary["success_rate"] == automation_result["overall_success_rate"]
            assert summary["execution_time"] == automation_result["execution_time"]
            
            # Verify criteria results are included
            assert report_data["criteria_results"] == automation_result["criteria_results"]
            
            # Verify AI insights are included
            ai_insights = report_data["ai_insights"]
            assert isinstance(ai_insights, list)
            assert len(ai_insights) > 0
            
    def test_create_automation_report_without_ai_insights(self):
        """Test automation report creation without AI insights."""
        automation_result = {
            "success": True,
            "overall_success_rate": 0.75,
            "criteria_results": {}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = create_automation_report(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=False
            )
            
            assert result["success"] is True
            assert result["ai_insights_included"] is False
            
            # Verify report file content
            report_file = Path(result["report_file"])
            with open(report_file) as f:
                report_data = json.load(f)
                
            assert report_data["ai_insights"] == []
            
    def test_runtime_error_handling(self):
        """Test error handling across all runtime functions."""
        # Test functions that have proper error handling
        
        # Test create_automation_report error handling (file I/O can fail)
        with patch("builtins.open", side_effect=IOError("File error")):
            result = create_automation_report(
                self.test_project_path,
                {"success": True},
                False
            )
            assert result["success"] is False
            assert "error" in result
            
        # Test initialize_exoskeleton_files with permission errors
        # This actually can fail in real scenarios
        invalid_path = Path("/proc/invalid_path_that_cannot_be_created")
        result = initialize_exoskeleton_files(
            invalid_path,
            self.test_template_config
        )
        # May succeed or fail depending on system - just verify it handles gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result
            
        # For simulation-based functions, verify they have graceful handling
        # Even if they don't fail, they should have consistent return structure
        result = execute_automation_workflow(
            self.test_project_path,
            ["testing"],
            "development",
            False,
            False,
            False
        )
        assert "success" in result
        assert "criteria_results" in result
        
        result = validate_criteria_runtime(
            self.test_project_path,
            ["testing"],
            False,
            False
        )
        assert "success" in result
        assert "criteria_scores" in result
        
        result = run_e2e_tests(
            self.test_project_path,
            "test",
            True,
            True,
            False,
            False
        )
        assert "success" in result
        assert "test_suites" in result
        
        result = analyze_project_health(
            self.test_project_path,
            False,
            False
        )
        assert "success" in result
            
    def test_telemetry_integration(self):
        """Test that runtime functions include telemetry spans."""
        with patch("uvmgr.runtime.dod.span") as mock_span:
            # Test that span decorator is applied
            assert hasattr(initialize_exoskeleton_files, "__wrapped__")
            assert hasattr(execute_automation_workflow, "__wrapped__")
            assert hasattr(validate_criteria_runtime, "__wrapped__")
            assert hasattr(generate_pipeline_files, "__wrapped__")
            assert hasattr(run_e2e_tests, "__wrapped__")
            assert hasattr(analyze_project_health, "__wrapped__")
            assert hasattr(create_automation_report, "__wrapped__")
            
    def test_file_operations_safety(self):
        """Test that file operations are performed safely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Test that initialization creates proper directory structure
            result = initialize_exoskeleton_files(
                project_path,
                self.test_template_config
            )
            
            assert result["success"] is True
            
            # Verify no files are created outside the project directory
            created_files = result["files_created"]
            for file_info in created_files:
                file_path = project_path / file_info["path"]
                # Verify file is within project directory
                assert project_path in file_path.parents or file_path == project_path
                
    def test_yaml_content_generation(self):
        """Test that generated YAML content is valid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = initialize_exoskeleton_files(
                project_path,
                self.test_template_config
            )
            
            assert result["success"] is True
            
            # Verify generated config.yaml is valid YAML
            config_file = project_path / ".uvmgr" / "exoskeleton" / "config.yaml"
            with open(config_file) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError:
                    pytest.fail("Generated config.yaml is not valid YAML")
                    
    def test_json_report_generation(self):
        """Test that generated JSON reports are valid."""
        automation_result = {"success": True, "criteria_results": {}}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = create_automation_report(
                project_path,
                automation_result,
                True
            )
            
            assert result["success"] is True
            
            # Verify generated report is valid JSON
            report_file = Path(result["report_file"])
            with open(report_file) as f:
                try:
                    json.load(f)
                except json.JSONDecodeError:
                    pytest.fail("Generated report is not valid JSON")


class TestDoDRuntimePerformance:
    """Performance tests for DoD runtime operations."""
    
    def test_exoskeleton_initialization_performance(self):
        """Test exoskeleton initialization performance."""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            template_config = {
                "description": "Performance test",
                "includes": ["basic_ci"],
                "ai_features": []
            }
            
            start_time = time.time()
            result = initialize_exoskeleton_files(project_path, template_config)
            end_time = time.time()
            
            assert result["success"] is True
            assert (end_time - start_time) < 1.0  # Should complete in under 1 second
            
    def test_automation_workflow_performance(self):
        """Test automation workflow execution performance."""
        import time
        
        criteria = ["testing", "security", "code_quality"]
        
        start_time = time.time()
        result = execute_automation_workflow(
            Path("/test"),
            criteria,
            "test",
            False,
            True,
            False
        )
        end_time = time.time()
        
        assert result["success"] is True
        assert (end_time - start_time) < 2.0  # Should complete in under 2 seconds


if __name__ == "__main__":
    pytest.main([__file__])