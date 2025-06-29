"""
Unit tests for DoD commands layer.

Tests the CLI interface, argument parsing, and command integration
for the Definition of Done automation system.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from uvmgr.commands.dod import app
from uvmgr.ops.dod import DOD_CRITERIA_WEIGHTS


class TestDoDCommands:
    """Test suite for DoD command-line interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_project_path = Path("/test/project")
        
    def test_dod_status_command_success(self):
        """Test successful DoD status command execution."""
        mock_result = {
            "success": True,
            "health_score": 85.5,
            "dod_status": {"overall_score": 82.5},
            "security_posture": {"score": 90.0},
            "suggestions": [
                "Improve integration test coverage",
                "Add performance benchmarks"
            ]
        }
        
        with patch("uvmgr.commands.dod.analyze_project_status", return_value=mock_result):
            result = self.runner.invoke(app, ["status"])
            
        assert result.exit_code == 0
        assert "📊 Project DoD Status" in result.stdout
        assert "Overall Health Score: 85.5%" in result.stdout
        assert "EXCELLENT" in result.stdout
        assert "Improve integration test coverage" in result.stdout
        
    def test_dod_status_command_needs_work(self):
        """Test DoD status command with low scores."""
        mock_result = {
            "success": True,
            "health_score": 45.0,
            "dod_status": {"overall_score": 40.0},
            "security_posture": {"score": 50.0},
            "suggestions": ["Fix critical security issues"]
        }
        
        with patch("uvmgr.commands.dod.analyze_project_status", return_value=mock_result):
            result = self.runner.invoke(app, ["status"])
            
        assert result.exit_code == 0
        assert "Overall Health Score: 45.0%" in result.stdout
        assert "NEEDS WORK" in result.stdout
        
    def test_complete_automation_success(self):
        """Test successful complete automation command."""
        mock_result = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0},
                "devops": {"passed": True, "score": 92.0}
            },
            "overall_success_rate": 0.91
        }
        
        with patch("uvmgr.commands.dod.execute_complete_automation", return_value=mock_result):
            result = self.runner.invoke(app, ["complete", "--env", "development", "--auto-fix"])
            
        assert result.exit_code == 0
        assert "🎯 Definition of Done Automation" in result.stdout
        assert "✅ PASS" in result.stdout
        assert "95.0%" in result.stdout
        assert "DoD automation completed successfully!" in result.stdout
        
    def test_complete_automation_failure(self):
        """Test complete automation command with failures."""
        mock_result = {
            "success": False,
            "criteria_results": {
                "testing": {"passed": False, "score": 45.0},
                "security": {"passed": True, "score": 88.0}
            },
            "error": "Some validations failed"
        }
        
        with patch("uvmgr.commands.dod.execute_complete_automation", return_value=mock_result):
            result = self.runner.invoke(app, ["complete"])
            
        assert result.exit_code == 1
        assert "❌ FAIL" in result.stdout
        assert "45.0%" in result.stdout
        assert "DoD automation failed" in result.stdout
        
    def test_exoskeleton_creation_success(self):
        """Test successful exoskeleton creation."""
        mock_result = {
            "success": True,
            "created_files": [
                {"path": ".uvmgr/exoskeleton/config.yaml"},
                {"path": ".uvmgr/automation/workflows/dod.yml"}
            ]
        }
        
        with patch("uvmgr.commands.dod.create_exoskeleton", return_value=mock_result):
            result = self.runner.invoke(app, ["exoskeleton", "--template", "enterprise"])
            
        assert result.exit_code == 0
        assert "🏗️ Initializing Weaver Forge Exoskeleton" in result.stdout
        assert "✅ Exoskeleton initialized successfully!" in result.stdout
        assert "Created 2 files:" in result.stdout
        
    def test_exoskeleton_creation_failure(self):
        """Test exoskeleton creation failure."""
        mock_result = {
            "success": False,
            "error": "Exoskeleton already exists"
        }
        
        with patch("uvmgr.commands.dod.create_exoskeleton", return_value=mock_result):
            result = self.runner.invoke(app, ["exoskeleton"])
            
        assert result.exit_code == 1
        assert "❌ Failed to initialize exoskeleton" in result.stdout
        assert "Exoskeleton already exists" in result.stdout
        
    def test_validate_criteria_success(self):
        """Test successful criteria validation."""
        mock_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 85.0, "passed": True},
                "security": {"score": 92.0, "passed": True},
                "code_quality": {"score": 78.0, "passed": True}
            },
            "overall_score": 85.0
        }
        
        with patch("uvmgr.commands.dod.validate_dod_criteria", return_value=mock_result):
            result = self.runner.invoke(app, ["validate", "--detailed"])
            
        assert result.exit_code == 0
        assert "✅ DoD Criteria Validation" in result.stdout
        assert "85.0%" in result.stdout
        assert "✅ PASS" in result.stdout
        assert "All validations passed!" in result.stdout
        
    def test_validate_criteria_with_specific_criteria(self):
        """Test validation with specific criteria."""
        mock_result = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 85.0, "passed": True},
                "security": {"score": 92.0, "passed": True}
            },
            "overall_score": 88.5
        }
        
        with patch("uvmgr.commands.dod.validate_dod_criteria", return_value=mock_result) as mock_validate:
            result = self.runner.invoke(app, ["validate", "--criteria", "testing", "--criteria", "security"])
            
        assert result.exit_code == 0
        # Verify the mock was called with the correct criteria
        call_args = mock_validate.call_args
        assert call_args[1]["criteria"] == ["testing", "security"]
        
    def test_validate_criteria_partial_failure(self):
        """Test validation with some failures."""
        mock_result = {
            "success": False,
            "criteria_scores": {
                "testing": {"score": 45.0, "passed": False},
                "security": {"score": 92.0, "passed": True}
            },
            "overall_score": 68.5
        }
        
        with patch("uvmgr.commands.dod.validate_dod_criteria", return_value=mock_result):
            result = self.runner.invoke(app, ["validate"])
            
        assert result.exit_code == 0  # Validation command doesn't exit with error
        assert "❌ FAIL" in result.stdout
        assert "45.0%" in result.stdout
        assert "Some validations failed" in result.stdout
        
    def test_pipeline_creation_success(self):
        """Test successful DevOps pipeline creation."""
        mock_result = {
            "success": True,
            "provider": "github",
            "files_created": [".github/workflows/dod-automation.yml"],
            "features_enabled": ["testing", "security"],
            "environments_configured": ["dev", "staging", "prod"]
        }
        
        with patch("uvmgr.commands.dod.generate_devops_pipeline", return_value=mock_result):
            result = self.runner.invoke(app, ["pipeline", "--provider", "github", "--environments", "dev,staging,prod"])
            
        assert result.exit_code == 0
        assert "🚀 DevOps Pipeline Creation" in result.stdout
        assert "✅ Pipeline created successfully!" in result.stdout
        assert "Provider: github" in result.stdout
        assert "Environments: dev, staging, prod" in result.stdout
        
    def test_pipeline_creation_failure(self):
        """Test DevOps pipeline creation failure."""
        mock_result = {
            "success": False,
            "error": "Invalid provider specified"
        }
        
        with patch("uvmgr.commands.dod.generate_devops_pipeline", return_value=mock_result):
            result = self.runner.invoke(app, ["pipeline", "--provider", "invalid"])
            
        assert result.exit_code == 0  # Pipeline command doesn't exit with error
        assert "❌ Failed to create pipeline" in result.stdout
        assert "Invalid provider specified" in result.stdout
        
    def test_comprehensive_testing_success(self):
        """Test successful comprehensive testing."""
        mock_result = {
            "success": True,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 25, "failed": 0},
                "api_tests": {"total": 15, "passed": 15, "failed": 0},
                "integration_tests": {"total": 8, "passed": 8, "failed": 0}
            }
        }
        
        with patch("uvmgr.commands.dod.run_e2e_automation", return_value=mock_result):
            result = self.runner.invoke(app, ["testing", "--strategy", "comprehensive", "--parallel"])
            
        assert result.exit_code == 0
        assert "🧪 Comprehensive Testing" in result.stdout
        assert "✅ PASS" in result.stdout
        assert "All tests passed!" in result.stdout
        
    def test_comprehensive_testing_failure(self):
        """Test comprehensive testing with failures."""
        mock_result = {
            "success": False,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 20, "failed": 5},
                "api_tests": {"total": 15, "passed": 15, "failed": 0}
            }
        }
        
        with patch("uvmgr.commands.dod.run_e2e_automation", return_value=mock_result):
            result = self.runner.invoke(app, ["testing"])
            
        assert result.exit_code == 1
        assert "❌ FAIL" in result.stdout
        assert "Some tests failed" in result.stdout
        
    def test_command_argument_parsing(self):
        """Test proper parsing of command arguments."""
        with patch("uvmgr.commands.dod.execute_complete_automation") as mock_execute:
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            
            self.runner.invoke(app, ["complete", "--env", "production", "--auto-fix", "--parallel"])
            
            call_args = mock_execute.call_args
            assert call_args[1]["environment"] == "production"
            assert call_args[1]["auto_fix"] is True
            assert call_args[1]["parallel"] is True
            
    def test_command_default_arguments(self):
        """Test command execution with default arguments."""
        with patch("uvmgr.commands.dod.execute_complete_automation") as mock_execute:
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            
            self.runner.invoke(app, ["complete"])
            
            call_args = mock_execute.call_args
            assert call_args[1]["environment"] == "development"
            assert call_args[1]["auto_fix"] is False
            assert call_args[1]["parallel"] is True
            
    def test_help_commands(self):
        """Test help output for all commands."""
        # Test main help
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Definition of Done automation" in result.stdout
        
        # Test individual command help
        for command in ["complete", "exoskeleton", "validate", "pipeline", "testing", "status"]:
            result = self.runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            
    def test_path_handling(self):
        """Test that commands properly handle project paths."""
        with patch("uvmgr.commands.dod.analyze_project_status") as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "health_score": 85.0,
                "dod_status": {"overall_score": 80.0},
                "security_posture": {"score": 90.0},
                "suggestions": []
            }
            
            self.runner.invoke(app, ["status"])
            
            # Verify that Path.cwd() was passed to the operation
            call_args = mock_analyze.call_args
            assert isinstance(call_args[1]["project_path"], Path)
            
    def test_error_handling_in_commands(self):
        """Test error handling in commands."""
        with patch("uvmgr.commands.dod.analyze_project_status", side_effect=Exception("Test error")):
            result = self.runner.invoke(app, ["status"])
            
        # Should handle gracefully and not crash
        assert result.exit_code != 0 or "error" in result.stdout.lower()


class TestDoDCommandsIntegration:
    """Integration tests for DoD commands with actual operations."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
        
    @pytest.mark.integration
    def test_full_dod_workflow(self):
        """Test complete DoD workflow integration."""
        # This would test the full workflow from command to result
        # but requires more complex mocking or real test environment
        pass
        
    @pytest.mark.integration 
    def test_command_operations_integration(self):
        """Test integration between commands and operations layers."""
        # Test that commands properly call operations with correct parameters
        # and handle results appropriately
        pass


class TestDoDCommandsPerformance:
    """Performance tests for DoD commands."""
    
    def test_command_response_time(self):
        """Test that commands respond within acceptable time limits."""
        import time
        
        with patch("uvmgr.commands.dod.analyze_project_status") as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "health_score": 85.0,
                "dod_status": {"overall_score": 80.0},
                "security_posture": {"score": 90.0},
                "suggestions": []
            }
            
            runner = CliRunner()
            start_time = time.time()
            result = runner.invoke(app, ["status"])
            end_time = time.time()
            
            assert result.exit_code == 0
            assert (end_time - start_time) < 2.0  # Should complete in under 2 seconds
            
    def test_memory_usage(self):
        """Test memory usage during command execution."""
        # This would require memory profiling tools
        # For now, just ensure commands complete without memory errors
        runner = CliRunner()
        
        with patch("uvmgr.commands.dod.analyze_project_status") as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "health_score": 85.0,
                "dod_status": {"overall_score": 80.0},
                "security_posture": {"score": 90.0},
                "suggestions": []
            }
            
            # Run multiple times to check for memory leaks
            for _ in range(10):
                result = runner.invoke(app, ["status"])
                assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__])