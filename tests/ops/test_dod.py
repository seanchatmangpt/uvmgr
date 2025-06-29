"""
Unit tests for DoD (Definition of Done) operations module.
Tests all business logic functions for complete automation functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from uvmgr.ops.dod import (
    create_exoskeleton,
    execute_complete_automation,
    validate_dod_criteria,
    generate_devops_pipeline,
    run_e2e_automation,
    analyze_project_status,
    generate_dod_report,
    DOD_CRITERIA_WEIGHTS,
    EXOSKELETON_TEMPLATES,
    _calculate_weighted_success_rate,
    _generate_exoskeleton_structure
)


class TestCreateExoskeleton:
    """Test exoskeleton creation functionality."""
    
    def test_create_exoskeleton_standard_template(self):
        """Test creating standard exoskeleton template."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {
                "success": True,
                "files_created": [
                    {"path": ".uvmgr/dod.yaml", "size": 1024},
                    {"path": ".github/workflows/dod-automation.yml", "size": 2048}
                ],
                "workflows_created": ["dod-validation", "continuous-integration"],
                "ai_integrations": ["code-review", "test-generation"]
            }
            
            result = create_exoskeleton(project_path, template="standard")
            
            assert result["success"] is True
            assert len(result["files_created"]) == 2
            assert len(result["workflows_created"]) == 2
            assert len(result["ai_integrations"]) == 2
            
            # Verify runtime layer was called correctly
            mock_init.assert_called_once_with(
                project_path=project_path,
                template_config=EXOSKELETON_TEMPLATES["standard"],
                force=False
            )
    
    def test_create_exoskeleton_enterprise_template(self):
        """Test creating enterprise exoskeleton template."""
        project_path = Path("/test/enterprise-project")
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.return_value = {
                "success": True,
                "files_created": [
                    {"path": ".uvmgr/dod.yaml", "size": 1024},
                    {"path": ".uvmgr/governance/policies.yaml", "size": 512},
                    {"path": ".github/workflows/enterprise-dod.yml", "size": 3072}
                ],
                "workflows_created": ["dod-validation", "compliance-check", "security-scan"],
                "ai_integrations": ["architecture-analysis", "security-advisory"]
            }
            
            result = create_exoskeleton(project_path, template="enterprise", force=True)
            
            assert result["success"] is True
            assert len(result["files_created"]) == 3
            assert len(result["workflows_created"]) == 3
            
            mock_init.assert_called_once_with(
                project_path=project_path,
                template_config=EXOSKELETON_TEMPLATES["enterprise"],
                force=True
            )
    
    def test_create_exoskeleton_preview_mode(self):
        """Test exoskeleton preview without creating files."""
        project_path = Path("/test/preview-project")
        
        result = create_exoskeleton(project_path, template="ai-native", preview=True)
        
        assert result["success"] is True
        assert result["preview"] is True
        assert result["template"] == "ai-native"
        assert "structure" in result
        assert "description" in result
        assert result["description"] == EXOSKELETON_TEMPLATES["ai-native"]["description"]
    
    def test_create_exoskeleton_invalid_template(self):
        """Test handling of invalid template."""
        project_path = Path("/test/project")
        
        result = create_exoskeleton(project_path, template="invalid-template")
        
        assert result["success"] is False
        assert "Unknown template" in result["error"]
        assert "invalid-template" in result["error"]
    
    def test_create_exoskeleton_runtime_failure(self):
        """Test handling of runtime layer failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            mock_init.side_effect = Exception("Runtime error")
            
            result = create_exoskeleton(project_path)
            
            assert result["success"] is False
            assert "Failed to create exoskeleton" in result["error"]
            assert "Runtime error" in result["error"]


class TestExecuteCompleteAutomation:
    """Test complete automation execution."""
    
    def test_execute_complete_automation_success(self):
        """Test successful complete automation execution."""
        project_path = Path("/test/project")
        
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0},
                "code_quality": {"passed": False, "score": 75.0}
            }
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.return_value = mock_automation_result
            
            result = execute_complete_automation(
                project_path=project_path,
                environment="production",
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
            
            assert result["success"] is True
            assert "overall_success_rate" in result
            assert "execution_time" in result
            assert result["criteria_executed"] == list(DOD_CRITERIA_WEIGHTS.keys())
            assert result["automation_strategy"] == "80/20"
            
            # Verify runtime layer was called correctly
            mock_execute.assert_called_once_with(
                project_path=project_path,
                criteria=list(DOD_CRITERIA_WEIGHTS.keys()),
                environment="production",
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
    
    def test_execute_complete_automation_skip_criteria(self):
        """Test automation with skipped criteria."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            
            result = execute_complete_automation(
                project_path=project_path,
                skip_tests=True,
                skip_security=True
            )
            
            # Verify that testing and security were removed from criteria
            called_criteria = mock_execute.call_args[1]["criteria"]
            assert "testing" not in called_criteria
            assert "security" not in called_criteria
            assert "devops" in called_criteria
            assert "code_quality" in called_criteria
    
    def test_execute_complete_automation_custom_criteria(self):
        """Test automation with custom criteria list."""
        project_path = Path("/test/project")
        custom_criteria = ["testing", "security"]
        
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            
            result = execute_complete_automation(
                project_path=project_path,
                criteria=custom_criteria
            )
            
            called_criteria = mock_execute.call_args[1]["criteria"]
            assert called_criteria == custom_criteria
    
    def test_execute_complete_automation_failure(self):
        """Test handling of automation execution failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.side_effect = Exception("Automation failed")
            
            result = execute_complete_automation(project_path)
            
            assert result["success"] is False
            assert "Automation execution failed" in result["error"]
            assert "execution_time" in result


class TestValidateDodCriteria:
    """Test DoD criteria validation functionality."""
    
    def test_validate_dod_criteria_all_passed(self):
        """Test validation when all criteria pass."""
        project_path = Path("/test/project")
        
        mock_validation_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0}
            }
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            mock_validate.return_value = mock_validation_result
            
            result = validate_dod_criteria(
                project_path=project_path,
                criteria=["testing", "security", "devops"],
                detailed=True,
                fix_suggestions=True
            )
            
            assert result["success"] is True
            assert "overall_score" in result
            assert "critical_score" in result
            assert "important_score" in result
            assert result["scoring_strategy"] == "80/20 weighted"
            assert "criteria_weights" in result
            
            # Verify runtime layer was called correctly
            mock_validate.assert_called_once_with(
                project_path=project_path,
                criteria=["testing", "security", "devops"],
                detailed=True,
                fix_suggestions=True
            )
    
    def test_validate_dod_criteria_default_all(self):
        """Test validation with default criteria (all)."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            mock_validate.return_value = {"success": True, "criteria_scores": {}}
            
            result = validate_dod_criteria(project_path)
            
            # Should validate all criteria when none specified
            called_criteria = mock_validate.call_args[1]["criteria"]
            assert called_criteria == list(DOD_CRITERIA_WEIGHTS.keys())
    
    def test_validate_dod_criteria_mixed_results(self):
        """Test validation with mixed pass/fail results."""
        project_path = Path("/test/project")
        
        mock_validation_result = {
            "success": False,
            "criteria_scores": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": False, "score": 65.0},
                "code_quality": {"passed": True, "score": 85.0}
            }
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            mock_validate.return_value = mock_validation_result
            
            result = validate_dod_criteria(project_path, criteria=["testing", "security", "code_quality"])
            
            # Should calculate weighted scores properly
            assert "overall_score" in result
            assert "critical_score" in result
            assert "important_score" in result
            
            # Critical score should be affected by security failure
            critical_scores = [95.0, 65.0]  # testing and security
            expected_critical = sum(critical_scores) / len(critical_scores)
            assert result["critical_score"] == expected_critical
    
    def test_validate_dod_criteria_runtime_failure(self):
        """Test handling of runtime validation failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
            mock_validate.side_effect = Exception("Validation error")
            
            result = validate_dod_criteria(project_path)
            
            assert result["success"] is False
            assert "Validation failed" in result["error"]
            assert result["overall_score"] == 0.0


class TestGenerateDevopsPipeline:
    """Test DevOps pipeline generation."""
    
    def test_generate_devops_pipeline_github_actions(self):
        """Test generating GitHub Actions pipeline."""
        project_path = Path("/test/project")
        
        mock_pipeline_result = {
            "success": True,
            "files_created": [
                ".github/workflows/dod-automation.yml",
                ".github/workflows/deployment.yml"
            ],
            "features_enabled": ["testing", "security", "deployment"],
            "environments_configured": ["dev", "staging", "production"]
        }
        
        with patch("uvmgr.ops.dod.generate_pipeline_files") as mock_generate:
            mock_generate.return_value = mock_pipeline_result
            
            result = generate_devops_pipeline(
                project_path=project_path,
                provider="github-actions",
                environments=["dev", "staging", "production"],
                features=["testing", "security", "deployment"],
                template="enterprise"
            )
            
            assert result["success"] is True
            assert len(result["files_created"]) == 2
            assert len(result["features_enabled"]) == 3
            
            # Verify runtime layer was called correctly
            mock_generate.assert_called_once_with(
                project_path=project_path,
                provider="github-actions",
                environments=["dev", "staging", "production"],
                features=["testing", "security", "deployment"],
                template="enterprise",
                output_path=None
            )
    
    def test_generate_devops_pipeline_defaults(self):
        """Test pipeline generation with default values."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.generate_pipeline_files") as mock_generate:
            mock_generate.return_value = {"success": True}
            
            result = generate_devops_pipeline(project_path)
            
            # Verify defaults were applied
            call_args = mock_generate.call_args[1]
            assert call_args["environments"] == ["dev", "staging", "production"]
            assert call_args["features"] == ["testing", "security", "deployment", "monitoring"]
            assert call_args["provider"] == "github-actions"
    
    def test_generate_devops_pipeline_custom_output_path(self):
        """Test pipeline generation with custom output path."""
        project_path = Path("/test/project")
        output_path = Path("/custom/output")
        
        with patch("uvmgr.ops.dod.generate_pipeline_files") as mock_generate:
            mock_generate.return_value = {"success": True}
            
            result = generate_devops_pipeline(project_path, output_path=output_path)
            
            call_args = mock_generate.call_args[1]
            assert call_args["output_path"] == output_path
    
    def test_generate_devops_pipeline_failure(self):
        """Test handling of pipeline generation failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.generate_pipeline_files") as mock_generate:
            mock_generate.side_effect = Exception("Pipeline generation error")
            
            result = generate_devops_pipeline(project_path)
            
            assert result["success"] is False
            assert "Pipeline generation failed" in result["error"]


class TestRunE2EAutomation:
    """Test end-to-end automation testing."""
    
    def test_run_e2e_automation_success(self):
        """Test successful E2E automation execution."""
        project_path = Path("/test/project")
        
        mock_e2e_result = {
            "success": True,
            "test_suites": {
                "browser_tests": {"total": 20, "passed": 18, "failed": 2},
                "api_tests": {"total": 15, "passed": 15, "failed": 0},
                "mobile_tests": {"total": 10, "passed": 9, "failed": 1},
                "performance_tests": {"total": 5, "passed": 5, "failed": 0}
            }
        }
        
        with patch("uvmgr.ops.dod.run_e2e_tests") as mock_run_tests:
            mock_run_tests.return_value = mock_e2e_result
            
            result = run_e2e_automation(
                project_path=project_path,
                environment="staging",
                parallel=True,
                headless=True,
                record_video=True,
                generate_report=True
            )
            
            assert result["success"] is True
            assert "success_rate" in result
            assert "total_tests" in result
            assert "passed_tests" in result
            assert "execution_time" in result
            
            # Calculate expected values
            total_tests = 20 + 15 + 10 + 5  # 50
            passed_tests = 18 + 15 + 9 + 5  # 47
            expected_success_rate = passed_tests / total_tests
            
            assert result["total_tests"] == total_tests
            assert result["passed_tests"] == passed_tests
            assert result["success_rate"] == expected_success_rate
            
            # Verify runtime layer was called correctly
            mock_run_tests.assert_called_once_with(
                project_path=project_path,
                environment="staging",
                parallel=True,
                headless=True,
                record_video=True,
                generate_report=True
            )
    
    def test_run_e2e_automation_defaults(self):
        """Test E2E automation with default parameters."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.run_e2e_tests") as mock_run_tests:
            mock_run_tests.return_value = {"success": True, "test_suites": {}}
            
            result = run_e2e_automation(project_path)
            
            # Verify defaults were applied
            call_args = mock_run_tests.call_args[1]
            assert call_args["environment"] == "development"
            assert call_args["parallel"] is True
            assert call_args["headless"] is True
            assert call_args["record_video"] is False
            assert call_args["generate_report"] is True
    
    def test_run_e2e_automation_no_tests(self):
        """Test E2E automation with no tests."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.run_e2e_tests") as mock_run_tests:
            mock_run_tests.return_value = {"success": True, "test_suites": {}}
            
            result = run_e2e_automation(project_path)
            
            assert result["total_tests"] == 0
            assert result["passed_tests"] == 0
            assert result["success_rate"] == 0.0
    
    def test_run_e2e_automation_failure(self):
        """Test handling of E2E automation failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.run_e2e_tests") as mock_run_tests:
            mock_run_tests.side_effect = Exception("E2E test error")
            
            result = run_e2e_automation(project_path)
            
            assert result["success"] is False
            assert "E2E testing failed" in result["error"]
            assert result["success_rate"] == 0.0
            assert "execution_time" in result


class TestAnalyzeProjectStatus:
    """Test project status analysis."""
    
    def test_analyze_project_status_healthy_project(self):
        """Test analysis of a healthy project."""
        project_path = Path("/test/healthy-project")
        
        mock_status_result = {
            "success": True,
            "dod_status": {"overall_score": 90.0},
            "automation_health": {"score": 85.0},
            "security_posture": {"score": 88.0},
            "code_quality": {"score": 92.0}
        }
        
        with patch("uvmgr.ops.dod.analyze_project_health") as mock_analyze:
            mock_analyze.return_value = mock_status_result
            
            result = analyze_project_status(
                project_path=project_path,
                detailed=True,
                suggestions=True
            )
            
            assert result["success"] is True
            assert "health_score" in result
            assert "health_components" in result
            assert result["scoring_strategy"] == "80/20 weighted health"
            
            # Calculate expected health score using 80/20 weights
            expected_health = (
                90.0 * 0.40 +  # dod_compliance
                85.0 * 0.30 +  # automation_health  
                88.0 * 0.20 +  # security_posture
                92.0 * 0.10    # code_quality
            )
            
            assert result["health_score"] == expected_health
    
    def test_analyze_project_status_problematic_project(self):
        """Test analysis of a project with issues."""
        project_path = Path("/test/problematic-project")
        
        mock_status_result = {
            "success": False,
            "dod_status": {"overall_score": 45.0},
            "automation_health": {"score": 30.0},
            "security_posture": {"score": 55.0},
            "code_quality": {"score": 40.0}
        }
        
        with patch("uvmgr.ops.dod.analyze_project_health") as mock_analyze:
            mock_analyze.return_value = mock_status_result
            
            result = analyze_project_status(project_path)
            
            # Should still succeed even if project has issues
            assert "health_score" in result
            
            # Health score should be low
            expected_health = (
                45.0 * 0.40 +  # dod_compliance
                30.0 * 0.30 +  # automation_health
                55.0 * 0.20 +  # security_posture
                40.0 * 0.10    # code_quality
            )
            
            assert result["health_score"] == expected_health
            assert result["health_score"] < 50.0
    
    def test_analyze_project_status_minimal_analysis(self):
        """Test status analysis with minimal options."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.analyze_project_health") as mock_analyze:
            mock_analyze.return_value = {
                "dod_status": {"overall_score": 75.0},
                "automation_health": {"score": 70.0},
                "security_posture": {"score": 80.0},
                "code_quality": {"score": 85.0}
            }
            
            result = analyze_project_status(
                project_path=project_path,
                detailed=False,
                suggestions=False
            )
            
            # Verify runtime layer was called correctly
            mock_analyze.assert_called_once_with(
                project_path=project_path,
                detailed=False,
                suggestions=False
            )
    
    def test_analyze_project_status_failure(self):
        """Test handling of status analysis failure."""
        project_path = Path("/test/project")
        
        with patch("uvmgr.ops.dod.analyze_project_health") as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis error")
            
            result = analyze_project_status(project_path)
            
            assert result["success"] is False
            assert "Status analysis failed" in result["error"]
            assert result["health_score"] == 0.0


class TestGenerateDodReport:
    """Test DoD report generation."""
    
    def test_generate_dod_report_success(self):
        """Test successful report generation."""
        project_path = Path("/test/project")
        automation_result = {
            "overall_success_rate": 85.5,
            "criteria_results": {
                "testing": {"passed": True, "score": 90.0},
                "security": {"passed": True, "score": 88.0}
            }
        }
        
        mock_report_result = {
            "success": True,
            "formats_generated": ["json", "markdown", "pdf"],
            "report_path": "/test/project/reports/dod-report.json"
        }
        
        with patch("uvmgr.ops.dod.create_automation_report") as mock_create_report:
            mock_create_report.return_value = mock_report_result
            
            result = generate_dod_report(project_path, automation_result)
            
            assert result["success"] is True
            assert len(result["formats_generated"]) == 3
            
            # Verify runtime layer was called correctly
            mock_create_report.assert_called_once_with(
                project_path=project_path,
                automation_result=automation_result,
                include_ai_insights=True
            )
    
    def test_generate_dod_report_failure(self):
        """Test handling of report generation failure."""
        project_path = Path("/test/project")
        automation_result = {"overall_success_rate": 0.0}
        
        with patch("uvmgr.ops.dod.create_automation_report") as mock_create_report:
            mock_create_report.side_effect = Exception("Report generation error")
            
            result = generate_dod_report(project_path, automation_result)
            
            assert result["success"] is False
            assert "Report generation failed" in result["error"]


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_calculate_weighted_success_rate_all_passed(self):
        """Test weighted success rate calculation with all criteria passed."""
        criteria_results = {
            "testing": {"passed": True, "score": 95.0},
            "security": {"passed": True, "score": 88.0},
            "devops": {"passed": True, "score": 92.0},
            "code_quality": {"passed": True, "score": 85.0}
        }
        criteria = ["testing", "security", "devops", "code_quality"]
        
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # The function prioritizes boolean 'passed' over 'score' values
        # When 'passed' is present, it converts True to 1.0, False to 0.0
        # So all passed criteria should result in success_rate = 1.0
        assert success_rate == 1.0
    
    def test_calculate_weighted_success_rate_score_only(self):
        """Test weighted success rate calculation with scores only (no passed field)."""
        criteria_results = {
            "testing": {"score": 95.0},
            "security": {"score": 88.0},
            "devops": {"score": 92.0},
            "code_quality": {"score": 85.0}
        }
        criteria = ["testing", "security", "devops", "code_quality"]
        
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Calculate expected weighted average using actual scores
        total_weight = (
            DOD_CRITERIA_WEIGHTS["testing"]["weight"] +
            DOD_CRITERIA_WEIGHTS["security"]["weight"] +
            DOD_CRITERIA_WEIGHTS["devops"]["weight"] +
            DOD_CRITERIA_WEIGHTS["code_quality"]["weight"]
        )
        
        expected_rate = (
            95.0 * DOD_CRITERIA_WEIGHTS["testing"]["weight"] +
            88.0 * DOD_CRITERIA_WEIGHTS["security"]["weight"] +
            92.0 * DOD_CRITERIA_WEIGHTS["devops"]["weight"] +
            85.0 * DOD_CRITERIA_WEIGHTS["code_quality"]["weight"]
        ) / total_weight
        
        assert success_rate == expected_rate
    
    def test_calculate_weighted_success_rate_boolean_scores(self):
        """Test weighted success rate with boolean scores."""
        criteria_results = {
            "testing": {"passed": True},
            "security": {"passed": False}
        }
        criteria = ["testing", "security"]
        
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Boolean true should be 1.0, false should be 0.0
        total_weight = (
            DOD_CRITERIA_WEIGHTS["testing"]["weight"] +
            DOD_CRITERIA_WEIGHTS["security"]["weight"]
        )
        
        expected_rate = (
            1.0 * DOD_CRITERIA_WEIGHTS["testing"]["weight"] +
            0.0 * DOD_CRITERIA_WEIGHTS["security"]["weight"]
        ) / total_weight
        
        assert success_rate == expected_rate
    
    def test_calculate_weighted_success_rate_empty_results(self):
        """Test weighted success rate with empty results."""
        success_rate = _calculate_weighted_success_rate({}, [])
        assert success_rate == 0.0
        
        success_rate = _calculate_weighted_success_rate({}, ["testing"])
        assert success_rate == 0.0
    
    def test_calculate_weighted_success_rate_missing_criteria(self):
        """Test weighted success rate with missing criteria."""
        criteria_results = {
            "testing": {"score": 95.0}
        }
        criteria = ["testing", "nonexistent"]
        
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Should only count testing criteria
        expected_rate = 95.0 * DOD_CRITERIA_WEIGHTS["testing"]["weight"] / DOD_CRITERIA_WEIGHTS["testing"]["weight"]
        assert success_rate == expected_rate
    
    def test_generate_exoskeleton_structure_standard(self):
        """Test exoskeleton structure generation for standard template."""
        template_config = EXOSKELETON_TEMPLATES["standard"]
        
        structure = _generate_exoskeleton_structure(template_config)
        
        assert "automation" in structure
        assert "ci_cd" in structure
        assert "testing" in structure
        assert "security" in structure
        assert "monitoring" in structure
        
        # Should not have governance for standard template
        assert "governance" not in structure
    
    def test_generate_exoskeleton_structure_enterprise(self):
        """Test exoskeleton structure generation for enterprise template."""
        template_config = EXOSKELETON_TEMPLATES["enterprise"]
        
        structure = _generate_exoskeleton_structure(template_config)
        
        assert "automation" in structure
        assert "governance" in structure  # Enterprise has "compliance" in includes
        assert "ai_integration" in structure  # Enterprise has AI features
    
    def test_generate_exoskeleton_structure_ai_native(self):
        """Test exoskeleton structure generation for AI-native template."""
        template_config = EXOSKELETON_TEMPLATES["ai-native"]
        
        structure = _generate_exoskeleton_structure(template_config)
        
        assert "automation" in structure
        assert "ai_integration" in structure  # AI-native should have AI integration


class TestDodConstants:
    """Test DoD constants and configuration."""
    
    def test_dod_criteria_weights_structure(self):
        """Test that DoD criteria weights are properly structured."""
        assert isinstance(DOD_CRITERIA_WEIGHTS, dict)
        
        # Check that all criteria have required fields
        for criteria_name, criteria_config in DOD_CRITERIA_WEIGHTS.items():
            assert "weight" in criteria_config
            assert "priority" in criteria_config
            assert isinstance(criteria_config["weight"], float)
            assert criteria_config["priority"] in ["critical", "important", "optional"]
        
        # Check that weights sum to approximately 1.0
        total_weight = sum(config["weight"] for config in DOD_CRITERIA_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow for small floating point differences
    
    def test_dod_criteria_weights_80_20_principle(self):
        """Test that weights follow 80/20 principle."""
        critical_weight = sum(
            config["weight"]
            for config in DOD_CRITERIA_WEIGHTS.values()
            if config["priority"] == "critical"
        )
        
        important_weight = sum(
            config["weight"]
            for config in DOD_CRITERIA_WEIGHTS.values()
            if config["priority"] == "important"
        )
        
        optional_weight = sum(
            config["weight"]
            for config in DOD_CRITERIA_WEIGHTS.values()
            if config["priority"] == "optional"
        )
        
        # Critical criteria should have majority of weight (80/20 principle)
        assert critical_weight >= 0.60  # At least 60% weight
        assert critical_weight + important_weight >= 0.89  # Critical + Important >= 89% (allow for floating point)
        assert optional_weight <= 0.20  # Optional <= 20%
    
    def test_exoskeleton_templates_structure(self):
        """Test that exoskeleton templates are properly structured."""
        assert isinstance(EXOSKELETON_TEMPLATES, dict)
        
        required_templates = ["standard", "enterprise", "ai-native"]
        for template_name in required_templates:
            assert template_name in EXOSKELETON_TEMPLATES
            
            template = EXOSKELETON_TEMPLATES[template_name]
            assert "description" in template
            assert "includes" in template
            assert "ai_features" in template
            
            assert isinstance(template["description"], str)
            assert isinstance(template["includes"], list)
            assert isinstance(template["ai_features"], list)


@pytest.fixture
def sample_project_path():
    """Fixture providing a sample project path."""
    return Path("/test/sample-project")


@pytest.fixture
def sample_criteria_results():
    """Fixture providing sample criteria results."""
    return {
        "testing": {"passed": True, "score": 95.0, "details": "All tests passing"},
        "security": {"passed": True, "score": 88.0, "details": "No critical vulnerabilities"},
        "devops": {"passed": False, "score": 65.0, "details": "Pipeline optimization needed"},
        "code_quality": {"passed": True, "score": 85.0, "details": "Good code quality"}
    }


@pytest.fixture
def sample_automation_result():
    """Fixture providing sample automation result."""
    return {
        "success": True,
        "overall_success_rate": 83.25,
        "criteria_results": {
            "testing": {"passed": True, "score": 95.0},
            "security": {"passed": True, "score": 88.0},
            "devops": {"passed": False, "score": 65.0},
            "code_quality": {"passed": True, "score": 85.0}
        },
        "execution_time": 45.2,
        "automation_strategy": "80/20"
    }


# Integration test scenarios

class TestDodIntegrationScenarios:
    """Integration tests for realistic DoD scenarios."""
    
    def test_complete_dod_workflow_success(self, sample_project_path):
        """Test complete DoD workflow from exoskeleton to report."""
        # Mock all runtime dependencies
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init, \
             patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute, \
             patch("uvmgr.ops.dod.create_automation_report") as mock_report:
            
            # Setup mock returns
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            mock_execute.return_value = {
                "success": True,
                "criteria_results": {
                    "testing": {"passed": True, "score": 95.0},
                    "security": {"passed": True, "score": 90.0}
                }
            }
            mock_report.return_value = {"success": True, "formats_generated": ["json"]}
            
            # Execute complete workflow
            exoskeleton_result = create_exoskeleton(sample_project_path, template="standard")
            assert exoskeleton_result["success"] is True
            
            automation_result = execute_complete_automation(sample_project_path)
            assert automation_result["success"] is True
            
            report_result = generate_dod_report(sample_project_path, automation_result)
            assert report_result["success"] is True
    
    def test_enterprise_dod_workflow(self, sample_project_path):
        """Test enterprise DoD workflow with governance."""
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init, \
             patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            
            # Setup enterprise-grade mocks
            mock_init.return_value = {
                "success": True,
                "files_created": [
                    {"path": ".uvmgr/governance/policies.yaml"},
                    {"path": ".uvmgr/compliance/audit.json"}
                ],
                "workflows_created": ["governance-check", "compliance-validation"],
                "ai_integrations": ["architecture-analysis", "security-advisory"]
            }
            
            mock_execute.return_value = {
                "success": True,
                "criteria_results": {
                    "testing": {"passed": True, "score": 98.0},
                    "security": {"passed": True, "score": 95.0},
                    "compliance": {"passed": True, "score": 92.0},
                    "devops": {"passed": True, "score": 88.0}
                }
            }
            
            # Create enterprise exoskeleton
            exoskeleton_result = create_exoskeleton(
                sample_project_path,
                template="enterprise",
                force=True
            )
            assert exoskeleton_result["success"] is True
            
            # Execute enterprise automation
            automation_result = execute_complete_automation(
                sample_project_path,
                environment="production",
                ai_assist=True
            )
            assert automation_result["success"] is True
            assert automation_result["overall_success_rate"] > 0.90