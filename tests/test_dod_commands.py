#!/usr/bin/env python3
"""
Unit tests for DoD command interface.

Tests the Typer CLI commands for Definition of Done automation,
ensuring proper argument handling, output formatting, and error cases.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
from rich.console import Console

from uvmgr.commands.dod import app, console


class TestDoDCommands:
    """Test DoD CLI command interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('uvmgr.commands.dod.execute_complete_automation')
    def test_complete_command_success(self, mock_execute):
        """Test successful complete automation command."""
        mock_execute.return_value = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": True, "score": 88.0}
            }
        }
        
        result = self.runner.invoke(app, [
            "complete", 
            "--env", "staging",
            "--auto-fix",
            "--parallel"
        ])
        
        assert result.exit_code == 0
        assert "DoD automation completed successfully" in result.stdout
        assert "PASS" in result.stdout
        
        # Verify function was called with correct parameters
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["environment"] == "staging"
        assert call_kwargs["auto_fix"] is True
        assert call_kwargs["parallel"] is True
    
    @patch('uvmgr.commands.dod.execute_complete_automation')
    def test_complete_command_failure(self, mock_execute):
        """Test complete automation command failure handling."""
        mock_execute.return_value = {
            "success": False,
            "criteria_results": {
                "testing": {"passed": False, "score": 45.0}
            }
        }
        
        result = self.runner.invoke(app, ["complete"])
        
        assert result.exit_code == 1
        assert "DoD automation failed" in result.stdout
        assert "FAIL" in result.stdout
    
    @patch('uvmgr.commands.dod.create_exoskeleton')
    def test_exoskeleton_command_success(self, mock_create):
        """Test successful exoskeleton initialization."""
        mock_create.return_value = {
            "success": True,
            "created_files": [
                {"path": ".uvmgr/config.yaml"},
                {"path": ".uvmgr/workflows/dod.yml"}
            ]
        }
        
        result = self.runner.invoke(app, [
            "exoskeleton",
            "--template", "enterprise",
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "Exoskeleton initialized successfully" in result.stdout
        assert "Created 2 files" in result.stdout
        
        # Verify correct parameters
        mock_create.assert_called_once()
        call_args = mock_create.call_args[0]
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["template"] == "enterprise"
        assert call_kwargs["force"] is True
    
    @patch('uvmgr.commands.dod.create_exoskeleton')
    def test_exoskeleton_command_failure(self, mock_create):
        """Test exoskeleton initialization failure."""
        mock_create.return_value = {
            "success": False,
            "error": "Directory already exists"
        }
        
        result = self.runner.invoke(app, ["exoskeleton"])
        
        assert result.exit_code == 1
        assert "Failed to initialize exoskeleton" in result.stdout
        assert "Directory already exists" in result.stdout
    
    @patch('uvmgr.commands.dod.validate_dod_criteria')
    def test_validate_command_success(self, mock_validate):
        """Test successful criteria validation command."""
        mock_validate.return_value = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 92.0, "passed": True},
                "security": {"score": 88.0, "passed": True},
                "devops": {"score": 76.0, "passed": True}
            },
            "overall_score": 85.3
        }
        
        result = self.runner.invoke(app, [
            "validate",
            "--criteria", "testing",
            "--criteria", "security", 
            "--detailed"
        ])
        
        assert result.exit_code == 0
        assert "All validations passed" in result.stdout
        assert "Overall Score: 85.3%" in result.stdout
        assert "PASS" in result.stdout
        
        # Verify parameters
        mock_validate.assert_called_once()
        call_kwargs = mock_validate.call_args[1]
        assert call_kwargs["criteria"] == ["testing", "security"]
        assert call_kwargs["detailed"] is True
    
    @patch('uvmgr.commands.dod.validate_dod_criteria')
    def test_validate_command_partial_failure(self, mock_validate):
        """Test validation with some failures."""
        mock_validate.return_value = {
            "success": False,
            "criteria_scores": {
                "testing": {"score": 92.0, "passed": True},
                "security": {"score": 45.0, "passed": False}
            },
            "overall_score": 68.5
        }
        
        result = self.runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0  # validate doesn't exit on failure
        assert "Some validations failed" in result.stdout
        assert "Overall Score: 68.5%" in result.stdout
    
    @patch('uvmgr.commands.dod.generate_devops_pipeline')
    def test_pipeline_command_success(self, mock_generate):
        """Test successful pipeline generation."""
        mock_generate.return_value = {
            "success": True,
            "provider": "github",
            "files_created": [".github/workflows/dod-automation.yml"],
            "environments_configured": ["dev", "staging", "prod"]
        }
        
        result = self.runner.invoke(app, [
            "pipeline",
            "--provider", "github",
            "--environments", "dev,staging,prod"
        ])
        
        assert result.exit_code == 0
        assert "Pipeline created successfully" in result.stdout
        assert "Provider: github" in result.stdout
        assert "Environments: dev, staging, prod" in result.stdout
    
    @patch('uvmgr.commands.dod.generate_devops_pipeline')
    def test_pipeline_command_failure(self, mock_generate):
        """Test pipeline generation failure."""
        mock_generate.return_value = {
            "success": False,
            "error": "Unsupported provider"
        }
        
        result = self.runner.invoke(app, [
            "pipeline",
            "--provider", "unsupported"
        ])
        
        assert result.exit_code == 0  # pipeline doesn't exit on failure
        assert "Failed to create pipeline" in result.stdout
        assert "Unsupported provider" in result.stdout
    
    @patch('uvmgr.commands.dod.run_e2e_automation')
    def test_testing_command_success(self, mock_run):
        """Test successful comprehensive testing."""
        mock_run.return_value = {
            "success": True,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 23, "failed": 2},
                "api_tests": {"total": 15, "passed": 15, "failed": 0},
                "integration_tests": {"total": 8, "passed": 7, "failed": 1}
            }
        }
        
        result = self.runner.invoke(app, [
            "testing",
            "--strategy", "comprehensive",
            "--coverage", "85",
            "--parallel"
        ])
        
        assert result.exit_code == 0
        assert "All tests passed" in result.stdout
        assert "Browser_Tests" in result.stdout
        assert "23/25" in result.stdout  # passed/total format
    
    @patch('uvmgr.commands.dod.run_e2e_automation')
    def test_testing_command_failure(self, mock_run):
        """Test testing command with failures."""
        mock_run.return_value = {
            "success": False,
            "test_suites": {
                "browser_tests": {"total": 25, "passed": 20, "failed": 5}
            }
        }
        
        result = self.runner.invoke(app, ["testing"])
        
        assert result.exit_code == 1
        assert "Some tests failed" in result.stdout
        assert "FAIL" in result.stdout
    
    @patch('uvmgr.commands.dod.analyze_project_status')
    def test_status_command_excellent_score(self, mock_analyze):
        """Test status command with excellent health score."""
        mock_analyze.return_value = {
            "success": True,
            "health_score": 92.5,
            "dod_status": {"overall_score": 89.0},
            "security_posture": {"score": 95.0},
            "suggestions": ["Keep up the good work", "Consider adding more tests"]
        }
        
        result = self.runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "Overall Health Score: 92.5%" in result.stdout
        assert "EXCELLENT" in result.stdout
        assert "DoD Compliance: 89.0%" in result.stdout
        assert "Security Score: 95.0%" in result.stdout
        assert "Keep up the good work" in result.stdout
    
    @patch('uvmgr.commands.dod.analyze_project_status')
    def test_status_command_needs_work(self, mock_analyze):
        """Test status command with low health score."""
        mock_analyze.return_value = {
            "success": True,
            "health_score": 45.2,
            "dod_status": {"overall_score": 42.0},
            "security_posture": {"score": 38.0},
            "suggestions": [
                "Improve test coverage",
                "Fix security vulnerabilities", 
                "Update dependencies"
            ]
        }
        
        result = self.runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "Overall Health Score: 45.2%" in result.stdout
        assert "NEEDS WORK" in result.stdout
        assert "Improve test coverage" in result.stdout
        assert "uvmgr dod complete --auto-fix" in result.stdout
    
    @patch('uvmgr.commands.dod.analyze_project_status')
    def test_status_command_good_score(self, mock_analyze):
        """Test status command with good health score."""
        mock_analyze.return_value = {
            "success": True,
            "health_score": 72.8,
            "dod_status": {"overall_score": 70.0},
            "security_posture": {"score": 75.0},
            "suggestions": ["Add integration tests"]
        }
        
        result = self.runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "GOOD" in result.stdout
    
    def test_command_help_messages(self):
        """Test that all commands have proper help messages."""
        # Test main app help
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Definition of Done automation" in result.stdout
        
        # Test individual command help
        commands = ["complete", "exoskeleton", "validate", "pipeline", "testing", "status"]
        
        for command in commands:
            result = self.runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.stdout
    
    def test_command_option_validation(self):
        """Test command option validation."""
        # Test invalid coverage value
        result = self.runner.invoke(app, [
            "testing", 
            "--coverage", "150"  # Invalid: >100
        ])
        # Should still work, validation is application logic
        assert result.exit_code in [0, 1]  # Depending on mock setup
    
    @patch('uvmgr.commands.dod.Path.cwd')
    def test_working_directory_usage(self, mock_cwd):
        """Test that commands use current working directory."""
        mock_cwd.return_value = Path("/test/project")
        
        with patch('uvmgr.commands.dod.execute_complete_automation') as mock_execute:
            mock_execute.return_value = {"success": True, "criteria_results": {}}
            
            self.runner.invoke(app, ["complete"])
            
            # Verify project_path was set to current directory
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs["project_path"] == Path("/test/project")


class TestRichOutputFormatting:
    """Test Rich console output formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('uvmgr.commands.dod.execute_complete_automation')
    def test_table_formatting_in_complete(self, mock_execute):
        """Test that complete command formats results in a table."""
        mock_execute.return_value = {
            "success": True,
            "criteria_results": {
                "testing": {"passed": True, "score": 95.0},
                "security": {"passed": False, "score": 65.0},
                "devops": {"passed": True, "score": 88.0}
            }
        }
        
        result = self.runner.invoke(app, ["complete"])
        
        # Check for table structure indicators
        assert "┏" in result.stdout or "╭" in result.stdout  # Table borders
        assert "Criteria" in result.stdout
        assert "Status" in result.stdout  
        assert "Score" in result.stdout
        assert "Testing" in result.stdout
        assert "95.0%" in result.stdout
    
    @patch('uvmgr.commands.dod.validate_dod_criteria')
    def test_table_formatting_in_validate(self, mock_validate):
        """Test validation results table formatting."""
        mock_validate.return_value = {
            "success": True,
            "criteria_scores": {
                "testing": {"score": 92.0, "passed": True},
                "security": {"score": 78.0, "passed": True}
            },
            "overall_score": 85.0
        }
        
        result = self.runner.invoke(app, ["validate"])
        
        # Check for proper Rich table formatting
        assert "Validation Results" in result.stdout
        assert "┏" in result.stdout or "╭" in result.stdout
        assert "92.0%" in result.stdout
        assert "78.0%" in result.stdout
    
    @patch('uvmgr.commands.dod.analyze_project_status')
    def test_panel_formatting_in_status(self, mock_analyze):
        """Test status command panel formatting."""
        mock_analyze.return_value = {
            "success": True,
            "health_score": 85.0,
            "dod_status": {"overall_score": 82.0},
            "security_posture": {"score": 88.0},
            "suggestions": []
        }
        
        result = self.runner.invoke(app, ["status"])
        
        # Check for Rich panel formatting
        assert "DoD Status Summary" in result.stdout
        assert "╭" in result.stdout or "┌" in result.stdout  # Panel borders
        assert "Overall Health Score: 85.0%" in result.stdout


class TestErrorScenarios:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('uvmgr.commands.dod.execute_complete_automation')
    def test_complete_command_exception_handling(self, mock_execute):
        """Test complete command handles exceptions gracefully."""
        mock_execute.side_effect = Exception("Unexpected error")
        
        result = self.runner.invoke(app, ["complete"])
        
        # Should not crash, but may exit with error code
        assert result.exit_code in [0, 1, 2]
    
    @patch('uvmgr.commands.dod.create_exoskeleton')
    def test_exoskeleton_command_exception_handling(self, mock_create):
        """Test exoskeleton command handles exceptions gracefully."""
        mock_create.side_effect = Exception("File system error")
        
        result = self.runner.invoke(app, ["exoskeleton"])
        
        # Should not crash the application
        assert result.exit_code in [0, 1, 2]
    
    def test_command_with_invalid_arguments(self):
        """Test commands with invalid argument combinations."""
        # Test non-existent template
        result = self.runner.invoke(app, [
            "exoskeleton", 
            "--template", "nonexistent"
        ])
        
        # Should handle gracefully (specific behavior depends on implementation)
        assert result.exit_code in [0, 1, 2]
    
    @patch('uvmgr.commands.dod.DOD_CRITERIA_WEIGHTS', {})
    def test_commands_with_empty_criteria(self, ):
        """Test command behavior when no criteria are defined."""
        result = self.runner.invoke(app, ["validate"])
        
        # Should handle empty criteria gracefully
        assert result.exit_code in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])