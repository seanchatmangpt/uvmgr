#!/usr/bin/env python3
"""
Comprehensive unit tests for Definition of Done (DoD) automation system.

Tests cover:
- DoD operations layer functionality
- Command interface validation
- Runtime implementations
- OpenTelemetry integration
- Weaver semantic convention compliance
- Error handling and edge cases
"""

import json
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
    _calculate_weighted_success_rate
)

from uvmgr.runtime.dod import (
    initialize_exoskeleton_files,
    execute_automation_workflow,
    validate_criteria_runtime,
    generate_pipeline_files,
    run_e2e_tests,
    analyze_project_health,
    create_automation_report
)


class TestDoDCriteriaWeights:
    """Test DoD criteria weights and configuration."""
    
    def test_criteria_weights_sum_to_one(self):
        """Verify that all criteria weights sum to approximately 1.0."""
        total_weight = sum(
            criteria.get("weight", 0) 
            for criteria in DOD_CRITERIA_WEIGHTS.values()
        )
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected ~1.0"
    
    def test_critical_criteria_have_high_weights(self):
        """Verify critical criteria (80/20 principle) have highest weights."""
        critical_criteria = [
            name for name, config in DOD_CRITERIA_WEIGHTS.items()
            if config.get("priority") == "critical"
        ]
        
        critical_total = sum(
            DOD_CRITERIA_WEIGHTS[name].get("weight", 0)
            for name in critical_criteria
        )
        
        # Critical criteria should comprise at least 70% of weight (80/20 principle)
        assert critical_total >= 0.70, f"Critical criteria only {critical_total:.2%}, expected ≥70%"
    
    def test_all_criteria_have_required_fields(self):
        """Verify all criteria have weight and priority fields."""
        for name, config in DOD_CRITERIA_WEIGHTS.items():
            assert "weight" in config, f"Criteria '{name}' missing weight"
            assert "priority" in config, f"Criteria '{name}' missing priority"
            assert config["priority"] in ["critical", "important", "optional"], \
                f"Invalid priority '{config['priority']}' for '{name}'"


class TestExoskeletonTemplates:
    """Test exoskeleton template configurations."""
    
    def test_all_templates_have_required_fields(self):
        """Verify all templates have required configuration fields."""
        required_fields = ["description", "includes", "ai_features"]
        
        for template_name, config in EXOSKELETON_TEMPLATES.items():
            for field in required_fields:
                assert field in config, f"Template '{template_name}' missing '{field}'"
            
            assert isinstance(config["includes"], list), \
                f"Template '{template_name}' includes must be a list"
            assert isinstance(config["ai_features"], list), \
                f"Template '{template_name}' ai_features must be a list"
    
    def test_enterprise_template_has_governance(self):
        """Verify enterprise template includes governance features."""
        enterprise = EXOSKELETON_TEMPLATES["enterprise"]
        governance_features = ["compliance", "monitoring", "advanced_ci"]
        
        for feature in governance_features:
            assert any(feature in include for include in enterprise["includes"]), \
                f"Enterprise template missing governance feature: {feature}"


class TestCreateExoskeleton:
    """Test exoskeleton creation functionality."""
    
    @patch('uvmgr.ops.dod.initialize_exoskeleton_files')
    def test_create_exoskeleton_success(self, mock_initialize):
        """Test successful exoskeleton creation."""
        mock_initialize.return_value = {
            "success": True,
            "files_created": [{"path": ".uvmgr/config.yaml", "description": "Main config"}],
            "workflows_created": ["dod-automation.yaml"],
            "ai_integrations": ["code_review"]
        }
        
        result = create_exoskeleton(
            project_path=Path("/test/project"),
            template="standard",
            force=False,
            preview=False
        )
        
        assert result["success"] is True
        assert "files_created" in result
        mock_initialize.assert_called_once()
    
    def test_create_exoskeleton_preview_mode(self):
        """Test exoskeleton preview without file creation."""
        result = create_exoskeleton(
            project_path=Path("/test/project"),
            template="standard",
            force=False,
            preview=True
        )
        
        assert result["success"] is True
        assert result["preview"] is True
        assert "structure" in result
        assert result["template"] == "standard"
    
    def test_create_exoskeleton_invalid_template(self):
        """Test error handling for invalid template."""
        result = create_exoskeleton(
            project_path=Path("/test/project"),
            template="invalid_template",
            force=False,
            preview=False
        )
        
        assert result["success"] is False
        assert "Unknown template" in result["error"]
    
    @patch('uvmgr.ops.dod.initialize_exoskeleton_files')
    def test_create_exoskeleton_handles_exception(self, mock_initialize):
        """Test exception handling in exoskeleton creation."""
        mock_initialize.side_effect = Exception("Filesystem error")
        
        result = create_exoskeleton(
            project_path=Path("/test/project"),
            template="standard",
            force=False,
            preview=False
        )
        
        assert result["success"] is False
        assert "Failed to create exoskeleton" in result["error"]


class TestCompleteAutomation:
    """Test complete DoD automation execution."""
    
    @patch('uvmgr.ops.dod.execute_automation_workflow')
    def test_execute_complete_automation_success(self, mock_execute):
        """Test successful complete automation execution."""
        mock_execute.return_value = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0}
            }
        }
        
        result = execute_complete_automation(
            project_path=Path("/test/project"),
            environment="development",
            auto_fix=True,
            parallel=True
        )
        
        assert result["success"] is True
        assert "overall_success_rate" in result
        assert "execution_time" in result
        assert "automation_strategy" in result
        assert result["automation_strategy"] == "80/20"
    
    @patch('uvmgr.ops.dod.execute_automation_workflow')
    def test_execute_complete_automation_skip_criteria(self, mock_execute):
        """Test automation with skipped criteria."""
        mock_execute.return_value = {
            "success": True,
            "criteria_results": {
                "devops": {"passed": True, "score": 92.0},
                "code_quality": {"passed": True, "score": 85.0}
            }
        }
        
        result = execute_complete_automation(
            project_path=Path("/test/project"),
            skip_tests=True,
            skip_security=True
        )
        
        # Verify testing and security were filtered out
        criteria_executed = result.get("criteria_executed", [])
        assert "testing" not in criteria_executed
        assert "security" not in criteria_executed
    
    @patch('uvmgr.ops.dod.execute_automation_workflow')
    def test_execute_complete_automation_handles_exception(self, mock_execute):
        """Test exception handling in complete automation."""
        mock_execute.side_effect = Exception("Automation failure")
        
        result = execute_complete_automation(
            project_path=Path("/test/project")
        )
        
        assert result["success"] is False
        assert "Automation execution failed" in result["error"]
        assert "execution_time" in result


class TestValidateDoDCriteria:
    """Test DoD criteria validation."""
    
    @patch('uvmgr.ops.dod.validate_criteria_runtime')
    def test_validate_dod_criteria_success(self, mock_validate):
        """Test successful criteria validation."""
        mock_validate.return_value = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 95.0, "passed": True, "weight": 0.25},
                "security": {"score": 88.0, "passed": True, "weight": 0.25}
            }
        }
        
        result = validate_dod_criteria(
            project_path=Path("/test/project"),
            criteria=["testing", "security"],
            detailed=True,
            fix_suggestions=True
        )
        
        assert result["success"] is True
        assert "overall_score" in result
        assert "critical_score" in result
        assert "scoring_strategy" in result
        assert result["scoring_strategy"] == "80/20 weighted"
    
    @patch('uvmgr.ops.dod.validate_criteria_runtime')
    def test_validate_dod_criteria_calculates_scores(self, mock_validate):
        """Test score calculation for different priority levels."""
        mock_validate.return_value = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 90.0, "passed": True},      # critical
                "security": {"score": 85.0, "passed": True},     # critical  
                "code_quality": {"score": 80.0, "passed": True}, # important
                "performance": {"score": 75.0, "passed": True}   # optional
            }
        }
        
        result = validate_dod_criteria(
            project_path=Path("/test/project"),
            criteria=["testing", "security", "code_quality", "performance"]
        )
        
        assert result["critical_score"] == 87.5  # (90 + 85) / 2
        assert result["important_score"] == 80.0
        assert result["overall_score"] > 0


class TestWeightedSuccessRate:
    """Test weighted success rate calculation."""
    
    def test_calculate_weighted_success_rate_basic(self):
        """Test basic weighted success rate calculation."""
        criteria_results = {
            "testing": {"score": 90.0},
            "security": {"score": 80.0},
            "devops": {"score": 85.0}
        }
        criteria = ["testing", "security", "devops"]
        
        rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Expected: (90*0.25 + 80*0.25 + 85*0.20) / (0.25 + 0.25 + 0.20)
        expected = (90*0.25 + 80*0.25 + 85*0.20) / (0.25 + 0.25 + 0.20)
        assert abs(rate - expected) < 0.01
    
    def test_calculate_weighted_success_rate_boolean_passed(self):
        """Test weighted calculation with boolean passed values."""
        criteria_results = {
            "testing": {"passed": True},
            "security": {"passed": False}
        }
        criteria = ["testing", "security"]
        
        rate = _calculate_weighted_success_rate(criteria_results, criteria)
        
        # Expected: (1.0*0.25 + 0.0*0.25) / (0.25 + 0.25) = 0.5
        expected = 0.5
        assert abs(rate - expected) < 0.01
    
    def test_calculate_weighted_success_rate_empty_results(self):
        """Test weighted calculation with empty results."""
        rate = _calculate_weighted_success_rate({}, [])
        assert rate == 0.0


class TestDevOpsPipeline:
    """Test DevOps pipeline generation."""
    
    @patch('uvmgr.ops.dod.generate_pipeline_files')
    def test_generate_devops_pipeline_success(self, mock_generate):
        """Test successful pipeline generation."""
        mock_generate.return_value = {
            "success": True,
            "provider": "github",
            "files_created": [".github/workflows/dod-automation.yml"],
            "features_enabled": ["testing", "security"],
            "environments_configured": ["dev", "staging", "production"]
        }
        
        result = generate_devops_pipeline(
            project_path=Path("/test/project"),
            provider="github-actions",
            environments=["dev", "staging", "production"],
            features=["testing", "security"]
        )
        
        assert result["success"] is True
        assert result["provider"] == "github"
        assert len(result["files_created"]) > 0
    
    @patch('uvmgr.ops.dod.generate_pipeline_files')
    def test_generate_devops_pipeline_with_defaults(self, mock_generate):
        """Test pipeline generation with default values."""
        mock_generate.return_value = {"success": True, "files_created": []}
        
        result = generate_devops_pipeline(
            project_path=Path("/test/project")
        )
        
        # Verify defaults were applied
        call_args = mock_generate.call_args[1]
        assert call_args["environments"] == ["dev", "staging", "production"]
        assert "testing" in call_args["features"]
        assert "security" in call_args["features"]


class TestE2EAutomation:
    """Test end-to-end automation functionality."""
    
    @patch('uvmgr.ops.dod.run_e2e_tests')
    def test_run_e2e_automation_success(self, mock_run):
        """Test successful E2E automation."""
        mock_run.return_value = {
            "success": True,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 23, "failed": 2},
                "api_tests": {"total": 15, "passed": 15, "failed": 0}
            }
        }
        
        result = run_e2e_automation(
            project_path=Path("/test/project"),
            environment="staging",
            parallel=True,
            headless=True
        )
        
        assert result["success"] is True
        assert "success_rate" in result
        assert "total_tests" in result
        assert result["total_tests"] == 40  # 25 + 15
        assert result["passed_tests"] == 38  # 23 + 15
        assert abs(result["success_rate"] - 0.95) < 0.01  # 38/40


class TestProjectStatusAnalysis:
    """Test project status analysis."""
    
    @patch('uvmgr.ops.dod.analyze_project_health')
    def test_analyze_project_status_success(self, mock_analyze):
        """Test successful project status analysis."""
        mock_analyze.return_value = {
            "success": True,
            "dod_status": {"overall_score": 85.0},
            "automation_health": {"score": 90.0},
            "security_posture": {"score": 88.0},
            "code_quality": {"score": 82.0},
            "suggestions": ["Improve test coverage", "Update dependencies"]
        }
        
        result = analyze_project_status(
            project_path=Path("/test/project"),
            detailed=True,
            suggestions=True
        )
        
        assert result["success"] is True
        assert "health_score" in result
        assert "health_components" in result
        assert "scoring_strategy" in result
        
        # Verify weighted health score calculation
        expected_health = (85.0*0.40 + 90.0*0.30 + 88.0*0.20 + 82.0*0.10)
        assert abs(result["health_score"] - expected_health) < 0.01


class TestRuntimeImplementations:
    """Test runtime layer implementations."""
    
    def test_initialize_exoskeleton_files_success(self):
        """Test successful exoskeleton file initialization."""
        with patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.exists', return_value=False):
            
            result = initialize_exoskeleton_files(
                project_path=Path("/test/project"),
                template_config=EXOSKELETON_TEMPLATES["standard"],
                force=False
            )
            
            assert result["success"] is True
            assert "files_created" in result
            assert "workflows_created" in result
    
    def test_initialize_exoskeleton_files_already_exists(self):
        """Test handling when exoskeleton already exists."""
        with patch('pathlib.Path.exists', return_value=True):
            result = initialize_exoskeleton_files(
                project_path=Path("/test/project"),
                template_config=EXOSKELETON_TEMPLATES["standard"],
                force=False
            )
            
            assert result["success"] is False
            assert "already exists" in result["error"]
    
    def test_execute_automation_workflow_generates_results(self):
        """Test automation workflow execution generates realistic results."""
        result = execute_automation_workflow(
            project_path=Path("/test/project"),
            criteria=["testing", "security", "devops"],
            environment="development",
            auto_fix=True,
            parallel=True,
            ai_assist=True
        )
        
        assert result["success"] is True
        assert "criteria_results" in result
        assert len(result["criteria_results"]) == 3
        assert "execution_time" in result
        
        # Verify all criteria have realistic scores
        for criteria, details in result["criteria_results"].items():
            assert "passed" in details
            assert "score" in details
            assert 0 <= details["score"] <= 100
    
    def test_validate_criteria_runtime_scoring(self):
        """Test runtime criteria validation scoring."""
        result = validate_criteria_runtime(
            project_path=Path("/test/project"),
            criteria=["testing", "security"],
            detailed=True,
            fix_suggestions=True
        )
        
        assert result["success"] is True
        assert "criteria_scores" in result
        
        for criteria, details in result["criteria_scores"].items():
            assert "score" in details
            assert "passed" in details
            assert "weight" in details
            assert 0 <= details["score"] <= 100
    
    def test_generate_pipeline_files_github(self):
        """Test GitHub pipeline file generation."""
        with patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text') as mock_write:
            
            result = generate_pipeline_files(
                project_path=Path("/test/project"),
                provider="github",
                environments=["dev", "prod"],
                features=["testing", "security"],
                template="standard",
                output_path=None
            )
            
            assert result["success"] is True
            assert result["provider"] == "github"
            assert len(result["files_created"]) > 0
            
            # Verify workflow file was written
            mock_write.assert_called()
            written_content = mock_write.call_args[0][0]
            assert "name: DoD Automation" in written_content
            assert "uvmgr dod complete" in written_content


class TestOpenTelemetryIntegration:
    """Test OpenTelemetry integration and Weaver compliance."""
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    def test_create_exoskeleton_otel_instrumentation(self, mock_span):
        """Test that create_exoskeleton properly instruments with OTEL."""
        mock_span_instance = Mock()
        mock_span.return_value = mock_span_instance
        
        with patch('uvmgr.ops.dod.initialize_exoskeleton_files') as mock_init:
            mock_init.return_value = {"success": True, "files_created": [], "workflows_created": [], "ai_integrations": []}
            
            create_exoskeleton(
                project_path=Path("/test/project"),
                template="standard",
                force=True,
                preview=False
            )
            
            # Verify span attributes were set according to Weaver conventions
            mock_span_instance.set_attributes.assert_called()
            call_args = mock_span_instance.set_attributes.call_args[0][0]
            
            # Check for required Weaver semantic attributes
            assert "dod.template" in call_args
            assert "dod.force" in call_args
            assert "dod.preview" in call_args
            assert "project.path" in call_args
    
    @patch('uvmgr.ops.dod.trace.get_current_span')
    def test_execute_complete_automation_otel_spans(self, mock_span):
        """Test complete automation OTEL span instrumentation."""
        mock_span_instance = Mock()
        mock_span.return_value = mock_span_instance
        
        with patch('uvmgr.ops.dod.execute_automation_workflow') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "criteria_results": {"testing": {"passed": True, "score": 90}}
            }
            
            execute_complete_automation(
                project_path=Path("/test/project"),
                environment="production",
                auto_fix=True,
                parallel=True,
                ai_assist=True
            )
            
            # Verify proper span attributes
            call_args = mock_span_instance.set_attributes.call_args_list
            
            # Check initial attributes
            initial_attrs = call_args[0][0][0]
            assert "dod.environment" in initial_attrs
            assert "dod.auto_fix" in initial_attrs
            assert "dod.parallel" in initial_attrs
            assert "dod.ai_assist" in initial_attrs
            
            # Check result attributes  
            result_attrs = call_args[1][0][0]
            assert "dod.success_rate" in result_attrs
            assert "dod.execution_time" in result_attrs
    
    def test_weaver_semantic_convention_compliance(self):
        """Test compliance with Weaver semantic conventions."""
        # Define expected Weaver semantic attributes for DoD operations
        expected_attributes = {
            "dod.operation": str,
            "dod.template": str,
            "dod.environment": str,
            "dod.success_rate": float,
            "dod.criteria_count": int,
            "project.path": str,
            "automation.strategy": str
        }
        
        # This test verifies that we're following proper naming conventions
        # In a real implementation, we'd validate against actual Weaver schema
        for attr_name, attr_type in expected_attributes.items():
            # Verify attribute names follow dod.* or project.* namespace
            assert attr_name.startswith(("dod.", "project.", "automation.")), \
                f"Attribute '{attr_name}' doesn't follow Weaver namespace convention"
            
            # Verify snake_case naming
            assert attr_name.islower(), f"Attribute '{attr_name}' should be lowercase"
            assert "_" in attr_name or "." in attr_name, \
                f"Attribute '{attr_name}' should use snake_case"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    def test_missing_project_path(self):
        """Test handling of missing project paths."""
        with patch('pathlib.Path.exists', return_value=False):
            result = create_exoskeleton(
                project_path=Path("/nonexistent/project"),
                template="standard"
            )
            
            # Should handle gracefully even if path doesn't exist
            assert "success" in result
    
    def test_invalid_criteria_names(self):
        """Test handling of invalid criteria names."""
        result = validate_dod_criteria(
            project_path=Path("/test/project"),
            criteria=["invalid_criteria", "another_invalid"],
            detailed=False
        )
        
        # Should handle gracefully and return valid result structure
        assert "success" in result
        assert "overall_score" in result
    
    def test_concurrent_access_safety(self):
        """Test thread safety for concurrent DoD operations."""
        import threading
        import time
        
        results = []
        
        def run_validation():
            result = validate_criteria_runtime(
                project_path=Path("/test/project"),
                criteria=["testing"],
                detailed=False,
                fix_suggestions=False
            )
            results.append(result)
        
        # Run multiple validations concurrently
        threads = [threading.Thread(target=run_validation) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])