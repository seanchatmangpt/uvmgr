"""
Test the full suite of GitHub Actions API commands.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from uvmgr.commands.actions import (
    status, workflows, run, jobs, logs, cancel, rerun, 
    artifacts, secrets, variables, usage
)


class TestGitHubActionsFullSuite:
    """Test the complete GitHub Actions API suite."""

    @patch('uvmgr.ops.actions.get_workflow_runs')
    @patch('subprocess.check_output')
    def test_status_command(self, mock_check_output, mock_get_runs):
        """Test the status command."""
        mock_check_output.return_value = "test-token"
        mock_get_runs.return_value = [
            {
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "head_branch": "main",
                "html_url": "https://github.com/test/repo/actions/runs/123"
            }
        ]

        with patch('typer.echo') as mock_echo:
            status(owner="test-owner", repo="test-repo", limit=5, token=None)

        mock_get_runs.assert_called_once_with("test-owner", "test-repo", 5, "test-token")

    @patch('uvmgr.ops.actions.get_workflows')
    @patch('subprocess.check_output')
    def test_workflows_command(self, mock_check_output, mock_get_workflows):
        """Test the workflows command."""
        mock_check_output.return_value = "test-token"
        mock_get_workflows.return_value = [
            {
                "name": "CI",
                "state": "active",
                "path": ".github/workflows/ci.yml",
                "id": "123"
            }
        ]

        with patch('typer.echo') as mock_echo:
            workflows(owner="test-owner", repo="test-repo", token=None)

        mock_get_workflows.assert_called_once_with("test-owner", "test-repo", "test-token")

    @patch('uvmgr.ops.actions.get_workflow_run')
    @patch('subprocess.check_output')
    def test_run_command(self, mock_check_output, mock_get_run):
        """Test the run command."""
        mock_check_output.return_value = "test-token"
        mock_get_run.return_value = {
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "head_sha": "abc123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T01:00:00Z",
            "html_url": "https://github.com/test/repo/actions/runs/123"
        }

        with patch('typer.echo') as mock_echo:
            run(owner="test-owner", repo="test-repo", run_id=123, token=None)

        mock_get_run.assert_called_once_with("test-owner", "test-repo", 123, "test-token")

    @patch('uvmgr.ops.actions.get_workflow_run_jobs')
    @patch('subprocess.check_output')
    def test_jobs_command(self, mock_check_output, mock_get_jobs):
        """Test the jobs command."""
        mock_check_output.return_value = "test-token"
        mock_get_jobs.return_value = [
            {
                "name": "Build",
                "status": "completed",
                "conclusion": "success",
                "duration": 120,
                "id": "456"
            }
        ]

        with patch('typer.echo') as mock_echo:
            jobs(owner="test-owner", repo="test-repo", run_id=123, token=None)

        mock_get_jobs.assert_called_once_with("test-owner", "test-repo", 123, "test-token")

    @patch('uvmgr.ops.actions.get_workflow_run_logs')
    @patch('subprocess.check_output')
    def test_logs_command_workflow(self, mock_check_output, mock_get_logs):
        """Test the logs command for workflow run."""
        mock_check_output.return_value = "test-token"
        mock_get_logs.return_value = "Log content here"

        with patch('typer.echo') as mock_echo:
            logs(owner="test-owner", repo="test-repo", run_id=123, job_id=None, token=None)

        mock_get_logs.assert_called_once_with("test-owner", "test-repo", 123, "test-token")

    @patch('uvmgr.ops.actions.get_job_logs')
    @patch('subprocess.check_output')
    def test_logs_command_job(self, mock_check_output, mock_get_job_logs):
        """Test the logs command for specific job."""
        mock_check_output.return_value = "test-token"
        mock_get_job_logs.return_value = "Job log content here"

        with patch('typer.echo') as mock_echo:
            logs(owner="test-owner", repo="test-repo", run_id=123, job_id=456, token=None)

        mock_get_job_logs.assert_called_once_with("test-owner", "test-repo", 456, "test-token")

    @patch('uvmgr.ops.actions.cancel_workflow_run')
    @patch('subprocess.check_output')
    def test_cancel_command(self, mock_check_output, mock_cancel):
        """Test the cancel command."""
        mock_check_output.return_value = "test-token"
        mock_cancel.return_value = True

        with patch('typer.echo') as mock_echo:
            cancel(owner="test-owner", repo="test-repo", run_id=123, token=None)

        mock_cancel.assert_called_once_with("test-owner", "test-repo", 123, "test-token")

    @patch('uvmgr.ops.actions.rerun_workflow')
    @patch('subprocess.check_output')
    def test_rerun_command(self, mock_check_output, mock_rerun):
        """Test the rerun command."""
        mock_check_output.return_value = "test-token"
        mock_rerun.return_value = True

        with patch('typer.echo') as mock_echo:
            rerun(owner="test-owner", repo="test-repo", run_id=123, failed_only=False, token=None)

        mock_rerun.assert_called_once_with("test-owner", "test-repo", 123, False, "test-token")

    @patch('uvmgr.ops.actions.get_workflow_run_artifacts')
    @patch('subprocess.check_output')
    def test_artifacts_command(self, mock_check_output, mock_get_artifacts):
        """Test the artifacts command."""
        mock_check_output.return_value = "test-token"
        mock_get_artifacts.return_value = [
            {
                "name": "build-artifacts",
                "size_in_bytes": 1048576,
                "expires_at": "2023-01-08T00:00:00Z",
                "id": "789"
            }
        ]

        with patch('typer.echo') as mock_echo:
            artifacts(owner="test-owner", repo="test-repo", run_id=123, token=None)

        mock_get_artifacts.assert_called_once_with("test-owner", "test-repo", 123, "test-token")

    @patch('uvmgr.ops.actions.get_repository_secrets')
    @patch('subprocess.check_output')
    def test_secrets_command(self, mock_check_output, mock_get_secrets):
        """Test the secrets command."""
        mock_check_output.return_value = "test-token"
        mock_get_secrets.return_value = [
            {
                "name": "API_KEY",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        ]

        with patch('typer.echo') as mock_echo:
            secrets(owner="test-owner", repo="test-repo", token=None)

        mock_get_secrets.assert_called_once_with("test-owner", "test-repo", "test-token")

    @patch('uvmgr.ops.actions.get_repository_variables')
    @patch('subprocess.check_output')
    def test_variables_command(self, mock_check_output, mock_get_variables):
        """Test the variables command."""
        mock_check_output.return_value = "test-token"
        mock_get_variables.return_value = [
            {
                "name": "ENV",
                "value": "production",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        ]

        with patch('typer.echo') as mock_echo:
            variables(owner="test-owner", repo="test-repo", token=None)

        mock_get_variables.assert_called_once_with("test-owner", "test-repo", "test-token")

    @patch('uvmgr.ops.actions.get_repository_usage')
    @patch('subprocess.check_output')
    def test_usage_command(self, mock_check_output, mock_get_usage):
        """Test the usage command."""
        mock_check_output.return_value = "test-token"
        mock_get_usage.return_value = {
            "billable_minutes": {"UBUNTU": 100},
            "total_minutes": {"UBUNTU": 200},
            "included_minutes": {"UBUNTU": 3000},
            "period": "2023-01"
        }

        with patch('typer.echo') as mock_echo:
            usage(owner="test-owner", repo="test-repo", token=None)

        mock_get_usage.assert_called_once_with("test-owner", "test-repo", "test-token")

    @patch('subprocess.check_output')
    def test_token_retrieval_failure(self, mock_check_output):
        """Test token retrieval failure."""
        mock_check_output.side_effect = FileNotFoundError()

        with patch('typer.echo') as mock_echo:
            with pytest.raises(Exception):  # Will catch both SystemExit and click.exceptions.Exit
                status(owner="test-owner", repo="test-repo", limit=5, token=None)

        # Verify error message was displayed
        mock_echo.assert_called()

    def test_commands_with_provided_token(self):
        """Test that commands work with provided tokens."""
        with patch('uvmgr.ops.actions.get_workflow_runs') as mock_get_runs:
            mock_get_runs.return_value = []
            
            with patch('typer.echo') as mock_echo:
                with pytest.raises(Exception):  # Will catch both SystemExit and click.exceptions.Exit
                    status(owner="test-owner", repo="test-repo", limit=5, token="provided-token")

            mock_get_runs.assert_called_once_with("test-owner", "test-repo", 5, "provided-token") 