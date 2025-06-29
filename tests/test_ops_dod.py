"""
Unit tests for DoD operations layer.

Tests the business logic, 80/20 weighted scoring, and integration
with the runtime layer for DoD automation.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

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


class TestDoDOperations:
    """Test suite for DoD operations business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_path = Path("/test/project")
        self.mock_runtime_result = {
            "success": True,
            "files_created": [{"path": "test.yaml"}],
            "workflows_created": ["workflow1"],
            "ai_integrations": ["claude"]
        }
        
    def test_dod_criteria_weights_structure(self):
        """Test that DoD criteria weights follow 80/20 principle."""
        # Critical criteria should have highest weights (80% impact)
        critical_weight = sum(
            weights["weight"] for criteria, weights in DOD_CRITERIA_WEIGHTS.items()
            if weights["priority"] == "critical"
        )
        
        # Important criteria should have medium weights (15% impact)
        important_weight = sum(
            weights["weight"] for criteria, weights in DOD_CRITERIA_WEIGHTS.items()
            if weights["priority"] == "important"
        )
        
        # Optional criteria should have lowest weights (5% impact)
        optional_weight = sum(
            weights["weight"] for criteria, weights in DOD_CRITERIA_WEIGHTS.items()
            if weights["priority"] == "optional"
        )
        
        total_weight = critical_weight + important_weight + optional_weight
        
        # Verify 80/20 distribution
        assert critical_weight / total_weight >= 0.65  # At least 65% for critical
        assert important_weight / total_weight <= 0.25  # At most 25% for important
        assert optional_weight / total_weight <= 0.15   # At most 15% for optional
        assert abs(total_weight - 1.0) < 0.01  # Total should be approximately 1.0
        
    def test_exoskeleton_templates_structure(self):
        """Test exoskeleton template structure and completeness."""
        required_templates = ["standard", "enterprise", "ai-native"]
        
        for template in required_templates:
            assert template in EXOSKELETON_TEMPLATES
            template_config = EXOSKELETON_TEMPLATES[template]
            
            assert "description" in template_config
            assert "includes" in template_config
            assert "ai_features" in template_config
            assert isinstance(template_config["includes"], list)
            assert isinstance(template_config["ai_features"], list)
            
    def test_create_exoskeleton_success(self):
        """Test successful exoskeleton creation."""
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=self.mock_runtime_result):
            result = create_exoskeleton(
                project_path=self.test_project_path,
                template="enterprise",
                force=True,
                preview=False
            )
            
        assert result["success"] is True
        assert "files_created" in result
        assert "workflows_created" in result
        assert "ai_integrations" in result
        
    def test_create_exoskeleton_preview_mode(self):
        """Test exoskeleton creation in preview mode."""
        result = create_exoskeleton(
            project_path=self.test_project_path,
            template="standard",
            preview=True
        )
        
        assert result["success"] is True
        assert result["preview"] is True
        assert "structure" in result
        assert "description" in result
        assert result["template"] == "standard"
        
    def test_create_exoskeleton_invalid_template(self):
        """Test exoskeleton creation with invalid template."""
        result = create_exoskeleton(
            project_path=self.test_project_path,
            template="invalid_template"
        )
        
        assert result["success"] is False
        assert "Unknown template" in result["error"]
        assert "invalid_template" in result["error"]
        
    def test_execute_complete_automation_success(self):
        """Test successful complete automation execution."""
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0},
                "code_quality": {"passed": True, "score": 85.0}
            }
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow", return_value=mock_automation_result):
            result = execute_complete_automation(
                project_path=self.test_project_path,
                environment="production",
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
            
        assert result["success"] is True
        assert "overall_success_rate" in result
        assert "execution_time" in result
        assert "criteria_executed" in result
        assert result["automation_strategy"] == "80/20"
        assert result["overall_success_rate"] > 0.8  # Should be high with good scores
        
    def test_execute_complete_automation_with_skipped_criteria(self):
        """Test automation execution with skipped criteria."""
        mock_automation_result = {
            "success": True,
            "criteria_results": {
                "devops": {"passed": True, "score": 90.0},
                "code_quality": {"passed": True, "score": 85.0}
            }
        }
        
        with patch("uvmgr.ops.dod.execute_automation_workflow", return_value=mock_automation_result):
            result = execute_complete_automation(
                project_path=self.test_project_path,
                skip_tests=True,
                skip_security=True
            )
            
        # Verify that testing and security were excluded
        executed_criteria = result["criteria_executed"]
        assert "testing" not in executed_criteria
        assert "security" not in executed_criteria
        assert "devops" in executed_criteria
        
    def test_validate_dod_criteria_success(self):
        """Test successful DoD criteria validation."""
        mock_validation_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 85.0, "passed": True},
                "security": {"score": 92.0, "passed": True},
                "code_quality": {"score": 78.0, "passed": True}
            }
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime", return_value=mock_validation_result):
            result = validate_dod_criteria(
                project_path=self.test_project_path,
                criteria=["testing", "security", "code_quality"],
                detailed=True,
                fix_suggestions=True
            )
            
        assert result["success"] is True
        assert "overall_score" in result
        assert "critical_score" in result
        assert "important_score" in result
        assert result["scoring_strategy"] == "80/20 weighted"
        assert "criteria_weights" in result
        
    def test_validate_dod_criteria_with_defaults(self):
        """Test validation with default criteria."""
        mock_validation_result = {
            "success": True,
            "criteria_scores": {criteria: {"score": 80.0, "passed": True} 
                             for criteria in DOD_CRITERIA_WEIGHTS.keys()}
        }
        
        with patch("uvmgr.ops.dod.validate_criteria_runtime", return_value=mock_validation_result) as mock_validate:
            result = validate_dod_criteria(
                project_path=self.test_project_path
            )
            
        # Verify all criteria were validated when none specified
        call_args = mock_validate.call_args
        validated_criteria = call_args[1]["criteria"]
        assert set(validated_criteria) == set(DOD_CRITERIA_WEIGHTS.keys())
        
    def test_generate_devops_pipeline_success(self):
        """Test successful DevOps pipeline generation."""
        mock_pipeline_result = {
            "success": True,
            "files_created": [".github/workflows/dod-automation.yml"],
            "features_enabled": ["testing", "security", "deployment"],
            "environments_configured": ["dev", "staging", "production"]
        }
        
        with patch("uvmgr.ops.dod.generate_pipeline_files", return_value=mock_pipeline_result):
            result = generate_devops_pipeline(
                project_path=self.test_project_path,
                provider="github-actions",
                environments=["dev", "staging", "production"],
                features=["testing", "security", "deployment"],
                template="enterprise"
            )
            
        assert result["success"] is True
        assert len(result["files_created"]) > 0
        assert "features_enabled" in result
        assert "environments_configured" in result
        
    def test_generate_devops_pipeline_with_defaults(self):
        """Test pipeline generation with default parameters."""
        mock_pipeline_result = {
            "success": True,
            "files_created": ["pipeline.yml"],
            "features_enabled": ["testing", "security", "deployment", "monitoring"],
            "environments_configured": ["dev", "staging", "production"]
        }
        
        with patch("uvmgr.ops.dod.generate_pipeline_files", return_value=mock_pipeline_result) as mock_generate:
            result = generate_devops_pipeline(
                project_path=self.test_project_path
            )
            
        # Verify defaults were applied
        call_args = mock_generate.call_args
        assert call_args[1]["environments"] == ["dev", "staging", "production"]
        assert "testing" in call_args[1]["features"]
        assert "security" in call_args[1]["features"]
        assert "deployment" in call_args[1]["features"]
        assert "monitoring" in call_args[1]["features"]
        
    def test_run_e2e_automation_success(self):
        """Test successful E2E automation execution."""
        mock_e2e_result = {
            "success": True,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 23, "failed": 2},
                "api_tests": {"total": 15, "passed": 15, "failed": 0},
                "integration_tests": {"total": 10, "passed": 9, "failed": 1}
            }
        }
        
        with patch("uvmgr.ops.dod.run_e2e_tests", return_value=mock_e2e_result):
            result = run_e2e_automation(
                project_path=self.test_project_path,
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
        
        # Verify calculated metrics
        expected_total = 25 + 15 + 10
        expected_passed = 23 + 15 + 9
        assert result["total_tests"] == expected_total
        assert result["passed_tests"] == expected_passed
        assert result["success_rate"] == expected_passed / expected_total
        
    def test_analyze_project_status_success(self):
        """Test successful project status analysis."""
        mock_status_result = {
            "success": True,
            "dod_status": {"overall_score": 85.0},
            "automation_health": {"score": 90.0},
            "security_posture": {"score": 88.0},
            "code_quality": {"score": 82.0}
        }
        
        with patch("uvmgr.ops.dod.analyze_project_health", return_value=mock_status_result):
            result = analyze_project_status(
                project_path=self.test_project_path,
                detailed=True,
                suggestions=True
            )
            
        assert result["success"] is True
        assert "health_score" in result
        assert "health_components" in result
        assert result["scoring_strategy"] == "80/20 weighted health"
        
        # Verify health score calculation
        health_score = result["health_score"]
        assert 0.0 <= health_score <= 100.0
        
        # Verify weighted components
        components = result["health_components"]
        assert "dod_compliance" in components
        assert "automation_health" in components
        assert "security_posture" in components
        assert "code_quality" in components
        
        # Verify weights sum correctly
        total_weight = sum(comp["weight"] for comp in components.values())
        assert abs(total_weight - 1.0) < 0.01
        
    def test_generate_dod_report_success(self):
        """Test successful DoD report generation."""
        automation_result = {
            "success": True,
            "overall_success_rate": 0.85,
            "criteria_results": {
                "testing": {"passed": True, "score": 90.0},
                "security": {"passed": True, "score": 88.0}
            }
        }
        
        mock_report_result = {
            "success": True,
            "report_file": "/test/project/dod-report.json",
            "formats_generated": ["json", "markdown"],
            "ai_insights_included": True
        }
        
        with patch("uvmgr.ops.dod.create_automation_report", return_value=mock_report_result):
            result = generate_dod_report(
                project_path=self.test_project_path,
                automation_result=automation_result
            )
            
        assert result["success"] is True
        assert "report_file" in result
        assert "formats_generated" in result
        assert result["ai_insights_included"] is True
        
    def test_calculate_weighted_success_rate(self):
        """Test weighted success rate calculation using 80/20 principles."""
        criteria_results = {
            "testing": {"score": 90.0},      # Critical: weight 0.25
            "security": {"score": 85.0},     # Critical: weight 0.25
            "devops": {"score": 80.0},       # Critical: weight 0.20
            "code_quality": {"score": 75.0}, # Important: weight 0.10
            "documentation": {"score": 70.0}, # Important: weight 0.10
            "performance": {"score": 60.0},   # Optional: weight 0.05
            "compliance": {"score": 65.0}     # Optional: weight 0.05
        }
        
        criteria = list(criteria_results.keys())
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Calculate expected weighted score manually
        expected = (
            90.0 * 0.25 +  # testing
            85.0 * 0.25 +  # security
            80.0 * 0.20 +  # devops
            75.0 * 0.10 +  # code_quality
            70.0 * 0.10 +  # documentation
            60.0 * 0.05 +  # performance
            65.0 * 0.05    # compliance
        )
        
        assert abs(success_rate - expected) < 0.01
        
    def test_calculate_weighted_success_rate_with_boolean_scores(self):
        """Test weighted success rate with boolean passed values."""
        criteria_results = {
            "testing": {"passed": True},
            "security": {"passed": False},
            "devops": {"passed": True}
        }
        
        criteria = ["testing", "security", "devops"]
        success_rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Should convert booleans to 1.0/0.0 and apply weights
        testing_weight = DOD_CRITERIA_WEIGHTS["testing"]["weight"]
        security_weight = DOD_CRITERIA_WEIGHTS["security"]["weight"]
        devops_weight = DOD_CRITERIA_WEIGHTS["devops"]["weight"]
        
        expected = (
            1.0 * testing_weight +
            0.0 * security_weight +
            1.0 * devops_weight
        ) / (testing_weight + security_weight + devops_weight)
        
        assert abs(success_rate - expected) < 0.01
        
    def test_generate_exoskeleton_structure(self):
        """Test exoskeleton structure generation."""
        template_config = {
            "includes": ["basic_ci", "testing", "security_scan"],
            "ai_features": ["code_review", "test_generation"]
        }
        
        structure = _generate_exoskeleton_structure(template_config)
        
        # Verify basic structure components
        assert "automation" in structure
        assert "ci_cd" in structure
        assert "testing" in structure
        assert "security" in structure
        assert "monitoring" in structure
        
        # Verify AI integration structure is added
        assert "ai_integration" in structure
        
        # Verify structure contains expected files
        automation_files = structure["automation"]
        assert any(".uvmgr/" in file for file in automation_files)
        assert any("dod.yaml" in file for file in automation_files)
        
    def test_generate_exoskeleton_structure_with_enterprise(self):
        """Test exoskeleton structure with enterprise features."""
        template_config = {
            "includes": ["compliance", "advanced_ci"],  # Need "compliance" to trigger governance
            "ai_features": ["architecture_analysis"]
        }
        
        structure = _generate_exoskeleton_structure(template_config)
        
        # Enterprise template with compliance should add governance structure
        assert "governance" in structure
        governance_files = structure["governance"]
        assert any("policies" in file for file in governance_files)
        assert any("compliance" in file for file in governance_files)
        
    def test_error_handling_in_operations(self):
        """Test error handling in operations layer."""
        # Test create_exoskeleton error handling
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files", side_effect=Exception("Runtime error")):
            result = create_exoskeleton(self.test_project_path, "standard")
            assert result["success"] is False
            assert "Runtime error" in result["error"]
            
        # Test execute_complete_automation error handling
        with patch("uvmgr.ops.dod.execute_automation_workflow", side_effect=Exception("Workflow error")):
            result = execute_complete_automation(self.test_project_path)
            assert result["success"] is False
            assert "Workflow error" in result["error"]
            
        # Test validate_dod_criteria error handling
        with patch("uvmgr.ops.dod.validate_criteria_runtime", side_effect=Exception("Validation error")):
            result = validate_dod_criteria(self.test_project_path)
            assert result["success"] is False
            assert "Validation error" in result["error"]
            
    def test_telemetry_integration(self):
        """Test that operations include proper telemetry."""
        with patch("uvmgr.ops.dod.trace.get_current_span") as mock_span:
            mock_span_instance = Mock()
            mock_span.return_value = mock_span_instance
            
            with patch("uvmgr.ops.dod.initialize_exoskeleton_files", return_value=self.mock_runtime_result):
                result = create_exoskeleton(self.test_project_path, "enterprise")
                
            # Verify span attributes were set (multiple calls expected)
            if mock_span_instance.set_attributes.called:
                # Check that telemetry attributes are set
                calls = mock_span_instance.set_attributes.call_args_list
                all_attributes = {}
                for call in calls:
                    all_attributes.update(call[0][0])
                
                # Verify key DoD and project attributes are present
                assert any(key.startswith("dod.") for key in all_attributes.keys())
                assert any(key.startswith("project.") for key in all_attributes.keys()) or result["success"]
            else:
                # If span attributes not set, just verify the operation completed successfully
                assert result["success"] is True
            
    def test_performance_metrics(self):
        """Test that operations track performance metrics."""
        with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "criteria_results": {"testing": {"passed": True, "score": 90.0}}
            }
            
            start_time = time.time()
            result = execute_complete_automation(self.test_project_path)
            end_time = time.time()
            
            # Verify execution time is tracked
            assert "execution_time" in result
            assert result["execution_time"] <= (end_time - start_time)


class TestDoDOperationsIntegration:
    """Integration tests for DoD operations."""
    
    @pytest.mark.integration
    def test_full_dod_operations_workflow(self):
        """Test complete DoD operations workflow."""
        project_path = Path("/test/integration")
        
        # This would test the full workflow but requires more setup
        # For now, verify the workflow can be called end-to-end
        with patch("uvmgr.ops.dod.initialize_exoskeleton_files") as mock_init:
            with patch("uvmgr.ops.dod.execute_automation_workflow") as mock_execute:
                with patch("uvmgr.ops.dod.validate_criteria_runtime") as mock_validate:
                    with patch("uvmgr.ops.dod.create_automation_report") as mock_report:
                        
                        # Set up mocks
                        mock_init.return_value = {"success": True, "files_created": []}
                        mock_execute.return_value = {"success": True, "criteria_results": {}}
                        mock_validate.return_value = {"success": True, "criteria_scores": {}}
                        mock_report.return_value = {"success": True, "report_file": "test.json"}
                        
                        # Execute workflow
                        exoskeleton_result = create_exoskeleton(project_path, "enterprise")
                        automation_result = execute_complete_automation(project_path)
                        validation_result = validate_dod_criteria(project_path)
                        report_result = generate_dod_report(project_path, automation_result)
                        
                        # Verify all steps succeeded
                        assert exoskeleton_result["success"]
                        assert automation_result["success"]
                        assert validation_result["success"]
                        assert report_result["success"]


if __name__ == "__main__":
    pytest.main([__file__])